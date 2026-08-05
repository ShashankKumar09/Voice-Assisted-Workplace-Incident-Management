"""
Reusable UI components for the Streamlit application.
"""

from __future__ import annotations

from html import escape
from typing import Optional

import streamlit as st




def render_html(html_content):
    """
    Render trusted application HTML and CSS.
    """
    if html_content is None:
        return

    st.markdown(
        str(html_content),
        unsafe_allow_html=True,
    )


def render_sidebar_brand() -> None:

    st.sidebar.markdown(
        """
        <div class="sidebar-brand">
            <div class="sidebar-brand-title">
                Workplace Incident<br/>
                Management System
            </div>

            <div class="sidebar-brand-subtitle">
                Voice-assisted reporting, classification,
                decision support and safety analytics.
            </div>
        </div>

        <div class="sidebar-divider"></div>
        """,
        unsafe_allow_html=True
    )


def render_hero() -> None:

    st.markdown(
        """
        <div class="hero-shell">

            <div class="hero-eyebrow">
                Enterprise Safety Intelligence
            </div>

            <div class="hero-title">
                Voice-Assisted Workplace<br/>
                Incident Management System
            </div>

            <div class="hero-subtitle">
                Capture workplace incidents through guided voice or manual
                reporting, classify four incident categories, apply confidence-based
                decision support, process batch records and monitor safety trends
                through one integrated application.
            </div>

            <div class="hero-pill-row">
                <div class="hero-pill">Guided Voice Reporting</div>
                <div class="hero-pill">Four-Target Classification</div>
                <div class="hero-pill">Decision Tier Routing</div>
                <div class="hero-pill">Historical Validation</div>
                <div class="hero-pill">Analytics & Reporting</div>
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


def render_section_header(
    kicker: str,
    title: str,
    description: str
) -> None:

    st.markdown(
        f"""
        <div class="section-kicker">
            {escape(kicker)}
        </div>

        <div class="section-title">
            {escape(title)}
        </div>

        <div class="section-description">
            {escape(description)}
        </div>
        """,
        unsafe_allow_html=True
    )


def render_module_card(
    icon: str,
    title: str,
    description: str,
    footer: str
) -> None:

    st.markdown(
        f"""
        <div class="module-card">

            <div class="module-icon">
                {escape(icon)}
            </div>

            <div class="module-title">
                {escape(title)}
            </div>

            <div class="module-description">
                {escape(description)}
            </div>

            <div class="module-footer">
                <span>●</span>
                <span>{escape(footer)}</span>
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


def render_kpi_card(
    label: str,
    value: str,
    caption: str
) -> None:

    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-label">
                {escape(label)}
            </div>

            <div class="kpi-value">
                {escape(value)}
            </div>

            <div class="kpi-caption">
                {escape(caption)}
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )


def render_workflow() -> None:

    st.markdown(
        """
        <div class="workflow-shell">

            <div class="workflow-row">

                <div class="workflow-step">
                    <div class="workflow-step-number">1</div>
                    <div class="workflow-step-title">
                        Capture Incident
                    </div>
                </div>

                <div class="workflow-arrow">→</div>

                <div class="workflow-step">
                    <div class="workflow-step-number">2</div>
                    <div class="workflow-step-title">
                        Classify Four Targets
                    </div>
                </div>

                <div class="workflow-arrow">→</div>

                <div class="workflow-step">
                    <div class="workflow-step-number">3</div>
                    <div class="workflow-step-title">
                        Validate & Route
                    </div>
                </div>

                <div class="workflow-arrow">→</div>

                <div class="workflow-step">
                    <div class="workflow-step-number">4</div>
                    <div class="workflow-step-title">
                        Report & Analyse
                    </div>
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True
    )


def render_placeholder_page(
    icon: str,
    title: str,
    description: str,
    next_phase: str
) -> None:

    st.markdown(
        f"""
        <div class="hero-shell" style="padding: 2.3rem 2.5rem;">

            <div class="hero-eyebrow">
                Application Module
            </div>

            <div class="hero-title" style="font-size: 2.5rem;">
                {escape(icon)} {escape(title)}
            </div>

            <div class="hero-subtitle">
                {escape(description)}
            </div>

        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown(
        f"""
        <div class="info-panel">
            The backend for this module is ready. The complete interactive
            workflow will be implemented in <b>{escape(next_phase)}</b>.
        </div>
        """,
        unsafe_allow_html=True
    )


def render_footer() -> None:

    st.markdown(
        """
        <div class="app-footer">
            Voice-Assisted Workplace Incident Management System
            &nbsp;•&nbsp;
            Classification, decision support and safety analytics
        </div>
        """,
        unsafe_allow_html=True
    )
