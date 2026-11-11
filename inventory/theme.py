"""Sistema visual compartido con Giovalia."""
import streamlit as st


def apply_brand():
    st.set_page_config(
        page_title="Gioval · Inventario", page_icon=":material/inventory_2:",
        layout="wide", initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
      :root { --gioval-blue:#010ED0; --gioval-ink:#1F2937; --gioval-muted:#64748B; }
      .stApp { background:#F5F7FB; color:var(--gioval-ink); }
      [data-testid="stHeader"] { background:rgba(245,247,251,.94); }
      [data-testid="stSidebar"] { background:#fff; border-right:1px solid #DCE3ED; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#475569; }
      .block-container { max-width:1480px; padding:2.2rem clamp(1rem,3vw,2.5rem) 3.25rem; }
      h1,h2,h3 { color:#172235; letter-spacing:-.025em; }
      h1 { font-size:clamp(1.7rem,3vw,2.25rem)!important; line-height:1.15!important; margin:.2rem 0 .4rem!important; }
      h2 { font-size:1.35rem!important; margin-top:1.8rem!important; }
      h3 { font-size:1.08rem!important; }
      [data-testid="stCaptionContainer"] { color:#64748B; }
      [data-testid="stMetric"] { background:#fff; border:1px solid #DCE3ED; border-radius:12px; padding:1.05rem 1.15rem; box-shadow:0 2px 5px #0f172a08; min-height:106px; }
      [data-testid="stMetricLabel"] { color:#64748B; font-size:.84rem; }
      [data-testid="stMetricValue"] { color:#172235; font-weight:700; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #DCE3ED; border-radius:10px; overflow:hidden; background:#fff; }
      [data-testid="stExpander"] { background:#fff; border:1px solid #DCE3ED; border-radius:10px; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius:12px; }
      [data-testid="stAlert"] { border-radius:10px; }
      .stButton button, .stDownloadButton button { border-radius:8px; min-height:42px; font-weight:600; transition:box-shadow .15s ease, transform .15s ease; }
      .stButton button:hover, .stDownloadButton button:hover { box-shadow:0 3px 10px #0f172a18; transform:translateY(-1px); }
      .stButton button[kind="primary"] { background:var(--gioval-blue); border-color:var(--gioval-blue); }
      [data-testid="stSidebar"] [role="radiogroup"] label { border-radius:8px; padding:.3rem .45rem; }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#F1F4FF; }
      input:focus, textarea:focus { border-color:var(--gioval-blue)!important; box-shadow:0 0 0 2px #010ED01f!important; }
      .gioval-eyebrow { color:var(--gioval-blue)!important; background:#E9EDFF; display:inline-flex; padding:.25rem .55rem; border-radius:4px; font-size:.72rem; font-weight:750; letter-spacing:.1em; text-transform:uppercase; margin-bottom:.45rem; opacity:1!important; }
      @media(max-width:900px) { .block-container { padding:1.45rem 1rem 2.25rem; } [data-testid="stMetric"] { min-height:92px; padding:.85rem; } }
      @media(max-width:700px) { .block-container { padding:1.15rem .75rem 1.75rem; } h2 { font-size:1.2rem!important; } }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, description: str):
    st.markdown('<div class="gioval-eyebrow">GIOVAL · OPERACIONES</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)

