"""
Voice-Assisted Workplace Incident Management System.

Clean Streamlit application entry point.
"""

import streamlit as st

from ui.theme import apply_theme
from views.analytics import render as render_analytics
from views.batch_process import render as render_batch
from views.home import render as render_home
from views.manual_report import render as render_manual
from views.voice_report import render as render_voice


st.set_page_config(
    page_title="Voice-Assisted Workplace Incident Management System",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded",
)

apply_theme()

pages = {
    "Incident Management": [
        st.Page(
            render_home,
            title="Home",
            icon=":material/home:",
            default=True,
        ),
        st.Page(
            render_voice,
            title="Voice Reporting",
            icon=":material/mic:",
        ),
        st.Page(
            render_manual,
            title="Manual Reporting",
            icon=":material/edit_document:",
        ),
        st.Page(
            render_batch,
            title="Batch Processing",
            icon=":material/upload_file:",
        ),
        st.Page(
            render_analytics,
            title="Safety Analytics",
            icon=":material/monitoring:",
        ),
    ]
}

selected_page = st.navigation(pages, position="sidebar")
selected_page.run()
