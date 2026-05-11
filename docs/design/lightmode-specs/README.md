# Strata — Light Mode Integration

This package contains everything needed to add a light/dark theme toggle to the Strata Streamlit app.

## How it works

Theme is controlled by a single attribute on the `<html>` root: `data-theme="dark"` (default) or `data-theme="light"`. All colors flow through CSS custom properties defined in `theme.css`, so switching the attribute swaps the entire palette instantly — no per-component code changes.

## Files

- `theme.css` — All theme tokens (dark + light) plus the light-mode overrides that need to address element-specific styling (cards, badges, charts, inputs, etc.). Drop-in replacement / extension of your existing CSS.
- `theme-toggle.py` — Streamlit snippet: a toggle widget + the `st.markdown` injection that sets `data-theme` on the root and persists user choice in `st.session_state`.

## Integration (Streamlit)

1. **Add `theme.css` contents** to your existing CSS-injection string (or `st.markdown(f"<style>{open('theme.css').read()}</style>", unsafe_allow_html=True)`).
2. **Add the toggle** somewhere in your sidebar or hero:
   ```python
   theme = st.toggle("Light mode", value=st.session_state.get("theme") == "light")
   st.session_state.theme = "light" if theme else "dark"
   ```
3. **Inject the data-theme attribute** at the top of every page render:
   ```python
   st.markdown(
       f"<script>document.documentElement.setAttribute('data-theme', '{st.session_state.get('theme', 'dark')}');</script>",
       unsafe_allow_html=True,
   )
   ```
   See `theme-toggle.py` for the full pattern.

## Color tokens

All semantic colors are exposed as CSS variables:

| Token | Dark | Light |
|---|---|---|
| `--bg` | `#060d1b` | `#f4f6fb` |
| `--surface` | `#0d1626` | `#ffffff` |
| `--border` | `#1a2e4a` | `#e2e8f0` |
| `--text-1` | `#f1f5f9` | `#0b1220` |
| `--text-3` | `#94a3b8` | `#475569` |
| `--accent-blue` | `#38bdf8` | `#0284c7` |
| `--risk-high` | `#f87171` | `#dc2626` |
| `--risk-mod` | `#fbbf24` | `#d97706` |
| `--risk-low` | `#4ade80` | `#16a34a` |
| `--accent-info` | `#a78bfa` | `#7c3aed` |

Risk colors are slightly deeper in light mode for WCAG contrast. The gradient accent bar (`--gradient-accent`) is tuned per theme.

## Notes for Plotly charts

Streamlit Plotly charts won't pick up CSS variables. In your chart-building Python code, read the current theme and switch the Plotly template:

```python
theme = st.session_state.get("theme", "dark")
fig.update_layout(
    template="plotly_dark" if theme == "dark" else "plotly_white",
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font_color="#f1f5f9" if theme == "dark" else "#0b1220",
)
# Reference range band fill
band_color = "rgba(74,222,128,0.10)" if theme == "dark" else "rgba(22,163,74,0.12)"
```

## Gotchas

- When overriding `.input` / `.select` styles in light mode, use **`background-color`** not the `background` shorthand — the shorthand resets `background-repeat: no-repeat` from the base rule and causes the chevron arrow to tile horizontally.
- The radial-gradient washes on the hero and risk cards reference theme-specific rgba values and are overridden inside the `[data-theme="light"]` block. Keep them paired.
