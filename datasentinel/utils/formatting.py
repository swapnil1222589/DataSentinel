"""Formatting utilities for numbers, bytes, badges, and scores."""

from typing import Union


def format_number(val: Union[int, float, None]) -> str:
    """Format an integer or float with comma separators."""
    if val is None:
        return "N/A"
    if isinstance(val, int):
        return f"{val:,}"
    if isinstance(val, float):
        if val.is_integer():
            return f"{int(val):,}"
        return f"{val:,.2f}"
    return str(val)


def format_percentage(val: Union[int, float, None], decimals: int = 1) -> str:
    """Format a ratio or percentage value."""
    if val is None:
        return "0.0%"
    return f"{val:.{decimals}f}%"


def format_bytes(size_bytes: Union[int, float, None]) -> str:
    """Format byte size into human readable string (KB, MB, GB)."""
    if size_bytes is None or size_bytes < 0:
        return "0 B"
    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0 or unit == "TB":
            return f"{size_bytes:.1f} {unit}" if unit != "B" else f"{int(size_bytes)} B"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"


def get_score_color(score: float) -> str:
    """Return theme color for a 0-100 quality score."""
    if score >= 90:
        return "#10B981"  # Emerald
    if score >= 75:
        return "#3B82F6"  # Bright Blue
    if score >= 60:
        return "#F59E0B"  # Amber
    return "#EF4444"  # Red


def get_grade_from_score(score: float) -> str:
    """Assign letter grade based on overall quality score."""
    if score >= 95:
        return "A+"
    if score >= 90:
        return "A"
    if score >= 80:
        return "B"
    if score >= 70:
        return "C"
    if score >= 60:
        return "D"
    return "F"


def get_severity_color(severity: str) -> str:
    """Return color for finding severity level."""
    mapping = {
        "critical": "#EF4444",
        "high": "#F97316",
        "medium": "#F59E0B",
        "low": "#3B82F6",
        "info": "#94A3B8",
    }
    return mapping.get(str(severity).lower(), "#94A3B8")
