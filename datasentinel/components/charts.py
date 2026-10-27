"""Plotly visualization components adhering to the DataSentinel dark theme."""

from typing import Any, Dict, List, Optional

import pandas as pd
import plotly.graph_objects as go

from datasentinel.utils.formatting import get_score_color, get_severity_color

DARK_LAYOUT_TEMPLATE = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#E2E8F0", family="-apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif"),
    xaxis=dict(
        gridcolor="#1E293B",
        zerolinecolor="#334155",
        showline=True,
        linecolor="#334155",
    ),
    yaxis=dict(
        gridcolor="#1E293B",
        zerolinecolor="#334155",
        showline=True,
        linecolor="#334155",
    ),
    margin=dict(l=30, r=20, t=35, b=30),
)


def create_quality_gauge(score: float, grade: str) -> go.Figure:
    """Create a semi-circular gauge meter for the overall quality score."""
    color = get_score_color(score)
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=score,
            number={"suffix": "/100", "font": {"size": 34, "color": "#F8FAFC"}},
            title={"text": f"<b>GRADE: {grade}</b>", "font": {"size": 18, "color": color}},
            gauge={
                "axis": {"range": [0, 100], "tickwidth": 1, "tickcolor": "#475569"},
                "bar": {"color": color, "thickness": 0.3},
                "bgcolor": "#151F32",
                "borderwidth": 1,
                "bordercolor": "#334155",
                "steps": [
                    {"range": [0, 59], "color": "rgba(239, 68, 68, 0.15)"},
                    {"range": [60, 74], "color": "rgba(245, 158, 11, 0.15)"},
                    {"range": [75, 89], "color": "rgba(59, 130, 246, 0.15)"},
                    {"range": [90, 100], "color": "rgba(16, 185, 129, 0.15)"},
                ],
            },
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font={"color": "#E2E8F0"},
        height=240,
        margin=dict(l=20, r=20, t=30, b=10),
    )
    return fig


def create_missing_values_bar(column_metrics: List[Dict[str, Any]], top_n: int = 15) -> Optional[go.Figure]:
    """Create a horizontal bar chart showing columns with missing values."""
    with_missing = [c for c in column_metrics if c["missing_count"] > 0][:top_n]
    if not with_missing:
        return None

    df_bar = pd.DataFrame(with_missing)
    fig = go.Figure(
        go.Bar(
            x=df_bar["missing_pct"],
            y=df_bar["column"],
            orientation="h",
            marker=dict(
                color=df_bar["missing_pct"],
                colorscale=[[0, "#3B82F6"], [0.5, "#F59E0B"], [1, "#EF4444"]],
                showscale=False,
                line=dict(color="#334155", width=1),
            ),
            text=[
                f"{pct:.1f}% ({cnt:,})" for pct, cnt in zip(df_bar["missing_pct"], df_bar["missing_count"])
            ],
            textposition="auto",
        )
    )
    layout_args = dict(DARK_LAYOUT_TEMPLATE)
    layout_args.update(
        height=max(250, len(with_missing) * 28),
        xaxis_title="Missing Rate (%)",
        yaxis=dict(autorange="reversed", gridcolor="#1E293B", linecolor="#334155"),
    )
    fig.update_layout(**layout_args)
    return fig


def create_severity_donut(findings: List[Any]) -> go.Figure:
    """Create a donut chart displaying distribution of findings by severity."""
    severities = ["critical", "high", "medium", "low", "info"]
    counts = [
        sum(
            1
            for f in findings
            if (getattr(f, "severity", None) and f.severity.value == s)
            or (isinstance(f, dict) and f.get("severity") == s)
        )
        for s in severities
    ]

    # Filter out zero counts
    labels = []
    values = []
    colors = []
    for s, c in zip(severities, counts):
        if c > 0:
            labels.append(s.title())
            values.append(c)
            colors.append(get_severity_color(s))

    if not values:
        labels = ["No Issues Detected"]
        values = [1]
        colors = ["#10B981"]

    fig = go.Figure(
        go.Pie(
            labels=labels,
            values=values,
            hole=0.65,
            marker=dict(colors=colors, line=dict(color="#0B111E", width=2)),
            textinfo="label+value",
            textposition="outside",
        )
    )
    fig.update_layout(
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#E2E8F0"),
        showlegend=False,
        height=220,
        margin=dict(l=10, r=10, t=10, b=10),
    )
    return fig


def create_numeric_distribution_chart(series: pd.Series, col_name: str) -> go.Figure:
    """Histogram with interactive binning for numeric feature distributions."""
    clean_series = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=clean_series,
            nbinsx=35,
            marker=dict(color="#3B82F6", line=dict(color="#1D4ED8", width=1)),
            opacity=0.85,
            name="Values",
        )
    )
    fig.update_layout(
        **DARK_LAYOUT_TEMPLATE,
        title=dict(text=f"Distribution: {col_name}", font=dict(size=14, color="#94A3B8")),
        xaxis_title=col_name,
        yaxis_title="Count",
        height=280,
    )
    return fig


def create_numeric_boxplot(series: pd.Series, col_name: str) -> go.Figure:
    """Boxplot displaying quartiles, median, and Tukey outliers."""
    clean_series = pd.to_numeric(series.dropna(), errors="coerce").dropna()
    fig = go.Figure()
    fig.add_trace(
        go.Box(
            x=clean_series,
            boxpoints="outliers",
            jitter=0.3,
            pointpos=-1.8,
            marker=dict(color="#EF4444", size=4),
            line=dict(color="#38BDF8"),
            fillcolor="rgba(56, 189, 248, 0.2)",
            name=col_name,
        )
    )
    fig.update_layout(
        **DARK_LAYOUT_TEMPLATE,
        title=dict(text=f"Quartiles & Outlier Spread: {col_name}", font=dict(size=14, color="#94A3B8")),
        xaxis_title=col_name,
        height=200,
    )
    return fig


def create_categorical_bar(top_categories: List[Dict[str, Any]], col_name: str) -> go.Figure:
    """Bar chart for top categorical frequencies."""
    df_cats = pd.DataFrame(top_categories)
    fig = go.Figure(
        go.Bar(
            x=df_cats["category"],
            y=df_cats["count"],
            marker=dict(color="#6366F1", line=dict(color="#4338CA", width=1)),
            text=[f"{p:.1f}%" for p in df_cats["percentage"]],
            textposition="auto",
        )
    )
    fig.update_layout(
        **DARK_LAYOUT_TEMPLATE,
        title=dict(text=f"Top Categories: {col_name}", font=dict(size=14, color="#94A3B8")),
        xaxis_title="Category",
        yaxis_title="Frequency",
        height=280,
    )
    return fig


def create_drift_comparison_chart(
    ref_series: pd.Series,
    curr_series: pd.Series,
    col_name: str,
) -> go.Figure:
    """Overlaid distribution chart comparing reference vs current dataset for drift inspection."""
    ref_clean = pd.to_numeric(ref_series.dropna(), errors="coerce").dropna()
    curr_clean = pd.to_numeric(curr_series.dropna(), errors="coerce").dropna()

    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=ref_clean,
            nbinsx=30,
            marker_color="#3B82F6",
            opacity=0.6,
            name="Reference Dataset",
            histnorm="probability density",
        )
    )
    fig.add_trace(
        go.Histogram(
            x=curr_clean,
            nbinsx=30,
            marker_color="#F59E0B",
            opacity=0.6,
            name="Current Dataset",
            histnorm="probability density",
        )
    )
    fig.update_layout(
        **DARK_LAYOUT_TEMPLATE,
        barmode="overlay",
        title=dict(text=f"Distribution Comparison: {col_name}", font=dict(size=14, color="#94A3B8")),
        xaxis_title=col_name,
        yaxis_title="Density",
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        height=300,
    )
    return fig
