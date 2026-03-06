"""
Run the full pipeline: generate -> clean -> validate -> metrics -> forecast -> export serving.
"""
from __future__ import annotations

import sys
from pathlib import Path

from config import DATA_RAW, DATA_PROCESSED, DATA_SERVING

# Ensure we can import stages
sys.path.insert(0, str(Path(__file__).resolve().parent))

from stage_a_generate import run as run_a
from stage_b_clean import run as run_b
from stage_c_validate import run as run_c
from stage_d_metrics import run as run_d
from stage_e_forecast import run as run_e
from export_serving import run as run_export


def main() -> int:
    """Execute pipeline stages in order."""
    DATA_RAW.mkdir(parents=True, exist_ok=True)
    DATA_PROCESSED.mkdir(parents=True, exist_ok=True)
    DATA_SERVING.mkdir(parents=True, exist_ok=True)

    print("Stage A: Generating raw data...")
    run_a()
    print("Stage B: Cleaning and standardizing...")
    run_b()
    print("Stage C: Validating schema...")
    report = run_c()
    if not report.get("valid", True):
        print("Validation had errors:", report.get("schema_errors", [])[:3])
    print("Stage D: Computing KPIs and quality scores...")
    run_d()
    print("Stage E: Forecasting and anomaly detection...")
    run_e()
    print("Export: Writing serving files...")
    run_export()
    print("Pipeline complete. Outputs in", DATA_SERVING)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
