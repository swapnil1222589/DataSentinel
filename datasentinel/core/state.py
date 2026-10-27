"""Streamlit session state management and analysis coordinator."""

from typing import List

import pandas as pd
import streamlit as st

from datasentinel.core.config import CONFIG
from datasentinel.engine.duplicates import analyze_duplicates
from datasentinel.engine.missing_values import analyze_missing_values
from datasentinel.engine.outliers import analyze_all_numeric_outliers
from datasentinel.engine.profiling import profile_all_columns
from datasentinel.engine.scoring import calculate_quality_score
from datasentinel.engine.type_checks import analyze_types_and_consistency
from datasentinel.engine.validation import evaluate_rules_suite
from datasentinel.schemas.findings import DatasetMetadata, IssueFinding, QualityScoreResult
from datasentinel.schemas.rules import ValidationRule


def initialize_session_state():
    """Initialize default session state keys if not already present."""
    if "df" not in st.session_state:
        st.session_state["df"] = None
    if "raw_df" not in st.session_state:
        st.session_state["raw_df"] = None
    if "metadata" not in st.session_state:
        st.session_state["metadata"] = None
    if "ingestion_warnings" not in st.session_state:
        st.session_state["ingestion_warnings"] = []
    if "cleaning_history" not in st.session_state:
        st.session_state["cleaning_history"] = []

    # Drift reference dataset
    if "ref_df" not in st.session_state:
        st.session_state["ref_df"] = None
    if "ref_metadata" not in st.session_state:
        st.session_state["ref_metadata"] = None

    # User configured rules
    if "validation_rules" not in st.session_state:
        st.session_state["validation_rules"] = []

    # Analysis results cache
    if "analysis_cache" not in st.session_state:
        st.session_state["analysis_cache"] = None

    # Custom weights
    if "scoring_weights" not in st.session_state:
        st.session_state["scoring_weights"] = dict(CONFIG.DEFAULT_WEIGHTS)

    # Current page navigation
    if "current_page" not in st.session_state:
        st.session_state["current_page"] = "Overview"


def set_dataset(df: pd.DataFrame, metadata: DatasetMetadata, warnings: List[str]):
    """Store newly uploaded dataset and trigger fresh analysis."""
    st.session_state["df"] = df.copy()
    st.session_state["raw_df"] = df.copy()
    st.session_state["metadata"] = metadata
    st.session_state["ingestion_warnings"] = warnings
    st.session_state["cleaning_history"] = []
    # Trigger analysis recomputation
    run_full_analysis()


def reset_dataset():
    """Clear the currently loaded dataset and all associated analysis caches."""
    st.session_state["df"] = None
    st.session_state["raw_df"] = None
    st.session_state["metadata"] = None
    st.session_state["ingestion_warnings"] = []
    st.session_state["cleaning_history"] = []
    st.session_state["analysis_cache"] = None


def revert_to_raw():
    """Revert any cleaning modifications back to the original uploaded dataset."""
    if st.session_state["raw_df"] is not None:
        st.session_state["df"] = st.session_state["raw_df"].copy()
        st.session_state["cleaning_history"].append("Reverted to raw uploaded dataset.")
        run_full_analysis()


def run_full_analysis():
    """Execute all data-quality analysis modules on the current dataset."""
    df = st.session_state.get("df")
    if df is None:
        st.session_state["analysis_cache"] = None
        return

    # 1. Missing values
    missing_summary, missing_findings = analyze_missing_values(df)

    # 2. Duplicates
    duplicate_summary, duplicate_findings = analyze_duplicates(df)

    # 3. Type integrity & consistency
    type_summary, type_findings = analyze_types_and_consistency(df)

    # 4. Outliers
    outlier_summary, outlier_findings = analyze_all_numeric_outliers(
        df, factor=CONFIG.OUTLIER_IQR_FACTOR, threshold=CONFIG.OUTLIER_ZSCORE_THRESHOLD
    )

    # 5. Validation rules
    rules: List[ValidationRule] = st.session_state.get("validation_rules", [])
    rule_results, rule_findings = evaluate_rules_suite(df, rules)

    # Aggregate all findings
    all_findings: List[IssueFinding] = (
        missing_findings + duplicate_findings + type_findings + outlier_findings + rule_findings
    )

    # 6. Quality Score
    weights = st.session_state.get("scoring_weights", CONFIG.DEFAULT_WEIGHTS)
    quality_score: QualityScoreResult = calculate_quality_score(
        df=df,
        findings=all_findings,
        weights=weights,
        missing_summary=missing_summary,
        duplicate_summary=duplicate_summary,
    )

    # 7. Column Profiles
    column_profiles = profile_all_columns(df)

    # Update cache
    st.session_state["analysis_cache"] = {
        "missing_summary": missing_summary,
        "missing_findings": missing_findings,
        "duplicate_summary": duplicate_summary,
        "duplicate_findings": duplicate_findings,
        "type_summary": type_summary,
        "type_findings": type_findings,
        "outlier_summary": outlier_summary,
        "outlier_findings": outlier_findings,
        "rule_results": rule_results,
        "rule_findings": rule_findings,
        "all_findings": all_findings,
        "quality_score": quality_score,
        "column_profiles": column_profiles,
    }
