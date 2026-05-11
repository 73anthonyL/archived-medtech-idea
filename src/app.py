"""
Strata — clinical marker intelligence dashboard.

Streamlit entry point. Loads pre-computed pipeline outputs and renders
the four-tab dashboard: Overview, Patient Detail, Marker Explorer,
About / Disclaimer.

Run with:  streamlit run src/app.py
"""

from pathlib import Path
import html as _html

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

_ROOT = Path(__file__).parent.parent
_OUTPUTS = _ROOT / "outputs"


# ---------------------------------------------------------------------------
# Page config (must be first Streamlit call)
# ---------------------------------------------------------------------------

st.set_page_config(
    page_title="Strata — Clinical Marker Intelligence",
    page_icon="⚕",
    layout="wide",
    initial_sidebar_state="collapsed",
)


# ---------------------------------------------------------------------------
# Custom CSS — premium dark-navy clinical theme
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

/* ── Global dark theme ── */
html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
}
.stApp { background-color: #060d1b !important; }
[data-testid="stHeader"] { background-color: #060d1b !important; }
section[data-testid="stSidebar"] { background-color: #080f1e !important; }
.block-container { padding-top: 1.5rem !important; }

/* ── Hero ── */
.strata-hero {
    background: linear-gradient(135deg, #080f1e 0%, #0b1a35 55%, #091528 100%);
    border: 1px solid #1a2e4a;
    border-radius: 16px;
    padding: 1.9rem 2.4rem 1.75rem;
    margin-bottom: 1.5rem;
    position: relative;
    overflow: hidden;
    display: flex;
    align-items: flex-start;
    justify-content: space-between;
    gap: 2rem;
}
.strata-hero::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 55%, #22d3ee 100%);
}
.strata-hero::after {
    content: '';
    position: absolute;
    bottom: -80px; right: -80px;
    width: 260px; height: 260px;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(29,78,216,0.10) 0%, transparent 70%);
    pointer-events: none;
}
.hero-left { flex: 1; position: relative; z-index: 1; }
.hero-right {
    flex-shrink: 0;
    display: flex;
    flex-direction: column;
    align-items: flex-end;
    gap: 0.55rem;
    position: relative;
    z-index: 1;
    padding-top: 0.1rem;
}
.strata-wordmark {
    font-size: 2.6rem;
    font-weight: 800;
    letter-spacing: -0.045em;
    color: #f1f5f9;
    line-height: 1;
    margin-bottom: 0.32rem;
}
.strata-wordmark span { color: #38bdf8; }
.strata-tagline {
    font-size: 0.72rem;
    font-weight: 600;
    color: #334155;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    margin-bottom: 0.6rem;
}
.strata-value-prop {
    font-size: 0.88rem;
    color: #64748b;
    line-height: 1.55;
    max-width: 520px;
    margin-bottom: 1.3rem;
}
.hero-stat-row { display: flex; gap: 0.7rem; flex-wrap: wrap; }
.hero-stat-chip {
    background: rgba(255,255,255,0.045);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 10px;
    padding: 0.6rem 1rem;
    display: flex;
    flex-direction: column;
    min-width: 90px;
}
.hero-stat-value {
    font-size: 1.55rem;
    font-weight: 800;
    color: #f1f5f9;
    line-height: 1;
    letter-spacing: -0.03em;
}
.hero-stat-label {
    font-size: 0.63rem;
    font-weight: 600;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-top: 0.26rem;
}
.hero-stat-chip.high .hero-stat-value     { color: #f87171; }
.hero-stat-chip.moderate .hero-stat-value { color: #fbbf24; }
.hero-stat-chip.avg .hero-stat-value      { color: #38bdf8; }
.demo-mode-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.4em;
    padding: 0.33em 0.85em;
    background: rgba(56,189,248,0.1);
    border: 1px solid rgba(56,189,248,0.28);
    border-radius: 999px;
    font-size: 0.68rem;
    font-weight: 700;
    letter-spacing: 0.1em;
    text-transform: uppercase;
    color: #38bdf8;
}
.demo-mode-badge::before {
    content: '●';
    font-size: 0.55em;
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%, 100% { opacity: 1; }
    50%       { opacity: 0.25; }
}
.hero-disclaimer-inline {
    font-size: 0.68rem;
    color: #334155;
    text-align: right;
    line-height: 1.45;
}

/* ── Metric KPI cards (4-col row) ── */
.metric-card {
    background: #0d1626;
    border: 1px solid #1a2e4a;
    border-radius: 14px;
    padding: 1.4rem 1.4rem 1.2rem;
    text-align: center;
    position: relative;
    overflow: hidden;
}
.metric-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    border-radius: 14px 14px 0 0;
}
.metric-card.total::before    { background: linear-gradient(90deg,#475569,#64748b); }
.metric-card.high::before     { background: linear-gradient(90deg,#dc2626,#f87171); }
.metric-card.moderate::before { background: linear-gradient(90deg,#d97706,#fbbf24); }
.metric-card.avg::before      { background: linear-gradient(90deg,#0284c7,#38bdf8); }
.metric-card .metric-icon {
    font-size: 1.25rem;
    line-height: 1;
    margin-bottom: 0.45rem;
    opacity: 0.7;
}
.metric-card .metric-value {
    font-size: 2.5rem;
    font-weight: 800;
    line-height: 1;
    color: #e2e8f0;
    letter-spacing: -0.045em;
    margin-bottom: 0.35rem;
}
.metric-card .metric-label {
    font-size: 0.67rem;
    font-weight: 600;
    color: #334155;
    text-transform: uppercase;
    letter-spacing: 0.1em;
}
.metric-card.high .metric-value     { color: #f87171; }
.metric-card.moderate .metric-value { color: #fbbf24; }
.metric-card.avg .metric-value      { color: #38bdf8; }

/* ── Risk badges ── */
.risk-badge {
    display: inline-flex;
    align-items: center;
    gap: 0.38em;
    padding: 0.28em 0.78em;
    border-radius: 999px;
    font-size: 0.72rem;
    font-weight: 700;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    white-space: nowrap;
}
.risk-badge::before { content: '●'; font-size: 0.52em; line-height: 1; }
.risk-badge.high     { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.risk-badge.moderate { background: rgba(245,158,11,0.15); color: #fbbf24; border: 1px solid rgba(245,158,11,0.3); }
.risk-badge.low      { background: rgba(34,197,94,0.12);  color: #4ade80; border: 1px solid rgba(34,197,94,0.25); }

/* ── Section headings ── */
.section-heading {
    display: flex;
    align-items: center;
    gap: 0.8rem;
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #334155;
    margin: 2rem 0 0.85rem 0;
}
.section-heading::after {
    content: '';
    flex: 1;
    height: 1px;
    background: #1a2e4a;
}
.section-subtext {
    font-size: 0.8rem;
    color: #334155;
    margin-top: -0.5rem;
    margin-bottom: 0.9rem;
}

/* ── Filter panel header ── */
.filter-panel-header {
    background: #0d1626;
    border: 1px solid #1a2e4a;
    border-bottom: none;
    border-radius: 14px 14px 0 0;
    padding: 1rem 1.5rem 0.85rem;
    margin-bottom: 0;
}
.filter-panel-title {
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.13em;
    color: #334155;
    margin-bottom: 0.18rem;
}
.filter-panel-sub {
    font-size: 0.78rem;
    color: #1e3050;
}
.filter-panel-widgets {
    background: #0d1626;
    border: 1px solid #1a2e4a;
    border-top: none;
    border-radius: 0 0 14px 14px;
    padding: 0.1rem 1.2rem 1.2rem;
    margin-bottom: 1.5rem;
}

/* ── Custom patient admissions table ── */
.patient-table-wrap {
    width: 100%;
    overflow-x: auto;
    border-radius: 12px;
    border: 1px solid #1a2e4a;
}
table.patient-table {
    width: 100%;
    border-collapse: collapse;
    font-size: 0.82rem;
    background: #0d1626;
}
table.patient-table thead tr {
    background: #0a1322;
    border-bottom: 1px solid #1a2e4a;
}
table.patient-table thead th {
    padding: 0.7rem 1rem;
    text-align: left;
    font-size: 0.63rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
    white-space: nowrap;
}
table.patient-table tbody tr {
    border-bottom: 1px solid #0f1b2e;
}
table.patient-table tbody tr:last-child { border-bottom: none; }
table.patient-table tbody tr:hover { background: rgba(56,189,248,0.04); }
table.patient-table tbody td {
    padding: 0.72rem 1rem;
    color: #94a3b8;
    vertical-align: middle;
}
table.patient-table .td-id    { color: #475569; font-size: 0.77rem; }
table.patient-table .td-score-wrap { display: flex; align-items: center; gap: 0.55rem; }
table.patient-table .td-score {
    font-weight: 700;
    font-size: 0.92rem;
    min-width: 24px;
}
table.patient-table .td-score.high     { color: #f87171; }
table.patient-table .td-score.moderate { color: #fbbf24; }
table.patient-table .td-score.low      { color: #4ade80; }
table.patient-table .score-bar-track {
    width: 48px;
    height: 4px;
    background: #1a2e4a;
    border-radius: 999px;
    overflow: hidden;
    flex-shrink: 0;
}
table.patient-table .score-bar-fill { height: 100%; border-radius: 999px; }
.score-bar-fill.high     { background: linear-gradient(90deg,#ef4444,#f87171); }
.score-bar-fill.moderate { background: linear-gradient(90deg,#d97706,#fbbf24); }
.score-bar-fill.low      { background: linear-gradient(90deg,#16a34a,#4ade80); }
table.patient-table .td-abn {
    text-align: center;
    font-weight: 600;
    color: #64748b;
}
table.patient-table .td-concern {
    color: #475569;
    font-size: 0.78rem;
    max-width: 200px;
    white-space: nowrap;
    overflow: hidden;
    text-overflow: ellipsis;
}

/* ── Clinical cards (patient detail) ── */
.clinical-card {
    background: #0d1626;
    border: 1px solid #1a2e4a;
    border-radius: 12px;
    padding: 1.2rem 1.4rem;
    margin-bottom: 0.85rem;
}
.clinical-card h4 {
    margin: 0 0 0.35rem 0;
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.1em;
    color: #334155;
}
.clinical-card .card-value {
    font-size: 1.9rem;
    font-weight: 800;
    color: #e2e8f0;
    line-height: 1;
    letter-spacing: -0.035em;
}
.clinical-card .card-sub { font-size: 0.82rem; color: #334155; margin-top: 0.25rem; }

/* ── Abnormal marker cards ── */
.marker-card {
    background: #0d1626;
    border: 1px solid #1a2e4a;
    border-left: 3px solid #1a2e4a;
    border-radius: 12px;
    padding: 1.1rem 1.25rem 1rem;
    margin-bottom: 0.75rem;
}
.marker-card.high   { border-left-color: #ef4444; }
.marker-card.low    { border-left-color: #3b82f6; }
.marker-card.normal { border-left-color: #22c55e; }
.marker-card .mk-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 0.55rem;
}
.marker-card .mk-name { font-size: 0.83rem; font-weight: 600; color: #cbd5e1; }
.marker-card .mk-status-badge {
    font-size: 0.64rem;
    font-weight: 700;
    letter-spacing: 0.07em;
    text-transform: uppercase;
    padding: 0.22em 0.6em;
    border-radius: 5px;
    flex-shrink: 0;
}
.marker-card.high .mk-status-badge   { background: rgba(239,68,68,0.15); color: #f87171; }
.marker-card.low .mk-status-badge    { background: rgba(59,130,246,0.15); color: #60a5fa; }
.marker-card.normal .mk-status-badge { background: rgba(34,197,94,0.12);  color: #4ade80; }
.marker-card .mk-value {
    font-size: 1.6rem;
    font-weight: 800;
    line-height: 1;
    letter-spacing: -0.035em;
}
.marker-card.high .mk-value   { color: #f87171; }
.marker-card.low .mk-value    { color: #60a5fa; }
.marker-card.normal .mk-value { color: #4ade80; }
.marker-card .mk-unit  { font-size: 0.8rem; font-weight: 400; color: #334155; margin-left: 0.2em; }
.marker-card .mk-range { font-size: 0.71rem; color: #1e3050; margin-top: 0.3rem; }
.marker-card .mk-aki-tag {
    display: inline-block;
    font-size: 0.65rem;
    color: #38bdf8;
    font-weight: 600;
    letter-spacing: 0.04em;
    margin-top: 0.25rem;
    background: rgba(56,189,248,0.1);
    border-radius: 4px;
    padding: 0.15em 0.5em;
}
.marker-card .mk-blurb {
    font-size: 0.77rem;
    color: #334155;
    margin-top: 0.65rem;
    line-height: 1.5;
    border-top: 1px solid #0f1b2e;
    padding-top: 0.55rem;
}

/* ── AKI risk card ── */
.aki-card {
    background: #0d1626;
    border: 1px solid #1a2e4a;
    border-radius: 14px;
    padding: 1.5rem 1.6rem;
}
.aki-card h4 {
    font-size: 0.67rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.12em;
    color: #334155;
    margin: 0 0 1.1rem 0;
}
.aki-score-row { display: flex; align-items: baseline; gap: 0.3rem; margin-bottom: 0.6rem; }
.aki-score-value { font-size: 3.8rem; font-weight: 900; line-height: 1; letter-spacing: -0.06em; }
.aki-score-denom { font-size: 1rem; font-weight: 400; color: #1e3050; }
.aki-card.high .aki-score-value     { color: #f87171; }
.aki-card.moderate .aki-score-value { color: #fbbf24; }
.aki-card.low .aki-score-value      { color: #4ade80; }
.aki-score-bar-track {
    height: 4px;
    background: #1a2e4a;
    border-radius: 999px;
    margin: 0.75rem 0 1rem;
    overflow: hidden;
}
.aki-score-bar-fill { height: 100%; border-radius: 999px; }
.aki-card.high .aki-score-bar-fill     { background: linear-gradient(90deg,#f87171,#dc2626); }
.aki-card.moderate .aki-score-bar-fill { background: linear-gradient(90deg,#fbbf24,#d97706); }
.aki-card.low .aki-score-bar-fill      { background: linear-gradient(90deg,#4ade80,#16a34a); }
.aki-reasons-label {
    font-size: 0.65rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 0.11em;
    color: #1e3050;
    margin-bottom: 0.35rem;
}
.reason-item {
    display: flex;
    align-items: flex-start;
    gap: 0.5rem;
    font-size: 0.79rem;
    color: #334155;
    padding: 0.38rem 0;
    border-bottom: 1px solid #0f1b2e;
    line-height: 1.4;
}
.reason-item .reason-bullet { color: #1e3050; font-size: 0.65rem; margin-top: 0.2rem; flex-shrink: 0; }
.reason-item:last-child { border-bottom: none; }

/* ── Patient summary card ── */
.patient-summary {
    background: linear-gradient(135deg, #080f1e 0%, #0d1c36 100%);
    border: 1px solid #1a2e4a;
    border-radius: 14px;
    padding: 1.5rem 1.7rem;
    margin-bottom: 0.85rem;
    position: relative;
    overflow: hidden;
}
.patient-summary::before {
    content: '';
    position: absolute;
    top: 0; left: 0; right: 0;
    height: 3px;
    background: linear-gradient(90deg, #1d4ed8, #38bdf8);
}
.patient-summary .ps-id {
    font-size: 0.65rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.13em; color: #1e3050; margin-bottom: 0.28rem;
}
.patient-summary .ps-name {
    font-size: 1.45rem; font-weight: 700; letter-spacing: -0.025em;
    margin-bottom: 1rem; color: #e2e8f0;
}
.patient-summary .ps-pills { display: flex; flex-wrap: wrap; gap: 0.4rem; }
.patient-summary .ps-pill {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.09);
    border-radius: 6px;
    padding: 0.24em 0.72em;
    font-size: 0.74rem; font-weight: 500; color: #475569;
}

/* ── Disclaimer card ── */
.disclaimer-card {
    background: rgba(245,158,11,0.06);
    border: 1px solid rgba(245,158,11,0.18);
    border-left: 3px solid rgba(245,158,11,0.55);
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    font-size: 0.79rem;
    color: #78350f;
    line-height: 1.65;
    margin-top: 1.5rem;
}
.disclaimer-card strong { color: #92400e; }

/* Keep old name as alias */
.disclaimer-box {
    background: rgba(245,158,11,0.06);
    border: 1px solid rgba(245,158,11,0.18);
    border-left: 3px solid rgba(245,158,11,0.55);
    border-radius: 10px;
    padding: 0.85rem 1.2rem;
    font-size: 0.79rem;
    color: #78350f;
    line-height: 1.65;
    margin-top: 1.5rem;
}
.disclaimer-box strong { color: #92400e; }

/* ── Streamlit widget overrides ── */
.stTabs [data-baseweb="tab-list"] {
    gap: 0.15rem;
    border-bottom: 1px solid #1a2e4a;
    background: transparent;
    padding-bottom: 0;
    margin-bottom: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
    font-size: 0.84rem;
    font-weight: 500;
    padding: 0.5rem 1.1rem;
    border-radius: 8px 8px 0 0;
    color: #334155;
    background: transparent;
}
.stTabs [aria-selected="true"] {
    color: #e2e8f0 !important;
    font-weight: 600 !important;
    background: #0d1626 !important;
}
div[data-baseweb="select"] > div {
    background-color: #0d1626 !important;
    border-color: #1a2e4a !important;
    color: #94a3b8 !important;
}
div[data-baseweb="input"] > div {
    background-color: #0d1626 !important;
    border-color: #1a2e4a !important;
}
div[data-baseweb="input"] input { color: #94a3b8 !important; }
div[data-testid="stDataFrameContainer"] {
    background: #0d1626;
    border-radius: 10px;
    border: 1px solid #1a2e4a;
}
div[data-testid="stDataFrameContainer"] table { font-size: 0.82rem; }
details[data-testid="stExpander"] {
    background: #0d1626 !important;
    border: 1px solid #1a2e4a !important;
    border-radius: 10px !important;
}
div[data-testid="stAlert"] {
    background: rgba(56,189,248,0.06) !important;
    border-color: rgba(56,189,248,0.18) !important;
    color: #475569 !important;
    border-radius: 10px !important;
}
.stCheckbox label { color: #64748b !important; }
label[data-testid="stWidgetLabel"] p { color: #475569 !important; }
</style>
"""

st.markdown(CUSTOM_CSS, unsafe_allow_html=True)


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all four pipeline output files."""
    patients = pd.read_csv(_OUTPUTS / "dashboard_patients.csv")
    markers  = pd.read_csv(_OUTPUTS / "patient_marker_summary.csv")
    ts       = pd.read_csv(_OUTPUTS / "patient_timeseries.csv", parse_dates=["charttime"])
    aki      = pd.read_csv(_OUTPUTS / "aki_risk_scores.csv")
    return patients, markers, ts, aki


# ---------------------------------------------------------------------------
# Helper functions
# ---------------------------------------------------------------------------

_TIER_CSS = {"High": "high", "Moderate": "moderate", "Low": "low"}
_TIER_COLORS = {"High": "#f87171", "Moderate": "#fbbf24", "Low": "#4ade80"}

PRIORITY_MARKERS = [
    "creatinine", "bun", "potassium", "bicarbonate",
    "wbc", "hemoglobin", "heart_rate", "map_noninvasive", "map_arterial", "sbp",
]


def risk_badge_html(tier: str) -> str:
    css = _TIER_CSS.get(tier, "low")
    return f'<span class="risk-badge {css}">{tier}</span>'


def metric_card_html(value: str, label: str, css_class: str = "", icon: str = "") -> str:
    icon_html = f'<div class="metric-icon">{icon}</div>' if icon else ""
    return (
        f'<div class="metric-card {css_class}">'
        f'{icon_html}'
        f'<div class="metric-value">{value}</div>'
        f'<div class="metric-label">{label}</div>'
        f'</div>'
    )


def hero_html(total_n: int, high_n: int, mod_n: int, avg_abn: float) -> str:
    return (
        '<div class="strata-hero">'
        # ── Left column
        '<div class="hero-left">'
        '<div class="strata-wordmark">Str<span>a</span>ta</div>'
        '<div class="strata-tagline">Clinical Marker Intelligence &nbsp;·&nbsp; AKI Early-Warning Module</div>'
        '<div class="strata-value-prop">'
        'Surfaces abnormal labs, vital trends, and kidney deterioration signals from structured EHR data.'
        '</div>'
        '<div class="hero-stat-row">'
        f'<div class="hero-stat-chip">'
        f'<span class="hero-stat-value">{total_n}</span>'
        f'<span class="hero-stat-label">Admissions</span>'
        f'</div>'
        f'<div class="hero-stat-chip high">'
        f'<span class="hero-stat-value">{high_n}</span>'
        f'<span class="hero-stat-label">High Risk</span>'
        f'</div>'
        f'<div class="hero-stat-chip moderate">'
        f'<span class="hero-stat-value">{mod_n}</span>'
        f'<span class="hero-stat-label">Moderate Risk</span>'
        f'</div>'
        f'<div class="hero-stat-chip avg">'
        f'<span class="hero-stat-value">{avg_abn:.1f}</span>'
        f'<span class="hero-stat-label">Avg Abnormal Markers</span>'
        f'</div>'
        '</div>'
        '</div>'
        # ── Right column
        '<div class="hero-right">'
        '<span class="demo-mode-badge">Demo Mode</span>'
        '<div class="hero-disclaimer-inline">Not diagnostic<br>For clinical review only</div>'
        '</div>'
        '</div>'
    )


def build_patient_table_html(df: pd.DataFrame) -> str:
    """Render the patient admissions table as a styled HTML table with risk badges and score bars."""
    rows = []
    for _, r in df.iterrows():
        tier  = str(r.get("aki_risk_tier", "Low"))
        score = int(r.get("aki_risk_score", 0))
        css   = _TIER_CSS.get(tier, "low")
        pct   = min(score, 100)
        sex   = "Male" if r.get("gender", "M") == "M" else "Female"
        icu   = "Yes" if r.get("has_icu_stay", False) else "No"
        abn   = int(r.get("abnormal_marker_count", 0))
        concern_raw = str(r.get("top_concern", ""))
        concern_short = _html.escape(concern_raw[:65] + ("…" if len(concern_raw) > 65 else ""))
        concern_title = _html.escape(concern_raw)
        rows.append(
            f'<tr>'
            f'<td class="td-id">{_html.escape(str(r["subject_id"]))}</td>'
            f'<td class="td-id">{_html.escape(str(r["hadm_id"]))}</td>'
            f'<td>{_html.escape(str(r.get("anchor_age", "—")))}</td>'
            f'<td>{sex}</td>'
            f'<td>{icu}</td>'
            f'<td>'
            f'<div class="td-score-wrap">'
            f'<span class="td-score {css}">{score}</span>'
            f'<div class="score-bar-track">'
            f'<div class="score-bar-fill {css}" style="width:{pct}%;"></div>'
            f'</div>'
            f'</div>'
            f'</td>'
            f'<td>{risk_badge_html(tier)}</td>'
            f'<td class="td-abn">{abn}</td>'
            f'<td class="td-concern" title="{concern_title}">{concern_short}</td>'
            f'</tr>'
        )
    rows_html = "\n".join(rows)
    return (
        '<div class="patient-table-wrap">'
        '<table class="patient-table">'
        '<thead><tr>'
        '<th>Subject ID</th><th>Admission ID</th><th>Age</th><th>Sex</th>'
        '<th>ICU</th><th>AKI Risk Score</th><th>Risk Tier</th>'
        '<th>Abnormal Markers</th><th>Top Concern</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table>'
        '</div>'
    )


def marker_card_html(
    name: str,
    value: float,
    unit: str,
    status: str,
    normal_low,
    normal_high,
    explanation: str,
    is_aki_relevant: bool,
) -> str:
    css = status.lower() if status.lower() in ("high", "low") else "normal"
    range_parts = []
    if pd.notna(normal_low):
        range_parts.append(f"{normal_low}")
    if pd.notna(normal_high):
        range_parts.append(f"{normal_high}")
    range_str = f"Ref: {' – '.join(range_parts)} {unit}" if range_parts else unit
    aki_tag = '<span class="mk-aki-tag">AKI-Relevant</span>' if is_aki_relevant else ""
    blurb = f'<div class="mk-blurb">{explanation}</div>' if explanation and str(explanation) not in ("nan", "") else ""
    value_fmt = f"{value:.1f}" if pd.notna(value) else "—"
    return (
        f'<div class="marker-card {css}">'
        f'<div class="mk-header">'
        f'<span class="mk-name">{name}</span>'
        f'<span class="mk-status-badge">{status}</span>'
        f'</div>'
        f'<div class="mk-value">{value_fmt}<span class="mk-unit">{unit}</span></div>'
        f'<div class="mk-range">{range_str}</div>'
        f'{aki_tag}'
        f'{blurb}'
        f'</div>'
    )


def patient_summary_html(row: pd.Series) -> str:
    sex_label = "Male" if row.get("gender", "M") == "M" else "Female"
    icu_label = "ICU Admission" if row.get("has_icu_stay", False) else "No ICU"
    los = row.get("length_of_stay_days", 0)
    los_str = f"{los:.1f} days" if pd.notna(los) else "—"
    return (
        f'<div class="patient-summary">'
        f'<div class="ps-id">Admission {row["hadm_id"]}</div>'
        f'<div class="ps-name">Subject {row["subject_id"]}</div>'
        f'<div class="ps-pills">'
        f'<span class="ps-pill">Age {row.get("anchor_age", "—")}</span>'
        f'<span class="ps-pill">{sex_label}</span>'
        f'<span class="ps-pill">{icu_label}</span>'
        f'<span class="ps-pill">{row.get("admission_type", "—")}</span>'
        f'<span class="ps-pill">LOS {los_str}</span>'
        f'</div>'
        f'</div>'
    )


def aki_card_html(row: pd.Series) -> str:
    score = row.get("aki_risk_score", 0)
    tier  = row.get("aki_risk_tier", "Low")
    css   = _TIER_CSS.get(tier, "low")
    reasons_raw = str(row.get("top_reasons", ""))
    reasons = [r.strip() for r in reasons_raw.split("|") if r.strip()] if reasons_raw else []
    reasons_html = "".join(
        f'<div class="reason-item"><span class="reason-bullet">▸</span>{r}</div>'
        for r in reasons[:5]
    )
    pct = min(int(score), 100)
    return (
        f'<div class="aki-card {css}">'
        f'<h4>AKI Risk Signal</h4>'
        f'<div class="aki-score-row">'
        f'<span class="aki-score-value">{score}</span>'
        f'<span class="aki-score-denom">&thinsp;/ 100</span>'
        f'</div>'
        f'{risk_badge_html(tier)}'
        f'<div class="aki-score-bar-track">'
        f'<div class="aki-score-bar-fill" style="width:{pct}%;"></div>'
        f'</div>'
        f'<div class="aki-reasons-label">Contributing signals</div>'
        f'{reasons_html}'
        f'</div>'
    )


def make_trend_chart(ts_df: pd.DataFrame, marker_key: str, marker_name: str, unit: str) -> go.Figure | None:
    """Return a Plotly area chart for a single marker's time series, dark-themed."""
    df = ts_df[ts_df["marker_key"] == marker_key].sort_values("charttime")
    if df.empty:
        return None
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["charttime"],
        y=df["value"],
        mode="lines+markers",
        line=dict(color="#38bdf8", width=2),
        marker=dict(size=5, color="#38bdf8", line=dict(color="#060d1b", width=1.5)),
        fill="tozeroy",
        fillcolor="rgba(56,189,248,0.06)",
        hovertemplate=f"%{{x|%b %d, %H:%M}}<br><b>%{{y:.1f}} {unit}</b><extra></extra>",
    ))
    fig.update_layout(
        title=dict(
            text=f"<b>{marker_name}</b>",
            font=dict(size=13, color="#94a3b8", family="Inter"),
            x=0,
            pad=dict(b=4),
        ),
        margin=dict(l=0, r=0, t=38, b=0),
        height=230,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(
            showgrid=False,
            zeroline=False,
            tickfont=dict(size=10, color="#334155", family="Inter"),
            tickformat="%b %d",
        ),
        yaxis=dict(
            gridcolor="#1a2e4a",
            gridwidth=1,
            zeroline=False,
            tickfont=dict(size=10, color="#334155", family="Inter"),
            title=dict(text=unit, font=dict(size=10, color="#334155")),
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor="#0d1626",
            bordercolor="#1a2e4a",
            font=dict(color="#e2e8f0", size=12, family="Inter"),
        ),
    )
    return fig


def style_tier_column(df: pd.DataFrame) -> "pd.io.formats.style.Styler":
    """Pandas Styler for AKI Risk Tier — used in Marker Explorer table."""
    bg_map = {
        "High":     ("rgba(239,68,68,0.12)",  "#f87171"),
        "Moderate": ("rgba(245,158,11,0.12)", "#fbbf24"),
        "Low":      ("rgba(34,197,94,0.10)",  "#4ade80"),
    }
    def _cell(val):
        bg, fg = bg_map.get(val, ("", ""))
        return f"background-color:{bg};color:{fg};font-weight:600;"
    return df.style.map(_cell, subset=["AKI Risk Tier"])


# ---------------------------------------------------------------------------
# Tab 1 — Overview
# ---------------------------------------------------------------------------

def render_overview(patients: pd.DataFrame) -> None:
    # ── Hero banner
    total_n = len(patients)
    high_n  = int((patients["aki_risk_tier"] == "High").sum())
    mod_n   = int((patients["aki_risk_tier"] == "Moderate").sum())
    avg_abn = patients["abnormal_marker_count"].mean()
    st.markdown(hero_html(total_n, high_n, mod_n, avg_abn), unsafe_allow_html=True)

    # ── KPI metric cards (4-col)
    st.markdown('<div class="section-heading">Overview</div>', unsafe_allow_html=True)
    mc1, mc2, mc3, mc4 = st.columns(4)
    with mc1:
        st.markdown(metric_card_html(str(total_n), "Total Admissions", "total", "🏥"), unsafe_allow_html=True)
    with mc2:
        st.markdown(metric_card_html(str(high_n), "High AKI Risk", "high", "🔴"), unsafe_allow_html=True)
    with mc3:
        st.markdown(metric_card_html(str(mod_n), "Moderate Risk", "moderate", "🟡"), unsafe_allow_html=True)
    with mc4:
        st.markdown(metric_card_html(f"{avg_abn:.1f}", "Avg Abnormal Markers", "avg", "📊"), unsafe_allow_html=True)

    # ── Triage Filters panel
    st.markdown(
        '<div class="filter-panel-header">'
        '<div class="filter-panel-title">Triage Filters</div>'
        '<div class="filter-panel-sub">Narrow admissions by risk tier, ICU status, or admission type.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    st.markdown('<div class="filter-panel-widgets">', unsafe_allow_html=True)
    fc1, fc2, fc3 = st.columns(3)
    with fc1:
        tier_opts = ["All"] + sorted(
            patients["aki_risk_tier"].dropna().unique().tolist(),
            key=lambda t: {"High": 0, "Moderate": 1, "Low": 2}.get(t, 9),
        )
        sel_tier = st.selectbox("AKI Risk Tier", tier_opts, key="ov_tier")
    with fc2:
        sel_icu = st.selectbox("ICU Stay", ["All", "ICU Only", "Non-ICU Only"], key="ov_icu")
    with fc3:
        adm_opts = ["All"] + sorted(patients["admission_type"].dropna().unique().tolist())
        sel_adm  = st.selectbox("Admission Type", adm_opts, key="ov_adm")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Apply filters
    filtered = patients.copy()
    if sel_tier != "All":
        filtered = filtered[filtered["aki_risk_tier"] == sel_tier]
    if sel_icu == "ICU Only":
        filtered = filtered[filtered["has_icu_stay"] == True]
    elif sel_icu == "Non-ICU Only":
        filtered = filtered[filtered["has_icu_stay"] == False]
    if sel_adm != "All":
        filtered = filtered[filtered["admission_type"] == sel_adm]
    filtered = filtered.sort_values("aki_risk_score", ascending=False)

    # ── Patient admissions table (custom HTML)
    st.markdown('<div class="section-heading">Patient Admissions</div>', unsafe_allow_html=True)
    st.markdown(
        f'<div class="section-subtext">'
        f'Admissions ranked by AKI-related risk signals — {len(filtered)} shown.'
        f'</div>',
        unsafe_allow_html=True,
    )
    st.markdown(build_patient_table_html(filtered), unsafe_allow_html=True)

    # ── Disclaimer
    st.markdown(
        '<div class="disclaimer-card">'
        '<strong>Demo only</strong> — Strata does not diagnose AKI or recommend treatment. '
        'All risk scores and abnormal marker flags are early-warning signals for clinical review only.'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tab 2 — Patient Detail
# ---------------------------------------------------------------------------

def render_patient_detail(
    patients: pd.DataFrame,
    markers: pd.DataFrame,
    ts: pd.DataFrame,
    aki: pd.DataFrame,
) -> None:

    st.markdown('<div class="section-heading">Select Admission</div>', unsafe_allow_html=True)

    sorted_pts = patients.sort_values("aki_risk_score", ascending=False)
    options = {
        f"Admission {row.hadm_id}  ·  Subject {row.subject_id}  ·  {row.aki_risk_tier} Risk ({row.aki_risk_score}/100)": int(row.hadm_id)
        for _, row in sorted_pts.iterrows()
    }
    chosen_label = st.selectbox("Choose a patient admission", list(options.keys()), key="detail_sel")
    hadm_id = options[chosen_label]

    pt_row  = patients[patients["hadm_id"] == hadm_id].iloc[0]
    ak_row  = aki[aki["hadm_id"] == hadm_id].iloc[0] if (aki["hadm_id"] == hadm_id).any() else pt_row
    pt_mkrs = markers[markers["hadm_id"] == hadm_id]
    pt_ts   = ts[ts["hadm_id"] == hadm_id]

    # ── Patient summary + AKI card
    col_ps, col_aki = st.columns([1.3, 1])
    with col_ps:
        st.markdown(patient_summary_html(pt_row), unsafe_allow_html=True)
        s1, s2, s3 = st.columns(3)
        with s1:
            abn = int(pt_row.get("abnormal_marker_count", 0))
            st.markdown(
                f'<div class="clinical-card" style="text-align:center;">'
                f'<h4>Abnormal Markers</h4>'
                f'<div class="card-value">{abn}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with s2:
            hi = int(pt_row.get("high_marker_count", 0))
            st.markdown(
                f'<div class="clinical-card" style="text-align:center;">'
                f'<h4>High</h4>'
                f'<div class="card-value" style="color:#f87171;">{hi}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
        with s3:
            lo = int(pt_row.get("low_marker_count", 0))
            st.markdown(
                f'<div class="clinical-card" style="text-align:center;">'
                f'<h4>Low</h4>'
                f'<div class="card-value" style="color:#60a5fa;">{lo}</div>'
                f'</div>',
                unsafe_allow_html=True,
            )
    with col_aki:
        st.markdown(aki_card_html(ak_row), unsafe_allow_html=True)

    # ── Abnormal markers
    abnormal = pt_mkrs[pt_mkrs["status"].isin(["High", "Low"])].copy()
    abnormal = abnormal.sort_values(["is_aki_relevant", "marker_name"], ascending=[False, True])

    if not abnormal.empty:
        st.markdown('<div class="section-heading">Abnormal Markers</div>', unsafe_allow_html=True)
        card_cols = st.columns(3)
        for i, (_, mkr) in enumerate(abnormal.iterrows()):
            with card_cols[i % 3]:
                st.markdown(
                    marker_card_html(
                        name=mkr["marker_name"],
                        value=mkr["latest_value"],
                        unit=str(mkr["unit"]),
                        status=mkr["status"],
                        normal_low=mkr.get("normal_low"),
                        normal_high=mkr.get("normal_high"),
                        explanation=str(mkr.get("explanation", "")),
                        is_aki_relevant=bool(mkr.get("is_aki_relevant", False)),
                    ),
                    unsafe_allow_html=True,
                )
    else:
        st.info("No abnormal markers recorded for this admission.")

    # ── Trend charts
    available_keys = pt_ts["marker_key"].unique().tolist()
    priority_available = [k for k in PRIORITY_MARKERS if k in available_keys]
    other_available    = [k for k in available_keys if k not in PRIORITY_MARKERS]
    ordered_keys       = priority_available + other_available

    if not pt_ts.empty and ordered_keys:
        st.markdown('<div class="section-heading">Trend Charts</div>', unsafe_allow_html=True)
        key_to_name = {
            k: pt_ts[pt_ts["marker_key"] == k]["marker_name"].iloc[0]
            for k in ordered_keys
        }
        sel_markers = st.multiselect(
            "Select markers to chart",
            options=ordered_keys,
            default=priority_available[:4],
            format_func=lambda k: key_to_name.get(k, k),
            key="detail_markers",
        )
        if sel_markers:
            chart_rows = [sel_markers[i:i+2] for i in range(0, len(sel_markers), 2)]
            for row_keys in chart_rows:
                ch_cols = st.columns(len(row_keys))
                for col, mk in zip(ch_cols, row_keys):
                    with col:
                        mk_ts   = pt_ts[pt_ts["marker_key"] == mk]
                        mk_name = key_to_name.get(mk, mk)
                        mk_unit = mk_ts["unit"].iloc[0] if not mk_ts.empty else ""
                        fig = make_trend_chart(pt_ts, mk, mk_name, mk_unit)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                            mk_summary = pt_mkrs[pt_mkrs["marker_key"] == mk]
                            if not mk_summary.empty:
                                explanation = str(mk_summary.iloc[0].get("explanation", ""))
                                status      = mk_summary.iloc[0].get("status", "Normal")
                                if explanation and explanation not in ("nan", "") and status != "Normal":
                                    with st.expander(f"{mk_name} — clinical context", expanded=False):
                                        st.caption(explanation)
                        else:
                            st.caption(f"No trend data for {mk_name}")
    else:
        st.info("No trend data available for this admission.")


# ---------------------------------------------------------------------------
# Tab 3 — Marker Explorer
# ---------------------------------------------------------------------------

def render_marker_explorer(
    patients: pd.DataFrame,
    markers: pd.DataFrame,
    ts: pd.DataFrame,
) -> None:

    st.markdown('<div class="section-heading">Explore Clinical Markers</div>', unsafe_allow_html=True)

    f1, f2, f3 = st.columns([2, 1, 1])
    with f1:
        search = st.text_input("Search marker name", placeholder="e.g. Creatinine, WBC, Potassium…", key="me_search")
    with f2:
        abnormal_only = st.checkbox("Abnormal markers only", value=False, key="me_abn")
    with f3:
        cat_opts = ["All"] + sorted(markers["category"].dropna().unique().tolist())
        sel_cat = st.selectbox("Category", cat_opts, key="me_cat")

    sorted_pts = patients.sort_values("aki_risk_score", ascending=False)
    pt_options = {
        f"Admission {row.hadm_id}  ·  Subject {row.subject_id}  ·  {row.aki_risk_tier} Risk": int(row.hadm_id)
        for _, row in sorted_pts.iterrows()
    }
    sel_pt_label = st.selectbox("Select patient admission", list(pt_options.keys()), key="me_patient")
    sel_hadm     = pt_options[sel_pt_label]

    pt_mkrs = markers[markers["hadm_id"] == sel_hadm].copy()
    if search:
        pt_mkrs = pt_mkrs[pt_mkrs["marker_name"].str.contains(search, case=False, na=False)]
    if abnormal_only:
        pt_mkrs = pt_mkrs[pt_mkrs["status"].isin(["High", "Low"])]
    if sel_cat != "All":
        pt_mkrs = pt_mkrs[pt_mkrs["category"] == sel_cat]

    st.markdown(
        f'<div class="section-heading">Markers ({len(pt_mkrs)} found)</div>',
        unsafe_allow_html=True,
    )

    if pt_mkrs.empty:
        st.info("No markers match your filters for this admission.")
    else:
        tbl_cols = {
            "marker_name":    "Marker",
            "category":       "Category",
            "latest_value":   "Latest",
            "min_value":      "Min",
            "max_value":      "Max",
            "mean_value":     "Mean",
            "unit":           "Unit",
            "status":         "Status",
            "is_aki_relevant":"AKI-Relevant",
            "explanation":    "Explanation",
        }
        tbl = pt_mkrs[list(tbl_cols.keys())].rename(columns=tbl_cols).reset_index(drop=True)
        tbl["AKI-Relevant"] = tbl["AKI-Relevant"].map({True: "Yes", False: "No"})

        def _style_status(val):
            if val == "High":
                return "background-color:rgba(239,68,68,0.12);color:#f87171;font-weight:600;"
            if val == "Low":
                return "background-color:rgba(59,130,246,0.12);color:#60a5fa;font-weight:600;"
            return "color:#4ade80;"

        tbl_styled = tbl.style.map(_style_status, subset=["Status"])
        st.dataframe(tbl_styled, use_container_width=True, hide_index=True, height=340)

        st.markdown('<div class="section-heading">Trend Chart</div>', unsafe_allow_html=True)
        pt_ts = ts[ts["hadm_id"] == sel_hadm]
        available_keys  = pt_ts["marker_key"].unique().tolist()
        mk_names_in_tbl = pt_mkrs["marker_key"].tolist()
        chartable = [k for k in mk_names_in_tbl if k in available_keys]

        if chartable:
            key_to_name = {
                k: pt_mkrs[pt_mkrs["marker_key"] == k]["marker_name"].iloc[0]
                for k in chartable
            }
            sel_mk = st.selectbox(
                "Select marker to view trend",
                chartable,
                format_func=lambda k: key_to_name.get(k, k),
                key="me_mk",
            )
            mk_ts   = pt_ts[pt_ts["marker_key"] == sel_mk]
            mk_name = key_to_name.get(sel_mk, sel_mk)
            mk_unit = mk_ts["unit"].iloc[0] if not mk_ts.empty else ""
            fig = make_trend_chart(pt_ts, sel_mk, mk_name, mk_unit)
            if fig:
                st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
            mk_row = pt_mkrs[pt_mkrs["marker_key"] == sel_mk]
            if not mk_row.empty:
                exp = str(mk_row.iloc[0].get("explanation", ""))
                if exp and exp not in ("nan", ""):
                    st.markdown(
                        f'<div class="clinical-card"><h4>Clinical Context</h4>'
                        f'<p style="font-size:0.86rem;color:#475569;line-height:1.65;margin:0;">{exp}</p>'
                        f'</div>',
                        unsafe_allow_html=True,
                    )
        else:
            st.info("No trend data available for the filtered markers.")


# ---------------------------------------------------------------------------
# Tab 4 — About / Disclaimer
# ---------------------------------------------------------------------------

def render_about() -> None:
    st.markdown(
        '<div class="strata-wordmark" style="margin-bottom:0.45rem;">'
        'Str<span>a</span>ta</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        "**Clinical Marker Intelligence + AKI Early Warning**  \n"
        "MIMIC-IV Clinical Demo · Version 1.0 MVP"
    )

    st.markdown('<div class="section-heading">What is Strata?</div>', unsafe_allow_html=True)
    st.markdown(
        "Strata is a clinical signal intelligence layer designed to help care teams "
        "quickly surface meaningful patterns across laboratory values, vital signs, "
        "medication context, and diagnosis history. "
        "It is built on the MIMIC-IV Clinical Demo dataset — a de-identified, "
        "publicly available critical care database from Beth Israel Deaconess Medical Center.\n\n"
        "The dashboard has two core modules:\n"
        "- **Clinical Marker Intelligence** — tracks key lab and vital markers per admission, "
        "flags abnormal values, and displays trends over time with plain-English explanation blurbs.\n"
        "- **AKI Early-Warning Signal** — computes a transparent, rule-based risk signal "
        "(0–100) based on creatinine, BUN, potassium, bicarbonate, hemodynamic status, "
        "urine output, comorbidity context, and nephrotoxic medication exposure."
    )

    st.markdown('<div class="section-heading">Risk Score Architecture</div>', unsafe_allow_html=True)
    score_data = {
        "Signal": [
            "Creatinine level", "Creatinine rise", "BUN level",
            "Potassium (abnormal)", "Bicarbonate (low)", "Hemodynamic / MAP",
            "Urine output (oliguria)", "Comorbidity context", "Nephrotoxic medication",
        ],
        "Max Points": [30, 20, 15, 10, 8, 12, 15, 10, 5],
        "Why it matters": [
            "Primary filtration marker — elevated levels signal reduced GFR",
            "Acute rise pattern associated with AKI staging criteria",
            "Nitrogen waste accumulation with impaired renal clearance",
            "Impaired renal potassium excretion in AKI",
            "Metabolic acidosis from reduced acid excretion",
            "Sustained low MAP reduces renal perfusion pressure",
            "Oliguria is a key diagnostic criterion for AKI",
            "CKD, diabetes, hypertension, sepsis increase baseline risk",
            "Known nephrotoxic agents increase AKI likelihood",
        ],
    }
    st.dataframe(pd.DataFrame(score_data), use_container_width=True, hide_index=True)

    st.markdown('<div class="section-heading">Risk Tiers</div>', unsafe_allow_html=True)
    tier_col1, tier_col2, tier_col3 = st.columns(3)
    with tier_col1:
        st.markdown(
            '<div class="clinical-card">'
            '<div class="risk-badge low" style="margin-bottom:0.65rem;">Low</div>'
            '<div class="card-value" style="color:#4ade80;">0 – 29</div>'
            '<div class="card-sub">Routine monitoring recommended</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with tier_col2:
        st.markdown(
            '<div class="clinical-card">'
            '<div class="risk-badge moderate" style="margin-bottom:0.65rem;">Moderate</div>'
            '<div class="card-value" style="color:#fbbf24;">30 – 59</div>'
            '<div class="card-sub">Enhanced clinical review recommended</div>'
            '</div>',
            unsafe_allow_html=True,
        )
    with tier_col3:
        st.markdown(
            '<div class="clinical-card">'
            '<div class="risk-badge high" style="margin-bottom:0.65rem;">High</div>'
            '<div class="card-value" style="color:#f87171;">60 – 100</div>'
            '<div class="card-sub">Priority clinical attention warranted</div>'
            '</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="section-heading">Data Source</div>', unsafe_allow_html=True)
    st.markdown(
        "This dashboard uses the **MIMIC-IV Clinical Database Demo v2.2**, "
        "a freely available, de-identified subset of the MIMIC-IV database. "
        "All data has been de-identified in accordance with HIPAA Safe Harbor guidelines. "
        "No real patient identities are present."
    )

    st.markdown('<div class="section-heading">Important Disclaimer</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="disclaimer-card">'
        '<strong>Strata is a demo only. It does not diagnose AKI or recommend treatment. '
        'It surfaces early-warning risk signals and abnormal markers for review in clinical context.</strong><br><br>'
        'All outputs are generated from de-identified MIMIC-IV demo data and are intended '
        'solely for product evaluation and demonstration purposes. '
        'This tool has not been validated for clinical use, is not a medical device, '
        'and should not be used to guide clinical decision-making in any form. '
        'All risk scores, flags, and signals require qualified clinical interpretation.'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
    st.caption("Strata MVP · Built with MIMIC-IV Clinical Demo · Not for clinical use")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    with st.spinner("Loading Strata data…"):
        patients, markers, ts, aki = load_data()

    tab_overview, tab_detail, tab_explorer, tab_about = st.tabs([
        "Overview",
        "Patient Detail",
        "Marker Explorer",
        "About / Disclaimer",
    ])

    with tab_overview:
        render_overview(patients)

    with tab_detail:
        render_patient_detail(patients, markers, ts, aki)

    with tab_explorer:
        render_marker_explorer(patients, markers, ts)

    with tab_about:
        render_about()


if __name__ == "__main__":
    main()
