"""Inventario por facturación · Gioval."""
from pathlib import Path
import streamlit as st

from inventory.database import connect
from inventory.auth import render_login, render_security_sidebar
from inventory.theme import apply_brand
from inventory.ui import dashboard, documents, movements, products

ROOT = Path(__file__).resolve().parent
apply_brand()
if not render_login(ROOT):
    st.stop()
con = connect(ROOT / "inventario.db")
render_security_sidebar(ROOT)

with st.sidebar:
    st.markdown("### 📦 Gioval")
    st.caption("CONTROL DE INVENTARIO")
    st.divider()
    page = st.radio("Secciones", ["Resumen", "Ingresar compras", "Productos", "Movimientos"],
                    label_visibility="collapsed")
    st.divider()
    st.caption("El stock solo cambia cuando confirmas una compra.")

if page == "Resumen":
    dashboard(con)
elif page == "Ingresar compras":
    documents(con, ROOT / "documentos")
elif page == "Productos":
    products(con)
else:
    movements(con)

con.close()
