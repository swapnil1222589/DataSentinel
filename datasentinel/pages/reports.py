"""Report generation and multi-format export page (JSON, CSV, HTML)."""

import streamlit as st

from datasentinel.engine.report_builder import (
    build_report_data,
    export_csv_issues,
    export_html_report,
    export_json_report,
)
from datasentinel.utils.formatting import get_score_color


def render_reports_page():
    """Render the Reports and Exports management page."""
    df = st.session_state.get("df")
    metadata = st.session_state.get("metadata")
    cache = st.session_state.get("analysis_cache")

    if df is None or metadata is None or cache is None:
        st.info("Please upload a dataset or load the demo dataset to generate and export reports.")
        return

    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">
                Reports & Data Exports
            </h1>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">
                Export comprehensive data quality audit packages in JSON, CSV, and standalone self-contained HTML formats.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Compile structured report dictionary
    drift_res = cache.get("drift_results")
    report_data = build_report_data(
        metadata=metadata,
        quality_score=cache["quality_score"],
        findings=cache["all_findings"],
        missing_summary=cache["missing_summary"],
        duplicate_summary=cache["duplicate_summary"],
        type_summary=cache["type_summary"],
        outlier_summary=cache["outlier_summary"],
        rule_results=cache.get("rule_results"),
        drift_summary=drift_res,
    )

    qs = cache["quality_score"]

    # Report Summary Card
    st.markdown(
        f"""
        <div style="background:#151F32; border:1px solid #334155; border-radius:10px; padding:20px; margin-bottom:24px;">
            <div style="display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px;">
                <div>
                    <span style="font-size:11px; font-weight:700; text-transform:uppercase; color:#38BDF8; letter-spacing:0.5px;">
                        AUDIT CERTIFICATE
                    </span>
                    <h3 style="color:#F8FAFC; margin:4px 0;">{metadata.filename}</h3>
                    <div style="font-size:13px; color:#94A3B8;">
                        Audit ID: <code>{report_data["report_id"]}</code> &bull; Timestamp: {report_data["generated_at"]}
                    </div>
                </div>
                <div style="text-align:right;">
                    <div style="font-size:12px; color:#94A3B8;">Overall Quality Score</div>
                    <div style="font-size:36px; font-weight:800; color:{get_score_color(qs.overall_score)}; line-height:1;">
                        {qs.overall_score:.1f} <span style="font-size:20px;">({qs.grade})</span>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # Clean filename base so there is no double extension (e.g. avoid .csv.html)
    import os
    import re

    base_raw = os.path.splitext(metadata.filename)[0]
    clean_base = re.sub(r"[^a-zA-Z0-9_\-]", "_", base_raw)

    # 4 Export Action Cards
    st.markdown("#### Export Formats")
    e1, e2, e3 = st.columns(3)

    # 1. Standalone HTML Report
    with e1:
        st.markdown(
            '<div style="font-size:24px;">🌐</div>'
            '<div style="font-size:16px; font-weight:700; color:#F8FAFC;">Standalone HTML Report</div>'
            '<div style="font-size:12px; color:#94A3B8; margin: 4px 0 12px 0;">'
            "Interactive, self-contained HTML audit with embedded styles. No internet required."
            "</div>",
            unsafe_allow_html=True,
        )
        html_bytes = export_html_report(report_data).encode("utf-8")
        st.download_button(
            label="Download HTML Report",
            data=html_bytes,
            file_name=f"datasentinel_report_{clean_base}.html",
            mime="text/html",
            type="primary",
            key="btn_download_html_report",
            use_container_width=True,
        )

    # 2. JSON Full Audit Report
    with e2:
        st.markdown(
            '<div style="font-size:24px;">📦</div>'
            '<div style="font-size:16px; font-weight:700; color:#F8FAFC;">Machine-Readable JSON</div>'
            '<div style="font-size:12px; color:#94A3B8; margin: 4px 0 12px 0;">'
            "Complete telemetry, dimension scores, exact deduction points, and findings payload."
            "</div>",
            unsafe_allow_html=True,
        )
        json_bytes = export_json_report(report_data).encode("utf-8")
        st.download_button(
            label="Download JSON Audit",
            data=json_bytes,
            file_name=f"datasentinel_audit_{clean_base}.json",
            mime="application/json",
            key="btn_download_json_report",
            use_container_width=True,
        )

    # 3. CSV of Issues & Remediations
    with e3:
        st.markdown(
            '<div style="font-size:24px;">📄</div>'
            '<div style="font-size:16px; font-weight:700; color:#F8FAFC;">Issue Details CSV</div>'
            '<div style="font-size:12px; color:#94A3B8; margin: 4px 0 12px 0;">'
            "Tabular list of all detected issues, severity, affected counts, and remediation advice."
            "</div>",
            unsafe_allow_html=True,
        )
        csv_bytes = export_csv_issues(cache["all_findings"]).encode("utf-8")
        st.download_button(
            label="Download Issues CSV",
            data=csv_bytes,
            file_name=f"datasentinel_issues_{clean_base}.csv",
            mime="text/csv",
            key="btn_download_csv_issues",
            use_container_width=True,
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Raw JSON Preview Expander
    with st.expander("👁️ Preview JSON Payload", expanded=False):
        st.json(report_data)
