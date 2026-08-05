"""
Manual Incident Reporting
"""

import streamlit as st

from ui.components import render_hero


def render() -> None:
    render_hero(
        eyebrow="Application Module",
        title="Manual Incident Reporting",
        subtitle="The clean manual reporting workflow will be rebuilt next.",
    )
    st.info(
        "This module is intentionally isolated while the clean application shell is validated."
    )
