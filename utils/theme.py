"""Visual theme: dusty rose page, lighter rose sheets, warm taupe tiles, pale pill chips.

Fonts: Gaegu (handwritten display), Lilita One (labels and names), Nunito (body).
Spacing follows an 8px scale. No gradients, no glass effects, no animation
beyond a small lift on hover.
"""
import streamlit as st

CSS = """
@import url('https://fonts.googleapis.com/css2?family=Gaegu:wght@300;400;700&family=Lilita+One&family=Nunito:wght@400;600;700&display=swap');
:root{
  --page:#D6B4B9; --sheet:#E7C9CE; --sheet-deep:#DDB5BC; --tile:#B0ABAC; --tile-soft:#F1EEEE;
  --chip:#EDE9E9; --ink:#2E2829; --ink-soft:#4D4445; --cream:#F7F0F0;
  --shadow:8px 12px 24px rgba(70,45,50,.22); --shadow-sm:4px 6px 14px rgba(70,45,50,.18);
  --r-sheet:44px; --r-card:26px; --r-tile:20px;
  --s1:8px; --s2:16px; --s3:24px; --s4:32px; --s5:40px;
  --display:'Gaegu','Comic Sans MS',cursive; --label:'Lilita One','Arial Rounded MT Bold',sans-serif; --body:'Nunito','Segoe UI',sans-serif;
}
.stApp{background:var(--page); color:var(--ink); font-family:var(--body);}
.stApp p,.stApp li,.stApp label,.stApp input,.stApp textarea,.stApp button,.stApp [data-testid="stMarkdownContainer"]{font-family:var(--body);}
.stApp p,.stApp li{color:var(--ink);}
#MainMenu,footer,[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none !important;}
header[data-testid="stHeader"]{background:transparent; height:0;}

/* the sheet that holds every page */
.stMainBlockContainer,.block-container,[data-testid="stMainBlockContainer"]{
  max-width:1120px; width:calc(100% - 32px); margin:var(--s3) auto; padding:var(--s5) var(--s5) var(--s5) !important;
  background:var(--sheet); border-radius:var(--r-sheet); border-top-left-radius:112px; box-shadow:var(--shadow);}
@media (max-width:640px){
  .stMainBlockContainer,.block-container,[data-testid="stMainBlockContainer"]{
    width:calc(100% - 16px); margin:var(--s1) auto; padding:var(--s3) var(--s2) var(--s4) !important;
    border-radius:28px; border-top-left-radius:56px;}
}

/* type */
.stApp .stMarkdown h1,.stApp .stMarkdown h2,.stApp .stMarkdown h3,.stApp .stMarkdown h4{font-family:var(--label); font-weight:400; color:var(--ink); letter-spacing:.01em;}
.lc-brand{display:flex; align-items:baseline; gap:var(--s1);}
.lc-brand-name{font-family:var(--display); font-size:3rem; line-height:1; color:var(--ink);}
.lc-brand-sub{font-family:var(--label); font-size:.8rem; letter-spacing:.18em; color:var(--ink);}
.stApp .lc-pagehead{margin:var(--s2) 0 var(--s3);}
.stApp .lc-pagehead h1{font-family:var(--display); font-weight:400; font-size:3.6rem; line-height:1; margin:0; padding:0; color:var(--ink);}
.stApp .lc-pagehead p{margin:var(--s1) 0 0; color:var(--ink-soft); font-size:1.05rem;}
.stApp .lc-h2{font-family:var(--display); font-size:2.2rem; line-height:1.1; margin:var(--s3) 0 var(--s2); color:var(--ink);}
.lc-hello{font-family:var(--display); font-size:3rem; line-height:1.05; margin:0 0 var(--s1); color:var(--ink);}
.lc-note{color:var(--ink-soft); font-size:.95rem;}
@media (max-width:640px){
  .stApp .lc-pagehead h1{font-size:2.6rem;} .lc-hello{font-size:2.3rem;} .lc-brand-name{font-size:2.4rem;}
}

/* panels (use utils.ui.panel) */
[class*="st-key-panel-curve-"]{background:var(--sheet-deep); border-radius:var(--r-card); border-top-left-radius:88px; padding:var(--s4) var(--s4) var(--s3) var(--s5); box-shadow:var(--shadow-sm);}
[class*="st-key-panel-sheet-"]{background:var(--sheet-deep); border-radius:var(--r-card); padding:var(--s3); box-shadow:var(--shadow-sm);}
[class*="st-key-panel-tile-"]{background:var(--tile); border-radius:var(--r-card); padding:var(--s2); box-shadow:var(--shadow-sm);}
[class*="st-key-panel-chip-"]{background:var(--chip); border-radius:var(--r-card); padding:var(--s2);}
@media (max-width:640px){[class*="st-key-panel-curve-"]{padding:var(--s3) var(--s2); border-top-left-radius:56px;}}

/* tiles */
.lc-img{background:var(--tile-soft); border-radius:var(--r-tile); aspect-ratio:4/5; display:flex; align-items:center; justify-content:center; overflow:hidden;}
.lc-img img{width:100%; height:100%; object-fit:contain;}
.lc-noimg{font-family:var(--label); font-size:.75rem; letter-spacing:.1em; text-transform:uppercase; color:var(--ink-soft);}
.lc-name{font-family:var(--label); font-size:1.1rem; text-align:center; margin:var(--s2) 0 4px; color:var(--ink);}
.lc-meta{font-size:.85rem; text-align:center; color:var(--ink); font-weight:600; margin-bottom:var(--s1);}
.lc-chips{display:flex; flex-wrap:wrap; justify-content:center; gap:4px; margin-bottom:var(--s1);}
.lc-chip{display:inline-block; background:var(--chip); color:var(--ink); border-radius:999px; padding:4px 12px; font-family:var(--label); font-size:.7rem; letter-spacing:.07em; text-transform:uppercase;}
.lc-chip.dark{background:var(--ink); color:var(--cream);}
.lc-chiprow{display:flex; flex-wrap:wrap; gap:var(--s1); margin:var(--s1) 0 var(--s2);}
.lc-collage{display:grid; grid-template-columns:repeat(2,1fr); gap:var(--s1);}
.lc-collage.n1{grid-template-columns:1fr;}
.lc-cell{background:var(--tile-soft); border-radius:14px; aspect-ratio:1; overflow:hidden; display:flex; align-items:center; justify-content:center;}
.lc-cell img{width:100%; height:100%; object-fit:contain;}
.lc-week{display:flex; gap:var(--s1); overflow-x:auto; padding-bottom:var(--s1);}
.lc-day{flex:1 0 104px; background:var(--chip); border-radius:var(--r-tile); padding:var(--s2) var(--s1); text-align:center; color:var(--ink);}
.lc-day.today{background:var(--ink); color:var(--cream);}
.lc-day .dow{font-family:var(--label); font-size:.72rem; letter-spacing:.1em; text-transform:uppercase;}
.lc-day .num{font-family:var(--display); font-size:2rem; line-height:1.1;}
.lc-day .plan{font-size:.82rem; font-weight:700; overflow-wrap:anywhere;}
.lc-weather{font-family:var(--label); font-size:1.4rem; color:var(--ink);}

/* buttons: pill, soft shadow, lift on hover (no fade) */
.stApp .stButton > button,.stApp .stDownloadButton > button,.stApp [data-testid="stFormSubmitButton"] > button,
.stApp [data-testid="stPopover"] > button,.stApp [data-testid="stPopoverButton"]{
  border-radius:999px; background:var(--chip); color:var(--ink); border:none; min-height:44px; padding:var(--s1) var(--s3);
  font-family:var(--label); font-weight:400; letter-spacing:.03em; box-shadow:var(--shadow-sm); transition:transform .12s ease;}
.stApp .stButton > button p,.stApp .stDownloadButton > button p,.stApp [data-testid="stFormSubmitButton"] > button p,
.stApp [data-testid="stPopover"] > button p{font-family:var(--label); color:inherit; font-weight:400;}
.stApp .stButton > button:hover,.stApp .stDownloadButton > button:hover,.stApp [data-testid="stFormSubmitButton"] > button:hover,
.stApp [data-testid="stPopover"] > button:hover{transform:translateY(-2px); color:var(--ink); background:var(--chip);}
.stApp button[data-testid="stBaseButton-primary"],.stApp button[data-testid="stBaseButton-primaryFormSubmit"],.stApp button[kind="primary"]{background:var(--ink); color:var(--cream);}
.stApp button[data-testid="stBaseButton-primary"] p,.stApp button[data-testid="stBaseButton-primaryFormSubmit"] p{color:var(--cream);}
.stApp button[data-testid="stBaseButton-primary"]:hover,.stApp button[data-testid="stBaseButton-primaryFormSubmit"]:hover{background:var(--ink); color:var(--cream);}
.stApp button:disabled{box-shadow:none; transform:none;}
.stApp button:focus-visible,.stApp input:focus-visible,.stApp textarea:focus-visible{outline:3px solid var(--ink); outline-offset:2px;}
[data-testid="stPopover"]{width:100%;}
[data-testid="stPopover"] > button{width:100%;}
[data-testid="stPopoverBody"]{background:var(--sheet); border-radius:var(--r-card);}

/* navigation chips */
.st-key-nav button{border-radius:999px; background:var(--chip); color:var(--ink); border:none; box-shadow:var(--shadow-sm); min-height:40px; padding:6px var(--s2);}
.st-key-nav button p{font-family:var(--label); font-size:.95rem; font-weight:400; color:inherit;}
.st-key-nav button[data-testid="stBaseButton-pillsActive"],.st-key-nav button[aria-checked="true"],.st-key-nav button[aria-pressed="true"]{background:var(--ink); color:var(--cream);}
.st-key-nav button[data-testid="stBaseButton-pillsActive"] p,.st-key-nav button[aria-checked="true"] p,.st-key-nav button[aria-pressed="true"] p{color:var(--cream);}

/* inputs */
.stApp div[data-baseweb="input"],.stApp div[data-baseweb="base-input"],.stApp div[data-baseweb="select"] > div,.stApp div[data-baseweb="textarea"]{border-radius:999px; background:var(--chip); border:none;}
.stApp div[data-baseweb="textarea"]{border-radius:var(--r-tile);}
.stApp input,.stApp textarea{color:var(--ink);}
.stApp [data-testid="stWidgetLabel"] p{font-family:var(--label); font-size:.78rem; letter-spacing:.08em; text-transform:uppercase; color:var(--ink);}
.stApp [data-testid="stFileUploaderDropzone"]{background:var(--chip); border:2px dashed var(--ink-soft); border-radius:var(--r-card);}
.stApp [data-testid="stExpander"] details{border-radius:var(--r-card); background:var(--chip); border:none;}
.stApp [data-testid="stAlert"]{border-radius:var(--r-tile);}
.stApp button[data-baseweb="tab"] p{font-family:var(--label); font-size:1rem; font-weight:400;}
.stApp [data-testid="stChatMessage"]{background:var(--chip); border-radius:var(--r-card); padding:var(--s2);}
.stApp [data-testid="stChatInput"]{border-radius:999px;}
.stApp [data-testid="stForm"]{border:none; padding:0;}
"""


def inject_theme():
    css = "".join(line.strip() for line in CSS.strip().splitlines())
    st.markdown(f"<style>{css}</style>", unsafe_allow_html=True)
