"""Voice-Assisted Workplace Incident Management System."""

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

st.markdown(
    """
    <style>
    html, body, [data-testid="stAppViewContainer"] {
        font-family: Inter, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif;
        color: #17324D;
    }

    [data-testid="stAppViewContainer"] h1,
    [data-testid="stAppViewContainer"] h2,
    [data-testid="stAppViewContainer"] h3,
    [data-testid="stAppViewContainer"] h4 {
        color: #17324D !important;
        font-weight: 800 !important;
        letter-spacing: -0.025em !important;
        line-height: 1.22 !important;
    }

    [data-testid="stAppViewContainer"] h1 { font-size: 2rem !important; }
    [data-testid="stAppViewContainer"] h2 { font-size: 1.55rem !important; }
    [data-testid="stAppViewContainer"] h3 { font-size: 1.22rem !important; }

    [data-testid="stAppViewContainer"] [data-testid="stWidgetLabel"] p {
        color: #23445B !important;
        font-size: .82rem !important;
        font-weight: 700 !important;
    }

    [data-testid="stAppViewContainer"] [data-testid="stMarkdownContainer"] p,
    [data-testid="stAppViewContainer"] .stCaptionContainer,
    [data-testid="stAppViewContainer"] [data-testid="stAlertContainer"] {
        color: #526B7C;
        font-weight: 500;
    }

    [data-baseweb="input"] input,
    [data-baseweb="textarea"] textarea,
    [data-baseweb="select"] > div,
    [data-testid="stDateInput"] input {
        color: #17324D !important;
        font-weight: 550 !important;
        font-size: .9rem !important;
    }

    [data-baseweb="input"],
    [data-baseweb="textarea"],
    [data-baseweb="select"] > div,
    [data-testid="stFileUploaderDropzone"] {
        border-radius: 11px !important;
    }

    /* Base button geometry */
    [data-testid="stAppViewContainer"] button {
        min-height: 2.55rem;
        border-radius: 10px !important;
        font-weight: 700 !important;
    }

    /* Secondary buttons, download buttons and regular form buttons */
    [data-testid="stAppViewContainer"] button[data-testid="stBaseButton-secondary"],
    [data-testid="stAppViewContainer"] button[kind="secondary"],
    [data-testid="stAppViewContainer"] .stDownloadButton button,
    [data-testid="stAppViewContainer"] [data-testid="stFormSubmitButton"] button:not([data-testid="stBaseButton-primary"]) {
        color: #17324D !important;
        background: #FFFFFF !important;
        border: 1px solid #C9D8E1 !important;
    }

    [data-testid="stAppViewContainer"] button[data-testid="stBaseButton-secondary"] *,
    [data-testid="stAppViewContainer"] button[kind="secondary"] *,
    [data-testid="stAppViewContainer"] .stDownloadButton button *,
    [data-testid="stAppViewContainer"] [data-testid="stFormSubmitButton"] button:not([data-testid="stBaseButton-primary"]) * {
        color: #17324D !important;
        opacity: 1 !important;
        font-weight: 750 !important;
        fill: #17324D !important;
    }

    [data-testid="stAppViewContainer"] button[data-testid="stBaseButton-secondary"]:hover,
    [data-testid="stAppViewContainer"] button[kind="secondary"]:hover,
    [data-testid="stAppViewContainer"] .stDownloadButton button:hover {
        background: #F2F8FB !important;
        border-color: #2B8BA5 !important;
    }

    /* Primary buttons, including manual form submit and voice confirm */
    [data-testid="stAppViewContainer"] button[data-testid="stBaseButton-primary"],
    [data-testid="stAppViewContainer"] button[kind="primary"],
    [data-testid="stAppViewContainer"] [data-testid="stFormSubmitButton"] button[kind="primary"] {
        color: #FFFFFF !important;
        background: #1F7892 !important;
        border-color: #1F7892 !important;
    }

    [data-testid="stAppViewContainer"] button[data-testid="stBaseButton-primary"] *,
    [data-testid="stAppViewContainer"] button[kind="primary"] *,
    [data-testid="stAppViewContainer"] [data-testid="stFormSubmitButton"] button[kind="primary"] * {
        color: #FFFFFF !important;
        opacity: 1 !important;
        font-weight: 750 !important;
        fill: #FFFFFF !important;
    }

    [data-testid="stAppViewContainer"] button[data-testid="stBaseButton-primary"]:hover,
    [data-testid="stAppViewContainer"] button[kind="primary"]:hover {
        background: #17647C !important;
        border-color: #17647C !important;
    }

    /* Disabled buttons */
    [data-testid="stAppViewContainer"] button:disabled {
        color: #78909F !important;
        background: #EAF0F4 !important;
        border-color: #D5E0E7 !important;
        opacity: .78 !important;
    }

    [data-testid="stAppViewContainer"] button:disabled * {
        color: #78909F !important;
        fill: #78909F !important;
        opacity: 1 !important;
    }

    [data-testid="stForm"] {
        padding: 1.35rem !important;
        border: 1px solid #D9E6ED !important;
        border-radius: 18px !important;
        background: rgba(255,255,255,.78) !important;
        box-shadow: 0 8px 22px rgba(23,50,77,.05);
    }

    [data-testid="stForm"] h3 {
        margin-top: .55rem !important;
        margin-bottom: .7rem !important;
        padding-bottom: .45rem;
        border-bottom: 1px solid #E5EDF2;
    }

    [data-testid="stMetric"] {
        padding: 1rem 1.05rem;
        border: 1px solid #DCE6ED;
        border-radius: 15px;
        background: #FFFFFF;
        box-shadow: 0 6px 16px rgba(23,50,77,.04);
    }

    [data-testid="stDataFrame"] {
        border: 1px solid #DCE6ED;
        border-radius: 13px;
        overflow: hidden;
    }

    [data-testid="stSidebar"],
    [data-testid="stSidebar"] * {
        color: #FFFFFF !important;
    }

    [data-testid="stSidebarNav"] p,
    [data-testid="stSidebarNav"] span,
    [data-testid="stSidebarNav"] a {
        color: #FFFFFF !important;
        opacity: 1 !important;
        font-weight: 650 !important;
    }

    [data-testid="stSidebarNav"] a[aria-current="page"] {
        background: rgba(255,255,255,.14) !important;
    }

    [data-testid="stSidebarNav"] a:hover {
        background: rgba(255,255,255,.10) !important;
    }

    @media (max-width: 900px) {
        [data-testid="stAppViewContainer"] h1 { font-size: 1.7rem !important; }
        [data-testid="stAppViewContainer"] h2 { font-size: 1.38rem !important; }
    }
    </style>
    """,
    unsafe_allow_html=True,
)

pages = {
    "Incident Management": [
        st.Page(render_home, title="Home", icon=":material/home:", url_path="home", default=True),
        st.Page(render_voice, title="Voice Reporting", icon=":material/mic:", url_path="voice-reporting"),
        st.Page(render_manual, title="Manual Reporting", icon=":material/edit_document:", url_path="manual-reporting"),
        st.Page(render_batch, title="Batch Processing", icon=":material/upload_file:", url_path="batch-processing"),
        st.Page(render_analytics, title="Safety Analytics", icon=":material/monitoring:", url_path="safety-analytics"),
    ]
}

selected_page = st.navigation(pages, position="sidebar")
selected_page.run()
