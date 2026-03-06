#!/usr/bin/env python3
"""Generate kpis.json, quality.json, forecast.json, anomalies.json from data/serving/*.csv for demo."""
import csv
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERVING = ROOT / "data" / "serving"


def main():
    SERVING.mkdir(parents=True, exist_ok=True)
    kpis = []
    quality = []
    forecast = []
    routes = ["Route A", "Route B", "Route C", "Route D", "Route E", "Route F"]
    for route in routes:
        letter = route.split()[-1].lower()
        path = SERVING / f"route_{letter}.csv"
        if not path.exists():
            continue
        with open(path) as f:
            rows = list(csv.DictReader(f))
        for i, r in enumerate(rows[:90]):  # up to 90 days
            date = r.get("date", "")[:10]
            ridership = int(float(r.get("ridership", 0)))
            on_time = float(r.get("on_time_pct", 0))
            cost = float(r.get("cost_usd", 0))
            fuel = float(r.get("fuel_liters", 0))
            co2 = float(r.get("co2_kg", 0))
            kpis.append({
                "date": date, "route": route, "ridership": ridership, "on_time_pct": round(on_time, 1),
                "cost_usd": round(cost, 2), "fuel_liters": round(fuel, 1), "co2_kg": round(co2, 1),
                "headway_regularity": 0.85,
            })
            # Most scores close to 1 (0.88–1.0), some lower (0.25–0.55) for contrast
            route_idx = ord(letter) - ord("a")
            day_hash = (hash(date) + route_idx * 31) % 100
            if day_hash < 75:  # ~75% of cells: high quality
                comp = 0.90 + (day_hash % 11) / 100.0
                valid = 0.92 + (day_hash % 9) / 100.0
                cons = 0.88 + (day_hash % 13) / 100.0
            else:  # ~25%: lower for heatmap variation
                comp = 0.25 + (day_hash % 35) / 100.0
                valid = 0.30 + (day_hash % 25) / 100.0
                cons = 0.22 + (day_hash % 33) / 100.0
            score = round((comp + valid + cons) / 3, 2)
            quality.append({
                "date": date, "route": route, "completeness": round(comp, 2), "validity": valid, "consistency": round(cons, 2),
                "quality_score": score,
            })
            forecast.append({
                "date": date, "route": route, "ridership_actual": ridership, "ridership_forecast": max(0, ridership + (hash(date) % 100 - 50)),
            })
    # Anomalies: pick a few high-cost or high-ridership days
    anomalies = []
    for r in sorted(kpis, key=lambda x: -x["cost_usd"])[:10]:
        anomalies.append({
            "date": r["date"], "route": r["route"], "ridership": r["ridership"],
            "cost_usd": r["cost_usd"], "anomaly_score": 0.8,
        })
    with open(SERVING / "kpis.json", "w") as f:
        json.dump(kpis, f, indent=0)
    with open(SERVING / "quality.json", "w") as f:
        json.dump(quality, f, indent=0)
    with open(SERVING / "forecast.json", "w") as f:
        json.dump(forecast, f, indent=0)
    with open(SERVING / "anomalies.json", "w") as f:
        json.dump(anomalies, f, indent=0)
    print("Generated kpis.json, quality.json, forecast.json, anomalies.json in data/serving/")


if __name__ == "__main__":
    main()
