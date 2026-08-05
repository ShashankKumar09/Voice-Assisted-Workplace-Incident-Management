"""
Reusable native Streamlit UI components.
"""

from html import escape
from typing import Iterable

import streamlit as st


def render_hero(
    eyebrow: str,
    title: str,
    subtitle: str,
    badges: Iterable[str] | None = None,
) -> None:
    badge_html = ""

    if badges:
        badge_html = "".join(
            f'<span class="hero-badge">{escape(str(item))}</span>'
            for item in badges
        )

    st.html(
        f"""
        <section class="app-hero">
            <div class="hero-glow hero-glow-one"></div>
            <div class="hero-glow hero-glow-two"></div>

            <div class="hero-content">
                <div class="app-eyebrow">{escape(eyebrow)}</div>

                <div class="app-title">
                    {escape(title)}
                </div>

                <div class="app-subtitle">
                    {escape(subtitle)}
                </div>

                <div class="hero-badge-row">
                    {badge_html}
                </div>
            </div>

            <div class="hero-side-mark">
                <div class="hero-side-icon">🛡️</div>
                <div class="hero-side-label">Incident Intelligence</div>
            </div>
        </section>
        """
    )


def render_section_heading(
    eyebrow: str,
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <div class="section-heading">
            <div class="section-eyebrow">{escape(eyebrow)}</div>
            <div class="section-title">{escape(title)}</div>
            <div class="section-description">{escape(description)}</div>
        </div>
        """
    )


def render_module_card(
    icon: str,
    number: str,
    title: str,
    description: str,
    accent: str,
) -> None:
    st.html(
        f"""
        <article class="module-card">
            <div class="module-card-top">
                <div class="module-icon">{escape(icon)}</div>
                <div class="module-number">{escape(number)}</div>
            </div>

            <div class="module-title">{escape(title)}</div>
            <div class="module-description">{escape(description)}</div>

            <div class="module-accent">
                <span class="module-accent-dot"></span>
                {escape(accent)}
            </div>
        </article>
        """
    )


def render_feature_card(
    icon: str,
    title: str,
    description: str,
) -> None:
    st.html(
        f"""
        <article class="feature-card">
            <div class="feature-icon">{escape(icon)}</div>
            <div class="feature-title">{escape(title)}</div>
            <div class="feature-description">{escape(description)}</div>
        </article>
        """
    )


def render_workflow(
    steps: list[tuple[str, str, str]],
) -> None:
    parts = []

    for index, (number, title, description) in enumerate(steps):
        parts.append(
            f"""
            <div class="workflow-step">
                <div class="workflow-number">{escape(number)}</div>
                <div class="workflow-text">
                    <div class="workflow-title">{escape(title)}</div>
                    <div class="workflow-description">{escape(description)}</div>
                </div>
            </div>
            """
        )

        if index < len(steps) - 1:
            parts.append('<div class="workflow-arrow">→</div>')

    st.html(
        f"""
        <div class="workflow-shell">
            <div class="workflow-row">
                {''.join(parts)}
            </div>
        </div>
        """
    )


# Kept for compatibility with existing placeholder views.
def render_status_card(
    label: str,
    value: str,
    caption: str,
) -> None:
    st.html(
        f"""
        <div class="status-card">
            <div class="status-label">{escape(label)}</div>
            <div class="status-value">{escape(value)}</div>
            <div class="status-caption">{escape(caption)}</div>
        </div>
        """
    )
