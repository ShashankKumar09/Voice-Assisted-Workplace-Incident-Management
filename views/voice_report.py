"""
Voice Incident Reporting
"""

import streamlit as st

from ui.components import render_hero


def render() -> None:
    render_hero(
        eyebrow="Application Module",
        title="Voice Incident Reporting",
        subtitle="The guided voice workflow will be rebuilt after the manual module is stable.",
    )
    st.info(
        "This module is intentionally isolated while the clean application shell is validated."
    )
