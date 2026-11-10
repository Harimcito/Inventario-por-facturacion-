"""Sistema visual compartido con Giovalia."""
import streamlit as st


def apply_brand():
    st.set_page_config(
        page_title="Gioval · Inventario", page_icon=":material/inventory_2:",
        layout="wide", initial_sidebar_state="collapsed",
    )
    st.markdown("""
    <style>
      :root { --gioval-blue:#010ED0; --gioval-ink:#1F2937; --gioval-muted:#64748B; }
      .stApp { background:#F5F7FB; color:var(--gioval-ink); }
      [data-testid="stHeader"] { background:rgba(245,247,251,.94); }
      [data-testid="stSidebar"] { background:#fff; border-right:1px solid #DCE3ED; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#475569; }
      .block-container { max-width:1440px; padding:2.55rem clamp(1rem,3vw,2.5rem) 3rem; }
      h1,h2,h3 { color:#172235; letter-spacing:-.025em; }
      h1 { font-size:clamp(1.7rem,3vw,2.25rem)!important; }
      [data-testid="stMetric"] { background:#fff; border:1px solid #DCE3ED; border-radius:10px; padding:1rem 1.15rem; box-shadow:0 1px 2px #0f172a0a; }
      [data-testid="stMetricLabel"] { color:#64748B; }
      [data-testid="stMetricValue"] { color:#172235; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #DCE3ED; border-radius:10px; overflow:hidden; }
      [data-testid="stExpander"] { background:#fff; border:1px solid #DCE3ED; border-radius:10px; }
      .stButton button[kind="primary"] { background:var(--gioval-blue); border-color:var(--gioval-blue); }
      .stButton button { border-radius:6px; }
      .gioval-eyebrow { color:var(--gioval-blue)!important; background:#E9EDFF; display:inline-flex; padding:.25rem .55rem; border-radius:4px; font-size:.72rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.45rem; opacity:1!important; }
      @media(max-width:700px) { .block-container { padding:1.2rem .85rem 2rem; } }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, description: str):
    st.markdown('<div class="gioval-eyebrow">GIOVAL · OPERACIONES</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)
