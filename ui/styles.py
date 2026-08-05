"""
Shared professional UI styling for the Streamlit application.
"""

APP_CSS = """
<style>

/* -------------------------------------------------------------------------- */
/* Global application styling                                                 */
/* -------------------------------------------------------------------------- */

.stApp {
    background:
        radial-gradient(
            circle at top right,
            rgba(40, 106, 155, 0.08),
            transparent 32%
        ),
        linear-gradient(
            180deg,
            #F7FAFC 0%,
            #FFFFFF 48%,
            #F8FAFC 100%
        );
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
    color: #243746;
}

.block-container {
    max-width: 1440px;
    padding-top: 1.8rem;
    padding-bottom: 3rem;
    padding-left: 2.4rem;
    padding-right: 2.4rem;
}

/* Hide default Streamlit chrome */
#MainMenu {
    visibility: hidden;
}

footer {
    visibility: hidden;
}

header[data-testid="stHeader"] {
    background: transparent;
}

/* -------------------------------------------------------------------------- */
/* Sidebar                                                                     */
/* -------------------------------------------------------------------------- */

section[data-testid="stSidebar"] {
    background:
        linear-gradient(
            180deg,
            #102A43 0%,
            #173F5F 58%,
            #1F5A7A 100%
        );
    border-right: 1px solid rgba(255, 255, 255, 0.08);
}

section[data-testid="stSidebar"] * {
    color: #FFFFFF;
}

section[data-testid="stSidebar"] .stRadio label {
    padding: 0.72rem 0.85rem;
    border-radius: 12px;
    margin-bottom: 0.35rem;
    transition: all 0.2s ease;
}

section[data-testid="stSidebar"] .stRadio label:hover {
    background: rgba(255, 255, 255, 0.10);
    transform: translateX(2px);
}

.sidebar-brand {
    padding: 0.4rem 0.15rem 1.2rem 0.15rem;
}

.sidebar-brand-title {
    color: #FFFFFF;
    font-size: 1.06rem;
    font-weight: 750;
    line-height: 1.35;
    letter-spacing: -0.01em;
}

.sidebar-brand-subtitle {
    color: rgba(255, 255, 255, 0.68);
    font-size: 0.78rem;
    line-height: 1.5;
    margin-top: 0.45rem;
}

.sidebar-divider {
    height: 1px;
    background: rgba(255, 255, 255, 0.13);
    margin: 0.9rem 0 1.1rem 0;
}

/* -------------------------------------------------------------------------- */
/* Hero section                                                                */
/* -------------------------------------------------------------------------- */

.hero-shell {
    position: relative;
    overflow: hidden;
    border-radius: 28px;
    padding: 3.2rem 3.4rem;
    color: #FFFFFF;
    background:
        linear-gradient(
            125deg,
            #12344D 0%,
            #1E5C7A 52%,
            #287FA0 100%
        );
    box-shadow:
        0 28px 65px rgba(16, 42, 67, 0.20);
    margin-bottom: 2rem;
}

.hero-shell::before {
    content: "";
    position: absolute;
    width: 420px;
    height: 420px;
    right: -170px;
    top: -210px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.10);
}

.hero-shell::after {
    content: "";
    position: absolute;
    width: 240px;
    height: 240px;
    right: 90px;
    bottom: -160px;
    border-radius: 50%;
    background: rgba(255, 255, 255, 0.07);
}

.hero-eyebrow {
    position: relative;
    z-index: 2;
    display: inline-flex;
    align-items: center;
    gap: 0.45rem;
    padding: 0.48rem 0.78rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.14);
    border: 1px solid rgba(255, 255, 255, 0.18);
    font-size: 0.74rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

.hero-title {
    position: relative;
    z-index: 2;
    max-width: 920px;
    font-size: clamp(2.15rem, 4vw, 4.25rem);
    line-height: 1.05;
    font-weight: 790;
    letter-spacing: -0.045em;
    margin-top: 1.25rem;
    margin-bottom: 1rem;
}

.hero-subtitle {
    position: relative;
    z-index: 2;
    max-width: 850px;
    color: rgba(255, 255, 255, 0.82);
    font-size: 1.05rem;
    line-height: 1.75;
    margin-bottom: 1.5rem;
}

.hero-pill-row {
    position: relative;
    z-index: 2;
    display: flex;
    flex-wrap: wrap;
    gap: 0.65rem;
}

.hero-pill {
    padding: 0.56rem 0.85rem;
    border-radius: 999px;
    background: rgba(255, 255, 255, 0.10);
    border: 1px solid rgba(255, 255, 255, 0.17);
    color: rgba(255, 255, 255, 0.90);
    font-size: 0.82rem;
    font-weight: 600;
}

/* -------------------------------------------------------------------------- */
/* Section headers                                                             */
/* -------------------------------------------------------------------------- */

.section-kicker {
    color: #286A9B;
    font-size: 0.75rem;
    font-weight: 800;
    letter-spacing: 0.10em;
    text-transform: uppercase;
    margin-bottom: 0.4rem;
}

.section-title {
    color: #17324D;
    font-size: 1.75rem;
    font-weight: 780;
    letter-spacing: -0.025em;
    line-height: 1.25;
    margin-bottom: 0.5rem;
}

.section-description {
    color: #627486;
    font-size: 0.96rem;
    line-height: 1.65;
    margin-bottom: 1.35rem;
}

/* -------------------------------------------------------------------------- */
/* Module cards                                                                */
/* -------------------------------------------------------------------------- */

.module-card {
    height: 100%;
    min-height: 260px;
    padding: 1.55rem;
    border-radius: 20px;
    border: 1px solid #DCE6ED;
    background:
        linear-gradient(
            180deg,
            rgba(255, 255, 255, 0.98),
            rgba(248, 251, 253, 0.98)
        );
    box-shadow:
        0 10px 28px rgba(26, 58, 79, 0.07);
    transition:
        transform 0.22s ease,
        box-shadow 0.22s ease,
        border-color 0.22s ease;
}

.module-card:hover {
    transform: translateY(-5px);
    box-shadow:
        0 18px 38px rgba(26, 58, 79, 0.13);
    border-color: #A9CBDD;
}

.module-icon {
    display: inline-flex;
    width: 52px;
    height: 52px;
    align-items: center;
    justify-content: center;
    border-radius: 15px;
    font-size: 1.55rem;
    margin-bottom: 1.1rem;
    background: #EAF3F8;
    border: 1px solid #D2E6F0;
}

.module-title {
    color: #17324D;
    font-size: 1.08rem;
    line-height: 1.35;
    font-weight: 760;
    margin-bottom: 0.55rem;
}

.module-description {
    color: #627486;
    font-size: 0.88rem;
    line-height: 1.65;
    min-height: 88px;
}

.module-footer {
    display: flex;
    align-items: center;
    gap: 0.42rem;
    margin-top: 1rem;
    color: #286A9B;
    font-size: 0.80rem;
    font-weight: 700;
}

/* -------------------------------------------------------------------------- */
/* KPI cards                                                                   */
/* -------------------------------------------------------------------------- */

.kpi-card {
    padding: 1.25rem 1.35rem;
    border-radius: 17px;
    background: #FFFFFF;
    border: 1px solid #DCE6ED;
    box-shadow: 0 8px 22px rgba(26, 58, 79, 0.06);
}

.kpi-label {
    color: #6A7F8F;
    font-size: 0.74rem;
    font-weight: 760;
    letter-spacing: 0.06em;
    text-transform: uppercase;
}

.kpi-value {
    color: #17324D;
    font-size: 1.65rem;
    font-weight: 800;
    margin-top: 0.35rem;
    letter-spacing: -0.025em;
}

.kpi-caption {
    color: #7B8D9A;
    font-size: 0.76rem;
    margin-top: 0.25rem;
}

/* -------------------------------------------------------------------------- */
/* Workflow strip                                                              */
/* -------------------------------------------------------------------------- */

.workflow-shell {
    padding: 1.4rem;
    border-radius: 20px;
    border: 1px solid #DCE6ED;
    background: #FFFFFF;
    box-shadow: 0 8px 22px rgba(26, 58, 79, 0.05);
}

.workflow-row {
    display: grid;
    grid-template-columns:
        minmax(120px, 1fr)
        34px
        minmax(120px, 1fr)
        34px
        minmax(120px, 1fr)
        34px
        minmax(120px, 1fr);
    gap: 0.4rem;
    align-items: center;
}

.workflow-step {
    text-align: center;
    padding: 1rem 0.7rem;
    border-radius: 14px;
    background: #F5F9FC;
    border: 1px solid #E0EAF0;
}

.workflow-step-number {
    display: inline-flex;
    width: 28px;
    height: 28px;
    align-items: center;
    justify-content: center;
    border-radius: 999px;
    color: #FFFFFF;
    background: #286A9B;
    font-size: 0.75rem;
    font-weight: 800;
    margin-bottom: 0.5rem;
}

.workflow-step-title {
    color: #17324D;
    font-size: 0.86rem;
    font-weight: 760;
}

.workflow-arrow {
    color: #7FA9BE;
    text-align: center;
    font-size: 1.25rem;
    font-weight: 800;
}

/* -------------------------------------------------------------------------- */
/* Status / information panels                                                 */
/* -------------------------------------------------------------------------- */

.info-panel {
    border-radius: 16px;
    padding: 1rem 1.15rem;
    border: 1px solid #CDE2EC;
    background: #EDF7FB;
    color: #31566B;
    font-size: 0.88rem;
    line-height: 1.6;
}

.success-panel {
    border-radius: 16px;
    padding: 1rem 1.15rem;
    border: 1px solid #BFE3D7;
    background: #ECF8F4;
    color: #216B58;
    font-size: 0.88rem;
    line-height: 1.6;
}

/* -------------------------------------------------------------------------- */
/* Streamlit controls                                                          */
/* -------------------------------------------------------------------------- */

.stButton > button {
    width: 100%;
    border-radius: 12px;
    border: 1px solid #286A9B;
    background: #286A9B;
    color: #FFFFFF;
    font-weight: 700;
    padding: 0.72rem 1rem;
    transition: all 0.20s ease;
}

.stButton > button:hover {
    background: #1F597E;
    border-color: #1F597E;
    color: #FFFFFF;
    box-shadow: 0 8px 18px rgba(40, 106, 155, 0.22);
}

.stDownloadButton > button {
    width: 100%;
    border-radius: 12px;
    font-weight: 700;
}

div[data-testid="stTextInput"] input,
div[data-testid="stNumberInput"] input,
div[data-testid="stTextArea"] textarea,
div[data-testid="stDateInput"] input,
div[data-testid="stSelectbox"] > div > div {
    border-radius: 11px;
}

/* -------------------------------------------------------------------------- */
/* Footer                                                                      */
/* -------------------------------------------------------------------------- */

.app-footer {
    margin-top: 3rem;
    padding-top: 1.2rem;
    border-top: 1px solid #DCE6ED;
    color: #7A8D9B;
    font-size: 0.76rem;
    line-height: 1.5;
    text-align: center;
}

/* -------------------------------------------------------------------------- */
/* Responsive                                                                  */
/* -------------------------------------------------------------------------- */

@media (max-width: 900px) {

    .block-container {
        padding-left: 1rem;
        padding-right: 1rem;
    }

    .hero-shell {
        padding: 2.2rem 1.6rem;
        border-radius: 22px;
    }

    .workflow-row {
        grid-template-columns: 1fr;
    }

    .workflow-arrow {
        transform: rotate(90deg);
    }
}

</style>
"""
