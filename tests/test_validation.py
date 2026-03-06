"""Unit tests for stage C schema validation."""
import sys
from pathlib import Path

import pandas as pd
import pandera as pa
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "python"))

from stage_c_validate import get_daily_schema


def test_schema_accepts_valid_row():
    schema = get_daily_schema()
    df = pd.DataFrame([{
        "date": "2025-01-01",
        "group": "Route A",
        "ridership": 1000,
        "on_time_pct": 88.5,
        "day_type": "Weekday",
        "vehicle_type": "Hybrid",
        "fuel_liters": 95.0,
        "cost_usd": 200.0,
        "co2_kg": 152.0,
    }])
    validated = schema.validate(df)
    assert len(validated) == 1
    assert validated["ridership"].iloc[0] == 1000


def test_schema_rejects_invalid_ridership():
    schema = get_daily_schema()
    df = pd.DataFrame([{
        "date": "2025-01-01",
        "group": "Route A",
        "ridership": -1,
        "on_time_pct": 88.0,
        "day_type": "Weekday",
        "vehicle_type": "Hybrid",
        "fuel_liters": 95.0,
        "cost_usd": 200.0,
        "co2_kg": 152.0,
    }])
    with pytest.raises(pa.errors.SchemaError):
        schema.validate(df)


def test_schema_rejects_invalid_route():
    schema = get_daily_schema()
    df = pd.DataFrame([{
        "date": "2025-01-01",
        "group": "Route X",
        "ridership": 1000,
        "on_time_pct": 88.0,
        "day_type": "Weekday",
        "vehicle_type": "Hybrid",
        "fuel_liters": 95.0,
        "cost_usd": 200.0,
        "co2_kg": 152.0,
    }])
    with pytest.raises(pa.errors.SchemaError):
        schema.validate(df)
