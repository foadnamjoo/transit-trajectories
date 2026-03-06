"""
Stage A: Generate synthetic transit ops data with intentional data-quality issues.

Produces dirty CSVs in data/raw/ with:
- Missing values (ridership, on_time_pct, vehicle_type)
- Duplicates (same route+date)
- Unit mismatches (some fuel in gallons, some distance in miles)
- Mixed timezones (naive local vs UTC)
- Invalid values (negative ridership, on_time > 100, impossible cost)
- Outliers (occasional spikes)
"""
from __future__ import annotations

import random
from pathlib import Path
from typing import Any

import pandas as pd

from config import (
    DATA_RAW,
    NUM_DAYS,
    NUM_ROUTES,
    ROUTE_IDS,
    SEED,
)


def _seed(route_idx: int, day_idx: int) -> float:
    """Deterministic [0,1) for reproducibility."""
    return (SEED + route_idx * 31 + day_idx * 17) % 1000 / 1000.0


def generate_raw_daily() -> pd.DataFrame:
    """
    Generate one row per route per day with intentional DQ issues.
    Returns a DataFrame with dirty data (missing, wrong units, duplicates, outliers).
    """
    random.seed(SEED)
    rows: list[dict[str, Any]] = []
    base_date = pd.Timestamp("2025-01-01", tz=None)

    for route_idx, route in enumerate(ROUTE_IDS):
        for day_idx in range(NUM_DAYS):
            dt = base_date + pd.Timedelta(days=day_idx)
            r = _seed(route_idx, day_idx)
            day_type = "Weekday" if dt.dayofweek < 5 else "Weekend"
            if day_idx in (10, 40, 70):
                day_type = "Holiday"  # inject a few holidays

            ridership = int(800 + 500 * r + (200 if day_type == "Weekday" else -150))
            on_time = min(99.0, max(75.0, 85.0 + r * 12))
            fuel_liters = round(80 + ridership * 0.04 + r * 15, 1)
            cost_usd = round(120 + fuel_liters * 1.5 + r * 20, 2)
            co2_kg = round(fuel_liters * 2.5, 1)
            vehicle = ["Hybrid", "Diesel", "CNG"][int(r * 3) % 3]

            row: dict[str, Any] = {
                "date": dt.strftime("%Y-%m-%d"),
                "route": route,
                "ridership": ridership,
                "on_time_pct": on_time,
                "day_type": day_type,
                "vehicle_type": vehicle,
                "fuel_liters": fuel_liters,
                "cost_usd": cost_usd,
                "co2_kg": co2_kg,
            }

            # --- Intentional data quality issues ---
            # 1) Missing values (2% of key fields)
            if (route_idx + day_idx) % 50 == 3:
                row["ridership"] = None
            if (route_idx + day_idx) % 47 == 7:
                row["on_time_pct"] = None
            if (route_idx + day_idx) % 43 == 11:
                row["vehicle_type"] = ""

            # 2) Wrong units: sometimes fuel in gallons (≈3.785 L), cost in wrong scale
            row["fuel_unit"] = "liters"
            if day_idx % 11 == 5:
                row["fuel_liters"] = round(fuel_liters / 3.785, 2)  # store as gallons
                row["fuel_unit"] = "gallons"
            if day_idx % 13 == 6:
                row["cost_usd"] = cost_usd * 100  # wrong scale

            # 3) Timezone: record mixed tz for cleaning (optional column)
            row["date_iso"] = dt.strftime("%Y-%m-%d")
            if day_idx % 17 == 8:
                row["date_iso"] = (dt.replace(tzinfo=__import__("datetime").timezone.utc).isoformat())

            # 4) Invalid / impossible values
            if day_idx == 22 and route_idx == 0:
                row["ridership"] = -10
            if day_idx == 33 and route_idx == 1:
                row["on_time_pct"] = 105.0
            if day_idx == 44 and route_idx == 2:
                row["cost_usd"] = -5.0

            # 5) Outliers
            if day_idx == 50 and route_idx == 0:
                row["ridership"] = 5000
            if day_idx == 60 and route_idx == 1:
                row["cost_usd"] = 50000.0

            rows.append(row)

    # 6) Duplicates: add 3% duplicate (route+date) rows
    dup_count = max(1, len(rows) // 33)
    for _ in range(dup_count):
        i = random.randint(0, len(rows) - 1)
        rows.append(rows[i].copy())

    df = pd.DataFrame(rows)
    return df


def run(raw_dir: Path | None = None) -> pd.DataFrame:
    """Generate raw CSVs and return the combined dirty DataFrame."""
    out_dir = raw_dir or DATA_RAW
    out_dir.mkdir(parents=True, exist_ok=True)

    df = generate_raw_daily()

    # Save one CSV per route (raw schema includes fuel_unit, date_iso for cleaning)
    for route in ROUTE_IDS:
        subset = df[df["route"] == route].copy()
        subset = subset.rename(columns={"route": "group"})
        fname = f"route_{route.split()[-1].lower()}.csv"
        subset.to_csv(out_dir / fname, index=False)
    df.to_csv(out_dir / "daily_all_raw.csv", index=False)
    return df
