from __future__ import annotations

import os
from pathlib import Path

APP_NAME = "Privacy Notice Reviewer"
PRIMARY_LAW = "UU No. 27 Tahun 2022 tentang Pelindungan Data Pribadi"
JURISDICTION = "Indonesia"
DEFAULT_EFFECTIVE_DATE = "2022-10-17"

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PROJECT_ROOT / "data"
OUTPUTS_DIR = PROJECT_ROOT / "outputs"
LEGAL_SOURCE_DIR = DATA_DIR / "legal_sources" / "uu_pdp_27_2022"
PROCESSED_DIR = DATA_DIR / "processed"
CONTROL_MATRIX_PATH = LEGAL_SOURCE_DIR / "legal_control_matrix_uu_pdp.csv"


def env_bool(name: str, default: bool = False) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def retention_days() -> int:
    value = os.getenv("CLIENT_DATA_RETENTION_DAYS", "30")
    try:
        return max(0, int(value))
    except ValueError:
        return 30

