# theme-toggle.py — Streamlit snippet for Strata light/dark toggle
#
# Drop this into your main app file (or import it). It:
#   1. Persists theme choice in st.session_state
#   2. Renders a toggle widget
#   3. Injects the data-theme attribute onto <html> so theme.css can switch palettes
#   4. Returns the current theme string ('dark' | 'light') so Plotly charts can adapt
#
# Usage in your Streamlit app:
#
#   from theme_toggle import render_theme_toggle, get_theme
#   import streamlit as st
#
#   # Load CSS once near the top
#   with open("theme.css") as f:
#       st.markdown(f"<style>{f.read()}</style>", unsafe_allow_html=True)
#
#   # Render toggle (e.g. in sidebar)
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


def get_theme() -> str:
    """Return current theme — 'dark' (default) or 'light'."""
    return st.session_state.get("strata_theme", "dark")


def set_theme(theme: str) -> None:
    """Set theme and inject the data-theme attribute on <html>."""
    assert theme in ("dark", "light")
    st.session_state.strata_theme = theme
    # Inject script that sets the attribute. Re-runs on every Streamlit render.
    st.markdown(
        f"""
        <script>
          (function() {{
            document.documentElement.setAttribute('data-theme', '{theme}');
          }})();
        </script>
        """,
        unsafe_allow_html=True,
    )


def render_theme_toggle(label: str = "Light mode") -> str:
    """Render a Streamlit toggle widget. Returns the current theme."""
    current = get_theme()
    is_light = st.toggle(label, value=(current == "light"), key="strata_theme_toggle")
    theme = "light" if is_light else "dark"
    set_theme(theme)
    return theme


def inject_theme_attribute() -> None:
    """Call near the top of each page render to ensure data-theme is set
    (Streamlit re-renders can lose DOM state otherwise)."""
    set_theme(get_theme())


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
