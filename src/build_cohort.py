"""
Strata — cohort builder.

Produces one row per hospital admission, enriched with patient demographics
and an ICU-stay summary.  This is the base table that all downstream modules
join against.

No lab or vital logic lives here — only structural joins and stay-level facts.
"""

from pathlib import Path

import pandas as pd

from src.load_data import load_admissions, load_icustays, load_patients

_OUTPUTS = Path(__file__).parent.parent / "outputs"


def _build_icu_summary(icustays: pd.DataFrame) -> pd.DataFrame:
    """
    Collapse icustays to one summary row per hadm_id.

    first_careunit / last_careunit are resolved by sorting on intime so that
    multi-stay admissions reflect the actual temporal order of units visited.
    """
    if icustays.empty:
        return pd.DataFrame(columns=[
            "hadm_id", "has_icu_stay", "num_icu_stays",
            "first_icu_intime", "last_icu_outtime",
            "first_careunit", "last_careunit",
        ])

    sorted_stays = icustays.sort_values(["hadm_id", "intime"])

    agg = sorted_stays.groupby("hadm_id", as_index=False).agg(
        num_icu_stays=("stay_id", "count"),
        first_icu_intime=("intime", "min"),
        last_icu_outtime=("outtime", "max"),
        first_careunit=("first_careunit", "first"),
        last_careunit=("last_careunit", "last"),
    )
    agg["has_icu_stay"] = True
    return agg


def build_cohort() -> pd.DataFrame:
    """
    Join patients + admissions + ICU summary into one admission-level table.

    Returns a DataFrame with one row per hadm_id.
    """
    patients = load_patients()
    admissions = load_admissions()
    icustays = load_icustays()

    # MIMIC-IV uses anchor_age (age at anchor_year) rather than DOB.
    patients_slim = patients[["subject_id", "gender", "anchor_age"]].rename(
        columns={"anchor_age": "age"}
    )

    admissions_slim = admissions[[
        "subject_id", "hadm_id",
        "admittime", "dischtime",
        "admission_type", "admission_location", "discharge_location",
        "race", "language", "marital_status", "insurance",
        "hospital_expire_flag",
    ]]

    cohort = admissions_slim.merge(patients_slim, on="subject_id", how="left")

    cohort["length_of_stay_days"] = (
        (cohort["dischtime"] - cohort["admittime"])
        .dt.total_seconds() / 86_400
    ).round(2)

    icu_summary = _build_icu_summary(icustays)
    cohort = cohort.merge(icu_summary, on="hadm_id", how="left")

    # Fill admissions with no ICU stay.
    cohort["has_icu_stay"] = cohort["has_icu_stay"].fillna(False)
    cohort["num_icu_stays"] = cohort["num_icu_stays"].fillna(0).astype(int)

    col_order = [
        "subject_id", "hadm_id",
        "age", "gender",
        "admission_type", "admission_location", "discharge_location",
        "race", "language", "marital_status", "insurance",
        "admittime", "dischtime", "length_of_stay_days",
        "has_icu_stay", "num_icu_stays",
        "first_icu_intime", "last_icu_outtime",
        "first_careunit", "last_careunit",
        "hospital_expire_flag",
    ]
    return cohort[col_order].reset_index(drop=True)


# ---------------------------------------------------------------------------
# python -m src.build_cohort
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cohort = build_cohort()

    _OUTPUTS.mkdir(exist_ok=True)
    out_path = _OUTPUTS / "cohort.csv"
    cohort.to_csv(out_path, index=False)

    print(f"\nShape: {cohort.shape}")
    print(f"Saved: {out_path}")
    print(f"\nFirst 5 rows:")
    print(cohort.head().to_string())
