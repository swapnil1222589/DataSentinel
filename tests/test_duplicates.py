"""Unit tests for duplicate detection and deduplication generator."""

import pandas as pd

from datasentinel.engine.duplicates import analyze_duplicates, generate_deduplicated_dataset
from datasentinel.schemas.findings import QualityDimension


def test_no_duplicates():
    df = pd.DataFrame({"id": [1, 2, 3], "val": ["a", "b", "c"]})
    summary, findings = analyze_duplicates(df)
    assert summary["duplicate_count"] == 0
    assert summary["duplicate_pct"] == 0.0
    assert len(findings) == 0


def test_exact_duplicates():
    df = pd.DataFrame(
        {
            "id": [1, 2, 1, 3, 2],
            "val": ["a", "b", "a", "c", "b"],
        }
    )
    summary, findings = analyze_duplicates(df)
    # id 1, val a appears twice (1 redundant)
    # id 2, val b appears twice (1 redundant)
    assert summary["duplicate_count"] == 2
    assert summary["duplicate_pct"] == 40.0
    assert len(findings) == 1
    assert findings[0].dimension == QualityDimension.UNIQUENESS


def test_subset_duplicates():
    df = pd.DataFrame(
        {
            "id": [1, 2, 1, 3],
            "timestamp": ["10:00", "10:05", "10:15", "10:20"],
        }
    )
    # Whole row is distinct because timestamps differ, but subset 'id' has a duplicate
    summary_all, _ = analyze_duplicates(df)
    assert summary_all["duplicate_count"] == 0

    summary_sub, findings_sub = analyze_duplicates(df, subset_columns=["id"])
    assert summary_sub["duplicate_count"] == 1
    assert len(findings_sub) == 1


def test_generate_deduplicated_dataset():
    original_df = pd.DataFrame({"id": [1, 1, 2], "val": ["x", "x", "y"]})
    clean_df, removed_cnt = generate_deduplicated_dataset(original_df)
    assert removed_cnt == 1
    assert len(clean_df) == 2
    # Ensure original dataframe was not mutated
    assert len(original_df) == 3
