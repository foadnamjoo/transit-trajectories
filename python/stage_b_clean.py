"""
Stage B: Clean and standardize raw data.

- Normalize units to canonical (liters, km, UTC)
- Handle missing values (drop or impute with justification)
- Deduplicate on (route, date) with stable ordering
- Clip/winsorize outliers and fix invalid ranges
- Output cleaned DataFrames to data/processed/
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

import pandas as pd

from config import DATA_RAW, DATA_PROCESSED, ROUTE_IDS


# Canonical units
GALLONS_TO_LITERS = 3.785411784


def load_raw_daily(raw_dir: Path) -> pd.DataFrame:
    """Load all raw daily CSVs into one DataFrame."""
    all_dfs: list[pd.DataFrame] = []
    for route in ROUTE_IDS:
        letter = route.split()[-1].lower()
        path = raw_dir / f"route_{letter}.csv"
        if not path.exists():
            continue
        df = pd.read_csv(path)
        if "route" not in df.columns and "group" in df.columns:
            df = df.rename(columns={"group": "route"})
        all_dfs.append(df)
    if not all_dfs:
        # Fallback: single file
        p = raw_dir / "daily_all_raw.csv"
        if p.exists():
            return pd.read_csv(p)
        return pd.DataFrame()
    return pd.concat(all_dfs, ignore_index=True)


def standardize_units(df: pd.DataFrame) -> pd.DataFrame:
    """Convert fuel to liters, cost to sensible scale, dates to date-only UTC."""
    df = df.copy()
    if "fuel_unit" in df.columns:
        gallons = df["fuel_unit"].fillna("liters").str.lower().str.strip() == "gallons"
        df.loc[gallons, "fuel_liters"] = (df.loc[gallons, "fuel_liters"] * GALLONS_TO_LITERS).round(2)
        df = df.drop(columns=["fuel_unit"])
    # Cost wrong scale: if median cost > 1000, assume values were stored * 100
    if "cost_usd" in df.columns and df["cost_usd"].median() > 5000:
        df["cost_usd"] = (df["cost_usd"] / 100).round(2)
    # Date: keep YYYY-MM-DD only (drop time/tz)
    if "date_iso" in df.columns:
        df["date"] = pd.to_datetime(df["date_iso"], utc=True).dt.tz_localize(None).dt.strftime("%Y-%m-%d")
        df = df.drop(columns=["date_iso"])
    elif "date" not in df.columns:
        df["date"] = pd.to_datetime(df["date"]).dt.strftime("%Y-%m-%d")
    return df


def fill_missing(df: pd.DataFrame) -> pd.DataFrame:
    """Fill missing values with justified strategy: median for numeric, mode for categorical."""
    df = df.copy()
    if "ridership" in df.columns:
        df["ridership"] = pd.to_numeric(df["ridership"], errors="coerce")
        med = df["ridership"].median()
        if pd.isna(med):
            med = 1000
        df["ridership"] = df["ridership"].fillna(med).astype(int)
    if "on_time_pct" in df.columns:
        df["on_time_pct"] = pd.to_numeric(df["on_time_pct"], errors="coerce")
        df["on_time_pct"] = df["on_time_pct"].fillna(df["on_time_pct"].median()).round(1)
    if "vehicle_type" in df.columns:
        df["vehicle_type"] = df["vehicle_type"].replace("", None).fillna("Hybrid")
    return df


def fix_invalid_ranges(df: pd.DataFrame) -> pd.DataFrame:
    """Clamp ridership to [0, inf), on_time_pct to [0, 100], cost/co2/fuel to non-negative."""
    df = df.copy()
    if "ridership" in df.columns:
        df["ridership"] = df["ridership"].clip(lower=0)
    if "on_time_pct" in df.columns:
        df["on_time_pct"] = df["on_time_pct"].clip(0, 100)
    for col in ("cost_usd", "fuel_liters", "co2_kg"):
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).clip(lower=0)
    return df


def winsorize_outliers(df: pd.DataFrame, column: str, lower_pct: float = 0.01, upper_pct: float = 0.99) -> pd.DataFrame:
    """Winsorize a numeric column to reduce outlier impact."""
    if column not in df.columns:
        return df
    df = df.copy()
    lo = df[column].quantile(lower_pct)
    hi = df[column].quantile(upper_pct)
    df[column] = df[column].clip(lo, hi)
    return df


def deduplicate(df: pd.DataFrame, key_cols: list[str]) -> pd.DataFrame:
    """Keep first occurrence of each key (stable sort)."""
    df = df.sort_values(key_cols).drop_duplicates(subset=key_cols, keep="first").reset_index(drop=True)
    return df


def clean(raw_dir: Path | None = None, processed_dir: Path | None = None) -> pd.DataFrame:
    """
    Run full cleaning: load raw, standardize units, fill missing, fix ranges, winsorize, dedupe.
    Saves to data/processed/ and returns the cleaned DataFrame.
    """
    raw = raw_dir or DATA_RAW
    out = processed_dir or DATA_PROCESSED
    out.mkdir(parents=True, exist_ok=True)

    df = load_raw_daily(raw)
    if df.empty:
        return df

    # Ensure route column
    if "route" not in df.columns and "group" in df.columns:
        df = df.rename(columns={"group": "route"})

    df = standardize_units(df)
    df = fill_missing(df)
    df = fix_invalid_ranges(df)
    df = winsorize_outliers(df, "ridership")
    df = winsorize_outliers(df, "cost_usd")
    df = deduplicate(df, ["route", "date"])

    # Serving schema: date, group, ridership, on_time_pct, day_type, vehicle_type, fuel_liters, cost_usd, co2_kg
    out_cols = ["date", "route", "ridership", "on_time_pct", "day_type", "vehicle_type", "fuel_liters", "cost_usd", "co2_kg"]
    for c in out_cols:
        if c not in df.columns and c == "route" and "group" in df.columns:
            df = df.rename(columns={"group": "route"})
    df = df[[c for c in out_cols if c in df.columns]]
    if "route" in df.columns:
        df = df.rename(columns={"route": "group"})

    df.to_csv(out / "daily_cleaned.csv", index=False)
    for route in ROUTE_IDS:
        g = route.split()[-1].lower()
        subset = df[df["group"] == route]
        if not subset.empty:
            subset.to_csv(out / f"route_{g}.csv", index=False)
    return df


def run(raw_dir: Path | None = None, processed_dir: Path | None = None) -> pd.DataFrame:
    """Entry point for stage B."""
    return clean(raw_dir=raw_dir, processed_dir=processed_dir)
