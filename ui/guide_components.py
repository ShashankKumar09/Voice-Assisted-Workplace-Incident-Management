"""
Shared user-guide components for application modules.
"""

from html import escape
from typing import Iterable

import streamlit as st


def render_module_header(
    eyebrow: str,
    title: str,
    description: str,
    icon: str,
) -> None:
    st.html(
        f"""
        <section class="module-page-hero">
            <div class="module-page-icon">{escape(icon)}</div>

            <div>
                <div class="module-page-eyebrow">{escape(eyebrow)}</div>
                <div class="module-page-title">{escape(title)}</div>
                <div class="module-page-description">{escape(description)}</div>
            </div>
        </section>
        """
    )


def render_user_guide(
    steps: Iterable[tuple[str, str]],
    note: str,
) -> None:
    step_html = []

    for index, (title, description) in enumerate(steps, start=1):
        step_html.append(
            f"""
            <div class="guide-step">
                <div class="guide-step-number">{index}</div>

                <div>
                    <div class="guide-step-title">
                        {escape(title)}
                    </div>

                    <div class="guide-step-description">
                        {escape(description)}
                    </div>
                </div>
            </div>
            """
        )

    st.html(
        f"""
        <section class="guide-shell">
            <div class="guide-heading-row">
                <div>
                    <div class="guide-eyebrow">User Guide</div>
                    <div class="guide-title">How to use this module</div>
                </div>

                <div class="guide-status">Step-by-step</div>
            </div>

            <div class="guide-grid">
                {''.join(step_html)}
            </div>

            <div class="guide-note">
                <b>Before you begin:</b> {escape(note)}
            </div>
        </section>
        """
    )


def render_backend_placeholder(
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <section class="backend-placeholder">
            <div class="backend-placeholder-icon">⚙️</div>

            <div>
                <div class="backend-placeholder-title">
                    {escape(title)}
                </div>

                <div class="backend-placeholder-description">
                    {escape(description)}
                </div>
            </div>
        </section>
        """
    )
