"""
Reusable native Streamlit UI components.
"""

from html import escape

import streamlit as st


def render_hero(eyebrow: str, title: str, subtitle: str) -> None:
    st.html(
        f"""
        <div class="app-hero">
            <div class="app-eyebrow">{escape(eyebrow)}</div>
            <div class="app-title">{escape(title)}</div>
            <div class="app-subtitle">{escape(subtitle)}</div>
        </div>
        """
    )


def render_status_card(label: str, value: str, caption: str) -> None:
    st.html(
        f"""
        <div class="status-card">
            <div class="status-label">{escape(label)}</div>
            <div class="status-value">{escape(value)}</div>
            <div class="status-caption">{escape(caption)}</div>
        </div>
        """
    )


def render_module_card(icon: str, title: str, description: str) -> None:
    st.html(
        f"""
        <div class="module-card">
            <div class="module-icon">{escape(icon)}</div>
            <div class="module-title">{escape(title)}</div>
            <div class="module-description">{escape(description)}</div>
        </div>
        """
    )
