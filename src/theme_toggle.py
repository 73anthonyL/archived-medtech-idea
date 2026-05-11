# theme-toggle.py — Streamlit snippet for Strata light/dark toggle
#
# Drop this into your main app file (or import it). It:
#   1. Persists theme choice in st.session_state
#   2. Renders a toggle widget
#   3. Injects CSS variable overrides for light mode (no JS needed — Streamlit strips scripts)
#   4. Returns the current theme string ('dark' | 'light') so Plotly charts can adapt
#
# Usage in your Streamlit app:
#
#   from theme_toggle import render_theme_toggle, inject_theme_attribute, get_theme
#   import streamlit as st
#
#   # Load base CSS and custom CSS first, then call inject_theme_attribute() last
#   # so the light-mode overrides win the cascade without needing !important.
#   st.markdown(base_css, unsafe_allow_html=True)
#   st.markdown(custom_css, unsafe_allow_html=True)
#   inject_theme_attribute()
#
#   # Render toggle (e.g. in sidebar) — it is position:fixed so placement doesn't matter
#   with st.sidebar:
#       render_theme_toggle()
#
#   # When building Plotly charts:
#   theme = get_theme()
#   fig.update_layout(
#       template="plotly_dark" if theme == "dark" else "plotly_white",
#       paper_bgcolor="rgba(0,0,0,0)",
#       plot_bgcolor="rgba(0,0,0,0)",
#       font_color="#f1f5f9" if theme == "dark" else "#0b1220",
#   )

import streamlit as st

# Full light-mode CSS injected when theme == "light".
# Streamlit strips <script> tags (DOMPurify), so we override CSS variables and structural
# rules via a <style> block instead of setting data-theme on the HTML element.
# Inject this AFTER base + custom CSS so it wins the cascade without !important.
_LIGHT_MODE_CSS = """
<style>
/* ── Light theme: CSS variable overrides ── */
:root {
  --bg: #f4f6fb;
  --bg-2: #eef2f8;
  --surface: #ffffff;
  --surface-2: #f5f7fb;
  --surface-3: #eef2f8;
  --border: #e2e8f0;
  --border-2: #cbd5e1;
  --text-1: #0b1220;
  --text-2: #1e293b;
  --text-3: #475569;
  --text-muted: #64748b;
  --text-faint: #94a3b8;
  --accent-blue: #0284c7;
  --accent-blue-2: #2563eb;
  --accent-blue-deep: #1d4ed8;
  --accent-cyan: #0891b2;
  --accent-info: #7c3aed;
  --risk-high: #dc2626;
  --risk-high-2: #b91c1c;
  --risk-mod: #d97706;
  --risk-mod-2: #b45309;
  --risk-low: #16a34a;
  --risk-low-2: #15803d;
  --gradient-accent: linear-gradient(90deg, #1d4ed8 0%, #2563eb 45%, #0891b2 100%);
}

/* ── Body ── */
body {
  background:
    radial-gradient(1200px 600px at 100% -10%, rgba(2,132,199,0.06), transparent 60%),
    radial-gradient(900px 500px at -10% 110%, rgba(124,58,237,0.05), transparent 60%),
    var(--bg);
  color: var(--text-2);
}

/* ── Sidebar ── */
.sidebar,
.strata-sidebar {
  background: linear-gradient(180deg, #ffffff 0%, #f7f9fd 100%);
  border-right: 1px solid var(--border);
}
.sidebar-logo { box-shadow: 0 4px 14px rgba(37,99,235,0.18); }
.sidebar-logo::after { background: #ffffff; }
.nav-item:hover { background: rgba(2,132,199,0.06); }
.nav-item.active {
  background: linear-gradient(90deg, rgba(2,132,199,0.10), rgba(2,132,199,0.02));
  border-color: rgba(2,132,199,0.30);
}
.sidebar-demo { background: rgba(2,132,199,0.06); border-color: rgba(2,132,199,0.25); }
.topnav { background: linear-gradient(180deg, #ffffff 0%, rgba(255,255,255,0.85) 100%); }

/* ── Cards / surfaces ── */
.card {
  background: var(--surface);
  border: 1px solid var(--border);
  box-shadow: 0 1px 0 rgba(15,23,42,0.02), 0 8px 24px -16px rgba(15,23,42,0.10);
}
.kpi-card {
  background: var(--surface);
  box-shadow: 0 1px 0 rgba(15,23,42,0.02), 0 8px 24px -16px rgba(15,23,42,0.10);
}

/* ── Hero ── */
.hero-card {
  background:
    radial-gradient(900px 400px at 100% -20%, rgba(2,132,199,0.10), transparent 60%),
    radial-gradient(700px 300px at -10% 120%, rgba(124,58,237,0.07), transparent 60%),
    var(--surface);
}
.hero-stat,
.hero-watchlist,
.mini-stat,
.trend-explain {
  background: var(--surface-2);
  border: 1px solid var(--border);
}
.demo-mode-pill {
  background: rgba(2,132,199,0.08); border-color: rgba(2,132,199,0.35); color: var(--accent-blue);
}

/* ── Inputs ── */
.input, .select {
  background-color: var(--surface);
  border: 1px solid var(--border);
  color: var(--text-1);
  box-shadow: inset 0 1px 0 rgba(15,23,42,0.02);
}
.input:focus, .select:focus {
  background-color: var(--surface);
  border-color: var(--accent-blue);
  box-shadow: 0 0 0 3px rgba(2,132,199,0.15);
}
.select {
  background-image: url("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='12' height='12' viewBox='0 0 12 12'><path d='M3 4.5L6 7.5L9 4.5' stroke='%23475569' stroke-width='1.5' fill='none' stroke-linecap='round'/></svg>");
}
.segseg { background: var(--surface-2); border-color: var(--border); }
.segseg-btn.active {
  background: #ffffff;
  box-shadow: 0 1px 0 rgba(15,23,42,0.04), 0 2px 8px rgba(15,23,42,0.06);
}

/* ── Streamlit native widget overrides ── */
div[data-baseweb="input"] > div {
  background-color: #ffffff !important;
  border-color: #e2e8f0 !important;
}
div[data-baseweb="input"] input {
  color: #0b1220 !important;
  background-color: transparent !important;
}
div[data-baseweb="input"] input::placeholder {
  color: #64748b !important;
  opacity: 1 !important;
}
div[data-baseweb="select"] > div {
  background-color: #ffffff !important;
  color: #1e293b !important;
}
div[data-testid="stMultiSelect"] > div {
  background-color: #ffffff !important;
}
div[data-testid="stMultiSelect"] span {
  color: #1e293b !important;
}

/* ── Badges & tags ── */
.status-pill.high  { background: rgba(220,38,38,0.08); color: var(--risk-high); border-color: rgba(220,38,38,0.30); }
.status-pill.low   { background: rgba(2,132,199,0.08); color: var(--accent-blue); border-color: rgba(2,132,199,0.30); }
.status-pill.normal { background: rgba(22,163,74,0.08); color: var(--risk-low); border-color: rgba(22,163,74,0.30); }
.aki-tag  { background: rgba(2,132,199,0.09); border-color: rgba(2,132,199,0.28); color: var(--accent-blue); }
.info-tag { background: rgba(124,58,237,0.07); border-color: rgba(124,58,237,0.28); color: var(--accent-info); }

/* ── Tables ── */
.table-card { background: var(--surface); }
.patient-table th, .explorer-table th, .arch-table th {
  background: #f8fafc; color: var(--text-muted); border-bottom: 1px solid var(--border);
}
.patient-table td, .explorer-table td, .arch-table td { border-bottom: 1px solid #eef2f8; }
.patient-table tbody tr:hover, .explorer-table tbody tr:hover { background: #f6f9ff; }
.row-high:hover     { background: rgba(220,38,38,0.05) !important; }
.row-moderate:hover { background: rgba(217,119,6,0.05) !important; }
.row-low:hover      { background: rgba(22,163,74,0.04) !important; }
.row-info:hover     { background: rgba(2,132,199,0.04) !important; }
.row-selected       { background: rgba(2,132,199,0.06) !important; }
.score-bar   { background: rgba(15,23,42,0.08); }
.rail-low    { background: linear-gradient(180deg, var(--risk-low), var(--risk-low-2)); }
.rail-normal { background: #cbd5e1; }

/* ── Skeleton ── */
.skeleton { background: linear-gradient(90deg, #eef2f8 0%, #f8fafc 50%, #eef2f8 100%); }

/* ── Patient detail / AKI cards ── */
.aki-high {
  background: radial-gradient(ellipse at top right, rgba(220,38,38,0.06), transparent 60%), var(--surface);
  border-color: rgba(220,38,38,0.20);
}
.aki-moderate {
  background: radial-gradient(ellipse at top right, rgba(217,119,6,0.06), transparent 60%), var(--surface);
  border-color: rgba(217,119,6,0.20);
}
.aki-low {
  background: radial-gradient(ellipse at top right, rgba(22,163,74,0.05), transparent 60%), var(--surface);
  border-color: rgba(22,163,74,0.20);
}
.aki-score-bar     { background: rgba(15,23,42,0.08); }
.aki-score-bar-tick { background: rgba(15,23,42,0.22); }

/* ── Marker cards ── */
.marker-card  { box-shadow: 0 1px 0 rgba(15,23,42,0.02), 0 6px 18px -12px rgba(15,23,42,0.10); }
.marker-explain { border-top: 1px dashed #e2e8f0; }
.ref-scale-track { background: rgba(15,23,42,0.06); }
.ref-scale-band  { background: rgba(22,163,74,0.16); border-color: rgba(22,163,74,0.35); }
.ref-scale-marker { box-shadow: 0 0 0 4px rgba(15,23,42,0.05); }

/* ── Chart tooltip ── */
.chart-tooltip {
  background: rgba(255,255,255,0.98); border: 1px solid var(--border-2);
  box-shadow: 0 8px 24px rgba(15,23,42,0.10);
}

/* ── Disclaimer ── */
.disclaimer-card { background: rgba(217,119,6,0.06); border-color: rgba(217,119,6,0.30); }

/* ── Misc ── */
.sidebar-user-info b { color: var(--text-1); }
.clock-num { color: var(--text-1); }
.clock-ss  { color: var(--text-faint); }
.row-total { background: rgba(2,132,199,0.04); }
</style>
"""


def get_theme() -> str:
    """Return current theme — 'light' (default) or 'dark'.

    Reads the toggle widget key directly so this returns the correct value even
    when called before render_theme_toggle() in the same script run (e.g. during
    CSS injection at the top of app.py).  The widget key is populated by
    Streamlit from the browser state before any Python code runs.
    """
    if "strata_theme_toggle" in st.session_state:
        # Toggle ON = dark mode
        return "dark" if st.session_state["strata_theme_toggle"] else "light"
    return st.session_state.get("strata_theme", "light")


def set_theme(theme: str) -> None:
    """Persist theme choice in session state."""
    assert theme in ("dark", "light")
    st.session_state.strata_theme = theme


def render_theme_toggle(label: str = "Dark mode") -> str:
    """Render a Streamlit toggle widget. Returns the current theme."""
    current = get_theme()
    is_dark = st.toggle(label, value=(current == "dark"), key="strata_theme_toggle")
    theme = "dark" if is_dark else "light"
    set_theme(theme)
    return theme


def inject_theme_attribute() -> None:
    """Inject light-mode CSS overrides when theme is 'light'.

    Call this AFTER all base and custom CSS has been injected so the
    light-mode rules win the cascade without needing !important on every rule.
    Does nothing in dark mode (dark is the default defined in theme.css).
    """
    if get_theme() == "light":
        st.markdown(_LIGHT_MODE_CSS, unsafe_allow_html=True)


# ----- Plotly helper -----
def plotly_theme_layout() -> dict:
    """Return layout dict to merge into Plotly figures so they match the active theme."""
    theme = get_theme()
    if theme == "light":
        return dict(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font_color="#0b1220",
            font_family="Inter, sans-serif",
            xaxis=dict(gridcolor="rgba(15,23,42,0.06)", linecolor="rgba(15,23,42,0.15)"),
            yaxis=dict(gridcolor="rgba(15,23,42,0.06)", linecolor="rgba(15,23,42,0.15)"),
            colorway=["#0284c7", "#7c3aed", "#dc2626", "#d97706", "#16a34a"],
        )
    return dict(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font_color="#f1f5f9",
        font_family="Inter, sans-serif",
        xaxis=dict(gridcolor="rgba(148,163,184,0.08)", linecolor="rgba(148,163,184,0.20)"),
        yaxis=dict(gridcolor="rgba(148,163,184,0.08)", linecolor="rgba(148,163,184,0.20)"),
        colorway=["#38bdf8", "#a78bfa", "#f87171", "#fbbf24", "#4ade80"],
    )


def reference_band_color() -> str:
    """Theme-aware fill color for the 'normal range' shaded band on trend charts."""
    return "rgba(22,163,74,0.12)" if get_theme() == "light" else "rgba(74,222,128,0.08)"
