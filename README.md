# Transit Ops IQ

**Recruiter-grade portfolio project:** end-to-end data pipeline (dirty data → cleaning → validation → metrics → forecasting & anomaly detection) plus an interactive D3 + Leaflet dashboard that consumes the processed outputs.

---

## What problem it solves

Transit operations teams need to monitor **reliability, cost, and emissions** across routes. Raw data is messy: missing values, wrong units (gallons vs liters, mixed timezones), duplicates, and outliers. This project:

1. **Simulates** realistic dirty transit data (6 routes, 90 days) with intentional data-quality issues.
2. **Cleans and validates** with a Python pipeline (units, missingness, dedup, outlier handling, Pandera schema checks).
3. **Computes KPIs and data-quality scores** per route/day and **forecasts ridership** and **detects anomalies** (IsolationForest).
4. **Serves** a dashboard that visualizes operations, forecast vs actual, and data quality.

---

## Architecture (ASCII)

```
┌─────────────────────────────────────────────────────────────────────────┐
│  data/raw/          (Stage A: synthetic dirty CSVs)                     │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  data/processed/    (Stage B: clean + Stage C: validate → report)       │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  data/serving/      (Stage D: kpis + quality │ Stage E: forecast +       │
│                     anomalies │ export route CSVs + shapes)              │
└──────────────────────────────┬──────────────────────────────────────────┘
                               ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Web dashboard      (D3 + Leaflet)                                       │
│  Tabs: Summary | Forecast | Data Quality                                │
│  Loads: data/serving/*.csv, *.json                                       │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## Pipeline steps

| Stage | Script | Input | Output |
|-------|--------|--------|--------|
| **A** | `python/stage_a_generate.py` | — | `data/raw/route_*.csv`, `daily_all_raw.csv` |
| **B** | `python/stage_b_clean.py` | raw | `data/processed/daily_cleaned.csv`, `route_*.csv` |
| **C** | `python/stage_c_validate.py` | processed | `data/processed/validation_report.json` |
| **D** | `python/stage_d_metrics.py` | processed | `data/serving/kpis.json`, `quality.json` |
| **E** | `python/stage_e_forecast.py` | processed | `data/serving/forecast.json`, `anomalies.json` |
| **Export** | `python/export_serving.py` | processed + repo data | `data/serving/route_*.csv`, `route_shapes.csv` |

---

## Data quality issues simulated (and how fixed)

| Issue | In raw data | Fix (Stage B) |
|-------|-------------|----------------|
| **Missing values** | 2% ridership, on_time_pct, vehicle_type | Median impute (numeric), mode "Hybrid" (categorical) |
| **Wrong units** | Some fuel in gallons, cost ×100 | Convert gallons→liters; detect cost scale and divide by 100 |
| **Mixed timezones** | Some rows with ISO timestamps | Normalize to date-only (UTC) |
| **Invalid ranges** | Negative ridership, on_time > 100, negative cost | Clip to valid ranges |
| **Outliers** | Spikes in ridership/cost | Winsorize at 1st/99th percentile |
| **Duplicates** | ~3% duplicate (route, date) | Deduplicate on (route, date), keep first |

---

## How to run

### One-command demo (pipeline + local server)

```bash
make demo
```

Runs the full pipeline then starts a static server at **http://localhost:8080**. Open the app and use **View** → Summary, Forecast, Data Quality.

### Pipeline only (no server)

```bash
make pipeline
```

Or:

```bash
python python/run_pipeline.py
```

Outputs go to `data/serving/`. Serve the repo root with any static server to view the dashboard.

### Demo mode (prebuilt data, e.g. GitHub Pages)

Prebuilt files in `data/serving/` (route CSVs, route_shapes.csv, kpis.json, quality.json, forecast.json, anomalies.json) are committed so the dashboard works without running the pipeline. To regenerate them:

```bash
python scripts/generate_serving_json.py   # from existing data/serving/*.csv
# or
make pipeline                             # full pipeline from raw → serving
```

Then:

```bash
make serve
```

### Tests

```bash
make test
```

or:

```bash
python -m pytest tests/ -v
```

Tests cover **cleaning** (unit conversion, missing fill, invalid ranges, winsorize, dedupe) and **validation** (Pandera schema: types, ranges, allowed categories).

### Lint / CI

```bash
make lint
```

CI (`.github/workflows/ci.yml`) runs on push/PR: install deps, compile Python, run pipeline, run pytest.

---

## Project structure

```
├── index.html              # Dashboard entry
├── script.js               # D3 charts, Leaflet map, tabs, KPI/forecast/quality views
├── style.css               # Styles
├── Makefile                # demo | pipeline | serve | test | lint
├── requirements.txt        # pandas, numpy, scikit-learn, pandera, pytest
├── data/
│   ├── raw/                # Stage A output (dirty)
│   ├── interim/            # (optional)
│   ├── processed/          # Stage B+C output (cleaned + validation_report.json)
│   └── serving/            # Stage D+E+export (CSVs + kpis, quality, forecast, anomalies)
├── python/
│   ├── config.py           # Paths, constants
│   ├── stage_a_generate.py # Synthetic dirty data
│   ├── stage_b_clean.py    # Clean + standardize
│   ├── stage_c_validate.py # Pandera schema + report
│   ├── stage_d_metrics.py  # KPIs + quality scores
│   ├── stage_e_forecast.py # Forecast + IsolationForest anomalies
│   ├── export_serving.py   # Copy to serving
│   └── run_pipeline.py     # Run all stages
├── scripts/
│   └── generate_serving_json.py  # Prebuild kpis/quality/forecast/anomalies from CSVs
├── tests/
│   ├── test_cleaning.py    # Unit tests for Stage B
│   └── test_validation.py  # Schema tests for Stage C
└── .github/workflows/
    └── ci.yml              # Lint + pipeline + pytest
```

---

## Project story (for recruiters)

- **Data engineering:** Raw → cleaned → validated → serving with clear stages, schema validation (Pandera), and documented data-quality issues and fixes.
- **Data science:** KPI and quality scoring, ridership forecasting (seasonal naive), and anomaly detection (IsolationForest) with outputs consumed by the dashboard.
- **Visualization:** Single-page dashboard (D3) with Summary (KPI cards + charts + fleet), Forecast (actual vs forecast + anomaly list), and Data Quality (heatmap).

---

## Screenshots / GIF

1. **Summary:** KPI cards at top; 2×2 charts (histogram, line, time series, scatter); fleet section (emissions over time, cost by route, vehicle type).
2. **Forecast:** Line chart (actual vs forecast) and bullet list of anomalies.
3. **Data Quality:** Table heatmap of quality score by route and date (green = high, red = low).

To record a GIF: run `make demo`, open Summary → change Route → open Forecast → open Data Quality.

---

## Author

**Foad Namjoo** · [Personal Webpage](https://users.cs.utah.edu/~foad27/)
