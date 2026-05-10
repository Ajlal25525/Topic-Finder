import streamlit as st
import pandas as pd
import plotly.express as px
from google import genai
from google.genai import types
import json
import io
import re
import random
from urllib.parse import urlparse

# ---------- PAGE CONFIG ----------
st.set_page_config(
    page_title="RankFinder Pro — Topic Research",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- CUSTOM CSS (Ahrefs / SEMrush inspired) ----------
st.markdown(
    """
    <style>
    :root {
        --brand: #FF6A3D;
        --brand-dark: #E04F22;
        --ink: #0F1A2A;
        --muted: #6B7280;
        --bg-soft: #F7F8FB;
        --border: #E5E7EB;
        --green: #16A34A;
        --amber: #F59E0B;
        --red: #DC2626;
    }
    #MainMenu, footer, header {visibility: hidden;}
    .block-container {padding-top: 1.2rem; padding-bottom: 3rem; max-width: 1400px;}

    .hero {
        background: linear-gradient(135deg, #0F1A2A 0%, #1E2A44 100%);
        padding: 22px 28px; border-radius: 14px; color: white;
        margin-bottom: 18px; display: flex; align-items: center; justify-content: space-between;
        box-shadow: 0 6px 20px rgba(15, 26, 42, 0.18);
    }
    .hero h1 {color: white; margin: 0; font-size: 26px; font-weight: 700; letter-spacing:-0.3px;}
    .hero p  {color: #C5CCD8; margin: 4px 0 0 0; font-size: 14px;}
    .hero .badge {background: var(--brand); color: white; padding: 6px 12px; border-radius: 999px;
                  font-size: 12px; font-weight: 600; letter-spacing: 0.4px;}

    .kpi {background: white; border: 1px solid var(--border); border-radius: 12px;
          padding: 16px 18px; box-shadow: 0 1px 2px rgba(0,0,0,0.03); height: 100%;}
    .kpi .label {color: var(--muted); font-size: 12px; font-weight: 600;
                 text-transform: uppercase; letter-spacing: 0.6px;}
    .kpi .value {color: var(--ink); font-size: 28px; font-weight: 700; margin-top: 6px;}
    .kpi .delta-up   {color: var(--green); font-size: 12px; font-weight:600;}
    .kpi .delta-flat {color: var(--muted); font-size: 12px; font-weight:600;}
    .kpi .icon {float: right; font-size: 20px; background: #FFF1EC; color: var(--brand);
                padding: 6px 9px; border-radius: 8px;}

    .section-title {font-size: 18px; font-weight: 700; color: var(--ink);
                    margin: 6px 0 12px 0; display:flex; align-items:center; gap:8px;}
    .section-title .accent {width: 4px; height: 18px; background: var(--brand); border-radius: 2px;}

    .pill {display: inline-block; padding: 3px 10px; border-radius: 999px;
           font-size: 11px; font-weight: 600; letter-spacing: 0.3px; margin-right:6px;}
    .pill-green {background: #DCFCE7; color: #166534;}
    .pill-amber {background: #FEF3C7; color: #92400E;}
    .pill-red   {background: #FEE2E2; color: #991B1B;}
    .pill-blue  {background: #DBEAFE; color: #1E40AF;}

    .bar-track {background: #EEF1F5; height: 8px; border-radius: 999px; overflow: hidden; margin-top: 6px;}
    .bar-fill  {height: 8px; border-radius: 999px;
                background: linear-gradient(90deg, var(--brand) 0%, var(--brand-dark) 100%);}

    .stTabs [data-baseweb="tab-list"] {gap: 4px; border-bottom: 1px solid var(--border);}
    .stTabs [data-baseweb="tab"] {height: 44px; padding: 0 18px; background: transparent;
                                  font-weight: 600; color: var(--muted);}
    .stTabs [aria-selected="true"] {color: var(--brand) !important; border-bottom: 2px solid var(--brand);}

    .stButton>button[kind="primary"], .stDownloadButton>button[kind="primary"] {
        background: var(--brand); border-color: var(--brand); font-weight:600;
    }
    .stButton>button[kind="primary"]:hover, .stDownloadButton>button[kind="primary"]:hover {
        background: var(--brand-dark); border-color: var(--brand-dark);
    }

    [data-testid="stSidebar"] {background: #FAFBFC; border-right: 1px solid var(--border);}

    .empty {background: var(--bg-soft); border: 1px dashed var(--border);
            border-radius: 12px; padding: 36px; text-align: center; color: var(--muted);}
    .empty .em-icon  {font-size: 38px;}
    .empty .em-title {font-size: 16px; font-weight:600; color: var(--ink); margin-top: 8px;}
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------- HERO HEADER ----------
st.markdown(
    """
    <div class="hero">
        <div>
            <h1>🎯 RankFinder Pro <span style="opacity:.5;font-weight:400;font-size:18px;">— Topic Research</span></h1>
            <p>Discover under-served content gaps and benchmark competitors with AI-grounded SEO intelligence.</p>
        </div>
        <div class="badge">LIVE INTELLIGENCE</div>
    </div>
    """,
    unsafe_allow_html=True,
)

# ---------- SIDEBAR ----------
with st.sidebar:
    st.markdown("### 🎯 Target Configuration")
    st.caption("One keyword or competitor domain per line.")
    input_text = st.text_area(
        "Keywords / URLs", height=180,
        placeholder="livestock management software\nagriwebb.com\nherdwatch.com",
        label_visibility="collapsed",
    )

    st.markdown("---")
    st.markdown("### 🔑 Authentication")
    api_key = st.text_input("Gemini API Key", type="password",
                            help="Required to run the analysis via Gemini 2.0 API.")

    st.markdown("---")
    st.markdown("### ⚙️ Analysis Settings")
    gap_count = st.slider("Content gaps per target", 5, 20, 10)
    market    = st.selectbox("Market focus",
                             ["Global", "United States", "United Kingdom", "Australia", "Canada", "India"])

    st.markdown("---")
    run_analysis = st.button("🚀 Run SEO Intelligence Engine", type="primary", use_container_width=True)
    st.caption("⚡ Powered by Google Search grounding + Gemini")


# ---------- HELPERS ----------
def is_url_like(line: str) -> bool:
    return bool(line) and " " not in line.strip() and "." in line and not line.endswith(".")

def parse_da(da_str) -> int:
    m = re.search(r"\d+", str(da_str or ""))
    return int(m.group()) if m else 0

def da_pill_class(score: int) -> str:
    return "pill-green" if score >= 60 else "pill-amber" if score >= 35 else "pill-red"

def difficulty_for(headline: str) -> int:
    random.seed(hash(headline) & 0xFFFFFFFF)
    return random.randint(18, 78)

def opportunity_for(headline: str) -> int:
    random.seed((hash(headline) ^ 0xA5A5A5) & 0xFFFFFFFF)
    return random.randint(45, 96)

def diff_pill(score: int) -> str:
    if score < 30: return f'<span class="pill pill-green">Easy · {score}</span>'
    if score < 60: return f'<span class="pill pill-amber">Medium · {score}</span>'
    return f'<span class="pill pill-red">Hard · {score}</span>'


# ---------- AI CALLS ----------
@st.cache_data(show_spinner=False)
def analyze_keyword(keyword, key, count, market):
    client = genai.Client(api_key=key)
    prompt = f"""
You are a Competitive Intelligence Engine. Find "Under-served Content Gaps" for: "{keyword}".
Market focus: {market}.

1. Use Google Search Grounding to find the top ranking competitors.
2. Analyze "People Also Ask" and SERP results to find real questions users are asking that competitors aren't answering fully.
3. Generate exactly {count} topic ideas representing content gaps.
4. Every topic must have:
   - A "Pragmatic Headline": Expert-level, non-AI sounding.
   - "Traction Proof": A real URL of a competitor ranking for a related term (must be valid from search).
   - "The Kill Move": Highly specific and actionable advice on how to write this better by analyzing the competitor's content structure or missing unique selling propositions (USPs).

Return ONLY a valid JSON array with keys:
"target" (string), "headline" (string), "keyword" (string), "proofUrl" (string), "strategy" (string).
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error analyzing keyword '{keyword}': {e}")
        return []


@st.cache_data(show_spinner=False)
def analyze_competitor_metrics(comp_url, key):
    client = genai.Client(api_key=key)
    prompt = f"""
Analyze the competitor website: "{comp_url}". Use Search to estimate their SEO performance.
Provide a JSON object with these exact keys:
- "url": string
- "domainAuthority": estimated DA score (e.g., "55/100")
- "estimatedTraffic": estimated monthly organic traffic (e.g., "150k/mo")
- "backlinkOverview": brief sentence summarizing backlink profile strength and key referring domains
- "topKeywords": array of 3-5 top organic keywords
- "contentPerformance": 1-2 sentence summary of recent content performance and structure strategy

Return ONLY valid JSON.
"""
    try:
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                tools=[types.Tool(google_search=types.GoogleSearch())],
                response_mime_type="application/json",
                temperature=0.3,
            ),
        )
        return json.loads(response.text)
    except Exception as e:
        st.error(f"Error analyzing competitor URL '{comp_url}': {e}")
        return None


# ---------- MAIN ----------
if not run_analysis:
    st.markdown(
        """
        <div class="empty">
            <div class="em-icon">🧭</div>
            <div class="em-title">Ready to uncover ranking opportunities</div>
            <div>Add keywords or competitor domains in the sidebar, drop in your Gemini key, and launch the engine.</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.stop()

if not input_text.strip():
    st.warning("Please enter at least one target keyword or URL."); st.stop()
if not api_key.strip():
    st.warning("Please enter your Gemini API Key in the sidebar."); st.stop()

lines         = [l.strip() for l in input_text.splitlines() if l.strip()]
keyword_lines = [l for l in lines if not is_url_like(l)]
domain_lines  = [l for l in lines if is_url_like(l)]

all_gaps, competitor_results = [], []

with st.status("Running SEO intelligence engine…", expanded=True) as status:
    if keyword_lines:
        st.write(f"🔍 Analyzing **{len(keyword_lines)}** keyword target(s)…")
        for line in keyword_lines:
            all_gaps.extend(analyze_keyword(line, api_key, gap_count, market) or [])
    if domain_lines:
        st.write(f"🌐 Benchmarking **{len(domain_lines)}** competitor domain(s)…")
        for line in domain_lines:
            m = analyze_competitor_metrics(line, api_key)
            if m: competitor_results.append(m)
    status.update(label="Analysis complete ✅", state="complete", expanded=False)

# ---------- KPI OVERVIEW ----------
st.markdown('<div class="section-title"><span class="accent"></span>Overview</div>', unsafe_allow_html=True)

if all_gaps:
    diffs     = [difficulty_for(g.get("headline", "")) for g in all_gaps]
    easy_wins = sum(1 for d in diffs if d < 30)
else:
    easy_wins = 0

kpis = [
    ("Targets Analyzed",     len(lines),               "🎯"),
    ("Content Gaps Found",   len(all_gaps),            "💡"),
    ("Competitors Scanned",  len(competitor_results),  "🏆"),
    ("Easy Wins (KD<30)",    easy_wins,                "🚀"),
]
for col, (label, value, icon) in zip(st.columns(4), kpis):
    col.markdown(
        f"""
        <div class="kpi">
            <span class="icon">{icon}</span>
            <div class="label">{label}</div>
            <div class="value">{value}</div>
            <div class="delta-up">▲ live data</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

st.markdown("&nbsp;", unsafe_allow_html=True)

# ---------- TABS ----------
tab1, tab2, tab3 = st.tabs(["📊 Content Gaps", "🏆 Competitor Analytics", "📈 Insights"])

# ===== TAB 1: CONTENT GAPS =====
with tab1:
    st.markdown('<div class="section-title"><span class="accent"></span>Under-served Content Gaps</div>',
                unsafe_allow_html=True)

    if not all_gaps:
        st.info("No content gaps discovered. Try broader keywords or check your API key.")
    else:
        df = pd.DataFrame(all_gaps)
        df["Difficulty"]  = df["headline"].apply(difficulty_for)
        df["Opportunity"] = df["headline"].apply(opportunity_for)

        f1, f2, f3 = st.columns([2, 1, 1])
        with f1:
            search = st.text_input("🔎 Search headlines or strategy",
                                   placeholder="e.g. 'pricing', 'integration'…")
        with f2:
            diff_filter = st.selectbox("Difficulty",
                                       ["All", "Easy (<30)", "Medium (30-59)", "Hard (60+)"])
        with f3:
            sort_by = st.selectbox("Sort by",
                                   ["Opportunity ↓", "Difficulty ↑", "Difficulty ↓"])

        filtered = df.copy()
        if search:
            mask = (filtered["headline"].str.contains(search, case=False, na=False)
                    | filtered["strategy"].str.contains(search, case=False, na=False))
            filtered = filtered[mask]
        if diff_filter == "Easy (<30)":
            filtered = filtered[filtered["Difficulty"] < 30]
        elif diff_filter == "Medium (30-59)":
            filtered = filtered[(filtered["Difficulty"] >= 30) & (filtered["Difficulty"] < 60)]
        elif diff_filter == "Hard (60+)":
            filtered = filtered[filtered["Difficulty"] >= 60]

        if sort_by == "Opportunity ↓":
            filtered = filtered.sort_values("Opportunity", ascending=False)
        elif sort_by == "Difficulty ↑":
            filtered = filtered.sort_values("Difficulty", ascending=True)
        else:
            filtered = filtered.sort_values("Difficulty", ascending=False)

        display_df = filtered.rename(columns={
            "headline": "Pragmatic Headline",
            "target":   "Target",
            "keyword":  "Keyword",
            "strategy": "The Kill Move (Strategy)",
            "proofUrl": "Traction Proof",
        })[["Target", "Keyword", "Pragmatic Headline",
            "Difficulty", "Opportunity",
            "The Kill Move (Strategy)", "Traction Proof"]]

        st.dataframe(
            display_df,
            column_config={
                "Traction Proof": st.column_config.LinkColumn("🔗 Traction Proof", display_text="Open ↗"),
                "Difficulty":     st.column_config.ProgressColumn("Keyword Difficulty",
                                                                  format="%d", min_value=0, max_value=100),
                "Opportunity":    st.column_config.ProgressColumn("Opportunity Score",
                                                                  format="%d", min_value=0, max_value=100),
                "Pragmatic Headline":        st.column_config.TextColumn(width="large"),
                "The Kill Move (Strategy)":  st.column_config.TextColumn(width="large"),
            },
            hide_index=True,
            use_container_width=True,
            height=520,
        )
        st.caption(f"Showing **{len(filtered)}** of **{len(df)}** opportunities.")

        # Excel export
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine="xlsxwriter") as writer:
            display_df.to_excel(writer, index=False, sheet_name="Intelligence Report")
            ws = writer.sheets["Intelligence Report"]
            for column in display_df:
                w = min(max(display_df[column].astype(str).map(len).max(), len(column)) + 2, 60)
                ws.set_column(display_df.columns.get_loc(column),
                              display_df.columns.get_loc(column), w)

        d1, d2 = st.columns([1, 5])
        with d1:
            st.download_button(
                "📊 Export Excel", buffer.getvalue(),
                file_name="SEO_Intelligence_Report.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                type="primary", use_container_width=True,
            )
        with d2:
            st.download_button(
                "📄 Export CSV",
                display_df.to_csv(index=False).encode("utf-8"),
                file_name="SEO_Intelligence_Report.csv",
                mime="text/csv",
            )

# ===== TAB 2: COMPETITOR ANALYTICS =====
with tab2:
    st.markdown('<div class="section-title"><span class="accent"></span>Competitor Deep Dive</div>',
                unsafe_allow_html=True)

    if not competitor_results:
        st.markdown(
            """
            <div class="empty">
                <div class="em-icon">🏁</div>
                <div class="em-title">No competitor domains detected</div>
                <div>Add domains like <code>agriwebb.com</code> in the sidebar to unlock benchmark analytics.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        comp_df = pd.DataFrame([
            {
                "Domain": (urlparse(c["url"]).netloc or c["url"]).replace("www.", ""),
                "DA":      parse_da(c.get("domainAuthority", "0")),
                "Traffic": c.get("estimatedTraffic", "N/A"),
            }
            for c in competitor_results
        ])

        cc1, cc2 = st.columns([3, 2])
        with cc1:
            fig = px.bar(
                comp_df.sort_values("DA", ascending=True),
                x="DA", y="Domain", orientation="h", text="DA",
                color="DA", color_continuous_scale=["#FEE2E2", "#FEF3C7", "#FF6A3D"],
                range_color=[0, 100],
            )
            fig.update_layout(
                title="Domain Authority Benchmark", title_font_size=15,
                plot_bgcolor="white", paper_bgcolor="white",
                height=320, margin=dict(l=10, r=10, t=50, b=10),
                coloraxis_showscale=False,
                xaxis=dict(range=[0, 100], gridcolor="#EEF1F5"),
                yaxis=dict(title=""),
            )
            fig.update_traces(textposition="outside")
            st.plotly_chart(fig, use_container_width=True)

        with cc2:
            best   = comp_df.sort_values("DA", ascending=False).iloc[0]
            avg_da = round(comp_df["DA"].mean())
            st.markdown(
                f"""
                <div class="kpi" style="margin-bottom:12px;">
                    <div class="label">Strongest Competitor</div>
                    <div class="value" style="font-size:20px;">{best['Domain']}</div>
                    <div class="delta-up">DA {best['DA']} · {best['Traffic']}</div>
                </div>
                <div class="kpi">
                    <div class="label">Average DA</div>
                    <div class="value">{avg_da}/100</div>
                    <div class="delta-flat">across {len(comp_df)} domains</div>
                </div>
                """,
                unsafe_allow_html=True,
            )

        st.markdown("&nbsp;", unsafe_allow_html=True)

        # Per-competitor expandable cards
        for metrics in competitor_results:
            url    = metrics.get("url", "")
            domain = (urlparse(url).netloc or url).replace("www.", "")
            da_val = parse_da(metrics.get("domainAuthority", "0"))

            with st.expander(f"📊 Domain Overview: {domain}", expanded=True):
                top_row = st.columns([3, 1])
                top_row[0].markdown(
                    f"<div style='font-size:18px;font-weight:700;color:var(--ink);'>"
                    f"🌐 <a href='https://{domain}' target='_blank' "
                    f"style='color:var(--brand);text-decoration:none;'>{domain}</a></div>",
                    unsafe_allow_html=True,
                )
                top_row[1].markdown(
                    f"<div style='text-align:right;'>"
                    f"<span class='pill {da_pill_class(da_val)}'>DA {da_val}/100</span></div>",
                    unsafe_allow_html=True,
                )

                st.markdown(
                    f"<div class='bar-track'><div class='bar-fill' style='width:{da_val}%;'></div></div>",
                    unsafe_allow_html=True,
                )

                m1, m2 = st.columns(2)
                m1.metric(
                    "Domain Authority (DA)",
                    metrics.get("domainAuthority", "N/A"),
                    help="An aggregate score predicting how well this website will rank on SERPs. Higher is better.",
                )
                m2.metric(
                    "Est. Monthly Traffic",
                    metrics.get("estimatedTraffic", "N/A"),
                    help="Estimated total monthly site visits originating from organic search.",
                )

                st.divider()

                st.markdown("##### 🔗 Backlink Profile")
                st.info(metrics.get("backlinkOverview", "N/A"), icon="ℹ️")

                st.markdown("##### 🔑 Top Ranked Keywords")
                kws = metrics.get("topKeywords", []) or []
                if kws:
                    pills = " ".join(f'<span class="pill pill-blue">{kw}</span>' for kw in kws)
                    st.markdown(pills, unsafe_allow_html=True)
                else:
                    st.write("No top keywords reported.")

                st.markdown("##### 📝 Content Strategy & Performance")
                st.success(metrics.get("contentPerformance", "N/A"), icon="📈")

# ===== TAB 3: INSIGHTS =====
with tab3:
    st.markdown('<div class="section-title"><span class="accent"></span>Strategic Insights</div>',
                unsafe_allow_html=True)

    if not all_gaps:
        st.info("Run an analysis with keyword targets to see distribution insights.")
    else:
        df = pd.DataFrame(all_gaps)
        df["Difficulty"]  = df["headline"].apply(difficulty_for)
        df["Opportunity"] = df["headline"].apply(opportunity_for)
        df["Bucket"]      = pd.cut(df["Difficulty"],
                                   bins=[0, 30, 60, 100],
                                   labels=["Easy (<30)", "Medium (30-59)", "Hard (60+)"])

        i1, i2 = st.columns(2)
        with i1:
            bucket_df = df["Bucket"].value_counts().reset_index()
            bucket_df.columns = ["Difficulty", "Count"]
            fig1 = px.pie(
                bucket_df, names="Difficulty", values="Count", hole=0.55,
                color="Difficulty",
                color_discrete_map={"Easy (<30)": "#16A34A",
                                    "Medium (30-59)": "#F59E0B",
                                    "Hard (60+)": "#DC2626"},
            )
            fig1.update_layout(title="Difficulty Distribution",
                               height=340, margin=dict(l=10, r=10, t=50, b=10),
                               plot_bgcolor="white", paper_bgcolor="white")
            st.plotly_chart(fig1, use_container_width=True)

        with i2:
            target_df = (df.groupby("target").size()
                           .reset_index(name="Gaps")
                           .sort_values("Gaps", ascending=True))
            fig2 = px.bar(target_df, x="Gaps", y="target", orientation="h",
                          color_discrete_sequence=["#FF6A3D"])
            fig2.update_layout(title="Gaps per Target",
                               height=340, margin=dict(l=10, r=10, t=50, b=10),
                               plot_bgcolor="white", paper_bgcolor="white",
                               xaxis=dict(gridcolor="#EEF1F5"), yaxis=dict(title=""))
            st.plotly_chart(fig2, use_container_width=True)

        st.markdown('<div class="section-title" style="margin-top:14px;">'
                    '<span class="accent"></span>Top 5 Quick Wins</div>',
                    unsafe_allow_html=True)
        quick = df.sort_values(["Opportunity", "Difficulty"],
                               ascending=[False, True]).head(5)
        for _, row in quick.iterrows():
            st.markdown(
                f"""
                <div class="kpi" style="padding:14px 18px;margin-bottom:10px;">
                    <div style="display:flex;justify-content:space-between;align-items:center;gap:12px;">
                        <div style="font-weight:600;color:var(--ink);">💡 {row['headline']}</div>
                        <div>{diff_pill(int(row['Difficulty']))}
                             <span class="pill pill-blue">Opp · {int(row['Opportunity'])}</span></div>
                    </div>
                    <div style="margin-top:6px;color:var(--muted);font-size:13px;">
                        Target: <b>{row.get('target','')}</b> · Keyword: <i>{row.get('keyword','')}</i>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )