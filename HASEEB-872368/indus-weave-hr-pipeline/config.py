"""Central settings for the Indus Weave HR pipeline."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_DIR = ROOT / "db"
RESULTS_DIR = ROOT / "analytics" / "results"

PERIOD_START = "2026-04-01"
PERIOD_END = "2026-09-30"
MONTHS = ["2026-04", "2026-05", "2026-06", "2026-07", "2026-08", "2026-09"]

GRACE_MINUTES = 10          # rule 13: late / early threshold
DUP_PUNCH_SECONDS = 120     # rule 9: two punches within 2 minutes = one
DRIFT_THRESHOLD_MIN = 30    # device clock flagged if median check-in offset differs this much
DRIFT_MIN_SAMPLES = 50      # ignore device-months with fewer samples

PLANTS = {
    "HO": "Head Office",
    "KOR": "Korangi Plant",
    "SITE": "SITE Plant",
    "FSD": "Faisalabad Plant",
}

CSV_FILES = [
    "employees", "employment_history", "departments", "shift_roster",
    "device_mapping", "biometric_punches", "holidays",
    "overtime_requests", "payroll_lines", "applications",
]
JSON_FILES = ["shifts", "leave_requests"]


def find_data_dir(cli_arg=None):
    """Find the folder that contains employees.csv."""
    candidates = []
    if cli_arg:
        candidates.append(Path(cli_arg))
    if os.environ.get("HR_DATA_DIR"):
        candidates.append(Path(os.environ["HR_DATA_DIR"]))
    candidates += [ROOT / "data", ROOT, ROOT.parent, Path.cwd()]
    for c in candidates:
        if (c / "employees.csv").exists():
            return c
    raise FileNotFoundError(
        "employees.csv not found. Put the 13 data files in a folder named 'data' next to "
        "run_pipeline.py, or run:  python run_pipeline.py \"C:\\path\\to\\data-hackathon-main\""
    )
