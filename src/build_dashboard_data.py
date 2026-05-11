"""
Strata — build_dashboard_data.py

Combines cohort, marker summary, and AKI risk scores into a single
per-admission dashboard table written to outputs/dashboard_patients.csv.
"""

from pathlib import Path

import pandas as pd

OUTPUTS = Path("outputs")

COHORT_COLS = [
    "subject_id", "hadm_id", "gender", "age", "admission_type",
    "admittime", "dischtime", "length_of_stay_days",
    "has_icu_stay", "first_careunit", "last_careunit",
]

AKI_COLS = [
    "subject_id", "hadm_id",
    "aki_risk_score", "aki_risk_tier", "top_reasons",
]


def _marker_counts(summary: pd.DataFrame) -> pd.DataFrame:
    """Return per-admission abnormal marker counts."""
    keys = ["subject_id", "hadm_id"]
    base = summary[keys].drop_duplicates().copy()

    def _count(mask: pd.Series, col: str) -> pd.DataFrame:
        return (
            summary[mask]
            .groupby(keys)
            .size()
            .to_frame(col)
            .reset_index()
        )

    status = summary["status"]
    abn = _count(status.isin(["High", "Low"]), "abnormal_marker_count")  # type: ignore[arg-type]
    high = _count(status == "High", "high_marker_count")  # type: ignore[arg-type]
    low = _count(status == "Low", "low_marker_count")  # type: ignore[arg-type]

    counts = (
        base
        .merge(abn, on=keys, how="left")
        .merge(high, on=keys, how="left")
        .merge(low, on=keys, how="left")
    )
    count_cols = ["abnormal_marker_count", "high_marker_count", "low_marker_count"]
    counts[count_cols] = counts[count_cols].fillna(0).astype(int)
    return counts


def _top_concern_from_markers(summary: pd.DataFrame) -> pd.DataFrame:
    """
    For each admission, pick the single most concerning abnormal marker label.

    Priority: AKI-relevant first, then High before Low, then alphabetical for
    determinism.  Returns the marker's explanation if one exists, otherwise the
    marker label + status.
    """
    abnormal = summary[summary["status"].isin(["High", "Low"])].copy()
    if abnormal.empty:
        return pd.DataFrame(columns=["subject_id", "hadm_id", "marker_top_concern"])

    # Encode sort priority (lower = more important)
    abnormal["_aki_priority"] = (~abnormal["is_aki_relevant"].astype(bool)).astype(int)
    abnormal["_status_priority"] = (abnormal["status"] == "Low").astype(int)  # High=0, Low=1
    sort_cols = ["subject_id", "hadm_id", "_aki_priority", "_status_priority", "marker_key"]
    abnormal = abnormal.sort_values(by=sort_cols)  # type: ignore[call-overload]

    top = abnormal.groupby(["subject_id", "hadm_id"]).first().reset_index()

    def _pick_concern(r: pd.Series) -> str:
        expl = r["explanation"]
        if isinstance(expl, str) and expl.strip():
            return expl
        return f"{r['marker_name']}: {r['status']}"

    top["marker_top_concern"] = top.apply(_pick_concern, axis=1)
    return top[["subject_id", "hadm_id", "marker_top_concern"]].copy()  # type: ignore[return-value]


def _resolve_top_concern(row: pd.Series) -> str:
    """
    Prefer the first reason from AKI top_reasons; fall back to the best abnormal
    marker explanation; final fallback is the no-signal sentinel string.
    """
    reasons = str(row.get("top_reasons", "") or "")
    if reasons and reasons not in ("nan", "None"):
        # top_reasons is a pipe-delimited list; take the first entry
        return reasons.split("|")[0].strip()

    marker_concern = str(row.get("marker_top_concern", "") or "")
    if marker_concern and marker_concern not in ("nan", "None"):
        return marker_concern.strip()

    return "No major abnormal marker signal detected."


def build_dashboard_data() -> pd.DataFrame:
    """Merge cohort, marker summary, and AKI scores into one dashboard table."""
    cohort = pd.read_csv(OUTPUTS / "cohort.csv", usecols=COHORT_COLS)
    cohort = cohort.rename(columns={"age": "anchor_age"})

    summary = pd.read_csv(OUTPUTS / "patient_marker_summary.csv")
    aki = pd.read_csv(OUTPUTS / "aki_risk_scores.csv", usecols=AKI_COLS)

    counts = _marker_counts(summary)
    marker_concern = _top_concern_from_markers(summary)

    dashboard = (
        cohort
        .merge(aki, on=["subject_id", "hadm_id"], how="left")
        .merge(counts, on=["subject_id", "hadm_id"], how="left")
        .merge(marker_concern, on=["subject_id", "hadm_id"], how="left")
    )

    # Fill admissions with no AKI score (shouldn't happen, but defensive)
    dashboard["aki_risk_score"] = dashboard["aki_risk_score"].fillna(0).astype(int)
    dashboard["aki_risk_tier"] = dashboard["aki_risk_tier"].fillna("Unknown")
    dashboard[["abnormal_marker_count", "high_marker_count", "low_marker_count"]] = (
        dashboard[["abnormal_marker_count", "high_marker_count", "low_marker_count"]].fillna(0).astype(int)
    )

    dashboard["top_concern"] = dashboard.apply(_resolve_top_concern, axis=1)

    output_cols = [
        "subject_id", "hadm_id", "gender", "anchor_age",
        "admission_type", "admittime", "dischtime", "length_of_stay_days",
        "has_icu_stay", "first_careunit", "last_careunit",
        "aki_risk_score", "aki_risk_tier",
        "abnormal_marker_count", "high_marker_count", "low_marker_count",
        "top_concern", "top_reasons",
    ]
    return dashboard[output_cols].copy()  # type: ignore[return-value]


def main() -> None:
    """Build and write outputs/dashboard_patients.csv."""
    df = build_dashboard_data()
    out_path = OUTPUTS / "dashboard_patients.csv"
    df.to_csv(out_path, index=False)
    print(f"Wrote {len(df)} rows → {out_path}")
    print(df[["subject_id", "hadm_id", "aki_risk_tier", "abnormal_marker_count", "top_concern"]].to_string(index=False))


if __name__ == "__main__":
    main()
