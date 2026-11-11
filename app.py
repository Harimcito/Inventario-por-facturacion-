"""Inventario por facturación · Gioval."""
from pathlib import Path
import importlib
import streamlit as st

from inventory import text as inventory_text
from inventory import classifier as inventory_classifier
from inventory import database as inventory_database
from inventory import readers as inventory_readers
from inventory import auth as inventory_auth
from inventory import theme as inventory_theme
from inventory import ui as inventory_ui

# Ensure edited service modules are picked up during Streamlit's in-place rerun.
for module in (inventory_text, inventory_classifier, inventory_database,
               inventory_readers, inventory_auth, inventory_theme, inventory_ui):
    importlib.reload(module)

from inventory.database import connect
from inventory.auth import render_login, render_security_sidebar
from inventory.theme import apply_brand, show_flash, brand_lockup
from inventory.ui import dashboard, documents, movements, products, receipts, exports

ROOT = Path(__file__).resolve().parent
apply_brand()
if not render_login(ROOT):
    st.stop()
show_flash()
con = connect(ROOT / "inventario.db")
render_security_sidebar(ROOT)

with st.sidebar:
    brand_lockup("OPERACIONES")
    st.divider()
    sections = ["Resumen", "Ingresar facturas", "Facturas", "Productos", "Movimientos", "Respaldo"]
    icons = {"Resumen": "◈", "Ingresar facturas": "＋", "Facturas": "▤",
             "Productos": "▦", "Movimientos": "↕", "Respaldo": "⇩"}
    page = st.radio("Secciones", sections,
                    format_func=lambda section: f"{icons[section]}   {section}",
                    label_visibility="collapsed")
    st.divider()
    st.caption("Solo las líneas clasificadas como mercadería ingresan al stock.")

if page == "Resumen":
    dashboard(con)
elif page == "Ingresar facturas":
    documents(con, ROOT / "documentos")
elif page == "Facturas":
    receipts(con, ROOT / "documentos")
elif page == "Productos":
    products(con)
elif page == "Respaldo":
    exports(con, ROOT)
else:
    movements(con)

con.close()

