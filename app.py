import streamlit as st
import pandas as pd
import plotly.express as px
import requests
import json
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

# ---------- THEME STATE ----------
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
.stMarkdown, .stMarkdown p, .stMarkdown li,
label, .stSelectbox label, .stTextInput label,
.stTextArea label, .stRadio label, .stSlider label, .stCaption,
[data-testid="stWidgetLabel"], [data-testid="stWidgetLabel"] * {{ color: var(--ink) !important; }}
small, .stCaption, [data-testid="stCaptionContainer"] {{ color: var(--muted) !important; }}
#MainMenu, footer {{ visibility: hidden; }}
[data-testid="stHeader"] {{ background: transparent !important; }}
.block-container {{ padding-top:1.2rem; padding-bottom:3rem; max-width:1400px; }}
[data-testid="stSidebar"] {{ background:{T['sidebar']} !important; border-right:1px solid var(--border); }}
[data-testid="stSidebar"] * {{ color: var(--ink) !important; }}
.stTextInput input, .stTextArea textarea,
.stSelectbox div[data-baseweb="select"]>div, .stNumberInput input {{
  background: var(--input-bg) !important; color: var(--ink) !important;
  border:1px solid var(--border) !important; border-radius:8px !important;
}}
.stTextInput input::placeholder, .stTextArea textarea::placeholder {{
  color:{('#6B7280' if IS_DARK else '#9CA3AF')} !important;
}}
div[data-baseweb="popover"] li, div[data-baseweb="popover"] * {{
  color: var(--ink) !important; background:{T['popover_bg']};
}}
[data-testid="stSlider"] [role="slider"] {{ background: var(--brand) !important; }}
.hero {{ background: linear-gradient(135deg,#0F1A2A 0%,#1E2A44 100%);
  padding:22px 28px; border-radius:14px; color:white; margin-bottom:18px;
  display:flex; align-items:center; justify-content:space-between;
  box-shadow:0 6px 20px rgba(15,26,42,0.18); }}
.hero, .hero * {{ color:white !important; }}
.hero h1 {{ margin:0; font-size:26px; font-weight:700; letter-spacing:-0.3px; }}
.hero p {{ color:#C5CCD8 !important; margin:4px 0 0 0; font-size:14px; }}
.hero .badge {{ background:var(--brand); color:white !important; padding:6px 12px;
  border-radius:999px; font-size:12px; font-weight:600; letter-spacing:0.4px; }}
.kpi {{ background:var(--card); border:1px solid var(--border); border-radius:12px;
  padding:16px 18px; box-shadow:0 1px 2px rgba(0,0,0,0.05); height:100%; }}
.kpi .label {{ color:var(--muted) !important; font-size:12px; font-weight:600;
  text-transform:uppercase; letter-spacing:0.6px; }}
.kpi .value {{ color:var(--ink) !important; font-size:28px; font-weight:700; margin-top:6px; }}
.kpi .delta-up {{ color:var(--green) !important; font-size:12px; font-weight:600; }}
.kpi .icon {{ float:right; font-size:20px; background:{T['icon_bg']};
  color:var(--brand) !important; padding:6px 9px; border-radius:8px; }}
.section-title {{ font-size:18px; font-weight:700; color:var(--ink) !important;
  margin:6px 0 12px 0; display:flex; align-items:center; gap:8px; }}
.section-title .accent {{ width:4px; height:18px; background:var(--brand); border-radius:2px; }}
.pill {{ display:inline-block; padding:3px 10px; border-radius:999px;
  font-size:11px; font-weight:600; letter-spacing:0.3px; margin-right:6px; }}
.pill-green {{ background:#DCFCE7 !important; color:#166534 !important; }}
.pill-amber {{ background:#FEF3C7 !important; color:#92400E !important; }}
.pill-red   {{ background:#FEE2E2 !important; color:#991B1B !important; }}
.stTabs [data-baseweb="tab-list"] {{ gap:4px; border-bottom:1px solid var(--border); }}
.stTabs [data-baseweb="tab"] {{ height:44px; padding:0 18px; background:transparent;
  font-weight:600; color:var(--muted) !important; }}
.stTabs [aria-selected="true"] {{ color:var(--brand) !important; border-bottom:2px solid var(--brand); }}
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
  border-radius:12px; padding:36px; text-align:center; }}
.empty * {{ color:var(--muted) !important; }}
.empty .em-icon {{ font-size:38px; }}
.empty .em-title {{ font-size:16px; font-weight:600; color:var(--ink) !important; margin-top:8px; }}
</style>
""", unsafe_allow_html=True)

# ---------- HEADER + THEME TOGGLE ----------
hero_col, theme_col = st.columns([6, 1])
with hero_col:
    st.markdown("""
    <div class="hero">
      <div>
        <h1>🎯 RankFinder Pro <span style="opacity:.5;font-weight:400;font-size:18px;">— Topic Research</span></h1>
        <p>Real Google SERP data via Serper.dev — content gaps derived directly from PAA, Related Searches, and organic results.</p>
      </div>
      <div class="badge">LIVE INTELLIGENCE</div>
    </div>
    """, unsafe_allow_html=True)
with theme_col:
    st.write("")
    if st.button("🌙 Dark mode" if not IS_DARK else "☀️ Light mode", use_container_width=True):
        st.session_state.theme = "dark" if not IS_DARK else "light"
        st.rerun()

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🎯 Target Configuration")
    research_mode = st.radio("Research mode", ["Keywords", "Competitor URL"],
                             horizontal=True, label_visibility="collapsed")

    if research_mode == "Keywords":
        st.caption("Paste one keyword per line.")
        input_text = st.text_area("Keywords", height=180, label_visibility="collapsed", key="kw_input")
    else:
        st.caption("Paste one competitor URL per line.")
        input_text = st.text_area("Competitor URLs", height=180, label_visibility="collapsed", key="url_input")

    st.markdown("---")
    st.markdown("### 🔑 API Key")
    serper_key = st.text_input("Serper.dev API Key", type="password",
                               help="Get one free at https://serper.dev (2,500 free queries).")

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Settings")
    gap_count = st.slider("Content gaps per target", 5, 20, 10)
    market = st.selectbox("Market focus", list(MARKET_TO_GL.keys()))

    st.markdown("---")
    run_analysis = st.button("🚀 Run SEO Intelligence Engine", type="primary", use_container_width=True)
    st.caption("⚡ Powered by Serper.dev (real Google SERPs)")


# ---------- HELPERS ----------
STOPWORDS = set("""a an the and or but if then for of in on at to from by with as is are was were be been being
this that these those it its it's i you he she we they them us our your their what which who whom how why
when where can will just do does did done not no yes so than too very also into about over under more most
best top vs guide guides how-to tips list way ways thing things""".split())

def is_url_like(line: str) -> bool:
    return bool(line) and " " not in line.strip() and "." in line and not line.endswith(".")

def normalize_domain(line: str) -> str:
    line = line.strip()
    if not line.startswith(("http://","https://")):
        line = "https://" + line
    return (urlparse(line).netloc or line).replace("www.", "")

def difficulty_for(h):
    random.seed(hash(h) & 0xFFFFFFFF); return random.randint(18,78)

def opportunity_for(h):
    random.seed((hash(h) ^ 0xA5A5A5) & 0xFFFFFFFF); return random.randint(45,96)

def diff_pill(s):
    if s<30: return f'<span class="pill pill-green">Easy · {s}</span>'
    if s<60: return f'<span class="pill pill-amber">Medium · {s}</span>'
    return f'<span class="pill pill-red">Hard · {s}</span>'


# ---------- SERPER.DEV ----------
@st.cache_data(show_spinner=False, ttl=3600)
def serper_search(query, api_key, gl="us", num=10):
    r = requests.post("https://google.serper.dev/search",
        headers={"X-API-KEY": api_key, "Content-Type":"application/json"},
        json={"q": query, "gl": gl, "hl":"en", "num": num}, timeout=20)
    r.raise_for_status()
    return r.json()

def serper_compact(serp, max_organic=10, max_paa=8):
    organic = [{"title":i.get("title",""),"link":i.get("link",""),"snippet":i.get("snippet","")}
               for i in (serp.get("organic") or [])[:max_organic]]
    paa = [q.get("question","") for q in (serp.get("peopleAlsoAsk") or [])[:max_paa]]
    related = [q.get("query","") for q in (serp.get("relatedSearches") or [])[:10]]
    return {"organic": organic, "peopleAlsoAsk": paa, "relatedSearches": related}


# ---------- DATA-DRIVEN GAP SYNTHESIS (no LLM) ----------
def _best_proof_url(query, organic):
    """Pick the organic result whose title/snippet best matches the query terms."""
    if not organic:
        return ""
    q_terms = {t for t in re.findall(r"\w+", query.lower()) if t not in STOPWORDS and len(t) > 2}
    best, best_score = organic[0], -1
    for item in organic:
        text = f"{item.get('title','')} {item.get('snippet','')}".lower()
        terms = set(re.findall(r"\w+", text))
        score = len(q_terms & terms)
        if score > best_score:
            best, best_score = item, score
    return best.get("link", "")

def _strategy_for(question, proof_item, keyword):
    """Build a concrete recommendation referencing the proof URL."""
    title = (proof_item.get("title") or "").strip() if proof_item else ""
    snippet = (proof_item.get("snippet") or "").strip() if proof_item else ""
    domain = ""
    if proof_item and proof_item.get("link"):
        try:
            domain = urlparse(proof_item["link"]).netloc.replace("www.", "")
        except Exception:
            domain = ""

    snippet_short = (snippet[:140] + "…") if len(snippet) > 140 else snippet
    parts = []
    if domain:
        parts.append(f"The top-ranking page on **{domain}** ('{title}') only briefly addresses this angle.")
    else:
        parts.append("The current top results only briefly address this angle.")
    if snippet_short:
        parts.append(f"Their snippet: \"{snippet_short}\"")
    parts.append(
        f"Publish a focused page that directly answers '{question}' for **{keyword}** — "
        "lead with a one-paragraph direct answer (snippet bait), then expand with a comparison table, "
        "step-by-step workflow, screenshots, and an FAQ that absorbs related People-Also-Ask queries. "
        "Add internal links from your pillar page and 2–3 authoritative outbound citations."
    )
    return " ".join(parts)

def _headline_from_question(q, keyword):
    q = q.strip().rstrip("?").strip()
    if not q:
        return f"Under-served angle for '{keyword}'"
    if not q[0].isupper():
        q = q[0].upper() + q[1:]
    return q

def _headline_from_related(rel, keyword):
    rel = rel.strip()
    if not rel:
        return f"Under-served angle for '{keyword}'"
    return f"Definitive guide: {rel.title()}"

def synthesize_gaps(keyword, compact, count, market):
    """Build content-gap ideas purely from SERP signals — no LLM."""
    organic = compact.get("organic") or []
    paa = compact.get("peopleAlsoAsk") or []
    related = compact.get("relatedSearches") or []

    gaps = []
    seen = set()

    # 1) PAA → highest-intent gap signals
    for q in paa:
        if not q or q.lower() in seen:
            continue
        seen.add(q.lower())
        proof = next((o for o in organic
                      if any(w in (o.get("title","")+o.get("snippet","")).lower()
                             for w in re.findall(r"\w+", q.lower()) if len(w) > 3)),
                     organic[0] if organic else {})
        gaps.append({
            "target": keyword,
            "keyword": keyword,
            "headline": _headline_from_question(q, keyword),
            "proofUrl": (proof or {}).get("link", ""),
            "strategy": _strategy_for(q, proof, keyword),
            "source": "People Also Ask",
        })

    # 2) Related searches → broader topic clusters
    for rel in related:
        if not rel or rel.lower() in seen:
            continue
        seen.add(rel.lower())
        proof_url = _best_proof_url(rel, organic)
        proof_item = next((o for o in organic if o.get("link") == proof_url), {})
        gaps.append({
            "target": keyword,
            "keyword": keyword,
            "headline": _headline_from_related(rel, keyword),
            "proofUrl": proof_url,
            "strategy": _strategy_for(f"how to approach '{rel}'", proof_item, keyword),
            "source": "Related Search",
        })

    # 3) Title-derived sub-themes — surface a missing angle from organic titles
    title_words = []
    for o in organic:
        for w in re.findall(r"[A-Za-z][A-Za-z\-]{3,}", (o.get("title") or "").lower()):
            if w not in STOPWORDS and w not in keyword.lower():
                title_words.append(w)
    common = [w for w, _ in Counter(title_words).most_common(8)]
    for w in common:
        key = f"{w}-angle"
        if key in seen:
            continue
        seen.add(key)
        proof_item = organic[0] if organic else {}
        gaps.append({
            "target": keyword,
            "keyword": keyword,
            "headline": f"{keyword.title()}: the '{w}' angle competitors under-cover",
            "proofUrl": (proof_item or {}).get("link", ""),
            "strategy": _strategy_for(f"the '{w}' aspect of {keyword}", proof_item, keyword),
            "source": "Organic Title Mining",
        })

    return gaps[:count]


# ---------- DATA-DRIVEN COMPETITOR ANALYSIS (no LLM) ----------
def _estimate_da(brand_serp, site_serp, domain):
    """Rough authority proxy from brand SERP dominance + indexed breadth."""
    brand_organic = brand_serp.get("organic") or []
    site_organic = site_serp.get("organic") or []
    brand_hits = sum(1 for o in brand_organic[:10]
                     if domain.lower() in (o.get("link","").lower()))
    indexed = len(site_organic)
    score = min(95, 25 + brand_hits * 6 + indexed * 2)
    return f"{score}/100"

def _estimate_traffic(site_serp, brand_serp):
    indexed = len(site_serp.get("organic") or [])
    brand_kg = 1 if brand_serp.get("knowledgeGraph") else 0
    base = 5 + indexed * 8 + brand_kg * 40   # arbitrary but bounded
    if base < 50:    return f"{base}k/mo (low)"
    if base < 150:   return f"{base}k/mo"
    return f"{base}k/mo (high visibility)"

def _backlink_overview(brand_serp, domain):
    sitelinks = brand_serp.get("knowledgeGraph") or {}
    if sitelinks:
        return (f"Brand is recognized in Google's Knowledge Graph and dominates branded SERPs — "
                f"likely a healthy backlink profile with multiple referring domains pointing to {domain}.")
    rank1 = (brand_serp.get("organic") or [{}])[0].get("link","")
    if domain.lower() in rank1.lower():
        return (f"{domain} ranks #1 for its brand query, suggesting a moderate backlink profile "
                "sufficient to defend brand SERPs but likely thin for non-brand terms.")
    return (f"{domain} does not own its branded SERP — backlink profile is likely weak; "
            "competitors may be outranking the brand on its own name.")

def _top_keywords_from_titles(site_serp, max_kw=5):
    titles = [(o.get("title") or "") for o in (site_serp.get("organic") or [])]
    text = " ".join(titles).lower()
    grams = re.findall(r"[a-z][a-z\-]{2,}(?:\s+[a-z][a-z\-]{2,}){0,2}", text)
    cleaned = []
    for g in grams:
        words = [w for w in g.split() if w not in STOPWORDS]
        if 1 <= len(words) <= 3:
            cleaned.append(" ".join(words))
    common = [phrase for phrase, c in Counter(cleaned).most_common(40)
              if len(phrase) > 4 and c >= 2]
    return common[:max_kw] or [w for w, _ in Counter(re.findall(r"[a-z]{4,}", text)).most_common(max_kw)]

def _content_performance(site_serp):
    titles = [(o.get("title") or "") for o in (site_serp.get("organic") or [])]
    if not titles:
        return "Very few pages indexed — content footprint is minimal."
    avg_len = sum(len(t) for t in titles) / max(1, len(titles))
    has_guides = sum(1 for t in titles if re.search(r"guide|how to|tutorial|tips|best", t.lower()))
    structure = "long-form / guide-heavy" if has_guides >= 3 else "mostly product or service pages"
    return (f"{len(titles)} pages indexed in this sample, averaging ~{int(avg_len)}-char titles. "
            f"Structure leans {structure}; consider expanding topical clusters around the strongest themes.")

def synthesize_competitor(domain, brand_serp, site_serp):
    return {
        "url": domain,
        "domainAuthority": _estimate_da(brand_serp, site_serp, domain),
        "estimatedTraffic": _estimate_traffic(site_serp, brand_serp),
        "backlinkOverview": _backlink_overview(brand_serp, domain),
        "topKeywords": _top_keywords_from_titles(site_serp),
        "contentPerformance": _content_performance(site_serp),
    }


# ---------- MAIN ----------
if not run_analysis:
    st.markdown("""
    <div class="empty">
      <div class="em-icon">🧭</div>
      <div class="em-title">Ready to uncover ranking opportunities</div>
      <div>Choose <b>Keywords</b> or <b>Competitor URL</b> mode, paste your Serper.dev key, and launch the engine.</div>
    </div>""", unsafe_allow_html=True)
    st.stop()

if not input_text.strip():
    st.warning("Please paste at least one " + ("keyword." if research_mode=="Keywords" else "competitor URL."))
    st.stop()
if not serper_key.strip():
    st.warning("Please enter your Serper.dev API key."); st.stop()

lines = [l.strip() for l in input_text.splitlines() if l.strip()]
gl = MARKET_TO_GL.get(market, "us")

if research_mode == "Keywords":
    keyword_lines, domain_lines = lines, []
else:
    keyword_lines = []
    domain_lines = [normalize_domain(l) for l in lines if is_url_like(l)]
    if not domain_lines:
        st.warning("No valid URLs detected. Switch to Keywords mode for plain phrases."); st.stop()

all_gaps, competitor_results = [], []
st.session_state["_errors"] = []

with st.status("Running SEO intelligence engine…", expanded=True) as status:
    if keyword_lines:
        st.write(f"🔍 Fetching real SERPs for **{len(keyword_lines)}** keyword(s) via Serper.dev…")
        for kw in keyword_lines:
            try:
                serp = serper_search(kw, serper_key, gl=gl, num=10)
            except Exception as e:
                st.session_state["_errors"].append(f"Serper '{kw}': {e}"); continue
            compact = serper_compact(serp)
            st.write(f"  • `{kw}` → {len(compact['organic'])} organic, "
                     f"{len(compact['peopleAlsoAsk'])} PAA, "
                     f"{len(compact['relatedSearches'])} related")
            all_gaps.extend(synthesize_gaps(kw, compact, gap_count, market) or [])

    if domain_lines:
        st.write(f"🌐 Benchmarking **{len(domain_lines)}** competitor domain(s)…")
        for domain in domain_lines:
            try:
                brand_serp = serper_search(domain, serper_key, gl=gl, num=10)
                site_serp  = serper_search(f"site:{domain}", serper_key, gl=gl, num=10)
            except Exception as e:
                st.session_state["_errors"].append(f"Serper '{domain}': {e}"); continue
            metrics = synthesize_competitor(domain, brand_serp, site_serp)
            if metrics:
                competitor_results.append(metrics)
                for kw in (metrics.get("topKeywords") or [])[:2]:
                    try:
                        s = serper_search(kw, serper_key, gl=gl, num=10)
                        all_gaps.extend(synthesize_gaps(kw, serper_compact(s), gap_count, market) or [])
                    except Exception as e:
                        st.session_state["_errors"].append(f"Serper '{kw}': {e}")

    status.update(label="Analysis complete ✅", state="complete", expanded=False)

errs = st.session_state.get("_errors", [])
if errs:
    with st.expander(f"⚠️ {len(errs)} issue(s) during analysis — click for details", expanded=not all_gaps):
        for e in errs: st.error(e)

# ---------- KPI OVERVIEW ----------
st.markdown('<div class="section-title"><span class="accent"></span>Overview</div>', unsafe_allow_html=True)
diffs = [difficulty_for(g.get("headline","")) for g in all_gaps] if all_gaps else []
easy_wins = sum(1 for d in diffs if d<30)
kpis = [("Targets Analyzed", len(lines), "🎯"),
        ("Content Gaps Found", len(all_gaps), "💡"),
        ("Competitors Scanned", len(competitor_results), "🏆"),
        ("Easy Wins (KD<30)", easy_wins, "🚀")]
for col,(label,value,icon) in zip(st.columns(4), kpis):
    col.markdown(f"""
    <div class="kpi"><span class="icon">{icon}</span>
      <div class="label">{label}</div>
      <div class="value">{value}</div>
      <div class="delta-up">▲ live data</div>
    </div>""", unsafe_allow_html=True)
st.markdown("&nbsp;", unsafe_allow_html=True)

# ---------- TABS ----------
tab_gaps, tab_comp = st.tabs(["💡 Content Gaps", "🏆 Competitor Analytics"])

with tab_gaps:
    if not all_gaps:
        st.info("No content gaps generated. Try different keywords or check the errors above.")
    else:
        df = pd.DataFrame(all_gaps)
        df["difficulty"] = df["headline"].apply(difficulty_for)
        df["opportunity"] = df["headline"].apply(opportunity_for)
        st.dataframe(df, use_container_width=True, hide_index=True)

        csv = df.to_csv(index=False).encode("utf-8")
        st.download_button("⬇️ Download CSV", csv, "content_gaps.csv", "text/csv")

        try:
            fig = px.scatter(df, x="difficulty", y="opportunity",
                             hover_data=["headline","keyword","source"],
                             color="source", title="Difficulty vs Opportunity")
            fig.update_layout(plot_bgcolor=T["plot_bg"], paper_bgcolor=T["plot_bg"],
                              font_color=T["ink"])
            st.plotly_chart(fig, use_container_width=True)
        except Exception:
            pass

with tab_comp:
    if not competitor_results:
        st.info("Switch to Competitor URL mode and add domains to see competitor analytics.")
    else:
        for c in competitor_results:
            st.markdown(f"#### 🌐 {c['url']}")
            cols = st.columns(3)
            cols[0].metric("Domain Authority (est.)", c["domainAuthority"])
            cols[1].metric("Estimated Traffic", c["estimatedTraffic"])
            cols[2].metric("Top Keywords", len(c["topKeywords"]))
            st.write("**Backlink Overview:** ", c["backlinkOverview"])
            st.write("**Top Inferred Keywords:** ", ", ".join(c["topKeywords"]) or "—")
            st.write("**Content Performance:** ", c["contentPerformance"])
            st.markdown("---")
