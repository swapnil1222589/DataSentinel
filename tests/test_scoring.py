"""Unit tests for transparent quality scoring engine."""

import pandas as pd

from datasentinel.engine.scoring import calculate_quality_score
from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityDimension


def test_perfect_dataset_score():
    df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    res = calculate_quality_score(df, findings=[])
    assert res.overall_score == 100.0
    assert res.grade == "A+"
    assert len(res.deductions) == 0


def test_empty_dataset_score():
    df = pd.DataFrame()
    res = calculate_quality_score(df, findings=[])
    assert res.overall_score == 0.0
    assert res.grade == "F"


def test_critical_issue_guardrail_cap():
    df = pd.DataFrame({"id": [1, 2, 3], "data": ["x", "y", "z"]})
    critical_finding = IssueFinding(
        dimension=QualityDimension.COMPLETENESS,
        severity=IssueSeverity.CRITICAL,
        issue_type="completely_empty_column",
        title="Column is empty",
        description="100% missing",
        column="empty_col",
        affected_count=3,
        affected_percentage=100.0,
    )
    # Even if other metrics are good, critical issue caps score at 65.0
    res = calculate_quality_score(df, findings=[critical_finding])
    assert res.overall_score <= 65.0
    assert any("guardrail" in d.get("dimension", "") for d in res.deductions)


def test_custom_dimension_weights():
    df = pd.DataFrame({"id": [1, 2], "val": [10, 20]})
    # 100% completeness weight
    weights = {"completeness": 1.0, "validity": 0.0, "uniqueness": 0.0, "consistency": 0.0}
    missing_summary = {"overall_missing_pct": 20.0}
    res = calculate_quality_score(df, findings=[], weights=weights, missing_summary=missing_summary)
    # 100 - (20 * 1.5) = 70.0
    assert res.overall_score == 70.0
