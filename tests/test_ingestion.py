"""Unit tests for dataset ingestion engine."""

import io

import pandas as pd
import pytest

from datasentinel.core.exceptions import FileSecurityError
from datasentinel.engine.ingestion import load_dataset


def test_valid_csv_ingestion():
    csv_content = b"name,age,score\nAlice,25,90.5\nBob,30,85.0\nCharlie,35,92.0\n"
    df, metadata, warnings = load_dataset(csv_content, "test.csv")
    assert len(df) == 3
    assert len(df.columns) == 3
    assert metadata.filename == "test.csv"
    assert metadata.row_count == 3
    assert metadata.column_count == 3
    assert "name" in df.columns
    assert "age" in df.columns
    assert "score" in df.columns


def test_duplicate_column_headers():
    csv_content = b"value,value,other\n1,2,3\n4,5,6\n"
    df, metadata, warnings = load_dataset(csv_content, "dups.csv")
    assert len(df.columns) == 3
    assert "value" in df.columns
    assert "value_1" in df.columns
    assert any("Duplicate column header" in w for w in warnings)


def test_empty_csv_raises_error():
    empty_content = b""
    with pytest.raises(FileSecurityError) as exc_info:
        load_dataset(empty_content, "empty.csv")
    assert "empty" in str(exc_info.value).lower()


def test_unsupported_file_extension():
    content = b"some,content\n1,2\n"
    with pytest.raises(FileSecurityError) as exc_info:
        load_dataset(content, "dataset.xlsx")
    assert "unsupported file extension" in str(exc_info.value).lower()


def test_executable_header_rejection():
    # Windows MZ header
    dangerous_content = b"MZ\x90\x00\x03\x00\x00\x00some,csv\n1,2\n"
    with pytest.raises(FileSecurityError) as exc_info:
        load_dataset(dangerous_content, "malicious.csv")
    assert "unsafe" in str(exc_info.value).lower()


def test_valid_parquet_ingestion():
    sample_df = pd.DataFrame(
        {
            "id": [1, 2, 3],
            "city": ["New York", "London", "Tokyo"],
            "temp": [22.5, 18.2, 26.0],
        }
    )
    buffer = io.BytesIO()
    sample_df.to_parquet(buffer, index=False)
    parquet_bytes = buffer.getvalue()

    df, metadata, warnings = load_dataset(parquet_bytes, "data.parquet")
    assert len(df) == 3
    assert metadata.column_count == 3
    assert list(df.columns) == ["id", "city", "temp"]


def test_file_size_limit_exceeded():
    large_header = b"col1,col2\n"
    small_limit_bytes = 100
    oversized_content = large_header + b"1,2\n" * 50  # > 100 bytes

    with pytest.raises(FileSecurityError) as exc_info:
        from datasentinel.utils.file_safety import validate_file_safety

        validate_file_safety(oversized_content, "large.csv", max_size_bytes=small_limit_bytes)
    assert "exceeds" in str(exc_info.value).lower()
