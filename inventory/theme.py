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
      .ops-flow .flow-step { display:grid; grid-template-columns:auto auto; gap:.1rem .35rem; align-items:center; white-space:nowrap; font-size:.62rem; font-weight:680; letter-spacing:.055em; }
      .ops-flow b { grid-row:1; color:#7781FF; font-size:.72rem; }
      .ops-flow span { grid-column:2; grid-row:1; }
      .ops-flow strong { grid-column:2; grid-row:2; color:#7D8290; font-size:.66rem; font-weight:560; letter-spacing:0; }
      .ops-flow .flow-step.is-active strong { color:#B7BAFF; }
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
      .ops-sectionline { display:flex; align-items:center; gap:.75rem; margin:1.8rem 0 .65rem; color:#7781FF; font-size:.67rem; font-weight:760; letter-spacing:.14em; }
      .ops-sectionline i { flex:1; height:1px; background:linear-gradient(90deg,#343747,transparent); }
      .ops-sectionline small { color:#717686; font-size:.6rem; letter-spacing:.1em; }
      .ops-attention { position:relative; overflow:hidden; margin:.5rem 0 .6rem; padding:1rem 1.1rem .8rem; border:1px solid #3A2E3D; border-left:3px solid #C0729B; border-radius:7px; background:radial-gradient(ellipse at 100% 0%,#C0729B12,transparent 45%),#11131B; }
      .attention-head { display:flex; align-items:center; justify-content:space-between; }
      .attention-kicker { color:#C98BAA; font-size:.62rem; font-weight:760; letter-spacing:.13em; }
      .attention-head h3,.ops-attention h3 { color:#F3F4F8; margin:.27rem 0 .65rem; font-size:1rem; }
      .attention-count { color:#D59AB5; font-size:1.7rem; font-weight:760; letter-spacing:-.06em; }
      .restock-list { display:grid; grid-template-columns:repeat(auto-fit,minmax(210px,1fr)); gap:.3rem .85rem; }
      .restock-row { display:flex; align-items:center; gap:.45rem; min-width:0; padding:.4rem 0; border-top:1px solid #252731; }
      .restock-dot { width:6px; height:6px; flex:none; border-radius:50%; background:#C0729B; box-shadow:0 0 8px #C0729B66; }
      .restock-name { overflow:hidden; color:#C8CAD3; font-size:.76rem; text-overflow:ellipsis; white-space:nowrap; }
      .restock-count { margin-left:auto; flex:none; color:#F3F4F8; font-size:.75rem; font-weight:700; }
      .restock-count small { color:#858997; font-size:.68rem; font-weight:500; }
      .attention-foot { margin-top:.45rem; color:#777C8A; font-size:.68rem; }
      .ops-attention.is-clear { display:flex; align-items:center; justify-content:space-between; padding:1rem 1.1rem; border-color:#2C3844; border-left-color:#6578A7; background:linear-gradient(100deg,#11131B,#111722); }
      .ops-attention.is-clear h3 { margin:.2rem 0 .15rem; }
      .ops-attention.is-clear p { margin:0; color:#8C929F; font-size:.76rem; }
      .clear-mark { display:grid; width:31px; height:31px; place-items:center; border:1px solid #344151; border-radius:50%; color:#8F9DB6; font-weight:700; }
      .st-key-open_restock button { min-height:34px; padding:.35rem .72rem; border-radius:5px; font-size:.78rem; }
      .intake-flow { display:flex; align-items:center; gap:.65rem; margin:.55rem 0 1rem; padding:.85rem 1rem; border:1px solid #292C38; border-radius:7px; background:linear-gradient(105deg,#11131B,#0D0E14); }
      .intake-step { display:grid; grid-template-columns:auto auto; gap:.05rem .5rem; align-items:center; flex:1; min-width:0; padding:.2rem .25rem; }
      .intake-step>b { grid-row:1; color:#666B79; font-size:.67rem; }
      .intake-icon { display:grid; width:27px; height:27px; grid-row:1/3; place-items:center; border:1px solid #343744; border-radius:6px; background:#171923; color:#9A9EAC; font-size:.95rem; }
      .intake-step small { display:block; color:#6F7481; font-size:.57rem; font-weight:730; letter-spacing:.12em; }
      .intake-step strong { display:block; overflow:hidden; color:#D7D9E0; font-size:.76rem; text-overflow:ellipsis; white-space:nowrap; }
      .intake-step em { display:block; color:#777C8A; font-size:.65rem; font-style:normal; }
      .intake-step.active .intake-icon { color:#D9DCFF; background:#11142A; border-color:#3D48B8; box-shadow:0 0 14px #010ED022; }
      .intake-step.active>b,.intake-step.active small { color:#8C96FF; }
      .intake-step.done .intake-icon { color:#E6E8FF; background:#010ED0; border-color:#303CE2; }
      .intake-step.done>b { color:#7781FF; }
      .intake-connector { width:clamp(12px,3vw,42px); height:1px; flex:none; background:linear-gradient(90deg,#343747,#010ED0,#343747); opacity:.7; }
      .intake-empty { display:flex; align-items:flex-start; gap:.8rem; margin:.65rem 0; padding:.95rem 1rem; border-left:2px solid #343747; background:linear-gradient(90deg,#11131B,#0D0E14); }
      .empty-mark { color:#7781FF; font-size:.72rem; font-weight:750; }
      .intake-empty strong { color:#E5E6EC; font-size:.82rem; }
      .intake-empty p { max-width:48rem; margin:.22rem 0 0; color:#858A98; font-size:.74rem; }
      .intake-queue { display:flex; align-items:center; flex-wrap:wrap; gap:.55rem; margin:.8rem 0; padding:.72rem .85rem; border:1px solid #303341; border-radius:6px; background:#11131B; }
      .queue-live { width:7px; height:7px; border-radius:50%; background:#7781FF; box-shadow:0 0 9px #010ED0; animation:queue-breathe 1.8s ease-in-out infinite; }
      .intake-queue strong { color:#DDE0EA; font-size:.76rem; }
      .intake-queue small { margin-left:auto; color:#858A98; font-size:.69rem; }
      [data-testid="stFileUploader"] section { border:1px dashed #414557; border-radius:7px; background:linear-gradient(120deg,#11131B,#10121A); transition:border-color .18s ease,background .18s ease; }
      [data-testid="stFileUploader"] section:hover { border-color:#6672D7; background:#11142A; }
      @keyframes queue-breathe { 0%,100% { opacity:.6; box-shadow:0 0 5px #010ED0; } 50% { opacity:1; box-shadow:0 0 12px #7781FF; } }
      @media(max-width:700px) { .intake-flow { align-items:stretch; flex-direction:column; gap:.25rem; padding:.75rem; } .intake-connector { width:1px; height:10px; margin-left:14px; } .intake-step { flex:none; } .intake-queue small { flex-basis:100%; margin-left:1rem; } }
      .st-key-app_navigation [data-testid="stRadio"] label { transition:background .16s ease,border-color .16s ease,transform .16s ease; }
      @media(max-width:900px) { .ops-hero { grid-template-columns:1fr; } .ops-hero-data { border-left:0; border-top:1px solid #292C38; } .login-story { padding:1.2rem; } }
      @media(max-width:640px) { .ops-hero-copy { padding:1.2rem; } .ops-flow { gap:.3rem; } .ops-flow div { font-size:.55rem; } .ops-flow i { width:12px; } }
      @keyframes page-enter { from { opacity:.82; transform:translateY(5px); } to { opacity:1; transform:translateY(0); } }
      @keyframes soft-appear { from { opacity:.65; } to { opacity:1; } }
      @keyframes button-ripple { from { width:10px;height:10px;opacity:.55; } to { width:180px;height:180px;opacity:0; } }
      @media(prefers-reduced-motion:reduce) { *,*::before,*::after { animation-duration:.01ms!important; transition-duration:.01ms!important; scroll-behavior:auto!important; } }
      @media(max-width:900px) { .block-container { padding:3rem 1rem 2.25rem; } [data-testid="stMetric"] { min-height:92px; padding:.85rem; } }
      @media(max-width:700px) { .block-container { padding:2.8rem .75rem 1.75rem; } h2 { font-size:1.2rem!important; } }
      /* GIOVAL / FUTURE CONSOLE */
      :root { --electric:#3F5BFF; --signal:#2CD9FF; --violet:#9B7BFF; --grid:#8CA4FF0A; }
      .stApp { background:radial-gradient(ellipse at 8% -10%,#2439A42E,transparent 36rem),radial-gradient(ellipse at 96% 20%,#003F6630,transparent 30rem),linear-gradient(140deg,#070A12,#0A0D17 54%,#090B13)!important; }
      .stApp::before { content:""; position:fixed; inset:0; z-index:0; pointer-events:none; opacity:.42; background-image:linear-gradient(var(--grid) 1px,transparent 1px),linear-gradient(90deg,var(--grid) 1px,transparent 1px); background-size:40px 40px; mask-image:linear-gradient(180deg,#000 0%,transparent 78%); }
      [data-testid="stAppViewContainer"], [data-testid="stMain"] { background:transparent!important; }
      .block-container { z-index:1; }
      [data-testid="stSidebar"] { background:linear-gradient(180deg,#0E1422F5,#0B0E17F8)!important; border-right:1px solid #24314D!important; box-shadow:8px 0 30px #00000020; }
      [data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p { color:#8895B0; }
      [data-testid="stSidebar"] [role="radiogroup"] label { margin:.12rem 0; border:1px solid transparent; }
      [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:linear-gradient(100deg,#14234A,#11182B)!important; border-color:#263966; box-shadow:inset 2px 0 var(--signal),0 4px 14px #00000020!important; }
      .gioval-eyebrow { background:linear-gradient(100deg,#111A33,#101D2B)!important; border:1px solid #25365C!important; color:#B6C5FF!important; box-shadow:inset 0 1px #FFFFFF08; }
      .gioval-mark { background:linear-gradient(145deg,#4C63FF,#1528D0)!important; box-shadow:0 0 16px #3158FF55; }
      .login-brand-image { box-shadow:0 0 24px #264EFF40; }
      h1 { text-shadow:0 0 32px #3658FF1A; }
      [data-testid="stMetric"] { background:linear-gradient(145deg,#111A2B 0%,#0E1421 75%,#111522)!important; border:1px solid #26334C!important; border-top:1px solid #35496B!important; border-radius:7px!important; box-shadow:inset 0 1px #FFFFFF07,0 12px 30px #00000030!important; }
      [data-testid="stMetric"]::after { width:2px!important; background:linear-gradient(180deg,var(--signal),var(--electric))!important; }
      [data-testid="stMetricValue"] { color:#EAF0FF!important; text-shadow:0 0 18px #3D64FF22; }
      [data-testid="stMetric"]:hover { transform:translateY(-3px)!important; border-color:#3A5A8A!important; box-shadow:0 16px 35px #00000046,0 0 22px #2866FF20!important; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { background:#0E1421!important; border-color:#26334C!important; box-shadow:0 12px 34px #00000034!important; }
      [data-testid="stExpander"], [data-testid="stForm"] { background:linear-gradient(145deg,#111827,#0D121D)!important; border-color:#2A3953!important; box-shadow:0 12px 30px #00000022!important; }
      .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button { border-radius:5px!important; letter-spacing:.015em; }
      .stButton button[kind^="primary"], .stForm button[kind^="primary"] { background:linear-gradient(105deg,#243EE8,#315CFF 58%,#227FCE)!important; border-color:#5177FF!important; box-shadow:0 5px 18px #1D49FF38,inset 0 1px #FFFFFF2A!important; }
      .stButton button[kind^="primary"]:hover, .stForm button[kind^="primary"]:hover { background:linear-gradient(105deg,#3452FF,#397BFF 58%,#26A8D1)!important; box-shadow:0 8px 25px #1D6DFF55,0 0 0 1px #65CAFF70!important; }
      .stButton button:not([kind^="primary"]), .stForm button:not([kind^="primary"]) { background:linear-gradient(110deg,#131D31,#111722)!important; border:1px solid #34445F!important; color:#DFE7FA!important; }
      .stButton button:not([kind^="primary"]):hover, .stForm button:not([kind^="primary"]):hover { background:#192641!important; border-color:#4C73B2!important; box-shadow:0 5px 20px #174B9630!important; }
      button:focus-visible { outline-color:var(--signal)!important; }
      .ops-hero { border-color:#2B3C5F!important; background:radial-gradient(ellipse at 0% 0%,#254FFF26,transparent 55%),radial-gradient(ellipse at 100% 100%,#00A6D316,transparent 44%),linear-gradient(115deg,#101827,#0A101B 72%)!important; box-shadow:0 18px 48px #0000004A,inset 0 1px #FFFFFF0A!important; }
      .ops-hero-copy { position:relative; }
      .ops-hero-copy::after { content:"LOCAL SYSTEM / 01"; position:absolute; right:1.25rem; top:1.25rem; color:#586A89; font:600 .58rem ui-monospace,Consolas,monospace; letter-spacing:.12em; }
      .ops-kicker { font-family:ui-monospace,Consolas,monospace!important; color:#92A4CB!important; }
      .ops-kicker span { color:var(--signal)!important; }
      .ops-hero h2 { letter-spacing:-.055em!important; }
      .ops-hero h2 em { color:#75A7FF!important; text-shadow:0 0 24px #386BFF65; }
      .ops-hero-data { border-left-color:#293B60!important; background:linear-gradient(160deg,#111C30D9,#0C1420E8)!important; }
      .ops-value { font-variant-numeric:tabular-nums; text-shadow:0 0 26px #3D72FF29; }
      .ops-value-label,.ops-category-head { font-family:ui-monospace,Consolas,monospace!important; color:#8295B9!important; }
      .ops-bar { background:#202B40!important; }
      .ops-bar i { background:linear-gradient(90deg,#324DFF,#34CFFF)!important; box-shadow:0 0 12px #318BFF66!important; }
      .ops-sectionline { color:#82A2FF!important; font-family:ui-monospace,Consolas,monospace; }
      .ops-sectionline i { background:linear-gradient(90deg,#2C426A,transparent)!important; }
      .ops-attention { border-color:#493347!important; border-left-color:#B66BBD!important; background:radial-gradient(ellipse at 100% 0%,#B66BBD17,transparent 48%),linear-gradient(120deg,#151522,#10131D)!important; box-shadow:0 10px 28px #0000002A; }
      .attention-kicker { color:#C694D0!important; font-family:ui-monospace,Consolas,monospace; }
      .attention-count { color:#D5A3E1!important; }
      .restock-dot { background:#C478D4!important; box-shadow:0 0 10px #B66BBD77!important; }
      .ops-attention.is-clear { border-color:#244258!important; border-left-color:#37BEDA!important; background:linear-gradient(100deg,#101923,#0D1720)!important; }
      .clear-mark { color:#63CDE4!important; border-color:#315467!important; }
      .intake-flow { background:linear-gradient(105deg,#101827,#0D121D)!important; border-color:#2A3A59!important; box-shadow:0 10px 30px #00000024,inset 0 1px #FFFFFF08; }
      .intake-step.active .intake-icon { color:#C4E9FF!important; background:linear-gradient(145deg,#162A55,#102033)!important; border-color:#2778B2!important; box-shadow:0 0 18px #13B5FF28!important; }
      .intake-step.active>b,.intake-step.active small { color:#52C9FF!important; }
      .intake-step.done .intake-icon { background:linear-gradient(145deg,#315BFF,#125FBD)!important; border-color:#398FFF!important; box-shadow:0 0 14px #168AFF36; }
      .intake-connector { background:linear-gradient(90deg,#2B3A55,#317FD0,#2B3A55)!important; }
      .queue-live { background:#39D6FF!important; box-shadow:0 0 10px #39D6FF!important; }
      .intake-queue { background:linear-gradient(100deg,#101827,#0D131F)!important; border-color:#2D4567!important; }
      .login-story { background:radial-gradient(ellipse at 100% 0%,#3155FF36,transparent 60%),linear-gradient(145deg,#101827,#0B101A)!important; border-color:#2A3C61!important; box-shadow:0 18px 45px #00000038,inset 0 1px #FFFFFF0A!important; }
      .login-kicker span { background:#37D7FF!important; box-shadow:0 0 12px #37D7FFAA!important; }
      .login-story h2 em { color:#75A7FF!important; text-shadow:0 0 22px #3B65FF77; }
      .login-route span { background:#111A2A!important; border-color:#2B3C5C!important; }
      .login-route b { color:#55CFFF!important; }
      [data-testid="stFileUploader"] section { background:linear-gradient(120deg,#101827,#0D1420)!important; border-color:#334A6C!important; }
      [data-testid="stFileUploader"] section:hover { border-color:#3D91D6!important; background:#101C31!important; }
      .intake-empty { border-left-color:#39BFEA!important; background:linear-gradient(90deg,#111A29,#0D131D)!important; }
      .empty-mark { color:#55CFFF!important; font-family:ui-monospace,Consolas,monospace; }
      @keyframes tech-glow { 0%,100% { box-shadow:0 0 8px #2357FF28; } 50% { box-shadow:0 0 19px #20BFFF46; } }
      .intake-step.active .intake-icon { animation:tech-glow 2.4s ease-in-out infinite; }
      @media(prefers-reduced-motion:reduce) { .intake-step.active .intake-icon { animation:none!important; } }
      /* PRISM PASS: una identidad más visible, editorial y menos parecida al tema base */
      :root { --prism-cyan:#55F2D1; --prism-lime:#D8FF62; --prism-lilac:#AA86FF; --prism-ink:#090B16; }
      .stApp { background:
        radial-gradient(ellipse at 4% 18%,#663EFF4A,transparent 31rem),
        radial-gradient(ellipse at 95% 6%,#00DDBA32,transparent 25rem),
        radial-gradient(ellipse at 82% 94%,#FF5A9A1C,transparent 30rem),
        linear-gradient(135deg,#090B16 0%,#11142A 48%,#080D18 100%)!important; }
      .stApp::before { opacity:.68; background-image:linear-gradient(#94A8FF12 1px,transparent 1px),linear-gradient(90deg,#94A8FF12 1px,transparent 1px); background-size:34px 34px; mask-image:radial-gradient(ellipse at 50% 25%,#000 10%,transparent 84%); }
      [data-testid="stHeader"] { background:#090B16C9!important; backdrop-filter:blur(18px); }
      [data-testid="stSidebar"] { background:linear-gradient(160deg,#15172AF7,#0C1220F7 66%,#10172AF7)!important; border-right:1px solid #5E63A640!important; box-shadow:14px 0 50px #0007; }
      [data-testid="stSidebar"] [role="radiogroup"] label { margin:.22rem 0!important; padding:.52rem .68rem!important; border:1px solid #FFFFFF08!important; border-radius:10px!important; color:#AEB8D4; }
      [data-testid="stSidebar"] [role="radiogroup"] label:hover { background:#252644!important; border-color:#A58BFF50!important; transform:translateX(3px); }
      [data-testid="stSidebar"] [role="radiogroup"] label:has(input:checked) { background:linear-gradient(100deg,#6939E84D,#13CDB52A)!important; border-color:#8C72FF85!important; box-shadow:inset 3px 0 var(--prism-cyan),0 8px 24px #4E3BAA30!important; color:#FFFFFF; }
      .gioval-eyebrow { border-color:#A18AFF55!important; background:linear-gradient(105deg,#6D4AD638,#15D7BE19)!important; color:#D8D0FF!important; border-radius:999px!important; padding:.34rem .78rem .34rem .38rem!important; }
      .gioval-mark { background:linear-gradient(135deg,#A68BFF,#6744F5 58%,#27D9C0)!important; box-shadow:0 0 22px #9274FF75,0 0 42px #00D8B522!important; }
      h1,h2,h3 { letter-spacing:-.045em!important; }
      h1 { background:linear-gradient(100deg,#FFF 8%,#C6B8FF 56%,#73F0D4 105%); color:transparent!important; background-clip:text!important; -webkit-background-clip:text!important; }
      [data-testid="stMetric"] { position:relative; overflow:hidden; background:linear-gradient(145deg,#1C2040 0%,#11182B 70%,#121E2A)!important; border:1px solid #7381CF50!important; border-radius:14px!important; box-shadow:0 16px 42px #03061185,inset 0 1px #FFFFFF16!important; }
      [data-testid="stMetric"]::before { content:""; position:absolute; width:130px; height:130px; right:-68px; top:-68px; border:1px solid #57F2D133; border-radius:50%; box-shadow:0 0 0 14px #57F2D10B,0 0 0 29px #AA86FF0A; }
      [data-testid="stMetric"]::after { background:linear-gradient(180deg,var(--prism-cyan),var(--prism-lilac),#FF7FB1)!important; width:3px!important; }
      [data-testid="stMetricValue"] { color:#F9FAFF!important; font-size:clamp(1.5rem,2.7vw,2.15rem)!important; text-shadow:0 0 22px #7F81FF46; }
      [data-testid="stMetricLabel"] { color:#A8B3D1!important; letter-spacing:.035em; }
      [data-testid="stDataFrame"], [data-testid="stTable"] { border:1px solid #7885C545!important; border-radius:14px!important; overflow:hidden; box-shadow:0 18px 44px #02040B70!important; }
      .stButton button, .stDownloadButton button, [data-testid="stFormSubmitButton"] button { min-height:46px!important; border-radius:11px!important; font-weight:720!important; transition:transform .2s cubic-bezier(.2,.8,.2,1),box-shadow .2s ease,filter .2s ease!important; }
      .stButton button[kind^="primary"], .stForm button[kind^="primary"] { background:linear-gradient(105deg,#7451FF 0%,#6255F7 48%,#19BDA9 120%)!important; border:1px solid #B4A4FF!important; box-shadow:0 8px 24px #7451FF52,inset 0 1px #FFFFFF55!important; color:white!important; }
      .stButton button[kind^="primary"]:hover, .stForm button[kind^="primary"]:hover { filter:saturate(1.3) brightness(1.17); transform:translateY(-3px)!important; box-shadow:0 13px 32px #7451FF74,0 0 0 3px #55F2D12D!important; }
      .stButton button:not([kind^="primary"]), .stForm button:not([kind^="primary"]) { background:linear-gradient(125deg,#1C2240,#151B2B)!important; color:#E8E8FF!important; border:1px solid #747BC852!important; }
      .stButton button:not([kind^="primary"]):hover { border-color:#55F2D1!important; transform:translateY(-2px)!important; box-shadow:0 10px 24px #00BFA526!important; }
      .ops-hero { position:relative; border:1px solid #9A83FF6B!important; border-radius:20px!important; background:radial-gradient(ellipse at 10% 0%,#9E78FF40,transparent 46%),radial-gradient(ellipse at 96% 100%,#16D4B72E,transparent 44%),linear-gradient(118deg,#19162F,#11192A 55%,#101F26)!important; box-shadow:0 22px 66px #03040F99, inset 0 1px #FFFFFF20!important; }
      .ops-hero::before { content:""; position:absolute; right:28%; top:-80px; width:300px; height:300px; border:1px solid #B49AFF29; border-radius:50%; box-shadow:0 0 0 22px #FFFFFF04,0 0 0 48px #FFFFFF03,0 0 0 76px #55F2D106; pointer-events:none; }
      .ops-hero-copy,.ops-hero-data { position:relative; z-index:1; }
      .ops-kicker { color:#C4B8F8!important; font-size:.72rem!important; }
      .ops-kicker span,.ops-flow b { color:var(--prism-cyan)!important; }
      .ops-hero h2 { font-size:clamp(2rem,4vw,3.2rem)!important; line-height:.99!important; letter-spacing:-.07em!important; }
      .ops-hero h2 em { background:linear-gradient(100deg,#B9A4FF,#67F4D8); color:transparent!important; background-clip:text!important; -webkit-background-clip:text!important; text-shadow:none!important; }
      .ops-hero-copy p { color:#B5BDD3!important; max-width:31rem!important; }
      .ops-flow .flow-step { padding:.55rem .65rem; border:1px solid #FFFFFF12; border-radius:9px; background:#080B174C; }
      .ops-flow strong { color:#8CF4DC!important; font-size:.75rem!important; }
      .ops-hero-data { border-left:1px solid #8E7DFF50!important; border-radius:0 18px 18px 0; background:linear-gradient(160deg,#201C3A88,#0D1927C7)!important; }
      .ops-value { color:#FFFFFF!important; font-size:clamp(2.3rem,4vw,3.5rem)!important; text-shadow:0 0 30px #65EBD644!important; }
      .ops-value-label,.ops-category-head { color:#9C9EC2!important; }
      .ops-bar { height:6px!important; border-radius:99px!important; background:#FFFFFF12!important; }
      .ops-bar i { border-radius:99px!important; background:linear-gradient(90deg,#8566FF,#43E8CF,#DBFF69)!important; box-shadow:0 0 16px #55F2D188!important; }
      .ops-sectionline { color:#B7A5FF!important; }
      .ops-sectionline i { background:linear-gradient(90deg,#A484FF70,#55F2D140,transparent)!important; height:2px!important; }
      .ops-attention { border:1px solid #FF8DB45C!important; border-left:4px solid #FF8DB4!important; border-radius:14px!important; background:radial-gradient(ellipse at 100% 0%,#FF559B22,transparent 48%),linear-gradient(115deg,#28192C,#19172A)!important; }
      .attention-kicker,.attention-count,.restock-dot { color:#FF9BBB!important; }
      .restock-dot { background:#FF75A2!important; box-shadow:0 0 12px #FF75A2!important; }
      .intake-flow { border:1px solid #927BFF70!important; border-radius:14px!important; background:linear-gradient(110deg,#211B3D,#111D2D)!important; box-shadow:0 13px 35px #07091475!important; }
      .intake-step.active .intake-icon { background:linear-gradient(140deg,#8A62FF,#2FD8BD)!important; color:#080B16!important; border:0!important; box-shadow:0 0 24px #61DCC699!important; }
      .intake-step.active>b,.intake-step.active small { color:#8EF5DE!important; }
      .intake-connector { background:linear-gradient(90deg,#9F7BFF,#55F2D1)!important; height:2px!important; }
      .login-story { min-height:345px; padding:2.2rem!important; border:1px solid #A58AFF80!important; border-radius:24px!important; background:radial-gradient(ellipse at 20% 8%,#8057FF73,transparent 45%),radial-gradient(ellipse at 90% 86%,#11D8B653,transparent 42%),linear-gradient(140deg,#201941,#111D2B 76%)!important; box-shadow:0 28px 75px #02040CBF,inset 0 1px #FFFFFF2E!important; }
      .login-story::before { content:"G"; position:absolute; right:1.2rem; top:-3rem; color:#FFFFFF09; font-size:25rem; line-height:1; font-weight:900; letter-spacing:-.13em; pointer-events:none; }
      .login-story::after { right:-75px!important; bottom:-110px!important; width:280px!important; height:280px!important; border-color:#55F2D16B!important; box-shadow:0 0 0 22px #55F2D110,0 0 0 48px #AA86FF14,0 0 58px #55F2D133!important; }
      .login-kicker { position:relative; z-index:1; color:#D6D0F8!important; }
      .login-kicker span { background:var(--prism-lime)!important; box-shadow:0 0 16px var(--prism-lime)!important; }
      .login-story h2 { position:relative; z-index:1; margin-top:2rem!important; font-size:clamp(2.3rem,4vw,3.5rem)!important; letter-spacing:-.075em!important; }
      .login-story h2 em { color:var(--prism-cyan)!important; text-shadow:0 0 28px #55F2D166!important; }
      .login-story p { position:relative; z-index:1; color:#D0D0E5!important; font-size:1rem!important; }
      .login-route { position:relative; z-index:1; gap:.42rem!important; }
      .login-route span { border-color:#B9A9FF50!important; border-radius:7px!important; background:#11152A99!important; color:#E4DFFF!important; }
      .login-route b { color:var(--prism-cyan)!important; }
      .stHorizontalBlock:has(.login-story) { gap:clamp(1.4rem,4vw,4rem)!important; }
      .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:first-child { align-self:stretch; padding:clamp(.8rem,2vw,1.5rem); border:1px solid #7B6CEB32; border-radius:28px; background:linear-gradient(145deg,#201A3B4D,#0E1B2933); box-shadow:0 30px 80px #0004; }
      .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:last-child { padding:clamp(1rem,2.7vw,2.6rem); border:1px solid #8CA0DA38; border-radius:22px; background:linear-gradient(150deg,#171E33E8,#101522F2); box-shadow:0 24px 65px #02040C7D,inset 0 1px #FFFFFF12; }
      .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:last-child h3 { font-size:1.65rem!important; }
      .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:last-child [data-testid="stForm"] { border:0!important; border-radius:0!important; padding:.5rem 0 0!important; background:transparent!important; box-shadow:none!important; }
      .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:last-child input { min-height:48px; border-radius:10px!important; background:#0C1020!important; border-color:#666CA366!important; }
      .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:last-child input:focus { border-color:#55F2D1!important; box-shadow:0 0 0 3px #55F2D129!important; }
      [data-testid="stFileUploader"] section { border:1px dashed #8F7DFFA6!important; border-radius:16px!important; background:linear-gradient(120deg,#201B3B,#101C2C)!important; padding:1.2rem!important; }
      [data-testid="stFileUploader"] section:hover { border-color:#55F2D1!important; box-shadow:0 0 26px #55F2D126!important; }
      @keyframes prism-breathe { 0%,100% { filter:brightness(1); } 50% { filter:brightness(1.13); } }
      .login-story { animation:prism-breathe 7s ease-in-out infinite; }
      @media(max-width:900px) { .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:first-child { padding:.7rem; } .login-story { min-height:290px!important; padding:1.6rem!important; } .login-story h2 { font-size:2.25rem!important; } }
      @media(max-width:640px) { .ops-hero { border-radius:15px!important; } .ops-hero h2 { font-size:2rem!important; } .ops-flow { flex-wrap:wrap; } .stHorizontalBlock:has(.login-story) > [data-testid="stColumn"]:last-child { padding:1.2rem!important; } .login-story::before { font-size:18rem; } }
      @media(prefers-reduced-motion:reduce) { .login-story { animation:none!important; } }
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

