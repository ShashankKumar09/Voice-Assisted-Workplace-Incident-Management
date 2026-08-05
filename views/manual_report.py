"""
Manual Incident Reporting page.
"""

from ui.guide_components import (
    render_backend_placeholder,
    render_module_header,
    render_user_guide,
)


def render() -> None:
    render_module_header(
        eyebrow="Structured Incident Entry",
        title="Manual Incident Reporting",
        description=(
            "Enter workplace incident details through a structured form, validate "
            "the information and generate a classified incident report."
        ),
        icon="📝",
    )

    render_user_guide(
        title="How to Use Manual Incident Reporting",
        steps=[
            (
                "Open a new incident form",
                "Begin a structured single-incident report.",
            ),
            (
                "Complete the incident fields",
                "Enter identification, employer, location and outcome details.",
            ),
            (
                "Write the final narrative",
                "Describe the activity, event, injury, body part and source.",
            ),
            (
                "Review and validate",
                "Correct missing or invalid values before submission.",
            ),
            (
                "Classify and download",
                "Review predictions, confidence, decision tier and report files.",
            ),
        ],
        note=(
            "Ensure the Final Narrative is complete and specific because it is "
            "the primary input used for classification."
        ),
    )

    render_backend_placeholder(
        title="Manual reporting integration is next",
        description=(
            "The validated 18-field form, predictor, decision engine and "
            "PDF/CSV downloads will be connected in the next implementation step."
        ),
    )
