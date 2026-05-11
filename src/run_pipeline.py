"""
Strata pipeline runner — executes all data-build steps in order and writes
output CSVs consumed by the Streamlit dashboard.
"""
import sys
import time
import traceback
from pathlib import Path

OUTPUTS = Path(__file__).parent.parent / "outputs"


def _step(label: str) -> None:
    print(f"\n[Strata] {label}…")


def _done(label: str, elapsed: float) -> None:
    print(f"[Strata] ✓ {label} ({elapsed:.1f}s)")


def _run_step(label: str, fn):
    """Run fn(), print progress, and re-raise with context on failure."""
    _step(label)
    t0 = time.monotonic()
    try:
        result = fn()
    except Exception:
        print(f"\n[Strata] ✗ '{label}' failed:\n", file=sys.stderr)
        traceback.print_exc()
        sys.exit(1)
    _done(label, time.monotonic() - t0)
    return result


def main() -> None:
    OUTPUTS.mkdir(exist_ok=True)
    print("[Strata] Starting pipeline…")
    t_start = time.monotonic()

    # Step 1 — cohort
    from src.build_cohort import build_cohort

    cohort = _run_step("Building admission cohort", build_cohort)
    cohort.to_csv(OUTPUTS / "cohort.csv", index=False)

    # Step 2 — clinical markers
    from src.build_markers import build_markers

    summary, timeseries = _run_step("Extracting clinical markers", build_markers)
    summary.to_csv(OUTPUTS / "patient_marker_summary.csv", index=False)
    timeseries.to_csv(OUTPUTS / "patient_timeseries.csv", index=False)

    # Step 3 — AKI risk scoring
    from src.aki_scoring import compute_aki_risk_scores

    scores = _run_step("Computing AKI risk scores", compute_aki_risk_scores)
    scores.to_csv(OUTPUTS / "aki_risk_scores.csv", index=False)

    # Step 4 — dashboard dataset
    from src.build_dashboard_data import build_dashboard_data

    dashboard = _run_step("Building dashboard dataset", build_dashboard_data)
    dashboard.to_csv(OUTPUTS / "dashboard_patients.csv", index=False)

    elapsed = time.monotonic() - t_start
    print(f"\n[Strata] Pipeline complete in {elapsed:.1f}s.")
    print(f"[Strata] Outputs written to: {OUTPUTS.resolve()}")
    print("\nStrata dashboard data is ready. Run: streamlit run src/app.py")


if __name__ == "__main__":
    main()
