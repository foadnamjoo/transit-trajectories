"""Pipeline configuration: paths, constants, and run settings."""
from pathlib import Path
from typing import Final

# Repo root (parent of python/)
REPO_ROOT: Final[Path] = Path(__file__).resolve().parent.parent

# Data directories
DATA_RAW: Final[Path] = REPO_ROOT / "data" / "raw"
DATA_INTERIM: Final[Path] = REPO_ROOT / "data" / "interim"
DATA_PROCESSED: Final[Path] = REPO_ROOT / "data" / "processed"
DATA_SERVING: Final[Path] = REPO_ROOT / "data" / "serving"

# Pipeline parameters (keep small for <30s runtime)
NUM_ROUTES: Final[int] = 6
ROUTE_IDS: Final[tuple[str, ...]] = ("Route A", "Route B", "Route C", "Route D", "Route E", "Route F")
NUM_DAYS: Final[int] = 90
SEED: Final[int] = 42

# Canonical units after cleaning
DISTANCE_UNIT: Final[str] = "km"
VOLUME_UNIT: Final[str] = "liters"
TIMEZONE: Final[str] = "UTC"
