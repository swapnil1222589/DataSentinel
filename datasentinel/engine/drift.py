"""Data Drift detection and distribution shift analysis engine."""

from typing import Any, Dict

import numpy as np
import pandas as pd

from datasentinel.core.config import CONFIG


def calculate_psi(
    ref_series: pd.Series,
    curr_series: pd.Series,
    num_bins: int = 10,
) -> float:
    """Calculate Population Stability Index (PSI) between two series.

    PSI < 0.1: No significant distribution change.
    0.1 <= PSI < 0.2: Moderate distribution shift.
    PSI >= 0.2: Significant distribution shift (drift).
    """
    ref_clean = ref_series.dropna()
    curr_clean = curr_series.dropna()

    if len(ref_clean) == 0 or len(curr_clean) == 0:
        return 0.0

    # If numeric, bin using reference quantiles
    if pd.api.types.is_numeric_dtype(ref_clean) and pd.api.types.is_numeric_dtype(curr_clean):
        try:
            percentiles = np.linspace(0, 100, num_bins + 1)
            bins = np.percentile(ref_clean, percentiles)
            bins = np.unique(bins)
            if len(bins) < 2:
                return 0.0
            bins[0] = -np.inf
            bins[-1] = np.inf

            ref_counts, _ = np.histogram(ref_clean, bins=bins)
            curr_counts, _ = np.histogram(curr_clean, bins=bins)
        except Exception:
            return 0.0
    else:
        # Categorical PSI
        all_cats = list(set(ref_clean.astype(str)).union(set(curr_clean.astype(str))))
        ref_counts = np.array([(ref_clean.astype(str) == c).sum() for c in all_cats])
        curr_counts = np.array([(curr_clean.astype(str) == c).sum() for c in all_cats])

    ref_pct = (ref_counts + 1e-4) / (len(ref_clean) + 1e-4 * len(ref_counts))
    curr_pct = (curr_counts + 1e-4) / (len(curr_clean) + 1e-4 * len(curr_counts))

    psi_val = np.sum((curr_pct - ref_pct) * np.log(curr_pct / ref_pct))
    return float(max(0.0, psi_val))


def analyze_column_drift(
    ref_series: pd.Series,
    curr_series: pd.Series,
    col_name: str,
    alpha: float = CONFIG.DRIFT_KS_ALPHA,
    psi_threshold: float = CONFIG.DRIFT_PSI_THRESHOLD,
) -> Dict[str, Any]:
    """Analyze distribution drift for a single column across reference and current datasets."""
    ref_null_pct = ref_series.isna().mean() * 100.0
    curr_null_pct = curr_series.isna().mean() * 100.0
    missing_pct_change = curr_null_pct - ref_null_pct

    ref_valid = ref_series.dropna()
    curr_valid = curr_series.dropna()

    result: Dict[str, Any] = {
        "column": col_name,
        "ref_count": len(ref_series),
        "curr_count": len(curr_series),
        "ref_null_pct": round(ref_null_pct, 2),
        "curr_null_pct": round(curr_null_pct, 2),
        "missing_pct_change": round(missing_pct_change, 2),
        "drift_detected": False,
        "method": "none",
        "statistic": None,
        "p_value": None,
        "psi": None,
        "message": "Insufficient data to evaluate drift.",
    }

    if len(ref_valid) < 5 or len(curr_valid) < 5:
        return result

    # Check if both numeric
    is_ref_num = pd.api.types.is_numeric_dtype(ref_valid)
    is_curr_num = pd.api.types.is_numeric_dtype(curr_valid)

    if is_ref_num and is_curr_num:
        # Use Kolmogorov-Smirnov test
        ks_stat = 0.0
        p_val = 1.0
        try:
            from scipy.stats import ks_2samp

            ks_res = ks_2samp(ref_valid, curr_valid)
            ks_stat = float(ks_res.statistic)
            p_val = float(ks_res.pvalue)
        except Exception:
            # Fallback pure-numpy KS calculation if scipy is unavailable
            combined = np.sort(np.concatenate([ref_valid, curr_valid]))
            cdf_ref = np.searchsorted(np.sort(ref_valid), combined, side="right") / len(ref_valid)
            cdf_curr = np.searchsorted(np.sort(curr_valid), combined, side="right") / len(curr_valid)
            ks_stat = float(np.max(np.abs(cdf_ref - cdf_curr)))
            # Approximate asymptotic p-value
            n_eff = (len(ref_valid) * len(curr_valid)) / (len(ref_valid) + len(curr_valid))
            lambda_val = (np.sqrt(n_eff) + 0.12 + 0.11 / np.sqrt(n_eff)) * ks_stat
            p_val = float(max(0.0, min(1.0, 2.0 * np.exp(-2.0 * lambda_val**2))))

        psi_val = calculate_psi(ref_valid, curr_valid)
        drift_detected = (p_val < alpha) or (psi_val >= psi_threshold)

        ref_mean = float(ref_valid.mean())
        curr_mean = float(curr_valid.mean())
        ref_std = float(ref_valid.std()) if len(ref_valid) > 1 else 0.0
        curr_std = float(curr_valid.std()) if len(curr_valid) > 1 else 0.0

        result.update(
            {
                "inferred_type": "numeric",
                "method": "Kolmogorov-Smirnov (2-Sample) & PSI",
                "statistic": round(ks_stat, 4),
                "p_value": round(p_val, 6),
                "psi": round(psi_val, 4),
                "drift_detected": drift_detected,
                "ref_mean": round(ref_mean, 2),
                "curr_mean": round(curr_mean, 2),
                "mean_shift": round(curr_mean - ref_mean, 2),
                "ref_std": round(ref_std, 2),
                "curr_std": round(curr_std, 2),
                "message": (
                    f"Statistically significant distribution shift detected (p={p_val:.4f} < {alpha}, PSI={psi_val:.3f})."
                    if drift_detected
                    else f"No significant numerical drift detected (p={p_val:.4f}, PSI={psi_val:.3f})."
                ),
            }
        )

    else:
        # Categorical drift using Population Stability Index (PSI)
        psi_val = calculate_psi(ref_valid, curr_valid)
        drift_detected = psi_val >= psi_threshold

        result.update(
            {
                "inferred_type": "categorical",
                "method": "Population Stability Index (PSI)",
                "psi": round(psi_val, 4),
                "drift_detected": drift_detected,
                "message": (
                    f"Significant categorical drift detected (PSI={psi_val:.3f} >= {psi_threshold})."
                    if drift_detected
                    else f"No significant categorical drift (PSI={psi_val:.3f} < {psi_threshold})."
                ),
            }
        )

    return result


def analyze_dataset_drift(
    ref_df: pd.DataFrame,
    curr_df: pd.DataFrame,
    alpha: float = CONFIG.DRIFT_KS_ALPHA,
    psi_threshold: float = CONFIG.DRIFT_PSI_THRESHOLD,
) -> Dict[str, Any]:
    """Perform dataset-level drift and distribution shift analysis across compatible columns."""
    ref_cols = set(ref_df.columns)
    curr_cols = set(curr_df.columns)

    common_cols = sorted(list(ref_cols.intersection(curr_cols)))
    added_cols = sorted(list(curr_cols - ref_cols))
    removed_cols = sorted(list(ref_cols - curr_cols))

    row_count_change = len(curr_df) - len(ref_df)
    row_count_pct_change = (row_count_change / len(ref_df) * 100.0) if len(ref_df) > 0 else 0.0

    columns_analysis = []
    drifted_columns_count = 0

    for col in common_cols:
        col_res = analyze_column_drift(
            ref_df[col], curr_df[col], col, alpha=alpha, psi_threshold=psi_threshold
        )
        columns_analysis.append(col_res)
        if col_res.get("drift_detected", False):
            drifted_columns_count += 1

    summary = {
        "reference_rows": len(ref_df),
        "current_rows": len(curr_df),
        "row_count_change": row_count_change,
        "row_count_pct_change": round(row_count_pct_change, 2),
        "common_columns_count": len(common_cols),
        "added_columns": added_cols,
        "removed_columns": removed_cols,
        "drifted_columns_count": drifted_columns_count,
        "total_analyzed_columns": len(common_cols),
        "columns_analysis": columns_analysis,
        "interpretation_note": (
            "Statistical drift indicates distribution shifts between reference and current datasets. "
            "Drift does not inherently imply model degradation; investigate feature attribution and label relevance."
        ),
    }

    return summary
