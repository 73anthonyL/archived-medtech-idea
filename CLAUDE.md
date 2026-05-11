# Claude Code Instructions for Strata MVP

You are helping build Strata, a Streamlit MVP demo.

Read docs/product_spec.md before making architectural decisions.

## Project Goal

Build a polished clinical marker dashboard using MIMIC-IV Clinical Demo data, with a specific AKI early-warning module.

## Product Name

The product is called Strata.

Use "Strata" in the UI, README, docs, comments where appropriate, and user-facing copy.

## Must-Haves

1. Load MIMIC-IV demo .csv.gz files from data/mimic-iv-demo.
2. Build one row per hospital admission.
3. Extract clinical marker summaries from labs/vitals.
4. Compute abnormal marker statuses using simple transparent rules.
5. Compute AKI risk score using explainable rules.
6. Generate output CSV files.
7. Build a polished Streamlit dashboard.
8. Include explanation blurbs for abnormal markers.
9. Include clear “demo only, not for clinical use” disclaimer.
10. Keep code modular and readable.

## Do Not

- Do not call the product KidneyWatch.
- Do not claim to diagnose AKI.
- Do not hardcode one fake patient.
- Do not build a huge complex ML model before the working dashboard exists.
- Do not require external APIs.
- Do not invent fake clinical data.
- Do not commit data, outputs, models, or PHI-like data.
- Do not break the app into too many unnecessary abstractions.

## Preferred Files

src/load_data.py
src/build_cohort.py
src/marker_config.py
src/build_markers.py
src/aki_scoring.py
src/build_dashboard_data.py
src/app.py

## Style

Use clean pandas code.
Use Plotly for charts.
Use Streamlit for dashboard.
Use type hints where helpful.
Add comments for clinical logic.

## UI Tone

Strata should feel:
- premium
- modern
- clinical
- clear
- visually engaging
- demo-ready

Use safe wording:
- risk signal
- possible concern
- clinical review
- marker intelligence
- early-warning signal

Avoid unsafe wording:
- diagnosis
- confirmed disease
- treatment recommendation
