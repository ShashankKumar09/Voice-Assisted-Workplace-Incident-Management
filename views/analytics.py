"""
Safety Analytics Dashboard
"""

import streamlit as st

from ui.components import render_hero


def render() -> None:
    render_hero(
        eyebrow="Application Module",
        title="Safety Analytics Dashboard",
        subtitle="The analytics engine is preserved and will be connected later.",
    )
    st.info(
        "This module is intentionally isolated while the clean application shell is validated."
    )
