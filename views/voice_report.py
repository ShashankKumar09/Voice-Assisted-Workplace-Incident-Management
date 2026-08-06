"""
Voice Incident Reporting page.

Stage 2:
Guided field-by-field incident capture with browser microphone recording,
speech-to-text transcription, editable transcripts and final review.
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
# Backend loader
# ==============================================================================

@st.cache_resource(show_spinner=False)
def load_speech_engine():
    """
    Load the local speech-recognition engine only when audio is first submitted.
    """
    from voice.speech_engine import SpeechRecognitionEngine

    return SpeechRecognitionEngine(
        model_size="tiny.en",
        device="cpu",
        compute_type="int8",
    )


# ==============================================================================
# Session-state helpers
# ==============================================================================

def transcript_key(step: int) -> str:
    return f"voice_transcript_{step}"


def audio_key(step: int) -> str:
    return f"voice_audio_{step}"


def audio_signature_key(step: int) -> str:
    return f"voice_audio_signature_{step}"


def initialize_voice_state() -> None:
    defaults = {
        "voice_stage": "welcome",
        "voice_step": 0,
        "voice_answers": {},
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_voice_workflow() -> None:
    """
    Clear workflow state and all dynamic audio/transcript widget values.
    """
    removable_keys = [
        key
        for key in list(st.session_state.keys())
        if (
            key in {
                "voice_stage",
                "voice_step",
                "voice_answers",
            }
            or key.startswith("voice_transcript_")
            or key.startswith("voice_audio_")
            or key.startswith("voice_audio_signature_")
        )
    ]

    for key in removable_keys:
        st.session_state.pop(key, None)

    initialize_voice_state()


def prepare_step_transcript(
    step: int,
) -> None:
    """
    Prepare the transcript widget value before its next render.
    """
    field = VOICE_FIELDS[step]
    st.session_state[transcript_key(step)] = (
        st.session_state.voice_answers.get(
            field["key"],
            "",
        )
    )


# ==============================================================================
# Value validation
# ==============================================================================

def validate_response(
    value: str,
    field: Dict[str, object],
) -> str | None:
    cleaned = value.strip()

    if bool(field["required"]) and not cleaned:
        return f"{field['label']} is required."

    if field["key"] == "Final Narrative":
        if len(cleaned) < 15 or len(cleaned.split()) < 4:
            return "Please provide a more descriptive incident narrative."

    if field["key"] in {
        "Hospitalized",
        "Amputation",
        "Loss of Eye",
    } and cleaned:
        if cleaned.lower() not in {
            "yes",
            "no",
            "y",
            "n",
        }:
            return f"{field['label']} must be Yes or No."

    if field["key"] == "FederalState" and cleaned:
        if cleaned.lower() not in {
            "federal",
            "state",
        }:
            return "Federal / State must be Federal or State."

    return None


def normalize_response(
    value: str,
    field: Dict[str, object],
) -> str:
    cleaned = value.strip()

    if field["key"] in {
        "Hospitalized",
        "Amputation",
        "Loss of Eye",
    }:
        if cleaned.lower() in {"yes", "y"}:
            return "Yes"
        if cleaned.lower() in {"no", "n"}:
            return "No"

    if field["key"] == "FederalState":
        if cleaned.lower() == "federal":
            return "Federal"
        if cleaned.lower() == "state":
            return "State"

    return cleaned


# ==============================================================================
# Reusable UI blocks
# ==============================================================================

def render_question_card(
    current_field: Dict[str, object],
    current_step: int,
    total_fields: int,
) -> None:
    required_text = (
        "Required"
        if bool(current_field["required"])
        else "Optional"
    )

    st.html(
        f"""
        <div style="
            padding: 1.4rem;
            border-radius: 18px;
            border: 1px solid #DCE6ED;
            background: linear-gradient(180deg,#FFFFFF 0%,#F8FBFD 100%);
            box-shadow: 0 8px 22px rgba(26,58,79,0.06);
        ">
            <div style="
                color:#286A9B;
                font-size:0.72rem;
                font-weight:800;
                letter-spacing:0.08em;
                text-transform:uppercase;
            ">
                Field {current_step + 1} of {total_fields}
                &nbsp;•&nbsp;
                {escape(required_text)}
            </div>

            <div style="
                margin-top:0.7rem;
                color:#17324D;
                font-size:1.45rem;
                font-weight:800;
            ">
                {escape(str(current_field["label"]))}
            </div>

            <div style="
                margin-top:0.55rem;
                color:#536B7D;
                font-size:0.95rem;
                line-height:1.65;
            ">
                {escape(str(current_field["question"]))}
            </div>

            <div style="
                margin-top:1rem;
                padding:0.85rem 1rem;
                border-radius:12px;
                background:#EDF7FB;
                border:1px solid #CDE2EC;
                color:#31566B;
                font-size:0.82rem;
            ">
                <b>Example:</b>
                {escape(str(current_field["example"]))}
            </div>
        </div>
        """
    )


def render_answer_card(
    label: str,
    value: str,
) -> None:
    st.html(
        f"""
        <div style="
            margin-bottom:0.6rem;
            padding:0.85rem 1rem;
            border-radius:14px;
            border:1px solid #DCE6ED;
            background:#FFFFFF;
            box-shadow:0 4px 12px rgba(26,58,79,0.04);
        ">
            <div style="
                color:#6A7F8F;
                font-size:0.70rem;
                font-weight:800;
                letter-spacing:0.06em;
                text-transform:uppercase;
            ">
                {escape(label)}
            </div>

            <div style="
                margin-top:0.25rem;
                color:#17324D;
                font-size:0.85rem;
                line-height:1.45;
                overflow-wrap:anywhere;
            ">
                {escape(value)}
            </div>
        </div>
        """
    )


# ==============================================================================
# Workflow screens
# ==============================================================================

def render_welcome_screen() -> None:
    st.markdown("## Guided Voice Reporting")

    st.info(
        "The assistant will guide you through 18 incident fields, one question "
        "at a time. Record each answer, review the transcript and confirm it "
        "before continuing."
    )

    st.markdown("")

    if st.button(
        "Start Guided Voice Report",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.voice_stage = "capture"
        st.session_state.voice_step = 0
        prepare_step_transcript(0)
        st.rerun()


def render_captured_information() -> None:
    st.markdown("### Captured Information")

    answers = st.session_state.voice_answers

    if not answers:
        st.info("Confirmed responses will appear here.")
        return

    for field in VOICE_FIELDS:
        field_key = str(field["key"])

        if field_key not in answers:
            continue

        value = answers.get(field_key, "")

        render_answer_card(
            label=str(field["label"]),
            value=(
                str(value)
                if str(value).strip()
                else "Skipped"
            ),
        )


def process_audio(
    audio_value,
    step: int,
) -> None:
    """
    Transcribe newly recorded audio once and populate the current transcript.
    """
    if audio_value is None:
        return

    audio_bytes = audio_value.getvalue()

    signature = (
        len(audio_bytes),
        hash(audio_bytes[:1024]),
    )

    signature_state_key = audio_signature_key(step)

    if st.session_state.get(signature_state_key) == signature:
        return

    try:
        with st.spinner("Transcribing your response..."):
            result = load_speech_engine().transcribe_bytes(
                audio_bytes,
                language="en",
            )

        transcript = str(
            result.get("transcript", "")
        ).strip()

        if not transcript:
            st.warning(
                "No speech was recognized. Please record again or type the response."
            )
            return

        # This key has not yet been instantiated as a text-area widget in this run,
        # so it can safely be populated here.
        st.session_state[transcript_key(step)] = transcript
        st.session_state[signature_state_key] = signature
        st.rerun()

    except Exception as error:
        st.error(
            "Speech transcription failed. "
            "You can record again or type the response manually."
        )
        st.caption(str(error))


def render_capture_screen() -> None:
    current_step = int(st.session_state.voice_step)
    total_fields = len(VOICE_FIELDS)
    current_field = VOICE_FIELDS[current_step]

    completed_fields = len(st.session_state.voice_answers)

    st.markdown("## Guided Voice Reporting")

    st.progress(
        completed_fields / total_fields,
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
        render_question_card(
            current_field=current_field,
            current_step=current_step,
            total_fields=total_fields,
        )

        st.markdown("")

        st.markdown("#### Record your response")

        audio_value = st.audio_input(
            f"Record {current_field['label']}",
            sample_rate=16000,
            key=audio_key(current_step),
            help=(
                "Use the microphone attached to your device for clearer "
                "recording input. Stop recording when your response is complete."
            ),
        )

        # Must run before the text-area widget is created.
        process_audio(
            audio_value=audio_value,
            step=current_step,
        )

        transcript = st.text_area(
            "Recognized transcript",
            key=transcript_key(current_step),
            height=(
                170
                if current_field["key"] == "Final Narrative"
                else 110
            ),
            placeholder=str(current_field["example"]),
            help=(
                "Review and edit the speech-to-text result before confirming."
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
                key=f"voice_previous_{current_step}",
            )

        with action_columns[1]:
            confirm_clicked = st.button(
                "Confirm & Continue",
                type="primary",
                use_container_width=True,
                key=f"voice_confirm_{current_step}",
            )

        with action_columns[2]:
            skip_clicked = st.button(
                "Skip Optional",
                use_container_width=True,
                disabled=bool(current_field["required"]),
                key=f"voice_skip_{current_step}",
            )

        if previous_clicked:
            target_step = current_step - 1
            st.session_state.voice_step = target_step
            prepare_step_transcript(target_step)
            st.rerun()

        if confirm_clicked:
            error = validate_response(
                transcript,
                current_field,
            )

            if error:
                st.error(error)

            else:
                st.session_state.voice_answers[
                    current_field["key"]
                ] = normalize_response(
                    transcript,
                    current_field,
                )

                if current_step == total_fields - 1:
                    st.session_state.voice_stage = "review"

                else:
                    target_step = current_step + 1
                    st.session_state.voice_step = target_step
                    prepare_step_transcript(target_step)

                st.rerun()

        if skip_clicked:
            st.session_state.voice_answers[
                current_field["key"]
            ] = ""

            if current_step < total_fields - 1:
                target_step = current_step + 1
                st.session_state.voice_step = target_step
                prepare_step_transcript(target_step)

            st.rerun()

        st.markdown("")

        if st.button(
            "Discard and Start Again",
            use_container_width=True,
            key=f"voice_reset_{current_step}",
        ):
            reset_voice_workflow()
            st.rerun()

    with right_column:
        render_captured_information()


def render_review_screen() -> None:
    st.progress(
        1.0,
        text=f"All {len(VOICE_FIELDS)} fields completed",
    )

    st.markdown("## Review Captured Incident")

    st.caption(
        "Review the confirmed responses before the editable final-review and "
        "classification stage is connected."
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

    st.success(
        "Voice capture and speech-to-text are complete. "
        "The next step will connect editable final review, classification "
        "and report downloads."
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
            target_step = len(VOICE_FIELDS) - 1
            st.session_state.voice_stage = "capture"
            st.session_state.voice_step = target_step
            prepare_step_transcript(target_step)
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
            "Use the microphone attached to your device for clearer recording "
            "input, speak clearly in a quiet environment, and review the "
            "transcript before proceeding."
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
