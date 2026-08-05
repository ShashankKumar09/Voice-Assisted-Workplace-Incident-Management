"""
Voice-Assisted Workplace Incident Management System

Professional Streamlit application shell.
"""

from __future__ import annotations

from pathlib import Path

import streamlit as st

from core.predictor import IncidentPredictor
from pages.home import render_home_page
from pages.voice_reporting import render_voice_reporting_page
from pages.manual_reporting import render_manual_reporting_page
from pages.batch_processing import render_batch_processing_page
from pages.analytics_dashboard import render_analytics_dashboard_page
from ui.components import (
    render_footer,
    render_placeholder_page,
    render_sidebar_brand,
)
from ui.styles import APP_CSS


# ------------------------------------------------------------------------------
# Streamlit page configuration
# ------------------------------------------------------------------------------

st.set_page_config(
    page_title=(
        "Voice-Assisted Workplace Incident "
        "Management System"
    ),
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown(
    APP_CSS,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# Application paths
# ------------------------------------------------------------------------------

APP_ROOT = Path(
    __file__
).resolve().parent

INCIDENT_DATA_PATH = (
    APP_ROOT
    / "data"
    / "incident_records.csv"
)

# ------------------------------------------------------------------------------
# Session-state initialization
# ------------------------------------------------------------------------------

SESSION_DEFAULTS = {
    "active_module":
        "Home",

    "voice_incident_data":
        {},

    "voice_current_field_index":
        0,

    "voice_prediction_result":
        None,

    "manual_prediction_result":
        None,

    "batch_processing_result":
        None,

    "dashboard_filters":
        {}
}

for key, default_value in SESSION_DEFAULTS.items():

    if key not in st.session_state:

        st.session_state[
            key
        ] = default_value

# ------------------------------------------------------------------------------
# Cached backend loader
# ------------------------------------------------------------------------------

@st.cache_resource(
    show_spinner=False
)
def load_application_predictor():

    return IncidentPredictor(
        application_root=APP_ROOT,
        device="auto"
    )

# Do not load the 540 MB model on the home screen.
# It will load only when a classification module first needs it.

# ------------------------------------------------------------------------------
# Sidebar
# ------------------------------------------------------------------------------

render_sidebar_brand()

navigation_options = [
    "Home",
    "Voice Incident Reporting",
    "Manual Incident Reporting",
    "Batch Incident Processing",
    "Safety Analytics Dashboard"
]

selected_module = st.sidebar.radio(
    "Navigation",
    options=navigation_options,
    index=navigation_options.index(
        st.session_state.get(
            "active_module",
            "Home"
        )
    ),
    label_visibility="collapsed"
)

st.session_state[
    "active_module"
] = selected_module

st.sidebar.markdown(
    """
    <div class="sidebar-divider"></div>

    <div style="
        color: rgba(255,255,255,0.62);
        font-size: 0.73rem;
        line-height: 1.55;
        padding: 0 0.15rem;
    ">
        Classification outputs:<br/>
        Nature • Body • Event • Source
        <br/><br/>
        Final routing:<br/>
        Auto Fill • Suggest Review • Manual Review
    </div>
    """,
    unsafe_allow_html=True
)

# ------------------------------------------------------------------------------
# Page routing
# ------------------------------------------------------------------------------

if selected_module == "Home":

    render_home_page(
        incident_data_path=
            INCIDENT_DATA_PATH
    )

elif selected_module == "Voice Incident Reporting":

    render_voice_reporting_page(
        predictor_loader=load_application_predictor,
        incident_data_path=INCIDENT_DATA_PATH
    )

elif selected_module == "Manual Incident Reporting":

    render_manual_reporting_page(
        predictor_loader=load_application_predictor,
        incident_data_path=INCIDENT_DATA_PATH
    )

elif selected_module == "Batch Incident Processing":

    render_batch_processing_page(
        application_root=APP_ROOT,
        predictor_loader=load_application_predictor,
        incident_data_path=INCIDENT_DATA_PATH
    )

elif selected_module == "Safety Analytics Dashboard":

    render_analytics_dashboard_page(
        incident_data_path=INCIDENT_DATA_PATH
    )

render_footer()
