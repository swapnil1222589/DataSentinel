"""Overview dashboard page displaying executive summary, quality score, and key metrics."""

import streamlit as st

from datasentinel.components.charts import (
    create_missing_values_bar,
    create_quality_gauge,
    create_severity_donut,
)
from datasentinel.components.issue_tables import render_deductions_list
from datasentinel.components.metric_cards import render_metric_card, render_severity_pill
from datasentinel.utils.formatting import format_bytes, format_number, format_percentage, get_score_color


def render_overview_page():
    """Render the main executive overview dashboard."""
    df = st.session_state.get("df")
    metadata = st.session_state.get("metadata")
    cache = st.session_state.get("analysis_cache")

    # Empty State: No Dataset Loaded
    if df is None or metadata is None or cache is None:
        st.markdown(
            '<div style="background: linear-gradient(135deg, #151F32 0%, #1E293B 100%); '
            'border: 1px solid #334155; border-radius: 12px; padding: 48px 32px; text-align: center; margin: 32px 0;">'
            '<div style="font-size: 40px; margin-bottom: 12px;">🛡️</div>'
            '<h2 style="color: #F8FAFC; font-size: 26px; font-weight: 800; margin-bottom: 8px;">Welcome to DataSentinel</h2>'
            '<p style="color: #94A3B8; font-size: 15px; max-width: 600px; margin: 0 auto 24px auto;">'
            "Production-grade dataset observability and automated quality assurance. "
            "Detect missingness, duplicates, schema drift, statistical anomalies, and domain rule violations."
            "</p>"
            '<div style="display: inline-block; background: #0B111E; border: 1px dashed #3B82F6; '
            'border-radius: 8px; padding: 14px 24px; color: #38BDF8; font-size: 14px;">'
            "⬅️ Upload a CSV or Parquet file in the sidebar to run the automated audit."
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )
        return

    # Header with Dataset info
    st.markdown(
        f'<div style="display:flex; justify-content:space-between; align-items:flex-start; margin-bottom: 20px; flex-wrap:wrap; gap:12px;">'
        f"<div>"
        f'<h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">Dataset Quality Overview</h1>'
        f'<div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">'
        f"Auditing <strong>{metadata.filename}</strong> &bull; Size: {format_bytes(metadata.file_size_bytes)} &bull; Memory: {format_bytes(metadata.memory_usage_bytes)}"
        f"</div>"
        f"</div>"
        f"</div>",
        unsafe_allow_html=True,
    )

    qs = cache["quality_score"]
    missing_summary = cache["missing_summary"]
    duplicate_summary = cache["duplicate_summary"]
    findings = cache["all_findings"]

    # Top Hero: Score Gauge + Primary KPIs
    hero_col1, hero_col2 = st.columns([1, 2])

    with hero_col1:
        st.markdown(
            '<div style="font-size:12px; font-weight:700; text-transform:uppercase; color:#94A3B8; text-align:center; margin-bottom:4px;">'
            "DataSentinel Quality Score"
            "</div>",
            unsafe_allow_html=True,
        )
        gauge_fig = create_quality_gauge(qs.overall_score, qs.grade)
        st.plotly_chart(gauge_fig, use_container_width=True, config={"displayModeBar": False})
        st.markdown(
            f'<div style="font-size:12px; text-align:center; color:#94A3B8; padding: 0 8px;">{qs.summary}</div>',
            unsafe_allow_html=True,
        )

    with hero_col2:
        # Row 1 of metrics
        m1, m2, m3 = st.columns(3)
        with m1:
            render_metric_card(
                "Total Rows",
                format_number(metadata.row_count),
                subtext="Records evaluated",
            )
        with m2:
            render_metric_card(
                "Total Columns",
                format_number(metadata.column_count),
                subtext=f"{len([c for c in metadata.column_types.values() if 'float' in c or 'int' in c])} numeric",
            )
        with m3:
            missing_pct = missing_summary.get("overall_missing_pct", 0.0)
            render_metric_card(
                "Missing Cells",
                format_percentage(missing_pct),
                subtext=f"{missing_summary.get('total_missing_cells', 0):,} cells missing",
                badge="Anomalous" if missing_pct > 5 else "Acceptable",
                badge_color="#EF4444" if missing_pct > 15 else ("#F59E0B" if missing_pct > 5 else "#10B981"),
            )

        # Row 2 of metrics
        m4, m5, m6 = st.columns(3)
        with m4:
            dup_cnt = duplicate_summary.get("duplicate_count", 0)
            dup_pct = duplicate_summary.get("duplicate_pct", 0.0)
            render_metric_card(
                "Duplicate Rows",
                format_number(dup_cnt),
                subtext=f"{dup_pct:.1f}% redundancy",
                badge="Critical" if dup_pct > 10 else ("Notice" if dup_cnt > 0 else "Clean"),
                badge_color="#EF4444" if dup_pct > 10 else ("#F59E0B" if dup_cnt > 0 else "#10B981"),
            )
        with m5:
            render_metric_card(
                "Detected Issues",
                str(len(findings)),
                subtext="Actionable findings",
                badge=f"{len(findings)} Total",
                badge_color="#38BDF8",
            )
        with m6:
            crit_count = sum(1 for f in findings if f.severity.value == "critical")
            render_metric_card(
                "Critical Severity",
                str(crit_count),
                subtext="Requires immediate fix",
                badge="Attention Required" if crit_count > 0 else "Clear",
                badge_color="#EF4444" if crit_count > 0 else "#10B981",
            )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Dimension Scores Row
    st.markdown("#### Quality Dimensions")
    d1, d2, d3, d4 = st.columns(4)
    dim_scores = qs.dimension_scores
    with d1:
        score_val = dim_scores.get("completeness", 100.0)
        render_metric_card(
            "Completeness",
            f"{score_val:.1f}",
            subtext="Nulls & empty values",
            badge=f"w={qs.dimension_weights.get('completeness', 0.35) * 100:.0f}%",
            badge_color=get_score_color(score_val),
        )
    with d2:
        score_val = dim_scores.get("validity", 100.0)
        render_metric_card(
            "Validity",
            f"{score_val:.1f}",
            subtext="Schema & rule compliance",
            badge=f"w={qs.dimension_weights.get('validity', 0.30) * 100:.0f}%",
            badge_color=get_score_color(score_val),
        )
    with d3:
        score_val = dim_scores.get("uniqueness", 100.0)
        render_metric_card(
            "Uniqueness",
            f"{score_val:.1f}",
            subtext="Exact & subset duplicates",
            badge=f"w={qs.dimension_weights.get('uniqueness', 0.20) * 100:.0f}%",
            badge_color=get_score_color(score_val),
        )
    with d4:
        score_val = dim_scores.get("consistency", 100.0)
        render_metric_card(
            "Consistency",
            f"{score_val:.1f}",
            subtext="Uniformity & zero-variance",
            badge=f"w={qs.dimension_weights.get('consistency', 0.15) * 100:.0f}%",
            badge_color=get_score_color(score_val),
        )

    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

    # Severity Breakdown Row
    st.markdown("#### Severity Breakdown")
    s_crit, s_high, s_med, s_low = st.columns(4)
    with s_crit:
        render_severity_pill("Critical", sum(1 for f in findings if f.severity.value == "critical"))
    with s_high:
        render_severity_pill("High", sum(1 for f in findings if f.severity.value == "high"))
    with s_med:
        render_severity_pill("Medium", sum(1 for f in findings if f.severity.value == "medium"))
    with s_low:
        render_severity_pill("Low", sum(1 for f in findings if f.severity.value == "low"))

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Visual Charts Row
    chart_c1, chart_c2 = st.columns(2)
    with chart_c1:
        st.markdown("##### Missing Values by Column")
        missing_bar = create_missing_values_bar(missing_summary.get("column_metrics", []))
        if missing_bar:
            st.plotly_chart(missing_bar, use_container_width=True)
        else:
            st.info("No missing values detected in any column.")

    with chart_c2:
        st.markdown("##### Issue Severity Distribution")
        donut_fig = create_severity_donut(findings)
        st.plotly_chart(donut_fig, use_container_width=True)

    # Transparent Deductions Expander
    with st.expander("🔍 Transparent Score Deductions Breakdown", expanded=False):
        st.markdown(f"*{qs.methodology_notes}*")
        render_deductions_list(qs.deductions)

    # Dataset Preview Section
    st.markdown("#### Dataset Preview (First 10 Records)")
    st.dataframe(df.head(10), use_container_width=True)
