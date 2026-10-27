"""Configurable statistical outlier detection engine (IQR and Z-score)."""

from typing import Any, Dict, List, Tuple

import numpy as np
import pandas as pd

from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityDimension


def detect_outliers_iqr(
    series: pd.Series,
    factor: float = 1.5,
) -> Dict[str, Any]:
    """Detect outliers in a numeric series using the Interquartile Range (Tukey's) method."""
    clean_series = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    n = len(clean_series)
    if n < 4:
        return {
            "method": "iqr",
            "total_evaluated": n,
            "outlier_count": 0,
            "outlier_pct": 0.0,
            "q1": None,
            "median": None,
            "q3": None,
            "iqr": None,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_indices": [],
            "sample_outliers": [],
        }

    q1 = float(clean_series.quantile(0.25))
    median = float(clean_series.median())
    q3 = float(clean_series.quantile(0.75))
    iqr = q3 - q1

    lower_bound = q1 - (factor * iqr)
    upper_bound = q3 + (factor * iqr)

    mask = (clean_series < lower_bound) | (clean_series > upper_bound)
    outlier_count = int(mask.sum())
    outlier_pct = (outlier_count / n * 100.0) if n > 0 else 0.0

    outlier_values = clean_series[mask].tolist()

    return {
        "method": "iqr",
        "factor": factor,
        "total_evaluated": n,
        "outlier_count": outlier_count,
        "outlier_pct": round(outlier_pct, 2),
        "q1": round(q1, 3),
        "median": round(median, 3),
        "q3": round(q3, 3),
        "iqr": round(iqr, 3),
        "lower_bound": round(lower_bound, 3),
        "upper_bound": round(upper_bound, 3),
        "outlier_indices": clean_series[mask].index.tolist()[:100],
        "sample_outliers": [round(float(x), 3) for x in outlier_values[:10]],
    }


def detect_outliers_zscore(
    series: pd.Series,
    threshold: float = 3.0,
) -> Dict[str, Any]:
    """Detect outliers in a numeric series using standard Z-score."""
    clean_series = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    n = len(clean_series)
    if n < 4:
        return {
            "method": "z_score",
            "total_evaluated": n,
            "outlier_count": 0,
            "outlier_pct": 0.0,
            "mean": None,
            "std": None,
            "threshold": threshold,
            "lower_bound": None,
            "upper_bound": None,
            "outlier_indices": [],
            "sample_outliers": [],
        }

    mean = float(clean_series.mean())
    std = float(clean_series.std())

    if std == 0.0 or np.isnan(std):
        return {
            "method": "z_score",
            "total_evaluated": n,
            "outlier_count": 0,
            "outlier_pct": 0.0,
            "mean": round(mean, 3),
            "std": 0.0,
            "threshold": threshold,
            "lower_bound": round(mean, 3),
            "upper_bound": round(mean, 3),
            "outlier_indices": [],
            "sample_outliers": [],
        }

    z_scores = np.abs((clean_series - mean) / std)
    mask = z_scores > threshold

    outlier_count = int(mask.sum())
    outlier_pct = (outlier_count / n * 100.0) if n > 0 else 0.0
    outlier_values = clean_series[mask].tolist()

    lower_bound = mean - (threshold * std)
    upper_bound = mean + (threshold * std)

    return {
        "method": "z_score",
        "threshold": threshold,
        "total_evaluated": n,
        "outlier_count": outlier_count,
        "outlier_pct": round(outlier_pct, 2),
        "mean": round(mean, 3),
        "std": round(std, 3),
        "lower_bound": round(lower_bound, 3),
        "upper_bound": round(upper_bound, 3),
        "outlier_indices": clean_series[mask].index.tolist()[:100],
        "sample_outliers": [round(float(x), 3) for x in outlier_values[:10]],
    }


def analyze_all_numeric_outliers(
    df: pd.DataFrame,
    method: str = "iqr",
    factor: float = 1.5,
    threshold: float = 3.0,
) -> Tuple[Dict[str, Any], List[IssueFinding]]:
    """Scan all numeric columns in dataset for outliers and generate diagnostic findings."""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    results = {}
    findings: List[IssueFinding] = []

    for col in numeric_cols:
        if method == "z_score":
            res = detect_outliers_zscore(df[col], threshold=threshold)
        else:
            res = detect_outliers_iqr(df[col], factor=factor)

        results[col] = res

        if res["outlier_count"] > 0:
            pct = res["outlier_pct"]
            severity = (
                IssueSeverity.HIGH
                if pct > 10.0
                else (IssueSeverity.MEDIUM if pct > 3.0 else IssueSeverity.LOW)
            )
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.VALIDITY,
                    severity=severity,
                    issue_type="numeric_outliers",
                    title=f"{res['outlier_count']:,} outliers detected in '{col}' ({pct:.1f}%)",
                    description=(
                        f"Using {res['method'].upper()} method, detected {res['outlier_count']:,} data points outside "
                        f"normal statistical boundaries [{res['lower_bound']} to {res['upper_bound']}]. "
                        "Note: Outliers represent statistical extremities and are not necessarily errors."
                    ),
                    column=col,
                    affected_count=res["outlier_count"],
                    affected_percentage=pct,
                    suggested_action="Investigate whether these extreme values reflect genuine physical phenomena, measurement errors, or data corruption.",
                    metadata=res,
                )
            )

    return results, findings
