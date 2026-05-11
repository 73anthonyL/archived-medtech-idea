"""
Strata — clinical marker intelligence dashboard.

Streamlit entry point. Loads pre-computed pipeline outputs and renders
the four-tab dashboard: Overview, Patient Detail, Marker Explorer,
About / Disclaimer.

Run with:  streamlit run src/app.py
"""

from pathlib import Path
import html as _html
import math

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import streamlit.components.v1 as components

from theme_toggle import render_theme_toggle, inject_theme_attribute, plotly_theme_layout, get_theme
from patient_names import add_display_names

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
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------------------------
# Custom CSS — ported from docs/design/styles.css
# ---------------------------------------------------------------------------

CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;600;700&display=swap');

/* ── Global ── */
html, body, [class*="css"] {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
  -webkit-font-smoothing: antialiased;
  color: var(--text-1);
}
.stApp { background-color: var(--bg) !important; color: var(--text-1) !important; }
[data-testid="stHeader"] { background-color: var(--bg) !important; }
/* Override Streamlit's hardcoded white text so light mode text is dark */
[data-testid="stMarkdownContainer"],
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] li { color: var(--text-1) !important; }
p, li { color: var(--text-1); }
section[data-testid="stSidebar"] { background: linear-gradient(180deg, #08111f 0%, #060d1b 100%) !important; border-right: 1px solid var(--border) !important; }
.block-container { padding-top: 1.5rem !important; }
/* hide decorative toolbar elements and sidebar controls */
[data-testid="stStatusWidget"]        { display: none !important; }
[data-testid="stAppDeployButton"]     { display: none !important; }
[data-testid="stMainMenuButton"]      { display: none !important; }
[data-testid="stConnectionStatus"]    { display: none !important; }
[data-testid="stToolbarActions"]      { display: none !important; }
/* ── Sidebar collapse button — always visible ── */
[data-testid="stSidebarHeader"] {
  visibility: visible !important;
  opacity: 1 !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarCollapseButton"] > button {
  opacity: 1 !important;
  visibility: visible !important;
  color: var(--text-3) !important;
}
[data-testid="stSidebarCollapseButton"] > button svg,
[data-testid="stSidebarCollapseButton"] > button svg path {
  fill: currentColor !important;
  stroke: currentColor !important;
}
[data-testid="stSidebarCollapseButton"]:hover > button,
[data-testid="stSidebarCollapseButton"] > button:hover {
  color: var(--text-1) !important;
  background: var(--surface-2) !important;
}

/* ── Sidebar content ── */
.sidebar-brand { padding: 4px 0 12px 0; border-bottom: 1px solid var(--border); margin-bottom: 14px; }
.sidebar-wordmark { font-size: 22px; font-weight: 800; letter-spacing: -0.04em; color: var(--text-1); line-height: 1; }
.sidebar-wordmark span { background: var(--gradient-accent); -webkit-background-clip: text; background-clip: text; color: transparent; }
.sidebar-tagline { font-size: 10px; letter-spacing: 0.16em; color: var(--text-muted); text-transform: uppercase; margin-top: 5px; font-weight: 500; }
.sidebar-section-label {
  font-size: 9.5px; letter-spacing: 0.2em; color: var(--text-muted);
  text-transform: uppercase; font-weight: 600; margin: 16px 0 8px 0;
}
.sidebar-stat-row { display: flex; justify-content: space-between; align-items: center; margin-bottom: 7px; }
.sidebar-stat-label { font-size: 12px; color: var(--text-3); }
.sidebar-stat-value { font-family: var(--mono); font-size: 13px; font-weight: 600; color: var(--text-2); }
.sidebar-risk-chips { display: flex; gap: 6px; flex-wrap: wrap; margin-bottom: 4px; }
.risk-chip {
  display: inline-flex; align-items: center; gap: 5px;
  padding: 4px 9px; border-radius: 999px;
  font-size: 11px; font-weight: 600; font-family: var(--mono);
}
.risk-chip-high   { background: rgba(248,113,113,0.12); color: var(--risk-high); border: 1px solid rgba(248,113,113,0.25); }
.risk-chip-mod    { background: rgba(251,191,36,0.10); color: var(--risk-mod); border: 1px solid rgba(251,191,36,0.22); }
.risk-chip-low    { background: rgba(74,222,128,0.10); color: var(--risk-low); border: 1px solid rgba(74,222,128,0.22); }
.sidebar-nav-item { display: flex; align-items: flex-start; gap: 8px; margin-bottom: 10px; }
.sidebar-nav-icon { font-size: 14px; line-height: 1.4; flex-shrink: 0; }
.sidebar-nav-text { font-size: 11.5px; color: var(--text-3); line-height: 1.45; }
.sidebar-nav-title { font-weight: 600; color: var(--text-2); display: block; margin-bottom: 1px; }
.sidebar-disclaimer {
  background: rgba(251,191,36,0.05); border: 1px solid rgba(251,191,36,0.18);
  border-radius: 8px; padding: 10px 12px; margin-top: 4px;
}
.sidebar-disclaimer p { font-size: 10.5px; color: var(--text-muted); line-height: 1.5; margin: 0; }
.sidebar-version { font-size: 10px; color: var(--text-faint); text-align: center; margin-top: 14px; font-family: var(--mono); }

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] {
  gap: 0.15rem;
  border-bottom: 1px solid var(--border);
  background: transparent;
  padding-bottom: 0;
  margin-bottom: 0.5rem;
}
.stTabs [data-baseweb="tab"] {
  font-size: 0.84rem;
  font-weight: 500;
  padding: 0.5rem 1.2rem;
  border-radius: 8px 8px 0 0;
  color: var(--text-muted);
  background: transparent;
}
.stTabs [aria-selected="true"] {
  color: var(--text-2) !important;
  font-weight: 600 !important;
  background: var(--surface) !important;
}

/* ── Streamlit widget overrides ── */
div[data-baseweb="select"] > div {
  background-color: var(--surface-2) !important;
  border-color: var(--border) !important;
  color: var(--text-3) !important;
  border-radius: var(--radius-sm) !important;
}
div[data-baseweb="input"] > div {
  background-color: var(--surface-2) !important;
  border-color: var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
div[data-baseweb="input"] input { color: var(--text-3) !important; }
div[data-testid="stDataFrameContainer"] {
  background: var(--surface);
  border-radius: 10px;
  border: 1px solid var(--border);
}
div[data-testid="stDataFrameContainer"] table { font-size: 0.82rem; }
details[data-testid="stExpander"] {
  background: var(--surface) !important;
  border: 1px solid var(--border) !important;
  border-radius: 10px !important;
}
div[data-testid="stAlert"] {
  background: rgba(56,189,248,0.06) !important;
  border-color: rgba(56,189,248,0.18) !important;
  color: var(--text-muted) !important;
  border-radius: 10px !important;
}
.stCheckbox label { color: var(--text-3) !important; }
label[data-testid="stWidgetLabel"] p { color: var(--text-muted) !important; font-size: 0.84rem !important; }
div[data-testid="stMultiSelect"] > div {
  background-color: var(--surface-2) !important;
  border-color: var(--border) !important;
  border-radius: var(--radius-sm) !important;
}
.stButton > button {
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  color: var(--text-2) !important;
  font-size: 0.82rem !important;
  transition: border-color 0.14s ease, color 0.14s ease !important;
}
.stButton > button:hover {
  border-color: var(--accent-blue) !important;
  color: var(--text-1) !important;
  background: var(--surface-3) !important;
}
/* Radio as segmented control */
div[data-testid="stRadio"] > label { display: none; }
div[data-testid="stRadio"] > div {
  display: flex !important;
  flex-direction: row !important;
  gap: 2px !important;
  background: var(--surface-2) !important;
  border: 1px solid var(--border) !important;
  border-radius: var(--radius-sm) !important;
  padding: 3px !important;
  width: fit-content !important;
}
div[data-testid="stRadio"] > div > label {
  display: flex !important;
  background: transparent !important;
  border: 1px solid transparent !important;
  border-radius: 6px !important;
  padding: 6px 12px !important;
  font-size: 12px !important;
  color: var(--text-3) !important;
  cursor: pointer !important;
  transition: all 0.14s ease !important;
  white-space: nowrap !important;
}
div[data-testid="stRadio"] > div > label:hover { color: var(--text-1) !important; }
div[data-testid="stRadio"] > div > label[data-baseweb="radio"] input:checked + div ~ span,
div[data-testid="stRadio"] > div > label:has(input:checked) {
  background: var(--surface-3) !important;
  color: var(--text-1) !important;
}
div[data-testid="stRadio"] input[type="radio"] { display: none !important; }

/* ── Hero card ── */
.hero-card {
  background: radial-gradient(ellipse at top right, rgba(29,78,216,0.10), transparent 60%), var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 28px 32px;
  position: relative;
  overflow: hidden;
  margin-bottom: 1.5rem;
}
.hero-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--gradient-accent);
}
.hero-grid {
  display: grid;
  grid-template-columns: 1.4fr 1fr;
  gap: 32px;
  align-items: start;
}
.hero-eyebrow {
  font-size: 10.5px;
  letter-spacing: 0.22em;
  color: var(--accent-blue);
  font-weight: 600;
  text-transform: uppercase;
  margin-bottom: 12px;
}
.hero-wordmark {
  font-size: 58px;
  font-weight: 800;
  letter-spacing: -0.045em;
  line-height: 0.95;
  margin: 0 0 12px 0;
  color: var(--text-1);
}
.hero-accent {
  background: var(--gradient-accent);
  -webkit-background-clip: text;
  background-clip: text;
  color: transparent;
}
.hero-tagline {
  font-size: 14px;
  line-height: 1.55;
  color: var(--text-3);
  max-width: 520px;
  margin-bottom: 22px;
}
.hero-stats { display: grid; grid-template-columns: repeat(4, 1fr); gap: 12px; }
.hero-stat {
  background: rgba(13,22,38,0.55);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
}
.hero-stat-value {
  font-family: var(--mono);
  font-size: 28px;
  font-weight: 700;
  letter-spacing: -0.02em;
  line-height: 1;
  margin-bottom: 8px;
  font-variant-numeric: tabular-nums;
}
.hero-stat-label {
  font-size: 9.5px;
  letter-spacing: 0.16em;
  color: var(--text-3);
  text-transform: uppercase;
  font-weight: 600;
}
.hero-right { display: flex; flex-direction: column; gap: 14px; align-items: flex-end; }
.demo-mode-pill {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 8px 14px;
  border-radius: 999px;
  background: rgba(56,189,248,0.08);
  border: 1px solid rgba(56,189,248,0.30);
  font-size: 11px;
  letter-spacing: 0.16em;
  color: var(--accent-blue);
  font-weight: 600;
  text-transform: uppercase;
}
.demo-dot {
  width: 7px; height: 7px;
  border-radius: 50%;
  background: var(--accent-blue);
  box-shadow: 0 0 10px var(--accent-blue);
  animation: s-pulse 1.6s ease-in-out infinite;
  display: inline-block;
  flex-shrink: 0;
}
@keyframes s-pulse {
  0%, 100% { opacity: 0.55; transform: scale(0.9); }
  50%       { opacity: 1;    transform: scale(1.15); }
}
.hero-watchlist {
  width: 100%;
  background: rgba(13,22,38,0.55);
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  overflow: hidden;
}
.hero-watchlist-label {
  font-size: 9.5px;
  letter-spacing: 0.20em;
  color: var(--text-muted);
  margin-bottom: 8px;
  display: flex;
  align-items: center;
  gap: 6px;
}
.hero-watchlist-label::before {
  content: "";
  width: 6px; height: 6px;
  border-radius: 50%;
  background: var(--risk-high);
  box-shadow: 0 0 8px var(--risk-high);
  animation: s-pulse 1.6s ease-in-out infinite;
  flex-shrink: 0;
}
.hero-ticker { overflow: hidden; mask-image: linear-gradient(90deg, transparent, black 8%, black 92%, transparent); }
.hero-ticker-inner {
  display: flex;
  gap: 28px;
  animation: ticker-scroll 40s linear infinite;
  white-space: nowrap;
}
@keyframes ticker-scroll {
  from { transform: translateX(0); }
  to   { transform: translateX(-50%); }
}
.ticker-item { display: inline-flex; align-items: center; gap: 8px; font-size: 11.5px; }
.ticker-id      { color: var(--text-3); font-family: var(--mono); }
.ticker-score   { font-family: var(--mono); font-weight: 700; color: var(--risk-high); }
.ticker-concern { color: var(--text-3); }
.hero-disclaimer-inline { font-size: 11px; color: var(--text-faint); text-align: right; line-height: 1.5; }

/* ── KPI cards ── */
.kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 14px; margin-bottom: 1.5rem; }
.kpi-card {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 18px 16px;
  overflow: hidden;
  transition: transform 0.15s ease, border-color 0.15s ease;
}
.kpi-card:hover { transform: translateY(-1px); border-color: var(--border-2); }
.kpi-stripe { position: absolute; top: 0; left: 0; right: 0; height: 2px; }
.kpi-top { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
.kpi-icon { font-size: 10px; }
.kpi-label { font-size: 10.5px; letter-spacing: 0.16em; color: var(--text-3); text-transform: uppercase; font-weight: 600; }
.kpi-value { font-family: var(--mono); font-size: 44px; font-weight: 700; letter-spacing: -0.03em; line-height: 1; font-variant-numeric: tabular-nums; margin-bottom: 10px; }
.kpi-sub   { font-size: 11.5px; color: var(--text-3); }
.kpi-card.total .kpi-value { color: var(--text-2); }
.kpi-card.high  .kpi-value { color: var(--risk-high); }
.kpi-card.mod   .kpi-value { color: var(--risk-mod); }
.kpi-card.info  .kpi-value { color: var(--accent-info); }

/* ── Section labels ── */
.section-label-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin: 1.75rem 0 0.75rem;
  padding: 0 2px;
}
.section-label {
  font-size: 10.5px;
  letter-spacing: 0.20em;
  color: var(--text-muted);
  text-transform: uppercase;
  font-weight: 600;
  white-space: nowrap;
}
.section-label-row::after {
  content: '';
  flex: 1;
  height: 1px;
  background: var(--border);
}
.section-action-meta { font-size: 11px; color: var(--text-3); letter-spacing: 0.04em; white-space: nowrap; }

/* ── Filter card ── */
.filter-card {
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px;
  margin-bottom: 0.5rem;
}
.filter-label {
  font-size: 10.5px;
  letter-spacing: 0.14em;
  color: var(--text-3);
  text-transform: uppercase;
  font-weight: 600;
  margin-bottom: 6px;
}

/* ── Risk badges ── */
.risk-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 9.5px;
  letter-spacing: 0.18em;
  font-weight: 700;
  border: 1px solid;
  text-transform: uppercase;
  white-space: nowrap;
}
.risk-dot { width: 6px; height: 6px; border-radius: 50%; display: inline-block; flex-shrink: 0; }
.risk-badge.high     { color: var(--risk-high); background: rgba(248,113,113,0.12); border-color: rgba(248,113,113,0.35); }
.risk-badge.moderate { color: var(--risk-mod);  background: rgba(251,191,36,0.10);  border-color: rgba(251,191,36,0.35); }
.risk-badge.low      { color: var(--risk-low);  background: rgba(74,222,128,0.10);  border-color: rgba(74,222,128,0.30); }

/* ── Status pill ── */
.status-pill {
  display: inline-flex;
  padding: 3px 8px;
  border-radius: 5px;
  font-size: 9.5px;
  letter-spacing: 0.14em;
  font-weight: 700;
  text-transform: uppercase;
  border: 1px solid;
}
.status-pill.high   { background: rgba(248,113,113,0.12); color: var(--risk-high);   border-color: rgba(248,113,113,0.25); }
.status-pill.low    { background: rgba(56,189,248,0.12);  color: var(--accent-blue); border-color: rgba(56,189,248,0.25); }
.status-pill.normal { background: rgba(74,222,128,0.10);  color: var(--risk-low);    border-color: rgba(74,222,128,0.25); }

/* ── Info tag ── */
.info-tag {
  display: inline-flex;
  padding: 4px 10px;
  border-radius: 999px;
  background: rgba(167,139,250,0.08);
  color: var(--accent-info);
  border: 1px solid rgba(167,139,250,0.22);
  font-size: 11px;
  letter-spacing: 0.04em;
  font-weight: 500;
  white-space: nowrap;
}

/* ── AKI tag ── */
.aki-tag {
  display: inline-flex;
  padding: 3px 8px;
  border-radius: 4px;
  background: rgba(56,189,248,0.10);
  color: var(--accent-blue);
  font-size: 9px;
  letter-spacing: 0.14em;
  font-weight: 700;
  border: 1px solid rgba(56,189,248,0.25);
  text-transform: uppercase;
}

/* ── Patient admissions table ── */
.table-card {
  width: 100%;
  overflow-x: auto;
  border-radius: var(--radius);
  border: 1px solid var(--border);
  margin-bottom: 1.5rem;
}
table.patient-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13px;
  background: var(--surface);
}
table.patient-table thead tr { background: var(--bg-2); border-bottom: 1px solid var(--border); }
table.patient-table thead th {
  padding: 14px 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--text-muted);
  white-space: nowrap;
}
table.patient-table thead th.th-rail { width: 6px; padding: 0; }
table.patient-table tbody tr { border-bottom: 1px solid rgba(26,46,74,0.5); transition: background 0.12s ease; }
table.patient-table tbody tr:last-child { border-bottom: none; }
table.patient-table tbody tr.row-high:hover     { background: rgba(248,113,113,0.04); }
table.patient-table tbody tr.row-moderate:hover { background: rgba(251,191,36,0.04); }
table.patient-table tbody tr.row-low:hover      { background: rgba(74,222,128,0.03); }
table.patient-table tbody td { padding: 12px; color: var(--text-2); vertical-align: middle; }
table.patient-table td.td-rail { width: 6px; padding: 0; }
.row-rail { display: block; width: 3px; height: 34px; border-radius: 0 2px 2px 0; }
.row-rail.rail-high     { background: linear-gradient(180deg, var(--risk-high), var(--risk-high-2)); box-shadow: 0 0 8px rgba(248,113,113,0.35); }
.row-rail.rail-moderate { background: linear-gradient(180deg, var(--risk-mod), var(--risk-mod-2));   box-shadow: 0 0 8px rgba(251,191,36,0.25); }
.row-rail.rail-low      { background: linear-gradient(180deg, var(--risk-low), var(--risk-low-2)); }
.td-mono   { font-family: var(--mono); color: var(--text-muted); font-size: 12px; }
.td-muted  { color: var(--text-muted); }
.score-cell { display: flex; align-items: center; gap: 10px; min-width: 140px; }
.score-num  { font-family: var(--mono); font-size: 15px; font-weight: 700; min-width: 30px; text-align: right; }
.score-bar  { flex: 1; height: 6px; background: rgba(148,163,184,0.10); border-radius: 3px; overflow: hidden; }
.score-bar-fill { height: 100%; border-radius: 3px; }
.score-bar-fill.high     { background: linear-gradient(90deg, var(--risk-high-2), var(--risk-high)); }
.score-bar-fill.moderate { background: linear-gradient(90deg, var(--risk-mod-2),  var(--risk-mod)); }
.score-bar-fill.low      { background: linear-gradient(90deg, var(--risk-low-2),  var(--risk-low)); }
.td-concern { color: var(--text-3); max-width: 300px; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; font-size: 12.5px; }

/* ── Patient detail ── */
.patient-header-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; margin-bottom: 0.5rem; }
.patient-summary-card {
  background: linear-gradient(135deg, var(--bg-2) 0%, var(--surface-2) 100%);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 24px 26px;
  position: relative;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  gap: 14px;
}
.patient-summary-card::before {
  content: '';
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 3px;
  background: var(--gradient-accent);
}
.patient-eyebrow { font-size: 10.5px; letter-spacing: 0.20em; color: var(--accent-blue); font-weight: 600; text-transform: uppercase; }
.patient-name { font-size: 30px; font-weight: 700; margin: 4px 0 0; letter-spacing: -0.02em; color: var(--text-1); }
.patient-pills { display: flex; flex-wrap: wrap; gap: 8px; }
.mini-stat-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin-top: 4px; }
.mini-stat { background: rgba(13,22,38,0.6); border: 1px solid var(--border); border-radius: 10px; padding: 12px 14px; }
.mini-stat-label { font-size: 9.5px; letter-spacing: 0.16em; color: var(--text-3); text-transform: uppercase; margin-bottom: 6px; font-weight: 600; }
.mini-stat-value { font-family: var(--mono); font-size: 26px; font-weight: 700; line-height: 1; }

/* ── AKI risk card ── */
.aki-risk-card {
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 22px 24px;
  display: flex;
  flex-direction: column;
  gap: 12px;
}
.aki-risk-card.aki-high     { background: radial-gradient(ellipse at top right, rgba(248,113,113,0.08), transparent 60%), var(--surface); border-color: rgba(248,113,113,0.28); }
.aki-risk-card.aki-moderate { background: radial-gradient(ellipse at top right, rgba(251,191,36,0.07),  transparent 60%), var(--surface); border-color: rgba(251,191,36,0.25); }
.aki-risk-card.aki-low      { background: radial-gradient(ellipse at top right, rgba(74,222,128,0.06),  transparent 60%), var(--surface); border-color: rgba(74,222,128,0.25); }
.aki-risk-top { display: flex; align-items: flex-start; justify-content: space-between; gap: 16px; }
.aki-score-row { display: flex; align-items: baseline; gap: 6px; margin: 6px 0 8px; }
.aki-score { font-family: var(--mono); font-size: 56px; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.aki-score-frac { font-size: 14px; color: var(--text-muted); font-family: var(--mono); }
.aki-score-bar {
  position: relative;
  height: 8px;
  background: rgba(148,163,184,0.10);
  border-radius: 4px;
  overflow: visible;
}
.aki-score-bar-fill { height: 100%; border-radius: 4px; position: relative; z-index: 1; }
.aki-score-bar-tick {
  position: absolute;
  top: -3px; bottom: -3px;
  width: 1px;
  background: rgba(148,163,184,0.30);
  z-index: 2;
}
.aki-score-bar-labels {
  display: flex;
  justify-content: space-between;
  font-size: 9.5px;
  color: var(--text-muted);
  letter-spacing: 0.10em;
  margin-top: 4px;
  font-family: var(--mono);
}
.contributing-signals { padding-top: 12px; border-top: 1px solid var(--border); }
.signals-list { list-style: none; padding: 0; margin: 8px 0 0; display: flex; flex-direction: column; gap: 8px; }
.signals-list li { display: flex; align-items: flex-start; gap: 10px; font-size: 12.5px; color: var(--text-2); line-height: 1.45; }
.signal-dot { width: 5px; height: 5px; border-radius: 50%; margin-top: 7px; flex-shrink: 0; }

/* ── Marker cards ── */
.marker-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 0.85rem; }
.marker-card {
  position: relative;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 18px 20px 18px 22px;
  display: flex;
  flex-direction: column;
  gap: 8px;
  overflow: hidden;
  transition: border-color 0.15s ease;
}
.marker-card:hover { border-color: var(--border-2); }
.marker-rail {
  position: absolute;
  top: 12px; bottom: 12px; left: 0;
  width: 3px;
  border-radius: 0 2px 2px 0;
}
.marker-rail.rail-high   { background: linear-gradient(180deg, var(--risk-high), var(--risk-high-2)); box-shadow: 0 0 8px rgba(248,113,113,0.25); }
.marker-rail.rail-low    { background: linear-gradient(180deg, var(--accent-blue), var(--accent-blue-2)); }
.marker-rail.rail-normal { background: linear-gradient(180deg, var(--risk-low), var(--risk-low-2)); }
.marker-card-head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
.marker-name  { font-size: 14px; color: var(--text-1); font-weight: 600; }
.marker-value { font-family: var(--mono); font-size: 32px; font-weight: 700; line-height: 1; letter-spacing: -0.02em; }
.marker-unit  { font-size: 13px; color: var(--text-3); margin-left: 6px; font-weight: 500; }
.marker-ref   { font-size: 11px; color: var(--text-muted); letter-spacing: 0.05em; font-family: var(--mono); }
.marker-explain { font-size: 12px; color: var(--text-3); line-height: 1.5; margin-top: 4px; padding-top: 10px; border-top: 1px dashed var(--border); }

/* ── Ref scale ── */
.ref-scale { margin: 2px 0; }
.ref-scale-track { position: relative; height: 6px; background: rgba(148,163,184,0.08); border-radius: 3px; }
.ref-scale-band { position: absolute; top: 0; bottom: 0; background: rgba(74,222,128,0.18); border: 1px solid rgba(74,222,128,0.30); border-radius: 3px; }
.ref-scale-marker { position: absolute; top: 50%; width: 10px; height: 10px; border-radius: 50%; transform: translate(-50%, -50%); }
.ref-scale-labels { display: flex; justify-content: space-between; font-size: 10px; color: var(--text-muted); margin-top: 4px; letter-spacing: 0.08em; font-family: var(--mono); }

/* ── Trend charts ── */
.trend-explain { background: rgba(13,22,38,0.6); border: 1px solid var(--border); border-radius: 10px; padding: 14px 16px; margin-top: 0.5rem; }
.trend-explain-label { font-size: 10px; letter-spacing: 0.18em; color: var(--text-muted); font-weight: 600; margin-bottom: 6px; text-transform: uppercase; }
.trend-explain-text { font-size: 13px; color: var(--text-2); line-height: 1.5; }

/* ── Explorer table ── */
.explorer-table-card { width: 100%; overflow-x: auto; border-radius: var(--radius); border: 1px solid var(--border); margin-bottom: 1rem; }
table.explorer-table { width: 100%; border-collapse: collapse; font-size: 13px; background: var(--surface); }
table.explorer-table thead tr { background: var(--bg-2); border-bottom: 1px solid var(--border); }
table.explorer-table thead th {
  padding: 12px;
  text-align: left;
  font-size: 10px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.16em;
  color: var(--text-muted);
  white-space: nowrap;
}
table.explorer-table thead th.th-rail { width: 6px; padding: 0; }
table.explorer-table tbody tr { border-bottom: 1px solid rgba(26,46,74,0.5); transition: background 0.12s ease; }
table.explorer-table tbody tr:last-child { border-bottom: none; }
table.explorer-table tbody tr.row-high:hover   { background: rgba(248,113,113,0.04); }
table.explorer-table tbody tr.row-info:hover   { background: rgba(56,189,248,0.04); }
table.explorer-table tbody tr.row-normal:hover { background: rgba(56,189,248,0.02); }
table.explorer-table tbody td { padding: 10px 12px; color: var(--text-2); vertical-align: middle; }
table.explorer-table td.td-rail { width: 6px; padding: 0; }
.cell-strong  { color: var(--text-1); font-weight: 500; }
.cell-explain { color: var(--text-3); max-width: 240px; font-size: 12px; line-height: 1.4; }
.cell-latest  { font-family: var(--mono); font-weight: 700; }
.empty-state  { padding: 52px 20px; display: flex; flex-direction: column; align-items: center; gap: 10px; text-align: center; }
.empty-icon   { font-size: 30px; color: var(--text-muted); margin-bottom: 4px; }
.empty-title  { font-size: 15px; color: var(--text-1); font-weight: 500; }
.empty-sub    { font-size: 13px; color: var(--text-3); max-width: 300px; }

/* ── About tab ── */
.about-hero {
  background: radial-gradient(ellipse at top right, rgba(29,78,216,0.10), transparent 60%), var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 36px 40px;
  position: relative;
  overflow: hidden;
  margin-bottom: 1rem;
}
.about-hero::before { content: ''; position: absolute; top: 0; left: 0; right: 0; height: 3px; background: var(--gradient-accent); }
.about-eyebrow { font-size: 11px; letter-spacing: 0.22em; color: var(--accent-blue); font-weight: 600; text-transform: uppercase; margin-bottom: 12px; }
.about-lede { font-size: 15px; line-height: 1.6; color: var(--text-3); max-width: 680px; margin-top: 10px; }
.tier-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 14px; margin-bottom: 1rem; }
.tier-card { position: relative; background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 20px 22px; overflow: hidden; }
.tier-card-stripe { position: absolute; top: 0; left: 0; right: 0; height: 3px; }
.tier-card-head { display: flex; align-items: center; justify-content: space-between; margin-bottom: 10px; }
.tier-range { font-size: 12px; color: var(--text-muted); font-family: var(--mono); }
.tier-card-title { font-size: 17px; font-weight: 600; letter-spacing: -0.01em; margin-bottom: 8px; }
.tier-card-body { font-size: 13px; color: var(--text-3); line-height: 1.5; }
.data-source-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; margin-bottom: 1rem; }
.data-source { display: flex; flex-direction: column; gap: 0; }
.data-source-line { display: grid; grid-template-columns: 110px 1fr; gap: 16px; font-size: 13px; padding: 12px 22px; border-bottom: 1px solid rgba(26,46,74,0.5); }
.data-source-line:last-child { border-bottom: none; }
.data-source-key { font-size: 10.5px; letter-spacing: 0.16em; color: var(--text-muted); text-transform: uppercase; align-self: center; font-weight: 600; }
.data-source-val { color: var(--text-2); font-family: var(--mono); font-size: 12.5px; align-self: center; }

/* ── Arch table ── */
.arch-table-card { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); overflow: hidden; margin-bottom: 1rem; }
table.arch-table { width: 100%; border-collapse: collapse; font-size: 13.5px; }
table.arch-table th { text-align: left; padding: 12px 18px; font-size: 10px; letter-spacing: 0.16em; color: var(--text-muted); text-transform: uppercase; font-weight: 600; border-bottom: 1px solid var(--border); background: var(--bg-2); }
table.arch-table td { padding: 13px 18px; border-bottom: 1px solid rgba(26,46,74,0.5); color: var(--text-2); }
table.arch-table tbody tr:last-child td { border-bottom: none; }
table.arch-table tbody tr.row-total { background: rgba(56,189,248,0.04); }

/* ── Disclaimer card ── */
.disclaimer-card { display: flex; gap: 0; background: rgba(251,191,36,0.04); border: 1px solid rgba(251,191,36,0.18); border-radius: var(--radius); overflow: hidden; margin-top: 1rem; }
.disclaimer-rail { width: 3px; background: var(--risk-mod); flex-shrink: 0; }
.disclaimer-body { padding: 16px 20px; }
.disclaimer-title { font-size: 11px; letter-spacing: 0.18em; color: var(--risk-mod); font-weight: 700; margin-bottom: 6px; text-transform: uppercase; }
.disclaimer-text { font-size: 12.5px; color: var(--text-3); line-height: 1.55; max-width: 860px; }

/* ── Sidebar overrides ── */
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"] .block-container { padding: 18px 14px 24px !important; }
.strata-sidebar-brand {
  display: flex; align-items: center; gap: 10px;
  padding: 6px 6px 18px 6px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 4px;
}
.strata-sidebar-logo {
  width: 32px; height: 32px; border-radius: 8px;
  background: linear-gradient(90deg, #1d4ed8 0%, #3b82f6 45%, #22d3ee 100%);
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 14px rgba(56,189,248,0.25);
  flex-shrink: 0;
}
.strata-sidebar-logo-inner {
  width: 14px; height: 14px; border-radius: 4px;
  background: #060d1b;
}
.strata-sidebar-wordmark {
  font-size: 18px; font-weight: 700; letter-spacing: -0.02em; color: var(--text-1); line-height: 1;
}
.strata-sidebar-wordmark .accent { background: linear-gradient(90deg,#3b82f6,#22d3ee); -webkit-background-clip: text; background-clip: text; color: transparent; }
.strata-sidebar-tagline { font-size: 9.5px; letter-spacing: 0.16em; color: var(--text-3); text-transform: uppercase; margin-top: 3px; }
.strata-section-label {
  font-size: 9.5px; letter-spacing: 0.20em; color: var(--text-muted);
  text-transform: uppercase; font-weight: 600;
  padding: 14px 8px 6px 8px;
}
.strata-cohort-row {
  display: flex; align-items: center; gap: 10px;
  font-size: 12.5px; color: var(--text-3); padding: 4px 8px;
}
.strata-cohort-dot { width: 8px; height: 8px; border-radius: 2px; flex-shrink: 0; }
.strata-cohort-count { margin-left: auto; font-family: var(--mono); font-size: 13px; font-weight: 600; color: var(--text-2); }
.strata-sidebar-foot { padding-top: 16px; border-top: 1px solid var(--border); display: flex; flex-direction: column; gap: 10px; }
.strata-demo-pill {
  display: flex; align-items: center; gap: 8px;
  padding: 10px 12px; border-radius: 10px;
  background: rgba(56,189,248,0.05); border: 1px solid rgba(56,189,248,0.2);
  font-size: 11px; color: var(--accent-blue); letter-spacing: 0.06em; font-weight: 600;
}
.strata-demo-dot {
  width: 7px; height: 7px; border-radius: 50%; background: var(--accent-blue);
  box-shadow: 0 0 8px var(--accent-blue);
  animation: s-pulse 1.6s ease-in-out infinite;
  flex-shrink: 0;
}
.strata-safety-line {
  font-size: 10px; color: var(--text-muted); letter-spacing: 0.06em; padding: 0 2px; line-height: 1.5;
}

/* ── Sidebar nav buttons (dark mode defaults) ── */
section[data-testid="stSidebar"] [data-testid^="nav_"] .stButton > button {
  background: transparent !important;
  border: 1px solid transparent !important;
  border-radius: 14px !important;
  color: #6b82a8 !important;
  font-size: 13px !important; font-weight: 500 !important;
  padding: 8px 14px !important;
  text-align: left !important;
  justify-content: flex-start !important;
  gap: 10px !important;
  transition: background 0.13s ease, color 0.13s ease, border-color 0.13s ease !important;
  box-shadow: none !important;
}
section[data-testid="stSidebar"] [data-testid^="nav_"] .stButton > button:hover {
  color: #a8bdd6 !important;
  background: rgba(56,189,248,0.05) !important;
  border-color: rgba(56,189,248,0.08) !important;
}
section[data-testid="stSidebar"] [data-testid^="nav_"][data-testid$="_active"] .stButton > button {
  background: linear-gradient(90deg, rgba(34,211,238,0.13), rgba(56,189,248,0.05)) !important;
  border-color: rgba(34,211,238,0.28) !important;
  color: #f0f8ff !important;
  font-weight: 600 !important;
  box-shadow: 0 0 18px rgba(34,211,238,0.09) !important;
}
section[data-testid="stSidebar"] [data-testid^="nav_"] .stButton {
  margin-bottom: 3px !important;
}
section[data-testid="stSidebar"] [data-testid^="nav_"] .stButton > button:focus:not(:active) {
  box-shadow: none !important;
  border-color: rgba(34,211,238,0.20) !important;
}

/* ── Sidebar user block ── */
.sidebar-user-block {
  display: flex; align-items: center; gap: 10px;
  padding: 10px 12px; border-radius: 10px;
  background: rgba(56,189,248,0.04); border: 1px solid var(--border);
  margin-top: 4px;
}
.sidebar-user-avatar {
  width: 32px; height: 32px; border-radius: 50%;
  background: linear-gradient(135deg, #1d4ed8 0%, #22d3ee 100%);
  display: flex; align-items: center; justify-content: center;
  font-size: 12px; font-weight: 700; color: #fff; flex-shrink: 0;
}
.sidebar-user-name { font-size: 12.5px; font-weight: 600; color: var(--text-2); line-height: 1.2; }
.sidebar-user-role { font-size: 10px; color: var(--text-muted); letter-spacing: 0.04em; margin-top: 1px; }

/* ── Entry animations ── */
@keyframes s-fadein {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}
@keyframes s-slide-up {
  from { opacity: 0; transform: translateY(16px); }
  to   { opacity: 1; transform: translateY(0); }
}
@media (prefers-reduced-motion: no-preference) {
  .hero-card         { animation: s-slide-up 0.50s cubic-bezier(0.22, 1, 0.36, 1) both; }
  .kpi-grid          { animation: s-fadein   0.45s ease 0.05s both; }
  .filter-card       { animation: s-fadein   0.40s ease 0.10s both; }
  .table-card        { animation: s-fadein   0.40s ease 0.15s both; }
  .about-hero        { animation: s-slide-up 0.50s cubic-bezier(0.22, 1, 0.36, 1) both; }
  .disclaimer-card   { animation: s-fadein   0.40s ease 0.20s both; }
  .marker-card       { animation: s-fadein   0.35s ease both; }
  .patient-summary-card { animation: s-slide-up 0.45s ease both; }
  .aki-risk-card     { animation: s-slide-up 0.45s ease 0.06s both; }
}

/* ── Filter panel header ── */
.filter-panel-header { margin-bottom: 14px; }
.filter-panel-title  { font-size: 13px; font-weight: 600; color: var(--text-1); margin-bottom: 3px; }
.filter-panel-sub    { font-size: 11.5px; color: var(--text-3); line-height: 1.4; }

/* ── Theme toggle — fixed floating pill, always visible ── */
@keyframes toggle-pulse {
  0%   { box-shadow: 0 4px 20px rgba(0,0,0,0.30), 0 0 0 0   rgba(139,92,246,0.60), 0 0 10px 2px rgba(139,92,246,0.28); }
  60%  { box-shadow: 0 4px 20px rgba(0,0,0,0.30), 0 0 0 8px rgba(139,92,246,0),    0 0 14px 4px rgba(139,92,246,0.16); }
  100% { box-shadow: 0 4px 20px rgba(0,0,0,0.30), 0 0 0 0   rgba(139,92,246,0),    0 0 10px 2px rgba(139,92,246,0.28); }
}
div[data-testid="stToggle"] {
  position: fixed !important;
  top: 12px !important;
  right: 20px !important;
  z-index: 9999 !important;
  display: inline-flex !important;
  align-items: center;
  background: var(--surface-2) !important;
  border: 1.5px solid rgba(139,92,246,0.70) !important;
  border-radius: 999px !important;
  padding: 8px 18px 8px 14px !important;
  width: fit-content !important;
  cursor: pointer;
  backdrop-filter: blur(14px) !important;
  -webkit-backdrop-filter: blur(14px) !important;
  animation: toggle-pulse 2.6s ease-in-out infinite;
  transition: border-color 0.2s ease, background 0.2s ease,
              box-shadow 0.2s ease, transform 0.15s ease;
}
div[data-testid="stToggle"]:hover {
  animation: none !important;
  border-color: rgba(139,92,246,0.95) !important;
  background: rgba(139,92,246,0.16) !important;
  box-shadow: 0 4px 24px rgba(0,0,0,0.35), 0 0 0 3px rgba(139,92,246,0.22), 0 0 20px 5px rgba(139,92,246,0.32) !important;
  transform: scale(1.06);
}
div[data-testid="stToggle"]:active {
  transform: scale(0.97);
  box-shadow: 0 2px 10px rgba(0,0,0,0.22), 0 0 0 2px rgba(139,92,246,0.45) !important;
}
div[data-testid="stToggle"] label {
  display: flex !important;
  align-items: center !important;
  gap: 8px !important;
  cursor: pointer !important;
}
div[data-testid="stToggle"] label p {
  color: var(--text-1) !important;
  font-size: 13px !important;
  font-weight: 700 !important;
  letter-spacing: 0.05em !important;
  text-transform: uppercase !important;
  margin: 0 !important;
}
</style>
"""

_THEME_CSS_PATH = _ROOT / "docs" / "design" / "lightmode-specs" / "theme.css"
st.markdown(f"<style>{_THEME_CSS_PATH.read_text()}</style>", unsafe_allow_html=True)
st.markdown(CUSTOM_CSS, unsafe_allow_html=True)
# Inject light-mode overrides last so they win the cascade without !important.
inject_theme_attribute()


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------

@st.cache_data(show_spinner=False)
def load_data() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Load all four pipeline output files and attach synthetic display names."""
    patients = pd.read_csv(_OUTPUTS / "dashboard_patients.csv")
    markers  = pd.read_csv(_OUTPUTS / "patient_marker_summary.csv")
    ts       = pd.read_csv(_OUTPUTS / "patient_timeseries.csv", parse_dates=["charttime"])
    aki      = pd.read_csv(_OUTPUTS / "aki_risk_scores.csv")
    add_display_names(patients)
    return patients, markers, ts, aki


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

_TIER_CSS = {"High": "high", "Moderate": "moderate", "Low": "low"}
_TIER_COLOR = {"High": "var(--risk-high)", "Moderate": "var(--risk-mod)", "Low": "var(--risk-low)"}

PRIORITY_MARKERS = [
    "creatinine", "bun", "potassium", "bicarbonate",
    "wbc", "hemoglobin", "heart_rate", "map_noninvasive", "map_arterial", "sbp",
]


# ---------------------------------------------------------------------------
# SVG helpers
# ---------------------------------------------------------------------------

def sparkline_svg(values: list, w: int = 70, h: int = 20, color: str = "#38bdf8") -> str:
    """Inline SVG sparkline from a list of numeric values."""
    clean = [v for v in values if v is not None and not (isinstance(v, float) and math.isnan(v))]
    if len(clean) < 2:
        return ""
    vmin, vmax = min(clean), max(clean)
    span = vmax - vmin or 1
    pad = 2
    pts = [
        (pad + i / (len(clean) - 1) * (w - pad * 2),
         pad + (1 - (v - vmin) / span) * (h - pad * 2))
        for i, v in enumerate(clean)
    ]
    path = "M" + " L".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    fill = f"{path} L{pts[-1][0]:.1f},{h - pad} L{pts[0][0]:.1f},{h - pad} Z"
    return (
        f'<svg width="{w}" height="{h}" style="display:block;overflow:visible;">'
        f'<path d="{fill}" fill="{color}" opacity="0.15"/>'
        f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.5"'
        f' stroke-linejoin="round" stroke-linecap="round"/>'
        f'</svg>'
    )


def risk_dial_svg(score: int, tier: str) -> str:
    """Circular gauge SVG — score 0–100."""
    color = {"High": "#f87171", "Moderate": "#fbbf24", "Low": "#4ade80"}.get(tier, "#4ade80")
    r, cx, cy = 36, 44, 44
    circ = 2 * math.pi * r
    offset = circ * (1 - min(score, 100) / 100)
    return (
        f'<svg width="88" height="88">'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="rgba(148,163,184,0.12)"'
        f' stroke-width="6" fill="none"/>'
        f'<circle cx="{cx}" cy="{cy}" r="{r}" stroke="{color}" stroke-width="6" fill="none"'
        f' stroke-dasharray="{circ:.2f}" stroke-dashoffset="{offset:.2f}"'
        f' stroke-linecap="round" transform="rotate(-90 {cx} {cy})"/>'
        f'<text x="{cx}" y="{cy + 7}" text-anchor="middle" font-size="18"'
        f' font-weight="700" fill="{color}"'
        f' font-family="JetBrains Mono,ui-monospace,monospace">{score}</text>'
        f'</svg>'
    )


def ref_scale_html(value: float, low: float, high: float, status: str) -> str:
    """Reference range scale bar showing where the value falls."""
    if not (pd.notna(value) and pd.notna(low) and pd.notna(high)) or high <= low:
        return ""
    color = "#f87171" if status == "High" else "#60a5fa" if status == "Low" else "#4ade80"
    shadow = (
        "rgba(248,113,113,0.25)" if status == "High"
        else "rgba(56,189,248,0.25)" if status == "Low"
        else "rgba(74,222,128,0.25)"
    )
    span = (high - low) * 2.5
    start = low - (high - low) * 0.75
    low_pct  = max(0.0, min(100.0, (low  - start) / span * 100))
    high_pct = max(0.0, min(100.0, (high - start) / span * 100))
    val_pct  = max(2.0, min(98.0,  (value - start) / span * 100))
    return (
        f'<div class="ref-scale">'
        f'<div class="ref-scale-track">'
        f'<div class="ref-scale-band"'
        f' style="left:{low_pct:.1f}%;width:{high_pct - low_pct:.1f}%;"></div>'
        f'<div class="ref-scale-marker"'
        f' style="left:{val_pct:.1f}%;background:{color};'
        f'box-shadow:0 0 0 3px {shadow};"></div>'
        f'</div>'
        f'<div class="ref-scale-labels">'
        f'<span>{low}</span><span>REF</span><span>{high}</span>'
        f'</div>'
        f'</div>'
    )


# ---------------------------------------------------------------------------
# HTML component builders
# ---------------------------------------------------------------------------

def risk_badge_html(tier: str) -> str:
    css = _TIER_CSS.get(tier, "low")
    color = {"High": "#f87171", "Moderate": "#fbbf24", "Low": "#4ade80"}.get(tier, "#4ade80")
    return (
        f'<span class="risk-badge {css}">'
        f'<span class="risk-dot" style="background:{color};"></span>'
        f'{tier.upper()}'
        f'</span>'
    )


def status_pill_html(status: str) -> str:
    css = status.lower() if status.lower() in ("high", "low") else "normal"
    return f'<span class="status-pill {css}">{status.upper()}</span>'


def kpi_card_html(value: str, label: str, sub: str, css_class: str, stripe: str, icon: str) -> str:
    return (
        f'<div class="kpi-card {css_class}">'
        f'<div class="kpi-stripe" style="background:{stripe};"></div>'
        f'<div class="kpi-top">'
        f'<span class="kpi-icon" style="color:{stripe};">{icon}</span>'
        f'<span class="kpi-label">{label}</span>'
        f'</div>'
        f'<div class="kpi-value">{value}</div>'
        f'<div class="kpi-sub">{sub}</div>'
        f'</div>'
    )


def hero_html(patients: pd.DataFrame) -> str:
    total_n = len(patients)
    high_n  = int((patients["aki_risk_tier"] == "High").sum())
    mod_n   = int((patients["aki_risk_tier"] == "Moderate").sum())
    avg_abn = patients["abnormal_marker_count"].mean()

    high_pct = round(high_n / total_n * 100) if total_n else 0
    mod_pct  = round(mod_n  / total_n * 100) if total_n else 0

    top_risk = (
        patients[patients["aki_risk_tier"] == "High"]
        .sort_values("aki_risk_score", ascending=False)
        .head(8)
    )

    ticker_items = "".join(
        f'<div class="ticker-item">'
        f'<span class="ticker-id">{_html.escape(str(r.get("display_name", f"#{int(r.hadm_id)}")))}</span>'
        f'<span class="ticker-score">{int(r.aki_risk_score)}</span>'
        f'<span class="ticker-concern">{_html.escape(str(r.get("top_concern", ""))[:40])}</span>'
        f'</div>'
        for _, r in top_risk.iterrows()
    )
    ticker_doubled = ticker_items * 2  # duplicate for seamless loop

    watchlist_html = (
        f'<div class="hero-watchlist">'
        f'<div class="hero-watchlist-label">LIVE · WATCHLIST · HIGH RISK</div>'
        f'<div class="hero-ticker"><div class="hero-ticker-inner">{ticker_doubled}</div></div>'
        f'</div>'
        if ticker_items else ""
    )

    return (
        f'<div class="hero-card">'
        f'<div class="hero-grid">'
        # left
        f'<div>'
        f'<div class="hero-eyebrow">Clinical Marker Intelligence · AKI Early-Warning Module</div>'
        f'<div class="hero-wordmark">Str<span class="hero-accent">a</span>ta</div>'
        f'<div style="font-size:13px;font-weight:600;color:var(--text-2);margin:-4px 0 8px 0;letter-spacing:0.01em;">'
        f'Clinical Marker Intelligence + AKI Early-Warning'
        f'</div>'
        f'<div class="hero-tagline">'
        f'Surface abnormal labs, vital trends, and kidney deterioration signals from structured EHR data.'
        f'</div>'
        f'<div class="hero-stats">'
        f'<div class="hero-stat">'
        f'<div class="hero-stat-value" style="color:var(--text-2);">{total_n}</div>'
        f'<div class="hero-stat-label">Admissions</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'<div class="hero-stat-value" style="color:var(--risk-high);">{high_n}</div>'
        f'<div class="hero-stat-label">High Risk · {high_pct}%</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'<div class="hero-stat-value" style="color:var(--risk-mod);">{mod_n}</div>'
        f'<div class="hero-stat-label">Moderate · {mod_pct}%</div>'
        f'</div>'
        f'<div class="hero-stat">'
        f'<div class="hero-stat-value" style="color:var(--accent-info);">{avg_abn:.1f}</div>'
        f'<div class="hero-stat-label">Avg Abnormal</div>'
        f'</div>'
        f'</div>'
        f'</div>'
        # right
        f'<div class="hero-right">'
        f'<div class="demo-mode-pill"><span class="demo-dot"></span>Demo Mode</div>'
        f'{watchlist_html}'
        f'<div class="hero-disclaimer-inline">Not diagnostic · For clinical review only</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def render_hero_component(patients: pd.DataFrame) -> None:
    """Render hero card via iframe so the JS live clock updates every second.

    Uses hardcoded colors matched to the active theme since the iframe cannot
    read parent-page CSS variables.
    """
    theme = get_theme()
    is_dark = theme == "dark"

    total_n  = len(patients)
    high_n   = int((patients["aki_risk_tier"] == "High").sum())
    mod_n    = int((patients["aki_risk_tier"] == "Moderate").sum())
    avg_abn  = patients["abnormal_marker_count"].mean()
    high_pct = round(high_n / total_n * 100) if total_n else 0
    mod_pct  = round(mod_n  / total_n * 100) if total_n else 0

    top_risk = (
        patients[patients["aki_risk_tier"] == "High"]
        .sort_values("aki_risk_score", ascending=False)
        .head(8)
    )
    ticker_items = "".join(
        f'<span class="t-item">'
        f'<span class="t-sep">▸</span>'
        f'<span class="t-id">{_html.escape(str(r.get("display_name", f"#{int(r.hadm_id)}")))}</span>'
        f'<span class="t-score"> {int(r.aki_risk_score)}</span>'
        f'<span class="t-con"> {_html.escape(str(r.get("top_concern", ""))[:42])}</span>'
        f'</span>'
        for _, r in top_risk.iterrows()
    )
    ticker_doubled = (ticker_items * 2) if ticker_items else ""

    if is_dark:
        body_bg   = "#060d1b"
        card_bg   = "radial-gradient(ellipse at top right, rgba(29,78,216,0.10), transparent 60%), #0d1626"
        card_bdr  = "#1a2e4a"
        text1     = "#f1f5f9"
        text2     = "#e2e8f0"
        text3     = "#94a3b8"
        muted     = "#475569"
        surface   = "rgba(13,22,38,0.55)"
        surf_bdr  = "#1a2e4a"
        acc_blue  = "#38bdf8"
        risk_high = "#f87171"
        risk_mod  = "#fbbf24"
        acc_info  = "#a78bfa"
        tkr_bg    = "rgba(6,13,27,0.50)"
    else:
        body_bg   = "#f4f6fb"
        card_bg   = "radial-gradient(900px 400px at 100% -20%, rgba(2,132,199,0.10), transparent 60%), #ffffff"
        card_bdr  = "#e2e8f0"
        text1     = "#0b1220"
        text2     = "#1e293b"
        text3     = "#475569"
        muted     = "#64748b"
        surface   = "#f5f7fb"
        surf_bdr  = "#e2e8f0"
        acc_blue  = "#0284c7"
        risk_high = "#dc2626"
        risk_mod  = "#d97706"
        acc_info  = "#7c3aed"
        tkr_bg    = "rgba(238,242,248,0.80)"

    grad = "linear-gradient(90deg,#1d4ed8 0%,#3b82f6 45%,#22d3ee 100%)"

    ticker_section = ""
    if ticker_doubled:
        ticker_section = f"""
  <div class="tkr-wrap">
    <div class="tkr-lbl"><span class="live-dot"></span>LIVE · WATCHLIST · HIGH RISK</div>
    <div class="tkr-track"><div class="tkr-inner">{ticker_doubled}</div></div>
  </div>"""

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8">
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600;700&display=swap" rel="stylesheet">
<style>
*{{margin:0;padding:0;box-sizing:border-box;}}
html,body{{height:100%;background:{body_bg};font-family:'Inter',-apple-system,sans-serif;-webkit-font-smoothing:antialiased;overflow:hidden;}}
.hero{{background:{card_bg};border:1px solid {card_bdr};border-radius:14px;overflow:hidden;}}
.top-bar{{height:3px;background:{grad};}}
.grid{{display:grid;grid-template-columns:1.4fr 1fr;gap:28px;padding:22px 28px 18px;align-items:start;}}
.eyebrow{{font-size:10px;letter-spacing:.22em;color:{acc_blue};font-weight:600;text-transform:uppercase;margin-bottom:10px;}}
.wm{{font-size:50px;font-weight:800;letter-spacing:-.045em;line-height:.93;margin:0 0 8px;color:{text1};}}
.wm .ac{{background:{grad};-webkit-background-clip:text;background-clip:text;color:transparent;}}
.sub{{font-size:12.5px;font-weight:600;color:{text2};margin:0 0 6px;letter-spacing:.01em;}}
.tgl{{font-size:12.5px;line-height:1.5;color:{text3};max-width:440px;margin-bottom:16px;}}
.stats{{display:grid;grid-template-columns:repeat(4,1fr);gap:10px;}}
.stat{{background:{surface};border:1px solid {surf_bdr};border-radius:10px;padding:10px 12px;}}
.sv{{font-family:'JetBrains Mono',monospace;font-size:26px;font-weight:700;letter-spacing:-.02em;line-height:1;margin-bottom:5px;font-variant-numeric:tabular-nums;}}
.sl{{font-size:9px;letter-spacing:.16em;color:{text3};text-transform:uppercase;font-weight:600;}}
.rgt{{display:flex;flex-direction:column;gap:12px;}}
.pill{{display:inline-flex;align-items:center;gap:8px;padding:7px 13px;border-radius:999px;background:rgba(56,189,248,.08);border:1px solid rgba(56,189,248,.30);font-size:11px;letter-spacing:.16em;color:{acc_blue};font-weight:600;text-transform:uppercase;width:fit-content;}}
.pdot{{width:7px;height:7px;border-radius:50%;background:{acc_blue};box-shadow:0 0 10px {acc_blue};flex-shrink:0;animation:pulse 1.6s ease-in-out infinite;}}
@keyframes pulse{{0%,100%{{opacity:.55;transform:scale(.9);}}50%{{opacity:1;transform:scale(1.15);}}}}
.ck-box{{background:{surface};border:1px solid {surf_bdr};border-radius:10px;padding:12px 16px;}}
.ck-lbl{{font-size:9px;letter-spacing:.20em;color:{muted};text-transform:uppercase;font-weight:600;margin-bottom:6px;}}
.ck-time{{font-family:'JetBrains Mono',monospace;font-size:28px;font-weight:700;letter-spacing:-.02em;line-height:1;color:{text2};font-variant-numeric:tabular-nums;}}
.disc{{font-size:10.5px;color:{muted};line-height:1.5;}}
.tkr-wrap{{border-top:1px solid {surf_bdr};background:{tkr_bg};padding:8px 0 10px;}}
.tkr-lbl{{font-size:9px;letter-spacing:.20em;color:{muted};text-transform:uppercase;font-weight:600;padding:0 16px 6px;display:flex;align-items:center;gap:6px;}}
.live-dot{{width:5px;height:5px;border-radius:50%;background:{risk_high};box-shadow:0 0 6px {risk_high};flex-shrink:0;animation:pulse 1.6s ease-in-out infinite;}}
.tkr-track{{overflow:hidden;mask-image:linear-gradient(90deg,transparent,black 4%,black 96%,transparent);-webkit-mask-image:linear-gradient(90deg,transparent,black 4%,black 96%,transparent);}}
.tkr-inner{{display:flex;gap:0;animation:scroll 38s linear infinite;white-space:nowrap;}}
@keyframes scroll{{from{{transform:translateX(0);}}to{{transform:translateX(-50%);}}}}
.t-item{{display:inline-flex;align-items:center;gap:5px;font-size:11px;padding:0 18px 0 0;}}
.t-sep{{color:{muted};font-size:9px;}}
.t-id{{color:{text3};font-family:'JetBrains Mono',monospace;font-size:10.5px;}}
.t-score{{font-family:'JetBrains Mono',monospace;font-weight:700;color:{risk_high};font-size:11px;}}
.t-con{{color:{text3};font-size:10.5px;}}
</style></head>
<body>
<div class="hero">
  <div class="top-bar"></div>
  <div class="grid">
    <div>
      <div class="eyebrow">Clinical Marker Intelligence · AKI Early-Warning Module</div>
      <div class="wm">Str<span class="ac">a</span>ta</div>
      <div class="sub">Clinical Marker Intelligence + AKI Early-Warning</div>
      <div class="tgl">Surface abnormal labs, vital trends, and kidney deterioration signals from structured EHR data.</div>
      <div class="stats">
        <div class="stat"><div class="sv" style="color:{text2};">{total_n}</div><div class="sl">Admissions</div></div>
        <div class="stat"><div class="sv" style="color:{risk_high};">{high_n}</div><div class="sl">High Risk · {high_pct}%</div></div>
        <div class="stat"><div class="sv" style="color:{risk_mod};">{mod_n}</div><div class="sl">Moderate · {mod_pct}%</div></div>
        <div class="stat"><div class="sv" style="color:{acc_info};">{avg_abn:.1f}</div><div class="sl">Avg Abnormal</div></div>
      </div>
    </div>
    <div class="rgt">
      <div class="pill"><span class="pdot"></span>Demo Mode</div>
      <div class="ck-box">
        <div class="ck-lbl">SESSION · LOCAL TIME</div>
        <div class="ck-time" id="ck">--:--:--</div>
      </div>
      <div class="disc">Not diagnostic · For clinical review only</div>
    </div>
  </div>
  {ticker_section}
</div>
<script>
function tick(){{var n=new Date(),el=document.getElementById('ck');if(el)el.textContent=String(n.getHours()).padStart(2,'0')+':'+String(n.getMinutes()).padStart(2,'0')+':'+String(n.getSeconds()).padStart(2,'0');}}
tick();setInterval(tick,1000);
</script>
</body></html>"""

    components.html(html, height=360, scrolling=False)


def build_patient_table_html(df: pd.DataFrame) -> str:
    """Patient admissions table with row rail and score bar."""
    rows = []
    for _, r in df.iterrows():
        tier    = str(r.get("aki_risk_tier", "Low"))
        score   = int(r.get("aki_risk_score", 0))
        css     = _TIER_CSS.get(tier, "low")
        pct     = min(score, 100)
        sex     = "Male" if r.get("gender", "M") == "M" else "Female"
        icu_tag = '<span class="info-tag">ICU</span>' if r.get("has_icu_stay", False) else '<span class="td-muted">—</span>'
        abn     = int(r.get("abnormal_marker_count", 0))
        concern_raw   = str(r.get("top_concern", ""))
        concern_short = _html.escape(concern_raw[:60] + ("…" if len(concern_raw) > 60 else ""))
        concern_title = _html.escape(concern_raw)
        display_name = str(r.get("display_name", f"Subject {int(r['subject_id'])}"))
        rows.append(
            f'<tr class="row-{css}">'
            f'<td class="td-rail"><span class="row-rail rail-{css}"></span></td>'
            f'<td class="cell-strong">{_html.escape(display_name)}</td>'
            f'<td class="td-mono td-muted" style="font-size:0.78rem;">{_html.escape(str(int(r["hadm_id"])))}</td>'
            f'<td>{_html.escape(str(r.get("anchor_age", "—")))}</td>'
            f'<td>{sex}</td>'
            f'<td>{icu_tag}</td>'
            f'<td>'
            f'<div class="score-cell">'
            f'<span class="score-num" style="color:{_TIER_COLOR.get(tier, "var(--risk-low)")};">{score}</span>'
            f'<div class="score-bar"><div class="score-bar-fill {css}" style="width:{pct}%;"></div></div>'
            f'</div>'
            f'</td>'
            f'<td>{risk_badge_html(tier)}</td>'
            f'<td class="td-mono" style="text-align:center;">{abn}</td>'
            f'<td class="td-concern" title="{concern_title}">{concern_short}</td>'
            f'</tr>'
        )
    rows_html = "\n".join(rows)

    if not rows:
        return (
            '<div class="table-card">'
            '<div class="empty-state">'
            '<div class="empty-icon">∅</div>'
            '<div class="empty-title">No admissions match your filters</div>'
            '<div class="empty-sub">Try widening the risk tier or clearing the search.</div>'
            '</div></div>'
        )

    return (
        '<div class="table-card">'
        '<table class="patient-table">'
        '<thead><tr>'
        '<th class="th-rail"></th>'
        '<th>Patient</th><th>Adm #</th><th>Age</th><th>Sex</th>'
        '<th>ICU</th><th>AKI Risk Score</th><th>Tier</th>'
        '<th>Abnormal</th><th>Top Concern</th>'
        '</tr></thead>'
        f'<tbody>{rows_html}</tbody>'
        '</table></div>'
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
    tone = status.lower() if status.lower() in ("high", "low") else "normal"
    color = (
        "var(--risk-high)" if tone == "high"
        else "var(--accent-blue)" if tone == "low"
        else "var(--risk-low)"
    )
    value_fmt = f"{value:.1f}" if pd.notna(value) else "—"
    ref_parts = []
    if pd.notna(normal_low):
        ref_parts.append(str(normal_low))
    if pd.notna(normal_high):
        ref_parts.append(str(normal_high))
    ref_str = f"Ref: {' – '.join(ref_parts)} {unit}".strip() if ref_parts else unit

    scale_html = ""
    if pd.notna(value) and pd.notna(normal_low) and pd.notna(normal_high):
        scale_html = ref_scale_html(float(value), float(normal_low), float(normal_high), status)

    aki_tag  = '<span class="aki-tag">AKI-Relevant</span>' if is_aki_relevant else ""
    expl_str = str(explanation) if explanation and str(explanation) not in ("nan", "") else ""
    blurb    = f'<div class="marker-explain">{_html.escape(expl_str)}</div>' if expl_str else ""

    return (
        f'<div class="marker-card">'
        f'<div class="marker-rail rail-{tone}"></div>'
        f'<div class="marker-card-head">'
        f'<span class="marker-name">{_html.escape(name)}</span>'
        f'{status_pill_html(status)}'
        f'</div>'
        f'<div class="marker-value" style="color:{color};">'
        f'{value_fmt}<span class="marker-unit">{_html.escape(unit)}</span>'
        f'</div>'
        f'{scale_html}'
        f'<div class="marker-ref">{ref_str}</div>'
        f'{aki_tag}'
        f'{blurb}'
        f'</div>'
    )


def patient_summary_html(row: pd.Series) -> str:
    sex_label    = "Male" if row.get("gender", "M") == "M" else "Female"
    icu_tag      = '<span class="info-tag">ICU Admission</span>' if row.get("has_icu_stay", False) else ""
    los          = row.get("length_of_stay_days", 0)
    los_str      = f"{los:.1f} days" if pd.notna(los) else "—"
    abn          = int(row.get("abnormal_marker_count", 0))
    hi           = int(row.get("high_marker_count", 0))
    lo           = int(row.get("low_marker_count", 0))
    display_name = str(row.get("display_name", f"Subject {int(row['subject_id'])}"))
    return (
        f'<div class="patient-summary-card">'
        f'<div class="patient-eyebrow">Adm {int(row["hadm_id"])} · ID {int(row["subject_id"])}</div>'
        f'<div class="patient-name">{_html.escape(display_name)}</div>'
        f'<div class="patient-pills">'
        f'<span class="info-tag">Age {row.get("anchor_age", "—")}</span>'
        f'<span class="info-tag">{sex_label}</span>'
        f'{icu_tag}'
        f'<span class="info-tag">{_html.escape(str(row.get("admission_type", "—")))}</span>'
        f'<span class="info-tag">LOS {los_str}</span>'
        f'</div>'
        f'<div class="mini-stat-grid">'
        f'<div class="mini-stat">'
        f'<div class="mini-stat-label">Abnormal Markers</div>'
        f'<div class="mini-stat-value" style="color:var(--accent-info);">{abn}</div>'
        f'</div>'
        f'<div class="mini-stat">'
        f'<div class="mini-stat-label">High</div>'
        f'<div class="mini-stat-value" style="color:var(--risk-high);">{hi}</div>'
        f'</div>'
        f'<div class="mini-stat">'
        f'<div class="mini-stat-label">Low</div>'
        f'<div class="mini-stat-value" style="color:var(--accent-blue);">{lo}</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )


def aki_card_html(row: pd.Series) -> str:
    score   = int(row.get("aki_risk_score", 0))
    tier    = str(row.get("aki_risk_tier", "Low"))
    css     = _TIER_CSS.get(tier, "low")
    color   = _TIER_COLOR.get(tier, "var(--risk-low)")
    pct     = min(score, 100)
    reasons = [r.strip() for r in str(row.get("top_reasons", "")).split("|") if r.strip()]
    signals = "".join(
        f'<li><span class="signal-dot" style="background:{color};"></span>{_html.escape(r)}</li>'
        for r in reasons[:5]
    )
    dial = risk_dial_svg(score, tier)
    return (
        f'<div class="aki-risk-card aki-{css}">'
        f'<div class="aki-risk-top">'
        f'<div>'
        f'<div class="section-label">AKI Risk Signal</div>'
        f'<div class="aki-score-row">'
        f'<div class="aki-score" style="color:{color};">{score}</div>'
        f'<div class="aki-score-frac">/ 100</div>'
        f'</div>'
        f'{risk_badge_html(tier)}'
        f'</div>'
        f'{dial}'
        f'</div>'
        f'<div class="aki-score-bar">'
        f'<div class="aki-score-bar-fill" style="width:{pct}%;background:{color};"></div>'
        f'<div class="aki-score-bar-tick" style="left:30%;"></div>'
        f'<div class="aki-score-bar-tick" style="left:60%;"></div>'
        f'</div>'
        f'<div class="aki-score-bar-labels">'
        f'<span>0</span><span>Low</span><span>Moderate</span><span>High</span><span>100</span>'
        f'</div>'
        f'<div class="contributing-signals">'
        f'<div class="section-label">Contributing Signals</div>'
        f'<ul class="signals-list">{signals}</ul>'
        f'</div>'
        f'</div>'
    )


def make_trend_chart(
    ts_df: pd.DataFrame,
    marker_key: str,
    marker_name: str,
    unit: str,
    accent: str = "#38bdf8",
) -> go.Figure | None:
    """Dark-themed Plotly area chart matching the design's visual language."""
    df = ts_df[ts_df["marker_key"] == marker_key].sort_values("charttime")
    if df.empty:
        return None

    tl = plotly_theme_layout()
    is_dark = get_theme() == "dark"
    grid_color  = tl["yaxis"]["gridcolor"]
    line_color  = tl["xaxis"]["linecolor"]
    tick_color  = "#475569" if is_dark else "#64748b"
    hover_bg    = "#0d1626" if is_dark else "rgba(255,255,255,0.98)"
    hover_border= "#25406b" if is_dark else "#e2e8f0"
    hover_font  = "#e2e8f0" if is_dark else "#1e293b"
    dot_border  = "#060d1b" if is_dark else "#ffffff"

    fill_rgba = accent.replace("#", "")
    r = int(fill_rgba[0:2], 16) if len(fill_rgba) == 6 else 56
    g = int(fill_rgba[2:4], 16) if len(fill_rgba) == 6 else 189
    b = int(fill_rgba[4:6], 16) if len(fill_rgba) == 6 else 248

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=df["charttime"], y=df["value"],
        mode="lines+markers",
        line=dict(color=accent, width=2, shape="linear"),
        marker=dict(size=5, color=accent, line=dict(color=dot_border, width=1.5)),
        fill="tozeroy",
        fillcolor=f"rgba({r},{g},{b},0.07)",
        hovertemplate=f"%{{x|%b %d %H:%M}}<br><b>%{{y:.2f}} {unit}</b><extra></extra>",
        name=marker_name,
    ))
    fig.update_layout(
        template=tl["template"],
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color=tl["font_color"],
        font_family="Inter, sans-serif",
        title=dict(
            text=f"<span style='font-size:12px;color:{tick_color};font-family:Inter,sans-serif;font-weight:600'>{marker_name}</span>",
            x=0, pad=dict(b=6),
        ),
        margin=dict(l=8, r=8, t=36, b=8),
        height=220,
        xaxis=dict(
            showgrid=False, zeroline=False,
            tickfont=dict(size=9, color=tick_color, family="JetBrains Mono, monospace"),
            tickformat="%b %d",
            tickcolor=line_color,
            linecolor=line_color,
        ),
        yaxis=dict(
            gridcolor=grid_color, gridwidth=1,
            zeroline=False,
            tickfont=dict(size=9, color=tick_color, family="JetBrains Mono, monospace"),
            title=dict(text=unit, font=dict(size=9, color=tick_color), standoff=4),
            tickcolor=line_color,
            linecolor=line_color,
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=hover_bg,
            bordercolor=hover_border,
            font=dict(color=hover_font, size=12, family="Inter, sans-serif"),
        ),
        showlegend=False,
    )
    return fig


def section_label(text: str, meta: str = "") -> None:
    meta_html = f'<span class="section-action-meta">{meta}</span>' if meta else ""
    st.markdown(
        f'<div class="section-label-row">'
        f'<div class="section-label">{text}</div>'
        f'{meta_html}'
        f'</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tab 1 — Overview
# ---------------------------------------------------------------------------

def render_overview(patients: pd.DataFrame) -> None:
    render_hero_component(patients)

    total_n = len(patients)
    high_n  = int((patients["aki_risk_tier"] == "High").sum())
    mod_n   = int((patients["aki_risk_tier"] == "Moderate").sum())
    avg_abn = patients["abnormal_marker_count"].mean()
    high_pct = round(high_n / total_n * 100) if total_n else 0
    mod_pct  = round(mod_n  / total_n * 100) if total_n else 0

    section_label("Overview · Key Metrics")
    st.markdown(
        '<div class="kpi-grid">'
        + kpi_card_html(str(total_n), "Total Admissions", "across active dataset", "total",
                        "linear-gradient(90deg,#475569,#64748b)", "■")
        + kpi_card_html(str(high_n), "High AKI Risk", f"{high_pct}% of cohort", "high",
                        "linear-gradient(90deg,var(--risk-high-2),var(--risk-high))", "▲")
        + kpi_card_html(str(mod_n), "Moderate Risk", f"{mod_pct}% of cohort", "mod",
                        "linear-gradient(90deg,var(--risk-mod-2),var(--risk-mod))", "◆")
        + kpi_card_html(f"{avg_abn:.1f}", "Avg Abnormal Markers", "per admission", "info",
                        "linear-gradient(90deg,#7c3aed,var(--accent-info))", "●")
        + '</div>',
        unsafe_allow_html=True,
    )

    # ── Filters
    section_label("Triage Filters")
    st.markdown(
        '<div class="filter-card">'
        '<div class="filter-panel-header">'
        '<div class="filter-panel-title">Triage Filters</div>'
        '<div class="filter-panel-sub">Narrow admissions by risk tier, ICU status, or admission type.</div>'
        '</div>',
        unsafe_allow_html=True,
    )
    fc1, fc2, fc3, fc4 = st.columns([2, 1.4, 1.4, 1.8])
    with fc1:
        search = st.text_input("Search", placeholder="Patient name or admission ID…", key="ov_search", label_visibility="collapsed")
    with fc2:
        st.markdown('<div class="filter-label">AKI Risk Tier</div>', unsafe_allow_html=True)
        sel_tier = st.radio("tier", ["All", "High", "Moderate", "Low"], key="ov_tier", horizontal=True, label_visibility="collapsed")
    with fc3:
        st.markdown('<div class="filter-label">ICU Stay</div>', unsafe_allow_html=True)
        sel_icu = st.radio("icu", ["All", "ICU", "Non-ICU"], key="ov_icu", horizontal=True, label_visibility="collapsed")
    with fc4:
        adm_opts = ["All"] + sorted(patients["admission_type"].dropna().unique().tolist())
        sel_adm  = st.selectbox("Admission Type", adm_opts, key="ov_adm")
    st.markdown('</div>', unsafe_allow_html=True)

    # ── Apply filters
    filtered = patients.copy()
    if search:
        q = search.strip()
        filtered = filtered[
            filtered["display_name"].str.contains(q, case=False, na=False) |
            filtered["subject_id"].astype(str).str.contains(q, na=False) |
            filtered["hadm_id"].astype(str).str.contains(q, na=False)
        ]
    if sel_tier != "All":
        filtered = filtered[filtered["aki_risk_tier"] == sel_tier]
    if sel_icu == "ICU":
        filtered = filtered[filtered["has_icu_stay"] == True]
    elif sel_icu == "Non-ICU":
        filtered = filtered[filtered["has_icu_stay"] == False]
    if sel_adm != "All":
        filtered = filtered[filtered["admission_type"] == sel_adm]
    filtered = filtered.sort_values("aki_risk_score", ascending=False)

    section_label("Patient Admissions · Ranked by AKI Risk Signal", f"Showing {len(filtered)} of {total_n}")
    st.markdown(build_patient_table_html(filtered), unsafe_allow_html=True)

    st.markdown(
        '<div class="disclaimer-card">'
        '<div class="disclaimer-rail"></div>'
        '<div class="disclaimer-body">'
        '<div class="disclaimer-title">Demo Environment · Not for Clinical Use</div>'
        '<div class="disclaimer-text">'
        'All data shown is de-identified demo content (MIMIC-IV Clinical Demo v2.2). '
        'Strata surfaces statistical signals from structured EHR data — it is not a diagnostic '
        'device and does not recommend treatment. Always apply clinical judgment.'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )


# ---------------------------------------------------------------------------
# Tab 2 — Patient Detail
# ---------------------------------------------------------------------------

def render_patient_detail(
    patients: pd.DataFrame,
    markers:  pd.DataFrame,
    ts:       pd.DataFrame,
    aki:      pd.DataFrame,
) -> None:

    sorted_pts = patients.sort_values("aki_risk_score", ascending=False).reset_index(drop=True)
    hadm_list  = sorted_pts["hadm_id"].tolist()
    label_list = [
        f"{r.get('display_name', f'Subject {int(r.subject_id)}')}  ·  Adm {int(r.hadm_id)}  ·  {r.aki_risk_tier} Risk ({int(r.aki_risk_score)}/100)"
        for _, r in sorted_pts.iterrows()
    ]

    if "detail_hadm_id" not in st.session_state:
        st.session_state.detail_hadm_id = int(hadm_list[0])

    def _curr_idx() -> int:
        try:
            return [int(h) for h in hadm_list].index(st.session_state.detail_hadm_id)
        except ValueError:
            return 0

    def _go_prev():
        idx = _curr_idx()
        if idx > 0:
            st.session_state.detail_hadm_id = int(hadm_list[idx - 1])
            st.session_state["detail_sel"] = label_list[idx - 1]

    def _go_next():
        idx = _curr_idx()
        if idx < len(hadm_list) - 1:
            st.session_state.detail_hadm_id = int(hadm_list[idx + 1])
            st.session_state["detail_sel"] = label_list[idx + 1]

    def _on_sel_change():
        lbl = st.session_state.detail_sel
        i   = label_list.index(lbl)
        st.session_state.detail_hadm_id = int(hadm_list[i])

    section_label("Select Admission", f"Sorted by AKI risk · {len(sorted_pts)} admissions")
    nav_prev, nav_sel, nav_next = st.columns([1, 7, 1])
    with nav_prev:
        st.button("↑ Higher risk", key="prev_pt", on_click=_go_prev,
                  disabled=(_curr_idx() == 0), use_container_width=True)
    with nav_sel:
        st.selectbox(
            "Patient admission", label_list,
            index=_curr_idx(), key="detail_sel",
            on_change=_on_sel_change, label_visibility="collapsed",
        )
    with nav_next:
        st.button("↓ Lower risk", key="next_pt", on_click=_go_next,
                  disabled=(_curr_idx() >= len(hadm_list) - 1), use_container_width=True)

    hadm_id = st.session_state.detail_hadm_id
    pt_row  = patients[patients["hadm_id"] == hadm_id].iloc[0]
    ak_row  = aki[aki["hadm_id"] == hadm_id].iloc[0] if (aki["hadm_id"] == hadm_id).any() else pt_row
    pt_mkrs = markers[markers["hadm_id"] == hadm_id]
    pt_ts   = ts[ts["hadm_id"] == hadm_id]

    # ── Patient summary + AKI card side-by-side
    st.markdown(
        f'<div class="patient-header-grid">'
        f'{patient_summary_html(pt_row)}'
        f'{aki_card_html(ak_row)}'
        f'</div>',
        unsafe_allow_html=True,
    )

    # ── Abnormal markers
    abnormal = pt_mkrs[pt_mkrs["status"].isin(["High", "Low"])].copy()
    abnormal = abnormal.sort_values(["is_aki_relevant", "marker_name"], ascending=[False, True])

    in_range = len(pt_mkrs) - len(abnormal)
    section_label("Abnormal Markers", f"{len(abnormal)} flagged · {in_range} within range")

    if abnormal.empty:
        st.markdown(
            '<div class="table-card">'
            '<div class="empty-state">'
            '<div class="empty-icon">✓</div>'
            '<div class="empty-title">All markers within reference range</div>'
            '<div class="empty-sub">No abnormal labs or vitals identified for this admission.</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        cards_html = "".join(
            marker_card_html(
                name=mkr["marker_name"],
                value=mkr["latest_value"],
                unit=str(mkr["unit"]),
                status=mkr["status"],
                normal_low=mkr.get("normal_low"),
                normal_high=mkr.get("normal_high"),
                explanation=str(mkr.get("explanation", "")),
                is_aki_relevant=bool(mkr.get("is_aki_relevant", False)),
            )
            for _, mkr in abnormal.iterrows()
        )
        st.markdown(f'<div class="marker-grid">{cards_html}</div>', unsafe_allow_html=True)

    # ── Trend charts
    available_keys    = pt_ts["marker_key"].unique().tolist()
    priority_available = [k for k in PRIORITY_MARKERS if k in available_keys]
    other_available    = [k for k in available_keys if k not in PRIORITY_MARKERS]
    ordered_keys       = priority_available + other_available

    if not pt_ts.empty and ordered_keys:
        section_label("Trend View · Priority Markers")
        key_to_name = {k: pt_ts[pt_ts["marker_key"] == k]["marker_name"].iloc[0] for k in ordered_keys}
        sel_markers = st.multiselect(
            "Select markers to chart",
            options=ordered_keys,
            default=priority_available[:4],
            format_func=lambda k: key_to_name.get(k, k),
            key="detail_markers",
        )
        if sel_markers:
            for i in range(0, len(sel_markers), 2):
                row_keys = sel_markers[i:i + 2]
                ch_cols  = st.columns(len(row_keys))
                for col, mk in zip(ch_cols, row_keys):
                    with col:
                        mk_ts   = pt_ts[pt_ts["marker_key"] == mk]
                        mk_name = key_to_name.get(mk, mk)
                        mk_unit = mk_ts["unit"].iloc[0] if not mk_ts.empty else ""
                        mk_summary = pt_mkrs[pt_mkrs["marker_key"] == mk]
                        _mk_status = mk_summary.iloc[0].get("status", "Normal") if not mk_summary.empty else "Normal"
                        _is_dark = get_theme() == "dark"
                        _mk_accent = ("#f87171" if _is_dark else "#dc2626") if _mk_status == "High" else ("#60a5fa" if _is_dark else "#2563eb") if _mk_status == "Low" else ("#38bdf8" if _is_dark else "#0284c7")
                        fig     = make_trend_chart(pt_ts, mk, mk_name, mk_unit, accent=_mk_accent)
                        if fig:
                            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
                            if not mk_summary.empty:
                                exp    = str(mk_summary.iloc[0].get("explanation", ""))
                                status = mk_summary.iloc[0].get("status", "Normal")
                                if exp and exp not in ("nan", "") and status != "Normal":
                                    st.markdown(
                                        f'<div class="trend-explain">'
                                        f'<div class="trend-explain-label">Clinical Context</div>'
                                        f'<div class="trend-explain-text">{_html.escape(exp)}</div>'
                                        f'</div>',
                                        unsafe_allow_html=True,
                                    )
                        else:
                            st.caption(f"No trend data for {mk_name}")
    else:
        st.info("No trend data available for this admission.")


# ---------------------------------------------------------------------------
# Tab 3 — Marker Explorer
# ---------------------------------------------------------------------------

def render_marker_explorer(
    patients: pd.DataFrame,
    markers:  pd.DataFrame,
    ts:       pd.DataFrame,
) -> None:

    section_label("Explore Clinical Markers")

    f1, f2, f3, f4 = st.columns([2.2, 1.2, 1.4, 1])
    with f1:
        search = st.text_input("Search marker name", placeholder="e.g. Creatinine, WBC, Potassium…", key="me_search")
    with f2:
        cat_opts = ["All"] + sorted(markers["category"].dropna().unique().tolist())
        sel_cat  = st.selectbox("Category", cat_opts, key="me_cat")
    with f3:
        sorted_pts = patients.sort_values("aki_risk_score", ascending=False)
        pt_options = {
            f"{r.get('display_name', f'Subject {int(r.subject_id)}')}  ·  {r.aki_risk_tier} ({int(r.aki_risk_score)})": int(r.hadm_id)
            for _, r in sorted_pts.iterrows()
        }
        sel_pt_label = st.selectbox("Patient admission", list(pt_options.keys()), key="me_patient")
        sel_hadm     = pt_options[sel_pt_label]
    with f4:
        abnormal_only = st.checkbox("Abnormal only", value=False, key="me_abn")

    pt_mkrs = markers[markers["hadm_id"] == sel_hadm].copy()
    if search:
        pt_mkrs = pt_mkrs[pt_mkrs["marker_name"].str.contains(search, case=False, na=False)]
    if abnormal_only:
        pt_mkrs = pt_mkrs[pt_mkrs["status"].isin(["High", "Low"])]
    if sel_cat != "All":
        pt_mkrs = pt_mkrs[pt_mkrs["category"] == sel_cat]

    pt_ts = ts[ts["hadm_id"] == sel_hadm]
    ts_by_key: dict[str, list[float]] = {}
    for mk_key in pt_mkrs["marker_key"].unique():
        vals = (
            pt_ts[pt_ts["marker_key"] == mk_key]
            .sort_values("charttime")["value"]
            .dropna()
            .tolist()
        )
        ts_by_key[mk_key] = vals

    sel_pt_row   = patients[patients["hadm_id"] == sel_hadm]
    sel_pt_name  = sel_pt_row.iloc[0].get("display_name", f"Adm {sel_hadm}") if not sel_pt_row.empty else f"Adm {sel_hadm}"
    section_label(f"Markers · {sel_pt_name}", f"{len(pt_mkrs)} found")

    if pt_mkrs.empty:
        st.markdown(
            '<div class="explorer-table-card">'
            '<div class="empty-state">'
            '<div class="empty-icon">∅</div>'
            '<div class="empty-title">No markers match your filters</div>'
            '<div class="empty-sub">Try clearing the search or category filter.</div>'
            '</div></div>',
            unsafe_allow_html=True,
        )
    else:
        rows = []
        for _, m in pt_mkrs.iterrows():
            s = str(m["status"])
            tone = "high" if s == "High" else "info" if s == "Low" else "normal"
            val_color = (
                "var(--risk-high)" if s == "High"
                else "var(--accent-blue)" if s == "Low"
                else "var(--text-1)"
            )
            spark = sparkline_svg(ts_by_key.get(str(m["marker_key"]), []),
                                  color="#f87171" if s == "High" else "#60a5fa" if s == "Low" else "#38bdf8")
            aki_cell = '<span class="aki-tag">AKI</span>' if m.get("is_aki_relevant") else '<span class="td-muted">—</span>'
            expl = str(m.get("explanation", ""))
            expl = expl if expl not in ("nan", "") else ""
            latest   = m["latest_value"]
            latest_fmt = f"{latest:.1f}"      if pd.notna(latest)         else "—"
            min_fmt    = f"{m['min_value']:.1f}"  if pd.notna(m["min_value"])  else "—"
            max_fmt    = f"{m['max_value']:.1f}"  if pd.notna(m["max_value"])  else "—"
            mean_fmt   = f"{m['mean_value']:.1f}" if pd.notna(m["mean_value"]) else "—"
            rows.append(
                f'<tr class="row-{tone}">'
                f'<td class="td-rail"><span class="row-rail rail-{tone}"></span></td>'
                f'<td class="cell-strong">{_html.escape(str(m["marker_name"]))}</td>'
                f'<td><span class="info-tag">{_html.escape(str(m["category"]))}</span></td>'
                f'<td class="cell-latest" style="color:{val_color};">{latest_fmt}</td>'
                f'<td class="td-mono">{min_fmt}</td>'
                f'<td class="td-mono">{max_fmt}</td>'
                f'<td class="td-mono">{mean_fmt}</td>'
                f'<td class="td-mono td-muted">{_html.escape(str(m["unit"]))}</td>'
                f'<td>{status_pill_html(s)}</td>'
                f'<td>{aki_cell}</td>'
                f'<td>{spark}</td>'
                f'<td class="cell-explain">{_html.escape(expl[:90])}{"…" if len(expl) > 90 else ""}</td>'
                f'</tr>'
            )
        rows_html = "\n".join(rows)
        st.markdown(
            '<div class="explorer-table-card">'
            '<table class="explorer-table">'
            '<thead><tr>'
            '<th class="th-rail"></th>'
            '<th>Marker</th><th>Category</th><th>Latest</th>'
            '<th>Min</th><th>Max</th><th>Mean</th><th>Unit</th>'
            '<th>Status</th><th>AKI</th><th>Trend</th><th>Explanation</th>'
            '</tr></thead>'
            f'<tbody>{rows_html}</tbody>'
            '</table></div>',
            unsafe_allow_html=True,
        )

    # ── Trend chart for selected marker
    available_keys = pt_ts["marker_key"].unique().tolist()
    chartable = pt_mkrs[pt_mkrs["marker_key"].isin(available_keys)]["marker_key"].tolist()

    if chartable:
        section_label("Trend Detail")
        key_to_name = {k: pt_mkrs[pt_mkrs["marker_key"] == k]["marker_name"].iloc[0] for k in chartable}
        sel_mk = st.selectbox(
            "Select marker to view trend", chartable,
            format_func=lambda k: key_to_name.get(k, k), key="me_mk",
        )
        mk_ts   = pt_ts[pt_ts["marker_key"] == sel_mk]
        mk_name = key_to_name.get(sel_mk, sel_mk)
        mk_unit = mk_ts["unit"].iloc[0] if not mk_ts.empty else ""
        _sel_row = pt_mkrs[pt_mkrs["marker_key"] == sel_mk]
        _sel_status = _sel_row.iloc[0].get("status", "Normal") if not _sel_row.empty else "Normal"
        _is_dark = get_theme() == "dark"
        _sel_accent = ("#f87171" if _is_dark else "#dc2626") if _sel_status == "High" else ("#60a5fa" if _is_dark else "#2563eb") if _sel_status == "Low" else ("#38bdf8" if _is_dark else "#0284c7")
        fig     = make_trend_chart(pt_ts, sel_mk, mk_name, mk_unit, accent=_sel_accent)
        if fig:
            st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})
        mk_row = pt_mkrs[pt_mkrs["marker_key"] == sel_mk]
        if not mk_row.empty:
            exp = str(mk_row.iloc[0].get("explanation", ""))
            if exp and exp not in ("nan", ""):
                st.markdown(
                    f'<div class="trend-explain">'
                    f'<div class="trend-explain-label">Clinical Context</div>'
                    f'<div class="trend-explain-text">{_html.escape(exp)}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
    else:
        st.info("No trend data available for the filtered markers.")


# ---------------------------------------------------------------------------
# Tab 4 — About / Disclaimer
# ---------------------------------------------------------------------------

def render_about(patients: pd.DataFrame) -> None:
    st.markdown(
        '<div class="about-hero">'
        '<div class="about-eyebrow">About</div>'
        '<div class="hero-wordmark">Str<span class="hero-accent">a</span>ta</div>'
        '<div class="about-lede">'
        'A clinical signal intelligence layer built to surface AKI early-warning patterns from '
        'structured EHR data. Strata weighs labs, vitals, diagnosis history, and trend dynamics '
        'into a single triage signal — designed for clinical review, not autonomous decisions.'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    section_label("Risk Score Architecture")
    arch_rows = [
        ("Creatinine elevation",        25, "Direct marker of reduced GFR — primary filtration signal"),
        ("Creatinine acute rise",        20, "Rapid rise pattern associated with AKI staging criteria"),
        ("BUN elevation",                15, "Nitrogen waste accumulation with impaired renal clearance"),
        ("Urine output (oliguria)",      15, "Direct AKI KDIGO diagnostic criterion"),
        ("MAP / BP signal",              12, "Sustained low MAP reduces renal perfusion pressure"),
        ("Potassium derangement",        10, "Impaired renal potassium excretion in AKI"),
        ("Bicarbonate / acidosis",        8, "Metabolic acidosis from reduced acid excretion"),
        ("Comorbidity context",          10, "CKD, diabetes, hypertension, sepsis increase baseline risk"),
        ("Nephrotoxic medication",        5, "Known nephrotoxic agents increase AKI likelihood"),
    ]
    arch_html = "".join(
        f'<tr><td class="cell-strong">{s}</td>'
        f'<td class="td-mono">{p}</td>'
        f'<td style="color:var(--text-3);">{w}</td></tr>'
        for s, p, w in arch_rows
    )
    st.markdown(
        '<div class="arch-table-card">'
        '<table class="arch-table">'
        '<thead><tr><th>Signal</th><th>Max Points</th><th>Why it matters</th></tr></thead>'
        f'<tbody>{arch_html}'
        '<tr class="row-total">'
        '<td class="cell-strong">Maximum risk score</td>'
        '<td class="td-mono"><b>100</b></td>'
        '<td style="color:var(--text-3);">Composite — capped at ceiling, not summed beyond</td>'
        '</tr>'
        '</tbody></table></div>',
        unsafe_allow_html=True,
    )

    section_label("Risk Tiers")
    st.markdown(
        '<div class="tier-grid">'
        # low
        '<div class="tier-card">'
        '<div class="tier-card-stripe" style="background:var(--risk-low);"></div>'
        '<div class="tier-card-head">'
        '<span class="risk-badge low"><span class="risk-dot" style="background:var(--risk-low);"></span>LOW</span>'
        '<span class="tier-range">0 – 29</span>'
        '</div>'
        '<div class="tier-card-title" style="color:var(--risk-low);">Low signal</div>'
        '<div class="tier-card-body">Markers largely within reference range. Routine clinical review at standard cadence.</div>'
        '</div>'
        # moderate
        '<div class="tier-card">'
        '<div class="tier-card-stripe" style="background:var(--risk-mod);"></div>'
        '<div class="tier-card-head">'
        '<span class="risk-badge moderate"><span class="risk-dot" style="background:var(--risk-mod);"></span>MODERATE</span>'
        '<span class="tier-range">30 – 59</span>'
        '</div>'
        '<div class="tier-card-title" style="color:var(--risk-mod);">Moderate signal</div>'
        '<div class="tier-card-body">Multiple abnormal markers or single high-weight signal. Consider closer monitoring.</div>'
        '</div>'
        # high
        '<div class="tier-card">'
        '<div class="tier-card-stripe" style="background:var(--risk-high);"></div>'
        '<div class="tier-card-head">'
        '<span class="risk-badge high"><span class="risk-dot" style="background:var(--risk-high);"></span>HIGH</span>'
        '<span class="tier-range">60 – 100</span>'
        '</div>'
        '<div class="tier-card-title" style="color:var(--risk-high);">High signal</div>'
        '<div class="tier-card-body">Strong AKI-relevant pattern across labs and perfusion. Warrants prompt clinical review.</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    section_label("Data Source")
    n = len(patients)
    st.markdown(
        '<div class="data-source-card"><div class="data-source">'
        '<div class="data-source-line"><span class="data-source-key">Source</span>'
        '<span class="data-source-val">MIMIC-IV Clinical Demo v2.2</span></div>'
        f'<div class="data-source-line"><span class="data-source-key">Version</span>'
        f'<span class="data-source-val">v2.2 · {n} de-identified admissions</span></div>'
        '<div class="data-source-line"><span class="data-source-key">License</span>'
        '<span class="data-source-val">PhysioNet Credentialed Health Data License 1.5.0</span></div>'
        '<div class="data-source-line"><span class="data-source-key">Citation</span>'
        '<span class="data-source-val">Johnson, A., et al. MIMIC-IV (PhysioNet)</span></div>'
        '<div class="data-source-line"><span class="data-source-key">De-identified</span>'
        '<span class="data-source-val">HIPAA Safe Harbor · No real patient identities present</span></div>'
        '</div></div>',
        unsafe_allow_html=True,
    )

    section_label("Important Disclaimer")
    st.markdown(
        '<div class="disclaimer-card">'
        '<div class="disclaimer-rail"></div>'
        '<div class="disclaimer-body">'
        '<div class="disclaimer-title">Full Disclaimer · Demo Only · Not for Clinical Use</div>'
        '<div class="disclaimer-text">'
        'Strata is a demonstration of statistical signal surfacing on structured EHR data. '
        'It is not a medical device, is not FDA-cleared, and does not provide diagnosis, '
        'treatment recommendations, or clinical decision support. All patient identifiers '
        'shown are de-identified demo data from MIMIC-IV Clinical Demo. '
        'The intelligence layer is intended to support, never replace, clinical judgment. '
        'All risk scores, flags, and signals require qualified clinical interpretation.'
        '</div>'
        '</div>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<div style="height:2rem;"></div>', unsafe_allow_html=True)
    st.caption("Strata MVP · Built with MIMIC-IV Clinical Demo · Not for clinical use")


# ---------------------------------------------------------------------------
# Sidebar
# ---------------------------------------------------------------------------

_NAV_PAGES: list[str] = ["Overview", "Patient Detail", "Marker Explorer", "About"]

# Lucide-style SVG icons (stroke-based, inherits currentColor)
_ICON_GRID = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<rect x="3" y="3" width="7" height="7" rx="1"/>'
    '<rect x="14" y="3" width="7" height="7" rx="1"/>'
    '<rect x="14" y="14" width="7" height="7" rx="1"/>'
    '<rect x="3" y="14" width="7" height="7" rx="1"/>'
    '</svg>'
)
_ICON_USER = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<circle cx="12" cy="7" r="4"/>'
    '<path d="M20 21v-2a4 4 0 0 0-4-4H8a4 4 0 0 0-4 4v2"/>'
    '</svg>'
)
_ICON_TREND = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<polyline points="22 7 13.5 15.5 8.5 10.5 2 17"/>'
    '<polyline points="16 7 22 7 22 13"/>'
    '</svg>'
)
_ICON_INFO = (
    '<svg xmlns="http://www.w3.org/2000/svg" width="20" height="20" viewBox="0 0 24 24"'
    ' fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round"'
    ' stroke-linejoin="round">'
    '<circle cx="12" cy="12" r="10"/>'
    '<path d="M12 16v-4"/><path d="M12 8h.01"/>'
    '</svg>'
)
_NAV_DEFS: list[tuple[str, str]] = [
    ("Overview",        _ICON_GRID),
    ("Patient Detail",  _ICON_USER),
    ("Marker Explorer", _ICON_TREND),
    ("About",           _ICON_INFO),
]

_NAV_ICONS: dict[str, str] = {
    "Overview":        ":material/grid_view:",
    "Patient Detail":  ":material/person:",
    "Marker Explorer": ":material/trending_up:",
    "About":           ":material/info:",
}


def _build_sidebar_nav_html(current_page: str, total_n: int) -> str:
    """Return a self-contained HTML string for the custom sidebar nav."""
    items: list[str] = []
    for i, (label, icon) in enumerate(_NAV_DEFS):
        active_cls = " active" if label == current_page else ""
        badge = (
            f'<span class="nav-badge">{total_n}</span>'
            if label == "Overview" else ""
        )
        items.append(
            f'<div class="nav-item{active_cls}" onclick="selectNav({i})">'
            f'<span class="nav-icon">{icon}</span>'
            f'<span class="nav-label">{label}</span>'
            f'{badge}'
            f'</div>'
        )
    items_html = "\n".join(items)

    # JS: uses React's native setter so Streamlit picks up the change
    js = """
function selectNav(idx) {
  try {
    var sidebar = window.parent.document.querySelector('[data-testid="stSidebar"]');
    var radioGroup = sidebar ? sidebar.querySelector('[data-testid="stRadio"]') : null;
    var radios = radioGroup ? radioGroup.querySelectorAll('input[type="radio"]') : [];
    var input = radios[idx];
    if (!input) return;
    var setter = Object.getOwnPropertyDescriptor(
      window.parent.HTMLInputElement.prototype, 'checked'
    ).set;
    setter.call(input, true);
    input.dispatchEvent(new Event('change', {bubbles: true}));
  } catch(e) { console.warn('nav click error', e); }
}
"""

    css = """
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body { background: transparent !important; overflow: hidden; }
body { font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
       -webkit-font-smoothing: antialiased; }

.nav-wrapper { display: flex; flex-direction: column; gap: 3px; }

.nav-item {
  display: flex; align-items: center; gap: 10px;
  padding: 9px 14px;
  border-radius: 14px;
  border: 1px solid transparent;
  cursor: pointer;
  color: #6b82a8;
  font-size: 13px; font-weight: 500; letter-spacing: 0.01em;
  transition: background 0.13s ease, color 0.13s ease, border-color 0.13s ease;
  user-select: none;
}
.nav-item:hover {
  color: #a8bdd6;
  background: rgba(56,189,248,0.05);
}
.nav-item.active {
  background: linear-gradient(90deg, rgba(34,211,238,0.13), rgba(56,189,248,0.05));
  border-color: rgba(34,211,238,0.28);
  color: #f0f8ff;
  font-weight: 600;
  box-shadow: 0 0 18px rgba(34,211,238,0.09);
}

.nav-icon {
  display: flex; align-items: center; flex-shrink: 0;
  color: #6b82a8;
  transition: color 0.13s ease;
}
.nav-item.active .nav-icon { color: #22d3ee; }
.nav-item:hover .nav-icon  { color: #a8bdd6; }

.nav-label { flex: 1; white-space: nowrap; }

.nav-badge {
  font-family: 'JetBrains Mono', 'Fira Mono', monospace;
  font-size: 11px; font-weight: 600; font-variant-numeric: tabular-nums;
  color: rgba(34,211,238,0.80);
  background: rgba(34,211,238,0.08);
  border: 1px solid rgba(34,211,238,0.22);
  padding: 1px 7px; border-radius: 999px;
  margin-left: auto;
}
"""

    return (
        "<!DOCTYPE html><html><head>"
        f"<style>{css}</style>"
        "</head><body>"
        f'<div class="nav-wrapper">{items_html}</div>'
        f"<script>{js}</script>"
        "</body></html>"
    )


def render_sidebar(patients: pd.DataFrame) -> None:
    """Sidebar with brand, vertical nav, cohort summary, demo badge, and user block."""
    total_n = len(patients)
    high_n  = int((patients["aki_risk_tier"] == "High").sum())
    mod_n   = int((patients["aki_risk_tier"] == "Moderate").sum())
    low_n   = int((patients["aki_risk_tier"] == "Low").sum())

    with st.sidebar:
        # Theme toggle is position:fixed — DOM order doesn't matter.
        render_theme_toggle()

        # ── Brand
        st.markdown(
            '<div class="strata-sidebar-brand">'
            '<div class="strata-sidebar-logo"><div class="strata-sidebar-logo-inner"></div></div>'
            '<div>'
            '<div class="strata-sidebar-wordmark">Str<span class="accent">a</span>ta</div>'
            '<div class="strata-sidebar-tagline">Clinical Signal Layer</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )

        # ── Workspace nav
        st.markdown('<div class="strata-section-label">Workspace</div>', unsafe_allow_html=True)
        current_page = st.session_state.get("active_page", "Overview")
        for label in _NAV_PAGES:
            safe = label.replace(" ", "_")
            suffix = "active" if label == current_page else "inactive"
            with st.container(key=f"nav_{safe}_{suffix}"):
                if st.button(
                    label,
                    key=f"nav_btn_{safe}",
                    icon=_NAV_ICONS.get(label, ""),
                    use_container_width=True,
                ):
                    st.session_state.active_page = label
                    st.rerun()

        # ── Cohort summary
        st.markdown(
            '<div class="strata-section-label" style="margin-top:8px;">Cohort</div>'
            f'<div class="strata-cohort-row">'
            f'<span class="strata-cohort-dot" style="background:#f87171;"></span>'
            f'<span>High</span><span class="strata-cohort-count">{high_n}</span>'
            f'</div>'
            f'<div class="strata-cohort-row">'
            f'<span class="strata-cohort-dot" style="background:#fbbf24;"></span>'
            f'<span>Moderate</span><span class="strata-cohort-count">{mod_n}</span>'
            f'</div>'
            f'<div class="strata-cohort-row">'
            f'<span class="strata-cohort-dot" style="background:#4ade80;"></span>'
            f'<span>Low</span><span class="strata-cohort-count">{low_n}</span>'
            f'</div>'
            f'<div class="strata-cohort-row" style="margin-top:6px;padding-top:6px;border-top:1px solid var(--border);">'
            f'<span style="color:var(--text-muted);font-size:11px;">Total</span>'
            f'<span class="strata-cohort-count">{total_n}</span>'
            f'</div>',
            unsafe_allow_html=True,
        )

        # ── Footer: demo badge + reviewer block
        st.markdown(
            '<div class="strata-sidebar-foot">'
            '<div class="strata-demo-pill">'
            '<span class="strata-demo-dot"></span><span>DEMO MODE</span>'
            '</div>'
            '<div class="strata-safety-line">'
            'Not diagnostic · For clinical review only.<br>MIMIC-IV Clinical Demo v2.2'
            '</div>'
            '<div class="sidebar-user-block">'
            '<div class="sidebar-user-avatar">CL</div>'
            '<div>'
            '<div class="sidebar-user-name">Clinical Lead</div>'
            '<div class="sidebar-user-role">Reviewer · Demo Access</div>'
            '</div>'
            '</div>'
            '</div>',
            unsafe_allow_html=True,
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    if "active_page" not in st.session_state:
        st.session_state.active_page = "Overview"

    with st.spinner("Loading Strata data…"):
        patients, markers, ts, aki = load_data()

    render_sidebar(patients)

    page = st.session_state.get("active_page", "Overview")
    if page == "Overview":
        render_overview(patients)
    elif page == "Patient Detail":
        render_patient_detail(patients, markers, ts, aki)
    elif page == "Marker Explorer":
        render_marker_explorer(patients, markers, ts)
    else:
        render_about(patients)


if __name__ == "__main__":
    main()
