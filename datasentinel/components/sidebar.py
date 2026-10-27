"""Application sidebar containing branding, navigation, and file upload."""

import streamlit as st

from datasentinel.core.exceptions import IngestionError
from datasentinel.core.state import reset_dataset, set_dataset
from datasentinel.engine.ingestion import load_dataset
from datasentinel.utils.formatting import format_bytes, format_number

NAVIGATION_ITEMS = [
    "Overview",
    "Dataset Explorer",
    "Quality Analysis",
    "Column Profiler",
    "Data Drift",
    "Reports",
    "Settings and About",
]


def render_sidebar() -> str:
    """Render sidebar navigation, brand logo, dataset status, and file uploader."""
    with st.sidebar:
        # Brand Logo and Tagline
        st.markdown(
            '<div style="padding: 10px 0 16px 0; border-bottom: 1px solid #1E293B;">'
            '<div style="display: flex; align-items: center; gap: 10px;">'
            '<div style="background: linear-gradient(135deg, #3B82F6, #1D4ED8); width: 34px; height: 34px; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-weight: 900; color: #FFF; font-size: 18px; box-shadow: 0 0 12px rgba(59, 130, 246, 0.4);">'
            "⛨"
            "</div>"
            "<div>"
            '<div style="font-size: 18px; font-weight: 800; color: #F8FAFC; letter-spacing: 0.5px;">DataSentinel</div>'
            '<div style="font-size: 10px; color: #38BDF8; font-weight: 600; letter-spacing: 0.3px;">QUALITY & OBSERVABILITY</div>'
            "</div>"
            "</div>"
            '<div style="font-size: 11px; color: #94A3B8; margin-top: 8px; font-style: italic;">'
            '"Know your data before your model does."'
            "</div>"
            "</div>",
            unsafe_allow_html=True,
        )

        st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)

        # Navigation Selector - Instant Single-Click Navigation
        if "current_page" not in st.session_state:
            st.session_state["current_page"] = "Overview"

        if "navigation_selection" not in st.session_state:
            st.session_state["navigation_selection"] = st.session_state["current_page"]

        if st.session_state.get("current_page") != st.session_state.get("navigation_selection"):
            st.session_state["navigation_selection"] = st.session_state["current_page"]

        def on_nav_change():
            st.session_state["current_page"] = st.session_state["navigation_selection"]

        selected_page = st.radio(
            "Navigation",
            options=NAVIGATION_ITEMS,
            key="navigation_selection",
            on_change=on_nav_change,
            label_visibility="collapsed",
        )
        st.session_state["current_page"] = selected_page

        st.markdown("<hr style='border-color: #1E293B; margin: 16px 0;'>", unsafe_allow_html=True)

        # Upload Dataset Section
        st.markdown(
            "<span style='font-size:12px; font-weight:700; color:#94A3B8; text-transform:uppercase;'>Upload Dataset</span>",
            unsafe_allow_html=True,
        )
        uploaded_file = st.file_uploader(
            "Upload CSV or Parquet",
            type=["csv", "parquet"],
            help="Supported formats: .csv, .parquet (max 100MB)",
            label_visibility="collapsed",
            key="sidebar_file_uploader",
        )

        if uploaded_file is not None:
            # Check if this is a newly uploaded file
            curr_meta = st.session_state.get("metadata")
            is_new = (curr_meta is None) or (curr_meta.filename != uploaded_file.name)

            if is_new:
                with st.spinner("Ingesting & running quality checks..."):
                    try:
                        df, metadata, warnings = load_dataset(uploaded_file, uploaded_file.name)
                        set_dataset(df, metadata, warnings)
                        st.success(f"Loaded {uploaded_file.name}")
                        st.rerun()
                    except IngestionError as ie:
                        st.error(f"Ingestion Error: {ie}")
                    except Exception as ex:
                        st.error(f"Failed to load file: {ex}")

        # Dataset Status Card
        df = st.session_state.get("df")
        metadata = st.session_state.get("metadata")

        if df is not None and metadata is not None:
            st.markdown(
                f'<div style="background:#151F32; border:1px solid #334155; border-radius:8px; padding:12px; margin-top:10px;">'
                f'<div style="font-size:11px; text-transform:uppercase; color:#38BDF8; font-weight:700;">Active Dataset</div>'
                f'<div style="font-size:13px; font-weight:700; color:#F8FAFC; word-break:break-all; margin-top:2px;">{metadata.filename}</div>'
                f'<div style="display:flex; justify-content:space-between; margin-top:8px; font-size:11px; color:#94A3B8;">'
                f'<span>Rows: <strong style="color:#FFF;">{format_number(metadata.row_count)}</strong></span>'
                f'<span>Cols: <strong style="color:#FFF;">{format_number(metadata.column_count)}</strong></span>'
                f'<span>Size: <strong style="color:#FFF;">{format_bytes(metadata.file_size_bytes)}</strong></span>'
                f"</div>"
                f"</div>",
                unsafe_allow_html=True,
            )

            if st.button("Reset Dataset", use_container_width=True, type="secondary"):
                reset_dataset()
                st.rerun()
        else:
            st.markdown(
                '<div style="background:#151F32; border:1px dashed #334155; border-radius:8px; padding:14px; text-align:center; margin-top:10px;">'
                '<div style="font-size:12px; color:#94A3B8;">No dataset active</div>'
                '<div style="font-size:11px; color:#64748B; margin-top:4px;">Upload CSV or Parquet above to begin quality audit.</div>'
                "</div>",
                unsafe_allow_html=True,
            )

        # Quick sample dataset button for fast demonstration
        if df is None:
            st.markdown("<div style='height: 8px;'></div>", unsafe_allow_html=True)
            if st.button("Load Demo E-Commerce Dataset", use_container_width=True):
                # Create demo dataset with typical real-world quality issues:
                # - missing values
                # - duplicate rows
                # - numeric outliers (e.g. price $99,999)
                # - whitespace in categories
                # - constant column
                # - age range violations
                import numpy as np
                import pandas as pd

                np.random.seed(42)
                n = 500
                demo_data = {
                    "customer_id": [f"CUST-{i:04d}" for i in range(1, n + 1)],
                    "age": np.random.choice(
                        [19, 25, 34, 42, 55, 68, -5, 180, None],
                        size=n,
                        p=[0.2, 0.25, 0.2, 0.15, 0.1, 0.05, 0.02, 0.01, 0.02],
                    ),
                    "annual_income": np.random.choice(
                        [35000, 48000, 62000, 85000, 110000, 950000, None],
                        size=n,
                        p=[0.25, 0.25, 0.2, 0.15, 0.1, 0.02, 0.03],
                    ),
                    "spending_score": np.random.choice(
                        [15, 39, 52, 77, 88, 99, 105, None],
                        size=n,
                        p=[0.15, 0.2, 0.25, 0.2, 0.1, 0.05, 0.02, 0.03],
                    ),
                    "membership_status": np.random.choice(
                        [" Gold", "Gold", "Silver", " Bronze ", "Platinum", "   ", "N/A", None],
                        size=n,
                        p=[0.1, 0.3, 0.3, 0.15, 0.05, 0.04, 0.03, 0.03],
                    ),
                    "country": ["United States"] * n,  # Constant column
                    "signup_date": np.random.choice(
                        ["2023-01-15", "2023-04-20", "2023-08-11", "2023-11-05", "invalid-date", None],
                        size=n,
                        p=[0.3, 0.3, 0.25, 0.1, 0.03, 0.02],
                    ),
                }
                demo_df = pd.DataFrame(demo_data)
                # Add 12 exact duplicates
                demo_df = pd.concat([demo_df, demo_df.iloc[:12]], ignore_index=True)
                csv_bytes = demo_df.to_csv(index=False).encode("utf-8")
                loaded_df, meta, warns = load_dataset(csv_bytes, "ecommerce_customer_data.csv")
                set_dataset(loaded_df, meta, warns)
                st.rerun()

        # Footer
        st.markdown(
            """
            <div style="position:fixed; bottom:12px; left:16px; font-size:11px; color:#475569;">
                DataSentinel v1.0.0 &bull; Local & Offline
            </div>
            """,
            unsafe_allow_html=True,
        )

    return selected_page
