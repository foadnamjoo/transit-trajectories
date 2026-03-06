"""Unit tests for stage B cleaning functions."""
import sys
from pathlib import Path

import pandas as pd
import pytest

# Add python dir to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from stage_b_clean import (
    deduplicate,
    fill_missing,
    fix_invalid_ranges,
    standardize_units,
    winsorize_outliers,
)


def test_standardize_units_gallons_to_liters():
    df = pd.DataFrame({
        "fuel_liters": [10.0, 26.4],
        "fuel_unit": ["liters", "gallons"],
        "cost_usd": [100.0],
        "date": ["2025-01-01"],
        "date_iso": ["2025-01-01"],
    })
    out = standardize_units(df)
    assert "fuel_unit" not in out.columns
    assert out["fuel_liters"].iloc[1] == pytest.approx(26.4 * 3.785, rel=1e-2)


def test_fill_missing_ridership():
    df = pd.DataFrame({"ridership": [100, None, 200], "on_time_pct": [90, 90, 90]})
    out = fill_missing(df)
    assert out["ridership"].isna().sum() == 0
    assert out["ridership"].iloc[1] == 150.0  # median of 100, 200


def test_fix_invalid_ranges():
    df = pd.DataFrame({
        "ridership": [-5, 10, 20],
        "on_time_pct": [80, 105, 90],
        "cost_usd": [-1, 5, 10],
    })
    out = fix_invalid_ranges(df)
    assert (out["ridership"] >= 0).all()
    assert (out["on_time_pct"] >= 0).all() and (out["on_time_pct"] <= 100).all()
    assert (out["cost_usd"] >= 0).all()


def test_winsorize_outliers():
    df = pd.DataFrame({"x": [1, 2, 3, 4, 5, 100]})
    out = winsorize_outliers(df, "x", upper_pct=0.99)
    assert out["x"].max() < 100


def test_deduplicate():
    df = pd.DataFrame({"route": ["A", "A", "B"], "date": ["2025-01-01", "2025-01-01", "2025-01-01"], "v": [1, 2, 3]})
    out = deduplicate(df, ["route", "date"])
    assert len(out) == 2
    assert out["v"].iloc[0] == 1  # first kept
