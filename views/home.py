"""
Application home page.
"""

import streamlit as st

from ui.components import (
    render_hero,
    render_module_card,
    render_status_card,
)


def render() -> None:
    render_hero(
        eyebrow="Enterprise Safety Intelligence",
        title="Voice-Assisted Workplace Incident Management System",
        subtitle=(
            "Capture incidents through voice or structured forms, classify four "
            "workplace-safety categories, route cases using confidence-based decisions, "
            "process batch records and review safety analytics."
        ),
    )

    st.markdown("## Application Readiness")

    columns = st.columns(4, gap="medium")

    readiness = [
        ("Application Shell", "Ready", "Clean Streamlit entry point and navigation."),
        ("Classification Model", "Preserved", "Model integration will follow UI validation."),
        ("Reporting Backend", "Preserved", "PDF, CSV and Excel engines remain unchanged."),
        ("Deployment", "Testing", "Minimal dependency-safe Cloud deployment."),
    ]

    for column, item in zip(columns, readiness):
        with column:
            render_status_card(
                label=item[0],
                value=item[1],
                caption=item[2],
            )

    st.html('<div class="section-title">Application Modules</div>')

    first_row = st.columns(2, gap="large")
    with first_row[0]:
        render_module_card(
            icon="🎤",
            title="Voice Incident Reporting",
            description=(
                "Guided field-by-field incident capture using browser microphone "
                "input and editable transcripts."
            ),
        )

    with first_row[1]:
        render_module_card(
            icon="📝",
            title="Manual Incident Reporting",
            description=(
                "Structured entry form for workplace incident details, "
                "classification and report generation."
            ),
        )

    second_row = st.columns(2, gap="large")
    with second_row[0]:
        render_module_card(
            icon="📂",
            title="Batch Incident Processing",
            description=(
                "Validate and classify CSV or Excel incident files and "
                "download completed batch results."
            ),
        )

    with second_row[1]:
        render_module_card(
            icon="📊",
            title="Safety Analytics Dashboard",
            description=(
                "Review incident volumes, classifications, decision tiers "
                "and historical trends."
            ),
        )
