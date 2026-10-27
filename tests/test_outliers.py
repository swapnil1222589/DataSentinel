"""Unit tests for statistical outlier detection."""

import pandas as pd

from datasentinel.engine.outliers import (
    analyze_all_numeric_outliers,
    detect_outliers_iqr,
    detect_outliers_zscore,
)


def test_iqr_outlier_detection():
    # Normal points around 10-20, with extreme outlier 1000
    series = pd.Series([10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 1000])
    res = detect_outliers_iqr(series, factor=1.5)
    assert res["outlier_count"] == 1
    assert 1000 in res["sample_outliers"]


def test_zscore_outlier_detection():
    # 50 points centered at 0, plus point at 100
    data = [0.0] * 50 + [100.0]
    series = pd.Series(data)
    res = detect_outliers_zscore(series, threshold=3.0)
    assert res["outlier_count"] >= 1
    assert 100.0 in res["sample_outliers"]


def test_constant_series_outlier_handling():
    series = pd.Series([5.0, 5.0, 5.0, 5.0, 5.0])
    res_iqr = detect_outliers_iqr(series)
    res_z = detect_outliers_zscore(series)
    assert res_iqr["outlier_count"] == 0
    assert res_z["outlier_count"] == 0


def test_analyze_all_numeric_outliers():
    df = pd.DataFrame(
        {
            "num_col": [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 500],
            "cat_col": ["a", "b", "c", "d", "e", "f", "g", "h", "i", "j", "k"],
        }
    )
    results, findings = analyze_all_numeric_outliers(df)
    assert "num_col" in results
    assert "cat_col" not in results
    assert len(findings) == 1
