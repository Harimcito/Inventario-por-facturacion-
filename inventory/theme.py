"""Sistema visual compartido con Giovalia."""
import streamlit as st


def apply_brand():
    st.set_page_config(
        page_title="Gioval · Inventario", page_icon=":material/inventory_2:",
        layout="wide", initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
      :root { --brand:#788BFF; --brand-deep:#A9B5FF; --ink:#F1F4FF; --muted:#A3B1CC; --line:#2A3A5B; --canvas:#0A1020; --mint:#B9FF74; --cyan:#59DDF5; --coral:#FF829B; }
      .stApp { background:radial-gradient(ellipse at 12% -8%,#283B78 0,transparent 34%),radial-gradient(ellipse at 96% 22%,#174253 0,transparent 27%),linear-gradient(145deg,#0A1020 0%,#0D172A 56%,#101629 100%); color:var(--ink); font-family:Inter,"Segoe UI",system-ui,sans-serif; }
      [data-testid="stHeader"] { background:rgba(10,16,32,.78); backdrop-filter:blur(14px); }
      [data-testid="stSidebar"] { background:linear-gradient(180deg,#101A30 0%,#111B31 58%,#12182C 100%); border-right:1px solid #2A3B5A; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#AAB8D1; }
      [data-testid="stSidebar"] h3 { color:#F4F6FF; }
      .block-container { max-width:1480px; padding:3.7rem clamp(1rem,3vw,2.5rem) 3.25rem; animation:page-enter .28s ease-out both; }
      h1,h2,h3 { color:var(--ink); letter-spacing:-.035em; }
      h1 { font-size:clamp(1.75rem,3vw,2.35rem)!important; line-height:1.12!important; margin:.22rem 0 .35rem!important; font-weight:760!important; }
      h2 { font-size:1.32rem!important; margin-top:1.7rem!important; font-weight:720!important; }
      h3 { font-size:1.06rem!important; font-weight:680!important; }
      [data-testid="stCaptionContainer"] { color:var(--muted); }
      [data-testid="stMetric"] { background:linear-gradient(145deg,#172643 0%,#121E36 68%,#18213A 100%); border:1px solid #2A3B5A; border-radius:16px; padding:1.05rem 1.18rem; box-shadow:0 8px 22px #02071338,inset 0 1px #ffffff08; min-height:108px; transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; position:relative; overflow:hidden; }
      [data-testid="stMetric"]::after { content:""; position:absolute; inset:0 auto 0 0; width:3px; background:linear-gradient(180deg,var(--cyan),var(--brand)); opacity:.9; }
      [data-testid="stMetric"]:hover { transform:translateY(-2px); box-shadow:0 14px 30px #02071355,0 0 18px #687dff16; border-color:#5667A2; }
      [data-testid="stMetricLabel"] { color:var(--muted); font-size:.84rem; font-weight:550; }
      [data-testid="stMetricValue"] { color:var(--brand-deep); font-weight:740; letter-spacing:-.04em; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #2B3C5B; border-radius:13px; overflow:hidden; background:#111C32; box-shadow:0 8px 24px #02071330; }
      [data-testid="stExpander"] { background:linear-gradient(135deg,#15223B,#121D33); border:1px solid #2B3C5B; border-radius:13px; transition:border-color .16s ease,box-shadow .16s ease; }
      [data-testid="stExpander"]:hover { border-color:#506296; box-shadow:0 6px 20px #0207133d; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius:14px; border-color:#304361!important; background:linear-gradient(145deg,#182742B8,#121F36D9); }
      [data-testid="stAlert"] { border-radius:12px; animation:soft-appear .24s ease-out both; background:#1B2942; }
      .stButton button, .stDownloadButton button { border-radius:9px; min-height:42px; font-weight:620; transition:box-shadow .16s ease,transform .16s ease,background .16s ease; }
      .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button { position:relative; isolation:isolate; overflow:hidden; }
      .stButton button:hover, .stDownloadButton button:hover { box-shadow:0 5px 14px #17245a1c; transform:translateY(-1px); }
      .stButton button:active, .stDownloadButton button:active { transform:translateY(1px) scale(.985); box-shadow:0 1px 4px #17245a18; }
      .stButton button:active::after, .stDownloadButton button:active::after, [data-testid="stFormSubmitButton"] button:active::after { content:""; position:absolute; left:50%; top:50%; width:10px; height:10px; border-radius:50%; background:#FFFFFF70; transform:translate(-50%,-50%); animation:button-ripple .42s ease-out; z-index:0; pointer-events:none; }
      .stButton button > div, .stDownloadButton button > div, [data-testid="stFormSubmitButton"] button > div { position:relative; z-index:1; }
      .stButton button:focus-visible, .stDownloadButton button:focus-visible, [data-testid="stFormSubmitButton"] button:focus-visible { outline:3px solid #59DDF5!important; outline-offset:3px; }
      .stButton button[kind^="primary"], .stForm button[kind^="primary"] { color:#FFFFFF!important; background:linear-gradient(120deg,#5267F4 0%,#7865F2 100%)!important; border:1px solid #8795FF!important; box-shadow:0 4px 15px #566BFF45,inset 0 1px #FFFFFF35!important; }
      .stButton button[kind^="primary"] *, .stForm button[kind^="primary"] * { color:#FFFFFF!important; }
      .stButton button[kind^="primary"]:hover, .stForm button[kind^="primary"]:hover { color:#FFFFFF!important; background:linear-gradient(120deg,#6378FF 0%,#8A75FF 100%)!important; border-color:#B4BEFF!important; box-shadow:0 7px 22px #6579FF70,0 0 0 3px #7488FF20!important; }
      .stButton button[kind^="primary"]:active, .stForm button[kind^="primary"]:active { background:#4559D8!important; }
      [data-testid="stForm"] { background:linear-gradient(145deg,#14223B,#111D33); border:1px solid #304260; border-radius:16px; padding:1.15rem; box-shadow:0 10px 28px #02071330; }
      [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input { background:#101B30!important; color:#F1F4FF!important; border-color:#344665!important; }
      [data-testid="stTextInput"] label, [data-testid="stNumberInput"] label { color:#D4DDF0!important; font-weight:560; }
      .stButton button:not([kind^="primary"]), .stForm button:not([kind^="primary"]) { background:#1B2942; color:#DCE5FF; border-color:#43536F; }
      [data-testid="stSidebar"] [role="radiogroup"] label { border-radius:9px; padding:.38rem .5rem; transition:background .15s ease,color .15s ease; }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#202D4C; }
      [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:linear-gradient(100deg,#26345A,#213C52); color:#D4FFAB; font-weight:680; box-shadow:inset 3px 0 #A9FF74; }
      input:focus, textarea:focus { border-color:#A9FF74!important; box-shadow:0 0 0 3px #A9FF7426!important; }
      .gioval-eyebrow { color:#D5FFB0!important; background:linear-gradient(100deg,#27385C,#1A4050); border:1px solid #49617B; display:inline-flex; align-items:center; gap:.48rem; padding:.3rem .68rem .3rem .35rem; border-radius:999px; font-size:.69rem; font-weight:760; letter-spacing:.11em; text-transform:uppercase; margin-bottom:.5rem; opacity:1!important; }
      .gioval-mark { width:21px; height:21px; display:inline-grid; place-items:center; border-radius:7px; color:#0B1530!important; background:linear-gradient(135deg,#B9FF74,#59DDF5); font-size:.82rem; font-weight:900; letter-spacing:-.08em; box-shadow:0 0 14px #59DDF544; }
      .login-brand { display:flex; align-items:center; gap:.7rem; color:#DDE6FF; font-size:.75rem; font-weight:760; letter-spacing:.14em; margin:0 0 1.25rem; }
      .login-brand-mark { width:38px; height:38px; display:grid; place-items:center; border-radius:12px 12px 12px 4px; background:linear-gradient(135deg,#B9FF74,#59DDF5); color:#0A142A; font-size:1.3rem; font-weight:900; letter-spacing:-.1em; box-shadow:0 5px 20px #59DDF533; }
      @keyframes page-enter { from { opacity:.82; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
      @keyframes soft-appear { from { opacity:.65; } to { opacity:1; } }
      @keyframes button-ripple { from { width:10px;height:10px;opacity:.55; } to { width:180px;height:180px;opacity:0; } }
      @media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
      @media(max-width:900px) { .block-container { padding:3rem 1rem 2.25rem; } [data-testid="stMetric"] { min-height:92px; padding:.85rem; } }
      @media(max-width:700px) { .block-container { padding:2.8rem .75rem 1.75rem; } h2 { font-size:1.2rem!important; } }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, description: str):
    st.markdown('<div class="gioval-eyebrow"><span class="gioval-mark">G</span> GIOVAL · OPERACIONES</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)


def flash_on_next_render(message: str, icon: str = "✅"):
    """Conserva una confirmación cuando una acción termina en rerun."""
    st.session_state["_gioval_flash"] = {"message": message, "icon": icon}


def show_flash():
    notice = st.session_state.pop("_gioval_flash", None)
    if notice:
        st.toast(notice["message"], icon=notice.get("icon", "✅"))

