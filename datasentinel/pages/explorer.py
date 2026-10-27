"""Interactive Dataset Explorer with pagination, column filters, search, and sorting."""

import math

import pandas as pd
import streamlit as st

from datasentinel.utils.formatting import format_number


def render_explorer_page():
    """Render the Dataset Explorer page."""
    df = st.session_state.get("df")
    metadata = st.session_state.get("metadata")

    if df is None or metadata is None:
        st.info(
            "Please upload a dataset or load the demo dataset from the sidebar to use the Dataset Explorer."
        )
        return

    st.markdown(
        '<div style="margin-bottom: 20px;">'
        '<h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">Dataset Explorer</h1>'
        '<div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">'
        "Interactive exploration, search, column filtering, and paginated record inspection."
        "</div>"
        "</div>",
        unsafe_allow_html=True,
    )

    all_columns = list(df.columns)

    # Top Controls Bar: Column selection, search query, sort
    col_filter_c1, col_filter_c2, col_filter_c3 = st.columns([3, 2, 2])

    with col_filter_c1:
        selected_cols = st.multiselect(
            "Select Columns to Display",
            options=all_columns,
            default=all_columns[: min(12, len(all_columns))],
            help="Choose columns to view in the paginated table",
        )
        if not selected_cols:
            selected_cols = all_columns

    with col_filter_c2:
        search_term = st.text_input(
            "Search Records",
            placeholder="Search text...",
            help="Filters rows matching text in any string column",
        )

    with col_filter_c3:
        sort_col = st.selectbox("Sort By Column", options=["None"] + selected_cols)
        sort_asc = st.checkbox("Ascending", value=True)

    # Process filtered dataset
    view_df = df[selected_cols].copy()

    # Apply search filter
    if search_term.strip():
        term = search_term.strip().lower()
        # Find matching rows in string/object columns
        mask = pd.Series(False, index=view_df.index)
        for c in selected_cols:
            series_str = view_df[c].astype(str).str.lower()
            mask = mask | series_str.str.contains(term, na=False)
        view_df = view_df[mask]

    # Apply sorting
    if sort_col != "None" and sort_col in view_df.columns:
        view_df = view_df.sort_values(by=sort_col, ascending=sort_asc)

    total_filtered_rows = len(view_df)

    # Pagination Controls
    pag_c1, pag_c2, pag_c3 = st.columns([2, 3, 2])
    with pag_c1:
        page_size = st.selectbox("Rows per page", options=[15, 25, 50, 100], index=0)
    with pag_c2:
        total_pages = max(1, math.ceil(total_filtered_rows / page_size))
        current_page = st.number_input(
            f"Page (1 to {total_pages})",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
        )
    with pag_c3:
        st.markdown(
            f'<div style="padding-top:28px; font-size:13px; color:#94A3B8;">'
            f"Showing <strong>{min(total_filtered_rows, (current_page - 1) * page_size + 1):,}</strong> - "
            f"<strong>{min(total_filtered_rows, current_page * page_size):,}</strong> of <strong>{total_filtered_rows:,}</strong> rows"
            f"</div>",
            unsafe_allow_html=True,
        )

    # Slice for active page
    start_idx = (current_page - 1) * page_size
    end_idx = start_idx + page_size
    page_data = view_df.iloc[start_idx:end_idx]

    # Display Dataframe
    st.dataframe(
        page_data,
        use_container_width=True,
        hide_index=False,
    )

    # Selected Columns Summary
    st.markdown("#### Selected Columns Schema & Summary")
    summary_records = []
    for c in selected_cols:
        series = df[c]
        null_cnt = int(series.isna().sum())
        null_pct = null_cnt / len(df) * 100.0 if len(df) > 0 else 0.0
        uniq_cnt = int(series.nunique())
        summary_records.append(
            {
                "Column Name": c,
                "Data Type": str(series.dtype),
                "Non-Null Count": format_number(len(series) - null_cnt),
                "Null Count": f"{null_cnt:,} ({null_pct:.1f}%)",
                "Unique Values": format_number(uniq_cnt),
                "Sample Value": str(series.dropna().iloc[0]) if len(series.dropna()) > 0 else "N/A",
            }
        )

    st.dataframe(pd.DataFrame(summary_records), use_container_width=True, hide_index=True)
