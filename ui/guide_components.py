"""Shared contextual guidance components for application pages."""
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


def render_section_header(
    number: str,
    title: str,
    description: str = "",
    icon: str = "",
) -> None:
    """Render a consistent, compact workflow section header."""
    description_html = (
        f'<div style="margin-top:.3rem;color:#6A7F8F;font-size:.86rem;line-height:1.5;">'
        f'{escape(description)}</div>'
        if description
        else ""
    )
    icon_html = (
        f'<div style="font-size:1.25rem;line-height:1;">{escape(icon)}</div>'
        if icon
        else ""
    )
    st.html(
        f"""
        <section style="
            margin:1.35rem 0 .75rem 0;
            padding:1rem 1.15rem;
            border:1px solid #D9E6ED;
            border-left:5px solid #2B8BA5;
            border-radius:16px;
            background:linear-gradient(135deg,#FFFFFF 0%,#F4FAFC 100%);
            box-shadow:0 8px 20px rgba(23,50,77,.06);
        ">
            <div style="display:flex;align-items:center;gap:.85rem;">
                <div style="
                    width:2rem;height:2rem;display:flex;align-items:center;justify-content:center;
                    border-radius:999px;background:#1F6A86;color:#FFFFFF;
                    font-size:.82rem;font-weight:800;flex:0 0 auto;
                ">{escape(str(number))}</div>
                {icon_html}
                <div style="min-width:0;">
                    <div style="color:#17324D;font-size:1.25rem;line-height:1.25;font-weight:850;">
                        {escape(title)}
                    </div>
                    {description_html}
                </div>
            </div>
        </section>
        """
    )


def render_user_guide(
    title: str,
    steps: Iterable[tuple[str, str]],
    note: str,
) -> None:
    step_html = []
    for index, (step_title, description) in enumerate(steps, start=1):
        step_html.append(
            f"""
            <div class="guide-step">
                <div class="guide-step-number">{index}</div>
                <div>
                    <div class="guide-step-title">{escape(step_title)}</div>
                    <div class="guide-step-description">{escape(description)}</div>
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
                    <div class="guide-title">{escape(title)}</div>
                </div>
                <div class="guide-status">Step-by-step</div>
            </div>
            <div class="guide-grid">{''.join(step_html)}</div>
            <div class="guide-note"><b>Before you begin:</b> {escape(note)}</div>
        </section>
        """
    )


def render_dashboard_overview(
    description: str,
    capabilities: Iterable[tuple[str, str, str]],
) -> None:
    cards = []
    for icon, title, detail in capabilities:
        cards.append(
            f"""
            <article class="feature-card">
                <div class="feature-icon">{escape(icon)}</div>
                <div class="feature-title">{escape(title)}</div>
                <div class="feature-description">{escape(detail)}</div>
            </article>
            """
        )

    st.html(
        f"""
        <section class="guide-shell">
            <div class="guide-heading-row">
                <div>
                    <div class="guide-eyebrow">Dashboard Overview</div>
                    <div class="guide-title">What This Dashboard Provides</div>
                </div>
                <div class="guide-status">Management insight</div>
            </div>
            <div class="section-description" style="margin-bottom:1.1rem;">
                {escape(description)}
            </div>
            <div style="display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:.9rem;">
                {''.join(cards)}
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
                <div class="backend-placeholder-title">{escape(title)}</div>
                <div class="backend-placeholder-description">{escape(description)}</div>
            </div>
        </section>
        """
    )
