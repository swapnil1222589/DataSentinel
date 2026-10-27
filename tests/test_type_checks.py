"""Unit tests for type integrity and dataset consistency checks."""

import pandas as pd

from datasentinel.engine.type_checks import analyze_types_and_consistency


def test_constant_column():
    df = pd.DataFrame(
        {
            "status": ["active", "active", "active", "active"],
            "age": [20, 25, 30, 35],
        }
    )
    summary, findings = analyze_types_and_consistency(df)
    assert len(summary["constant_columns"]) == 1
    assert summary["constant_columns"][0]["column"] == "status"
    assert any(f.issue_type == "constant_column" for f in findings)


def test_numeric_stored_as_text():
    df = pd.DataFrame(
        {
            "amount_str": ["100.5", "200", "350.25", "500", "120"],
        }
    )
    summary, findings = analyze_types_and_consistency(df)
    assert len(summary["numeric_stored_as_text"]) == 1
    assert any(f.issue_type == "numeric_stored_as_text" for f in findings)


def test_untrimmed_whitespace():
    df = pd.DataFrame(
        {
            "category": [" Tech", "Finance ", " Tech", "Healthcare"],
        }
    )
    summary, findings = analyze_types_and_consistency(df)
    assert len(summary["whitespace_issues"]) == 1
    assert any(f.issue_type == "untrimmed_whitespace" for f in findings)


def test_duplicate_columns():
    df = pd.DataFrame(
        {
            "price_usd": [10, 20, 30],
            "cost_usd": [10, 20, 30],
            "quantity": [1, 2, 3],
        }
    )
    summary, findings = analyze_types_and_consistency(df)
    assert len(summary["duplicate_columns"]) == 1
    assert any(f.issue_type == "duplicate_columns" for f in findings)
