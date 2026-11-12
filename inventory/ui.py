"""Vistas Streamlit; las reglas de negocio permanecen en servicios separados."""
import uuid
import sqlite3
import html
from difflib import SequenceMatcher
from pathlib import Path
from datetime import date
import streamlit as st

from inventory.database import (find_duplicate, record_receipt, update_product, set_product_classification,
                                normalize_gioval_product_id)
from inventory.readers import ai_extract, drafts_from_upload, local_ocr, openai_key, document_preview
from inventory.theme import page_header, flash_on_next_render
from inventory.text import clean_product_name, normalize_product_key, display_product_name, parse_clp, parse_invoice_quantity
from inventory.classifier import (classify_line, suggest_product_category, LINE_TYPES, MERCHANDISE,
                                  PRODUCT_CATEGORIES, STATIONERY_CATEGORY)


def _go_to_section(section: str):
    st.session_state["app_navigation"] = section


def _go_to_restock():
    st.session_state["products_stock_filter"] = "Requiere reposición"
    st.session_state["app_navigation"] = "Productos"


def _responsive_table(rows, label: str):
    """Tabla fluida en escritorio y tarjetas legibles en pantallas angostas."""
    if not rows:
        return
    columns = list(rows[0].keys())
    header = "".join(f"<th scope=\"col\">{html.escape(str(name))}</th>" for name in columns)
    body = []
    for row in rows:
        cells = "".join(
            f'<td data-label="{html.escape(str(name), quote=True)}">{html.escape(str(row.get(name, "—")))}</td>'
            for name in columns
        )
        body.append(f"<tr>{cells}</tr>")
    st.markdown(
        f'<div class="responsive-table-shell"><table class="responsive-inventory-table" aria-label="{html.escape(label, quote=True)}">'
        f"<thead><tr>{header}</tr></thead><tbody>{''.join(body)}</tbody></table></div>",
        unsafe_allow_html=True,
    )


def dashboard(con):
    products = con.execute("SELECT * FROM products WHERE active=1 AND item_type='Mercadería' ORDER BY name").fetchall()
    receipts = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NULL").fetchone()["n"]
    duplicates = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NOT NULL").fetchone()["n"]
    excluded = con.execute("SELECT COUNT(*) AS n FROM products WHERE active=1 AND item_type<>'Mercadería'").fetchone()["n"]
    inventory_value = sum(int(p["stock"]) * int(p["cost"]) for p in products)
    unit_count = sum(int(p["stock"]) for p in products)
    low_stock = sum(p["stock"] < p["min_stock"] for p in products)
    low_rows = sorted((p for p in products if p["stock"] < p["min_stock"]),
                      key=lambda p: (p["stock"] - p["min_stock"], p["name"]))
    month_key = date.today().strftime("%Y-%m")
    month_receipts = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NULL AND substr(doc_date,1,7)=?", (month_key,)).fetchone()["n"]
    pending_docs = len(st.session_state.get("queue", {}))
    category_totals = {}
    for product in products:
        category = product["category"] or "Sin categoría"
        category_totals[category] = category_totals.get(category, 0) + int(product["stock"])
    largest_category = max(category_totals.values(), default=0)
    category_bars = "".join(
        f'<div class="ops-category"><span>{html.escape(category)}</span><span>{units} u.</span>'
        f'<div class="ops-bar"><i style="width:{round(units / largest_category * 100) if largest_category else 0}%"></i></div></div>'
        for category, units in sorted(category_totals.items(), key=lambda item: (-item[1], item[0]))[:3]
    )
    value_label = f"$ {inventory_value:,}".replace(",", ".")
    st.markdown(f'''<section class="ops-hero">
      <div class="ops-hero-copy"><div class="ops-kicker"><span>GIOVAL</span> / CONTROL DE INVENTARIO</div>
        <h2>Tu inventario,<br><em>paso a paso.</em></h2>
        <p>Carga una factura, revisa los productos y confirma para actualizar las existencias.</p>
        <div class="ops-flow"><div class="flow-step"><b>01</b><span>Facturas</span><strong>{month_receipts}</strong></div><i></i><div class="flow-step{' is-active' if pending_docs else ''}"><b>02</b><span>Por revisar</span><strong>{pending_docs}</strong></div><i></i><div class="flow-step"><b>03</b><span>Unidades</span><strong>{unit_count}</strong></div></div>
      </div>
      <div class="ops-hero-data"><div class="ops-value-label">VALOR DE COMPRA DEL INVENTARIO</div>
        <div class="ops-value">{value_label}</div><div class="ops-value-note">{unit_count:,} unidades · {len(products)} productos</div>
        <div class="ops-category-head">UNIDADES POR CATEGORÍA</div>{category_bars or '<div class="ops-empty-category">Tus categorías aparecerán aquí.</div>'}
      </div>
    </section>''', unsafe_allow_html=True)
    quick_a, quick_b, note = st.columns([1.1, 1, 1.4], vertical_alignment="center")
    if quick_a.button("Cargar facturas", type="primary", use_container_width=True,
                      on_click=_go_to_section, args=("Ingresar facturas",)):
        pass
    if quick_b.button("Ver inventario", use_container_width=True,
                      on_click=_go_to_section, args=("Productos",)):
        pass
    note.caption(f"{month_receipts} factura(s) este mes · {pending_docs} en revisión · {low_stock} alerta(s) de stock bajo")

    st.markdown('<div class="ops-sectionline"><span>VISTA GENERAL</span><i></i><small>POSICIÓN ACTUAL DEL INVENTARIO</small></div>', unsafe_allow_html=True)
    a, b, c, d = st.columns(4)
    a.metric("Productos en inventario", len(products))
    b.metric("Unidades disponibles", unit_count)
    c.metric("Costo total del inventario", value_label)
    d.metric("Facturas guardadas", receipts)
    if excluded:
        st.caption(f"{excluded} servicios, comisiones y ajustes se conservan en sus facturas, fuera del stock.")
    if duplicates:
        st.caption(f"{duplicates} documento(s) repetido(s) archivado(s), sin alterar el inventario.")
    if low_rows:
        restock_units = sum(max(0, int(p["min_stock"]) - int(p["stock"])) for p in low_rows)
        restock_cost = sum(max(0, int(p["min_stock"]) - int(p["stock"])) * int(p["cost"]) for p in low_rows)
        format_clp = lambda amount: f"$ {amount:,}".replace(",", ".")
        restock_rows = "".join(
            f'<div class="restock-row"><span class="restock-dot"></span><span class="restock-name">{html.escape(display_product_name(p["name"]))}</span>'
            f'<span class="restock-current">{int(p["stock"])} / {int(p["min_stock"])} u.</span>'
            f'<span class="restock-count">+{max(0, int(p["min_stock"]) - int(p["stock"]))} u.<small>{format_clp(max(0, int(p["min_stock"]) - int(p["stock"])) * int(p["cost"]))}</small></span></div>'
            for p in low_rows[:6]
        )
        more_items = f'<div class="attention-foot">Y {len(low_rows) - 6} producto(s) más en la lista de reposición.</div>' if len(low_rows) > 6 else ""
        st.markdown(f'''<section class="ops-attention"><div class="attention-head"><div>
          <span class="attention-kicker">SEÑAL DE REPOSICIÓN</span><h3>{low_stock} producto(s) necesitan atención</h3>
          <div class="restock-summary">Para llegar al mínimo: <strong>{restock_units} unidades</strong><i>·</i> costo referencial <strong>{format_clp(restock_cost)}</strong></div>
          </div><span class="attention-count">{low_stock:02d}</span></div>
          <div class="restock-list">{restock_rows}</div>
          {more_items}<div class="attention-foot">Estimación al costo unitario registrado; no modifica el stock.</div></section>''', unsafe_allow_html=True)
        if st.button("Revisar reposiciones", key="open_restock", on_click=_go_to_restock):
            pass
    else:
        st.markdown('<div class="ops-attention is-clear"><div><span class="attention-kicker">SEÑAL DE REPOSICIÓN</span><h3>Todo al día</h3><p>Ningún producto está bajo su mínimo.</p></div><span class="clear-mark">✓</span></div>', unsafe_allow_html=True)
    st.subheader("Productos en inventario")
    if products:
        s1, s2 = st.columns([2, 1])
        search = s1.text_input("Buscar producto", placeholder="Nombre, marca o variante", key="dashboard_product_search")
        categories = sorted({p["category"] for p in products if p["category"]})
        category = s2.selectbox("Categoría", ["Todas"] + categories, key="dashboard_product_category")
        visible = [p for p in products if (not search or search.casefold() in (p["name"] + " " + (p["description"] or "")).casefold())
                   and (category == "Todas" or p["category"] == category)]
        st.caption(f"Mostrando {len(visible)} de {len(products)} productos inventariables")
        _responsive_table([{"Producto": display_product_name(p["name"]), "Categoría": p["category"] or "—", "Unidades": p["stock"],
            "Costo unitario": f"$ {p['cost']:,}".replace(",", "."), "Margen": f"{p['margin']:g}%",
            "Precio sugerido": f"$ {round(p['cost']*(1+p['margin']/100)):,}".replace(",", ".")}
            for p in visible], "Stock actual")
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
    page_header("Cargar facturas y boletas", "Selecciona los documentos, revisa sus productos y guarda para actualizar el inventario.")
    queue = st.session_state.setdefault("queue", {})
    with st.expander("Importar archivo de respaldo del SII", expanded=False):
        st.markdown("**Importación oficial de facturas recibidas**")
        st.write("El SII permite generar un archivo de respaldo XML con DTE recibidos. Descárgalo en el portal y súbelo aquí: cada factura se separará para revisar sus productos.")
        st.link_button("Abrir guía oficial del SII", "https://www.sii.cl/destacados/factura_electronica/guias_ayuda/como_generar_archivo_respaldo.htm")
        st.caption("Ruta: Oficina Virtual → Factura Electrónica → Historial de DTE recibidos → Archivo Respaldo (XML). Esta app no guarda tu Clave Tributaria.")
        st.info("El SII no publica una API abierta para descargar automáticamente todas las facturas entrantes. La importación usa el respaldo XML oficial y evita automatizaciones frágiles del portal.")

    ai_key = openai_key() or st.session_state.get("openai_key", "")
    with st.expander("Lectura automática del documento", expanded=False):
        st.caption("La IA puede leer PDF e imágenes. El XML del SII se interpreta localmente sin consumir API.")
        typed_key = st.text_input("API key de OpenAI (opcional)", value="", type="password", placeholder="Se usa solo durante esta sesión")
        if typed_key:
            st.session_state["openai_key"] = typed_key.strip()
            ai_key = typed_key.strip()
        if ai_key:
            st.success("Lectura con IA disponible")
        else:
            st.caption("Agrega aquí tu API key o configura OPENAI_API_KEY en el equipo.")

    uploads = st.file_uploader("Selecciona facturas, boletas o un archivo del SII",
        type=["pdf", "png", "jpg", "jpeg", "xml"], accept_multiple_files=True,
        help="Puedes seleccionar varias facturas; los respaldos XML se dividen por DTE.")
    if uploads and st.button(f"Revisar documentos ({len(uploads)})", type="primary"):
        queue = st.session_state.setdefault("queue", {})
        for error in _add_uploads(uploads, queue):
            st.error(error)
        if queue:
            flash_on_next_render(f"{len(queue)} documento(s) listo(s) para revisar", "📄")
        st.rerun()

    pending = len(queue)
    duplicate_pending = sum(find_duplicate(con, draft) is not None for draft in queue.values())
    receipts_total = con.execute("SELECT COUNT(*) AS n FROM receipts WHERE duplicate_of IS NULL").fetchone()["n"]
    inventory_count = con.execute("SELECT COUNT(*) AS n FROM products WHERE active=1 AND item_type='Mercadería'").fetchone()["n"]
    s1_state = "done" if pending else "active"
    s2_state = "active" if pending else "waiting"
    s3_state = "done" if receipts_total else "waiting"
    st.markdown(f'''<div class="intake-flow">
      <div class="intake-step {s1_state}"><b>01</b><span class="intake-icon">↑</span><div><small>ETAPA 01</small><strong>Agregar archivos</strong><em>PDF · XML · imagen</em></div></div>
      <span class="intake-connector"></span>
      <div class="intake-step {s2_state}"><b>02</b><span class="intake-icon">⌕</span><div><small>ETAPA 02</small><strong>Revisar contenido</strong><em>{pending} pendiente(s)</em></div></div>
      <span class="intake-connector"></span>
      <div class="intake-step {s3_state}"><b>03</b><span class="intake-icon">▦</span><div><small>ETAPA 03</small><strong>Actualizar stock</strong><em>{inventory_count} productos activos</em></div></div>
    </div>''', unsafe_allow_html=True)
    if not queue:
        st.markdown('<div class="intake-empty"><span class="empty-mark">01</span><div><strong>Todo comienza con el documento.</strong><p>Selecciona una o varias facturas arriba. Se separarán para que puedas revisar cada una antes de modificar el inventario.</p></div></div>', unsafe_allow_html=True)
        return
    message = f"{pending} documento(s) en la bandeja · {duplicate_pending} repetido(s) detectado(s)" if duplicate_pending else f"{pending} documento(s) en la bandeja · cada factura se confirma por separado"
    st.markdown(f'<div class="intake-queue"><span class="queue-live"></span><strong>{message}</strong><small>El stock no cambia hasta confirmar la revisión.</small></div>', unsafe_allow_html=True)
    queue_names = list(queue)
    queue_position = {name: index + 1 for index, name in enumerate(queue_names)}
    selected = st.selectbox("Factura que estás revisando", queue_names,
        format_func=lambda name: f"{queue_position[name]} de {len(queue_names)} · {name}")
    item = queue[selected]
    original, review = st.columns([.85, 1.35], gap="large")
    with original:
        st.subheader("Documento original")
        if item["source_name"].lower().endswith((".jpg", ".jpeg", ".png", ".pdf")):
            try:
                preview, page_count = document_preview(item["bytes"], item["source_name"])
                st.image(preview, use_container_width=True)
                if page_count > 1:
                    st.caption(f"Vista previa de la página 1 de {page_count}.")
            except Exception as exc:
                st.warning(f"No pude mostrar una vista previa: {str(exc)[:160]}")
            st.download_button("Descargar archivo original", item["bytes"], file_name=item["source_name"])
        else:
            st.download_button("Descargar archivo original", item["bytes"], file_name=item["source_name"])
        if item.get("dte"):
            st.success("Datos del DTE extraídos desde XML en este equipo.")
            st.caption(f"RUT: {item.get('rut') or '—'} · Tipo DTE: {item.get('kind') or '—'} · Total declarado: $ {item.get('total') or '—'}")
        else:
            engine = st.radio("Cómo leer el documento", ["OpenAI", "OCR local"], horizontal=True,
                              format_func=lambda value: {"OpenAI": "IA de OpenAI", "OCR local": "Lectura en este equipo"}[value],
                              index=0 if ai_key else 1, key=f"engine_{selected}",
                              help="La lectura en este equipo no envía el documento a internet.")
            if st.button("Leer datos de esta factura", key=f"read_{selected}", disabled=engine == "OpenAI" and not ai_key):
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
                            st.session_state[f"qty_{selected}_{index}"] = max(0.0, parse_invoice_quantity(row.get("cantidad", 0)))
                            st.session_state[f"cost_{selected}_{index}"] = max(0, parse_clp(row.get("costo_unitario", 0)))
                        flash_on_next_render("Lectura lista: revisa los datos antes de confirmar", "✨")
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
        st.subheader("Revisa los datos")
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
                quantity = c1.number_input("Unidades/cantidad", min_value=0.0, max_value=100000.0,
                    value=max(0.0, parse_invoice_quantity(row.get("cantidad", 1))), step=1.0, key=f"qty_{selected}_{index}")
                cost = c2.number_input("Valor unitario", min_value=0, max_value=100000000,
                    value=max(0, parse_clp(row.get("costo_unitario", 0))), step=100, key=f"cost_{selected}_{index}")
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
                    mapping = st.selectbox("¿A qué producto del inventario corresponde?", options,
                        index=options.index(default_id) if default_id in options else 0,
                        format_func=lambda pid: "Crear producto nuevo" if pid is None else next(
                            f"{p['name']} · {p['category']}" if p["category"] else p["name"]
                            for p in catalog if p["id"] == pid),
                        key=f"mapping_{selected}_{index}")
                    if mapping is None:
                        st.caption("Si confirmas, esta línea creará un producto nuevo en el catálogo.")
                    elif normalize_product_key(name) != normalize_product_key(next(p["name"] for p in catalog if p["id"] == mapping)):
                        st.caption("Al confirmar, este nombre de factura se guardará como alias para facilitar futuras coincidencias.")
                    mapped_product = next((p for p in catalog if p["id"] == mapping), None)
                    if mapped_product and cost > 0 and mapped_product["cost"] > 0:
                        low, high = sorted((int(cost), int(mapped_product["cost"])))
                        if high >= low * 3:
                            invoice_cost = f"$ {int(cost):,}".replace(",", ".")
                            current_cost = f"$ {int(mapped_product['cost']):,}".replace(",", ".")
                            st.warning(
                                f"El costo de esta factura ({invoice_cost}) difiere mucho del costo actual de "
                                f"{mapped_product['name']} ({current_cost}). Verifica que sea la misma variante antes de confirmar."
                            )
                else:
                    st.info("Se conservará en el detalle de la factura y no se ingresará al stock.")
                if selected_type == MERCHANDISE and not float(quantity).is_integer():
                    st.warning("El inventario usa unidades enteras. Ajusta esta cantidad antes de confirmar, o clasifica la línea como no inventariable.")
                edited.append({"nombre": name, "cantidad": quantity, "costo_unitario": cost,
                               "product_id": mapping, "line_type": selected_type})
        item["supplier"], item["number"], item["date"], item["items"] = supplier, number, doc_date, edited
        add, remove_line, remove = st.columns(3)
        if add.button("＋ Agregar producto", key=f"add_{selected}"):
            item["items"].append({"nombre": "", "cantidad": 1, "costo_unitario": 0})
            flash_on_next_render("Línea nueva lista para completar", "➕")
            st.rerun()
        if remove_line.button("− Quitar última línea", key=f"remove_line_{selected}", disabled=len(edited) <= 1):
            item["items"] = edited[:-1]
            flash_on_next_render("Se quitó la última línea de esta revisión", "↩️")
            st.rerun()
        if remove.button("Quitar documento", key=f"remove_{selected}"):
            del queue[selected]
            flash_on_next_render("Documento quitado de la cola de revisión", "🗑️")
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
                    flash_on_next_render("Copia archivada. El stock quedó sin cambios", "🗂️")
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
                flash_on_next_render(f"Factura ingresada · {merchandise_count} línea(s) de mercadería sumaron al stock", "📦")
                st.rerun()
            except Exception as exc:
                st.error(str(exc))


def products(con):
    page_header("Inventario", "Busca productos y revisa o cambia las cantidades, costos y precios.")
    with st.expander("＋ Agregar producto"):
        with st.form("new_product"):
            name = st.text_input("Nombre del producto")
            category = st.selectbox("Categoría", PRODUCT_CATEGORIES,
                                    index=PRODUCT_CATEGORIES.index(STATIONERY_CATEGORY))
            description = st.text_input("Descripción / formato / variante", placeholder="Ej.: sabor, tamaño, color o presentación")
            gioval_product_id = st.text_input("ID global de Gioval (opcional)",
                help="Pégalo solo después de confirmar que es el mismo producto y variante en la ficha maestra de Gioval. No se asigna por coincidencia de nombre o alias.")
            a, b, c = st.columns(3)
            stock = a.number_input("Stock inicial (unidades)", 0, 100000, 0)
            cost = b.number_input("Costo unitario", 0, 100000000, 0)
            margin = c.number_input("Margen sobre costo (%)", 0., 10000., 30., help="El precio se calcula como costo × (1 + margen/100).")
            min_stock = st.number_input("Avisarme al llegar a (unidades)", 0, 100000, 3)
            st.caption(f"Precio sugerido con estos valores: $ {round(cost * (1 + margin / 100)):,}".replace(",", "."))
            if st.form_submit_button("Guardar producto", type="primary"):
                name = clean_product_name(name)
                if not name:
                    st.error("Escribe el nombre del producto.")
                else:
                    try:
                        gioval_id = normalize_gioval_product_id(gioval_product_id)
                        with con:
                            con.execute("INSERT INTO products(name,category,description,stock,cost,margin,min_stock,gioval_product_id) VALUES(?,?,?,?,?,?,?,?)",
                                (name.strip(), category.strip(), description.strip(), stock, cost, margin, min_stock, gioval_id))
                        flash_on_next_render(f"{name.strip()} quedó agregado al catálogo", "✨")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo guardar: {exc}")
    all_active = con.execute("SELECT * FROM products WHERE active=1 ORDER BY name").fetchall()
    cost_alerts = con.execute("""SELECT p.id,p.name,MIN(m.unit_cost) AS min_cost,MAX(m.unit_cost) AS max_cost,
        COUNT(*) AS purchases FROM products p JOIN movements m ON m.product_id=p.id
        WHERE p.active=1 AND p.item_type='Mercadería' AND m.unit_cost>0
        GROUP BY p.id HAVING MAX(m.unit_cost)>=MIN(m.unit_cost)*3 ORDER BY p.name""").fetchall()
    if cost_alerts:
        with st.expander(f"Revisar costos o variantes ({len(cost_alerts)})", expanded=True):
            st.caption("Hay productos con compras registradas a precios muy distintos. Puede ser una lectura incorrecta o variantes que conviene separar; revisa antes de editar el costo actual.")
            st.dataframe([{"Producto": display_product_name(p["name"]),
                "Costo menor registrado": f"$ {int(p['min_cost']):,}".replace(",", "."),
                "Costo mayor registrado": f"$ {int(p['max_cost']):,}".replace(",", "."),
                "Compras": p["purchases"]} for p in cost_alerts], width="stretch", height="auto", row_height=42, hide_index=True)
    uncategorized = [(p, suggest_product_category(p["name"])) for p in all_active
                     if p["item_type"] == MERCHANDISE and not p["category"] and suggest_product_category(p["name"])]
    if uncategorized:
        with st.expander(f"Completar categorías del catálogo ({len(uncategorized)})", expanded=False):
            st.dataframe([{"Producto": display_product_name(p["name"]), "Categoría sugerida": category}
                          for p, category in uncategorized], width="stretch", height="auto", row_height=42, hide_index=True)
            if st.button("Aplicar categorías sugeridas", key="apply_product_categories"):
                with con:
                    for p, category in uncategorized:
                        con.execute("UPDATE products SET category=? WHERE id=? AND (category IS NULL OR category='')",
                                    (category, p["id"]))
                flash_on_next_render(f"Categorías completadas para {len(uncategorized)} producto(s)", "🏷️")
                st.rerun()
    suggested = [(p, *classify_line(p["name"])) for p in all_active
                 if p["item_type"] == MERCHANDISE and classify_line(p["name"])[0] != MERCHANDISE]
    if suggested:
        with st.expander(f"Revisar conceptos que parecen servicios o cargos ({len(suggested)})", expanded=True):
            st.caption("La app conserva la factura, pero estos conceptos no deberían contar como mercadería. Aplicar la sugerencia deja su saldo en cero y registra el ajuste.")
            st.dataframe([{"Descripción detectada": display_product_name(p["name"]), "Tipo sugerido": kind,
                "Unidades a retirar del stock": p["stock"], "Motivo": reason} for p, kind, reason in suggested],
                width="stretch", height="auto", row_height=42, hide_index=True)
            if st.button(f"Aplicar las sugerencias a {len(suggested)} concepto(s)", type="primary", key="classify_existing_nonstock"):
                for p, kind, _ in suggested:
                    set_product_classification(con, p["id"], kind)
                flash_on_next_render("Conceptos reclasificados y cambios guardados en el historial", "🧹")
                st.rerun()
    noninventory = [p for p in all_active if p["item_type"] != MERCHANDISE]
    if noninventory:
        with st.expander(f"Conceptos excluidos del inventario ({len(noninventory)})", expanded=False):
            st.dataframe([{"Descripción": display_product_name(p["name"]), "Clasificación": p["item_type"]}
                          for p in noninventory], width="stretch", height="auto", row_height=42, hide_index=True)
            noninventory_by_id = {int(product["id"]): product for product in noninventory}
            selected_noninventory_id = st.selectbox("Reincorporar como mercadería", list(noninventory_by_id),
                format_func=lambda product_id: display_product_name(noninventory_by_id[product_id]["name"]),
                key="reinclude_noninventory")
            if st.button("Reincorporar al inventario", key="reinclude_inventory_item"):
                set_product_classification(con, selected_noninventory_id, MERCHANDISE)
                flash_on_next_render("Producto reincorporado al inventario", "📦")
                st.rerun()
    rows = [p for p in all_active if p["item_type"] == MERCHANDISE]
    if not rows:
        st.info("Todavía no hay mercadería en el catálogo. Puedes agregar productos o reincorporar uno excluido.")
        return
    f_search, f_category, f_stock = st.columns([1.5, 1, 1])
    catalog_search = f_search.text_input("Buscar producto", placeholder="Nombre, descripción o marca", key="products_catalog_search")
    categories = sorted({p["category"] for p in rows if p["category"]})
    catalog_category = f_category.selectbox("Categoría", ["Todas"] + categories, key="products_catalog_category")
    stock_filter = f_stock.selectbox("Disponibilidad", ["Todas", "Requiere reposición", "Sobre el mínimo"],
        format_func=lambda value: {"Todas": "Todos", "Requiere reposición": "Necesita reposición", "Sobre el mínimo": "Stock suficiente"}[value],
        key="products_stock_filter")
    if catalog_search:
        query = catalog_search.casefold()
        rows = [p for p in rows if query in (p["name"] + " " + (p["description"] or "") + " " + (p["category"] or "")).casefold()]
    if catalog_category != "Todas":
        rows = [p for p in rows if p["category"] == catalog_category]
    if stock_filter == "Requiere reposición":
        rows = [p for p in rows if p["stock"] < p["min_stock"]]
    elif stock_filter == "Sobre el mínimo":
        rows = [p for p in rows if p["stock"] > p["min_stock"]]
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
            st.dataframe([{"Actual": old, "Corregido": new} for _, old, new in changes], width="stretch", height="auto", row_height=42, hide_index=True)
            if conflicts:
                st.warning("Algunos nombres coincidirían con otro producto y no se cambiarán automáticamente.")
            if safe_changes and st.button(f"Aplicar {len(safe_changes)} corrección(es)", key="clean_product_names"):
                with con:
                    for pid, _, new in safe_changes:
                        con.execute("UPDATE products SET name=? WHERE id=?", (new, pid))
                flash_on_next_render(f"{len(safe_changes)} descripción(es) normalizadas; el stock no cambió", "✍️")
                st.rerun()
    _responsive_table([{"Producto": display_product_name(p["name"]), "Descripción / variante": p["description"] or "—",
        "Categoría": p["category"] or "—", "Unidades": p["stock"], "Mínimo": p["min_stock"],
        "Margen": f"{p['margin']:g}%",
        "Costo unitario": f"$ {p['cost']:,}".replace(",", "."),
        "Precio sugerido": f"$ {round(p['cost'] * (1 + p['margin'] / 100)):,}".replace(",", ".")}
        for p in rows], "Catálogo de productos")
    with st.expander("Editar los datos de un producto"):
        products_by_id = {int(p["id"]): p for p in rows}
        selected_product_id = st.selectbox("Producto", list(products_by_id),
            format_func=lambda product_id: display_product_name(products_by_id[product_id]["name"]))
        product = products_by_id[selected_product_id]
        with st.form(f"edit_{product['id']}"):
            name = st.text_input("Nombre del producto", product["name"])
            category = st.selectbox("Categoría", PRODUCT_CATEGORIES,
                index=PRODUCT_CATEGORIES.index(product["category"])
                    if product["category"] in PRODUCT_CATEGORIES
                    else PRODUCT_CATEGORIES.index(STATIONERY_CATEGORY))
            description = st.text_input("Descripción / formato / variante", product["description"] or "")
            gioval_product_id = st.text_input("ID global de Gioval (opcional)", product["gioval_product_id"] or "",
                help="Pégalo solo después de confirmar que es el mismo producto y variante en la ficha maestra de Gioval. Borrar el campo quita el vínculo.")
            current_aliases = [r[0] for r in con.execute("SELECT alias FROM product_aliases WHERE product_id=? ORDER BY alias", (product["id"],))]
            aliases_text = st.text_input("Nombres alternativos de proveedores (separados por coma)", ", ".join(current_aliases),
                help="Se usarán para reconocer este producto en próximas facturas.")
            a, b, c = st.columns(3)
            stock = a.number_input("Stock (unidades)", 0, 100000, product["stock"])
            cost = b.number_input("Costo", 0, 100000000, product["cost"])
            margin = c.number_input("Margen sobre costo (%)", 0., 10000., float(product["margin"]),
                help="El precio sugerido se calcula como costo × (1 + margen/100).")
            min_stock = st.number_input("Avisarme al llegar a (unidades)", 0, 100000, int(product["min_stock"]))
            st.caption(f"Precio sugerido actual: $ {round(cost * (1 + margin / 100)):,}".replace(",", "."))
            reason = st.text_input("Motivo del ajuste de stock", placeholder="Recuento, merma, consumo…")
            if st.form_submit_button("Guardar cambios", type="primary"):
                name = clean_product_name(name)
                if not name:
                    st.error("El nombre no puede quedar vacío.")
                else:
                    try:
                        aliases = [alias.strip() for alias in aliases_text.split(",") if alias.strip()]
                        update_product(con, product["id"], name, category, stock, cost, margin, min_stock, reason, description, aliases,
                                       gioval_product_id=gioval_product_id)
                        flash_on_next_render(f"Cambios de {name} guardados", "💾")
                        st.rerun()
                    except Exception as exc:
                        st.error(f"No se pudo guardar el producto: {exc}")


def movements(con):
    page_header("Entradas y ajustes", "Revisa las facturas que ingresaron productos y los cambios manuales de stock.")
    rows = con.execute("""SELECT m.created_at,p.name,r.supplier,r.invoice_no,r.filename,m.quantity,m.unit_cost
        FROM movements m JOIN products p ON p.id=m.product_id JOIN receipts r ON r.id=m.receipt_id
        WHERE p.item_type='Mercadería' ORDER BY m.id DESC""").fetchall()
    if rows:
        st.dataframe([dict(row) for row in rows], width="stretch", height="auto", row_height=42, hide_index=True)
    else:
        st.info("Los ingresos de stock confirmados aparecerán aquí.")
    adjustments = con.execute("""SELECT a.created_at,p.name,a.old_stock,a.new_stock,a.delta,a.reason
        FROM inventory_adjustments a JOIN products p ON p.id=a.product_id ORDER BY a.id DESC""").fetchall()
    st.subheader("Ajustes manuales de stock")
    if adjustments:
        st.dataframe([dict(row) for row in adjustments], width="stretch", height="auto", row_height=42, hide_index=True)
    else:
        st.caption("Los cambios manuales quedarán registrados aquí con su motivo.")
    duplicates = con.execute("""SELECT d.created_at,d.supplier,d.invoice_no,d.filename,
        original.id AS original_id FROM receipts d JOIN receipts original ON original.id=d.duplicate_of
        ORDER BY d.id DESC""").fetchall()
    if duplicates:
        st.subheader("Facturas repetidas archivadas · sin cambios de stock")
        st.dataframe([dict(row) for row in duplicates], width="stretch", height="auto", row_height=42, hide_index=True)


def receipts(con, docs_dir: Path):
    page_header("Historial de facturas", "Busca documentos guardados y revisa los productos de cada factura.")
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
        "Total": r["total_amount"], "Archivo": r["filename"]} for r in rows], width="stretch", height="auto", row_height=42, hide_index=True)
    receipts_by_id = {int(r["id"]): r for r in rows}
    selected_receipt_id = st.selectbox("Ver detalle de factura", list(receipts_by_id),
        format_func=lambda receipt_id: f"{receipts_by_id[receipt_id]['doc_date']} · {receipts_by_id[receipt_id]['supplier']} · Folio {receipts_by_id[receipt_id]['invoice_no']}" + (" · REPETIDA" if receipts_by_id[receipt_id]["duplicate_of"] else ""))
    choice = receipts_by_id[selected_receipt_id]
    lines = con.execute("""SELECT l.line_number,l.original_description,l.line_type,p.name AS producto,l.quantity,l.unit_cost,l.line_total
        FROM receipt_lines l LEFT JOIN products p ON p.id=l.product_id WHERE l.receipt_id=? ORDER BY l.line_number""", (choice["id"],)).fetchall()
    if lines:
        st.dataframe([{"Línea": x["line_number"], "Descripción factura": display_product_name(x["original_description"]),
            "Clasificación": x["line_type"], "Producto del catálogo": display_product_name(x["producto"]) if x["producto"] else "—",
            "Cantidad": x["quantity"], "Valor unitario": x["unit_cost"], "Total línea": x["line_total"]}
            for x in lines], width="stretch", height="auto", row_height=42, hide_index=True)
    file_path = docs_dir / (choice["stored_filename"] or "")
    if file_path.is_file():
        st.download_button("Descargar documento original", file_path.read_bytes(), file_name=choice["filename"] or file_path.name)
    if choice["duplicate_of"]:
        st.info(f"Archivada como repetida del registro #{choice['duplicate_of']}; no generó movimientos ni stock.")


def exports(con, root: Path):
    import csv, io, zipfile
    from datetime import datetime
    page_header("Copias de seguridad", "Descarga una copia para guardar tus productos y documentos.")
    products = con.execute("""SELECT p.name,p.description,p.category,p.gioval_product_id,p.stock,p.min_stock,p.cost,p.margin,
        ROUND(p.cost*(1+p.margin/100)) AS suggested,
        (SELECT group_concat(alias, '; ') FROM product_aliases a WHERE a.product_id=p.id) AS aliases
        FROM products p WHERE p.active=1 AND p.item_type='Mercadería' ORDER BY p.name""").fetchall()
    out = io.StringIO(); writer = csv.writer(out)
    writer.writerow(["Producto", "Descripción", "Categoría", "ID global Gioval", "Nombres alternativos", "Stock", "Stock mínimo", "Costo", "Margen %", "Precio sugerido"])
    writer.writerows([(row["name"], row["description"], row["category"], row["gioval_product_id"], row["aliases"], row["stock"],
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


