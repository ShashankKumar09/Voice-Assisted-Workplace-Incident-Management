"""
Professional application home page.
"""

from __future__ import annotations

import pandas as pd
import streamlit as st

from ui.components import (
    render_hero,
    render_kpi_card,
    render_module_card,
    render_section_header,
    render_workflow,
)


def render_home_page(
    incident_data_path
) -> None:

    render_hero()

    # --------------------------------------------------------------------------
    # Operational overview
    # --------------------------------------------------------------------------

    try:

        incident_df = pd.read_csv(
            incident_data_path,
            low_memory=False
        )

    except Exception:

        incident_df = pd.DataFrame()

    total_incidents = len(
        incident_df
    )

    if (
        not incident_df.empty
        and "Decision" in incident_df.columns
    ):

        auto_fill_count = int(
            incident_df[
                "Decision"
            ].eq(
                "Auto Fill"
            ).sum()
        )

        suggest_count = int(
            incident_df[
                "Decision"
            ].eq(
                "Suggest Review"
            ).sum()
        )

        manual_count = int(
            incident_df[
                "Decision"
            ].eq(
                "Manual Review"
            ).sum()
        )

    else:

        auto_fill_count = 0
        suggest_count = 0
        manual_count = 0

    render_section_header(
        kicker="Operational Overview",
        title="One integrated incident-management workspace",
        description=(
            "The application supports guided reporting, automated classification, "
            "human review routing, downloadable reports and management analytics."
        )
    )

    kpi_columns = st.columns(
        4,
        gap="medium"
    )

    with kpi_columns[0]:

        render_kpi_card(
            label="Incident Records",
            value=f"{total_incidents:,}",
            caption="Available in the application data store"
        )

    with kpi_columns[1]:

        render_kpi_card(
            label="Auto Fill",
            value=f"{auto_fill_count:,}",
            caption="High-confidence final outcomes"
        )

    with kpi_columns[2]:

        render_kpi_card(
            label="Suggest Review",
            value=f"{suggest_count:,}",
            caption="Recommendations requiring confirmation"
        )

    with kpi_columns[3]:

        render_kpi_card(
            label="Manual Review",
            value=f"{manual_count:,}",
            caption="Records requiring full reviewer attention"
        )

    st.markdown(
        "<div style='height: 1.5rem;'></div>",
        unsafe_allow_html=True
    )

    # --------------------------------------------------------------------------
    # Module cards
    # --------------------------------------------------------------------------

    render_section_header(
        kicker="Application Modules",
        title="Choose how you want to work",
        description=(
            "Each module uses the same validated backend and produces consistent "
            "classification, decision and historical-validation outputs."
        )
    )

    first_row = st.columns(
        2,
        gap="large"
    )

    with first_row[0]:

        render_module_card(
            icon="🎤",
            title="Voice Incident Reporting",
            description=(
                "Complete a guided incident report one field at a time using "
                "microphone input, review the captured details and classify "
                "the final narrative."
            ),
            footer="Guided field-by-field reporting"
        )

    with first_row[1]:

        render_module_card(
            icon="📝",
            title="Manual Incident Reporting",
            description=(
                "Enter all 18 incident fields through a structured form, validate "
                "the information, classify the incident and download the final "
                "PDF or CSV report."
            ),
            footer="Structured single-incident form"
        )

    st.markdown(
        "<div style='height: 1rem;'></div>",
        unsafe_allow_html=True
    )

    second_row = st.columns(
        2,
        gap="large"
    )

    with second_row[0]:

        render_module_card(
            icon="📂",
            title="Batch Incident Processing",
            description=(
                "Download the official template, upload CSV or Excel records, "
                "run validation and classification, and export completed batch "
                "results with row-level processing details."
            ),
            footer="CSV and Excel processing"
        )

    with second_row[1]:

        render_module_card(
            icon="📊",
            title="Safety Analytics Dashboard",
            description=(
                "Explore incidents by date, year, quarter, employer, location, "
                "classification, decision tier and historical-validation outcome."
            ),
            footer="Dynamic filters and downloadable analytics"
        )

    st.markdown(
        "<div style='height: 1.8rem;'></div>",
        unsafe_allow_html=True
    )

    # --------------------------------------------------------------------------
    # Workflow
    # --------------------------------------------------------------------------

    render_section_header(
        kicker="End-to-End Workflow",
        title="From incident capture to management insight",
        description=(
            "Every reporting channel follows the same controlled processing path."
        )
    )

    render_workflow()

    st.markdown(
        "<div style='height: 1.8rem;'></div>",
        unsafe_allow_html=True
    )

    # --------------------------------------------------------------------------
    # Backend readiness
    # --------------------------------------------------------------------------

    render_section_header(
        kicker="System Readiness",
        title="Validated backend components",
        description=(
            "The application shell is connected to deployment-ready assets "
            "prepared during Phase 12."
        )
    )

    readiness_columns = st.columns(
        4,
        gap="medium"
    )

    readiness_items = [
        (
            "Shared DeBERTa",
            "Four prediction heads"
        ),
        (
            "Decision Engine",
            "Three routing outcomes"
        ),
        (
            "Historical Validation",
            "Six pairwise relationships"
        ),
        (
            "Reporting Engine",
            "PDF, CSV and Excel exports"
        )
    ]

    for column, (
        title,
        caption
    ) in zip(
        readiness_columns,
        readiness_items
    ):

        with column:

            st.markdown(
                f"""
                <div class="success-panel">
                    <b>✓ {title}</b><br/>
                    {caption}
                </div>
                """,
                unsafe_allow_html=True
            )
