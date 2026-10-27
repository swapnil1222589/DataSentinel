"""Detailed column profiler with distributions, category frequencies, and datetime ranges."""

import pandas as pd
import streamlit as st

from datasentinel.components.charts import (
    create_categorical_bar,
    create_numeric_boxplot,
    create_numeric_distribution_chart,
)
from datasentinel.components.metric_cards import render_metric_card
from datasentinel.engine.profiling import profile_column
from datasentinel.utils.formatting import format_number


def render_column_profiler_page():
    """Render the Column Profiler page."""
    df = st.session_state.get("df")
    metadata = st.session_state.get("metadata")

    if df is None or metadata is None:
        st.info("Please upload a dataset or load the demo dataset to profile individual columns.")
        return

    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">Column Profiler</h1>'
        '<div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">'
        "Fine-grained statistical profiling, value distributions, cardinality, and feature characteristics."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    all_cols = list(df.columns)
    selected_col = st.selectbox("Select Column to Inspect", options=all_cols)

    if not selected_col:
        return

    # Generate profile for selected column
    prof = profile_column(df[selected_col], selected_col)

    # Warnings if any
    for w in prof.get("warnings", []):
        st.warning(f"⚠️ {w}")

    # Top summary metrics
    m1, m2, m3, m4 = st.columns(4)
    with m1:
        render_metric_card(
            "Inferred Nature",
            str(prof.get("inferred_type", "")).title(),
            subtext=f"Raw dtype: {prof.get('raw_dtype')}",
        )
    with m2:
        render_metric_card(
            "Valid Count",
            format_number(prof.get("valid_count", 0)),
            subtext=f"Total: {format_number(prof.get('total_count', 0))}",
        )
    with m3:
        null_cnt = prof.get("null_count", 0)
        null_pct = prof.get("null_pct", 0.0)
        render_metric_card(
            "Missing",
            f"{null_pct:.1f}%",
            subtext=f"{null_cnt:,} null values",
            badge="Clear" if null_cnt == 0 else "Contains Nulls",
            badge_color="#10B981" if null_cnt == 0 else "#EF4444",
        )
    with m4:
        render_metric_card(
            "Unique Values", format_number(prof.get("unique_count", 0)), subtext="Distinct items"
        )

    st.markdown("<div style='height: 16px;'></div>", unsafe_allow_html=True)

    # Detailed Type-Specific Profiles
    col_type = prof.get("inferred_type")

    if col_type == "numeric":
        st.markdown("#### Numerical Summary Statistics")
        s1, s2, s3, s4 = st.columns(4)
        s1.metric("Mean", str(prof.get("mean", "N/A")))
        s2.metric("Median (Q2)", str(prof.get("median", "N/A")))
        s3.metric("Std Dev", str(prof.get("std", "N/A")))
        s4.metric("Skewness", str(prof.get("skewness", "N/A")))

        s5, s6, s7, s8 = st.columns(4)
        s5.metric("Minimum", str(prof.get("min", "N/A")))
        s6.metric("25th Percentile (Q1)", str(prof.get("q25", "N/A")))
        s7.metric("75th Percentile (Q3)", str(prof.get("q75", "N/A")))
        s8.metric("Maximum", str(prof.get("max", "N/A")))

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        c_hist, c_box = st.columns(2)
        with c_hist:
            st.plotly_chart(
                create_numeric_distribution_chart(df[selected_col], selected_col), use_container_width=True
            )
        with c_box:
            st.plotly_chart(create_numeric_boxplot(df[selected_col], selected_col), use_container_width=True)

    elif col_type == "categorical":
        st.markdown("#### Categorical Frequency Distribution")
        top_cats = prof.get("top_categories", [])
        if top_cats:
            cat_chart = create_categorical_bar(top_cats, selected_col)
            st.plotly_chart(cat_chart, use_container_width=True)

            st.markdown("##### Frequency Table")
            st.dataframe(pd.DataFrame(top_cats), use_container_width=True, hide_index=True)
        else:
            st.info("No categorical values to display.")

    elif col_type == "datetime":
        st.markdown("#### Datetime Range & Timeline")
        d1, d2, d3 = st.columns(3)
        d1.metric("Earliest Timestamp", str(prof.get("min_date", "N/A")))
        d2.metric("Latest Timestamp", str(prof.get("max_date", "N/A")))
        d3.metric("Span", f"{prof.get('date_range_days', 0):,} days")

        # Distribution over time histogram
        date_series = pd.to_datetime(df[selected_col], errors="coerce").dropna()
        if len(date_series) > 0:
            df_dates = pd.DataFrame({"timestamp": date_series})
            import plotly.express as px

            fig_dt = px.histogram(
                df_dates, x="timestamp", nbins=30, title=f"Timeline Frequency: {selected_col}"
            )
            fig_dt.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font=dict(color="#E2E8F0"),
                height=260,
                margin=dict(l=20, r=20, t=30, b=20),
            )
            st.plotly_chart(fig_dt, use_container_width=True)

    else:
        st.info("Column contains insufficient or unparseable data.")
