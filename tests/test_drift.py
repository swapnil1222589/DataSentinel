"""Unit tests for dataset drift and distribution shift engine."""

import numpy as np
import pandas as pd

from datasentinel.engine.drift import analyze_column_drift, analyze_dataset_drift, calculate_psi


def test_identical_datasets_no_drift():
    ref_df = pd.DataFrame(
        {
            "num": [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0, 90.0, 100.0],
            "cat": ["a", "b", "a", "b", "a", "b", "a", "b", "a", "b"],
        }
    )
    curr_df = ref_df.copy()

    drift_res = analyze_dataset_drift(ref_df, curr_df)
    assert drift_res["drifted_columns_count"] == 0
    assert drift_res["row_count_change"] == 0


def test_numeric_distribution_shift_detected():
    np.random.seed(42)
    # Reference centered at 10, current centered at 100
    ref_series = pd.Series(np.random.normal(loc=10.0, scale=2.0, size=100))
    curr_series = pd.Series(np.random.normal(loc=100.0, scale=2.0, size=100))

    res = analyze_column_drift(ref_series, curr_series, "feature_x")
    assert res["drift_detected"] is True
    assert res["p_value"] < 0.05


def test_categorical_psi_shift():
    # Reference is 90% 'A', current is 90% 'B'
    ref_series = pd.Series(["A"] * 90 + ["B"] * 10)
    curr_series = pd.Series(["A"] * 10 + ["B"] * 90)

    psi_val = calculate_psi(ref_series, curr_series)
    assert psi_val > 0.2  # Exceeds standard drift threshold


def test_schema_column_differences():
    ref_df = pd.DataFrame({"col_a": [1, 2, 3], "col_b": [4, 5, 6]})
    curr_df = pd.DataFrame({"col_a": [1, 2, 3], "col_c": [7, 8, 9]})

    res = analyze_dataset_drift(ref_df, curr_df)
    assert "col_c" in res["added_columns"]
    assert "col_b" in res["removed_columns"]
    assert res["common_columns_count"] == 1
