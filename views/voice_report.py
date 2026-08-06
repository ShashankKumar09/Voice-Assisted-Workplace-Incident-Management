"""
Voice Incident Reporting page.

Stage 1:
Guided field-by-field incident capture workflow.
Microphone transcription and classification will be connected next.
"""

from __future__ import annotations

from html import escape
from typing import Dict, List

import streamlit as st

from ui.guide_components import (
    render_module_header,
    render_user_guide,
)


# ==============================================================================
# Guided voice-reporting fields
# ==============================================================================

VOICE_FIELDS: List[Dict[str, object]] = [
    {
        "key": "ID",
        "label": "Incident ID",
        "question": "Please provide the Incident ID.",
        "example": "INC-1001",
        "required": True,
    },
    {
        "key": "UPA",
        "label": "UPA",
        "question": "Please provide the UPA reference.",
        "example": "UPA-2501",
        "required": False,
    },
    {
        "key": "EventDate",
        "label": "Event Date",
        "question": "Please provide the date when the incident occurred.",
        "example": "5 August 2026",
        "required": False,
    },
    {
        "key": "Employer",
        "label": "Employer",
        "question": "Please provide the employer name.",
        "example": "ABC Manufacturing",
        "required": False,
    },
    {
        "key": "Address1",
        "label": "Address Line 1",
        "question": "Please provide Address Line 1.",
        "example": "100 Industrial Road",
        "required": False,
    },
    {
        "key": "Address2",
        "label": "Address Line 2",
        "question": "Please provide Address Line 2, or skip this field.",
        "example": "Building B",
        "required": False,
    },
    {
        "key": "City",
        "label": "City",
        "question": "Please provide the city.",
        "example": "Bengaluru",
        "required": False,
    },
    {
        "key": "State",
        "label": "State",
        "question": "Please provide the state.",
        "example": "Karnataka",
        "required": False,
    },
    {
        "key": "Zip",
        "label": "ZIP / Postal Code",
        "question": "Please provide the ZIP or postal code.",
        "example": "560001",
        "required": False,
    },
    {
        "key": "Latitude",
        "label": "Latitude",
        "question": "Please provide the latitude, or skip this field.",
        "example": "12.9716",
        "required": False,
    },
    {
        "key": "Longitude",
        "label": "Longitude",
        "question": "Please provide the longitude, or skip this field.",
        "example": "77.5946",
        "required": False,
    },
    {
        "key": "Primary NAICS",
        "label": "Primary NAICS",
        "question": "Please provide the Primary NAICS code.",
        "example": "332710",
        "required": False,
    },
    {
        "key": "Hospitalized",
        "label": "Hospitalized",
        "question": "Was the employee hospitalized? Please answer Yes or No.",
        "example": "Yes",
        "required": False,
    },
    {
        "key": "Amputation",
        "label": "Amputation",
        "question": "Did the incident involve an amputation? Please answer Yes or No.",
        "example": "No",
        "required": False,
    },
    {
        "key": "Loss of Eye",
        "label": "Loss of Eye",
        "question": "Did the incident involve loss of an eye? Please answer Yes or No.",
        "example": "No",
        "required": False,
    },
    {
        "key": "Inspection",
        "label": "Inspection",
        "question": "Please provide the inspection reference.",
        "example": "INS-45021",
        "required": False,
    },
    {
        "key": "FederalState",
        "label": "Federal / State",
        "question": "Please specify whether this is Federal or State.",
        "example": "State",
        "required": False,
    },
    {
        "key": "Final Narrative",
        "label": "Final Narrative",
        "question": (
            "Please describe what happened. Include the activity, event, injury, "
            "body part and source where known."
        ),
        "example": (
            "An employee slipped on a wet floor, fell on the same level, "
            "and fractured the left ankle."
        ),
        "required": True,
    },
]


# ==============================================================================
# Session-state helpers
# ==============================================================================

def initialize_voice_state() -> None:
    """
    Initialize the guided voice-reporting workflow.
    """

    defaults = {
        "voice_stage": "welcome",
        "voice_step": 0,
        "voice_answers": {},
        "voice_transcript": "",
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_voice_workflow() -> None:
    """
    Clear all voice-reporting session data.
    """

    keys = [
        "voice_stage",
        "voice_step",
        "voice_answers",
        "voice_transcript",
    ]

    for key in keys:
        st.session_state.pop(
            key,
            None,
        )

    initialize_voice_state()


def load_current_answer() -> None:
    """
    Load the saved answer for the current field into the transcript box.
    """

    current_step = int(
        st.session_state.voice_step
    )

    current_field = VOICE_FIELDS[
        current_step
    ]

    st.session_state.voice_transcript = (
        st.session_state.voice_answers.get(
            current_field["key"],
            "",
        )
    )


# ==============================================================================
# Workflow screens
# ==============================================================================

def render_welcome_screen() -> None:
    """
    Render the start screen before guided capture begins.
    """

    st.markdown("## Guided Voice Reporting")

    st.info(
        "The assistant will guide you through 18 incident fields, one question "
        "at a time. In this first stage, type the response into the transcript "
        "box. Microphone recording and speech recognition will be connected next."
    )

    st.markdown("")

    if st.button(
        "Start Guided Voice Report",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.voice_stage = "capture"
        st.session_state.voice_step = 0
        st.session_state.voice_transcript = ""
        st.rerun()


def render_captured_information() -> None:
    """
    Show all confirmed responses collected so far.
    """

    st.markdown("### Captured Information")

    answers = st.session_state.voice_answers

    if not answers:
        st.info(
            "Confirmed responses will appear here."
        )
        return

    for field in VOICE_FIELDS:
        field_key = str(
            field["key"]
        )

        if field_key not in answers:
            continue

        value = answers.get(
            field_key,
            "",
        )

        display_value = (
            value
            if str(value).strip()
            else "Skipped"
        )

        st.html(
            f"""
            <div style="
                margin-bottom: 0.6rem;
                padding: 0.85rem 1rem;
                border-radius: 14px;
                border: 1px solid #DCE6ED;
                background: #FFFFFF;
            ">
                <div style="
                    color: #6A7F8F;
                    font-size: 0.70rem;
                    font-weight: 800;
                    letter-spacing: 0.06em;
                    text-transform: uppercase;
                ">
                    {escape(str(field["label"]))}
                </div>

                <div style="
                    margin-top: 0.25rem;
                    color: #17324D;
                    font-size: 0.85rem;
                    line-height: 1.45;
                ">
                    {escape(str(display_value))}
                </div>
            </div>
            """
        )


def render_capture_screen() -> None:
    """
    Render the active guided-question screen.
    """

    current_step = int(
        st.session_state.voice_step
    )

    total_fields = len(
        VOICE_FIELDS
    )

    current_field = VOICE_FIELDS[
        current_step
    ]

    completed_fields = len(
        st.session_state.voice_answers
    )

    progress_value = (
        completed_fields / total_fields
    )

    st.markdown("## Guided Voice Reporting")

    st.progress(
        progress_value,
        text=(
            f"{completed_fields} of "
            f"{total_fields} fields completed"
        ),
    )

    left_column, right_column = st.columns(
        [1.55, 1],
        gap="large",
    )

    with left_column:
        required_text = (
            "Required"
            if current_field["required"]
            else "Optional"
        )

        st.html(
            f"""
            <div style="
                padding: 1.4rem;
                border-radius: 18px;
                border: 1px solid #DCE6ED;
                background: linear-gradient(
                    180deg,
                    #FFFFFF 0%,
                    #F8FBFD 100%
                );
                box-shadow: 0 8px 22px rgba(26,58,79,0.06);
            ">
                <div style="
                    color: #286A9B;
                    font-size: 0.72rem;
                    font-weight: 800;
                    letter-spacing: 0.08em;
                    text-transform: uppercase;
                ">
                    Field {current_step + 1} of {total_fields}
                    &nbsp;•&nbsp;
                    {escape(required_text)}
                </div>

                <div style="
                    margin-top: 0.7rem;
                    color: #17324D;
                    font-size: 1.45rem;
                    font-weight: 800;
                ">
                    {escape(str(current_field["label"]))}
                </div>

                <div style="
                    margin-top: 0.55rem;
                    color: #536B7D;
                    font-size: 0.95rem;
                    line-height: 1.65;
                ">
                    {escape(str(current_field["question"]))}
                </div>

                <div style="
                    margin-top: 1rem;
                    padding: 0.85rem 1rem;
                    border-radius: 12px;
                    background: #EDF7FB;
                    border: 1px solid #CDE2EC;
                    color: #31566B;
                    font-size: 0.82rem;
                ">
                    <b>Example:</b> {escape(str(current_field["example"]))}
                </div>
            </div>
            """
        )

        st.markdown("")

        transcript = st.text_area(
            "Transcript",
            key="voice_transcript",
            height=(
                170
                if current_field["key"] == "Final Narrative"
                else 110
            ),
            placeholder=str(
                current_field["example"]
            ),
            help=(
                "For this first stage, type the response manually. "
                "The microphone will populate this box in the next stage."
            ),
        )

        action_columns = st.columns(
            3,
            gap="small",
        )

        with action_columns[0]:
            previous_clicked = st.button(
                "← Previous",
                use_container_width=True,
                disabled=current_step == 0,
            )

        with action_columns[1]:
            confirm_clicked = st.button(
                "Confirm & Continue",
                type="primary",
                use_container_width=True,
            )

        with action_columns[2]:
            skip_clicked = st.button(
                "Skip Optional",
                use_container_width=True,
                disabled=bool(
                    current_field["required"]
                ),
            )

        if previous_clicked:
            previous_step = current_step - 1

            st.session_state.voice_step = (
                previous_step
            )

            load_current_answer()
            st.rerun()

        if confirm_clicked:
            cleaned_transcript = (
                transcript.strip()
            )

            if (
                current_field["required"]
                and not cleaned_transcript
            ):
                st.error(
                    f"{current_field['label']} is required."
                )

            elif (
                current_field["key"] == "Final Narrative"
                and (
                    len(cleaned_transcript) < 15
                    or len(
                        cleaned_transcript.split()
                    ) < 4
                )
            ):
                st.error(
                    "Please provide a more descriptive incident narrative."
                )

            else:
                st.session_state.voice_answers[
                    current_field["key"]
                ] = cleaned_transcript

                if current_step == total_fields - 1:
                    st.session_state.voice_stage = "review"

                else:
                    st.session_state.voice_step = (
                        current_step + 1
                    )

                    next_field = VOICE_FIELDS[
                        current_step + 1
                    ]

                    st.session_state.voice_transcript = (
                        st.session_state.voice_answers.get(
                            next_field["key"],
                            "",
                        )
                    )

                st.rerun()

        if skip_clicked:
            st.session_state.voice_answers[
                current_field["key"]
            ] = ""

            if current_step < total_fields - 1:
                st.session_state.voice_step = (
                    current_step + 1
                )

                next_field = VOICE_FIELDS[
                    current_step + 1
                ]

                st.session_state.voice_transcript = (
                    st.session_state.voice_answers.get(
                        next_field["key"],
                        "",
                    )
                )

            st.rerun()

        st.markdown("")

        if st.button(
            "Discard and Start Again",
            use_container_width=True,
        ):
            reset_voice_workflow()
            st.rerun()

    with right_column:
        render_captured_information()


def render_review_screen() -> None:
    """
    Render the final review screen after all fields are completed.
    """

    st.progress(
        1.0,
        text=(
            f"All {len(VOICE_FIELDS)} fields completed"
        ),
    )

    st.markdown("## Review Captured Incident")

    st.caption(
        "Review every response before continuing. "
        "The complete editable review form will be added in the next stage."
    )

    review_rows = []

    for field in VOICE_FIELDS:
        value = st.session_state.voice_answers.get(
            field["key"],
            "",
        )

        review_rows.append(
            {
                "Field": field["label"],
                "Response": (
                    value
                    if str(value).strip()
                    else "Skipped"
                ),
            }
        )

    st.dataframe(
        review_rows,
        hide_index=True,
        use_container_width=True,
    )

    st.info(
        "The guided capture workflow is complete. "
        "Microphone transcription, editable final review and model "
        "classification will be connected in the next stages."
    )

    control_columns = st.columns(
        2,
        gap="medium",
    )

    with control_columns[0]:
        if st.button(
            "← Return to Last Field",
            use_container_width=True,
        ):
            last_step = len(
                VOICE_FIELDS
            ) - 1

            st.session_state.voice_stage = "capture"
            st.session_state.voice_step = last_step

            load_current_answer()
            st.rerun()

    with control_columns[1]:
        if st.button(
            "Start New Voice Report",
            type="primary",
            use_container_width=True,
        ):
            reset_voice_workflow()
            st.rerun()


# ==============================================================================
# Main page
# ==============================================================================

def render() -> None:
    initialize_voice_state()

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

    st.markdown("---")

    stage = st.session_state.voice_stage

    if stage == "welcome":
        render_welcome_screen()

    elif stage == "capture":
        render_capture_screen()

    elif stage == "review":
        render_review_screen()

    else:
        reset_voice_workflow()
        st.rerun()
