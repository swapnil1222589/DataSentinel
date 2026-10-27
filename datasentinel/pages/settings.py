"""Application settings, scoring methodology, and system information."""

import os

import streamlit as st

from datasentinel.core.config import CONFIG
from datasentinel.core.state import reset_dataset, run_full_analysis


def render_settings_page():
    """Render the Settings, Scoring Configuration, and System Info page."""
    st.markdown(
        """
        <div style="margin-bottom: 20px;">
            <h1 style="font-size: 26px; font-weight: 800; color: #F8FAFC; margin: 0;">
                Settings & About DataSentinel
            </h1>
            <div style="color: #94A3B8; font-size: 13px; margin-top: 4px;">
                Scoring weights calibration, outlier sensitivities, offline architecture, and system observability.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    tab_weights, tab_ai, tab_info = st.tabs(
        [
            "Scoring Methodology & Weights",
            "AI Explanation Interface (Optional)",
            "System & Architecture",
        ]
    )

    # TAB 1: SCORING METHODOLOGY & WEIGHTS
    with tab_weights:
        st.markdown("### Transparent Scoring Weights")
        st.markdown(
            "Customize the relative importance of each dimension in computing the overall DataSentinel Quality Score. "
            "Weights are automatically normalized."
        )

        curr_weights = st.session_state.get("scoring_weights", dict(CONFIG.DEFAULT_WEIGHTS))

        w1, w2 = st.columns(2)
        with w1:
            comp_w = st.slider(
                "Completeness Weight",
                min_value=0.0,
                max_value=1.0,
                value=float(curr_weights.get("completeness", 0.35)),
                step=0.05,
            )
            val_w = st.slider(
                "Validity Weight",
                min_value=0.0,
                max_value=1.0,
                value=float(curr_weights.get("validity", 0.30)),
                step=0.05,
            )
        with w2:
            uniq_w = st.slider(
                "Uniqueness Weight",
                min_value=0.0,
                max_value=1.0,
                value=float(curr_weights.get("uniqueness", 0.20)),
                step=0.05,
            )
            cons_w = st.slider(
                "Consistency Weight",
                min_value=0.0,
                max_value=1.0,
                value=float(curr_weights.get("consistency", 0.15)),
                step=0.05,
            )

        total_w = comp_w + val_w + uniq_w + cons_w
        if total_w > 0:
            norm_comp = comp_w / total_w
            norm_val = val_w / total_w
            norm_uniq = uniq_w / total_w
            norm_cons = cons_w / total_w
        else:
            norm_comp, norm_val, norm_uniq, norm_cons = 0.35, 0.30, 0.20, 0.15

        st.info(
            f"**Normalized Weights Active:** Completeness: {norm_comp * 100:.1f}%, "
            f"Validity: {norm_val * 100:.1f}%, Uniqueness: {norm_uniq * 100:.1f}%, "
            f"Consistency: {norm_cons * 100:.1f}%"
        )

        if st.button("Apply New Scoring Weights", type="primary"):
            st.session_state["scoring_weights"] = {
                "completeness": norm_comp,
                "validity": norm_val,
                "uniqueness": norm_uniq,
                "consistency": norm_cons,
            }
            run_full_analysis()
            st.success("Scoring weights updated and scores recomputed!")
            st.rerun()

        st.markdown("<hr style='border-color:#334155; margin:24px 0;'>", unsafe_allow_html=True)
        st.markdown("#### Quality Scoring Heuristic Rules")
        st.markdown(
            """
            - **Completeness (0–100):** Evaluates overall missing cell percentage and imposes a 10-point penalty for each completely empty column.
            - **Validity (0–100):** Deducts points for custom rule failures, mixed types in single columns, and numeric features stored as strings.
            - **Uniqueness (0–100):** Deducts points proportionally based on duplicate row percentage.
            - **Consistency (0–100):** Penalizes constant zero-variance columns, redundant identical columns, and untrimmed whitespace.
            - **Critical Guardrail:** Any Critical-severity finding automatically caps the overall score to 65.0 (Grade D) to prevent high overall scores from concealing severe flaws.
            """
        )

    # TAB 2: OPTIONAL AI INTEGRATION INTERFACE
    with tab_ai:
        st.markdown("### Optional AI Provider Interface")
        st.markdown(
            """
            > [!IMPORTANT]
            > **Zero External Dependency Guarantee:** DataSentinel is 100% functional offline using deterministic Python algorithms.
            > AI is **never required** and does not replace deterministic statistical checks or invent data quality metrics.
            """
        )

        ai_provider = os.getenv("DATASENTINEL_AI_PROVIDER", "none").lower()

        st.markdown(
            f'<div style="background:#151F32; border:1px solid #334155; border-radius:8px; padding:16px; margin:16px 0;">'
            f'<div style="font-size:12px; color:#94A3B8; text-transform:uppercase; font-weight:700;">Current AI Status</div>'
            f'<div style="font-size:18px; font-weight:700; color:#F8FAFC; margin-top:4px;">'
            f"Mode: <code>{ai_provider}</code> (Offline Deterministic Mode Active)"
            f"</div>"
            f'<div style="font-size:13px; color:#94A3B8; margin-top:6px;">'
            f"No external AI provider configured. All detections and statistical analyses are executed locally using NumPy, Pandas, and SciPy."
            f"</div>"
            f"</div>",
            unsafe_allow_html=True,
        )

        st.markdown("#### How AI Integration Works (When Configured)")
        st.markdown(
            """
            1. **Privacy First:** Raw dataset records are **NEVER uploaded** to any AI service. Only aggregated finding summaries (e.g. column name, issue type, affected percentage) may be sent for natural language remediation recommendations.
            2. **No Hallucinated Numbers:** All numbers, percentages, and statistical distributions are strictly calculated by the local Python engine.
            3. **Environment Driven:** Enable optional providers via `.env` file (`DATASENTINEL_AI_PROVIDER=openai`, `DATASENTINEL_AI_API_KEY=...`).
            """
        )

    # TAB 3: SYSTEM & ARCHITECTURE
    with tab_info:
        st.markdown("### System Observability & Architecture")

        import platform

        s1, s2, s3 = st.columns(3)
        with s1:
            st.metric("Python Version", platform.python_version())
        with s2:
            st.metric("Operating System", platform.system())
        with s3:
            st.metric("Platform Architecture", platform.machine())

        st.markdown("<div style='height:16px;'></div>", unsafe_allow_html=True)

        st.markdown(
            """
            #### Architectural Principles
            - **Locality:** Runs completely on your workstation without cloud dependencies, API keys, or telemetry tracking.
            - **Deterministic:** Reliable, reproducible findings based on rigorous statistical criteria (Tukey's IQR, Z-scores, KS-test, PSI).
            - **Immutability:** Uploaded raw datasets are treated as strictly immutable; cleaning operations produce separate exportable artifacts.
            """
        )

        if st.button("Reset Entire Application Session", type="secondary"):
            reset_dataset()
            st.session_state.clear()
            st.success("Session state cleared.")
            st.rerun()
