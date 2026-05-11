"""
Strata — clinical marker builder.

Loads labevents (hosp) and chartevents (ICU), matches each row to a
marker_key defined in marker_config.py, and produces two output files:

  outputs/patient_marker_summary.csv  — one row per (hadm_id, marker_key)
  outputs/patient_timeseries.csv      — one row per individual measurement

Matching is done by itemid (primary) — no fuzzy text matching needed since
MIMIC itemids are stable and already catalogued in marker_config.py.
"""

from pathlib import Path

import pandas as pd

from src.build_cohort import build_cohort
from src.load_data import load_chartevents, load_labevents
from src.marker_config import LAB_MARKERS, VITAL_MARKERS, MarkerDef

_OUTPUTS = Path(__file__).parent.parent / "outputs"

_ALL_MARKERS: dict[str, MarkerDef] = {**LAB_MARKERS, **VITAL_MARKERS}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _itemid_key_frame(markers: dict[str, MarkerDef]) -> pd.DataFrame:
    """
    Return a DataFrame with columns [itemid, marker_key], one row per
    (itemid, marker_key) pair.  Handles itemids shared across multiple keys.
    """
    rows = [
        {"itemid": iid, "marker_key": key}
        for key, mdef in markers.items()
        for iid in mdef.itemids
    ]
    return pd.DataFrame(rows) if rows else pd.DataFrame(columns=["itemid", "marker_key"])


def _first_unit(s: pd.Series) -> str | None:
    """Return the most common non-null unit in the series, or None."""
    clean = s.dropna()
    if clean.empty:
        return None
    return clean.mode().iloc[0]


def _determine_status(value: float, low, high) -> str:
    """
    Classify a numeric value against normal range thresholds.

    Uses latest_value and transparent comparison:
      - Low    if value < normal_low (when low defined)
      - High   if value > normal_high (when high defined)
      - Normal if value is within range
      - Observed if no range defined
    """
    low_missing = low is None or pd.isna(low)
    high_missing = high is None or pd.isna(high)
    if low_missing and high_missing:
        return "Observed"
    if not low_missing and value < low:
        return "Low"
    if not high_missing and value > high:
        return "High"
    return "Normal"


def _get_explanation(marker_key: str, status: str) -> str | None:
    """Return the matching blurb for a marker's status, or None."""
    mdef = _ALL_MARKERS.get(marker_key)
    if mdef is None:
        return None
    if status == "High":
        return mdef.blurb_high
    if status == "Low":
        return mdef.blurb_low
    return None


# ---------------------------------------------------------------------------
# Event loading — labs and vitals into a unified tidy frame
# ---------------------------------------------------------------------------

def _load_lab_events(cohort_hadm_ids: set[int]) -> pd.DataFrame:
    """
    Load labevents, filter to cohort, match to LAB_MARKERS by itemid.

    Returns tidy frame:
        subject_id, hadm_id, charttime, marker_key, marker_name,
        value, unit, category
    """
    labs = load_labevents()
    labs = labs[labs["hadm_id"].isin(cohort_hadm_ids)].copy()
    labs = labs.dropna(subset=["hadm_id", "valuenum", "charttime"])

    id_map = _itemid_key_frame(LAB_MARKERS)
    merged = labs.merge(id_map, on="itemid", how="inner")

    merged["marker_name"] = merged["marker_key"].map(
        {k: v.label for k, v in LAB_MARKERS.items()}
    )
    merged["category"] = merged["marker_key"].map(
        {k: v.category for k, v in LAB_MARKERS.items()}
    )

    return merged[[
        "subject_id", "hadm_id", "charttime",
        "marker_key", "marker_name", "valuenum", "valueuom", "category",
    ]].rename(columns={"valuenum": "value", "valueuom": "unit"})


def _load_vital_events(cohort_hadm_ids: set[int]) -> pd.DataFrame:
    """
    Load chartevents, filter to cohort, match to VITAL_MARKERS by itemid.

    Returns the same tidy frame schema as _load_lab_events.
    """
    charts = load_chartevents()
    charts = charts[charts["hadm_id"].isin(cohort_hadm_ids)].copy()
    charts = charts.dropna(subset=["hadm_id", "valuenum", "charttime"])

    id_map = _itemid_key_frame(VITAL_MARKERS)
    merged = charts.merge(id_map, on="itemid", how="inner")

    merged["marker_name"] = merged["marker_key"].map(
        {k: v.label for k, v in VITAL_MARKERS.items()}
    )
    merged["category"] = merged["marker_key"].map(
        {k: v.category for k, v in VITAL_MARKERS.items()}
    )

    return merged[[
        "subject_id", "hadm_id", "charttime",
        "marker_key", "marker_name", "valuenum", "valueuom", "category",
    ]].rename(columns={"valuenum": "value", "valueuom": "unit"})


# ---------------------------------------------------------------------------
# Timeseries
# ---------------------------------------------------------------------------

def _build_timeseries(tidy: pd.DataFrame) -> pd.DataFrame:
    """
    Reorder and sort the tidy events frame into the timeseries output schema.
    """
    ts = tidy[[
        "subject_id", "hadm_id", "charttime",
        "marker_key", "marker_name", "value", "unit", "category",
    ]].copy()
    return ts.sort_values(
        ["hadm_id", "marker_key", "charttime"]
    ).reset_index(drop=True)


# ---------------------------------------------------------------------------
# Marker summary
# ---------------------------------------------------------------------------

def _build_summary(tidy: pd.DataFrame) -> pd.DataFrame:
    """
    Aggregate tidy events to one row per (subject_id, hadm_id, marker_key).

    Computes statistical summaries, applies status logic to latest_value,
    and attaches normal ranges, explanation blurbs, and AKI relevance from
    marker_config.
    """
    sorted_tidy = tidy.sort_values(["hadm_id", "marker_key", "charttime"])

    agg = sorted_tidy.groupby(
        ["subject_id", "hadm_id", "marker_key"], as_index=False
    ).agg(
        marker_name=("marker_name", "first"),
        category=("category", "first"),
        latest_value=("value", "last"),
        min_value=("value", "min"),
        max_value=("value", "max"),
        mean_value=("value", "mean"),
        count=("value", "count"),
        first_charttime=("charttime", "min"),
        latest_charttime=("charttime", "max"),
        unit=("unit", _first_unit),
    )

    agg["mean_value"] = agg["mean_value"].round(3)

    agg["normal_low"] = agg["marker_key"].map(
        {k: v.low for k, v in _ALL_MARKERS.items()}
    )
    agg["normal_high"] = agg["marker_key"].map(
        {k: v.high for k, v in _ALL_MARKERS.items()}
    )
    agg["is_aki_relevant"] = agg["marker_key"].map(
        {k: v.aki_relevant for k, v in _ALL_MARKERS.items()}
    )

    agg["status"] = agg.apply(
        lambda r: _determine_status(r["latest_value"], r["normal_low"], r["normal_high"]),
        axis=1,
    )

    agg["explanation"] = agg.apply(
        lambda r: _get_explanation(r["marker_key"], r["status"]),
        axis=1,
    )

    col_order = [
        "subject_id", "hadm_id", "marker_key", "marker_name", "category",
        "latest_value", "min_value", "max_value", "mean_value", "count",
        "first_charttime", "latest_charttime", "unit",
        "normal_low", "normal_high", "status", "explanation", "is_aki_relevant",
    ]
    return agg[col_order].reset_index(drop=True)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def build_markers(
    cohort: pd.DataFrame | None = None,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Build clinical marker summary and timeseries for all cohort admissions.

    Args:
        cohort: Pre-loaded cohort DataFrame.  If None, loads from
                outputs/cohort.csv (if it exists) or calls build_cohort().

    Returns:
        (patient_marker_summary, patient_timeseries) as DataFrames.
    """
    if cohort is None:
        cohort_path = _OUTPUTS / "cohort.csv"
        if cohort_path.exists():
            cohort = pd.read_csv(
                cohort_path, parse_dates=["admittime", "dischtime"]
            )
        else:
            cohort = build_cohort()

    hadm_ids: set[int] = set(cohort["hadm_id"].dropna().astype(int))
    print(f"  Cohort: {len(hadm_ids)} admissions")

    print("  Loading lab events…")
    lab_tidy = _load_lab_events(hadm_ids)
    print(f"    {len(lab_tidy):,} lab rows matched")

    print("  Loading vital events…")
    vital_tidy = _load_vital_events(hadm_ids)
    print(f"    {len(vital_tidy):,} vital rows matched")

    tidy = pd.concat([lab_tidy, vital_tidy], ignore_index=True)
    print(f"  Total events: {len(tidy):,} across {tidy['hadm_id'].nunique()} admissions")

    if tidy.empty:
        empty_summary = pd.DataFrame(columns=[
            "subject_id", "hadm_id", "marker_key", "marker_name", "category",
            "latest_value", "min_value", "max_value", "mean_value", "count",
            "first_charttime", "latest_charttime", "unit",
            "normal_low", "normal_high", "status", "explanation", "is_aki_relevant",
        ])
        empty_ts = pd.DataFrame(columns=[
            "subject_id", "hadm_id", "charttime",
            "marker_key", "marker_name", "value", "unit", "category",
        ])
        return empty_summary, empty_ts

    timeseries = _build_timeseries(tidy)
    summary = _build_summary(tidy)

    return summary, timeseries


# ---------------------------------------------------------------------------
# python -m src.build_markers
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    print("Strata — building clinical marker summary…\n")

    summary, timeseries = build_markers()

    _OUTPUTS.mkdir(exist_ok=True)
    summary_path = _OUTPUTS / "patient_marker_summary.csv"
    timeseries_path = _OUTPUTS / "patient_timeseries.csv"

    summary.to_csv(summary_path, index=False)
    timeseries.to_csv(timeseries_path, index=False)

    print(f"\nSummary shape:    {summary.shape}")
    print(f"Timeseries shape: {timeseries.shape}")
    print(f"\nSaved: {summary_path}")
    print(f"Saved: {timeseries_path}")

    print(f"\nStatus distribution:")
    print(summary["status"].value_counts().to_string())

    print(f"\nMarker coverage (total observations):")
    print(
        summary.groupby("marker_key")["count"]
        .sum()
        .sort_values(ascending=False)
        .to_string()
    )
