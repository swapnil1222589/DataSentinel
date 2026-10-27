"""Metric cards and visual KPI elements styled with dark navy aesthetics."""

from typing import Optional

import streamlit as st

from datasentinel.utils.formatting import get_severity_color


def render_metric_card(
    label: str,
    value: str,
    subtext: Optional[str] = None,
    badge: Optional[str] = None,
    badge_color: Optional[str] = None,
):
    """Render a single styled SaaS KPI card without markdown indentation issues."""
    badge_html = ""
    if badge:
        b_color = badge_color or "#3B82F6"
        badge_html = (
            f'<span style="background:{b_color}22; color:{b_color}; border:1px solid {b_color}44; '
            f"padding:2px 8px; border-radius:12px; font-size:11px; font-weight:700; "
            f'letter-spacing:0.3px; float:right;">{badge}</span>'
        )

    sub_html = (
        f'<div style="font-size:12px; color:#94A3B8; margin-top:4px;">{subtext}</div>' if subtext else ""
    )

    html = (
        f'<div style="background:#151F32; border:1px solid #334155; border-radius:10px; padding:16px 18px; margin-bottom:8px;">'
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">'
        f'<span style="font-size:12px; font-weight:600; text-transform:uppercase; color:#94A3B8; letter-spacing:0.5px;">{label}</span>'
        f"{badge_html}"
        f"</div>"
        f'<div style="font-size:26px; font-weight:800; color:#F8FAFC; line-height:1.2;">{value}</div>'
        f"{sub_html}"
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def render_severity_pill(severity: str, count: int):
    """Render an issue severity counter pill."""
    color = get_severity_color(severity)
    html = (
        f'<div style="background:{color}18; border:1px solid {color}44; border-radius:8px; padding:10px 14px; text-align:center;">'
        f'<div style="font-size:11px; font-weight:700; text-transform:uppercase; color:{color}; letter-spacing:0.5px;">{severity}</div>'
        f'<div style="font-size:22px; font-weight:800; color:#F8FAFC; margin-top:2px;">{count:,}</div>'
        f"</div>"
    )
    st.markdown(html, unsafe_allow_html=True)


def inject_custom_styles():
    """Inject custom CSS to enhance Streamlit container styling and contrast."""
    css = """<style>
/* Hide Streamlit default auto-generated multi-page sidebar navigation */
div[data-testid="stSidebarNav"] {
    display: none !important;
}

/* Overall App Background & Typography */
.stApp {
    background-color: #0B111E;
    color: #E2E8F0;
}

/* Sidebar Styling */
section[data-testid="stSidebar"] {
    background-color: #0F172A;
    border-right: 1px solid #1E293B;
}

/* Button Styling */
.stButton>button {
    border-radius: 8px;
    font-weight: 600;
    transition: all 0.2s ease;
}
.stButton>button:hover {
    border-color: #3B82F6;
    box-shadow: 0 0 10px rgba(59, 130, 246, 0.3);
}

/* Table & Dataframe Container */
div[data-testid="stDataFrame"] {
    border: 1px solid #334155;
    border-radius: 8px;
    overflow: hidden;
}

/* Expander Styling */
div[data-testid="stExpander"] {
    background-color: #151F32;
    border: 1px solid #334155;
    border-radius: 8px;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 6px;
    padding: 8px 16px;
    background-color: #151F32;
    color: #94A3B8;
    font-weight: 600;
}
.stTabs [aria-selected="true"] {
    background-color: #1E293B !important;
    color: #38BDF8 !important;
    border-bottom: 2px solid #38BDF8 !important;
}
</style>"""
    st.markdown(css, unsafe_allow_html=True)
