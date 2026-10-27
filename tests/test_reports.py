"""Unit tests for report builder and export formats."""

import json

from datasentinel.engine.report_builder import (
    build_report_data,
    export_csv_issues,
    export_html_report,
    export_json_report,
)
from datasentinel.schemas.findings import (
    DatasetMetadata,
    IssueFinding,
    IssueSeverity,
    QualityDimension,
    QualityScoreResult,
)


def test_report_builder_and_json_export():
    meta = DatasetMetadata(
        filename="test.csv",
        file_size_bytes=1024,
        row_count=100,
        column_count=5,
        memory_usage_bytes=4096,
        column_types={"col1": "int64"},
        created_at="2026-10-27T00:00:00Z",
    )
    qs = QualityScoreResult(
        overall_score=88.5,
        dimension_scores={"completeness": 90.0, "validity": 85.0, "uniqueness": 95.0, "consistency": 84.0},
        dimension_weights={"completeness": 0.35, "validity": 0.3, "uniqueness": 0.2, "consistency": 0.15},
        deductions=[],
        grade="B",
        summary="Good quality",
        methodology_notes="Test notes",
    )
    finding = IssueFinding(
        dimension=QualityDimension.VALIDITY,
        severity=IssueSeverity.MEDIUM,
        issue_type="test_issue",
        title="Sample Issue",
        description="Detail",
        column="col1",
        affected_count=5,
        affected_percentage=5.0,
        suggested_action="Fix it",
    )

    report_dict = build_report_data(
        metadata=meta,
        quality_score=qs,
        findings=[finding],
        missing_summary={"total_cells": 500, "overall_missing_pct": 0.0},
        duplicate_summary={"total_rows": 100, "duplicate_count": 0, "duplicate_pct": 0.0},
        type_summary={},
        outlier_summary={},
    )

    # Test JSON export
    json_str = export_json_report(report_dict)
    parsed = json.loads(json_str)
    assert parsed["metadata"]["filename"] == "test.csv"
    assert parsed["quality_score"]["overall_score"] == 88.5
    assert len(parsed["findings"]) == 1

    # Test CSV export
    csv_str = export_csv_issues([finding])
    assert "MEDIUM" in csv_str
    assert "col1" in csv_str
    assert "Sample Issue" in csv_str

    # Test HTML export
    html_str = export_html_report(report_dict)
    assert "<!DOCTYPE html>" in html_str
    assert "DataSentinel" in html_str
    assert "test.csv" in html_str
    assert "88.5" in html_str
