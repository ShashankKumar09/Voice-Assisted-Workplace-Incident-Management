"""
Shared Streamlit UI theme.
"""

import streamlit as st


APP_CSS = """
<style>

.block-container {
    max-width: 1380px;
    padding-top: 2rem;
    padding-bottom: 3rem;
}

[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #102A43 0%,
            #174B67 58%,
            #1F6A82 100%
        );
}

[data-testid="stSidebar"] * {
    color: white;
}

.app-hero {
    padding: 2.8rem 3rem;
    border-radius: 26px;
    margin-bottom: 1.8rem;
    background:
        linear-gradient(
            125deg,
            #12344D 0%,
            #1B617D 55%,
            #2A829E 100%
        );
    color: white;
    box-shadow:
        0 22px 50px rgba(16, 42, 67, 0.18);
}

.app-eyebrow {
    font-size: 0.76rem;
    font-weight: 800;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    opacity: 0.80;
}

.app-title {
    font-size: 2.7rem;
    line-height: 1.12;
    font-weight: 800;
    margin-top: 0.8rem;
}

.app-subtitle {
    max-width: 850px;
    margin-top: 0.9rem;
    line-height: 1.7;
    font-size: 1rem;
    opacity: 0.84;
}

.status-card,
.module-card {
    height: 100%;
    padding: 1.25rem;
    border-radius: 18px;
    border: 1px solid #DCE6ED;
    background: white;
    box-shadow: 0 8px 22px rgba(26, 58, 79, 0.06);
}

.module-card {
    min-height: 190px;
}

.status-label {
    color: #6A7F8F;
    font-size: 0.74rem;
    font-weight: 800;
    letter-spacing: 0.07em;
    text-transform: uppercase;
}

.status-value {
    margin-top: 0.45rem;
    color: #17324D;
    font-size: 1.2rem;
    font-weight: 800;
}

.status-caption,
.module-description {
    margin-top: 0.35rem;
    color: #6F8290;
    font-size: 0.80rem;
    line-height: 1.5;
}

.module-icon {
    font-size: 1.6rem;
}

.module-title {
    margin-top: 0.8rem;
    color: #17324D;
    font-size: 1.05rem;
    font-weight: 800;
}

.section-title {
    margin-top: 1.4rem;
    margin-bottom: 1rem;
    color: #17324D;
    font-size: 1.55rem;
    font-weight: 800;
}

</style>
"""


def apply_theme() -> None:
    st.markdown(APP_CSS, unsafe_allow_html=True)
