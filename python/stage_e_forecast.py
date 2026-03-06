"""
Stage E: Forecasting and anomaly detection.

- Ridership forecast: seasonal naive (same weekday last week) or simple lag regression
- Anomaly detection: IsolationForest on (ridership, cost) + flag high residuals
- Output: data/serving/forecast.json, data/serving/anomalies.json
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler

from config import DATA_PROCESSED, DATA_SERVING, ROUTE_IDS, SEED


def load_cleaned(processed_dir: Path) -> pd.DataFrame:
    """Load daily_cleaned.csv."""
    path = processed_dir / "daily_cleaned.csv"
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    return df


def forecast_ridership_naive(df: pd.DataFrame) -> list[dict[str, Any]]:
    """Seasonal naive: predict next week = same weekday last week. One record per route/date."""
    if df.empty or len(df) < 7:
        return []
    df = df.sort_values(["group", "date"])
    out: list[dict[str, Any]] = []
    for route in df["group"].unique():
        sub = df[df["group"] == route].sort_values("date")
        for i, row in sub.iterrows():
            d = row["date"]
            lag7 = sub[sub["date"] == d - pd.Timedelta(days=7)]
            pred = int(lag7["ridership"].iloc[0]) if len(lag7) else int(row["ridership"])
            out.append({
                "date": d.strftime("%Y-%m-%d"),
                "route": route,
                "ridership_actual": int(row["ridership"]),
                "ridership_forecast": pred,
            })
    return out


def detect_anomalies(df: pd.DataFrame, contamination: float = 0.05) -> list[dict[str, Any]]:
    """IsolationForest on (ridership, cost_usd). Return list of anomaly records with route, date, score."""
    if df.empty or len(df) < 10:
        return []
    X = df[["ridership", "cost_usd"]].fillna(0).values
    scaler = StandardScaler()
    Xs = scaler.fit_transform(X)
    clf = IsolationForest(random_state=SEED, contamination=contamination)
    pred = clf.fit_predict(Xs)
    score = -clf.score_samples(Xs)  # higher = more anomalous
    df = df.copy()
    df["anomaly"] = pred == -1
    df["anomaly_score"] = score
    anomalies = df[df["anomaly"]].copy()
    anomalies["date"] = pd.to_datetime(anomalies["date"]).dt.strftime("%Y-%m-%d")
    out = anomalies[["date", "group", "ridership", "cost_usd", "anomaly_score"]].rename(columns={"group": "route"}).to_dict(orient="records")
    for r in out:
        r["anomaly_score"] = round(float(r["anomaly_score"]), 4)
    return out


def run(processed_dir: Path | None = None, serving_dir: Path | None = None) -> tuple[list, list]:
    """Run forecast and anomaly detection, write JSON. Returns (forecasts, anomalies)."""
    proc = processed_dir or DATA_PROCESSED
    out = serving_dir or DATA_SERVING
    out.mkdir(parents=True, exist_ok=True)

    df = load_cleaned(proc)
    forecasts = forecast_ridership_naive(df)
    anomalies = detect_anomalies(df)

    with open(out / "forecast.json", "w") as f:
        json.dump(forecasts, f, indent=0)
    with open(out / "anomalies.json", "w") as f:
        json.dump(anomalies, f, indent=0)
    return forecasts, anomalies
