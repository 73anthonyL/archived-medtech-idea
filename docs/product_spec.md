# Strata MVP Product Spec

## Purpose

Build a visually polished clinical marker dashboard with a focused AKI early-warning module.

Strata uses MIMIC-IV Clinical Demo data. This is a demo/prototype, not a diagnostic medical device.

## Core Product

Strata has two layers:

1. Comprehensive clinical marker dashboard
2. AKI risk / kidney deterioration early-warning module

## User

Prospective client, physician, clinical operations leader, healthcare innovation stakeholder, or product evaluator.

## Dataset

MIMIC-IV Clinical Demo v2.2.

Use structured EHR data:
- patients
- admissions
- labevents
- d_labitems
- diagnoses_icd
- d_icd_diagnoses
- prescriptions
- icustays
- chartevents
- d_items
- outputevents if useful

## Main Views

### 1. Patient Overview

The overview page should show:
- Patient/admission table
- Overall status
- AKI risk score
- AKI risk tier
- Number of abnormal markers
- Top concern
- Filters for risk level, ICU stay, abnormal marker category

### 2. Patient Detail

The patient detail page should show:
- Patient summary card
- AKI risk card
- Top contributing reasons
- Abnormal lab/marker cards
- Trend charts for creatinine, BUN, potassium, bicarbonate, WBC, hemoglobin, heart rate, MAP/BP
- Explanation panel

### 3. Marker Explorer

The marker explorer should show:
- Search all markers
- Filter abnormal only
- Latest/min/max/mean values
- Normal ranges
- Plain-English explanation blurbs
- Trend chart for selected marker

## AKI Module

Risk score should be 0 to 100 based on explainable rules:
- Creatinine high or rising
- BUN high
- Potassium abnormal
- Bicarbonate low
- Low MAP/hypotension
- Low urine output if available
- CKD/diabetes/hypertension diagnosis context
- Nephrotoxic or kidney-relevant medications

Risk tiers:
- 0-29 Low
- 30-59 Moderate
- 60-100 High

## UI Requirements

The app should feel premium and demo-friendly:
- Clean modern layout
- Cards
- Color-coded risk badges
- Trend charts
- Human-readable explanations
- Clear disclaimer: demo only, not for clinical use

## Technical Requirements

Use:
- Python
- pandas
- Streamlit
- Plotly
- scikit-learn optional

Generate outputs:
- outputs/patient_marker_summary.csv
- outputs/aki_risk_scores.csv
- outputs/patient_timeseries.csv
- outputs/dashboard_patients.csv

## Medical Safety

Do not claim diagnosis.

Use wording:
- “risk signal”
- “possible AKI risk”
- “kidney deterioration signal”
- “requires clinical review”
- “clinical marker intelligence”

Do not use wording:
- “diagnosed”
- “confirmed AKI”
- “treatment recommendation”
- “doctor should do X”

## Product Positioning

Strata is a clinical signal intelligence layer. It helps surface meaningful patterns across labs, vitals, medications, and diagnosis context.

The MVP should demonstrate how a clinician could quickly see:
- Which patients have concerning signals
- Which markers are abnormal
- Why those markers matter
- Whether AKI-related risk signals are present
