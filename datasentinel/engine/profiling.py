"""Detailed column profiling engine for numeric, categorical, and datetime features."""

from typing import Any, Dict

import pandas as pd

from datasentinel.core.config import CONFIG


def profile_column(series: pd.Series, column_name: str) -> Dict[str, Any]:
    """Generate statistical profile for a given column based on its inferable nature."""
    total_count = len(series)
    null_count = int(series.isna().sum())
    null_pct = (null_count / total_count * 100.0) if total_count > 0 else 0.0
    non_null_series = series.dropna()
    valid_count = len(non_null_series)
    unique_count = int(non_null_series.nunique())

    profile: Dict[str, Any] = {
        "column_name": column_name,
        "total_count": total_count,
        "valid_count": valid_count,
        "null_count": null_count,
        "null_pct": round(null_pct, 2),
        "unique_count": unique_count,
        "raw_dtype": str(series.dtype),
        "inferred_type": "unknown",
        "warnings": [],
    }

    if valid_count == 0:
        profile["inferred_type"] = "empty"
        profile["warnings"].append("Column is 100% missing.")
        return profile

    # Determine if column is datetime or date-like
    is_datetime = pd.api.types.is_datetime64_any_dtype(series)
    if not is_datetime and (series.dtype == object or pd.api.types.is_string_dtype(series)):
        # Attempt sampling to check if datetime
        sample_str = non_null_series.astype(str).head(50)
        # Avoid treating simple short strings or numbers as dates
        if not sample_str.str.isnumeric().all():
            try:
                parsed_dates = pd.to_datetime(sample_str, errors="coerce", format="mixed")
                if parsed_dates.notna().mean() >= 0.8:
                    is_datetime = True
            except Exception:
                pass

    if is_datetime:
        profile["inferred_type"] = "datetime"
        date_series = pd.to_datetime(non_null_series, errors="coerce")
        valid_dates = date_series.dropna()
        invalid_dates_count = valid_count - len(valid_dates)

        if len(valid_dates) > 0:
            profile["min_date"] = str(valid_dates.min())
            profile["max_date"] = str(valid_dates.max())
            profile["date_range_days"] = (valid_dates.max() - valid_dates.min()).days
        else:
            profile["min_date"] = "N/A"
            profile["max_date"] = "N/A"
            profile["date_range_days"] = 0

        profile["invalid_date_count"] = invalid_dates_count
        if invalid_dates_count > 0:
            profile["warnings"].append(
                f"{invalid_dates_count} date-like entries could not be parsed into valid timestamps."
            )
        return profile

    # Determine if column is numeric
    is_numeric = pd.api.types.is_numeric_dtype(series)
    if not is_numeric and (series.dtype == object or pd.api.types.is_string_dtype(series)):
        # Check if numeric stored as string
        sample = non_null_series.astype(str).head(100)
        numeric_sample = pd.to_numeric(sample.str.replace(",", "", regex=False), errors="coerce")
        if numeric_sample.notna().mean() >= 0.9 and not sample.str.isalpha().any():
            is_numeric = True

    if is_numeric:
        num_series = pd.to_numeric(non_null_series, errors="coerce").dropna()
        if len(num_series) > 0:
            profile["inferred_type"] = "numeric"
            profile["mean"] = round(float(num_series.mean()), 3)
            profile["std"] = round(float(num_series.std()), 3) if len(num_series) > 1 else 0.0
            profile["min"] = round(float(num_series.min()), 3)
            profile["q25"] = round(float(num_series.quantile(0.25)), 3)
            profile["median"] = round(float(num_series.median()), 3)
            profile["q75"] = round(float(num_series.quantile(0.75)), 3)
            profile["max"] = round(float(num_series.max()), 3)
            profile["skewness"] = round(float(num_series.skew()), 3) if len(num_series) > 2 else 0.0
            profile["zero_count"] = int((num_series == 0).sum())
            profile["negative_count"] = int((num_series < 0).sum())
            return profile

    # Otherwise treat as categorical / textual
    profile["inferred_type"] = "categorical"
    str_series = non_null_series.astype(str).str.strip()
    val_counts = str_series.value_counts()

    top_n = min(15, len(val_counts))
    top_categories = []
    for cat, cnt in val_counts.head(top_n).items():
        top_categories.append(
            {
                "category": str(cat),
                "count": int(cnt),
                "percentage": round(cnt / valid_count * 100.0, 2),
            }
        )

    profile["top_categories"] = top_categories

    # Check for high cardinality
    cardinality_ratio = unique_count / valid_count if valid_count > 0 else 0.0
    if cardinality_ratio > CONFIG.HIGH_CARDINALITY_RATIO and unique_count > 50:
        profile["warnings"].append(
            f"High cardinality detected ({unique_count:,} unique values, {cardinality_ratio * 100:.1f}% unique ratio). "
            "May represent an ID, key, or unstructured free text."
        )

    return profile


def profile_all_columns(df: pd.DataFrame) -> Dict[str, Dict[str, Any]]:
    """Generate statistical profiles for all columns in DataFrame."""
    return {str(col): profile_column(df[col], str(col)) for col in df.columns}
