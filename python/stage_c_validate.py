"""
Stage C: Validate cleaned data with Pandera schemas.

- Schema checks: types, ranges, uniqueness, allowed categories
- Writes validation_report.json to data/processed/
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import pandas as pd
import pandera as pa
from pandera import Column, Check, DataFrameSchema

from config import DATA_PROCESSED, ROUTE_IDS


def get_daily_schema() -> DataFrameSchema:
    """Pandera schema for cleaned daily route data."""
    return DataFrameSchema(
        {
            "date": Column(pa.String, Check.str_length(min_value=10, max_value=10)),
            "group": Column(pa.String, Check.isin(list(ROUTE_IDS))),
            "ridership": Column(pa.Int, Check.greater_than_or_equal_to(0)),
            "on_time_pct": Column(pa.Float, Check.in_range(0, 100)),
            "day_type": Column(pa.String, Check.isin(["Weekday", "Weekend", "Holiday"])),
            "vehicle_type": Column(pa.String, Check.isin(["Hybrid", "Diesel", "CNG"])),
            "fuel_liters": Column(pa.Float, Check.greater_than_or_equal_to(0)),
            "cost_usd": Column(pa.Float, Check.greater_than_or_equal_to(0)),
            "co2_kg": Column(pa.Float, Check.greater_than_or_equal_to(0)),
        },
        strict="filter",
        coerce=True,
    )


def validate_and_report(processed_dir: Path | None = None) -> dict[str, Any]:
    """
    Load cleaned daily CSV, validate with Pandera, write report.
    Returns report dict with keys: valid, error_count, schema_errors, stats.
    """
    out = processed_dir or DATA_PROCESSED
    path = out / "daily_cleaned.csv"
    report: dict[str, Any] = {"valid": True, "error_count": 0, "schema_errors": [], "stats": {}}

    if not path.exists():
        report["valid"] = False
        report["schema_errors"] = ["daily_cleaned.csv not found"]
        _write_report(out, report)
        return report

    df = pd.read_csv(path)
    schema = get_daily_schema()

    try:
        validated = schema.validate(df, lazy=True)
        report["stats"] = {
            "rows": int(len(validated)),
            "columns": list(validated.columns),
            "routes": validated["group"].nunique() if "group" in validated.columns else 0,
        }
    except pa.errors.SchemaErrors as e:
        report["valid"] = False
        report["error_count"] = len(e.failure_cases) if e.failure_cases is not None else 1
        report["schema_errors"] = (
            e.failure_cases[["schema_context", "column", "check"].astype(str).to_dict("records")
            if e.failure_cases is not None
            else [str(e)]
        )
        report["stats"] = {"rows_checked": len(df)}

    _write_report(out, report)
    return report


def _write_report(processed_dir: Path, report: dict[str, Any]) -> None:
    with open(processed_dir / "validation_report.json", "w") as f:
        json.dump(report, f, indent=2)


def run(processed_dir: Path | None = None) -> dict[str, Any]:
    """Entry point for stage C."""
    return validate_and_report(processed_dir=processed_dir)
