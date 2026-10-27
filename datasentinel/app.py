"""DataSentinel - Modern Open-Source Data Quality & Observability Platform.

Main entry point for the Streamlit application.
"""

import os
import sys

# Ensure package root is in python path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)
if current_dir not in sys.path:
    sys.path.insert(0, current_dir)

import streamlit as st

from datasentinel.components.metric_cards import inject_custom_styles
from datasentinel.components.sidebar import render_sidebar
from datasentinel.core.state import initialize_session_state
from datasentinel.pages.column_profiler import render_column_profiler_page
from datasentinel.pages.drift import render_drift_page
from datasentinel.pages.explorer import render_explorer_page
from datasentinel.pages.overview import render_overview_page
from datasentinel.pages.quality_analysis import render_quality_analysis_page
from datasentinel.pages.reports import render_reports_page
from datasentinel.pages.settings import render_settings_page


def main():
    """Main application orchestrator."""
    st.set_page_config(
        page_title="DataSentinel - Data Quality & Observability Platform",
        page_icon="⛨",
        layout="wide",
        initial_sidebar_state="expanded",
    )

    # Inject custom styling for dark slate aesthetics
    inject_custom_styles()

    # Initialize session state cache
    initialize_session_state()

    # Render sidebar and get active navigation selection
    selected_page = render_sidebar()

    # Route to selected page
    if selected_page == "Overview":
        render_overview_page()
    elif selected_page == "Dataset Explorer":
        render_explorer_page()
    elif selected_page == "Quality Analysis":
        render_quality_analysis_page()
    elif selected_page == "Column Profiler":
        render_column_profiler_page()
    elif selected_page == "Data Drift":
        render_drift_page()
    elif selected_page == "Reports":
        render_reports_page()
    elif selected_page == "Settings and About":
        render_settings_page()
    else:
        render_overview_page()


if __name__ == "__main__":
    main()
