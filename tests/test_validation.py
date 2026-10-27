"""Unit tests for custom domain validation rules."""

import pandas as pd

from datasentinel.engine.validation import evaluate_single_rule
from datasentinel.schemas.rules import RuleType, ValidationRule


def test_range_rule():
    df = pd.DataFrame({"score": [85, 92, 105, 78, -10]})
    rule = ValidationRule(
        id="r1",
        column="score",
        rule_type=RuleType.RANGE,
        params={"min": 0, "max": 100},
    )
    res = evaluate_single_rule(df, rule)
    assert not res.passed
    assert res.violation_count == 2  # 105 and -10


def test_non_negative_rule():
    df = pd.DataFrame({"age": [25, 30, -5, 40]})
    rule = ValidationRule(id="r2", column="age", rule_type=RuleType.NON_NEGATIVE)
    res = evaluate_single_rule(df, rule)
    assert not res.passed
    assert res.violation_count == 1
    assert -5 in res.sample_violations


def test_not_null_rule():
    df = pd.DataFrame({"name": ["Alice", None, "Charlie"]})
    rule = ValidationRule(id="r3", column="name", rule_type=RuleType.NOT_NULL)
    res = evaluate_single_rule(df, rule)
    assert not res.passed
    assert res.violation_count == 1


def test_unique_rule():
    df = pd.DataFrame({"id": ["A01", "A02", "A01", "A03"]})
    rule = ValidationRule(id="r4", column="id", rule_type=RuleType.UNIQUE)
    res = evaluate_single_rule(df, rule)
    assert not res.passed
    assert res.violation_count == 1


def test_allowed_values_rule():
    df = pd.DataFrame({"tier": ["Gold", "Silver", "Diamond", "Bronze"]})
    rule = ValidationRule(
        id="r5",
        column="tier",
        rule_type=RuleType.ALLOWED_VALUES,
        params={"allowed": ["Gold", "Silver", "Bronze"]},
    )
    res = evaluate_single_rule(df, rule)
    assert not res.passed
    assert res.violation_count == 1
    assert "Diamond" in res.sample_violations


def test_regex_rule():
    df = pd.DataFrame({"code": ["AB-1234", "XY-9999", "INVALID", "CD-5678"]})
    rule = ValidationRule(
        id="r6",
        column="code",
        rule_type=RuleType.REGEX_MATCH,
        params={"pattern": r"^[A-Z]{2}-\d{4}$"},
    )
    res = evaluate_single_rule(df, rule)
    assert not res.passed
    assert res.violation_count == 1
    assert "INVALID" in res.sample_violations


def test_disabled_rule_skipped():
    df = pd.DataFrame({"age": [-10, -20]})
    rule = ValidationRule(id="r7", column="age", rule_type=RuleType.NON_NEGATIVE, enabled=False)
    res = evaluate_single_rule(df, rule)
    assert res.passed
    assert res.violation_count == 0
