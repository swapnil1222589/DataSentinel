"""Schemas for data quality findings, scoring results, and dataset metadata."""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional


class IssueSeverity(str, Enum):
    """Severity levels for data quality findings."""

    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


class QualityDimension(str, Enum):
    """Core dimensions of data quality."""

    COMPLETENESS = "completeness"
    UNIQUENESS = "uniqueness"
    VALIDITY = "validity"
    CONSISTENCY = "consistency"


@dataclass
class IssueFinding:
    """Represents an individual detected data quality issue."""

    dimension: QualityDimension
    severity: IssueSeverity
    issue_type: str
    title: str
    description: str
    column: Optional[str] = None
    affected_count: int = 0
    affected_percentage: float = 0.0
    suggested_action: str = ""
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert finding to dictionary representation."""
        return {
            "dimension": self.dimension.value,
            "severity": self.severity.value,
            "issue_type": self.issue_type,
            "title": self.title,
            "description": self.description,
            "column": self.column or "N/A",
            "affected_count": self.affected_count,
            "affected_percentage": round(self.affected_percentage, 2),
            "suggested_action": self.suggested_action,
            "metadata": self.metadata,
        }


@dataclass
class QualityScoreResult:
    """Detailed transparent quality scoring results."""

    overall_score: float
    dimension_scores: Dict[str, float]
    dimension_weights: Dict[str, float]
    deductions: List[Dict[str, Any]]
    grade: str
    summary: str
    methodology_notes: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert quality score to dictionary representation."""
        return {
            "overall_score": round(self.overall_score, 1),
            "dimension_scores": {k: round(v, 1) for k, v in self.dimension_scores.items()},
            "dimension_weights": self.dimension_weights,
            "deductions": self.deductions,
            "grade": self.grade,
            "summary": self.summary,
            "methodology_notes": self.methodology_notes,
        }


@dataclass
class DatasetMetadata:
    """Metadata regarding an uploaded and processed dataset."""

    filename: str
    file_size_bytes: int
    row_count: int
    column_count: int
    memory_usage_bytes: int
    column_types: Dict[str, str]
    created_at: str

    def to_dict(self) -> Dict[str, Any]:
        """Convert metadata to dictionary representation."""
        return {
            "filename": self.filename,
            "file_size_bytes": self.file_size_bytes,
            "row_count": self.row_count,
            "column_count": self.column_count,
            "memory_usage_bytes": self.memory_usage_bytes,
            "column_types": self.column_types,
            "created_at": self.created_at,
        }
