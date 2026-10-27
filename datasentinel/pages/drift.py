"""Data Drift analysis module comparing reference baseline vs current dataset."""

import pandas as pd
import streamlit as st

from datasentinel.components.charts import create_drift_comparison_chart
from datasentinel.components.metric_cards import render_metric_card
from datasentinel.core.exceptions import IngestionError
from datasentinel.engine.drift import analyze_dataset_drift
from datasentinel.engine.ingestion import load_dataset
from datasentinel.utils.formatting import format_number


def render_drift_page():
    """Render the Data Drift analysis interface."""
    curr_df = st.session_state.get("df")
    curr_meta = st.session_state.get("metadata")

    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">Data Drift & Distribution Shift</h1>'
        '<div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">'
        "Detect covariate shift and distribution divergence between a baseline reference dataset and production data."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    if curr_df is None or curr_meta is None:
        st.info("Please upload a current dataset in the sidebar first before conducting drift comparison.")
        return

    # Reference Dataset Uploader
    st.markdown("#### Reference Baseline Dataset")
    ref_col1, ref_col2 = st.columns([3, 1])

    with ref_col1:
        ref_file = st.file_uploader(
            "Upload Reference / Baseline Dataset (CSV or Parquet)",
            type=["csv", "parquet"],
            key="ref_dataset_uploader",
        )
        if ref_file is not None:
            curr_ref_meta = st.session_state.get("ref_metadata")
            if curr_ref_meta is None or curr_ref_meta.filename != ref_file.name:
                try:
                    loaded_ref_df, ref_meta, _ = load_dataset(ref_file, ref_file.name)
                    st.session_state["ref_df"] = loaded_ref_df
                    st.session_state["ref_metadata"] = ref_meta
                    st.success(f"Reference dataset '{ref_file.name}' loaded successfully!")
                    st.rerun()
                except IngestionError as err:
                    st.error(f"Error loading reference dataset: {err}")

    with ref_col2:
        st.markdown("<div style='height:28px;'></div>", unsafe_allow_html=True)
        if st.button(
            "Generate Synthetic Baseline",
            help="Creates a baseline with minor distribution shift for demonstration",
        ):
            # Create synthetic reference dataset based on current df with slight shift
            import numpy as np

            ref_sim = curr_df.copy()
            for col in ref_sim.select_dtypes(include=[np.number]).columns:
                ref_sim[col] = ref_sim[col] * np.random.uniform(0.85, 1.15)
            st.session_state["ref_df"] = ref_sim
            import datetime

            from datasentinel.schemas.findings import DatasetMetadata

            st.session_state["ref_metadata"] = DatasetMetadata(
                filename="synthetic_baseline_reference.csv",
                file_size_bytes=curr_meta.file_size_bytes,
                row_count=len(ref_sim),
                column_count=len(ref_sim.columns),
                memory_usage_bytes=curr_meta.memory_usage_bytes,
                column_types=curr_meta.column_types,
                created_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            )
            st.success("Synthetic baseline generated!")
            st.rerun()

    ref_df = st.session_state.get("ref_df")
    ref_meta = st.session_state.get("ref_metadata")

    if ref_df is None or ref_meta is None:
        st.markdown(
            '<div style="background:#151F32; border:1px dashed #334155; border-radius:10px; padding:32px; text-align:center; margin-top:20px;">'
            '<div style="font-size:32px; margin-bottom:8px;">📊</div>'
            '<h4 style="color:#F8FAFC; margin-bottom:4px;">No Reference Dataset Uploaded</h4>'
            '<p style="color:#94A3B8; font-size:14px; max-width:500px; margin:0 auto;">'
            "Upload a historical baseline dataset or click <strong>Generate Synthetic Baseline</strong> above to calculate Kolmogorov-Smirnov tests and Population Stability Index (PSI)."
            "</p>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # Threshold Configuration Sliders
    with st.expander("⚙️ Drift Sensitivity Settings", expanded=False):
        tc1, tc2 = st.columns(2)
        with tc1:
            ks_alpha = st.slider(
                "Kolmogorov-Smirnov Alpha (p-value threshold)",
                min_value=0.01,
                max_value=0.10,
                value=0.05,
                step=0.01,
            )
        with tc2:
            psi_thresh = st.slider(
                "Population Stability Index (PSI) Drift Threshold",
                min_value=0.1,
                max_value=0.4,
                value=0.2,
                step=0.05,
            )

    # Execute Drift Analysis
    with st.spinner("Computing statistical distribution shifts..."):
        drift_results = analyze_dataset_drift(ref_df, curr_df, alpha=ks_alpha, psi_threshold=psi_thresh)

    # Cache drift results for reports
    if "analysis_cache" in st.session_state and st.session_state["analysis_cache"] is not None:
        st.session_state["analysis_cache"]["drift_results"] = drift_results

    # Summary KPI Cards
    dm1, dm2, dm3, dm4 = st.columns(4)
    with dm1:
        render_metric_card(
            "Reference Rows", format_number(drift_results["reference_rows"]), subtext=ref_meta.filename
        )
    with dm2:
        render_metric_card(
            "Current Rows", format_number(drift_results["current_rows"]), subtext=curr_meta.filename
        )
    with dm3:
        row_diff = drift_results["row_count_change"]
        render_metric_card(
            "Row Count Change",
            f"{row_diff:+,}",
            subtext=f"{drift_results['row_count_pct_change']:+.1f}% shift",
            badge="Shift" if abs(drift_results["row_count_pct_change"]) > 10 else "Stable",
            badge_color="#F59E0B" if abs(drift_results["row_count_pct_change"]) > 10 else "#10B981",
        )
    with dm4:
        drift_cols = drift_results["drifted_columns_count"]
        total_cols = drift_results["total_analyzed_columns"]
        render_metric_card(
            "Drifted Columns",
            f"{drift_cols} / {total_cols}",
            subtext="Significant shift",
            badge="Drift Detected" if drift_cols > 0 else "No Drift",
            badge_color="#EF4444" if drift_cols > 0 else "#10B981",
        )

    st.markdown(
        """
        > [!NOTE]
        > **Statistical Observability Notice:** Statistical distribution shifts highlight columns whose characteristics have changed over time.
        > A shift does not necessarily mean your model is broken, but signals that model monitoring and re-validation are recommended.
        """
    )

    # Columns Drift Findings Table
    st.markdown("#### Column-by-Column Drift Analysis")
    cols_data = []
    for c in drift_results["columns_analysis"]:
        cols_data.append(
            {
                "Column": c["column"],
                "Status": "🚨 DRIFT DETECTED" if c["drift_detected"] else "✅ STABLE",
                "Method": c.get("method", "N/A"),
                "KS Statistic": c.get("statistic", "N/A"),
                "p-value": f"{c.get('p_value'):.5f}" if c.get("p_value") is not None else "N/A",
                "PSI": f"{c.get('psi'):.4f}" if c.get("psi") is not None else "N/A",
                "Ref Missing %": f"{c.get('ref_null_pct'):.1f}%",
                "Curr Missing %": f"{c.get('curr_null_pct'):.1f}%",
                "Mean Shift": c.get("mean_shift", "N/A"),
            }
        )

    st.dataframe(pd.DataFrame(cols_data), use_container_width=True, hide_index=True)

    # Interactive Distribution Overlay for Selected Drifted Column
    common_num_cols = [
        c["column"] for c in drift_results["columns_analysis"] if c.get("inferred_type") == "numeric"
    ]
    if common_num_cols:
        st.markdown("#### Visual Distribution Comparison")
        inspect_col = st.selectbox("Select Numeric Column to Compare Distributions", options=common_num_cols)
        drift_chart = create_drift_comparison_chart(ref_df[inspect_col], curr_df[inspect_col], inspect_col)
        st.plotly_chart(drift_chart, use_container_width=True)
