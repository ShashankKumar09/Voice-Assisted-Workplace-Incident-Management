"""
Professional application home page.
"""

import streamlit as st

from ui.components import (
    render_feature_card,
    render_hero,
    render_module_card,
    render_section_heading,
    render_workflow,
)


def render() -> None:
    render_hero(
        eyebrow="Enterprise Safety Intelligence",
        title="Voice-Assisted Workplace Incident Management System",
        subtitle=(
            "A unified workplace-safety platform for guided incident capture, "
            "four-target classification, confidence-based review routing, "
            "batch processing and management analytics."
        ),
        badges=[
            "Voice & Manual Reporting",
            "Nature • Body • Event • Source",
            "Confidence-Based Routing",
            "PDF • CSV • Excel",
        ],
    )

    render_section_heading(
        eyebrow="Application Modules",
        title="Choose how you want to work",
        description=(
            "Every module follows the same controlled workflow and produces "
            "consistent classification, review and reporting outputs."
        ),
    )

    first_row = st.columns(2, gap="large")

    with first_row[0]:
        render_module_card(
            icon="🎤",
            number="01",
            title="Voice Incident Reporting",
            description=(
                "Capture all incident details through a guided, field-by-field "
                "voice workflow with editable transcripts and final review."
            ),
            accent="Guided capture",
        )

    with first_row[1]:
        render_module_card(
            icon="📝",
            number="02",
            title="Manual Incident Reporting",
            description=(
                "Complete a structured incident form, validate the information, "
                "classify the narrative and generate a final report."
            ),
            accent="Single incident",
        )

    second_row = st.columns(2, gap="large")

    with second_row[0]:
        render_module_card(
            icon="📂",
            number="03",
            title="Batch Incident Processing",
            description=(
                "Upload CSV or Excel records, validate each row, classify incidents "
                "and export completed results with processing status."
            ),
            accent="Bulk processing",
        )

    with second_row[1]:
        render_module_card(
            icon="📊",
            number="04",
            title="Safety Analytics Dashboard",
            description=(
                "Explore incident patterns, decision tiers, confidence levels "
                "and category trends through interactive filters and charts."
            ),
            accent="Management insight",
        )

    render_section_heading(
        eyebrow="System Workflow",
        title="From incident capture to management insight",
        description=(
            "The application converts unstructured incident information into "
            "review-ready classifications, reports and analytics."
        ),
    )

    render_workflow(
        steps=[
            ("1", "Capture", "Voice, manual or batch input"),
            ("2", "Validate", "Required fields and data quality"),
            ("3", "Classify", "Nature, Body, Event and Source"),
            ("4", "Route", "Auto Fill, Suggest or Manual Review"),
            ("5", "Report", "PDF, CSV, Excel and analytics"),
        ]
    )

    render_section_heading(
        eyebrow="Business Value",
        title="Designed for faster and more consistent incident management",
        description=(
            "The platform supports safety teams by reducing repetitive manual work "
            "while keeping human review in the decision process."
        ),
    )

    value_columns = st.columns(3, gap="large")

    values = [
        (
            "⚡",
            "Faster Reporting",
            "Structured capture reduces the time required to prepare complete incident records.",
        ),
        (
            "🎯",
            "Consistent Classification",
            "The same four-target model and decision logic are applied across every reporting channel.",
        ),
        (
            "🧭",
            "Controlled Review",
            "Confidence-based routing clearly separates automatic, suggested and manual-review cases.",
        ),
    ]

    for column, item in zip(value_columns, values):
        with column:
            render_feature_card(
                icon=item[0],
                title=item[1],
                description=item[2],
            )

    st.html(
        """
        <div class="home-footer-note">
            <span class="home-footer-dot"></span>
            Built for workplace incident reporting, classification,
            review routing and safety intelligence.
        </div>
        """
    )
