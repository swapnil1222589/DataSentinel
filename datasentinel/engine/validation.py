"""Custom domain validation rule engine."""

import re
from typing import List, Tuple

import pandas as pd

from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityDimension
from datasentinel.schemas.rules import RuleEvaluationResult, RuleType, ValidationRule


def evaluate_single_rule(df: pd.DataFrame, rule: ValidationRule) -> RuleEvaluationResult:
    """Evaluate a single user-configured validation rule against a DataFrame safely."""
    if not rule.enabled:
        return RuleEvaluationResult(
            rule=rule,
            passed=True,
            total_evaluated=0,
            violation_count=0,
            violation_percentage=0.0,
            sample_violations=[],
            message="Rule is disabled.",
        )

    col = rule.column
    if col not in df.columns:
        return RuleEvaluationResult(
            rule=rule,
            passed=False,
            total_evaluated=0,
            violation_count=0,
            violation_percentage=0.0,
            sample_violations=[],
            message=f"Column '{col}' does not exist in dataset.",
        )

    series = df[col]
    total_evaluated = len(series)
    violation_mask = pd.Series(False, index=series.index)
    explanation = ""

    if rule.rule_type == RuleType.NOT_NULL:
        violation_mask = series.isna()
        explanation = f"Found null/missing values in column '{col}'."

    elif rule.rule_type == RuleType.UNIQUE:
        # duplicated marks subsequent appearances as duplicates
        violation_mask = series.duplicated(keep="first") & series.notna()
        explanation = f"Found duplicate values in column '{col}'."

    elif rule.rule_type == RuleType.NON_NEGATIVE:
        num_series = pd.to_numeric(series, errors="coerce")
        violation_mask = (num_series < 0) & num_series.notna()
        explanation = f"Found negative numbers in column '{col}'."

    elif rule.rule_type == RuleType.RANGE:
        num_series = pd.to_numeric(series, errors="coerce")
        min_val = rule.params.get("min")
        max_val = rule.params.get("max")
        conditions = []
        if min_val is not None:
            conditions.append(num_series < float(min_val))
        if max_val is not None:
            conditions.append(num_series > float(max_val))

        if conditions:
            violation_mask = conditions[0]
            for c in conditions[1:]:
                violation_mask = violation_mask | c
            violation_mask = violation_mask & num_series.notna()
        explanation = f"Values outside allowed range [{min_val}, {max_val}]."

    elif rule.rule_type == RuleType.ALLOWED_VALUES:
        allowed = rule.params.get("allowed", [])
        # convert to string for robust comparison
        allowed_set = {str(x).strip().lower() for x in allowed}
        str_series = series.dropna().astype(str).str.strip().str.lower()
        invalid_submask = ~str_series.isin(allowed_set)
        violation_mask.loc[series.notna()] = invalid_submask
        explanation = f"Values not in allowed set: {allowed}."

    elif rule.rule_type == RuleType.REGEX_MATCH:
        pattern = rule.params.get("pattern", "")
        if pattern:
            try:
                re.compile(pattern)
                str_series = series.dropna().astype(str)
                invalid_submask = ~str_series.str.match(pattern, na=False)
                violation_mask.loc[series.notna()] = invalid_submask
                explanation = f"Values failing regex pattern '{pattern}'."
            except re.error as err:
                return RuleEvaluationResult(
                    rule=rule,
                    passed=False,
                    total_evaluated=total_evaluated,
                    violation_count=0,
                    violation_percentage=0.0,
                    sample_violations=[],
                    message=f"Invalid regular expression syntax: {err}",
                )

    violation_count = int(violation_mask.sum())
    violation_pct = (violation_count / total_evaluated * 100.0) if total_evaluated > 0 else 0.0
    sample_violations = series[violation_mask].dropna().head(10).tolist()
    passed = violation_count == 0

    return RuleEvaluationResult(
        rule=rule,
        passed=passed,
        total_evaluated=total_evaluated,
        violation_count=violation_count,
        violation_percentage=round(violation_pct, 2),
        sample_violations=sample_violations,
        message="Passed" if passed else (rule.description or explanation),
    )


def evaluate_rules_suite(
    df: pd.DataFrame, rules: List[ValidationRule]
) -> Tuple[List[RuleEvaluationResult], List[IssueFinding]]:
    """Evaluate a suite of user-configured validation rules and produce structured findings."""
    results: List[RuleEvaluationResult] = []
    findings: List[IssueFinding] = []

    for rule in rules:
        if not rule.enabled:
            continue
        eval_res = evaluate_single_rule(df, rule)
        results.append(eval_res)

        if not eval_res.passed:
            severity = IssueSeverity.HIGH if eval_res.violation_percentage > 10.0 else IssueSeverity.MEDIUM
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.VALIDITY,
                    severity=severity,
                    issue_type=f"rule_violation_{rule.rule_type.value}",
                    title=f"Rule violation in '{rule.column}': {rule.description or rule.rule_type.value}",
                    description=(
                        f"{eval_res.violation_count:,} records ({eval_res.violation_percentage:.1f}%) violated "
                        f"rule '{rule.rule_type.value}'. Message: {eval_res.message}"
                    ),
                    column=rule.column,
                    affected_count=eval_res.violation_count,
                    affected_percentage=eval_res.violation_percentage,
                    suggested_action=f"Review and clean non-conforming rows in column '{rule.column}'.",
                    metadata={"sample_violations": [str(x) for x in eval_res.sample_violations[:5]]},
                )
            )

    return results, findings
