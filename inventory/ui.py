"""Vistas Streamlit; las reglas de negocio permanecen en servicios separados."""
import uuid
from pathlib import Path
from datetime import date
import streamlit as st

from inventory.database import find_duplicate, record_receipt
from inventory.readers import ai_extract, drafts_from_upload, local_ocr, openai_key
from inventory.theme import page_header
from inventory.text import clean_product_name


def dashboard(con):
    products = con.execute("SELECT * FROM products WHERE active=1 ORDER BY name").fetchall()
    receipts = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NULL").fetchone()["n"]
    duplicates = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NOT NULL").fetchone()["n"]
    page_header("Inventario de mercadería", "Compras recibidas, unidades disponibles y precios sugeridos.")
    a, b, c, d = st.columns(4)
    a.metric("Productos activos", len(products))
    b.metric("Unidades en stock", sum(p["stock"] for p in products))
    c.metric("Facturas registradas", receipts)
    d.metric("Repetidas archivadas", duplicates)
    low_stock = sum(p["stock"] <= 3 for p in products)
    if low_stock:
        st.warning(f"{low_stock} producto(s) tienen 3 unidades o menos.")
    st.subheader("Stock actual")
    if products:
        st.dataframe([{"Producto": p["name"], "Categoría": p["category"] or "—", "Unidades": p["stock"],
            "Costo unitario": f"$ {p['cost']:,}".replace(",", "."), "Margen": f"{p['margin']:g}%",
            "Precio sugerido": f"$ {round(p['cost']*(1+p['margin']/100)):,}".replace(",", ".")}
            for p in products], use_container_width=True, hide_index=True)
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
    page_header("Ingresar compras", "Carga varios documentos y valida cada detalle antes de sumar unidades al stock.")
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
        st.markdown("**Productos recibidos**")
        if any(float(row.get("cantidad") or 0) % 1 for row in rows):
            st.warning("El XML incluye una cantidad fraccionaria. Ajusta manualmente las unidades completas antes de confirmar.")
        edited = []
        for index, row in enumerate(rows):
            with st.container(border=True):
                c1, c2, c3 = st.columns([2.3, .8, 1.15])
                name = c1.text_input("Producto", row.get("nombre", ""), key=f"name_{selected}_{index}")
                quantity = c2.number_input("Unidades", min_value=0, max_value=100000,
                    value=max(0, int(float(row.get("cantidad") or 1))), step=1, key=f"qty_{selected}_{index}")
                cost = c3.number_input("Costo unitario", min_value=0, max_value=100000000,
                    value=max(0, int(float(row.get("costo_unitario") or 0))), step=100, key=f"cost_{selected}_{index}")
                edited.append({"nombre": name, "cantidad": quantity, "costo_unitario": cost})
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
        elif st.button("Confirmar compra y actualizar stock", type="primary", key=f"confirm_{selected}"):
            try:
                if any(not row["nombre"].strip() for row in edited):
                    raise ValueError("Completa el nombre de cada producto.")
                if any(row["cantidad"] <= 0 for row in edited):
                    raise ValueError("Las unidades deben ser mayores que cero.")
                path = docs_dir / f"{uuid.uuid4().hex}_{Path(item['source_name']).name}"
                record_receipt(con, item, edited, path)
                del queue[selected]
                st.success("Compra confirmada y stock actualizado.")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def products(con):
    page_header("Productos", "Administra el catálogo, unidades disponibles, costos y márgenes.")
    with st.expander("＋ Agregar producto"):
        with st.form("new_product"):
            name = st.text_input("Nombre del producto")
            category = st.text_input("Categoría")
            a, b, c = st.columns(3)
            stock = a.number_input("Stock inicial (unidades)", 0, 100000, 0)
            cost = b.number_input("Costo unitario", 0, 100000000, 0)
            margin = c.number_input("Margen sobre costo (%)", 0., 10000., 30.)
            if st.form_submit_button("Guardar producto", type="primary"):
                name = clean_product_name(name)
                if not name:
                    st.error("Escribe el nombre del producto.")
                else:
                    try:
                        with con:
                            con.execute("INSERT INTO products(name,category,stock,cost,margin) VALUES(?,?,?,?,?)",
                                (name.strip(), category.strip(), stock, cost, margin))
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo guardar: {exc}")
    rows = con.execute("SELECT * FROM products WHERE active=1 ORDER BY name").fetchall()
    if not rows:
        st.info("Todavía no hay productos en el catálogo.")
        return
    proposals = [(p["id"], p["name"], clean_product_name(p["name"])) for p in rows]
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
    st.dataframe([{"Producto": p["name"], "Categoría": p["category"] or "—", "Unidades": p["stock"],
        "Costo": p["cost"], "Margen %": p["margin"], "Precio sugerido": round(p["cost"] * (1 + p["margin"] / 100))}
        for p in rows], use_container_width=True, hide_index=True)
    with st.expander("Editar producto"):
        product = st.selectbox("Producto", rows, format_func=lambda p: p["name"])
        with st.form(f"edit_{product['id']}"):
            name = st.text_input("Nombre del producto", product["name"])
            category = st.text_input("Categoría", product["category"] or "")
            a, b, c = st.columns(3)
            stock = a.number_input("Stock (unidades)", 0, 100000, product["stock"])
            cost = b.number_input("Costo", 0, 100000000, product["cost"])
            margin = c.number_input("Margen %", 0., 10000., float(product["margin"]))
            if st.form_submit_button("Guardar cambios", type="primary"):
                name = clean_product_name(name)
                if not name:
                    st.error("El nombre no puede quedar vacío.")
                else:
                    try:
                        with con:
                            con.execute("UPDATE products SET name=?,category=?,stock=?,cost=?,margin=? WHERE id=?",
                                (name, category.strip(), stock, cost, margin, product["id"]))
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo guardar el producto: {exc}")


def movements(con):
    page_header("Movimientos", "Historial de compras confirmadas y cambios de stock.")
    rows = con.execute("""SELECT m.created_at,p.name,r.supplier,r.invoice_no,r.filename,m.quantity,m.unit_cost
        FROM movements m JOIN products p ON p.id=m.product_id JOIN receipts r ON r.id=m.receipt_id ORDER BY m.id DESC""").fetchall()
    if rows:
        st.dataframe([dict(row) for row in rows], use_container_width=True, hide_index=True)
    else:
        st.info("Los ingresos de stock confirmados aparecerán aquí.")
    duplicates = con.execute("""SELECT d.created_at,d.supplier,d.invoice_no,d.filename,
        original.id AS original_id FROM receipts d JOIN receipts original ON original.id=d.duplicate_of
        ORDER BY d.id DESC""").fetchall()
    if duplicates:
        st.subheader("Facturas repetidas archivadas · sin cambios de stock")
        st.dataframe([dict(row) for row in duplicates], use_container_width=True, hide_index=True)
