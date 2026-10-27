"""Transparent, multi-dimensional DataSentinel quality scoring engine."""

from typing import Any, Dict, List, Optional

import pandas as pd

from datasentinel.core.config import CONFIG
from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityScoreResult
from datasentinel.utils.formatting import get_grade_from_score


def calculate_quality_score(
    df: pd.DataFrame,
    findings: List[IssueFinding],
    weights: Optional[Dict[str, float]] = None,
    missing_summary: Optional[Dict[str, Any]] = None,
    duplicate_summary: Optional[Dict[str, Any]] = None,
) -> QualityScoreResult:
    """Calculate deterministic, transparent data quality score (0-100) across 4 dimensions.

    Dimensions:
    - Completeness (default 35%): Measures presence of required values vs missing/pseudo-nulls.
    - Validity (default 30%): Measures adherence to types, ranges, schema constraints, and absence of extreme anomalies.
    - Uniqueness (default 20%): Measures absence of duplicate or redundant records.
    - Consistency (default 15%): Measures internal dataset uniformity, clean strings, absence of zero-variance columns.
    """
    if weights is None:
        weights = CONFIG.DEFAULT_WEIGHTS

    # Normalize weights so they strictly sum to 1.0
    weight_sum = sum(weights.values())
    if weight_sum <= 0:
        norm_weights = CONFIG.DEFAULT_WEIGHTS
    else:
        norm_weights = {k: v / weight_sum for k, v in weights.items()}

    total_rows = len(df)
    total_cols = len(df.columns)

    # Edge case: Empty dataset
    if total_rows == 0 or total_cols == 0:
        return QualityScoreResult(
            overall_score=0.0,
            dimension_scores={"completeness": 0.0, "uniqueness": 0.0, "validity": 0.0, "consistency": 0.0},
            dimension_weights=norm_weights,
            deductions=[
                {"dimension": "all", "reason": "Dataset is empty", "penalty": 100.0, "severity": "critical"}
            ],
            grade="F",
            summary="Dataset contains zero rows or columns.",
            methodology_notes="Empty datasets are automatically scored as 0 across all dimensions.",
        )

    deductions: List[Dict[str, Any]] = []

    # 1. Completeness Score
    missing_pct = missing_summary.get("overall_missing_pct", 0.0) if missing_summary else 0.0
    empty_cols = sum(1 for f in findings if f.issue_type == "completely_empty_column")

    comp_score = 100.0
    if missing_pct > 0:
        comp_penalty = min(80.0, missing_pct * 1.5)
        comp_score -= comp_penalty
        deductions.append(
            {
                "dimension": "completeness",
                "reason": f"Overall missing cell rate of {missing_pct:.1f}%",
                "penalty": round(comp_penalty, 1),
                "severity": "high" if missing_pct > 20 else "medium",
            }
        )

    if empty_cols > 0:
        empty_penalty = min(40.0, empty_cols * 10.0)
        comp_score -= empty_penalty
        deductions.append(
            {
                "dimension": "completeness",
                "reason": f"{empty_cols} completely empty column(s)",
                "penalty": round(empty_penalty, 1),
                "severity": "critical",
            }
        )

    comp_score = max(0.0, min(100.0, comp_score))

    # 2. Uniqueness Score
    dup_pct = duplicate_summary.get("duplicate_pct", 0.0) if duplicate_summary else 0.0
    uniq_score = 100.0
    if dup_pct > 0:
        dup_penalty = min(90.0, dup_pct * 2.5)
        uniq_score -= dup_penalty
        deductions.append(
            {
                "dimension": "uniqueness",
                "reason": f"Duplicate rows rate of {dup_pct:.1f}%",
                "penalty": round(dup_penalty, 1),
                "severity": "high" if dup_pct > 15 else "medium",
            }
        )

    uniq_score = max(0.0, min(100.0, uniq_score))

    # 3. Validity Score
    val_score = 100.0
    rule_violations = [f for f in findings if "rule_violation" in f.issue_type]
    for rv in rule_violations:
        penalty = min(25.0, max(5.0, rv.affected_percentage * 0.4))
        val_score -= penalty
        deductions.append(
            {
                "dimension": "validity",
                "reason": f"Validation rule failure on '{rv.column}': {rv.title}",
                "penalty": round(penalty, 1),
                "severity": rv.severity.value,
            }
        )

    mixed_type_findings = [f for f in findings if f.issue_type == "mixed_data_types"]
    for m in mixed_type_findings:
        val_score -= 8.0
        deductions.append(
            {
                "dimension": "validity",
                "reason": f"Mixed data types in column '{m.column}'",
                "penalty": 8.0,
                "severity": "medium",
            }
        )

    num_text_findings = [f for f in findings if f.issue_type == "numeric_stored_as_text"]
    for n in num_text_findings:
        val_score -= 5.0
        deductions.append(
            {
                "dimension": "validity",
                "reason": f"Numeric column '{n.column}' stored as text string",
                "penalty": 5.0,
                "severity": "medium",
            }
        )

    val_score = max(0.0, min(100.0, val_score))

    # 4. Consistency Score
    cons_score = 100.0
    constant_findings = [f for f in findings if f.issue_type == "constant_column"]
    for c in constant_findings:
        cons_score -= 5.0
        deductions.append(
            {
                "dimension": "consistency",
                "reason": f"Constant column '{c.column}' with zero variance",
                "penalty": 5.0,
                "severity": "low",
            }
        )

    dup_col_findings = [f for f in findings if f.issue_type == "duplicate_columns"]
    for d in dup_col_findings:
        cons_score -= 8.0
        deductions.append(
            {
                "dimension": "consistency",
                "reason": f"Redundant identical columns '{d.column}'",
                "penalty": 8.0,
                "severity": "low",
            }
        )

    whitespace_findings = [f for f in findings if f.issue_type == "untrimmed_whitespace"]
    for w in whitespace_findings:
        cons_score -= 4.0
        deductions.append(
            {
                "dimension": "consistency",
                "reason": f"Untrimmed whitespace in column '{w.column}'",
                "penalty": 4.0,
                "severity": "low",
            }
        )

    cons_score = max(0.0, min(100.0, cons_score))

    # Calculate weighted overall score
    raw_overall = (
        norm_weights["completeness"] * comp_score
        + norm_weights["uniqueness"] * uniq_score
        + norm_weights["validity"] * val_score
        + norm_weights["consistency"] * cons_score
    )

    # Safety Guardrail: If any CRITICAL issue exists, cap maximum overall score to 65.0
    has_critical = any(f.severity == IssueSeverity.CRITICAL for f in findings)
    if has_critical and raw_overall > 65.0:
        deductions.append(
            {
                "dimension": "guardrail",
                "reason": "Overall score capped due to the presence of Critical severity issue(s).",
                "penalty": round(raw_overall - 65.0, 1),
                "severity": "critical",
            }
        )
        overall_score = 65.0
    else:
        overall_score = raw_overall

    grade = get_grade_from_score(overall_score)

    summary = (
        f"DataSentinel Quality Score: {overall_score:.1f}/100 (Grade {grade}). "
        f"Completeness: {comp_score:.1f}, Uniqueness: {uniq_score:.1f}, "
        f"Validity: {val_score:.1f}, Consistency: {cons_score:.1f}."
    )

    methodology = (
        "Quality score is a deterministic DataSentinel heuristic computed across 4 dimensions: "
        f"Completeness ({norm_weights['completeness'] * 100:.0f}%), "
        f"Validity ({norm_weights['validity'] * 100:.0f}%), "
        f"Uniqueness ({norm_weights['uniqueness'] * 100:.0f}%), and "
        f"Consistency ({norm_weights['consistency'] * 100:.0f}%). "
        "Each dimension starts at 100 points with transparent deductions applied for detected anomalies."
    )

    return QualityScoreResult(
        overall_score=round(overall_score, 1),
        dimension_scores={
            "completeness": round(comp_score, 1),
            "uniqueness": round(uniq_score, 1),
            "validity": round(val_score, 1),
            "consistency": round(cons_score, 1),
        },
        dimension_weights=norm_weights,
        deductions=deductions,
        grade=grade,
        summary=summary,
        methodology_notes=methodology,
    )
