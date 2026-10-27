"""Dataset ingestion engine for CSV and Parquet formats."""

import datetime
import io
import os
import re
from typing import BinaryIO, List, Tuple, Union

import pandas as pd

from datasentinel.core.exceptions import IngestionError
from datasentinel.schemas.findings import DatasetMetadata
from datasentinel.utils.file_safety import sanitize_filename, validate_file_safety


def _disambiguate_columns(columns: List[str]) -> Tuple[List[str], List[str]]:
    """Detect and rename duplicate column headers safely."""
    seen = {}
    renamed = []
    warnings = []

    for col in columns:
        col_str = str(col).strip()
        if not col_str:
            col_str = "unnamed_column"

        # Check if pandas appended .1, .2 to duplicate columns
        match = re.match(r"^(.*?)\.(\d+)$", col_str)
        if match:
            base, num = match.groups()
            if base in seen:
                new_col = f"{base}_{num}"
                renamed.append(new_col)
                warnings.append(f"Duplicate column header '{base}' automatically renamed to '{new_col}'.")
                seen[base] += 1
                continue

        if col_str in seen:
            seen[col_str] += 1
            new_col = f"{col_str}_{seen[col_str]}"
            renamed.append(new_col)
            warnings.append(f"Duplicate column header '{col_str}' automatically renamed to '{new_col}'.")
        else:
            seen[col_str] = 0
            renamed.append(col_str)

    return renamed, warnings


def load_dataset(
    file_source: Union[BinaryIO, bytes, str],
    filename: str,
) -> Tuple[pd.DataFrame, DatasetMetadata, List[str]]:
    """Safely ingest a CSV or Parquet file into a pandas DataFrame.

    Returns:
        (df, metadata, warnings_list)
    Raises:
        IngestionError: If file cannot be read, parsed, or is empty.
    """
    clean_name = sanitize_filename(filename)
    warnings: List[str] = []

    # If file_source is a path string, open in binary mode
    if isinstance(file_source, str):
        if not os.path.isfile(file_source):
            raise IngestionError(f"File not found on disk: {file_source}")
        with open(file_source, "rb") as f:
            file_bytes = f.read()
        file_size = len(file_bytes)
        stream = io.BytesIO(file_bytes)
    elif isinstance(file_source, bytes):
        file_size = len(file_source)
        stream = io.BytesIO(file_source)
    else:
        # Seekable stream
        file_source.seek(0)
        file_bytes = file_source.read()
        file_size = len(file_bytes)
        stream = io.BytesIO(file_bytes)

    # Validate file safety
    validate_file_safety(stream, clean_name)
    stream.seek(0)

    _, ext = os.path.splitext(clean_name.lower())

    df: pd.DataFrame
    try:
        if ext == ".parquet":
            df = pd.read_parquet(stream)
        elif ext == ".csv":
            # Attempt multiple encodings in order
            encodings = ["utf-8", "utf-8-sig", "latin1", "cp1252"]
            parsed = False
            last_err = None
            for enc in encodings:
                try:
                    stream.seek(0)
                    df = pd.read_csv(stream, encoding=enc, low_memory=False)
                    parsed = True
                    if enc != "utf-8":
                        warnings.append(f"File decoded using fallback encoding: {enc}")
                    break
                except UnicodeDecodeError as ude:
                    last_err = ude
                except Exception as ex:
                    last_err = ex
                    break
            if not parsed:
                raise IngestionError(f"Failed to parse CSV file: {last_err}")
        else:
            raise IngestionError(f"Unsupported format '{ext}'. Expected .csv or .parquet")
    except Exception as exc:
        if isinstance(exc, IngestionError):
            raise
        raise IngestionError(f"Error reading dataset '{clean_name}': {str(exc)}") from exc

    # Validate dataset structure
    if df is None or (df.empty and len(df.columns) == 0):
        raise IngestionError(f"Dataset '{clean_name}' contains no readable columns or rows.")

    # Check and disambiguate column names
    original_cols = [str(c) for c in df.columns]
    sanitized_cols, col_warnings = _disambiguate_columns(original_cols)
    df.columns = pd.Index(sanitized_cols)
    warnings.extend(col_warnings)

    # Collect metadata
    mem_usage = int(df.memory_usage(deep=True).sum()) if len(df) > 0 else 0
    col_types = {str(col): str(dtype) for col, dtype in df.dtypes.items()}

    metadata = DatasetMetadata(
        filename=clean_name,
        file_size_bytes=file_size,
        row_count=len(df),
        column_count=len(df.columns),
        memory_usage_bytes=mem_usage,
        column_types=col_types,
        created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
    )

    return df, metadata, warnings
