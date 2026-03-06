"""
Export processed data to data/serving/ for the web dashboard.

- Copy cleaned route CSVs (route_a.csv … route_f.csv) and route_shapes to serving
- Dashboard loads from data/serving/ (or data/ in demo mode with prebuilt serving)
"""
from __future__ import annotations

import shutil
from pathlib import Path

from config import DATA_PROCESSED, DATA_SERVING, REPO_ROOT, ROUTE_IDS


def export_serving(processed_dir: Path | None = None, serving_dir: Path | None = None) -> None:
    """Copy processed route CSVs and shapes to serving dir."""
    proc = processed_dir or DATA_PROCESSED
    out = serving_dir or DATA_SERVING
    out.mkdir(parents=True, exist_ok=True)

    for route in ROUTE_IDS:
        letter = route.split()[-1].lower()
        src = proc / f"route_{letter}.csv"
        if src.exists():
            shutil.copy2(src, out / f"route_{letter}.csv")

    # Route shapes for map (from existing data or copy from repo data/)
    shapes_src = REPO_ROOT / "data" / "route_shapes.csv"
    if shapes_src.exists():
        shutil.copy2(shapes_src, out / "route_shapes.csv")


def run(processed_dir: Path | None = None, serving_dir: Path | None = None) -> None:
    export_serving(processed_dir=processed_dir, serving_dir=serving_dir)
