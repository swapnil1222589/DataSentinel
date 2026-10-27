"""Missing-value analysis engine and finding generators."""

from typing import Any, Dict, List, Tuple

import pandas as pd

from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityDimension

# Strings commonly representing disguised missing data
PSEUDO_NULL_STRINGS = {"", " ", "null", "none", "na", "n/a", "nan", "--", "?", "missing"}


def analyze_missing_values(df: pd.DataFrame) -> Tuple[Dict[str, Any], List[IssueFinding]]:
    """Compute detailed column-level and dataset-level missingness metrics.

    Returns:
        (summary_metrics_dict, list_of_findings)
    """
    total_rows = len(df)
    total_columns = len(df.columns)
    total_cells = total_rows * total_columns

    if total_rows == 0 or total_columns == 0:
        summary = {
            "total_cells": 0,
            "total_missing_cells": 0,
            "overall_missing_pct": 0.0,
            "columns_with_missing": 0,
            "column_metrics": [],
        }
        return summary, []

    # Standard pandas missing check (NaN/None/pd.NA)
    null_counts = df.isna().sum()

    # Check for pseudo-null empty strings in object/string columns
    pseudo_null_counts = {}
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            # Stringified check stripped and lowered
            series_str = df[col].dropna().astype(str).str.strip().str.lower()
            pseudo_count = int(series_str.isin(PSEUDO_NULL_STRINGS).sum())
            if pseudo_count > 0:
                pseudo_null_counts[col] = pseudo_count

    total_missing_cells = int(null_counts.sum())
    overall_missing_pct = (total_missing_cells / total_cells * 100.0) if total_cells > 0 else 0.0

    column_metrics = []
    findings: List[IssueFinding] = []

    for col in df.columns:
        raw_nulls = int(null_counts[col])
        null_pct = (raw_nulls / total_rows * 100.0) if total_rows > 0 else 0.0
        pseudo_count = pseudo_null_counts.get(col, 0)
        combined_missing = raw_nulls + pseudo_count
        combined_pct = (combined_missing / total_rows * 100.0) if total_rows > 0 else 0.0

        column_metrics.append(
            {
                "column": col,
                "missing_count": raw_nulls,
                "missing_pct": round(null_pct, 2),
                "pseudo_null_count": pseudo_count,
                "combined_missing_count": combined_missing,
                "combined_missing_pct": round(combined_pct, 2),
                "dtype": str(df[col].dtype),
            }
        )

        # Generate findings based on severity thresholds
        if raw_nulls == total_rows:
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.COMPLETENESS,
                    severity=IssueSeverity.CRITICAL,
                    issue_type="completely_empty_column",
                    title=f"Column '{col}' is entirely empty",
                    description=f"Column '{col}' contains 100% missing values across all {total_rows} rows.",
                    column=col,
                    affected_count=raw_nulls,
                    affected_percentage=100.0,
                    suggested_action=f"Consider dropping column '{col}' as it provides zero variance or informational value.",
                )
            )
        elif null_pct >= 50.0:
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.COMPLETENESS,
                    severity=IssueSeverity.HIGH,
                    issue_type="high_missingness",
                    title=f"Critical missing rate in '{col}'",
                    description=f"{raw_nulls:,} rows ({null_pct:.1f}%) have missing values.",
                    column=col,
                    affected_count=raw_nulls,
                    affected_percentage=null_pct,
                    suggested_action=f"Evaluate whether imputation is scientifically valid or if '{col}' should be dropped.",
                )
            )
        elif null_pct >= 20.0:
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.COMPLETENESS,
                    severity=IssueSeverity.MEDIUM,
                    issue_type="moderate_missingness",
                    title=f"Moderate missing values in '{col}'",
                    description=f"{raw_nulls:,} rows ({null_pct:.1f}%) are missing.",
                    column=col,
                    affected_count=raw_nulls,
                    affected_percentage=null_pct,
                    suggested_action="Apply median/mode imputation or model-based imputation depending on feature importance.",
                )
            )
        elif raw_nulls > 0:
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.COMPLETENESS,
                    severity=IssueSeverity.LOW,
                    issue_type="minor_missingness",
                    title=f"Occasional missing values in '{col}'",
                    description=f"{raw_nulls:,} rows ({null_pct:.1f}%) are null.",
                    column=col,
                    affected_count=raw_nulls,
                    affected_percentage=null_pct,
                    suggested_action="Review data collection pipeline or impute using standard strategies.",
                )
            )

        if pseudo_count > 0:
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.COMPLETENESS,
                    severity=IssueSeverity.MEDIUM,
                    issue_type="pseudo_null_strings",
                    title=f"Whitespace or placeholder null strings in '{col}'",
                    description=f"Found {pseudo_count} text cells containing placeholder null values (e.g., whitespace, 'N/A', 'null').",
                    column=col,
                    affected_count=pseudo_count,
                    affected_percentage=(pseudo_count / total_rows * 100.0),
                    suggested_action="Standardize empty strings and placeholders to proper null representations (NaN).",
                )
            )

    # Sort column metrics descending by missing percentage
    column_metrics.sort(key=lambda x: x["missing_pct"], reverse=True)

    summary = {
        "total_cells": total_cells,
        "total_missing_cells": total_missing_cells,
        "overall_missing_pct": round(overall_missing_pct, 2),
        "columns_with_missing": sum(1 for c in column_metrics if c["missing_count"] > 0),
        "column_metrics": column_metrics,
    }

    return summary, findings
