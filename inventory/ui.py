"""Vistas Streamlit; las reglas de negocio permanecen en servicios separados."""
import uuid
import sqlite3
from difflib import SequenceMatcher
from pathlib import Path
from datetime import date
import streamlit as st

from inventory.database import find_duplicate, record_receipt, update_product, set_product_classification
from inventory.readers import ai_extract, drafts_from_upload, local_ocr, openai_key
from inventory.theme import page_header
from inventory.text import clean_product_name, normalize_product_key, display_product_name
from inventory.classifier import classify_line, suggest_product_category, LINE_TYPES, MERCHANDISE


def dashboard(con):
    products = con.execute("SELECT * FROM products WHERE active=1 AND item_type='Mercadería' ORDER BY name").fetchall()
    receipts = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NULL").fetchone()["n"]
    duplicates = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NOT NULL").fetchone()["n"]
    excluded = con.execute("SELECT COUNT(*) AS n FROM products WHERE active=1 AND item_type<>'Mercadería'").fetchone()["n"]
    page_header("Inventario de mercadería", "Compras recibidas, unidades disponibles y precios sugeridos.")
    a, b, c, d = st.columns(4)
    a.metric("Productos activos", len(products))
    b.metric("Unidades en stock", sum(p["stock"] for p in products))
    c.metric("Facturas registradas", receipts)
    d.metric("Repetidas archivadas", duplicates)
    if excluded:
        st.caption(f"{excluded} servicios, comisiones y ajustes se conservan en sus facturas, fuera del stock.")
    low_stock = sum(p["stock"] <= p["min_stock"] for p in products)
    if low_stock:
        st.warning(f"{low_stock} producto(s) están en su mínimo de stock o por debajo.")
    st.subheader("Stock actual")
    if products:
        s1, s2 = st.columns([2, 1])
        search = s1.text_input("Buscar producto", placeholder="Nombre, marca o variante", key="dashboard_product_search")
        categories = sorted({p["category"] for p in products if p["category"]})
        category = s2.selectbox("Categoría", ["Todas"] + categories, key="dashboard_product_category")
        visible = [p for p in products if (not search or search.casefold() in (p["name"] + " " + (p["description"] or "")).casefold())
                   and (category == "Todas" or p["category"] == category)]
        st.caption(f"Mostrando {len(visible)} de {len(products)} productos inventariables")
        st.dataframe([{"Producto": display_product_name(p["name"]), "Descripción": p["description"] or "—", "Categoría": p["category"] or "—", "Unidades": p["stock"], "Stock mínimo": p["min_stock"],
            "Costo unitario": f"$ {p['cost']:,}".replace(",", "."), "Margen": f"{p['margin']:g}%",
            "Precio sugerido": f"$ {round(p['cost']*(1+p['margin']/100)):,}".replace(",", ".")}
            for p in visible], use_container_width=True, hide_index=True)
    else:
        st.info("Tu catálogo aparecerá aquí cuando confirmes una factura o agregues un producto.")


def _add_uploads(uploads, queue):
    errors = []
    for file in uploads:
        try:
            for index, draft in enumerate(drafts_from_upload(file.name, file.getvalue()), start=1):
                label = f"{draft.get('supplier') or file.name} · F{draft.get('number') or index}"
                key, suffix = label, 2
                while key in queue:
                    key, suffix = f"{label} ({suffix})", suffix + 1
                queue[key] = draft
        except Exception as exc:
            errors.append(f"{file.name}: {str(exc)[:180]}")
    return errors


def documents(con, docs_dir: Path):
    page_header("Ingresar facturas", "Revisa y clasifica cada línea antes de actualizar el inventario.")
    with st.expander("Conectar con el SII", expanded=False):
        st.markdown("**Importación oficial de facturas recibidas**")
        st.write("El SII permite generar un archivo de respaldo XML con DTE recibidos. Descárgalo en el portal y súbelo aquí: cada factura se separará para revisar sus productos.")
        st.link_button("Abrir guía oficial del SII", "https://www.sii.cl/destacados/factura_electronica/guias_ayuda/como_generar_archivo_respaldo.htm")
        st.caption("Ruta: Oficina Virtual → Factura Electrónica → Historial de DTE recibidos → Archivo Respaldo (XML). Esta app no guarda tu Clave Tributaria.")
        st.info("El SII no publica una API abierta para descargar automáticamente todas las facturas entrantes. La importación usa el respaldo XML oficial y evita automatizaciones frágiles del portal.")

    ai_key = openai_key() or st.session_state.get("openai_key", "")
    with st.expander("Lectura con inteligencia artificial", expanded=False):
        st.caption("La IA puede leer PDF e imágenes. El XML del SII se interpreta localmente sin consumir API.")
        typed_key = st.text_input("API key de OpenAI (opcional)", value="", type="password", placeholder="Se usa solo durante esta sesión")
        if typed_key:
            st.session_state["openai_key"] = typed_key.strip()
            ai_key = typed_key.strip()
        if ai_key:
            st.success("Lectura con IA disponible")
        else:
            st.caption("Agrega aquí tu API key o configura OPENAI_API_KEY en el equipo.")

    uploads = st.file_uploader("Archivos de proveedores o respaldo XML del SII",
        type=["pdf", "png", "jpg", "jpeg", "xml"], accept_multiple_files=True,
        help="Puedes seleccionar varias facturas; los respaldos XML se dividen por DTE.")
    if uploads and st.button(f"Preparar {len(uploads)} archivo(s)", type="primary"):
        queue = st.session_state.setdefault("queue", {})
        for error in _add_uploads(uploads, queue):
            st.error(error)
        st.rerun()

    queue = st.session_state.setdefault("queue", {})
    if not queue:
        st.info("Tus archivos aparecerán aquí listos para revisar.")
        return
    selected = st.selectbox("Documento por revisar", list(queue), format_func=lambda name: f"Pendiente · {name}")
    item = queue[selected]
    original, review = st.columns([.85, 1.35], gap="large")
    with original:
        st.subheader("Documento original")
        if item["source_name"].lower().endswith((".jpg", ".jpeg", ".png")):
            st.image(item["bytes"], use_container_width=True)
        else:
            st.download_button("Descargar archivo original", item["bytes"], file_name=item["source_name"])
        if item.get("dte"):
            st.success("Datos del DTE extraídos desde XML en este equipo.")
            st.caption(f"RUT: {item.get('rut') or '—'} · Tipo DTE: {item.get('kind') or '—'} · Total declarado: $ {item.get('total') or '—'}")
        else:
            engine = st.radio("Método de lectura", ["OpenAI", "OCR local"], horizontal=True,
                              index=0 if ai_key else 1, key=f"engine_{selected}")
            if st.button("Leer documento", key=f"read_{selected}", disabled=engine == "OpenAI" and not ai_key):
                try:
                    if engine == "OpenAI":
                        data = ai_extract(item["bytes"], item["source_name"], ai_key)
                        item["supplier"] = data.get("proveedor", "")
                        item["number"] = data.get("numero", "")
                        try:
                            item["date"] = date.fromisoformat(data.get("fecha", ""))
                        except (ValueError, TypeError):
                            pass
                        item["items"] = data.get("productos", [])
                        st.session_state[f"supplier_{selected}"] = item["supplier"]
                        st.session_state[f"number_{selected}"] = item["number"]
                        st.session_state[f"date_{selected}"] = item["date"]
                        for index, row in enumerate(item["items"]):
                            st.session_state[f"name_{selected}_{index}"] = row.get("nombre", "")
                            st.session_state[f"qty_{selected}_{index}"] = max(0, int(float(row.get("cantidad") or 1)))
                            st.session_state[f"cost_{selected}_{index}"] = max(0, int(float(row.get("costo_unitario") or 0)))
                        st.success("Lectura lista: revisa datos y cantidades antes de confirmar.")
                    else:
                        item["raw"] = local_ocr(item["bytes"], item["source_name"])
                        item["supplier"] = item["supplier"] or (item["raw"].splitlines()[0][:100] if item["raw"].strip() else "")
                        st.info("Texto reconocido. Completa o corrige el detalle manualmente.")
                    st.rerun()
                except Exception as exc:
                    st.error(f"No se pudo leer el archivo: {str(exc)[:240]}")
            if item.get("raw"):
                with st.expander("Texto detectado por OCR"):
                    st.text(item["raw"])

    with review:
        st.subheader("Revisión editable")
        supplier = st.text_input("Proveedor", item["supplier"], key=f"supplier_{selected}")
        number = st.text_input("Folio", item["number"], key=f"number_{selected}")
        doc_date = st.date_input("Fecha de emisión", value=item["date"], key=f"date_{selected}")
        rows = item.get("items") or [{"nombre": "", "cantidad": 1, "costo_unitario": 0}]
        item["items"] = rows
        st.markdown("**Líneas de la factura**")
        st.caption("La app sugiere qué líneas son mercadería. Servicios, comisiones y fletes se guardan en la factura, pero no crean productos ni aumentan el stock.")
        if any(float(row.get("cantidad") or 0) % 1 for row in rows):
            st.warning("El XML incluye una cantidad fraccionaria. Ajusta manualmente las unidades completas antes de confirmar.")
        edited = []
        catalog = con.execute("SELECT id,name,category,description FROM products WHERE active=1 AND item_type='Mercadería' ORDER BY name").fetchall()
        alias_rows = con.execute("SELECT product_id,alias,alias_key FROM product_aliases").fetchall()
        aliases_by_product = {}
        for alias in alias_rows:
            aliases_by_product.setdefault(alias["product_id"], []).append(alias["alias"])
        for index, row in enumerate(rows):
            with st.container(border=True):
                name = st.text_input("Descripción de factura", row.get("nombre", ""), key=f"name_{selected}_{index}")
                suggested_type, reason = classify_line(name)
                saved_type = row.get("line_type", suggested_type)
                selected_type = st.selectbox("Clasificación", LINE_TYPES,
                    index=LINE_TYPES.index(saved_type) if saved_type in LINE_TYPES else LINE_TYPES.index(suggested_type),
                    key=f"line_type_{selected}_{index}",
                    help="Solo las líneas clasificadas como Mercadería afectan el inventario.")
                if selected_type == suggested_type:
                    st.caption(f"Sugerencia automática: {suggested_type}. {reason}")
                else:
                    st.caption(f"Clasificación modificada manualmente. La sugerencia por descripción era: {suggested_type}.")
                c1, c2 = st.columns([.8, 1.2])
                quantity = c1.number_input("Unidades/cantidad", min_value=0, max_value=100000,
                    value=max(0, int(float(row.get("cantidad") or 1))), step=1, key=f"qty_{selected}_{index}")
                cost = c2.number_input("Valor unitario", min_value=0, max_value=100000000,
                    value=max(0, int(float(row.get("costo_unitario") or 0))), step=100, key=f"cost_{selected}_{index}")
                mapping = None
                if selected_type == MERCHANDISE:
                    normalized_name = normalize_product_key(name)
                    def similarity(product):
                        labels = [product["name"], *aliases_by_product.get(product["id"], [])]
                        return max((SequenceMatcher(None, normalized_name, normalize_product_key(label)).ratio()
                                    for label in labels), default=0)
                    ranked = sorted(catalog, key=similarity, reverse=True)
                    possible = [p for p in ranked if normalized_name and similarity(p) >= .68][:3]
                    if possible:
                        st.caption("Posibles coincidencias: " + " · ".join(p["name"] for p in possible) + ". Confirma la correcta en el selector.")
                    options = [None] + [p["id"] for p in ranked]
                    default_id = row.get("product_id")
                    if default_id not in options:
                        exact = next((p["id"] for p in catalog if normalize_product_key(p["name"]) == normalized_name), None)
                        if exact is None:
                            exact = next((a["product_id"] for a in alias_rows if a["alias_key"] == normalized_name), None)
                        default_id = exact
                    mapping = st.selectbox("Asociar al producto del inventario", options,
                        index=options.index(default_id) if default_id in options else 0,
                        format_func=lambda pid: "Crear producto nuevo" if pid is None else next(
                            f"{p['name']} · {p['category']}" if p["category"] else p["name"]
                            for p in catalog if p["id"] == pid),
                        key=f"mapping_{selected}_{index}")
                    if mapping is None:
                        st.caption("Si confirmas, esta línea creará un producto nuevo en el catálogo.")
                    elif normalize_product_key(name) != normalize_product_key(next(p["name"] for p in catalog if p["id"] == mapping)):
                        st.caption("Al confirmar, este nombre de factura se guardará como alias para facilitar futuras coincidencias.")
                else:
                    st.info("Se conservará en el detalle de la factura y no se ingresará al stock.")
                edited.append({"nombre": name, "cantidad": quantity, "costo_unitario": cost,
                               "product_id": mapping, "line_type": selected_type})
        item["supplier"], item["number"], item["date"], item["items"] = supplier, number, doc_date, edited
        add, remove = st.columns(2)
        if add.button("＋ Agregar producto", key=f"add_{selected}"):
            item["items"].append({"nombre": "", "cantidad": 1, "costo_unitario": 0})
            st.rerun()
        if remove.button("Quitar documento", key=f"remove_{selected}"):
            del queue[selected]
            st.rerun()
        duplicate = find_duplicate(con, item)
        if duplicate:
            st.warning("Esta factura ya está registrada. Si agregas esta copia, quedará archivada como repetida y no cambiará el stock.")
            st.caption(f"Documento original: {duplicate['supplier']} · Folio {duplicate['invoice_no']} · registro #{duplicate['id']}")
            save_duplicate, discard_duplicate = st.columns([1.5, 1])
            if save_duplicate.button("Agregar como repetida · sin modificar stock", key=f"duplicate_{selected}"):
                try:
                    path = docs_dir / f"{uuid.uuid4().hex}_{Path(item['source_name']).name}"
                    record_receipt(con, item, edited, path, duplicate_of=duplicate["id"])
                    del queue[selected]
                    st.success("Copia archivada como repetida. No se creó stock ni movimiento.")
                    st.rerun()
                except Exception as exc:
                    st.error(str(exc))
            if discard_duplicate.button("Descartar copia", key=f"discard_duplicate_{selected}"):
                del queue[selected]
                st.rerun()
        elif st.button("Confirmar factura", type="primary", key=f"confirm_{selected}"):
            try:
                if any(not row["nombre"].strip() for row in edited):
                    raise ValueError("Completa el nombre de cada producto.")
                if any(row["line_type"] == MERCHANDISE and row["cantidad"] <= 0 for row in edited):
                    raise ValueError("Las unidades de mercadería deben ser mayores que cero.")
                path = docs_dir / f"{uuid.uuid4().hex}_{Path(item['source_name']).name}"
                record_receipt(con, item, edited, path)
                del queue[selected]
                merchandise_count = sum(row["line_type"] == MERCHANDISE for row in edited)
                other_count = len(edited) - merchandise_count
                st.success(f"Factura guardada. {merchandise_count} línea(s) de mercadería ingresaron al inventario; {other_count} línea(s) de servicios o cargos quedaron solo en el detalle.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def products(con):
    page_header("Productos", "Administra el catálogo, unidades disponibles, costos y márgenes.")
    with st.expander("＋ Agregar producto"):
        with st.form("new_product"):
            name = st.text_input("Nombre del producto")
            category = st.text_input("Categoría")
            description = st.text_input("Descripción / formato / variante", placeholder="Ej.: sabor, tamaño, color o presentación")
            a, b, c = st.columns(3)
            stock = a.number_input("Stock inicial (unidades)", 0, 100000, 0)
            cost = b.number_input("Costo unitario", 0, 100000000, 0)
            margin = c.number_input("Margen sobre costo (%)", 0., 10000., 30.)
            min_stock = st.number_input("Avisarme al llegar a (unidades)", 0, 100000, 3)
            if st.form_submit_button("Guardar producto", type="primary"):
                name = clean_product_name(name)
                if not name:
                    st.error("Escribe el nombre del producto.")
                else:
                    try:
                        with con:
                            con.execute("INSERT INTO products(name,category,description,stock,cost,margin,min_stock) VALUES(?,?,?,?,?,?,?)",
                                (name.strip(), category.strip(), description.strip(), stock, cost, margin, min_stock))
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo guardar: {exc}")
    all_active = con.execute("SELECT * FROM products WHERE active=1 ORDER BY name").fetchall()
    uncategorized = [(p, suggest_product_category(p["name"])) for p in all_active
                     if p["item_type"] == MERCHANDISE and not p["category"] and suggest_product_category(p["name"])]
    if uncategorized:
        with st.expander(f"Completar categorías del catálogo ({len(uncategorized)})", expanded=False):
            st.dataframe([{"Producto": display_product_name(p["name"]), "Categoría sugerida": category}
                          for p, category in uncategorized], use_container_width=True, hide_index=True)
            if st.button("Aplicar categorías sugeridas", key="apply_product_categories"):
                with con:
                    for p, category in uncategorized:
                        con.execute("UPDATE products SET category=? WHERE id=? AND (category IS NULL OR category='')",
                                    (category, p["id"]))
                st.rerun()
    suggested = [(p, *classify_line(p["name"])) for p in all_active
                 if p["item_type"] == MERCHANDISE and classify_line(p["name"])[0] != MERCHANDISE]
    if suggested:
        with st.expander(f"Revisar conceptos que parecen servicios o cargos ({len(suggested)})", expanded=True):
            st.caption("La app conserva la factura, pero estos conceptos no deberían contar como mercadería. Aplicar la sugerencia deja su saldo en cero y registra el ajuste.")
            st.dataframe([{"Descripción detectada": display_product_name(p["name"]), "Tipo sugerido": kind,
                "Unidades a retirar del stock": p["stock"], "Motivo": reason} for p, kind, reason in suggested],
                use_container_width=True, hide_index=True)
            if st.button(f"Aplicar las sugerencias a {len(suggested)} concepto(s)", type="primary", key="classify_existing_nonstock"):
                for p, kind, _ in suggested:
                    set_product_classification(con, p["id"], kind)
                st.success("Conceptos reclasificados. Sus facturas y ajustes quedaron en el historial.")
                st.rerun()
    noninventory = [p for p in all_active if p["item_type"] != MERCHANDISE]
    if noninventory:
        with st.expander(f"Conceptos excluidos del inventario ({len(noninventory)})", expanded=False):
            st.dataframe([{"Descripción": display_product_name(p["name"]), "Clasificación": p["item_type"]}
                          for p in noninventory], use_container_width=True, hide_index=True)
            selected_noninventory = st.selectbox("Reincorporar como mercadería", noninventory,
                format_func=lambda p: display_product_name(p["name"]), key="reinclude_noninventory")
            if st.button("Reincorporar al inventario", key="reinclude_inventory_item"):
                set_product_classification(con, selected_noninventory["id"], MERCHANDISE)
                st.rerun()
    rows = [p for p in all_active if p["item_type"] == MERCHANDISE]
    if not rows:
        st.info("Todavía no hay mercadería en el catálogo. Puedes agregar productos o reincorporar uno excluido.")
        return
    catalog_search = st.text_input("Buscar en el catálogo", placeholder="Producto, descripción o marca", key="products_catalog_search")
    if catalog_search:
        query = catalog_search.casefold()
        rows = [p for p in rows if query in (p["name"] + " " + (p["description"] or "") + " " + (p["category"] or "")).casefold()]
    st.caption(f"{len(rows)} producto(s) en la vista")
    if not rows:
        st.info("No encontré productos con ese texto.")
        return
    proposals = [(p["id"], p["name"], display_product_name(p["name"])) for p in rows]
    changes = [(pid, old, new) for pid, old, new in proposals if old != new]
    if changes:
        proposed_counts = {}
        for _, _, new in changes:
            proposed_counts[new] = proposed_counts.get(new, 0) + 1
        safe_changes, conflicts = [], []
        for pid, old, new in changes:
            collision = con.execute("SELECT 1 FROM products WHERE name=? AND id<>? LIMIT 1", (new, pid)).fetchone()
            if collision or proposed_counts[new] > 1:
                conflicts.append((old, new))
            else:
                safe_changes.append((pid, old, new))
        with st.expander(f"Revisar descripciones para corregir ({len(changes)})", expanded=False):
            st.caption("Vista previa de espacios entre letras y signos de lectura erróneos. Los nombres con posible conflicto se dejan intactos.")
            st.dataframe([{"Actual": old, "Corregido": new} for _, old, new in changes], use_container_width=True, hide_index=True)
            if conflicts:
                st.warning("Algunos nombres coincidirían con otro producto y no se cambiarán automáticamente.")
            if safe_changes and st.button(f"Aplicar {len(safe_changes)} corrección(es)", key="clean_product_names"):
                with con:
                    for pid, _, new in safe_changes:
                        con.execute("UPDATE products SET name=? WHERE id=?", (new, pid))
                st.success("Descripciones corregidas sin cambiar stock ni movimientos.")
                st.rerun()
    st.dataframe([{"Producto": display_product_name(p["name"]), "Descripción": p["description"] or "—", "Categoría": p["category"] or "—", "Unidades": p["stock"], "Mínimo": p["min_stock"],
        "Costo": p["cost"], "Margen %": p["margin"], "Precio sugerido": round(p["cost"] * (1 + p["margin"] / 100))}
        for p in rows], use_container_width=True, hide_index=True)
    with st.expander("Editar producto"):
        product = st.selectbox("Producto", rows, format_func=lambda p: display_product_name(p["name"]))
        with st.form(f"edit_{product['id']}"):
            name = st.text_input("Nombre del producto", product["name"])
            category = st.text_input("Categoría", product["category"] or "")
            description = st.text_input("Descripción / formato / variante", product["description"] or "")
            current_aliases = [r[0] for r in con.execute("SELECT alias FROM product_aliases WHERE product_id=? ORDER BY alias", (product["id"],))]
            aliases_text = st.text_input("Nombres alternativos de proveedores (separados por coma)", ", ".join(current_aliases),
                help="Se usarán para reconocer este producto en próximas facturas.")
            a, b, c = st.columns(3)
            stock = a.number_input("Stock (unidades)", 0, 100000, product["stock"])
            cost = b.number_input("Costo", 0, 100000000, product["cost"])
            margin = c.number_input("Margen %", 0., 10000., float(product["margin"]))
            min_stock = st.number_input("Avisarme al llegar a (unidades)", 0, 100000, int(product["min_stock"]))
            reason = st.text_input("Motivo del ajuste de stock", placeholder="Recuento, merma, consumo…")
            if st.form_submit_button("Guardar cambios", type="primary"):
                name = clean_product_name(name)
                if not name:
                    st.error("El nombre no puede quedar vacío.")
                else:
                    try:
                        aliases = [alias.strip() for alias in aliases_text.split(",") if alias.strip()]
                        update_product(con, product["id"], name, category, stock, cost, margin, min_stock, reason, description, aliases)
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo guardar el producto: {exc}")


def movements(con):
    page_header("Movimientos", "Historial de compras confirmadas y cambios de stock.")
    rows = con.execute("""SELECT m.created_at,p.name,r.supplier,r.invoice_no,r.filename,m.quantity,m.unit_cost
        FROM movements m JOIN products p ON p.id=m.product_id JOIN receipts r ON r.id=m.receipt_id
        WHERE p.item_type='Mercadería' ORDER BY m.id DESC""").fetchall()
    if rows:
        st.dataframe([dict(row) for row in rows], use_container_width=True, hide_index=True)
    else:
        st.info("Los ingresos de stock confirmados aparecerán aquí.")
    adjustments = con.execute("""SELECT a.created_at,p.name,a.old_stock,a.new_stock,a.delta,a.reason
        FROM inventory_adjustments a JOIN products p ON p.id=a.product_id ORDER BY a.id DESC""").fetchall()
    st.subheader("Ajustes manuales de stock")
    if adjustments:
        st.dataframe([dict(row) for row in adjustments], use_container_width=True, hide_index=True)
    else:
        st.caption("Los cambios manuales quedarán registrados aquí con su motivo.")
    duplicates = con.execute("""SELECT d.created_at,d.supplier,d.invoice_no,d.filename,
        original.id AS original_id FROM receipts d JOIN receipts original ON original.id=d.duplicate_of
        ORDER BY d.id DESC""").fetchall()
    if duplicates:
        st.subheader("Facturas repetidas archivadas · sin cambios de stock")
        st.dataframe([dict(row) for row in duplicates], use_container_width=True, hide_index=True)


def receipts(con, docs_dir: Path):
    page_header("Facturas", "Consulta documentos guardados, líneas reconocidas y facturas repetidas.")
    suppliers = [r[0] for r in con.execute("SELECT DISTINCT supplier FROM receipts ORDER BY supplier")]
    c1, c2 = st.columns([1, 2])
    supplier = c1.selectbox("Proveedor", ["Todos"] + suppliers)
    query = c2.text_input("Buscar folio o proveedor")
    sql = "SELECT * FROM receipts WHERE 1=1"
    params = []
    if supplier != "Todos":
        sql += " AND supplier=?"; params.append(supplier)
    if query:
        sql += " AND (invoice_no LIKE ? OR supplier LIKE ?)"; params.extend([f"%{query}%", f"%{query}%"])
    rows = con.execute(sql + " ORDER BY id DESC", params).fetchall()
    if not rows:
        st.info("Aún no hay documentos que coincidan."); return
    st.dataframe([{"Fecha": r["doc_date"], "Proveedor": r["supplier"], "Folio": r["invoice_no"],
        "Estado": "Repetida · no suma stock" if r["duplicate_of"] else "Ingresada",
        "Total": r["total_amount"], "Archivo": r["filename"]} for r in rows], use_container_width=True, hide_index=True)
    choice = st.selectbox("Ver detalle de factura", rows,
        format_func=lambda r: f"{r['doc_date']} · {r['supplier']} · Folio {r['invoice_no']}" + (" · REPETIDA" if r["duplicate_of"] else ""))
    lines = con.execute("""SELECT l.line_number,l.original_description,l.line_type,p.name AS producto,l.quantity,l.unit_cost,l.line_total
        FROM receipt_lines l LEFT JOIN products p ON p.id=l.product_id WHERE l.receipt_id=? ORDER BY l.line_number""", (choice["id"],)).fetchall()
    if lines:
        st.dataframe([{"Línea": x["line_number"], "Descripción factura": display_product_name(x["original_description"]),
            "Clasificación": x["line_type"], "Producto del catálogo": display_product_name(x["producto"]) if x["producto"] else "—",
            "Cantidad": x["quantity"], "Valor unitario": x["unit_cost"], "Total línea": x["line_total"]}
            for x in lines], use_container_width=True, hide_index=True)
    file_path = docs_dir / (choice["stored_filename"] or "")
    if file_path.is_file():
        st.download_button("Descargar documento original", file_path.read_bytes(), file_name=choice["filename"] or file_path.name)
    if choice["duplicate_of"]:
        st.info(f"Archivada como repetida del registro #{choice['duplicate_of']}; no generó movimientos ni stock.")


def exports(con, root: Path):
    import csv, io, zipfile
    from datetime import datetime
    page_header("Respaldo y exportación", "Descarga una copia del inventario y de sus documentos originales.")
    products = con.execute("""SELECT p.name,p.description,p.category,p.stock,p.min_stock,p.cost,p.margin,
        ROUND(p.cost*(1+p.margin/100)) AS suggested,
        (SELECT group_concat(alias, '; ') FROM product_aliases a WHERE a.product_id=p.id) AS aliases
        FROM products p WHERE p.active=1 AND p.item_type='Mercadería' ORDER BY p.name""").fetchall()
    out = io.StringIO(); writer = csv.writer(out)
    writer.writerow(["Producto", "Descripción", "Categoría", "Nombres alternativos", "Stock", "Stock mínimo", "Costo", "Margen %", "Precio sugerido"])
    writer.writerows([(row["name"], row["description"], row["category"], row["aliases"], row["stock"],
                       row["min_stock"], row["cost"], row["margin"], row["suggested"]) for row in products])
    st.download_button("Descargar inventario en CSV", out.getvalue().encode("utf-8-sig"), "inventario.csv", "text/csv")
    if st.button("Preparar respaldo completo (base + documentos)", type="primary"):
        db_copy = root / "respaldo_temporal.db"
        try:
            backup = sqlite3.connect(db_copy); con.backup(backup); backup.close()
            archive = io.BytesIO()
            with zipfile.ZipFile(archive, "w", zipfile.ZIP_DEFLATED) as z:
                z.write(db_copy, "inventario.db")
                for file in (root / "documentos").glob("*"):
                    if file.is_file(): z.write(file, f"documentos/{file.name}")
            st.session_state["inventory_backup"] = archive.getvalue()
        finally:
            db_copy.unlink(missing_ok=True)
    if "inventory_backup" in st.session_state:
        stamp = datetime.now().strftime("%Y%m%d_%H%M")
        st.download_button("Descargar respaldo ZIP", st.session_state["inventory_backup"], f"respaldo_inventario_{stamp}.zip", "application/zip")


