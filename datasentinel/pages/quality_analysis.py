"""Quality Analysis deep dive: missing values, duplicates, types, outliers, and custom rules."""

import pandas as pd
import streamlit as st

from datasentinel.components.charts import (
    create_missing_values_bar,
    create_numeric_boxplot,
    create_numeric_distribution_chart,
)
from datasentinel.components.issue_tables import render_findings_table
from datasentinel.core.state import run_full_analysis
from datasentinel.engine.duplicates import analyze_duplicates, generate_deduplicated_dataset
from datasentinel.engine.outliers import detect_outliers_iqr, detect_outliers_zscore
from datasentinel.schemas.rules import RuleType, ValidationRule
from datasentinel.utils.formatting import format_number


def render_quality_analysis_page():
    """Render the Quality Analysis view with comprehensive audit tabs."""
    df = st.session_state.get("df")
    metadata = st.session_state.get("metadata")
    cache = st.session_state.get("analysis_cache")

    if df is None or metadata is None or cache is None:
        st.info("Please upload a dataset or load the demo dataset to perform Quality Analysis.")
        return

    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">Quality Analysis Engine</h1>'
        '<div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">'
        "Deep-dive investigation across missing values, duplicates, schema integrity, outliers, and custom domain rules."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    tab_missing, tab_dup, tab_types, tab_outliers, tab_rules = st.tabs(
        [
            "Missing Values",
            "Duplicates",
            "Type & Consistency",
            "Numeric Outliers",
            "Custom Rules",
        ]
    )

    # ---------------------------------------------------------
    # TAB 1: MISSING VALUES
    # ---------------------------------------------------------
    with tab_missing:
        st.markdown("### Missing-Value Analysis")
        ms = cache["missing_summary"]
        m_findings = cache["missing_findings"]

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Total Cells", format_number(ms.get("total_cells", 0)))
        c2.metric("Missing Cells", format_number(ms.get("total_missing_cells", 0)))
        c3.metric("Missing Rate", f"{ms.get('overall_missing_pct', 0.0):.2f}%")
        c4.metric("Columns Affected", f"{ms.get('columns_with_missing', 0)} / {len(df.columns)}")

        chart = create_missing_values_bar(ms.get("column_metrics", []))
        if chart:
            st.plotly_chart(chart, use_container_width=True)

        st.markdown("#### Column-Level Missing Details")
        st.dataframe(pd.DataFrame(ms.get("column_metrics", [])), use_container_width=True, hide_index=True)

        st.markdown("#### Detected Missingness Findings")
        render_findings_table(m_findings, key_prefix="missing_tab")

    # ---------------------------------------------------------
    # TAB 2: DUPLICATES
    # ---------------------------------------------------------
    with tab_dup:
        st.markdown("### Duplicate Row Analysis")
        dup_summary = cache["duplicate_summary"]
        dup_findings = cache["duplicate_findings"]

        d1, d2, d3 = st.columns(3)
        d1.metric("Total Rows", format_number(dup_summary.get("total_rows", 0)))
        d2.metric("Duplicate Rows", format_number(dup_summary.get("duplicate_count", 0)))
        d3.metric("Duplicate Rate", f"{dup_summary.get('duplicate_pct', 0.0):.2f}%")

        st.markdown("#### Subset-Based Duplicate Inspection")
        subset_cols = st.multiselect(
            "Select specific key columns to evaluate uniqueness (Optional)",
            options=list(df.columns),
            help="Leave empty to evaluate exact duplicates across all columns",
        )

        if subset_cols:
            custom_dup_summary, _ = analyze_duplicates(df, subset_columns=subset_cols)
            st.info(
                f"Duplicate rows considering only {subset_cols}: "
                f"**{custom_dup_summary['duplicate_count']:,}** ({custom_dup_summary['duplicate_pct']:.1f}%)"
            )
            sample_df = custom_dup_summary["sample_duplicates"]
        else:
            sample_df = dup_summary["sample_duplicates"]

        if not sample_df.empty:
            st.markdown("#### Sample Duplicate Records")
            st.dataframe(sample_df, use_container_width=True)

            st.markdown("#### Cleaned Dataset Generation")
            st.markdown(
                "Original uploaded data is always preserved. You can explicitly export a deduplicated copy."
            )
            clean_df, removed_cnt = generate_deduplicated_dataset(df, subset_columns=subset_cols or None)

            import os

            clean_base = os.path.splitext(metadata.filename)[0]
            csv_clean = clean_df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label=f"Download Deduplicated CSV ({removed_cnt:,} duplicates removed)",
                data=csv_clean,
                file_name=f"deduplicated_{clean_base}.csv",
                mime="text/csv",
                type="primary",
                key="btn_download_dedup_csv",
            )
        else:
            st.success("No duplicate rows found!")

        st.markdown("#### Uniqueness Findings")
        render_findings_table(dup_findings, key_prefix="dup_tab")

    # ---------------------------------------------------------
    # TAB 3: TYPE INTEGRITY & CONSISTENCY
    # ---------------------------------------------------------
    with tab_types:
        st.markdown("### Data Type Integrity & Dataset Consistency")
        type_summary = cache["type_summary"]
        type_findings = cache["type_findings"]

        st.markdown("#### Findings Summary")
        render_findings_table(type_findings, key_prefix="types_tab")

        with st.expander("Constant Columns (Zero Variance)", expanded=True):
            const_cols = type_summary.get("constant_columns", [])
            if const_cols:
                st.table(pd.DataFrame(const_cols))
            else:
                st.write("None detected.")

        with st.expander("Numeric Stored as Text", expanded=True):
            num_text = type_summary.get("numeric_stored_as_text", [])
            if num_text:
                st.table(pd.DataFrame(num_text))
            else:
                st.write("None detected.")

        with st.expander("Untrimmed Whitespace in Categorical Columns", expanded=False):
            whitespace = type_summary.get("whitespace_issues", [])
            if whitespace:
                st.table(pd.DataFrame(whitespace))
            else:
                st.write("None detected.")

    # ---------------------------------------------------------
    # TAB 4: NUMERIC OUTLIERS
    # ---------------------------------------------------------
    with tab_outliers:
        st.markdown("### Configurable Numeric Outlier Analysis")
        numeric_cols = [c for c in df.columns if pd.api.types.is_numeric_dtype(df[c])]

        if not numeric_cols:
            st.info("No numeric columns detected in this dataset.")
        else:
            oc1, oc2, oc3 = st.columns([2, 2, 2])
            with oc1:
                selected_col = st.selectbox("Select Numeric Column", options=numeric_cols)
            with oc2:
                method = st.selectbox("Detection Method", options=["IQR (Tukey)", "Z-score"])
            with oc3:
                if method == "IQR (Tukey)":
                    iqr_factor = st.slider(
                        "IQR Multiplier", min_value=1.0, max_value=3.0, value=1.5, step=0.1
                    )
                    res = detect_outliers_iqr(df[selected_col], factor=iqr_factor)
                else:
                    z_thresh = st.slider(
                        "Z-Score Threshold", min_value=2.0, max_value=5.0, value=3.0, step=0.5
                    )
                    res = detect_outliers_zscore(df[selected_col], threshold=z_thresh)

            # Display metric cards for outlier inspection
            om1, om2, om3, om4 = st.columns(4)
            om1.metric("Outlier Count", format_number(res.get("outlier_count", 0)))
            om2.metric("Outlier Rate", f"{res.get('outlier_pct', 0.0):.1f}%")
            om3.metric("Lower Bound", str(res.get("lower_bound", "N/A")))
            om4.metric("Upper Bound", str(res.get("upper_bound", "N/A")))

            st.markdown(
                """
                > [!NOTE]
                > **Observational Notice:** Outliers represent statistical extremities relative to standard distributions.
                > They are not automatically errors and should be vetted by domain experts before removal.
                """
            )

            # Distribution chart & Boxplot
            c_hist, c_box = st.columns(2)
            with c_hist:
                st.plotly_chart(
                    create_numeric_distribution_chart(df[selected_col], selected_col),
                    use_container_width=True,
                )
            with c_box:
                st.plotly_chart(
                    create_numeric_boxplot(df[selected_col], selected_col), use_container_width=True
                )

            if res.get("sample_outliers"):
                st.markdown(f"**Sample Outlier Values in `{selected_col}`:** {res['sample_outliers']}")

    # ---------------------------------------------------------
    # TAB 5: CUSTOM VALIDATION RULES
    # ---------------------------------------------------------
    with tab_rules:
        st.markdown("### Custom Domain Validation Rules")
        st.markdown(
            "Define custom business constraints (e.g., marks between 0-100, age non-negative, IDs unique) "
            "to enforce deterministic domain expectations."
        )

        with st.expander("➕ Create New Validation Rule", expanded=False):
            rc1, rc2 = st.columns(2)
            with rc1:
                rule_col = st.selectbox("Target Column", options=list(df.columns), key="rule_create_col")
                rule_type_str = st.selectbox(
                    "Rule Type",
                    options=[
                        "Range (Min / Max)",
                        "Non-Negative (>= 0)",
                        "Not Null",
                        "Unique",
                        "Allowed Values (Set)",
                        "Regex Match",
                    ],
                    key="rule_create_type",
                )
            with rc2:
                rule_desc = st.text_input(
                    "Rule Description (Optional)", placeholder="e.g. Marks must be between 0 and 100"
                )
                params = {}
                if rule_type_str == "Range (Min / Max)":
                    min_val = st.number_input("Minimum Allowed Value", value=0.0)
                    max_val = st.number_input("Maximum Allowed Value", value=100.0)
                    params = {"min": min_val, "max": max_val}
                    rule_enum = RuleType.RANGE
                elif rule_type_str == "Non-Negative (>= 0)":
                    rule_enum = RuleType.NON_NEGATIVE
                elif rule_type_str == "Not Null":
                    rule_enum = RuleType.NOT_NULL
                elif rule_type_str == "Unique":
                    rule_enum = RuleType.UNIQUE
                elif rule_type_str == "Allowed Values (Set)":
                    allowed_str = st.text_input("Allowed Values (comma separated)", "Gold, Silver, Bronze")
                    params = {"allowed": [x.strip() for x in allowed_str.split(",") if x.strip()]}
                    rule_enum = RuleType.ALLOWED_VALUES
                elif rule_type_str == "Regex Match":
                    regex_str = st.text_input("Regex Pattern", r"^[A-Z]{2}-\d{4}$")
                    params = {"pattern": regex_str}
                    rule_enum = RuleType.REGEX_MATCH

            if st.button("Add Validation Rule", type="primary"):
                new_rule = ValidationRule(
                    id=f"rule_{len(st.session_state['validation_rules']) + 1}",
                    column=rule_col,
                    rule_type=rule_enum,
                    params=params,
                    enabled=True,
                    description=rule_desc or f"{rule_type_str} on {rule_col}",
                )
                st.session_state["validation_rules"].append(new_rule)
                run_full_analysis()
                st.success(f"Added rule for '{rule_col}'!")
                st.rerun()

        # Display and manage active rules
        rules = st.session_state.get("validation_rules", [])
        if not rules:
            st.info(
                "No custom validation rules defined yet. Click 'Create New Validation Rule' above to add one."
            )
        else:
            st.markdown(f"**Active Rules ({len(rules)}):**")
            rule_results = cache.get("rule_results", [])
            results_dict = {r.rule.id: r for r in rule_results}

            for idx, r in enumerate(rules):
                res = results_dict.get(r.id)
                col_r1, col_r2, col_r3 = st.columns([5, 2, 1])
                with col_r1:
                    status_badge = "✅ Passed" if (res and res.passed) else "❌ Failed"
                    st.markdown(f"**{r.column}**: {r.description or r.rule_type.value} &bull; {status_badge}")
                    if res and not res.passed:
                        st.markdown(
                            f"<span style='color:#EF4444; font-size:12px;'>Violations: {res.violation_count:,} ({res.violation_percentage:.1f}%) | Samples: {res.sample_violations}</span>",
                            unsafe_allow_html=True,
                        )
                with col_r2:
                    is_enabled = st.checkbox("Enabled", value=r.enabled, key=f"rule_chk_{r.id}")
                    if is_enabled != r.enabled:
                        r.enabled = is_enabled
                        run_full_analysis()
                        st.rerun()
                with col_r3:
                    if st.button("🗑️", key=f"del_rule_{r.id}", help="Delete rule"):
                        st.session_state["validation_rules"].pop(idx)
                        run_full_analysis()
                        st.rerun()
