"""Data type integrity and dataset consistency checks."""

from typing import Any, Dict, List, Tuple

import pandas as pd

from datasentinel.schemas.findings import IssueFinding, IssueSeverity, QualityDimension


def analyze_types_and_consistency(df: pd.DataFrame) -> Tuple[Dict[str, Any], List[IssueFinding]]:
    """Detect mixed types, numbers stored as text, constant columns, whitespace issues, and duplicate columns.

    Returns:
        (metrics_dict, list_of_findings)
    """
    total_rows = len(df)
    findings: List[IssueFinding] = []

    if total_rows == 0:
        return {
            "constant_columns": [],
            "numeric_stored_as_text": [],
            "mixed_type_columns": [],
            "whitespace_issues": [],
            "duplicate_columns": [],
        }, []

    constant_columns = []
    numeric_stored_as_text = []
    mixed_type_columns = []
    whitespace_issues = []
    duplicate_columns = []

    # 1. Constant columns (cardinality == 1)
    for col in df.columns:
        series = df[col].dropna()
        unique_cnt = series.nunique()
        if unique_cnt == 1 and total_rows > 1:
            val = series.iloc[0]
            constant_columns.append({"column": col, "value": str(val)})
            findings.append(
                IssueFinding(
                    dimension=QualityDimension.CONSISTENCY,
                    severity=IssueSeverity.LOW,
                    issue_type="constant_column",
                    title=f"Constant column '{col}' has zero variance",
                    description=f"Column '{col}' holds only a single unique value ('{val}') across all non-null rows.",
                    column=col,
                    affected_count=total_rows,
                    affected_percentage=100.0,
                    suggested_action="Verify if this column provides predictive utility or should be removed.",
                )
            )

    # 2. Text / Object column checks: Numeric stored as text, whitespace, mixed types
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            non_null = df[col].dropna()
            if len(non_null) == 0:
                continue

            # Check for leading/trailing whitespace
            str_series = non_null.astype(str)
            stripped = str_series.str.strip()
            whitespace_diff = (str_series != stripped).sum()
            if whitespace_diff > 0:
                pct = whitespace_diff / len(non_null) * 100.0
                whitespace_issues.append({"column": col, "count": int(whitespace_diff), "percentage": pct})
                findings.append(
                    IssueFinding(
                        dimension=QualityDimension.CONSISTENCY,
                        severity=IssueSeverity.LOW,
                        issue_type="untrimmed_whitespace",
                        title=f"Untrimmed whitespace in '{col}'",
                        description=f"{whitespace_diff:,} values ({pct:.1f}%) contain leading or trailing spaces.",
                        column=col,
                        affected_count=int(whitespace_diff),
                        affected_percentage=pct,
                        suggested_action="Apply `.str.strip()` to eliminate inconsistent categorical matches.",
                    )
                )

            # Check if numeric values are stored as string
            # Sample up to 1000 items to keep fast
            sample_series = str_series.head(1000)
            numeric_parsed = pd.to_numeric(sample_series.str.replace(",", "", regex=False), errors="coerce")
            num_success_rate = numeric_parsed.notna().mean()
            # If > 80% parse to numbers and it's not all pure non-digits
            if num_success_rate >= 0.8 and not sample_series.str.isalpha().any():
                numeric_stored_as_text.append(
                    {"column": col, "parsable_pct": round(num_success_rate * 100, 1)}
                )
                findings.append(
                    IssueFinding(
                        dimension=QualityDimension.VALIDITY,
                        severity=IssueSeverity.MEDIUM,
                        issue_type="numeric_stored_as_text",
                        title=f"Numeric column '{col}' stored as text",
                        description=(
                            f"Approximately {num_success_rate * 100:.1f}% of values in '{col}' are convertible "
                            "to numeric types. Storing numbers as text prevents mathematical operations."
                        ),
                        column=col,
                        affected_count=int(num_success_rate * len(non_null)),
                        affected_percentage=num_success_rate * 100,
                        suggested_action=f"Cast '{col}' to float64 or int64 using `pd.to_numeric()`.",
                    )
                )

            # Check for mixed python types (e.g., ints, strings, dicts in same column)
            types_set = {type(v).__name__ for v in non_null.head(500)}
            if len(types_set) > 1:
                mixed_type_columns.append({"column": col, "types": list(types_set)})
                findings.append(
                    IssueFinding(
                        dimension=QualityDimension.VALIDITY,
                        severity=IssueSeverity.MEDIUM,
                        issue_type="mixed_data_types",
                        title=f"Mixed data types in '{col}'",
                        description=f"Column '{col}' contains multiple disparate Python types: {', '.join(types_set)}.",
                        column=col,
                        affected_count=len(non_null),
                        affected_percentage=100.0,
                        suggested_action="Standardize data types across all rows before downstream processing.",
                    )
                )

    # 3. Possible duplicate columns (two columns with identical values)
    col_list = list(df.columns)
    for i in range(len(col_list)):
        for j in range(i + 1, len(col_list)):
            col1 = col_list[i]
            col2 = col_list[j]
            try:
                # Fast equality check: identical nulls and identical values
                if df[col1].equals(df[col2]):
                    duplicate_columns.append({"column_1": col1, "column_2": col2})
                    findings.append(
                        IssueFinding(
                            dimension=QualityDimension.CONSISTENCY,
                            severity=IssueSeverity.LOW,
                            issue_type="duplicate_columns",
                            title=f"Columns '{col1}' and '{col2}' are completely identical",
                            description="Both columns hold identical values across all rows.",
                            column=f"{col1}, {col2}",
                            affected_count=total_rows,
                            affected_percentage=100.0,
                            suggested_action=f"Consider dropping redundant column '{col2}'.",
                        )
                    )
            except Exception:
                pass

    summary = {
        "constant_columns": constant_columns,
        "numeric_stored_as_text": numeric_stored_as_text,
        "mixed_type_columns": mixed_type_columns,
        "whitespace_issues": whitespace_issues,
        "duplicate_columns": duplicate_columns,
    }

    return summary, findings
