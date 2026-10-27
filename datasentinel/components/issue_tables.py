"""Issue tables and deduction logs with severity filters and sorting."""

from typing import Any, Dict, List

import pandas as pd
import streamlit as st

from datasentinel.schemas.findings import IssueFinding
from datasentinel.utils.formatting import get_severity_color


def render_findings_table(findings: List[IssueFinding], key_prefix: str = "findings"):
    """Render an interactive findings table with severity and dimension filters."""
    if not findings:
        st.success("🎉 No data quality issues detected! Dataset meets all verified criteria.")
        return

    # Filter controls in columns
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        severities = ["All", "critical", "high", "medium", "low", "info"]
        selected_sev = st.selectbox("Filter by Severity", severities, index=0, key=f"{key_prefix}_sev")
    with c2:
        dimensions = ["All", "completeness", "validity", "uniqueness", "consistency"]
        selected_dim = st.selectbox("Filter by Dimension", dimensions, index=0, key=f"{key_prefix}_dim")
    with c3:
        search_query = st.text_input("Search issues / column", "", key=f"{key_prefix}_search")

    # Apply filters
    filtered = findings
    if selected_sev != "All":
        filtered = [f for f in filtered if f.severity.value.lower() == selected_sev.lower()]
    if selected_dim != "All":
        filtered = [f for f in filtered if f.dimension.value.lower() == selected_dim.lower()]
    if search_query.strip():
        q = search_query.strip().lower()
        filtered = [
            f
            for f in filtered
            if q in (f.column or "").lower() or q in f.title.lower() or q in f.description.lower()
        ]

    st.markdown(f"**Showing {len(filtered)} of {len(findings)} detected issues**")

    if not filtered:
        st.info("No issues match the selected filter criteria.")
        return

    # Convert to presentation DataFrame
    table_data = []
    for f in filtered:
        table_data.append(
            {
                "Severity": f.severity.value.upper(),
                "Dimension": f.dimension.value.title(),
                "Column": f.column or "Dataset-level",
                "Issue": f.title,
                "Affected": f"{f.affected_count:,} ({f.affected_percentage:.1f}%)"
                if f.affected_count > 0
                else "N/A",
                "Suggested Action": f.suggested_action,
            }
        )

    df_table = pd.DataFrame(table_data)
    st.dataframe(
        df_table,
        use_container_width=True,
        hide_index=True,
    )


def render_deductions_list(deductions: List[Dict[str, Any]]):
    """Render transparent score deductions audit list."""
    if not deductions:
        st.markdown("*No deductions applied. Score is 100/100.*")
        return

    for d in deductions:
        sev = d.get("severity", "medium")
        color = get_severity_color(sev)
        penalty = d.get("penalty", 0.0)
        reason = d.get("reason", "Anomaly deduction")
        dim = str(d.get("dimension", "")).title()

        html = (
            f'<div style="background:#151F32; border-left:4px solid {color}; padding:8px 14px; '
            f'border-radius:4px; margin-bottom:8px; display:flex; justify-content:space-between; align-items:center;">'
            f"<div>"
            f'<span style="font-size:11px; font-weight:700; color:{color}; text-transform:uppercase;">[{dim}]</span>'
            f'<span style="font-size:13px; color:#E2E8F0; margin-left:6px;">{reason}</span>'
            f"</div>"
            f'<div style="font-weight:700; color:#EF4444; font-size:14px;">-{penalty} pts</div>'
            f"</div>"
        )
        st.markdown(html, unsafe_allow_html=True)
