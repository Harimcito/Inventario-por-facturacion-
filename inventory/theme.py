"""Sistema visual compartido con Giovalia."""
import streamlit as st


def apply_brand():
    st.set_page_config(
        page_title="Gioval · Inventario", page_icon=":material/inventory_2:",
        layout="wide", initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
      :root { --brand:#1525C8; --brand-deep:#111B64; --ink:#172338; --muted:#66758B; --line:#E3E8F1; --canvas:#F4F6FA; --mint:#D9F6EB; }
      .stApp { background:var(--canvas); color:var(--ink); font-family:Inter,"Segoe UI",system-ui,sans-serif; }
      [data-testid="stHeader"] { background:rgba(244,246,250,.88); backdrop-filter:blur(12px); }
      [data-testid="stSidebar"] { background:linear-gradient(180deg,#fff 0%,#FAFBFF 100%); border-right:1px solid var(--line); }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#536279; }
      [data-testid="stSidebar"] h3 { color:var(--brand-deep); }
      .block-container { max-width:1480px; padding:2.2rem clamp(1rem,3vw,2.5rem) 3.25rem; animation:page-enter .28s ease-out both; }
      h1,h2,h3 { color:var(--ink); letter-spacing:-.035em; }
      h1 { font-size:clamp(1.75rem,3vw,2.35rem)!important; line-height:1.12!important; margin:.22rem 0 .35rem!important; font-weight:760!important; }
      h2 { font-size:1.32rem!important; margin-top:1.7rem!important; font-weight:720!important; }
      h3 { font-size:1.06rem!important; font-weight:680!important; }
      [data-testid="stCaptionContainer"] { color:var(--muted); }
      [data-testid="stMetric"] { background:linear-gradient(145deg,#fff 55%,#F7F8FF); border:1px solid var(--line); border-radius:15px; padding:1.05rem 1.18rem; box-shadow:0 4px 14px #16204a08; min-height:108px; transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; }
      [data-testid="stMetric"]:hover { transform:translateY(-2px); box-shadow:0 10px 24px #16204a12; border-color:#CDD4F6; }
      [data-testid="stMetricLabel"] { color:var(--muted); font-size:.84rem; font-weight:550; }
      [data-testid="stMetricValue"] { color:var(--brand-deep); font-weight:740; letter-spacing:-.04em; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid var(--line); border-radius:12px; overflow:hidden; background:#fff; box-shadow:0 3px 12px #16204a06; }
      [data-testid="stExpander"] { background:#fff; border:1px solid var(--line); border-radius:12px; transition:border-color .16s ease,box-shadow .16s ease; }
      [data-testid="stExpander"]:hover { border-color:#C9D1EA; box-shadow:0 4px 14px #16204a08; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; border-color:var(--line)!important; background:#FFFFFFB8; }
      [data-testid="stAlert"] { border-radius:12px; animation:soft-appear .24s ease-out both; }
      .stButton button, .stDownloadButton button { border-radius:9px; min-height:42px; font-weight:620; transition:box-shadow .16s ease,transform .16s ease,background .16s ease; }
      .stButton button:hover, .stDownloadButton button:hover { box-shadow:0 5px 14px #17245a1c; transform:translateY(-1px); }
      .stButton button:active, .stDownloadButton button:active { transform:translateY(1px) scale(.985); box-shadow:0 1px 4px #17245a18; }
      .stButton button[kind="primary"] { color:white; background:linear-gradient(115deg,#1525C8,#3748E5); border-color:#1525C8; box-shadow:0 4px 10px #1525C829; }
      .stButton button[kind="primary"]:hover { background:linear-gradient(115deg,#111B64,#2638C9); box-shadow:0 7px 18px #1525C83D; }
      [data-testid="stSidebar"] [role="radiogroup"] label { border-radius:9px; padding:.38rem .5rem; transition:background .15s ease,color .15s ease; }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#EEF1FF; }
      [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#EEF1FF; color:var(--brand); font-weight:650; }
      input:focus, textarea:focus { border-color:var(--brand)!important; box-shadow:0 0 0 3px #1525C81A!important; }
      .gioval-eyebrow { color:var(--brand)!important; background:linear-gradient(100deg,#E8EBFF,#E8F8F3); display:inline-flex; align-items:center; padding:.3rem .65rem; border-radius:999px; font-size:.69rem; font-weight:760; letter-spacing:.11em; text-transform:uppercase; margin-bottom:.5rem; opacity:1!important; }
      @keyframes page-enter { from { opacity:.82; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
      @keyframes soft-appear { from { opacity:.65; } to { opacity:1; } }
      @media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
      @media(max-width:900px) { .block-container { padding:1.45rem 1rem 2.25rem; } [data-testid="stMetric"] { min-height:92px; padding:.85rem; } }
      @media(max-width:700px) { .block-container { padding:1.15rem .75rem 1.75rem; } h2 { font-size:1.2rem!important; } }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, description: str):
    st.markdown('<div class="gioval-eyebrow">GIOVAL · OPERACIONES</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)

