"""Duplicate row detection and deduplication generator."""

from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityDimension


def analyze_duplicates(
    df: pd.DataFrame,
    subset_columns: Optional[List[str]] = None,
) -> Tuple[Dict[str, Any], List[IssueFinding]]:
    """Analyze exact or subset-based duplicate records.

    Returns:
        (duplicate_metrics_dict, list_of_findings)
    """
    total_rows = len(df)
    if total_rows == 0:
        return {
            "total_rows": 0,
            "duplicate_count": 0,
            "duplicate_pct": 0.0,
            "subset_columns": subset_columns or [],
            "sample_duplicates": pd.DataFrame(),
        }, []

    valid_subset = None
    if subset_columns:
        valid_subset = [c for c in subset_columns if c in df.columns]
        if not valid_subset:
            valid_subset = None

    # Identify duplicates (keep=False marks all duplicate instances for inspection)
    duplicate_mask_all = df.duplicated(subset=valid_subset, keep=False)
    # Marks rows that would be dropped (keep='first')
    duplicate_mask_redundant = df.duplicated(subset=valid_subset, keep="first")

    duplicate_count = int(duplicate_mask_redundant.sum())
    duplicate_pct = (duplicate_count / total_rows * 100.0) if total_rows > 0 else 0.0

    # Extract sample duplicates for user inspection
    sample_df = df[duplicate_mask_all].head(20)

    findings: List[IssueFinding] = []

    if duplicate_count > 0:
        severity = (
            IssueSeverity.HIGH
            if duplicate_pct > 15.0
            else (IssueSeverity.MEDIUM if duplicate_pct > 2.0 else IssueSeverity.LOW)
        )
        col_desc = (
            f"across subset columns ({', '.join(valid_subset)})" if valid_subset else "across all columns"
        )

        findings.append(
            IssueFinding(
                dimension=QualityDimension.UNIQUENESS,
                severity=severity,
                issue_type="duplicate_rows",
                title=f"Detected {duplicate_count:,} duplicate records ({duplicate_pct:.1f}%)",
                description=(
                    f"Found {duplicate_count:,} redundant rows {col_desc}. "
                    "Unintended duplicates can bias model training and inflate analytics."
                ),
                column=", ".join(valid_subset) if valid_subset else "Entire Row",
                affected_count=duplicate_count,
                affected_percentage=duplicate_pct,
                suggested_action=(
                    "Inspect the duplicate rows in Dataset Explorer or Quality Analysis, and download "
                    "a deduplicated dataset if these represent data collection duplicates."
                ),
                metadata={"subset": valid_subset or "all"},
            )
        )

    summary = {
        "total_rows": total_rows,
        "duplicate_count": duplicate_count,
        "duplicate_pct": round(duplicate_pct, 2),
        "subset_columns": valid_subset or [],
        "sample_duplicates": sample_df,
    }

    return summary, findings


def generate_deduplicated_dataset(
    df: pd.DataFrame,
    subset_columns: Optional[List[str]] = None,
    keep: str = "first",
) -> Tuple[pd.DataFrame, int]:
    """Return a deduplicated copy of DataFrame without mutating the original.

    Returns:
        (cleaned_df, removed_count)
    """
    valid_subset = None
    if subset_columns:
        valid_subset = [c for c in subset_columns if c in df.columns]
        if not valid_subset:
            valid_subset = None

    cleaned_df = df.drop_duplicates(subset=valid_subset, keep=keep).copy()
    removed_count = len(df) - len(cleaned_df)
    return cleaned_df, removed_count
