"""
Shared Streamlit UI theme.
"""

import streamlit as st


APP_CSS = """
<style>

:root {
    --ink: #17324D;
    --muted: #687B8A;
    --line: #DCE6ED;
    --panel: #FFFFFF;
    --soft: #F3F7FA;
    --blue: #1F6A86;
    --blue-dark: #123B56;
    --blue-light: #2A8AA6;
}

html,
body,
[class*="css"] {
    font-family:
        Inter,
        -apple-system,
        BlinkMacSystemFont,
        "Segoe UI",
        sans-serif;
}

.stApp {
    background:
        radial-gradient(
            circle at 88% 8%,
            rgba(42, 138, 166, 0.08),
            transparent 24rem
        ),
        linear-gradient(
            180deg,
            #F7FAFC 0%,
            #FFFFFF 52%,
            #F7FAFC 100%
        );
}

.block-container {
    max-width: 1480px;
    padding-top: 2.1rem;
    padding-bottom: 3.5rem;
    padding-left: 2.2rem;
    padding-right: 2.2rem;
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
    color: #FFFFFF;
}

[data-testid="stSidebarNav"] {
    padding-top: 0.75rem;
}

[data-testid="stSidebarNav"] a {
    border-radius: 10px;
    margin-bottom: 0.2rem;
}

[data-testid="stSidebarNav"] a:hover {
    background: rgba(255,255,255,0.10);
}

.app-hero {
    position: relative;
    overflow: hidden;
    display: grid;
    grid-template-columns: minmax(0, 1fr) 190px;
    align-items: center;
    min-height: 290px;
    padding: 3.1rem 3.25rem;
    border-radius: 28px;
    margin-bottom: 3.2rem;
    color: #FFFFFF;
    background:
        linear-gradient(
            122deg,
            #123B56 0%,
            #1C6681 58%,
            #2B8BA5 100%
        );
    box-shadow:
        0 28px 68px rgba(16, 42, 67, 0.22);
}

.hero-content {
    position: relative;
    z-index: 2;
}

.hero-glow {
    position: absolute;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.08);
}

.hero-glow-one {
    width: 420px;
    height: 420px;
    right: -160px;
    top: -250px;
}

.hero-glow-two {
    width: 240px;
    height: 240px;
    right: 130px;
    bottom: -185px;
}

.app-eyebrow {
    display: inline-flex;
    padding: 0.42rem 0.7rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.10);
    font-size: 0.72rem;
    font-weight: 800;
    letter-spacing: 0.11em;
    text-transform: uppercase;
}

.app-title {
    max-width: 980px;
    margin-top: 1.05rem;
    font-size: clamp(2rem, 3.35vw, 3.55rem);
    line-height: 1.04;
    letter-spacing: -0.045em;
    font-weight: 850;
}

.app-subtitle {
    max-width: 860px;
    margin-top: 1.1rem;
    color: rgba(255,255,255,0.82);
    font-size: 1.08rem;
    line-height: 1.72;
}

.hero-badge-row {
    display: flex;
    flex-wrap: wrap;
    gap: 0.58rem;
    margin-top: 1.55rem;
}

.hero-badge {
    padding: 0.5rem 0.75rem;
    border-radius: 999px;
    border: 1px solid rgba(255,255,255,0.16);
    background: rgba(255,255,255,0.09);
    color: rgba(255,255,255,0.90);
    font-size: 0.78rem;
    font-weight: 650;
}

.hero-side-mark {
    position: relative;
    z-index: 2;
    justify-self: end;
    width: 150px;
    padding: 1.25rem 1rem;
    border-radius: 22px;
    text-align: center;
    border: 1px solid rgba(255,255,255,0.17);
    background: rgba(255,255,255,0.10);
    backdrop-filter: blur(8px);
}

.hero-side-icon {
    font-size: 2.2rem;
}

.hero-side-label {
    margin-top: 0.65rem;
    color: rgba(255,255,255,0.84);
    font-size: 0.72rem;
    font-weight: 750;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}


.intro-strip {
    display: grid;
    grid-template-columns: 12px minmax(0, 1fr);
    gap: 0.85rem;
    align-items: start;
    margin: -1.15rem 0 2.2rem 0;
    padding: 1.15rem 1.35rem;
    border-radius: 18px;
    border: 1px solid #D7E5EC;
    background: rgba(255, 255, 255, 0.92);
    box-shadow: 0 9px 24px rgba(26, 58, 79, 0.06);
}

.intro-strip-mark {
    color: #2B8BA5;
    font-size: 0.72rem;
    line-height: 1.8;
}

.intro-strip-title {
    color: var(--ink);
    font-size: 0.98rem;
    font-weight: 820;
}

.intro-strip-description {
    max-width: 980px;
    margin-top: 0.28rem;
    color: var(--muted);
    font-size: 0.86rem;
    line-height: 1.62;
}

.section-heading {
    margin-top: 1.35rem;
    margin-bottom: 1.25rem;
}

.section-eyebrow {
    color: #2B7897;
    font-size: 0.72rem;
    font-weight: 850;
    letter-spacing: 0.12em;
    text-transform: uppercase;
}

.section-title {
    margin-top: 0.42rem;
    color: var(--ink);
    font-size: 1.62rem;
    line-height: 1.2;
    font-weight: 850;
    letter-spacing: -0.025em;
}

.section-description {
    max-width: 900px;
    margin-top: 0.5rem;
    color: var(--muted);
    font-size: 0.91rem;
    line-height: 1.7;
}

.module-card {
    position: relative;
    overflow: hidden;
    min-height: 245px;
    padding: 1.55rem 1.65rem;
    margin-bottom: 1rem;
    border-radius: 22px;
    border: 1px solid var(--line);
    background:
        linear-gradient(
            180deg,
            rgba(255,255,255,0.99),
            rgba(247,250,252,0.99)
        );
    box-shadow:
        0 12px 30px rgba(26, 58, 79, 0.07);
    transition:
        transform 0.22s ease,
        box-shadow 0.22s ease,
        border-color 0.22s ease;
}

.module-card::after {
    content: "";
    position: absolute;
    width: 130px;
    height: 130px;
    right: -70px;
    bottom: -72px;
    border-radius: 999px;
    background: rgba(42, 138, 166, 0.07);
}

.module-card:hover {
    transform: translateY(-5px);
    border-color: #AFCEDB;
    box-shadow:
        0 20px 42px rgba(26, 58, 79, 0.12);
}

.module-card-top {
    display: flex;
    align-items: center;
    justify-content: space-between;
}

.module-icon {
    display: inline-flex;
    width: 54px;
    height: 54px;
    align-items: center;
    justify-content: center;
    border-radius: 16px;
    border: 1px solid #D4E6EE;
    background: #EAF4F8;
    font-size: 1.45rem;
}

.module-number {
    color: #A1B4C1;
    font-size: 0.78rem;
    font-weight: 850;
    letter-spacing: 0.10em;
}

.module-title {
    margin-top: 1.2rem;
    color: var(--ink);
    font-size: 1.12rem;
    line-height: 1.35;
    font-weight: 830;
}

.module-description {
    max-width: 600px;
    min-height: 76px;
    margin-top: 0.55rem;
    color: var(--muted);
    font-size: 0.87rem;
    line-height: 1.65;
}

.module-accent {
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    margin-top: 1rem;
    color: #2B7897;
    font-size: 0.76rem;
    font-weight: 750;
}

.module-accent-dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: #2B8BA5;
}

.workflow-shell {
    padding: 1.1rem;
    margin-bottom: 2.3rem;
    border-radius: 22px;
    border: 1px solid var(--line);
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(26,58,79,0.06);
}

.workflow-row {
    display: grid;
    grid-template-columns:
        minmax(150px, 1fr)
        28px
        minmax(150px, 1fr)
        28px
        minmax(150px, 1fr)
        28px
        minmax(150px, 1fr)
        28px
        minmax(150px, 1fr);
    gap: 0.35rem;
    align-items: center;
}

.workflow-step {
    display: flex;
    gap: 0.75rem;
    align-items: center;
    padding: 1rem 0.9rem;
    border-radius: 15px;
    background: #F4F8FA;
    border: 1px solid #E2EBF0;
}

.workflow-number {
    display: inline-flex;
    min-width: 30px;
    height: 30px;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    color: #FFFFFF;
    background: #1F6A86;
    font-size: 0.72rem;
    font-weight: 850;
}

.workflow-title {
    color: var(--ink);
    font-size: 0.84rem;
    font-weight: 820;
}

.workflow-description {
    margin-top: 0.12rem;
    color: #788A96;
    font-size: 0.70rem;
    line-height: 1.35;
}

.workflow-arrow {
    color: #88AFC0;
    text-align: center;
    font-size: 1.15rem;
    font-weight: 850;
}

.feature-card {
    min-height: 190px;
    padding: 1.4rem;
    border-radius: 20px;
    border: 1px solid var(--line);
    background: #FFFFFF;
    box-shadow: 0 9px 24px rgba(26,58,79,0.06);
}

.feature-icon {
    font-size: 1.55rem;
}

.feature-title {
    margin-top: 0.8rem;
    color: var(--ink);
    font-size: 1rem;
    font-weight: 820;
}

.feature-description {
    margin-top: 0.45rem;
    color: var(--muted);
    font-size: 0.84rem;
    line-height: 1.6;
}

.home-footer-note {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.55rem;
    margin-top: 2.7rem;
    padding-top: 1.2rem;
    border-top: 1px solid var(--line);
    color: #718592;
    font-size: 0.76rem;
}

.home-footer-dot {
    width: 7px;
    height: 7px;
    border-radius: 999px;
    background: #2B8BA5;
}

.status-card {
    height: 100%;
    padding: 1.25rem;
    border-radius: 18px;
    border: 1px solid var(--line);
    background: #FFFFFF;
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
    color: var(--ink);
    font-size: 1.2rem;
    font-weight: 800;
}

.status-caption {
    margin-top: 0.35rem;
    color: #6F8290;
    font-size: 0.80rem;
    line-height: 1.5;
}

@media (max-width: 1100px) {

    .app-hero {
        grid-template-columns: 1fr;
    }

    .hero-side-mark {
        display: none;
    }

    .workflow-row {
        grid-template-columns: 1fr;
    }

    .workflow-arrow {
        transform: rotate(90deg);
    }
}

@media (max-width: 760px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .app-hero {
        padding: 2.2rem 1.6rem;
        border-radius: 22px;
    }

    .app-title {
        font-size: 2.15rem;
    }
}


/* -------------------------------------------------------------------------- */
/* Module page guides                                                         */
/* -------------------------------------------------------------------------- */

.module-page-hero {
    display: grid;
    grid-template-columns: 74px minmax(0, 1fr);
    gap: 1.25rem;
    align-items: center;
    padding: 2rem 2.2rem;
    margin-bottom: 1.35rem;
    border-radius: 24px;
    color: #FFFFFF;
    background:
        linear-gradient(
            125deg,
            #123B56 0%,
            #1C6681 60%,
            #2B8BA5 100%
        );
    box-shadow: 0 18px 42px rgba(16, 42, 67, 0.17);
}

.module-page-icon {
    display: inline-flex;
    width: 66px;
    height: 66px;
    align-items: center;
    justify-content: center;
    border-radius: 19px;
    border: 1px solid rgba(255,255,255,0.18);
    background: rgba(255,255,255,0.11);
    font-size: 1.8rem;
}

.module-page-eyebrow,
.guide-eyebrow {
    font-size: 0.71rem;
    font-weight: 850;
    letter-spacing: 0.11em;
    text-transform: uppercase;
}

.module-page-eyebrow {
    color: rgba(255,255,255,0.72);
}

.module-page-title {
    margin-top: 0.35rem;
    font-size: 2.05rem;
    line-height: 1.15;
    font-weight: 850;
    letter-spacing: -0.03em;
}

.module-page-description {
    max-width: 900px;
    margin-top: 0.55rem;
    color: rgba(255,255,255,0.82);
    font-size: 0.94rem;
    line-height: 1.65;
}

.guide-shell {
    padding: 1.45rem;
    margin-bottom: 1.3rem;
    border-radius: 22px;
    border: 1px solid #DCE6ED;
    background: #FFFFFF;
    box-shadow: 0 10px 28px rgba(26,58,79,0.06);
}

.guide-heading-row {
    display: flex;
    align-items: center;
    justify-content: space-between;
    gap: 1rem;
    margin-bottom: 1.15rem;
}

.guide-eyebrow {
    color: #2B7897;
}

.guide-title {
    margin-top: 0.3rem;
    color: #17324D;
    font-size: 1.35rem;
    font-weight: 840;
}

.guide-status {
    padding: 0.42rem 0.68rem;
    border-radius: 999px;
    color: #256D86;
    background: #EAF4F8;
    border: 1px solid #D3E7EF;
    font-size: 0.72rem;
    font-weight: 750;
}

.guide-grid {
    display: grid;
    grid-template-columns: repeat(5, minmax(0, 1fr));
    gap: 0.75rem;
}

.guide-step {
    min-height: 155px;
    padding: 1rem;
    border-radius: 16px;
    border: 1px solid #E0E9EE;
    background: #F7FAFC;
}

.guide-step-number {
    display: inline-flex;
    width: 29px;
    height: 29px;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    color: #FFFFFF;
    background: #1F6A86;
    font-size: 0.72rem;
    font-weight: 850;
}

.guide-step-title {
    margin-top: 0.75rem;
    color: #17324D;
    font-size: 0.84rem;
    font-weight: 820;
}

.guide-step-description {
    margin-top: 0.35rem;
    color: #6A7D8B;
    font-size: 0.74rem;
    line-height: 1.5;
}

.guide-note {
    margin-top: 1rem;
    padding: 0.85rem 1rem;
    border-radius: 14px;
    border-left: 4px solid #2B8BA5;
    background: #EEF7FA;
    color: #31566B;
    font-size: 0.80rem;
    line-height: 1.55;
}

.backend-placeholder {
    display: grid;
    grid-template-columns: 48px minmax(0, 1fr);
    gap: 0.9rem;
    align-items: center;
    padding: 1.1rem 1.2rem;
    border-radius: 17px;
    border: 1px dashed #B8CED9;
    background: rgba(244,248,250,0.85);
}

.backend-placeholder-icon {
    display: inline-flex;
    width: 44px;
    height: 44px;
    align-items: center;
    justify-content: center;
    border-radius: 13px;
    background: #E7F1F5;
    font-size: 1.25rem;
}

.backend-placeholder-title {
    color: #17324D;
    font-size: 0.93rem;
    font-weight: 820;
}

.backend-placeholder-description {
    margin-top: 0.25rem;
    color: #6A7D8B;
    font-size: 0.79rem;
    line-height: 1.55;
}

@media (max-width: 1100px) {
    .guide-grid {
        grid-template-columns: repeat(2, minmax(0, 1fr));
    }
}

@media (max-width: 700px) {
    .module-page-hero {
        grid-template-columns: 1fr;
    }

    .guide-grid {
        grid-template-columns: 1fr;
    }

    .guide-heading-row {
        align-items: flex-start;
        flex-direction: column;
    }
}

</style>
"""


def apply_theme() -> None:
    st.markdown(
        APP_CSS,
        unsafe_allow_html=True,
    )
