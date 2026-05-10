import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import re
import random
from collections import Counter
from urllib.parse import urlparse

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

# ---------- CSS ----------
st.markdown(f"""
<style>
:root {{
  --brand:#FF6A3D; --brand-dark:#E04F22;
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
[data-testid="stSidebar"] {{ background:{T['sidebar']} !important; border-right:1px solid var(--border); }}
[data-testid="stSidebar"] * {{ color: var(--ink) !important; }}
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div, .stNumberInput input {{
  background: var(--input-bg) !important; color: var(--ink) !important;
  border:1px solid var(--border) !important; border-radius:8px !important;
}}
[data-testid="stSlider"] [role="slider"] {{ background: var(--brand) !important; }}

.app-header {{
  display:flex; align-items:center; justify-content:space-between;
  padding: 4px 0 14px 0; border-bottom: 1px solid var(--border); margin-bottom: 18px;
}}
.app-title {{ font-size: 22px; font-weight: 700; color: var(--ink); margin:0;
  display:flex; align-items:center; gap:10px; }}
.app-title .dot {{ width:10px; height:10px; border-radius:50%; background:var(--brand); }}
.app-sub {{ font-size: 13px; color: var(--muted); margin-top: 2px; }}

.kpi {{ background:var(--card); border:1px solid var(--border); border-radius:10px;
  padding:14px 16px; height:100%; }}
.kpi .label {{ color:var(--muted) !important; font-size:11px; font-weight:600;
  text-transform:uppercase; letter-spacing:0.5px; }}
.kpi .value {{ color:var(--ink) !important; font-size:24px; font-weight:700; margin-top:4px; }}
.section-title {{ font-size:16px; font-weight:700; color:var(--ink) !important;
  margin:6px 0 12px 0; display:flex; align-items:center; gap:8px; }}
.section-title .accent {{ width:4px; height:16px; background:var(--brand); border-radius:2px; }}

.stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {{
  background:var(--brand) !important; border-color:var(--brand) !important;
  color:white !important; font-weight:600;
}}
.stButton>button[kind="primary"]:hover, .stDownloadButton>button[kind="primary"]:hover {{
  background:var(--brand-dark) !important; border-color:var(--brand-dark) !important;
}}
.stButton>button, .stDownloadButton>button {{
  background:{T['btn_bg']}; color:var(--ink) !important; border:1px solid var(--border);
}}
.empty {{ background:var(--bg-soft); border:1px dashed var(--border);
  border-radius:12px; padding:32px; text-align:center; }}
.empty * {{ color:var(--muted) !important; }}
.empty .em-title {{ font-size:15px; font-weight:600; color:var(--ink) !important; margin-top:6px; }}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER (clean, no big hero) ----------
hcol1, hcol2 = st.columns([8, 2])
with hcol1:
    st.markdown("""
    <div class="app-header">
      <div>
        <div class="app-title"><span class="dot"></span>Topic Research</div>
        <div class="app-sub">Surfaces real topic ideas your competitors rank for that you don't yet cover — built for both Google search and LLM citations.</div>
      </div>
    </div>
    """, unsafe_allow_html=True)
with hcol2:
    st.write("")
    if st.button("Dark mode" if not IS_DARK else "Light mode", use_container_width=True):
        st.session_state.theme = "dark" if not IS_DARK else "light"
        st.rerun()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### Your Website")
    st.caption("Required. We scan what you already cover so we only suggest NEW topics.")
    your_site = st.text_input("Your domain", label_visibility="collapsed")

    st.markdown("---")
    st.markdown("### Seed Keywords")
    st.caption("One per line. Leave empty to auto-discover from your site.")
    keyword_input = st.text_area("Keywords", height=160, label_visibility="collapsed", key="kw_input")

    st.markdown("---")
    st.markdown("### Serper.dev API Key")
    serper_key = st.text_input("Serper key", type="password", label_visibility="collapsed",
                               help="Free 2,500 queries at https://serper.dev")

    st.markdown("---")
    st.markdown("### Settings")
    market = st.selectbox("Market", list(MARKET_TO_GL.keys()))
    topics_per_keyword = st.slider("Topic ideas per keyword", 5, 40, 20)
    competitors_per_keyword = st.slider("Competitors mined per keyword", 1, 5, 3)
    min_new_tokens = st.slider("Gap strictness (min new words)", 1, 4, 2,
        help="Higher = stricter. Topic must introduce this many words your site doesn't cover.")
    use_expansion = st.checkbox("Use query expansion (richer ideas, more API calls)", value=True)

    st.markdown("---")
    run_analysis = st.button("Run Topic Research", type="primary", use_container_width=True)
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
    """
    Reject competitor nav, brand, category pages. Keep only real articles.
    """
    if not title or not link: return False
    title = title.strip()
    if len(title) < 25 or len(title) > 200: return False

    # "X | Brand" or "X - Brand" with short X → likely nav/category
    for sep in (" | ", " - ", " – ", " — "):
        if sep in title:
            first = title.split(sep)[0].strip()
            if len(first.split()) < 4:
                return False

    # First segment is a known nav word
    first_seg = re.split(r"[\|\-–—:]", title)[0].strip().lower()
    if first_seg in NAV_WORDS:
        return False

    words = title.split()
    if len(words) < 5:
        return False

    # Must include at least one seed-keyword token
    title_tokens = tokens_of(title)
    if not (title_tokens & keyword_tokens):
        return False

    # URL hint OR strong article title (How/What/Why/Best/Guide/Top/Ultimate/Complete + length)
    url_lower = link.lower()
    has_url_hint = any(h in url_lower for h in ARTICLE_URL_HINTS)
    first_word = words[0].lower()
    is_article_shape = first_word in {"how","what","why","when","where","which",
                                      "best","top","guide","ultimate","complete",
                                      "the","a","an","is","are","why"} or "?" in title
    if not has_url_hint and not (is_article_shape and len(words) >= 6):
        return False

    return True


# ---------- SERPER ----------
@st.cache_data(show_spinner=False, ttl=3600)
def serper_search(query, api_key, gl="us", num=10):
    r = requests.post("https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
        json={"q": query, "gl": gl, "hl": "en", "num": num}, timeout=20)
    r.raise_for_status()
    return r.json()

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
            how_to_rank, how_for_llm):
        key = (topic or "").lower().strip()
        if not key or key in seen: return
        if not is_new_topic(topic, profile, min_new_tokens=min_new_tokens): return
        # must mention at least one seed-keyword token (relevance gate)
        if not (tokens_of(topic) & keyword_tokens): return
        seen.add(key)
        intent = intent_hint or classify_intent(topic)
        ideas.append({
            "your_site": your_domain,
            "seed_keyword": keyword,
            "topic_idea": topic,
            "intent": intent,
            "channel": channel_score(topic, intent, source),
            "source": source,
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

        # PAA — real user questions
        for q in paa:
            question = (q.get("question") or "").strip()
            add(
                topic=question,
                intent_hint=classify_intent(question),
                source="People Also Ask",
                comp_domain=domain_of(proof.get("link", "")),
                comp_url=proof.get("link", ""),
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
            )

        # Related searches — cluster expansion
        for rel in related:
            rq = rel.get("query") if isinstance(rel, dict) else rel
            rq = (rq or "").strip()
            add(
                topic=rq,
                intent_hint=classify_intent(rq),
                source="Related Search",
                comp_domain="",
                comp_url="",
                snippet="Surfaced by Google as a related query — strong topic-cluster signal.",
                how_to_rank=(
                    f"Build a dedicated supporting page for '{rq}' and internally link it to your "
                    f"'{keyword}' pillar to build topic-cluster authority Google rewards."
                ),
                how_for_llm=(
                    "Cover this as a distinct subtopic with its own H2 inside the cluster. "
                    "LLMs cite breadth — full cluster coverage raises citation odds."
                ),
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
            )

    # Priority order: PAA → Competitor articles → Related
    rank = {"People Also Ask": 0}
    ideas.sort(key=lambda g: (rank.get(g["source"],
               1 if g["source"].startswith("Competitor") else 2)))
    return ideas[:count]


# ---------- MAIN ----------
if not run_analysis:
    st.markdown("""
    <div class="empty">
      <div class="em-title">Ready to find topics you don't yet cover</div>
      <div>Enter your website URL on the left, optionally paste seed keywords, add your Serper.dev key, and run.</div>
    </div>""", unsafe_allow_html=True)
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

kpis = [
    ("Seed Keywords", len(seed_keywords)),
    ("New Topic Ideas", len(all_ideas)),
    ("LLM-Citation Topics", llm_count),
    ("Google-Ranking Topics", google_count),
    ("Competitors Found", unique_competitors),
]
cols = st.columns(len(kpis))
for col, (label, value) in zip(cols, kpis):
    col.markdown(f"""
    <div class="kpi">
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
    df["difficulty"]  = df["topic_idea"].apply(difficulty_for)
    df["opportunity"] = df["topic_idea"].apply(opportunity_for)

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

    cols_order = ["topic_idea","channel","intent","source",
                  "ranking_competitor","competitor_url",
                  "what_they_cover","how_to_rank_google","how_to_get_cited_by_llms",
                  "seed_keyword","difficulty","opportunity"]
    cols_order = [c for c in cols_order if c in fdf.columns]

    st.dataframe(
        fdf[cols_order],
        use_container_width=True, hide_index=True,
        column_config={
            "topic_idea":               st.column_config.TextColumn("Topic Idea", width="large"),
            "channel":                  st.column_config.TextColumn("Best Channel", width="small"),
            "intent":                   st.column_config.TextColumn("Intent", width="small"),
            "source":                   st.column_config.TextColumn("Source", width="small"),
            "ranking_competitor":       st.column_config.TextColumn("Competitor", width="small"),
            "competitor_url":           st.column_config.LinkColumn("Competitor URL"),
            "what_they_cover":          st.column_config.TextColumn("What They Cover", width="medium"),
            "how_to_rank_google":       st.column_config.TextColumn("How To Rank on Google", width="large"),
            "how_to_get_cited_by_llms": st.column_config.TextColumn("How To Get Cited by LLMs", width="large"),
            "seed_keyword":             st.column_config.TextColumn("Seed", width="small"),
        }
    )

    st.download_button(
        "Download CSV",
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
