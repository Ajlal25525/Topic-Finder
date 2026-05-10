import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
import random
from collections import Counter
from urllib.parse import urlparse, quote_plus

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="RankFinder Pro — Topic Research",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- THEME ----------
if "theme" not in st.session_state:
    st.session_state.theme = "light"

PALETTES = {
    "light": {"bg":"#FFFFFF","bg_soft":"#F7F8FB","sidebar":"#FAFBFC","ink":"#0F1A2A",
              "muted":"#6B7280","border":"#E5E7EB","card":"#FFFFFF","input_bg":"#FFFFFF",
              "track":"#EEF1F5","popover_bg":"#FFFFFF","btn_bg":"#FFFFFF",
              "icon_bg":"#FFF1EC","plot_bg":"white"},
    "dark":  {"bg":"#0B1220","bg_soft":"#111827","sidebar":"#0F1A2A","ink":"#E5E7EB",
              "muted":"#9CA3AF","border":"#1F2A3C","card":"#111827","input_bg":"#0F1A2A",
              "track":"#1F2A3C","popover_bg":"#111827","btn_bg":"#111827",
              "icon_bg":"#3A1F14","plot_bg":"#111827"},
}
T = PALETTES[st.session_state.theme]
IS_DARK = st.session_state.theme == "dark"

MARKET_TO_GL = {"Global":"us","United States":"us","United Kingdom":"gb",
                "Australia":"au","Canada":"ca","India":"in"}

STOPWORDS = set("""a an the and or but if then for of in on at to from by with as is are was were be been being
this that these those it its it's i you he she we they them us our your their what which who whom how why
when where can will just do does did done not no yes so than too very also into about over under more most
best top vs guide guides how-to tips list way ways thing things you're we're they're""".split())

NAV_WORDS = {"home","about","contact","pricing","login","signup","sign","register","cart","search",
             "menu","blog","news","resources","resource","products","product","services","service",
             "solutions","solution","industries","industry","support","help","faq","privacy","terms"}

ARTICLE_URL_HINTS = ["/blog/","/article/","/articles/","/post/","/posts/","/guide/","/guides/",
                     "/resource/","/resources/","/learn/","/insights/","/news/","/knowledge/",
                     "/case-stud","/whitepaper","/ebook","/tutorial","/how-to"]

QUERY_VARIANTS = [
    "{kw}",
    "best {kw}",
    "{kw} guide",
    "how to use {kw}",
]

CURRENT_YEAR = 2026

GENERIC_MODIFIERS = {
    "best","top","free","paid","cheap","affordable","budget","premium","luxury",
    "easy","simple","beginner","beginners","advanced","professional","pro",
    "online","cloud","mobile","desktop","web","web-based","saas","offline",
    "open","open-source","enterprise","small","medium","large",
    "new","modern","latest","ultimate","complete","comprehensive","essential",
    "how","what","why","when","where","which","who","is","are","can","do","does","should","will",
    "the","a","an","my","your","our",
}

ARTICLE_STARTERS = {"how","what","why","when","where","which","who",
                    "best","top","guide","ultimate","complete","essential",
                    "the","a","an","is","are","do","does","can","should","will",
                    "introducing","everything","beginner","beginners","ultimate"}

JUNK_QUERY_TOKENS = {"synonym","synonyms","pdf","doc","docx","ppt","pptx","ebook",
                     "wikipedia","wiki","translate","translation","login","logo",
                     "youtube","picture","pictures","images","image",
                     "crack","torrent","resume","cv","quizlet"}

def is_junk_query(query):
    ql = (query or "").lower()
    if not ql: return True
    words = set(re.findall(r"[a-z][a-z\-]+", ql))
    if words & JUNK_QUERY_TOKENS: return True
    # Dated year query (2018-2024) without a clear "best/top/guide" angle = noise
    if re.search(r"\b20(1\d|2[0-4])\b", ql) and not any(w in ql for w in ["best","top","guide"]):
        return True
    return False

# ---------- CSS ----------
st.markdown(f"""
<style>
:root {{
  --brand:#FF6A3D; --brand-dark:#E04F22; --brand-soft:#FFF1EC;
  --accent:#3B82F6; --accent-soft:#EFF6FF;
  --ink:{T['ink']}; --muted:{T['muted']};
  --bg:{T['bg']}; --bg-soft:{T['bg_soft']};
  --border:{T['border']}; --card:{T['card']};
  --input-bg:{T['input_bg']}; --track:{T['track']};
  --green:#16A34A; --amber:#F59E0B; --red:#DC2626;
}}
html, body, .stApp,
[data-testid="stAppViewContainer"],
[data-testid="stHeader"],
[data-testid="stMain"] {{ background-color: var(--bg) !important; color: var(--ink) !important; }}
.stApp * {{ color: var(--ink); }}
.stMarkdown, label, [data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] *
  {{ color: var(--ink) !important; }}
small, .stCaption, [data-testid="stCaptionContainer"] {{ color: var(--muted) !important; }}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ padding-top:1rem; padding-bottom:3rem; max-width:1500px; }}

/* ---------- Sidebar ---------- */
[data-testid="stSidebar"] {{ background:{T['sidebar']} !important; border-right:1px solid var(--border); }}
[data-testid="stSidebar"] * {{ color: var(--ink) !important; }}
[data-testid="stSidebar"] .sidebar-brand {{
  display:flex; align-items:center; gap:10px; padding: 4px 0 16px 0;
  border-bottom:1px solid var(--border); margin-bottom: 14px;
}}
[data-testid="stSidebar"] .sidebar-brand .logo {{
  width:34px; height:34px; border-radius:9px;
  background: linear-gradient(135deg, var(--brand), var(--brand-dark));
  display:flex; align-items:center; justify-content:center;
  color:white !important; font-size:18px; font-weight:800;
  box-shadow: 0 4px 10px rgba(255,106,61,0.3);
}}
[data-testid="stSidebar"] .sidebar-brand .name {{ font-weight:700; font-size:15px; }}
[data-testid="stSidebar"] .sidebar-brand .tag {{ font-size:11px; color:var(--muted) !important; }}
[data-testid="stSidebar"] .side-section {{
  font-size:11px; font-weight:700; text-transform:uppercase; letter-spacing:0.7px;
  color: var(--muted) !important; margin: 12px 0 6px 0;
  display:flex; align-items:center; gap:6px;
}}
[data-testid="stSidebar"] .side-section .ico {{ font-size:13px; }}

/* ---------- Inputs ---------- */
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div, .stNumberInput input {{
  background: var(--input-bg) !important; color: var(--ink) !important;
  border:1px solid var(--border) !important; border-radius:8px !important;
  font-size:13px !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
  color:{('#6B7280' if IS_DARK else '#9CA3AF')} !important; opacity:1;
}}
.stTextInput input:focus, .stTextArea textarea:focus {{
  border-color: var(--brand) !important;
  box-shadow: 0 0 0 3px rgba(255,106,61,0.12) !important;
}}
[data-testid="stSlider"] [role="slider"] {{ background: var(--brand) !important; }}

/* ---------- Header ---------- */
.app-header {{
  display:flex; align-items:center; justify-content:space-between;
  padding: 6px 0 16px 0; border-bottom: 1px solid var(--border); margin-bottom: 22px;
}}
.app-title {{ font-size: 24px; font-weight: 700; color: var(--ink); margin:0;
  display:flex; align-items:center; gap:12px; }}
.app-title .icon {{
  width:36px; height:36px; border-radius:10px;
  background: linear-gradient(135deg, var(--brand), var(--brand-dark));
  display:inline-flex; align-items:center; justify-content:center;
  color:white !important; font-size:18px; box-shadow: 0 4px 12px rgba(255,106,61,0.25);
}}
.app-sub {{ font-size: 13px; color: var(--muted); margin-top: 4px; padding-left:48px; }}
.live-pill {{
  display:inline-flex; align-items:center; gap:6px;
  background: var(--accent-soft); color: var(--accent) !important;
  padding: 5px 12px; border-radius:999px; font-size: 11px; font-weight:700;
  letter-spacing:0.4px; border: 1px solid rgba(59,130,246,0.25);
}}
.live-pill .dot {{ width:7px; height:7px; border-radius:50%; background: var(--accent);
  box-shadow: 0 0 0 3px rgba(59,130,246,0.18); }}

/* ---------- KPI Cards ---------- */
.kpi {{ background:var(--card); border:1px solid var(--border); border-radius:12px;
  padding:16px 18px; height:100%; position:relative; overflow:hidden;
  transition: transform .15s ease, box-shadow .15s ease;
}}
.kpi::before {{
  content:""; position:absolute; top:0; left:0; right:0; height:3px;
  background: linear-gradient(90deg, var(--brand), var(--brand-dark));
}}
.kpi:hover {{ transform: translateY(-2px); box-shadow: 0 8px 20px rgba(15,26,42,0.08); }}
.kpi .label {{ color:var(--muted) !important; font-size:11px; font-weight:700;
  text-transform:uppercase; letter-spacing:0.6px; }}
.kpi .value {{ color:var(--ink) !important; font-size:28px; font-weight:700; margin-top:6px;
  display:flex; align-items:center; gap:8px; }}
.kpi .icon {{ float:right; font-size:18px; background: var(--brand-soft);
  color:var(--brand) !important; padding:7px 9px; border-radius:8px; margin-top:-2px; }}

.section-title {{ font-size:16px; font-weight:700; color:var(--ink) !important;
  margin:14px 0 12px 0; display:flex; align-items:center; gap:8px; }}
.section-title .accent {{ width:4px; height:16px; background:var(--brand); border-radius:2px; }}

/* ---------- Buttons ---------- */
.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {{
  background: linear-gradient(135deg, var(--brand), var(--brand-dark)) !important;
  border:none !important; color:white !important; font-weight:600;
  box-shadow: 0 4px 12px rgba(255,106,61,0.28); border-radius:9px !important;
}}
.stButton>button[kind="primary"]:hover, .stDownloadButton>button[kind="primary"]:hover {{
  box-shadow: 0 6px 16px rgba(255,106,61,0.4); transform: translateY(-1px);
}}
.stButton>button, .stDownloadButton>button {{
  background:{T['btn_bg']}; color:var(--ink) !important; border:1px solid var(--border);
  border-radius:9px !important; font-weight:500;
}}

/* ---------- Empty / welcome state ---------- */
.welcome-grid {{
  display:grid; grid-template-columns: repeat(3, 1fr); gap:18px;
  margin: 20px 0 26px 0;
}}
.feat-card {{
  background: var(--card); border: 1px solid var(--border);
  border-radius: 14px; padding: 22px; position: relative; overflow:hidden;
  transition: transform .18s ease, box-shadow .18s ease;
}}
.feat-card:hover {{ transform: translateY(-3px); box-shadow: 0 12px 28px rgba(15,26,42,0.08); }}
.feat-card .icon-wrap {{
  width:44px; height:44px; border-radius:11px;
  display:flex; align-items:center; justify-content:center;
  font-size:20px; margin-bottom:14px;
}}
.feat-card .icon-orange {{ background: var(--brand-soft); color: var(--brand) !important; }}
.feat-card .icon-blue   {{ background: var(--accent-soft); color: var(--accent) !important; }}
.feat-card .icon-green  {{ background: #DCFCE7; color: #16A34A !important; }}
.feat-card h3 {{ font-size:15px; font-weight:700; margin:0 0 6px 0; color:var(--ink); }}
.feat-card p {{ font-size:13px; color:var(--muted) !important; line-height:1.55; margin:0; }}

.welcome-cta {{
  background: linear-gradient(135deg,#0F1A2A 0%,#1E2A44 100%);
  border-radius:14px; padding: 28px 32px; color:white !important;
  display:flex; align-items:center; justify-content:space-between; gap:24px;
  margin-bottom: 18px;
}}
.welcome-cta * {{ color:white !important; }}
.welcome-cta h2 {{ font-size:22px; font-weight:700; margin:0; }}
.welcome-cta p {{ font-size:14px; color:#C5CCD8 !important; margin:4px 0 0 0; }}
.welcome-cta .step-pills {{ display:flex; gap:10px; flex-shrink:0; }}
.welcome-cta .pill {{
  background: rgba(255,255,255,0.08); border:1px solid rgba(255,255,255,0.18);
  padding: 8px 14px; border-radius: 999px; font-size:12px; font-weight:600;
}}

.tips {{
  background: var(--bg-soft); border:1px solid var(--border);
  border-radius:12px; padding:18px 20px; margin-top:8px;
}}
.tips .tip-title {{ font-size:13px; font-weight:700; color:var(--ink) !important;
  display:flex; align-items:center; gap:6px; margin-bottom:8px; }}
.tips ul {{ margin:0; padding-left:18px; color:var(--muted) !important; font-size:13px; line-height:1.7; }}
.tips ul li {{ color:var(--muted) !important; }}
.tips ul li b {{ color: var(--ink) !important; }}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER ----------
hcol1, hcol2 = st.columns([8, 2])
with hcol1:
    st.markdown("""
    <div class="app-header">
      <div style="flex:1;">
        <div class="app-title">
          <span class="icon">🎯</span>
          <span>Topic Research <span style="font-weight:400;color:var(--muted);font-size:16px;">— Content Gap Engine</span></span>
        </div>
        <div class="app-sub">
          Surfaces real topic ideas your competitors rank for that you don't yet cover — built for both Google search and LLM citations.
        </div>
      </div>
      <div><span class="live-pill"><span class="dot"></span>LIVE SERP DATA</span></div>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    st.write("")
    if st.button("🌙 Dark" if not IS_DARK else "☀️ Light", use_container_width=True):
        st.session_state.theme = "dark" if not IS_DARK else "light"
        st.rerun()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("""
    <div class="sidebar-brand">
      <div class="logo">R</div>
      <div>
        <div class="name">RankFinder Pro</div>
        <div class="tag">Topic & Gap Intelligence</div>
      </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown('<div class="side-section"><span class="ico">🌐</span> YOUR WEBSITE</div>',
                unsafe_allow_html=True)
    your_site = st.text_input(
        "Your domain", label_visibility="collapsed",
        placeholder="e.g. yourdomain.com",
    )
    st.caption("We scan what you already cover so we only suggest NEW topics.")

    st.markdown('<div class="side-section"><span class="ico">🎯</span> SEED KEYWORDS</div>',
                unsafe_allow_html=True)
    keyword_input = st.text_area(
        "Keywords", height=150, label_visibility="collapsed", key="kw_input",
        placeholder=("e.g.\n"
                     "farm management software\n"
                     "livestock tracking app\n"
                     "agriculture ERP solutions"),
    )
    st.caption("One per line. Leave empty to auto-discover from your site.")

    st.markdown('<div class="side-section"><span class="ico">🔑</span> API KEY</div>',
                unsafe_allow_html=True)
    serper_key = st.text_input(
        "Serper key", type="password", label_visibility="collapsed",
        placeholder="Paste your Serper.dev API key",
        help="Free 2,500 queries at https://serper.dev",
    )

    st.markdown('<div class="side-section"><span class="ico">⚙️</span> SETTINGS</div>',
                unsafe_allow_html=True)
    market = st.selectbox("Market focus", list(MARKET_TO_GL.keys()))
    topics_per_keyword = st.slider("Topic ideas per keyword (max)", 5, 15, 10,
        help="Quality over quantity. The tool returns fewer if it can't find enough strong, unique ideas.")
    competitors_per_keyword = st.slider("Competitors mined per keyword", 1, 5, 3)
    min_new_tokens = st.slider("Gap strictness (min new words)", 1, 4, 1,
        help="Higher = stricter. Topic must introduce this many words your site doesn't cover.")
    use_expansion = st.checkbox("Query expansion (richer ideas, more API calls)", value=True)

    st.markdown('<div style="margin-top:18px;"></div>', unsafe_allow_html=True)
    run_analysis = st.button("🚀 Run Topic Research", type="primary", use_container_width=True)
    st.caption("Powered by Serper.dev — real Google SERP data")


# ---------- HELPERS ----------
def normalize_domain(line: str) -> str:
    line = (line or "").strip()
    if not line:
        return ""
    if not line.startswith(("http://", "https://")):
        line = "https://" + line
    return (urlparse(line).netloc or line).replace("www.", "")

def domain_of(url: str) -> str:
    try:
        return urlparse(url or "").netloc.replace("www.", "")
    except Exception:
        return ""

def difficulty_for(text):
    random.seed(hash(text) & 0xFFFFFFFF); return random.randint(18, 78)

def opportunity_for(text):
    random.seed((hash(text) ^ 0xA5A5A5) & 0xFFFFFFFF); return random.randint(45, 96)

def tokens_of(text):
    return {t for t in re.findall(r"[a-z][a-z\-]{2,}", (text or "").lower())
            if t not in STOPWORDS and len(t) > 2}

def classify_intent(text):
    t = (text or "").lower()
    if any(w in t for w in ["buy","price","pricing","cost","demo","free trial","discount","quote"]):
        return "Transactional"
    if any(w in t for w in [" vs "," vs.","comparison","alternative","alternatives",
                            "best ","top ","review","reviews"]):
        return "Commercial"
    if any(w in t for w in ["how to","what is","what are","why","guide","tutorial",
                            "explained","examples","definition","meaning"]):
        return "Informational"
    return "Informational"

def google_search_url(query, gl="us"):
    return f"https://www.google.com/search?q={quote_plus(query)}&gl={gl}"

def jaccard(a, b):
    if not a or not b: return 0.0
    return len(a & b) / len(a | b)

def dedupe_topics(ideas, similarity_threshold=0.55):
    """Drop topics with high token overlap with already-kept ideas."""
    kept, kept_token_sets = [], []
    for idea in ideas:
        toks = tokens_of(idea["topic_idea"])
        if not toks: continue
        is_dup = False
        for existing in kept_token_sets:
            if jaccard(toks, existing) >= similarity_threshold:
                is_dup = True; break
        if not is_dup:
            kept.append(idea)
            kept_token_sets.append(toks)
    return kept

def has_brand_modifier(query, seed_tokens):
    """True if query starts with a non-seed, non-generic word (likely a brand/product name)."""
    words = re.findall(r"[a-z][a-z\-]+", (query or "").lower())
    if not words: return False
    first = words[0]
    if first in seed_tokens or first in GENERIC_MODIFIERS:
        return False
    return True

def to_article_title(query):
    """Transform a raw keyword into a real article-shaped headline.
    Returns None if no specific template fits — never falls back to a generic guide."""
    if not query: return None
    q = query.strip().rstrip("?")
    ql = q.lower()
    Y = CURRENT_YEAR

    if is_junk_query(q): return None

    # Already a question — keep as is
    if ql.startswith(("what ","what's ","how ","why ","when ","where ","which ","who ",
                      "is ","are ","can ","do ","does ","should ","will ","how to ")):
        s = q[0].upper() + q[1:]
        return s if s.endswith("?") else s + "?"

    # "best X" / "top X"  — only if rest doesn't have a dated year
    if ql.startswith("best "):
        rest = q[5:].strip()
        if re.search(r"\b20\d\d\b", rest): return None
        return f"The 9 Best {rest.title()} in {Y} (Tested, Compared & Ranked)"
    if ql.startswith("top "):
        rest = q[4:].strip()
        if re.search(r"\b20\d\d\b", rest): return None
        return f"Top {rest.title()}: {Y} Buyer's Guide With Real Comparisons"

    # "free X"
    if ql.startswith("free "):
        rest = q[5:].strip()
        return f"Are Free {rest.title()} Worth It? Honest {Y} Review"

    # "cheap / affordable / budget X"
    if ql.startswith(("cheap ","affordable ","budget ","low cost ","low-cost ")):
        parts = q.split(" ", 1)
        rest = parts[1] if len(parts) > 1 else q
        return f"{rest.title()} on a Budget: {Y}'s Most Affordable Options"

    # "easy / simple / beginner X"
    if ql.startswith(("easy ","simple ","beginner ","beginners ")):
        parts = q.split(" ", 1)
        rest = parts[1] if len(parts) > 1 else q
        return f"The Easiest {rest.title()} for Beginners ({Y} Picks)"

    # "online / cloud / mobile / web-based / saas X"
    if ql.startswith(("online ","cloud ","mobile ","web-based ","web based ","saas ")):
        parts = q.split(" ", 1)
        prefix = parts[0]; rest = parts[1] if len(parts) > 1 else q
        return f"{prefix.title()} {rest.title()}: {Y} Comparison Guide"

    # "open source X"
    if ql.startswith(("open source ","open-source ")):
        rest = re.sub(r"^open[ \-]source ", "", q, flags=re.I)
        return f"Open-Source {rest.title()}: Pros, Cons & Top Picks"

    # "X vs Y" — comparison
    if " vs " in ql or " vs. " in ql:
        return f"{q.title()}: Which Should You Choose in {Y}?"

    # "X cost / price / pricing"
    if re.search(r"\b(cost|price|pricing)\b", ql):
        base = re.sub(r"\b(cost|price|pricing)\b", "", q, flags=re.I).strip()
        if not base: return None
        return f"How Much Does {base.title()} Cost in {Y}? Real Pricing Breakdown"

    # "X alternative(s)"
    if "alternative" in ql:
        return f"{q.title()}: Best Alternatives Compared ({Y})"

    # "X review(s)"
    if "review" in ql:
        return f"{q.title()}: In-Depth {Y} Review (Pros, Cons, Verdict)"

    # "X for sale" / "buy X"
    if " for sale" in ql or ql.startswith("buy "):
        return f"{q.title()}: Where to Buy & What to Look For ({Y})"

    # "X for Y" — common modifier pattern (e.g. "feedlot software for cattle")
    if " for " in ql:
        return f"{q.title()}: A Practical Guide ({Y})"

    # "X management/system/strategy/process/techniques"  — operational topic
    if any(w in ql for w in [" management"," system"," strategy"," strategies",
                             " process"," techniques"," practices"," methods"]):
        return f"{q.title()}: Practical Playbook for {Y}"

    # Substantive 3+ word query with a clear modifier (e.g. "cattle feedlot management")
    # Keep the original phrasing but frame it as a focused guide.
    if len(q.split()) >= 3:
        return f"{q.title()}: A Focused Guide ({Y})"

    # 2-word phrase — too thin for a clear angle without context
    return None

def rationale_for(source, comp_domain):
    if "Reddit" in source:
        return ("Real users actively discussing this on Reddit — strong human-demand signal with "
                "real pain points. Perplexity and ChatGPT heavily cite Reddit threads, so a "
                "definitive guide here can capture both Google traffic AND become the LLM-cited "
                "answer for this query.")
    if "Quora" in source:
        return ("People asking this exact question on Quora — direct demand signal that often "
                "precedes Google's PAA. Quora questions map to long-tail Google searches with "
                "lower competition than head terms.")
    if "People Also Ask" in source:
        return ("Google explicitly surfaces this question on the SERP — direct, validated demand. "
                "Pages that answer it cleanly capture the AI Overview slot AND get cited by "
                "ChatGPT/Perplexity for the same question.")
    if "Related Search" in source:
        return ("Google's 'searches related to' identifies this as part of the topic cluster around "
                "your seed keyword. Covering it strengthens topical authority and unlocks long-tail "
                "traffic the head term doesn't capture.")
    if "Competitor Article" in source and comp_domain:
        return (f"{comp_domain} currently captures search traffic with this exact angle — they've "
                "already validated demand and the SERP rewards this format. Match their depth, then "
                "beat them on freshness, originality, and structured data.")
    return "Real SERP signal — covering this fills a measurable gap in your content map."

def channel_score(topic, intent, source):
    """LLM-first (AEO) | Google-first (SEO) | Both."""
    t = (topic or "").lower()
    is_question = bool(re.match(r"(what|how|why|when|where|which|who|is |are |can |does |do )", t)) \
                  or t.endswith("?") or "people also ask" in source.lower()
    is_definitional = any(w in t for w in ["what is","what are","definition","meaning","explained"])
    is_listicle = bool(re.match(r"(top|best|\d+ )", t)) or "best " in t or "top " in t
    is_comparison = " vs " in t or "comparison" in t or "alternative" in t

    llm_friendly = is_question or is_definitional or intent == "Informational"
    google_friendly = is_listicle or is_comparison or intent in ("Commercial","Transactional")

    if llm_friendly and google_friendly: return "Both (Google + LLM)"
    if llm_friendly: return "LLM-first (AEO)"
    return "Google-first (SEO)"


# ---------- QUALITY FILTER FOR COMPETITOR ARTICLES ----------
def is_quality_article(title, link, keyword_tokens):
    """Reject competitor nav, brand, category pages. Keep real articles."""
    if not title or not link: return False
    title = title.strip()
    if len(title) < 22 or len(title) > 220: return False

    # "X | Brand" or "X - Brand" with very short X → nav/category
    for sep in (" | ", " - ", " – ", " — "):
        if sep in title:
            first = title.split(sep)[0].strip()
            if len(first.split()) < 3:
                return False

    first_seg = re.split(r"[\|\-–—:]", title)[0].strip().lower()
    if first_seg in NAV_WORDS:
        return False

    words = title.split()
    if len(words) < 5:
        return False

    if not (tokens_of(title) & keyword_tokens):
        return False

    # Quality signals — pass if any one is true
    url_lower = link.lower()
    has_url_hint  = any(h in url_lower for h in ARTICLE_URL_HINTS)
    has_year      = bool(re.search(r"20[2-9]\d", title))
    has_number    = bool(re.search(r"\b\d{1,3}\b", title))
    first_word    = words[0].lower().strip(":,")
    has_starter   = first_word in ARTICLE_STARTERS or "?" in title
    long_enough   = len(words) >= 7

    if has_url_hint:
        return True
    # Need >=2 of the article-shape signals
    return sum([has_starter, has_year, has_number, long_enough]) >= 2


# ---------- SERPER ----------
@st.cache_data(show_spinner=False, ttl=3600)
def serper_search(query, api_key, gl="us", num=10):
    r = requests.post("https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "gl": gl, "hl": "en", "num": num}, timeout=20)
    r.raise_for_status()
    return r.json()

def _clean_reddit_title(title):
    title = re.sub(r"\s*[:\-]\s*r/\w+.*$", "", title or "", flags=re.I)
    title = re.sub(r"\s*\|\s*Reddit.*$", "", title, flags=re.I)
    title = re.sub(r"\s*-\s*Reddit\s*$", "", title, flags=re.I)
    return title.strip()

def _clean_quora_title(title):
    title = re.sub(r"\s*-\s*Quora\s*$", "", title or "", flags=re.I)
    title = re.sub(r"\s*\|\s*Quora.*$", "", title, flags=re.I)
    return title.strip()

def fetch_community_topics(keyword, serper_key, gl, max_results=8):
    """Real human questions and discussions from Reddit and Quora."""
    out = {"reddit": [], "quora": []}
    try:
        rs = serper_search(f"site:reddit.com {keyword}", serper_key, gl=gl, num=max_results)
        for o in (rs.get("organic") or []):
            title = _clean_reddit_title(o.get("title", ""))
            link  = o.get("link", "")
            snip  = o.get("snippet", "")
            if title and len(title) >= 15 and len(title.split()) >= 4:
                out["reddit"].append({"title": title, "link": link, "snippet": snip})
    except Exception:
        pass
    try:
        qs = serper_search(f"site:quora.com {keyword}", serper_key, gl=gl, num=max_results)
        for o in (qs.get("organic") or []):
            title = _clean_quora_title(o.get("title", ""))
            link  = o.get("link", "")
            snip  = o.get("snippet", "")
            if title and len(title) >= 15 and len(title.split()) >= 4:
                out["quora"].append({"title": title, "link": link, "snippet": snip})
    except Exception:
        pass
    return out

def fetch_competitor_articles(competitor_domain, keyword, serper_key, gl,
                              keyword_tokens, max_pages=10):
    """Pull only quality, article-shaped pages from a competitor for a keyword."""
    try:
        serp = serper_search(f"site:{competitor_domain} {keyword}",
                             serper_key, gl=gl, num=max_pages)
    except Exception:
        return []
    out = []
    for o in (serp.get("organic") or []):
        title = (o.get("title") or "").strip()
        link  = (o.get("link") or "").strip()
        snip  = (o.get("snippet") or "").strip()
        if is_quality_article(title, link, keyword_tokens):
            out.append({"title": title, "link": link, "snippet": snip})
    return out


# ---------- YOUR-SITE PROFILER ----------
def profile_your_site(your_domain, serper_key, gl):
    profile = {"titles": [], "tokens": set(), "indexed_count": 0}
    try:
        serp = serper_search(f"site:{your_domain}", serper_key, gl=gl, num=10)
    except Exception:
        return profile, "Could not fetch site index — check the domain spelling."
    organic = serp.get("organic") or []
    profile["indexed_count"] = len(organic)
    for o in organic:
        title = (o.get("title") or "")
        snip  = (o.get("snippet") or "")
        profile["titles"].append(title.lower())
        profile["tokens"] |= tokens_of(title) | tokens_of(snip)
    return profile, None

def auto_seed_keywords(profile, max_seeds=5):
    text = " ".join(profile["titles"])
    grams = re.findall(r"[a-z][a-z\-]{2,}(?:\s+[a-z][a-z\-]{2,}){1,2}", text)
    cleaned = []
    for g in grams:
        words = [w for w in g.split() if w not in STOPWORDS]
        if 2 <= len(words) <= 3 and len(" ".join(words)) > 6:
            cleaned.append(" ".join(words))
    return [phrase for phrase, _ in Counter(cleaned).most_common(max_seeds)]


# ---------- GAP FILTER ----------
def is_new_topic(candidate_text, profile, min_new_tokens=2):
    cand_tokens = tokens_of(candidate_text)
    if not cand_tokens: return False
    cand_lower = (candidate_text or "").lower().strip()
    for t in profile["titles"]:
        if cand_lower and cand_lower in t: return False
    return len(cand_tokens - profile["tokens"]) >= min_new_tokens


# ---------- TOPIC RESEARCH ENGINE ----------
def research_keyword(keyword, your_domain, profile, serper_key, gl,
                     count, max_competitors, min_new_tokens, expand=True):
    """Surface real topic ideas for a keyword that user does NOT yet cover."""
    keyword_tokens = tokens_of(keyword)
    ideas, seen = [], set()

    def add(topic, intent_hint, source, comp_domain, comp_url, snippet,
            how_to_rank, how_for_llm, raw_query=None):
        # Competitor articles, Reddit, Quora are already real titles — keep verbatim.
        # PAA + Related Searches go through transformation.
        if source.startswith("Competitor Article") or source in ("Reddit Discussion","Quora Question"):
            display_topic = topic
        else:
            display_topic = to_article_title(topic)
            if not display_topic:  # no specific template fit — skip
                return

        key = (display_topic or "").lower().strip()
        if not key or key in seen: return
        if not is_new_topic(display_topic, profile, min_new_tokens=min_new_tokens): return
        if not (tokens_of(display_topic) & keyword_tokens): return
        seen.add(key)
        intent = intent_hint or classify_intent(display_topic)
        ideas.append({
            "your_site": your_domain,
            "seed_keyword": keyword,
            "topic_idea": display_topic,
            "raw_query": raw_query or topic,
            "intent": intent,
            "channel": channel_score(display_topic, intent, source),
            "source": source,
            "why_cover": rationale_for(source, comp_domain),
            "ranking_competitor": comp_domain,
            "competitor_url": comp_url,
            "what_they_cover": (snippet or "")[:240],
            "how_to_rank_google": how_to_rank,
            "how_to_get_cited_by_llms": how_for_llm,
        })

    # Build the list of queries to run (base + expansions for richer PAA pool)
    variants = QUERY_VARIANTS if expand else ["{kw}"]
    query_list = [v.format(kw=keyword) for v in variants]

    base_serp = None
    competitor_domains = []

    for qi, query in enumerate(query_list):
        try:
            serp = serper_search(query, serper_key, gl=gl, num=10)
        except Exception:
            continue
        if qi == 0:
            base_serp = serp

        organic = serp.get("organic") or []
        paa     = serp.get("peopleAlsoAsk") or []
        related = serp.get("relatedSearches") or []
        proof   = organic[0] if organic else {}

        # collect competitor domains from base SERP only (most relevant)
        if qi == 0:
            for o in organic[:6]:
                d = domain_of(o.get("link", ""))
                if d and d != your_domain and d not in competitor_domains:
                    competitor_domains.append(d)

        # PAA — real user questions (already topic-shaped)
        for q in paa:
            question = (q.get("question") or "").strip()
            if not question: continue
            add(
                topic=question,
                intent_hint=classify_intent(question),
                source="People Also Ask",
                comp_domain="google.com",
                comp_url=google_search_url(question, gl=gl),
                snippet=proof.get("snippet", ""),
                how_to_rank=(
                    f"This is a real user question on the '{query}' SERP. Publish a page titled "
                    "around this exact question. Lead with a 50-70 word direct answer (snippet bait), "
                    "then expand: examples, comparison table, FAQ that absorbs related PAA."
                ),
                how_for_llm=(
                    "Use the question verbatim as an H2 with a clean 2-4 sentence answer right "
                    "below. LLMs preferentially cite question/answer pairs. Add FAQPage schema."
                ),
                raw_query=question,
            )

        # Related searches — transform into article titles
        for rel in related:
            rq = rel.get("query") if isinstance(rel, dict) else rel
            rq = (rq or "").strip()
            if not rq: continue
            add(
                topic=rq,
                intent_hint=classify_intent(rq),
                source="Related Search",
                comp_domain="google.com",
                comp_url=google_search_url(rq, gl=gl),
                snippet="Google surfaces this as a related query — strong topic-cluster signal.",
                how_to_rank=(
                    f"Build a dedicated supporting page for '{rq}' and internally link it to your "
                    f"'{keyword}' pillar. Add a comparison table, FAQ, and schema markup."
                ),
                how_for_llm=(
                    "Cover this as a distinct subtopic with its own H2 inside the cluster. "
                    "LLMs cite breadth — full cluster coverage raises citation odds."
                ),
                raw_query=rq,
            )

    # Community discussions — Reddit + Quora (real human questions / pain points)
    community = fetch_community_topics(keyword, serper_key, gl, max_results=8)
    for r in community["reddit"]:
        add(
            topic=r["title"],
            intent_hint="Informational",
            source="Reddit Discussion",
            comp_domain="reddit.com",
            comp_url=r["link"],
            snippet=r["snippet"],
            how_to_rank="",
            how_for_llm="",
            raw_query=r["title"],
        )
    for q in community["quora"]:
        add(
            topic=q["title"],
            intent_hint="Informational",
            source="Quora Question",
            comp_domain="quora.com",
            comp_url=q["link"],
            snippet=q["snippet"],
            how_to_rank="",
            how_for_llm="",
            raw_query=q["title"],
        )

    # Competitor articles (real, filtered) — using base keyword
    for cd in competitor_domains[:max_competitors]:
        articles = fetch_competitor_articles(cd, keyword, serper_key, gl,
                                             keyword_tokens, max_pages=10)
        for art in articles:
            add(
                topic=art["title"],
                intent_hint=classify_intent(art["title"]),
                source=f"Competitor Article — {cd}",
                comp_domain=cd,
                comp_url=art["link"],
                snippet=art["snippet"],
                how_to_rank=(
                    f"**{cd}** ranks with this exact article. To outrank: cover everything they "
                    "cover, then add (a) original data or screenshots, (b) a comparison table, "
                    "(c) a clear methodology section, and (d) an FAQ that absorbs PAA."
                ),
                how_for_llm=(
                    "Match their depth, then add structured elements LLMs love: TL;DR at top, "
                    "bulleted key takeaways, definitions block, citations to primary sources. "
                    "Add Article schema."
                ),
                raw_query=art["title"],
            )

    # Priority: PAA → Reddit → Quora → Competitor → Related
    priority = {"People Also Ask": 0, "Reddit Discussion": 1, "Quora Question": 2}
    def _p(src):
        if src in priority: return priority[src]
        if src.startswith("Competitor"): return 3
        return 4
    ideas.sort(key=lambda g: _p(g["source"]))
    # Dedupe near-identical topic ideas (Jaccard >= 0.55)
    ideas = dedupe_topics(ideas, similarity_threshold=0.55)
    return ideas[:count]


# ---------- MAIN ----------
if not run_analysis:
    st.markdown("""
    <div class="welcome-cta">
      <div>
        <h2>Find what your competitors rank for — and you don't</h2>
        <p>Real Google SERP analysis + competitor article mining + LLM-citation scoring. No fluff topics, no AI hallucinations.</p>
      </div>
      <div class="step-pills">
        <div class="pill">1 · Enter URL</div>
        <div class="pill">2 · Add Seeds</div>
        <div class="pill">3 · Run</div>
      </div>
    </div>

    <div class="welcome-grid">
      <div class="feat-card">
        <div class="icon-wrap icon-orange">🔍</div>
        <h3>Site Profiling</h3>
        <p>We scan your existing pages via real Google index data, then filter every suggested topic against what you already cover — so you only ever see <b>new</b> ideas.</p>
      </div>
      <div class="feat-card">
        <div class="icon-wrap icon-blue">📊</div>
        <h3>Competitor Mining</h3>
        <p>We pull the actual article titles your top-ranking competitors are publishing for each seed keyword — the exact pages winning traffic today.</p>
      </div>
      <div class="feat-card">
        <div class="icon-wrap icon-green">🤖</div>
        <h3>SEO + AEO Ready</h3>
        <p>Each topic is scored for both <b>Google ranking</b> potential (CTR, listicles, comparisons) and <b>LLM citation</b> potential (Q&A, definitions, how-to).</p>
      </div>
    </div>

    <div class="tips">
      <div class="tip-title">💡 Tips for best results</div>
      <ul>
        <li><b>Use 3–5 specific seed keywords</b> rather than one generic term. The narrower the seed, the better the topic ideas.</li>
        <li><b>Leave keywords empty</b> if you want the tool to auto-discover seeds from your site's strongest themes.</li>
        <li><b>Bump up "Competitors mined per keyword"</b> if your niche has many strong players — more sources, richer ideas.</li>
        <li><b>Lower "Gap strictness"</b> if you have a large existing site and few results pass through.</li>
      </ul>
    </div>
    """, unsafe_allow_html=True)
    st.stop()

if not your_site.strip():
    st.warning("Please enter your website URL on the left."); st.stop()
if not serper_key.strip():
    st.warning("Please enter your Serper.dev API key."); st.stop()

your_domain = normalize_domain(your_site)
gl = MARKET_TO_GL.get(market, "us")
seed_keywords = [l.strip() for l in keyword_input.splitlines() if l.strip()]

all_ideas, errors = [], []

with st.status("Running topic research…", expanded=True) as status:
    st.write(f"Profiling **{your_domain}** — scanning what you already cover…")
    profile, prof_err = profile_your_site(your_domain, serper_key, gl)
    if prof_err: st.warning(prof_err)
    st.write(f"Indexed pages sampled: **{profile['indexed_count']}** · "
             f"unique tokens covered: **{len(profile['tokens'])}**")

    if not seed_keywords:
        st.write("No seed keywords provided — auto-discovering from your site…")
        seed_keywords = auto_seed_keywords(profile, max_seeds=5)
        if not seed_keywords:
            status.update(label="Could not auto-discover seeds.", state="error")
            st.error("Your site has too few indexed pages to auto-discover seeds. Paste at least one keyword.")
            st.stop()
        st.write(f"Auto-seeds: **{', '.join(seed_keywords)}**")

    st.write(f"Researching **{len(seed_keywords)}** keyword(s) (expansion: {'on' if use_expansion else 'off'})…")
    for kw in seed_keywords:
        try:
            ideas = research_keyword(
                kw, your_domain, profile, serper_key, gl,
                count=topics_per_keyword,
                max_competitors=competitors_per_keyword,
                min_new_tokens=min_new_tokens,
                expand=use_expansion,
            )
        except Exception as e:
            errors.append(f"'{kw}': {e}"); continue
        st.write(f"  • `{kw}` → **{len(ideas)}** quality topic ideas.")
        all_ideas.extend(ideas)

    # Global dedupe across all seed keywords so the same topic doesn't appear twice
    all_ideas = dedupe_topics(all_ideas, similarity_threshold=0.55)

    status.update(label="Analysis complete", state="complete", expanded=False)

if errors:
    with st.expander(f"{len(errors)} issue(s) during analysis", expanded=not all_ideas):
        for e in errors: st.error(e)

# ---------- KPI OVERVIEW ----------
st.markdown('<div class="section-title"><span class="accent"></span>Overview</div>',
            unsafe_allow_html=True)

llm_count    = sum(1 for g in all_ideas if "LLM" in g["channel"] or "Both" in g["channel"])
google_count = sum(1 for g in all_ideas if "Google" in g["channel"] or "Both" in g["channel"])
unique_competitors = len({g["ranking_competitor"] for g in all_ideas if g["ranking_competitor"]})

community_count = sum(1 for g in all_ideas if g["source"] in ("Reddit Discussion","Quora Question"))

kpis = [
    ("Seed Keywords", len(seed_keywords), "🎯"),
    ("New Topic Ideas", len(all_ideas), "💡"),
    ("Community Signals", community_count, "💬"),
    ("LLM-Citation Topics", llm_count, "🤖"),
    ("Google-Ranking Topics", google_count, "🔍"),
    ("Competitors Found", unique_competitors, "🏆"),
]
cols = st.columns(len(kpis))
for col, (label, value, icon) in zip(cols, kpis):
    col.markdown(f"""
    <div class="kpi">
      <span class="icon">{icon}</span>
      <div class="label">{label}</div>
      <div class="value">{value}</div>
    </div>""", unsafe_allow_html=True)
st.markdown("&nbsp;", unsafe_allow_html=True)

# ---------- RESULTS TABLE ----------
df = pd.DataFrame(all_ideas) if all_ideas else pd.DataFrame()

if df.empty:
    st.info("No new topic ideas surfaced. Try lowering 'Gap strictness', adding more seed keywords, "
            "or increasing 'Competitors mined per keyword'.")
else:
    st.markdown('<div class="section-title"><span class="accent"></span>Topic Ideas (Not Yet Covered on Your Site)</div>',
                unsafe_allow_html=True)

    fcol1, fcol2, fcol3 = st.columns([2, 2, 2])
    with fcol1:
        ch_filter = st.multiselect("Channel",
                                   sorted(df["channel"].unique()),
                                   default=list(df["channel"].unique()))
    with fcol2:
        in_filter = st.multiselect("Intent",
                                   sorted(df["intent"].unique()),
                                   default=list(df["intent"].unique()))
    with fcol3:
        src_filter = st.multiselect("Source",
                                    sorted(df["source"].unique()),
                                    default=list(df["source"].unique()))

    fdf = df[df["channel"].isin(ch_filter) &
             df["intent"].isin(in_filter) &
             df["source"].isin(src_filter)].copy()

    cols_order = ["topic_idea","source","channel","intent","why_cover",
                  "ranking_competitor","competitor_url"]
    cols_order = [c for c in cols_order if c in fdf.columns]

    st.dataframe(
        fdf[cols_order],
        use_container_width=True, hide_index=True,
        column_config={
            "topic_idea":         st.column_config.TextColumn("Topic Idea", width="large"),
            "source":             st.column_config.TextColumn("Source", width="small"),
            "channel":            st.column_config.TextColumn("Channel", width="small"),
            "intent":             st.column_config.TextColumn("Intent", width="small"),
            "why_cover":          st.column_config.TextColumn("Why Cover This", width="large"),
            "ranking_competitor": st.column_config.TextColumn("Source / Competitor", width="small"),
            "competitor_url":     st.column_config.LinkColumn("Source URL"),
        }
    )

    st.download_button(
        "⬇️ Download CSV",
        fdf[cols_order].to_csv(index=False).encode("utf-8"),
        "topic_ideas.csv", "text/csv"
    )

    try:
        mix = fdf["channel"].value_counts().reset_index()
        mix.columns = ["channel", "count"]
        fig = px.pie(mix, names="channel", values="count", hole=0.55,
                     title="Channel mix")
        fig.update_layout(plot_bgcolor=T["plot_bg"], paper_bgcolor=T["plot_bg"],
                          font_color=T["ink"])
        st.plotly_chart(fig, use_container_width=True)
    except Exception:
        pass
