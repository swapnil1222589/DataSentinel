"""Schemas for custom validation rules and evaluation results."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class RuleType(str, Enum):
    """Supported custom validation rule types."""

    RANGE = "range"
    NON_NEGATIVE = "non_negative"
    NOT_NULL = "not_null"
    UNIQUE = "unique"
    ALLOWED_VALUES = "allowed_values"
    REGEX_MATCH = "regex_match"


@dataclass
class ValidationRule:
    """Definition of a user-configurable validation rule."""

    id: str
    column: str
    rule_type: RuleType
    params: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True
    description: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert rule definition to dictionary."""
        return {
            "id": self.id,
            "column": self.column,
            "rule_type": self.rule_type.value,
            "params": self.params,
            "enabled": self.enabled,
            "description": self.description,
        }


@dataclass
class RuleEvaluationResult:
    """Result of evaluating a single validation rule against a dataset."""

    rule: ValidationRule
    passed: bool
    total_evaluated: int
    violation_count: int
    violation_percentage: float
    sample_violations: List[Any] = field(default_factory=list)
    message: str = ""

    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation result to dictionary."""
        return {
            "rule_id": self.rule.id,
            "column": self.rule.column,
            "rule_type": self.rule.rule_type.value,
            "description": self.rule.description,
            "passed": self.passed,
            "total_evaluated": self.total_evaluated,
            "violation_count": self.violation_count,
            "violation_percentage": round(self.violation_percentage, 2),
            "sample_violations": [str(x) for x in self.sample_violations[:5]],
            "message": self.message,
        }
