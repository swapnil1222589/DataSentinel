"""Configuration and theme constants for DataSentinel."""

import os
from dataclasses import dataclass, field
from typing import Dict


@dataclass(frozen=True)
class AppConfig:
    """Global configuration settings for DataSentinel."""

    # File ingestion limits
    MAX_UPLOAD_SIZE_BYTES: int = int(os.getenv("DATASENTINEL_MAX_UPLOAD_MB", "100")) * 1024 * 1024
    ALLOWED_EXTENSIONS: tuple = (".csv", ".parquet")

    # Scoring weights (must sum to 1.0)
    DEFAULT_WEIGHTS: Dict[str, float] = field(
        default_factory=lambda: {
            "completeness": 0.35,
            "validity": 0.30,
            "uniqueness": 0.20,
            "consistency": 0.15,
        }
    )

    # Statistical thresholds
    OUTLIER_IQR_FACTOR: float = 1.5
    OUTLIER_ZSCORE_THRESHOLD: float = 3.0
    DRIFT_KS_ALPHA: float = 0.05
    DRIFT_PSI_THRESHOLD: float = 0.2
    HIGH_CARDINALITY_RATIO: float = 0.5
    HIGH_CARDINALITY_MAX_UNIQUE: int = 500

    # UI Theme Palette (Dark Navy / Slate with Vibrant Accents)
    COLOR_PRIMARY: str = "#3B82F6"  # Bright Blue
    COLOR_SECONDARY: str = "#6366F1"  # Indigo
    COLOR_SUCCESS: str = "#10B981"  # Emerald Teal
    COLOR_WARNING: str = "#F59E0B"  # Amber
    COLOR_DANGER: str = "#EF4444"  # Coral Red
    COLOR_INFO: str = "#38BDF8"  # Sky Blue
    COLOR_SURFACE_DARK: str = "#0B111E"  # Deep Navy
    COLOR_SURFACE_CARD: str = "#151F32"  # Card Dark Navy
    COLOR_SURFACE_MUTED: str = "#1E293B"  # Muted Slate
    COLOR_TEXT_PRIMARY: str = "#F8FAFC"  # Crisp White
    COLOR_TEXT_MUTED: str = "#94A3B8"  # Slate Gray
    COLOR_BORDER: str = "#334155"  # Slate Border


CONFIG = AppConfig()
