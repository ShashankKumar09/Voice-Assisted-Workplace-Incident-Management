"""
Voice Incident Reporting page.
"""

from ui.guide_components import (
    render_backend_placeholder,
    render_module_header,
    render_user_guide,
)


def render() -> None:
    render_module_header(
        eyebrow="Guided Incident Capture",
        title="Voice Incident Reporting",
        description=(
            "Record incident details one field at a time, review the recognized "
            "text and submit the completed narrative for classification."
        ),
        icon="🎤",
    )

    render_user_guide(
        title="How to Use Voice Incident Reporting",
        steps=[
            (
                "Start a new report",
                "Open the module and begin the guided reporting workflow.",
            ),
            (
                "Record each response",
                "Use the connected microphone to answer one incident question at a time.",
            ),
            (
                "Review the transcript",
                "Correct any speech-to-text errors before confirming the field.",
            ),
            (
                "Complete the final review",
                "Verify all incident details and the final narrative.",
            ),
            (
                "Classify and download",
                "Run classification, review the decision tier and download the report.",
            ),
        ],
        note=(
            "Connect a microphone to your device, speak clearly in a quiet "
            "environment, and review the transcript before proceeding."
        ),
    )

    render_backend_placeholder(
        title="Voice workflow integration is next",
        description=(
            "The microphone, speech recognition, classification and "
            "report-generation services will be connected after this page "
            "structure is approved."
        ),
    )
