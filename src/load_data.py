"""
Strata — data loading layer.

Each function loads one MIMIC-IV demo table from its .csv.gz file and
returns a typed DataFrame.  No transformation happens here; callers own
that responsibility.
"""

from pathlib import Path
import pandas as pd

# Resolve paths relative to the project root (one level above src/).
_ROOT = Path(__file__).parent.parent
_HOSP = _ROOT / "data" / "mimic-iv-demo" / "hosp"
_ICU = _ROOT / "data" / "mimic-iv-demo" / "icu"


# ---------------------------------------------------------------------------
# Hospital tables
# ---------------------------------------------------------------------------

def load_patients() -> pd.DataFrame:
    """Load patients.csv.gz — one row per patient."""
    return pd.read_csv(
        _HOSP / "patients.csv.gz",
        parse_dates=["dod"],
    )


def load_admissions() -> pd.DataFrame:
    """Load admissions.csv.gz — one row per hospital admission."""
    return pd.read_csv(
        _HOSP / "admissions.csv.gz",
        parse_dates=["admittime", "dischtime", "deathtime", "edregtime", "edouttime"],
    )


def load_labevents() -> pd.DataFrame:
    """Load labevents.csv.gz — one row per laboratory result."""
    return pd.read_csv(
        _HOSP / "labevents.csv.gz",
        parse_dates=["charttime", "storetime"],
    )


def load_d_labitems() -> pd.DataFrame:
    """Load d_labitems.csv.gz — lab item dictionary (itemid → label/category)."""
    return pd.read_csv(_HOSP / "d_labitems.csv.gz")


def load_diagnoses_icd() -> pd.DataFrame:
    """Load diagnoses_icd.csv.gz — ICD diagnosis codes per admission."""
    return pd.read_csv(_HOSP / "diagnoses_icd.csv.gz")


def load_d_icd_diagnoses() -> pd.DataFrame:
    """Load d_icd_diagnoses.csv.gz — ICD code dictionary (code → long title)."""
    return pd.read_csv(_HOSP / "d_icd_diagnoses.csv.gz")


def load_prescriptions() -> pd.DataFrame:
    """Load prescriptions.csv.gz — medication orders per admission."""
    return pd.read_csv(
        _HOSP / "prescriptions.csv.gz",
        parse_dates=["starttime", "stoptime"],
    )


# ---------------------------------------------------------------------------
# ICU tables
# ---------------------------------------------------------------------------

def load_icustays() -> pd.DataFrame:
    """Load icustays.csv.gz — one row per ICU stay."""
    return pd.read_csv(
        _ICU / "icustays.csv.gz",
        parse_dates=["intime", "outtime"],
    )


def load_chartevents() -> pd.DataFrame:
    """Load chartevents.csv.gz — bedside vitals and nursing chart entries."""
    return pd.read_csv(
        _ICU / "chartevents.csv.gz",
        parse_dates=["charttime", "storetime"],
    )


def load_d_items() -> pd.DataFrame:
    """Load d_items.csv.gz — ICU item dictionary (itemid → label/category)."""
    return pd.read_csv(_ICU / "d_items.csv.gz")


def load_outputevents() -> pd.DataFrame:
    """Load outputevents.csv.gz — fluid output measurements (includes urine output)."""
    return pd.read_csv(
        _ICU / "outputevents.csv.gz",
        parse_dates=["charttime", "storetime"],
    )


# ---------------------------------------------------------------------------
# Convenience loader — returns all tables as a dict
# ---------------------------------------------------------------------------

def load_all() -> dict[str, pd.DataFrame]:
    """Load every table and return a name-keyed dict."""
    return {
        "patients":        load_patients(),
        "admissions":      load_admissions(),
        "labevents":       load_labevents(),
        "d_labitems":      load_d_labitems(),
        "diagnoses_icd":   load_diagnoses_icd(),
        "d_icd_diagnoses": load_d_icd_diagnoses(),
        "prescriptions":   load_prescriptions(),
        "icustays":        load_icustays(),
        "chartevents":     load_chartevents(),
        "d_items":         load_d_items(),
        "outputevents":    load_outputevents(),
    }


# ---------------------------------------------------------------------------
# Quick smoke-test: python -m src.load_data
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    tables = load_all()
    col_width = max(len(k) for k in tables)
    print(f"\n{'Table':<{col_width}}  {'Rows':>8}  {'Cols':>5}")
    print("-" * (col_width + 18))
    for name, df in tables.items():
        print(f"{name:<{col_width}}  {len(df):>8,}  {df.shape[1]:>5}")
    print()
