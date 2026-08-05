
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
