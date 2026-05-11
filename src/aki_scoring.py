"""
Strata — AKI risk scoring.

Computes a transparent, rule-based AKI risk signal per hospital admission.
All rules are explicit and independently traceable to a specific lab value,
vital sign, clinical diagnosis, or medication.

This module does NOT diagnose AKI.  All outputs are risk signals intended
for clinical review only.  See outputs/aki_risk_scores.csv for results.

Score architecture (max 100):
  Creatinine signal  — max 35  (level up to 30 + rise up to 20, capped)
  BUN signal         — max 15
  Potassium signal   — max 10
  Bicarbonate signal — max  8
  Hemodynamic signal — max 12
  Urine output signal— max 15
  Diagnosis context  — max 10  (CKD 5, diabetes 3, HTN 3, sepsis 5)
  Medication context — max  5

Risk tiers:  0–29 Low  |  30–59 Moderate  |  60–100 High
"""

from pathlib import Path

import numpy as np
import pandas as pd

from src.load_data import load_diagnoses_icd, load_outputevents, load_prescriptions
from src.marker_config import (
    CKD_ICD_PREFIXES,
    DIABETES_ICD_PREFIXES,
    HYPERTENSION_ICD_PREFIXES,
    MAP_HYPOPERFUSION_THRESHOLD,
    NEPHROTOXIC_DRUGS,
    SEPSIS_ICD_PREFIXES,
    URINE_OUTPUT_OLIGURIA_ML_24H,
)

_OUTPUTS = Path(__file__).parent.parent / "outputs"


# ---------------------------------------------------------------------------
# Creatinine level thresholds (mg/dL)
# ---------------------------------------------------------------------------
_CREAT_MILD   = 1.2   # below → 0 pts
_CREAT_MOD    = 1.5   # 1.2–1.49 → 8 pts
_CREAT_HIGH   = 2.0   # 1.5–1.99 → 15 pts
_CREAT_SEVERE = 3.0   # 2.0–2.99 → 25 pts; ≥3.0 → 30 pts

# Creatinine absolute rise thresholds (mg/dL, min→latest)
_CREAT_RISE_MILD = 0.3   # below → 0 pts
_CREAT_RISE_MOD  = 0.5   # 0.3–0.49 → 8 pts
_CREAT_RISE_HIGH = 1.0   # 0.5–0.99 → 15 pts; ≥1.0 → 20 pts

# BUN level thresholds (mg/dL)
_BUN_MILD   = 20    # ≤20 → 0 pts
_BUN_MOD    = 30    # 21–30 → 5 pts
_BUN_HIGH   = 50    # 31–50 → 10 pts; >50 → 15 pts

# Potassium severity thresholds (mmol/L)
_K_NORMAL_HIGH = 5.2   # >5.2 starts mild concern
_K_MILD_HIGH   = 5.7   # >5.7 → severe (10 pts); 5.3–5.7 → mild (5 pts)
_K_NORMAL_LOW  = 3.5   # <3.5 starts mild concern
_K_MILD_LOW    = 3.0   # <3.0 → severe (10 pts); 3.0–3.4 → mild (5 pts)

# Bicarbonate level thresholds (mEq/L)
_BICARB_NORMAL = 22   # ≥22 → 0 pts
_BICARB_LOW    = 18   # 18–21 → 4 pts; <18 → 8 pts

# Hemodynamic severity threshold — MAP below this is "severe" (vs "mild" at < 65)
_MAP_SEVERE_THRESHOLD = 55.0   # mmHg

# Urine output strong-oliguria threshold (mL/day); mild uses URINE_OUTPUT_OLIGURIA_ML_24H (400)
_UO_STRONG_THRESHOLD = 200.0   # mL/day


# ---------------------------------------------------------------------------
# Per-domain score caps
# ---------------------------------------------------------------------------
_CAP_CREATININE  = 35
_CAP_BUN         = 15
_CAP_POTASSIUM   = 10
_CAP_BICARBONATE = 8
_CAP_HEMODYNAMIC = 12
_CAP_URINE_OUT   = 15
_CAP_DIAGNOSIS   = 10
_CAP_MEDICATION  = 5

# Diagnosis context individual point weights
_DX_CKD    = 5
_DX_DIAB   = 3
_DX_HTN    = 3
_DX_SEPSIS = 5


# ---------------------------------------------------------------------------
# Urine-specific itemids in MIMIC-IV outputevents
# ---------------------------------------------------------------------------
_URINE_ITEMIDS: frozenset[int] = frozenset({
    226559,  # Foley
    226560,  # Void
    226561,  # Condom Cath
    226567,  # Straight Cath
    226627,  # OR Urine
})

_RELEVANT_MARKER_KEYS = [
    "creatinine", "bun", "potassium", "bicarbonate",
    "map_noninvasive", "map_arterial", "sbp",
]

_OUTPUT_COLUMNS = [
    "subject_id", "hadm_id",
    "aki_risk_score", "aki_risk_tier", "top_reasons",
    "creatinine_signal", "bun_signal", "potassium_signal",
    "bicarbonate_signal", "hemodynamic_signal", "urine_output_signal",
    "diagnosis_context_signal", "medication_signal",
]

_SIGNAL_TO_POINTS = {
    "creatinine_signal":        "creatinine_points",
    "bun_signal":               "bun_points",
    "potassium_signal":         "potassium_points",
    "bicarbonate_signal":       "bicarbonate_points",
    "hemodynamic_signal":       "hemodynamic_points",
    "urine_output_signal":      "urine_output_points",
    "diagnosis_context_signal": "diagnosis_context_points",
    "medication_signal":        "medication_points",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _score_to_tier(score: int) -> str:
    """Map a numeric score to a risk tier label."""
    if score >= 60:
        return "High"
    if score >= 30:
        return "Moderate"
    return "Low"


def _col(df: pd.DataFrame, name: str, default) -> pd.Series:
    """Return column from df, or a constant-filled Series if column is absent."""
    return df[name] if name in df.columns else pd.Series(default, index=df.index)


def _pivot_markers(summary: pd.DataFrame) -> pd.DataFrame:
    """
    Pivot patient_marker_summary to a wide row-per-hadm_id format.

    Produces columns like creatinine_latest_value, creatinine_min_value,
    creatinine_status for each marker in _RELEVANT_MARKER_KEYS.
    """
    filtered = summary[summary["marker_key"].isin(_RELEVANT_MARKER_KEYS)].copy()
    filtered = filtered.dropna(subset=["hadm_id"]).copy()
    filtered["hadm_id"] = filtered["hadm_id"].astype(int)
    filtered = filtered.drop_duplicates(subset=["hadm_id", "marker_key"])

    if filtered.empty:
        return pd.DataFrame(columns=["hadm_id"])

    wide = filtered.pivot(
        index="hadm_id",
        columns="marker_key",
        values=["latest_value", "min_value", "status"],
    )
    # Flatten MultiIndex: (stat, marker_key) → marker_key_stat
    wide.columns = [f"{mk}_{stat}" for stat, mk in wide.columns]
    return wide.reset_index()


def _icd_matched_hadm_ids(
    dx: pd.DataFrame, prefixes: list[str]
) -> set[int]:
    """Return the set of hadm_ids with at least one ICD code matching a prefix list."""
    pattern = "|".join(f"^{p}" for p in prefixes)
    matched = dx[dx["icd_code"].str.match(pattern, na=False)]
    return set(matched["hadm_id"].dropna().astype(int))


# ---------------------------------------------------------------------------
# Per-signal scorers — each mutates df in-place and returns it
# ---------------------------------------------------------------------------

def _apply_creatinine_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Severity-based creatinine scoring.

    Absolute level (max 30) plus absolute rise from min (max 20), capped at 35.
    Rise uses mg/dL change rather than ratio to better reflect acute-on-chronic
    patterns without over-penalising patients who start high.
    """
    latest = _col(df, "creatinine_latest_value", float("nan"))
    min_v  = _col(df, "creatinine_min_value",    float("nan"))

    level_pts = pd.Series(
        np.select(
            [latest.isna(), latest < _CREAT_MILD, latest < _CREAT_MOD,
             latest < _CREAT_HIGH, latest < _CREAT_SEVERE],
            [0, 0, 8, 15, 25],
            default=30,
        ),
        index=df.index,
    )

    rise = latest - min_v  # NaN if either input is missing
    rise_pts = pd.Series(
        np.select(
            [rise.isna(), rise < _CREAT_RISE_MILD, rise < _CREAT_RISE_MOD,
             rise < _CREAT_RISE_HIGH],
            [0, 0, 8, 15],
            default=20,
        ),
        index=df.index,
    )

    df["creatinine_points"] = (level_pts + rise_pts).clip(upper=_CAP_CREATININE).astype(int)

    def _fmt(val, mn, pts):
        if pts == 0 or pd.isna(val):
            return ""
        rrise = (val - mn) if pd.notna(mn) else None

        # Level severity label
        if val >= _CREAT_SEVERE:
            level_lbl = f"Creatinine {val:.1f} mg/dL: strong kidney function risk signal"
        elif val >= _CREAT_HIGH:
            level_lbl = f"Creatinine {val:.1f} mg/dL: elevated creatinine — kidney function risk signal"
        elif val >= _CREAT_MOD:
            level_lbl = f"Creatinine {val:.1f} mg/dL: moderately elevated — requires clinical context"
        else:
            level_lbl = None  # value within normal range; only rise is driving score

        if rrise is not None and rrise >= _CREAT_RISE_HIGH:
            rise_lbl = f"acute rise +{rrise:.1f} mg/dL"
        elif rrise is not None and rrise >= _CREAT_RISE_MOD:
            rise_lbl = f"rise +{rrise:.1f} mg/dL"
        elif rrise is not None and rrise >= _CREAT_RISE_MILD:
            rise_lbl = f"mild rise +{rrise:.1f} mg/dL"
        else:
            rise_lbl = None

        if level_lbl and rise_lbl:
            return f"Creatinine {val:.1f} mg/dL (+{rrise:.1f} rise): strong kidney function risk signal"
        if level_lbl:
            return level_lbl
        if rise_lbl:
            return f"Creatinine {rise_lbl}: acute rise — possible AKI risk signal"
        return ""

    df["creatinine_signal"] = [
        _fmt(v, m, p) for v, m, p in zip(latest, min_v, df["creatinine_points"])
    ]
    return df


def _apply_bun_signal(df: pd.DataFrame) -> pd.DataFrame:
    """BUN severity scoring: mild (5), moderate (10), severe (15)."""
    latest = _col(df, "bun_latest_value", float("nan"))

    bun_pts = pd.Series(
        np.select(
            [latest.isna(), latest <= _BUN_MILD, latest <= _BUN_MOD, latest <= _BUN_HIGH],
            [0, 0, 5, 10],
            default=15,
        ),
        index=df.index,
    )
    df["bun_points"] = bun_pts.astype(int)

    def _fmt(val, pts):
        if pts == 0 or pd.isna(val):
            return ""
        if val > _BUN_HIGH:
            return f"BUN {val:.0f} mg/dL: significantly elevated nitrogen waste — strong renal clearance risk signal"
        if val > _BUN_MOD:
            return f"BUN {val:.0f} mg/dL: moderately elevated nitrogen waste marker — requires clinical context"
        return f"BUN {val:.0f} mg/dL: mildly elevated nitrogen waste marker — requires clinical context"

    df["bun_signal"] = [_fmt(v, p) for v, p in zip(latest, df["bun_points"])]
    return df


def _apply_potassium_signal(df: pd.DataFrame) -> pd.DataFrame:
    """Potassium severity scoring: mild abnormality (5), severe (10)."""
    latest = _col(df, "potassium_latest_value", float("nan"))

    mild_high   = (latest > _K_NORMAL_HIGH) & (latest <= _K_MILD_HIGH)
    severe_high = latest > _K_MILD_HIGH
    mild_low    = (latest < _K_NORMAL_LOW) & (latest >= _K_MILD_LOW)
    severe_low  = latest < _K_MILD_LOW

    df["potassium_points"] = pd.Series(
        np.where(
            latest.isna(), 0,
            np.where(severe_high | severe_low, 10,
            np.where(mild_high | mild_low, 5, 0)),
        ),
        index=df.index,
    ).astype(int)

    def _fmt(val, pts):
        if pts == 0 or pd.isna(val):
            return ""
        if val > _K_MILD_HIGH:
            return f"Potassium {val:.1f} mmol/L: severe hyperkalemia signal — strong renal risk signal"
        if val > _K_NORMAL_HIGH:
            return f"Potassium {val:.1f} mmol/L: mild hyperkalemia signal — requires clinical context"
        if val < _K_MILD_LOW:
            return f"Potassium {val:.1f} mmol/L: severe hypokalemia signal — possible concern"
        return f"Potassium {val:.1f} mmol/L: mild hypokalemia signal — requires clinical context"

    df["potassium_signal"] = [_fmt(v, p) for v, p in zip(latest, df["potassium_points"])]
    return df


def _apply_bicarbonate_signal(df: pd.DataFrame) -> pd.DataFrame:
    """Bicarbonate severity scoring: mildly low (4 pts), severely low (8 pts)."""
    latest = _col(df, "bicarbonate_latest_value", float("nan"))

    bicarb_pts = pd.Series(
        np.select(
            [latest.isna(), latest >= _BICARB_NORMAL, latest >= _BICARB_LOW],
            [0, 0, 4],
            default=8,
        ),
        index=df.index,
    )
    df["bicarbonate_points"] = bicarb_pts.astype(int)

    def _fmt(val, pts):
        if pts == 0 or pd.isna(val):
            return ""
        if val < _BICARB_LOW:
            return f"Bicarbonate {val:.0f} mEq/L: significantly low — possible metabolic acidosis risk signal"
        return f"Bicarbonate {val:.0f} mEq/L: mildly low — may suggest early acid-base stress"

    df["bicarbonate_signal"] = [_fmt(v, p) for v, p in zip(latest, df["bicarbonate_points"])]
    return df


def _apply_hemodynamic_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Hemodynamic severity scoring.

    Mild low MAP/BP signal: +6.  Repeated or severe signal: +12.

    Severe is defined as MAP min < 55 mmHg (critical hypotension) or both MAP
    and SBP flagging low simultaneously (multi-source pattern).
    Mild is a single-source MAP 55–65 mmHg or SBP-low without MAP signal.
    """
    map_ni_min = _col(df, "map_noninvasive_min_value", float("nan"))
    map_a_min  = _col(df, "map_arterial_min_value",    float("nan"))
    sbp_status = _col(df, "sbp_status",                None)

    map_severe = (
        (map_ni_min.notna() & (map_ni_min < _MAP_SEVERE_THRESHOLD)) |
        (map_a_min.notna()  & (map_a_min  < _MAP_SEVERE_THRESHOLD))
    )
    map_mild_only = (
        (map_ni_min.notna() & (map_ni_min >= _MAP_SEVERE_THRESHOLD) & (map_ni_min < MAP_HYPOPERFUSION_THRESHOLD)) |
        (map_a_min.notna()  & (map_a_min  >= _MAP_SEVERE_THRESHOLD) & (map_a_min  < MAP_HYPOPERFUSION_THRESHOLD))
    )
    map_any_low = map_severe | map_mild_only
    sbp_low     = (sbp_status == "Low").fillna(False)

    # Severe: MAP critically low, or both MAP and SBP signalling together
    severe_flag = map_severe | (map_any_low & sbp_low)
    mild_flag   = ~severe_flag & (map_mild_only | sbp_low)

    df["hemodynamic_points"] = pd.Series(
        np.where(severe_flag, _CAP_HEMODYNAMIC, np.where(mild_flag, 6, 0)),
        index=df.index,
    ).astype(int)

    def _fmt(ni_min, a_min, pts):
        if pts == 0:
            return ""
        maps = [v for v in [ni_min, a_min] if pd.notna(v)]
        map_str = f" (min MAP {min(maps):.0f} mmHg)" if maps else ""
        if pts == _CAP_HEMODYNAMIC:
            return f"Low MAP/BP signal{map_str}: repeated or severe renal perfusion risk signal"
        return f"Low MAP/BP signal{map_str}: possible renal perfusion stress — requires clinical context"

    df["hemodynamic_signal"] = [
        _fmt(ni, a, p)
        for ni, a, p in zip(map_ni_min, map_a_min, df["hemodynamic_points"])
    ]
    return df


def _apply_urine_output_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Urine output severity scoring.

    < 200 mL/day → strong oliguria signal (15 pts).
    200–400 mL/day → possible low output signal (8 pts).

    Admissions with LOS < 0.5 days are excluded to avoid false flags on
    very short stays where urine data coverage is incomplete.
    """
    try:
        oe = load_outputevents()
    except Exception:
        df["urine_output_points"] = 0
        df["urine_output_signal"] = ""
        return df

    hadm_ids = set(df["hadm_id"].dropna().astype(int))
    urine = (
        oe[oe["itemid"].isin(_URINE_ITEMIDS) & oe["hadm_id"].isin(hadm_ids)]
        .dropna(subset=["value"])
        .copy()
    )

    if urine.empty:
        df["urine_output_points"] = 0
        df["urine_output_signal"] = ""
        return df

    total_ml = urine.groupby("hadm_id")["value"].sum()
    los      = df.set_index("hadm_id")["length_of_stay_days"]

    uo = total_ml.to_frame("total_ml").join(los, how="left")
    uo = uo[uo["length_of_stay_days"].fillna(0) >= 0.5].copy()
    uo["daily_ml"] = uo["total_ml"] / uo["length_of_stay_days"]

    strong_hadm   = set(uo[uo["daily_ml"] < _UO_STRONG_THRESHOLD].index)
    possible_hadm = set(
        uo[(uo["daily_ml"] >= _UO_STRONG_THRESHOLD) &
           (uo["daily_ml"] < URINE_OUTPUT_OLIGURIA_ML_24H)].index
    )
    daily_ml_map = uo["daily_ml"].to_dict()

    def _pts(hadm_id: int) -> int:
        if hadm_id in strong_hadm:
            return _CAP_URINE_OUT
        if hadm_id in possible_hadm:
            return 8
        return 0

    def _sig(hadm_id: int) -> str:
        daily = daily_ml_map.get(hadm_id)
        ml_str = f" (~{daily:.0f} mL/day)" if daily is not None else ""
        if hadm_id in strong_hadm:
            return f"Low urine output{ml_str}: strong oliguria risk signal"
        if hadm_id in possible_hadm:
            return f"Low urine output{ml_str}: possible low output signal — requires clinical context"
        return ""

    df["urine_output_points"] = df["hadm_id"].apply(_pts)
    df["urine_output_signal"] = df["hadm_id"].apply(_sig)
    return df


def _apply_diagnosis_context_signal(df: pd.DataFrame) -> pd.DataFrame:
    """
    Diagnosis context scoring, capped at 10.

    CKD: +5, diabetes: +3, hypertension: +3, sepsis/infection context: +5.
    Context is intentionally lower-weight than lab/vital signals — diagnosis
    history shifts baseline risk but is not a direct acute marker.
    """
    try:
        diagnoses = load_diagnoses_icd()
    except Exception:
        df["diagnosis_context_points"] = 0
        df["diagnosis_context_signal"] = ""
        return df

    hadm_ids = set(df["hadm_id"].dropna().astype(int))
    dx = diagnoses[diagnoses["hadm_id"].isin(hadm_ids)].copy()
    dx["icd_code"] = dx["icd_code"].astype(str).str.strip().str.upper()

    ckd_hadm    = _icd_matched_hadm_ids(dx, CKD_ICD_PREFIXES)
    diab_hadm   = _icd_matched_hadm_ids(dx, DIABETES_ICD_PREFIXES)
    htn_hadm    = _icd_matched_hadm_ids(dx, HYPERTENSION_ICD_PREFIXES)
    sepsis_hadm = _icd_matched_hadm_ids(dx, SEPSIS_ICD_PREFIXES)

    ckd    = df["hadm_id"].isin(ckd_hadm)
    diab   = df["hadm_id"].isin(diab_hadm)
    htn    = df["hadm_id"].isin(htn_hadm)
    sepsis = df["hadm_id"].isin(sepsis_hadm)

    raw_pts = (
        ckd.astype(int)    * _DX_CKD    +
        diab.astype(int)   * _DX_DIAB   +
        htn.astype(int)    * _DX_HTN    +
        sepsis.astype(int) * _DX_SEPSIS
    )
    df["diagnosis_context_points"] = raw_pts.clip(upper=_CAP_DIAGNOSIS).astype(int)

    def _detail(c: bool, d: bool, h: bool, s: bool) -> str:
        found = []
        if c:
            found.append("CKD history")
        if d:
            found.append("diabetes history")
        if h:
            found.append("hypertension history")
        if s:
            found.append("sepsis/infection context")
        if found:
            return f"Diagnosis context: {', '.join(found)} — relevant risk signal"
        return ""

    df["diagnosis_context_signal"] = [
        _detail(c, d, h, s) for c, d, h, s in zip(ckd, diab, htn, sepsis)
    ]
    return df


def _apply_medication_signal(df: pd.DataFrame) -> pd.DataFrame:
    """Kidney-relevant or nephrotoxic medication exposure: up to 5 pts."""
    try:
        rx = load_prescriptions()
    except Exception:
        df["medication_points"] = 0
        df["medication_signal"] = ""
        return df

    hadm_ids = set(df["hadm_id"].dropna().astype(int))
    rx = rx[rx["hadm_id"].isin(hadm_ids)].dropna(subset=["drug"]).copy()
    rx["drug_lower"] = rx["drug"].str.lower()

    pattern  = "|".join(NEPHROTOXIC_DRUGS)
    rx_toxic = rx[rx["drug_lower"].str.contains(pattern, na=False)]

    matched_drugs = (
        rx_toxic.groupby("hadm_id")["drug"]
        .apply(lambda s: sorted(s.str.title().unique().tolist()))
    )

    def _detail(drugs: list[str]) -> str:
        names  = ", ".join(drugs[:3])
        suffix = " and others" if len(drugs) > 3 else ""
        return f"Kidney-relevant medication: {names}{suffix} — possible nephrotoxic exposure"

    flag = df["hadm_id"].isin(matched_drugs.index)
    drug_detail = matched_drugs.apply(_detail)

    df["medication_points"] = flag.astype(int) * _CAP_MEDICATION
    df["medication_signal"] = df["hadm_id"].map(drug_detail).fillna("")
    return df


# ---------------------------------------------------------------------------
# Top-reasons builder
# ---------------------------------------------------------------------------

def _build_top_reasons(row: pd.Series) -> str:
    """
    Collect active risk signal strings, ordered by point contribution.

    Returns a pipe-delimited summary of contributing signals, or a
    'no significant risk signals' message if score is zero.
    """
    active = [
        (row.get(sig, ""), row.get(pts, 0))
        for sig, pts in _SIGNAL_TO_POINTS.items()
        if row.get(sig, "")
    ]
    active.sort(key=lambda x: x[1], reverse=True)
    if not active:
        return "No significant risk signals detected"
    return " | ".join(text for text, _ in active)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def compute_aki_risk_scores(
    cohort: pd.DataFrame | None = None,
    summary: pd.DataFrame | None = None,
) -> pd.DataFrame:
    """
    Compute AKI risk scores for all admissions in the cohort.

    Args:
        cohort:  One-row-per-admission DataFrame.  Loaded from
                 outputs/cohort.csv if None.
        summary: patient_marker_summary DataFrame.  Loaded from
                 outputs/patient_marker_summary.csv if None.

    Returns:
        DataFrame with AKI risk scores, tiers, and per-signal detail columns.
        One row per hadm_id.  Score is capped at 100.
    """
    if cohort is None:
        cohort = pd.read_csv(
            _OUTPUTS / "cohort.csv",
            parse_dates=["admittime", "dischtime"],
        )
    if summary is None:
        summary = pd.read_csv(
            _OUTPUTS / "patient_marker_summary.csv",
        )

    base = cohort[["subject_id", "hadm_id", "length_of_stay_days"]].copy()

    wide = _pivot_markers(summary)
    base = base.merge(wide, on="hadm_id", how="left")

    base = _apply_creatinine_signal(base)
    base = _apply_bun_signal(base)
    base = _apply_potassium_signal(base)
    base = _apply_bicarbonate_signal(base)
    base = _apply_hemodynamic_signal(base)
    base = _apply_urine_output_signal(base)
    base = _apply_diagnosis_context_signal(base)
    base = _apply_medication_signal(base)

    point_cols = list(_SIGNAL_TO_POINTS.values())
    base["aki_risk_score"] = (
        base[point_cols].fillna(0).sum(axis=1).clip(upper=100).astype(int)
    )
    base["aki_risk_tier"] = base["aki_risk_score"].apply(_score_to_tier)
    base["top_reasons"]   = base.apply(_build_top_reasons, axis=1)

    return base[_OUTPUT_COLUMNS].reset_index(drop=True)


# ---------------------------------------------------------------------------
# python -m src.aki_scoring
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Strata — computing AKI risk scores…\n")

    scores = compute_aki_risk_scores()

    _OUTPUTS.mkdir(exist_ok=True)
    out_path = _OUTPUTS / "aki_risk_scores.csv"
    scores.to_csv(out_path, index=False)

    print(f"Admissions scored: {len(scores)}")
    print(f"Saved: {out_path}")

    print("\nRisk tier distribution:")
    print(scores["aki_risk_tier"].value_counts().to_string())

    print("\nScore distribution (percentiles):")
    print(scores["aki_risk_score"].describe(percentiles=[0.25, 0.5, 0.75, 0.9]).to_string())

    print("\nSignal prevalence (% of admissions):")
    signal_cols = [
        "creatinine_signal", "bun_signal", "potassium_signal",
        "bicarbonate_signal", "hemodynamic_signal", "urine_output_signal",
        "diagnosis_context_signal", "medication_signal",
    ]
    for col in signal_cols:
        active = (scores[col] != "").sum()
        pct    = 100 * active / len(scores) if len(scores) else 0
        print(f"  {col:<30}  {active:>4} admissions ({pct:.1f}%)")

    print("\nTop 10 by AKI risk score:")
    print(
        scores[["hadm_id", "aki_risk_score", "aki_risk_tier", "top_reasons"]]
        .sort_values("aki_risk_score", ascending=False)
        .head(10)
        .to_string(index=False)
    )
