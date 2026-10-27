"""Unit tests for missing value detection engine."""

import numpy as np
import pandas as pd

from datasentinel.engine.missing_values import analyze_missing_values
from datasentinel.schemas.findings import IssueSeverity


def test_no_missing_values():
    df = pd.DataFrame({"a": [1, 2, 3], "b": ["x", "y", "z"]})
    summary, findings = analyze_missing_values(df)
    assert summary["total_missing_cells"] == 0
    assert summary["overall_missing_pct"] == 0.0
    assert summary["columns_with_missing"] == 0
    assert len(findings) == 0


def test_partial_missing_values():
    df = pd.DataFrame(
        {
            "a": [1, np.nan, 3, 4],
            "b": ["x", "y", "z", None],
            "c": [10, 20, 30, 40],
        }
    )
    summary, findings = analyze_missing_values(df)
    assert summary["total_missing_cells"] == 2
    assert summary["overall_missing_pct"] == round((2 / 12) * 100.0, 2)
    assert summary["columns_with_missing"] == 2


def test_completely_empty_column_critical_finding():
    df = pd.DataFrame(
        {
            "valid_col": [1, 2, 3],
            "empty_col": [np.nan, np.nan, np.nan],
        }
    )
    summary, findings = analyze_missing_values(df)
    assert any(
        f.severity == IssueSeverity.CRITICAL and f.issue_type == "completely_empty_column" for f in findings
    )


def test_pseudo_null_detection():
    df = pd.DataFrame(
        {
            "col_with_spaces": ["valid", "   ", "NA", "real_value"],
        }
    )
    summary, findings = analyze_missing_values(df)
    pseudo_findings = [f for f in findings if f.issue_type == "pseudo_null_strings"]
    assert len(pseudo_findings) > 0
    assert pseudo_findings[0].affected_count == 2  # '   ' and 'NA'


def test_empty_dataframe_missing_values():
    df = pd.DataFrame()
    summary, findings = analyze_missing_values(df)
    assert summary["total_cells"] == 0
    assert summary["total_missing_cells"] == 0
    assert len(findings) == 0
