"""
Strata — clinical marker configuration.

Pure static data: no I/O, no computation.  All clinical rules, normal ranges,
item IDs, explanation blurbs, and MIMIC label aliases live here so they can be
updated without touching pipeline logic.

Normal ranges are population-level reference ranges suitable for adult ICU
context.  They are intentionally transparent and adjustable — not derived from
a model.
"""

from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Marker definition
# ---------------------------------------------------------------------------

@dataclass
class MarkerDef:
    """Definition of one clinical marker."""
    label: str                       # Human-readable name shown in the UI
    itemids: list[int]               # One or more MIMIC itemids that map to this marker
    low: float | None                # Lower bound of normal range (None = no lower bound)
    high: float | None               # Upper bound of normal range (None = no upper bound)
    unit: str                        # Display unit
    category: str                    # renal | metabolic | hematology | hemodynamic
    source: str                      # "lab" (labevents) or "vital" (chartevents)
    aki_relevant: bool = False       # Whether this marker contributes to AKI risk assessment
    aliases: list[str] = field(default_factory=list)  # MIMIC label strings for text-based matching
    blurb_high: str | None = None    # Plain-English explanation when value is above normal
    blurb_low: str | None = None     # Plain-English explanation when value is below normal


# ---------------------------------------------------------------------------
# Lab markers  (source: labevents, hosp module)
# ---------------------------------------------------------------------------

LAB_MARKERS: dict[str, MarkerDef] = {

    # --- Renal ---
    "creatinine": MarkerDef(
        label="Creatinine",
        itemids=[50912],
        low=0.5, high=1.2,
        unit="mg/dL",
        category="renal",
        source="lab",
        aki_relevant=True,
        aliases=["Creatinine", "Creatinine, Serum", "Creatinine, Blood"],
        blurb_high=(
            "Elevated creatinine may suggest reduced kidney filtration (GFR). "
            "A rising trend across multiple draws can be associated with AKI — "
            "requires clinical context and serial review."
        ),
        blurb_low=(
            "Low creatinine is often benign (low muscle mass) but may affect "
            "the sensitivity of creatinine-based AKI criteria."
        ),
    ),
    "bun": MarkerDef(
        label="BUN (Urea Nitrogen)",
        itemids=[51006],
        low=7.0, high=25.0,
        unit="mg/dL",
        category="renal",
        source="lab",
        aki_relevant=True,
        aliases=["Urea Nitrogen", "Blood Urea Nitrogen", "BUN", "Urea Nitrogen, Blood"],
        blurb_high=(
            "Elevated BUN may suggest impaired urea clearance, which can be "
            "associated with reduced kidney function or high protein catabolism. "
            "In combination with elevated creatinine, it may reinforce an AKI "
            "risk signal — requires clinical context."
        ),
        blurb_low=None,
    ),
    "potassium": MarkerDef(
        label="Potassium",
        itemids=[50971],
        low=3.5, high=5.0,
        unit="mEq/L",
        category="renal",
        source="lab",
        aki_relevant=True,
        aliases=["Potassium", "Potassium, Serum", "Potassium, Whole Blood", "K"],
        blurb_high=(
            "High potassium (hyperkalemia) can be associated with impaired renal "
            "excretion.  Levels above 5.5 mEq/L may warrant clinical review due "
            "to possible cardiac implications."
        ),
        blurb_low=(
            "Low potassium (hypokalemia) may suggest GI losses, diuretic use, "
            "or inadequate intake.  Requires clinical context."
        ),
    ),
    "bicarbonate": MarkerDef(
        label="Bicarbonate",
        itemids=[50882],
        low=22.0, high=29.0,
        unit="mEq/L",
        category="renal",
        source="lab",
        aki_relevant=True,
        aliases=["Bicarbonate", "HCO3", "Bicarbonate, Serum", "Total CO2", "CO2"],
        blurb_high=(
            "Elevated bicarbonate may suggest metabolic alkalosis, sometimes "
            "seen with diuretic use or vomiting.  Clinical review is recommended."
        ),
        blurb_low=(
            "Low bicarbonate may suggest metabolic acidosis.  In the context of "
            "possible kidney stress, this can be associated with a reduced ability "
            "to excrete acid — an early-warning signal worth clinical review."
        ),
    ),

    # --- Metabolic ---
    "sodium": MarkerDef(
        label="Sodium",
        itemids=[50983],
        low=136.0, high=145.0,
        unit="mEq/L",
        category="metabolic",
        source="lab",
        aki_relevant=False,
        aliases=["Sodium", "Sodium, Serum", "Sodium, Whole Blood", "Na"],
        blurb_high=(
            "High sodium (hypernatremia) may suggest dehydration or free-water "
            "deficit, which can be associated with increased kidney stress."
        ),
        blurb_low=(
            "Low sodium (hyponatremia) is common in hospitalized patients and can "
            "result from fluid overload, SIADH, or other causes.  Clinical review "
            "is recommended."
        ),
    ),
    "chloride": MarkerDef(
        label="Chloride",
        itemids=[50902],
        low=98.0, high=107.0,
        unit="mEq/L",
        category="metabolic",
        source="lab",
        aki_relevant=False,
        aliases=["Chloride", "Chloride, Serum", "Chloride, Whole Blood", "Cl"],
        blurb_high=(
            "High chloride (hyperchloremia) can be associated with acidosis or "
            "excessive saline administration.  High chloride combined with low "
            "bicarbonate may suggest non-anion-gap metabolic acidosis."
        ),
        blurb_low=(
            "Low chloride may accompany metabolic alkalosis or significant "
            "GI losses.  Requires clinical context."
        ),
    ),
    "glucose": MarkerDef(
        label="Glucose",
        itemids=[50931],
        low=70.0, high=140.0,
        unit="mg/dL",
        category="metabolic",
        source="lab",
        aki_relevant=False,
        aliases=["Glucose", "Glucose, Serum", "Glucose, Whole Blood", "Blood Glucose"],
        blurb_high=(
            "High glucose (hyperglycemia) is common in critically ill patients "
            "and in those with diabetes.  Persistent elevation may be associated "
            "with kidney stress over time."
        ),
        blurb_low=(
            "Low glucose (hypoglycemia) requires prompt clinical attention, "
            "particularly in patients on insulin."
        ),
    ),
    "lactate": MarkerDef(
        label="Lactate",
        itemids=[50813],
        low=0.5, high=2.0,
        unit="mmol/L",
        category="metabolic",
        source="lab",
        aki_relevant=True,
        aliases=["Lactate", "Lactic Acid", "Lactate, Whole Blood"],
        blurb_high=(
            "Elevated lactate may suggest tissue hypoperfusion or anaerobic "
            "metabolism.  In the context of possible sepsis or circulatory "
            "compromise, it can be associated with organ — including kidney — "
            "stress.  Requires clinical context."
        ),
        blurb_low=None,
    ),
    "albumin": MarkerDef(
        label="Albumin",
        itemids=[50862],
        low=3.5, high=5.0,
        unit="g/dL",
        category="metabolic",
        source="lab",
        aki_relevant=False,
        aliases=["Albumin", "Albumin, Serum"],
        blurb_high=None,
        blurb_low=(
            "Low albumin (hypoalbuminemia) can be associated with malnutrition, "
            "liver disease, or protein loss.  It may signal systemic inflammation "
            "and can affect drug binding.  Clinical review is recommended."
        ),
    ),
    "bilirubin_total": MarkerDef(
        label="Bilirubin (Total)",
        itemids=[50885],
        low=0.1, high=1.2,
        unit="mg/dL",
        category="metabolic",
        source="lab",
        aki_relevant=False,
        aliases=["Bilirubin, Total", "Total Bilirubin", "Bilirubin Total"],
        blurb_high=(
            "Elevated bilirubin may suggest liver dysfunction or hemolysis. "
            "Hepatorenal interactions may be relevant in patients with combined "
            "liver and kidney stress — requires clinical context."
        ),
        blurb_low=None,
    ),

    # --- Hematology ---
    "hemoglobin": MarkerDef(
        label="Hemoglobin",
        itemids=[51222],
        low=11.0, high=17.5,
        unit="g/dL",
        category="hematology",
        source="lab",
        aki_relevant=True,
        aliases=["Hemoglobin", "Hgb", "Hemoglobin, Blood"],
        blurb_high=None,
        blurb_low=(
            "Low hemoglobin (anemia) is common in CKD and may be associated with "
            "AKI due to reduced erythropoietin production.  It may also reflect "
            "blood loss or bone marrow suppression — requires clinical context."
        ),
    ),
    "hematocrit": MarkerDef(
        label="Hematocrit",
        itemids=[51221],
        low=36.0, high=52.0,
        unit="%",
        category="hematology",
        source="lab",
        aki_relevant=False,
        aliases=["Hematocrit", "Hct", "Hematocrit, Calculated"],
        blurb_high=None,
        blurb_low=(
            "Low hematocrit parallels hemoglobin as a marker of anemia. "
            "Trending alongside hemoglobin gives a fuller picture of red "
            "cell mass.  Requires clinical context."
        ),
    ),
    "wbc": MarkerDef(
        label="WBC",
        itemids=[51301],
        low=4.5, high=11.0,
        unit="K/uL",
        category="hematology",
        source="lab",
        aki_relevant=True,
        aliases=["White Blood Cells", "WBC", "Leukocytes", "WBC Count"],
        blurb_high=(
            "Elevated WBC may suggest infection, inflammation, or stress response. "
            "Sepsis-related kidney stress often presents alongside an elevated or "
            "rapidly changing WBC — requires clinical context."
        ),
        blurb_low=(
            "Low WBC may suggest immunosuppression or bone marrow compromise, "
            "which can increase infection risk."
        ),
    ),
    "platelets": MarkerDef(
        label="Platelet Count",
        itemids=[51265],
        low=150.0, high=400.0,
        unit="K/uL",
        category="hematology",
        source="lab",
        aki_relevant=False,
        aliases=["Platelet Count", "Platelets", "PLT"],
        blurb_high=(
            "Elevated platelet count may accompany inflammatory states or "
            "reactive thrombocytosis.  Requires clinical context."
        ),
        blurb_low=(
            "Low platelets (thrombocytopenia) can be associated with sepsis, "
            "DIC, or drug effects.  Critically low levels may increase "
            "bleeding risk — clinical review is recommended."
        ),
    ),
    "inr": MarkerDef(
        label="INR",
        itemids=[51237],
        low=0.9, high=1.1,
        unit="ratio",
        category="hematology",
        source="lab",
        aki_relevant=False,
        aliases=["INR(PT)", "INR", "PT - INR", "International Normalized Ratio"],
        blurb_high=(
            "Elevated INR may suggest impaired coagulation, often associated with "
            "liver dysfunction, vitamin K deficiency, or anticoagulant use. "
            "Clinical review is needed to identify the cause."
        ),
        blurb_low=None,
    ),
    "troponin_t": MarkerDef(
        label="Troponin T",
        itemids=[51003],
        low=None, high=0.01,
        unit="ng/mL",
        category="hematology",
        source="lab",
        aki_relevant=False,
        aliases=["Troponin T", "Troponin-T", "cTnT"],
        blurb_high=(
            "Elevated troponin T may signal myocardial stress or injury. "
            "Cardiorenal interactions are relevant — both heart failure and "
            "kidney stress can be associated with troponin elevation. "
            "Requires clinical context."
        ),
        blurb_low=None,
    ),

    # --- Hemodynamic (lab) ---
    "lactate_hemodynamic": MarkerDef(
        label="Lactate (hemodynamic context)",
        itemids=[50813],
        low=None, high=2.0,
        unit="mmol/L",
        category="hemodynamic",
        source="lab",
        aki_relevant=True,
        aliases=["Lactate", "Lactic Acid", "Lactate, Whole Blood"],
        blurb_high=(
            "Lactate above 2 mmol/L may suggest tissue hypoperfusion. "
            "In critically ill patients, this can be an early-warning signal "
            "for hemodynamic instability that may contribute to pre-renal "
            "kidney stress — requires clinical context."
        ),
        blurb_low=None,
    ),
}


# ---------------------------------------------------------------------------
# Vital markers  (source: chartevents, ICU module)
# ---------------------------------------------------------------------------

VITAL_MARKERS: dict[str, MarkerDef] = {

    "heart_rate": MarkerDef(
        label="Heart Rate",
        itemids=[220045],
        low=60.0, high=100.0,
        unit="bpm",
        category="hemodynamic",
        source="vital",
        aki_relevant=True,
        aliases=["Heart Rate", "HR", "Pulse"],
        blurb_high=(
            "Persistent tachycardia may suggest pain, fever, hypovolemia, or "
            "possible sepsis — all of which can be associated with reduced "
            "renal perfusion.  Requires clinical context."
        ),
        blurb_low=(
            "Low heart rate (bradycardia) may reflect cardiac conduction issues "
            "or medication effect and warrants clinical review."
        ),
    ),
    "map_noninvasive": MarkerDef(
        label="MAP (Non-invasive)",
        itemids=[220181],
        low=70.0, high=100.0,
        unit="mmHg",
        category="hemodynamic",
        source="vital",
        aki_relevant=True,
        aliases=["Non Invasive Blood Pressure mean", "NBP Mean", "NIBP Mean"],
        blurb_high=(
            "Elevated MAP may suggest hypertension, which over time can be "
            "associated with renal vascular stress."
        ),
        blurb_low=(
            "MAP below 65–70 mmHg may be associated with reduced renal "
            "perfusion pressure.  Sustained low MAP is a possible early-warning "
            "signal for pre-renal kidney stress — requires clinical context."
        ),
    ),
    "map_arterial": MarkerDef(
        label="MAP (Arterial)",
        itemids=[220052],
        low=70.0, high=100.0,
        unit="mmHg",
        category="hemodynamic",
        source="vital",
        aki_relevant=True,
        aliases=["Arterial Blood Pressure mean", "ABP Mean", "ART BP Mean", "Art. BP Mean"],
        blurb_high=(
            "Elevated arterial MAP may suggest hypertension or vasopressor use. "
            "Requires clinical context."
        ),
        blurb_low=(
            "Low arterial MAP may be associated with reduced organ perfusion "
            "pressure, including to the kidneys — a possible early-warning signal."
        ),
    ),
    "sbp": MarkerDef(
        label="Systolic BP (Non-invasive)",
        itemids=[220179],
        low=90.0, high=140.0,
        unit="mmHg",
        category="hemodynamic",
        source="vital",
        aki_relevant=True,
        aliases=["Non Invasive Blood Pressure systolic", "NBP systolic", "NIBP Systolic", "SBP"],
        blurb_high=(
            "Elevated systolic BP may signal hypertension, a known risk factor "
            "associated with chronic kidney stress over time."
        ),
        blurb_low=(
            "Low systolic BP may suggest hemodynamic compromise and possible "
            "reduced renal perfusion pressure.  Requires clinical context."
        ),
    ),
    "dbp": MarkerDef(
        label="Diastolic BP (Non-invasive)",
        itemids=[220180],
        low=60.0, high=90.0,
        unit="mmHg",
        category="hemodynamic",
        source="vital",
        aki_relevant=False,
        aliases=["Non Invasive Blood Pressure diastolic", "NBP diastolic", "NIBP Diastolic", "DBP"],
        blurb_high=None,
        blurb_low=(
            "Low diastolic BP can accompany distributive states, possibly "
            "reducing renal perfusion.  Requires clinical context."
        ),
    ),
    "spo2": MarkerDef(
        label="SpO₂",
        itemids=[220277],
        low=95.0, high=None,
        unit="%",
        category="hemodynamic",
        source="vital",
        aki_relevant=False,
        aliases=["O2 saturation pulseoxymetry", "SpO2", "Pulse Ox", "Oxygen Saturation"],
        blurb_high=None,
        blurb_low=(
            "Low oxygen saturation may suggest hypoxemia, which can place "
            "additional stress on all organs including the kidneys. "
            "Requires clinical context."
        ),
    ),
    "respiratory_rate": MarkerDef(
        label="Respiratory Rate",
        itemids=[220210],
        low=12.0, high=20.0,
        unit="insp/min",
        category="hemodynamic",
        source="vital",
        aki_relevant=True,
        aliases=["Respiratory Rate", "RR", "Resp Rate"],
        blurb_high=(
            "Elevated respiratory rate may suggest metabolic acidosis "
            "(compensatory breathing), which can be associated with kidney "
            "stress — an early-warning signal worth clinical review."
        ),
        blurb_low=None,
    ),
    "temperature_f": MarkerDef(
        label="Temperature",
        itemids=[223761],
        low=97.0, high=99.5,
        unit="°F",
        category="hemodynamic",
        source="vital",
        aki_relevant=True,
        aliases=["Temperature Fahrenheit", "Temp F", "Temperature F"],
        blurb_high=(
            "Fever is common in infection and inflammatory states. "
            "Sepsis-associated kidney stress is one of the most common forms "
            "of hospital-acquired kidney injury — requires clinical context."
        ),
        blurb_low=(
            "Low temperature in the ICU context may suggest severe sepsis or "
            "hemodynamic compromise — requires clinical review."
        ),
    ),
}

# Combined view for modules that iterate all markers.
ALL_MARKERS: dict[str, MarkerDef] = {**LAB_MARKERS, **VITAL_MARKERS}

# Flat alias → marker key lookup for text-based MIMIC label matching.
ALIAS_TO_KEY: dict[str, str] = {
    alias.lower(): key
    for key, mdef in ALL_MARKERS.items()
    for alias in mdef.aliases
}


# ---------------------------------------------------------------------------
# AKI scoring weights
# Each key maps to a scoring rule in aki_scoring.py.
# Weights sum to 100.
# ---------------------------------------------------------------------------

AKI_SCORE_WEIGHTS: dict[str, int] = {
    "creatinine_high":     20,  # Latest creatinine above normal
    "creatinine_rising":   15,  # Creatinine increasing across draws
    "bun_high":            15,  # BUN above normal
    "bicarbonate_low":     10,  # Bicarbonate below normal (metabolic acidosis signal)
    "potassium_abnormal":  10,  # Potassium outside normal range
    "map_low":             10,  # MAP below 65 mmHg (renal hypoperfusion threshold)
    "urine_output_low":    10,  # Oliguric pattern from outputevents
    "comorbidity":          5,  # CKD, diabetes, or hypertension ICD code present
    "nephrotoxic_drug":     5,  # Nephrotoxic medication prescribed
}

# MAP threshold that triggers the hypoperfusion flag (below normal low, stricter).
MAP_HYPOPERFUSION_THRESHOLD = 65.0  # mmHg

# Oliguria threshold: mL/kg/hr is not available, so we use total 24-hr output.
URINE_OUTPUT_OLIGURIA_ML_24H = 400.0  # mL — below this over any 24-h window → flag

# Creatinine rising: flag if latest value exceeds first value by this ratio.
CREATININE_RISE_RATIO = 1.5  # i.e., 50% increase from baseline


# ---------------------------------------------------------------------------
# Nephrotoxic drug substrings (case-insensitive match against prescriptions.drug)
# ---------------------------------------------------------------------------

NEPHROTOXIC_DRUGS: list[str] = [
    # Aminoglycosides
    "gentamicin",
    "tobramycin",
    "amikacin",
    # Glycopeptides
    "vancomycin",
    # Antifungals
    "amphotericin",
    # Calcineurin inhibitors
    "cyclosporine",
    "tacrolimus",
    # Chemotherapy
    "cisplatin",
    "carboplatin",
    "methotrexate",
    # NSAIDs
    "ibuprofen",
    "naproxen",
    "ketorolac",
    "indomethacin",
    "diclofenac",
    # Contrast (oral formulations sometimes charted)
    "contrast",
    # Antiviral
    "acyclovir",
    "tenofovir",
]


# ---------------------------------------------------------------------------
# Comorbidity ICD code prefixes (both ICD-9 and ICD-10)
# ---------------------------------------------------------------------------

# Chronic kidney disease
CKD_ICD_PREFIXES: list[str] = ["N18", "585"]

# Diabetes mellitus (all types)
DIABETES_ICD_PREFIXES: list[str] = ["E10", "E11", "E12", "E13", "250"]

# Hypertension
HYPERTENSION_ICD_PREFIXES: list[str] = ["I10", "I11", "I12", "I13", "401", "402", "403"]

# Sepsis and systemic infection context (ICD-9 and ICD-10)
SEPSIS_ICD_PREFIXES: list[str] = [
    "A40",   # Streptococcal sepsis (ICD-10)
    "A41",   # Other sepsis (ICD-10)
    "A22",   # Anthrax/septicemia (ICD-10)
    "R65",   # SIRS / severe sepsis (ICD-10)
    "B37",   # Candidal septicemia (ICD-10)
    "038",   # Septicemia (ICD-9)
    "995",   # Systemic inflammatory/sepsis response (ICD-9)
]

# Combined list used by aki_scoring.py
COMORBIDITY_ICD_PREFIXES: list[str] = (
    CKD_ICD_PREFIXES + DIABETES_ICD_PREFIXES + HYPERTENSION_ICD_PREFIXES
)


# ---------------------------------------------------------------------------
# Risk tier labels
# ---------------------------------------------------------------------------

AKI_RISK_TIERS: dict[str, tuple[int, int]] = {
    "Low":      (0,  29),
    "Moderate": (30, 59),
    "High":     (60, 100),
}

TIER_COLORS: dict[str, str] = {
    "Low":      "#2ecc71",   # green
    "Moderate": "#f39c12",   # amber
    "High":     "#e74c3c",   # red
}
