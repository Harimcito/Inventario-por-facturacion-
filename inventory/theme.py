"""Sistema visual compartido con Giovalia."""
import streamlit as st
import base64
from pathlib import Path


def apply_brand():
    st.set_page_config(
        page_title="Gioval · Inventario", page_icon=":material/inventory_2:",
        layout="wide", initial_sidebar_state="expanded",
    )
    st.markdown("""
    <style>
      :root { --brand:#010ED0; --brand-hover:#1724EA; --brand-glow:#010ED04D; --ink:#F3F4F8; --muted:#9A9EAC; --line:#292C38; --canvas:#0A0B10; --panel:#11131B; --panel-2:#171923; --panel-3:#1C1F2A; }
      .stApp { background:radial-gradient(ellipse at 8% 0%,#010ED01A,transparent 34rem),radial-gradient(ellipse at 96% 4%,#010ED012,transparent 28rem),#0A0B10; color:var(--ink); font-family:Inter,"Segoe UI",system-ui,sans-serif; }
      [data-testid="stHeader"] { background:rgba(10,11,16,.94); backdrop-filter:blur(14px); }
      [data-testid="stSidebar"] { background:linear-gradient(180deg,#11131B 0%,#0E1017 100%); border-right:1px solid var(--line); }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#B4B7C4; }
      [data-testid="stSidebar"] h3 { color:#F4F6FF; }
      .block-container { max-width:1480px; padding:3.7rem clamp(1rem,3vw,2.5rem) 3.25rem; animation:page-enter .28s ease-out both; }
      h1,h2,h3 { color:var(--ink); letter-spacing:-.035em; }
      h1 { font-size:clamp(1.75rem,3vw,2.35rem)!important; line-height:1.12!important; margin:.22rem 0 .35rem!important; font-weight:760!important; }
      h2 { font-size:1.32rem!important; margin-top:1.7rem!important; font-weight:720!important; }
      h3 { font-size:1.06rem!important; font-weight:680!important; }
      [data-testid="stCaptionContainer"] { color:var(--muted); }
      [data-testid="stMetric"] { background:linear-gradient(145deg,#151720 0%,#11131B 72%,#151720 100%); border:1px solid #292C38; border-top:2px solid #3A3E49; border-radius:8px; padding:1.05rem 1.18rem; box-shadow:0 8px 22px #00000030; min-height:108px; transition:transform .18s ease,box-shadow .18s ease,border-color .18s ease; position:relative; overflow:hidden; }
      [data-testid="stMetric"]::after { content:""; position:absolute; inset:0 auto 0 0; width:2px; background:var(--brand); opacity:.8; }
      [data-testid="stMetric"]:hover { transform:translateY(-2px); box-shadow:0 12px 26px #00000054,0 0 18px var(--brand-glow); border-color:#3B3E4A; border-top-color:var(--brand); }
      [data-testid="stMetricLabel"] { color:var(--muted); font-size:.84rem; font-weight:550; }
      [data-testid="stMetricValue"] { color:#F3F4F8; font-weight:740; letter-spacing:-.04em; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #292C38; border-radius:8px; overflow:hidden; background:#11131B; box-shadow:0 8px 24px #00000030; }
      [data-testid="stExpander"] { background:#11131B; border:1px solid #292C38; border-radius:8px; transition:border-color .16s ease,box-shadow .16s ease; }
      [data-testid="stExpander"]:hover { border-color:#454958; box-shadow:0 6px 20px #00000045; }
      [data-testid="stVerticalBlockBorderWrapper"] { border-radius:8px; border-color:#292C38!important; background:#11131B; }
      [data-testid="stAlert"] { border-radius:8px; animation:soft-appear .24s ease-out both; background:#151720; }
      .stButton button, .stDownloadButton button { border-radius:9px; min-height:42px; font-weight:620; transition:box-shadow .16s ease,transform .16s ease,background .16s ease; }
      .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button { position:relative; isolation:isolate; overflow:hidden; }
      .stButton button:hover, .stDownloadButton button:hover { box-shadow:0 5px 14px #17245a1c; transform:translateY(-1px); }
      .stButton button:active, .stDownloadButton button:active { transform:translateY(1px) scale(.985); box-shadow:0 1px 4px #17245a18; }
      .stButton button:active::after, .stDownloadButton button:active::after, [data-testid="stFormSubmitButton"] button:active::after { content:""; position:absolute; left:50%; top:50%; width:10px; height:10px; border-radius:50%; background:#FFFFFF70; transform:translate(-50%,-50%); animation:button-ripple .42s ease-out; z-index:0; pointer-events:none; }
      .stButton button > div, .stDownloadButton button > div, [data-testid="stFormSubmitButton"] button > div { position:relative; z-index:1; }
      .stButton button:focus-visible, .stDownloadButton button:focus-visible, [data-testid="stFormSubmitButton"] button:focus-visible { outline:3px solid #7781FF!important; outline-offset:3px; }
      .stButton button[kind^="primary"], .stForm button[kind^="primary"] { color:#FFFFFF!important; background:var(--brand)!important; border:1px solid var(--brand)!important; box-shadow:none!important; }
      .stButton button[kind^="primary"] *, .stForm button[kind^="primary"] * { color:#FFFFFF!important; }
      .stButton button[kind^="primary"]:hover, .stForm button[kind^="primary"]:hover { color:#FFFFFF!important; background:var(--brand-hover)!important; border-color:#3944F2!important; box-shadow:0 0 0 3px var(--brand-glow)!important; }
      .stButton button[kind^="primary"]:active, .stForm button[kind^="primary"]:active { background:#000BB4!important; }
      [data-testid="stForm"] { background:linear-gradient(145deg,#11131B,#151720); border:1px solid #292C38; border-radius:8px; padding:1.15rem; box-shadow:0 10px 28px #00000030; }
      [data-testid="stTextInput"] input, [data-testid="stNumberInput"] input, [data-testid="stDateInput"] input { background:#0D0F16!important; color:#F3F4F8!important; border-color:#353847!important; }
      [data-testid="stTextInput"] label, [data-testid="stNumberInput"] label { color:#D4D6DE!important; font-weight:560; }
      .stButton button:not([kind^="primary"]), .stForm button:not([kind^="primary"]) { background:#171923; color:#E7E8EE; border-color:#323542; }
      [data-testid="stSidebar"] [role="radiogroup"] label { border-radius:9px; padding:.38rem .5rem; transition:background .15s ease,color .15s ease; }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#202331; }
      [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:#11142A; color:#FFFFFF; font-weight:680; box-shadow:inset 3px 0 var(--brand); }
      input:focus, textarea:focus { border-color:var(--brand)!important; box-shadow:0 0 0 2px var(--brand-glow)!important; }
      .gioval-eyebrow { color:#C7CAFF!important; background:#11142A; border:1px solid #292C38; display:inline-flex; align-items:center; gap:.48rem; padding:.28rem .68rem .28rem .35rem; border-radius:6px; font-size:.69rem; font-weight:760; letter-spacing:.11em; text-transform:uppercase; margin-bottom:.5rem; opacity:1!important; }
      .gioval-mark { width:21px; height:21px; display:inline-grid; place-items:center; border-radius:4px; color:#FFFFFF!important; background:var(--brand); font-size:.82rem; font-weight:900; letter-spacing:-.08em; }
      .login-brand { display:flex; align-items:center; gap:.7rem; color:#F3F4F8; font-size:.75rem; font-weight:760; letter-spacing:.14em; margin:0 0 1.25rem; }
      .login-brand-mark { width:38px; height:38px; display:grid; place-items:center; border-radius:7px; background:var(--brand); color:#FFFFFF; font-size:1.3rem; font-weight:900; letter-spacing:-.1em; box-shadow:0 4px 14px var(--brand-glow); }
      .login-brand-image { width:42px; height:42px; object-fit:contain; border-radius:7px; box-shadow:0 4px 14px #00000044; }
      .login-story { position:relative; overflow:hidden; padding:1.65rem 1.5rem 1.4rem; margin-top:.35rem; border:1px solid #292C38; border-radius:8px; background:radial-gradient(ellipse at 100% 0%,#010ED02B,transparent 58%),linear-gradient(145deg,#11131B,#0D0E14); }
      .login-story::after { content:""; position:absolute; right:-55px; bottom:-90px; width:210px; height:210px; border:1px solid #343747; border-radius:50%; box-shadow:0 0 0 22px #ffffff03,0 0 0 45px #ffffff02; pointer-events:none; }
      .login-kicker,.ops-kicker { color:#9A9EAC; font-size:.69rem; font-weight:700; letter-spacing:.13em; }
      .login-kicker span { display:inline-block; width:7px; height:7px; margin-right:.42rem; border-radius:50%; background:#010ED0; box-shadow:0 0 10px #010ED0AA; }
      .login-story h2 { color:#F3F4F8; font-size:clamp(1.8rem,3.1vw,2.55rem)!important; line-height:1.08!important; margin:1.2rem 0 .65rem!important; font-weight:760!important; }
      .login-story h2 em,.ops-hero h2 em { color:#7781FF; font-style:normal; }
      .login-story p { color:#9A9EAC; max-width:31rem; font-size:.96rem; }
      .login-route { display:flex; align-items:center; gap:.52rem; flex-wrap:wrap; margin-top:1.7rem; color:#B7BAC6; font-size:.63rem; font-weight:700; letter-spacing:.06em; }
      .login-route span { padding:.4rem .5rem; border:1px solid #292C38; border-radius:4px; background:#11131B; }
      .login-route b { color:#7781FF; font-weight:500; }
      .ops-hero { display:grid; grid-template-columns:minmax(0,1.45fr) minmax(250px,.75fr); margin:.2rem 0 1rem; border:1px solid #292C38; border-radius:8px; overflow:hidden; background:radial-gradient(ellipse at 6% 0%,#010ED020,transparent 58%),linear-gradient(115deg,#11131B,#0D0E14 72%); box-shadow:0 14px 38px #00000038; }
      .ops-hero-copy { padding:1.65rem 1.7rem 1.4rem; }
      .ops-kicker { color:#A8ACBA; }
      .ops-kicker span { color:#7781FF; }
      .ops-hero h2 { color:#F3F4F8; font-size:clamp(1.6rem,2.7vw,2.25rem)!important; line-height:1.08!important; margin:.85rem 0 .6rem!important; font-weight:760!important; }
      .ops-hero-copy p { max-width:35rem; color:#9A9EAC; font-size:.94rem; }
      .ops-flow { display:flex; align-items:center; gap:.65rem; margin-top:1.45rem; color:#BFC2CE; }
      .ops-flow div { display:flex; align-items:center; gap:.35rem; white-space:nowrap; font-size:.64rem; font-weight:680; letter-spacing:.055em; }
      .ops-flow b { color:#7781FF; font-size:.72rem; }
      .ops-flow i { width:clamp(14px,3vw,38px); height:1px; background:linear-gradient(90deg,#010ED0,#343747); }
      .ops-hero-data { padding:1.45rem 1.35rem; border-left:1px solid #292C38; background:linear-gradient(160deg,#151720B8,#0D0F16D9); }
      .ops-value-label,.ops-category-head { color:#8F94A3; font-size:.63rem; letter-spacing:.12em; font-weight:720; }
      .ops-value { margin:.18rem 0 .16rem; color:#F3F4F8; font-size:clamp(1.8rem,3vw,2.35rem); line-height:1.1; font-weight:760; letter-spacing:-.05em; }
      .ops-value-note { color:#9A9EAC; font-size:.78rem; }
      .ops-category-head { margin:1.05rem 0 .5rem; }
      .ops-category { display:grid; grid-template-columns:1fr auto; gap:.28rem .5rem; margin:.38rem 0; color:#B8BBC7; font-size:.72rem; }
      .ops-bar { grid-column:1/-1; height:3px; border-radius:9px; background:#292C38; overflow:hidden; }
      .ops-bar i { display:block; height:100%; border-radius:9px; background:linear-gradient(90deg,#010ED0,#7781FF); box-shadow:0 0 9px #010ED055; }
      .ops-empty-category { color:#777C8A; font-size:.78rem; }
      .st-key-app_navigation [data-testid="stRadio"] label { transition:background .16s ease,border-color .16s ease,transform .16s ease; }
      @media(max-width:900px) { .ops-hero { grid-template-columns:1fr; } .ops-hero-data { border-left:0; border-top:1px solid #292C38; } .login-story { padding:1.2rem; } }
      @media(max-width:640px) { .ops-hero-copy { padding:1.2rem; } .ops-flow { gap:.3rem; } .ops-flow div { font-size:.55rem; } .ops-flow i { width:12px; } }
      @keyframes page-enter { from { opacity:.82; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
      @keyframes soft-appear { from { opacity:.65; } to { opacity:1; } }
      @keyframes button-ripple { from { width:10px;height:10px;opacity:.55; } to { width:180px;height:180px;opacity:0; } }
      @media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
      @media(max-width:900px) { .block-container { padding:3rem 1rem 2.25rem; } [data-testid="stMetric"] { min-height:92px; padding:.85rem; } }
      @media(max-width:700px) { .block-container { padding:2.8rem .75rem 1.75rem; } h2 { font-size:1.2rem!important; } }
    </style>
    """, unsafe_allow_html=True)


def page_header(title: str, description: str):
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "gioval-logo.svg"
    logo = base64.b64encode(logo_path.read_bytes()).decode("ascii") if logo_path.exists() else ""
    logo_html = f'<img src="data:image/svg+xml;base64,{logo}" class="gioval-mark" alt="Giovalia">' if logo else '<span class="gioval-mark">G</span>'
    st.markdown(f'<div class="gioval-eyebrow">{logo_html} GIOVAL · OPERACIONES</div>', unsafe_allow_html=True)
    st.title(title)
    st.caption(description)


def brand_lockup(label="INVENTARIO"):
    logo_path = Path(__file__).resolve().parent.parent / "assets" / "gioval-logo.svg"
    logo, name = st.columns([.7, 2.8], vertical_alignment="center")
    with logo:
        if logo_path.exists():
            logo_data = base64.b64encode(logo_path.read_bytes()).decode("ascii")
            st.markdown(f'<img src="data:image/svg+xml;base64,{logo_data}" class="login-brand-image" alt="Giovalia">',
                        unsafe_allow_html=True)
        else:
            st.markdown('<span class="login-brand-mark">G</span>', unsafe_allow_html=True)
    with name:
        st.markdown(f'<div class="login-brand">GIOVAL / {label}</div>', unsafe_allow_html=True)


def flash_on_next_render(message: str, icon: str = "✅"):
    """Conserva una confirmación cuando una acción termina en rerun."""
    st.session_state["_gioval_flash"] = {"message": message, "icon": icon}


def show_flash():
    notice = st.session_state.pop("_gioval_flash", None)
    if notice:
        st.toast(notice["message"], icon=notice.get("icon", "✅"))

