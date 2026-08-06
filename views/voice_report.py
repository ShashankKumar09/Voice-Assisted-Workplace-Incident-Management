"""
Voice Incident Reporting.

Complete guided workflow:
- browser microphone capture
- background-noise reduction and speech-to-text
- editable transcript
- previous, skip, confirm and record-again controls
- editable final review
- DeBERTa classification
- historical validation
- PDF and CSV downloads
- incident-store persistence
"""

from __future__ import annotations

from datetime import datetime
from hashlib import sha256
from html import escape
import re
from typing import Dict, List

import streamlit as st

from ui.guide_components import (
    render_module_header,
    render_user_guide,
)

# Reuse the already-tested Manual Reporting backend and result design.
from views.manual_report import (
    generate_report,
    load_predictor,
    render_prediction_results,
    save_incident_record,
)


VOICE_FIELDS: List[Dict[str, object]] = [
    {
        "key": "ID",
        "label": "Incident ID",
        "question": "Please provide the Incident ID.",
        "example": "INC-1001",
        "required": True,
        "type": "identifier",
    },
    {
        "key": "UPA",
        "label": "UPA",
        "question": "Please provide the UPA reference.",
        "example": "UPA-2501",
        "required": False,
        "type": "identifier",
    },
    {
        "key": "EventDate",
        "label": "Event Date",
        "question": "Please provide the date when the incident occurred.",
        "example": "5 August 2026",
        "required": False,
        "type": "date",
    },
    {
        "key": "Employer",
        "label": "Employer",
        "question": "Please provide the employer name.",
        "example": "ABC Manufacturing",
        "required": False,
        "type": "text",
    },
    {
        "key": "Address1",
        "label": "Address Line 1",
        "question": "Please provide Address Line 1.",
        "example": "100 Industrial Road",
        "required": False,
        "type": "text",
    },
    {
        "key": "Address2",
        "label": "Address Line 2",
        "question": "Please provide Address Line 2, or skip this field.",
        "example": "Building B",
        "required": False,
        "type": "text",
    },
    {
        "key": "City",
        "label": "City",
        "question": "Please provide the city.",
        "example": "Bengaluru",
        "required": False,
        "type": "text",
    },
    {
        "key": "State",
        "label": "State",
        "question": "Please provide the state.",
        "example": "Karnataka",
        "required": False,
        "type": "text",
    },
    {
        "key": "Zip",
        "label": "ZIP / Postal Code",
        "question": "Please provide the ZIP or postal code.",
        "example": "560001",
        "required": False,
        "type": "digits",
    },
    {
        "key": "Latitude",
        "label": "Latitude",
        "question": "Please provide the latitude, or skip this field.",
        "example": "12.9716",
        "required": False,
        "type": "latitude",
    },
    {
        "key": "Longitude",
        "label": "Longitude",
        "question": "Please provide the longitude, or skip this field.",
        "example": "77.5946",
        "required": False,
        "type": "longitude",
    },
    {
        "key": "Primary NAICS",
        "label": "Primary NAICS",
        "question": "Please provide the Primary NAICS code.",
        "example": "332710",
        "required": False,
        "type": "digits",
    },
    {
        "key": "Hospitalized",
        "label": "Hospitalized",
        "question": "Was the employee hospitalized? Please answer Yes or No.",
        "example": "Yes",
        "required": False,
        "type": "yes_no",
    },
    {
        "key": "Amputation",
        "label": "Amputation",
        "question": "Did the incident involve an amputation? Please answer Yes or No.",
        "example": "No",
        "required": False,
        "type": "yes_no",
    },
    {
        "key": "Loss of Eye",
        "label": "Loss of Eye",
        "question": "Did the incident involve loss of an eye? Please answer Yes or No.",
        "example": "No",
        "required": False,
        "type": "yes_no",
    },
    {
        "key": "Inspection",
        "label": "Inspection",
        "question": "Please provide the inspection reference.",
        "example": "INS-45021",
        "required": False,
        "type": "identifier",
    },
    {
        "key": "FederalState",
        "label": "Federal / State",
        "question": "Please specify whether this is Federal or State.",
        "example": "State",
        "required": False,
        "type": "federal_state",
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
        "type": "narrative",
    },
]


@st.cache_resource(show_spinner=False)
def load_speech_engine():
    from voice.speech_engine import SpeechRecognitionEngine

    return SpeechRecognitionEngine(
        model_size="base.en",
        device="cpu",
        compute_type="int8",
    )


def transcript_key(step: int) -> str:
    return f"voice_transcript_{step}"


def audio_version_key(step: int) -> str:
    return f"voice_audio_version_{step}"


def current_audio_key(step: int) -> str:
    version = int(
        st.session_state.get(
            audio_version_key(step),
            0,
        )
    )
    return f"voice_audio_{step}_{version}"


def audio_signature_key(step: int) -> str:
    return f"voice_audio_signature_{step}"


def pending_reset_key(step: int) -> str:
    return f"voice_pending_reset_{step}"


def initialize_voice_state() -> None:
    defaults = {
        "voice_stage": "welcome",
        "voice_step": 0,
        "voice_answers": {},
        "voice_prediction": None,
        "voice_report_package": None,
        "voice_saved": False,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_voice_workflow() -> None:
    removable_keys = [
        key
        for key in list(st.session_state.keys())
        if (
            key.startswith("voice_")
            and key not in {
                "voice_navigation",
            }
        )
    ]

    for key in removable_keys:
        st.session_state.pop(
            key,
            None,
        )

    initialize_voice_state()


def prepare_step_transcript(step: int) -> None:
    field = VOICE_FIELDS[step]

    st.session_state[
        transcript_key(step)
    ] = st.session_state.voice_answers.get(
        field["key"],
        "",
    )


def consume_pending_recording_reset(
    step: int,
) -> None:
    """
    Clear widget state before widgets are instantiated on the new run.
    """
    reset_key = pending_reset_key(step)

    if not st.session_state.get(
        reset_key,
        False,
    ):
        return

    st.session_state.pop(
        transcript_key(step),
        None,
    )
    st.session_state.pop(
        audio_signature_key(step),
        None,
    )

    st.session_state[reset_key] = False



DIGIT_WORDS = {
    "zero": "0",
    "oh": "0",
    "o": "0",
    "one": "1",
    "two": "2",
    "to": "2",
    "too": "2",
    "three": "3",
    "four": "4",
    "for": "4",
    "five": "5",
    "six": "6",
    "seven": "7",
    "eight": "8",
    "ate": "8",
    "nine": "9",
}

REPEAT_WORDS = {
    "double": 2,
    "triple": 3,
}

SEPARATOR_WORDS = {
    "dash": "-",
    "hyphen": "-",
    "minus": "-",
    "underscore": "_",
    "slash": "/",
    "dot": ".",
    "point": ".",
}


def _clean_spoken_tokens(value: str) -> List[str]:
    """Return lowercase tokens while retaining identifier separators."""
    cleaned = value.lower().strip()
    cleaned = cleaned.replace("–", "-").replace("—", "-")
    return re.findall(r"[a-z]+|\d+|[-_/.]", cleaned)


def normalize_spoken_code(
    value: str,
    *,
    digits_only: bool = False,
) -> str:
    """
    Convert digit-by-digit speech to a compact code.

    Examples:
    ``two zero one five zero one double zero one five`` -> ``2015010015``
    ``I N C dash one zero zero one`` -> ``INC-1001``.
    """
    tokens = _clean_spoken_tokens(value)
    if not tokens:
        return value.strip()

    output: List[str] = []
    recognized = 0
    index = 0

    while index < len(tokens):
        token = tokens[index]

        if token in REPEAT_WORDS and index + 1 < len(tokens):
            next_token = tokens[index + 1]
            repeated_digit = DIGIT_WORDS.get(next_token)
            if repeated_digit is None and next_token.isdigit() and len(next_token) == 1:
                repeated_digit = next_token

            if repeated_digit is not None:
                output.append(repeated_digit * REPEAT_WORDS[token])
                recognized += 2
                index += 2
                continue

        if token in DIGIT_WORDS:
            output.append(DIGIT_WORDS[token])
            recognized += 1
        elif token.isdigit():
            output.append(token)
            recognized += 1
        elif token in SEPARATOR_WORDS:
            output.append(SEPARATOR_WORDS[token])
            recognized += 1
        elif token in {"-", "_", "/", "."}:
            output.append(token)
            recognized += 1
        elif not digits_only:
            # Whisper sometimes separates an acronym into individual letters.
            output.append(token.upper())
        index += 1

    if digits_only:
        normalized = "".join(part for part in output if part.isdigit())
        # Do not destroy an ordinary non-numeric response if no number was found.
        return normalized if normalized else value.strip()

    normalized = "".join(output)
    if not normalized or recognized == 0:
        return value.strip()

    # Whisper frequently inserts punctuation between dictated digits even when
    # the speaker did not say a separator (for example ``9-311-7-6``). When an
    # identifier contains digits and separators only, remove those artificial
    # separators. Genuine alphanumeric identifiers such as ``UPA-2501`` retain
    # their separator because letters are present.
    if re.fullmatch(r"[0-9._/-]+", normalized):
        compact_digits = re.sub(r"[^0-9]", "", normalized)
        return compact_digits if compact_digits else normalized

    return normalized


def normalize_spoken_decimal(value: str) -> str:
    """Normalize spoken latitude/longitude, including minus and decimal point."""
    tokens = _clean_spoken_tokens(value)
    output: List[str] = []
    index = 0

    while index < len(tokens):
        token = tokens[index]

        if token in {"negative", "minus"} and not output:
            output.append("-")
        elif token in {"point", "dot"}:
            output.append(".")
        elif token in REPEAT_WORDS and index + 1 < len(tokens):
            next_digit = DIGIT_WORDS.get(tokens[index + 1])
            if next_digit is not None:
                output.append(next_digit * REPEAT_WORDS[token])
                index += 1
        elif token in DIGIT_WORDS:
            output.append(DIGIT_WORDS[token])
        elif token.isdigit():
            output.append(token)
        elif token in {".", "-"}:
            output.append(token)

        index += 1

    normalized = "".join(output)
    return normalized if normalized not in {"", "-", "."} else value.strip()


def normalize_spoken_date(value: str) -> str:
    """Convert common spoken or typed dates to ISO ``YYYY-MM-DD``."""
    cleaned = value.strip()
    if not cleaned:
        return ""

    normalized = cleaned.lower()
    normalized = re.sub(r"\b(\d+)(st|nd|rd|th)\b", r"\1", normalized)
    normalized = re.sub(r"[,]+", " ", normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()

    formats = (
        "%d %B %Y",
        "%d %b %Y",
        "%B %d %Y",
        "%b %d %Y",
        "%Y-%m-%d",
        "%d-%m-%Y",
        "%d/%m/%Y",
        "%m/%d/%Y",
    )

    for date_format in formats:
        try:
            return datetime.strptime(normalized, date_format).strftime("%Y-%m-%d")
        except ValueError:
            continue

    return cleaned


def normalize_field_value(
    raw_value: str,
    field: Dict[str, object],
) -> str:
    """Apply field-aware cleanup to voice and manually edited transcripts."""
    value = raw_value.strip()
    field_type = str(field["type"])

    if not value:
        return ""

    if field_type == "identifier":
        return normalize_spoken_code(value)

    if field_type == "digits":
        return normalize_spoken_code(value, digits_only=True)

    if field_type in {"latitude", "longitude"}:
        return normalize_spoken_decimal(value)

    if field_type == "date":
        return normalize_spoken_date(value)

    return value


def transcription_prompt(field: Dict[str, object]) -> str:
    """Provide Whisper with concise context for the current incident field."""
    field_type = str(field["type"])
    label = str(field["label"])

    if field_type == "identifier":
        return (
            f"The speaker is dictating the {label}. "
            "Write letters, digits, hyphens and separators exactly."
        )

    if field_type == "digits":
        return (
            f"The speaker is dictating the numeric {label}. "
            "Transcribe every digit separately and preserve zeroes."
        )

    if field_type in {"latitude", "longitude"}:
        return (
            f"The speaker is dictating a {label} coordinate. "
            "Preserve the minus sign and decimal point."
        )

    if field_type == "date":
        return "The speaker is dictating an incident date in English."

    if field_type == "yes_no":
        return f"The speaker is answering Yes or No for {label}."

    if field_type == "federal_state":
        return "The speaker is answering Federal or State."

    if field_type == "narrative":
        return (
            "The speaker is describing a workplace safety incident, including "
            "the activity, event, injury, body part and source."
        )

    return f"The speaker is providing the incident field: {label}."


def validate_response(
    raw_value: str,
    field: Dict[str, object],
) -> tuple[str, str | None]:
    value = normalize_field_value(raw_value, field)

    if bool(field["required"]) and not value:
        return "", f"{field['label']} is required."

    field_type = str(field["type"])

    if not value:
        return "", None

    if field_type == "yes_no":
        normalized = (
            value.lower()
            .replace(".", "")
            .strip()
        )

        if normalized in {
            "yes",
            "y",
            "yeah",
            "true",
            "1",
            "one",
        }:
            return "Yes", None

        if normalized in {
            "no",
            "n",
            "nope",
            "false",
            "0",
            "zero",
        }:
            return "No", None

        return "", f"{field['label']} must be Yes or No."

    if field_type == "federal_state":
        normalized = value.lower().strip()

        if "federal" in normalized:
            return "Federal", None

        if (
            normalized == "state"
            or normalized.endswith(
                " state"
            )
        ):
            return "State", None

        return "", "Federal / State must be Federal or State."

    if field_type in {
        "latitude",
        "longitude",
    }:
        numeric_text = (
            value.lower()
            .replace("negative ", "-")
            .replace("minus ", "-")
            .replace(",", ".")
        )

        try:
            numeric_value = float(
                numeric_text
            )
        except ValueError:
            return "", f"{field['label']} must be numeric."

        minimum, maximum = (
            (-90.0, 90.0)
            if field_type == "latitude"
            else (-180.0, 180.0)
        )

        if not minimum <= numeric_value <= maximum:
            return (
                "",
                f"{field['label']} must be between "
                f"{minimum:g} and {maximum:g}.",
            )

        return str(numeric_value), None

    if field_type == "narrative":
        if (
            len(value) < 15
            or len(value.split()) < 4
        ):
            return (
                "",
                "Please provide a more descriptive incident narrative.",
            )

    return value, None


def render_question_card(
    field: Dict[str, object],
    step: int,
    total: int,
) -> None:
    requirement = (
        "Required"
        if bool(field["required"])
        else "Optional"
    )

    st.html(
        f"""
        <div style="
            padding:1.45rem;
            border-radius:20px;
            border:1px solid #D7E4EB;
            background:linear-gradient(180deg,#FFFFFF 0%,#F8FBFD 100%);
            box-shadow:0 10px 28px rgba(26,58,79,.07);
        ">
            <div style="
                color:#286A9B;
                font-size:.72rem;
                font-weight:800;
                letter-spacing:.08em;
                text-transform:uppercase;
            ">
                Question {step + 1} of {total}
                &nbsp;•&nbsp;
                {escape(requirement)}
            </div>

            <div style="
                margin-top:.75rem;
                color:#17324D;
                font-size:1.55rem;
                font-weight:850;
            ">
                {escape(str(field["label"]))}
            </div>

            <div style="
                margin-top:.55rem;
                color:#536B7D;
                font-size:.96rem;
                line-height:1.65;
            ">
                {escape(str(field["question"]))}
            </div>

            <div style="
                margin-top:1rem;
                padding:.85rem 1rem;
                border-radius:12px;
                border:1px solid #CDE2EC;
                background:#EDF7FB;
                color:#31566B;
                font-size:.83rem;
            ">
                <b>Example:</b>
                {escape(str(field["example"]))}
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
            margin-bottom:.6rem;
            padding:.85rem 1rem;
            border-radius:14px;
            border:1px solid #DCE6ED;
            background:#FFFFFF;
            box-shadow:0 4px 12px rgba(26,58,79,.04);
        ">
            <div style="
                color:#6A7F8F;
                font-size:.69rem;
                font-weight:800;
                letter-spacing:.06em;
                text-transform:uppercase;
            ">
                ✓ {escape(label)}
            </div>

            <div style="
                margin-top:.25rem;
                color:#17324D;
                font-size:.84rem;
                line-height:1.45;
                overflow-wrap:anywhere;
            ">
                {escape(value)}
            </div>
        </div>
        """
    )


def render_captured_information() -> None:
    st.markdown("### Live Incident Summary")

    answers = st.session_state.voice_answers

    if not answers:
        st.info(
            "Confirmed responses will appear here."
        )
        return

    for field in VOICE_FIELDS:
        field_key = str(field["key"])

        if field_key not in answers:
            continue

        value = answers.get(
            field_key,
            "",
        )

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
    if audio_value is None:
        return

    audio_bytes = audio_value.getvalue()

    # Use a stable digest rather than Python's process-randomized hash().
    # This reliably prevents the same recording from being transcribed again
    # during Streamlit reruns.
    signature = sha256(audio_bytes).hexdigest()

    signature_key = audio_signature_key(
        step
    )

    if st.session_state.get(
        signature_key
    ) == signature:
        return

    try:
        with st.spinner(
            "Capturing speech and selecting the clearest transcription..."
        ):
            field = VOICE_FIELDS[step]
            result = load_speech_engine().transcribe_bytes(
                audio_bytes,
                language="en",
                prompt=transcription_prompt(field),
                field_type=str(field["type"]),
            )

        transcript = str(
            result.get(
                "transcript",
                "",
            )
        ).strip()

        transcript = normalize_field_value(
            transcript,
            VOICE_FIELDS[step],
        )

        if not transcript:
            st.warning(
                "No speech was recognized. "
                "Please select Record Again."
            )
            return

        st.session_state[
            transcript_key(step)
        ] = transcript

        st.session_state[
            signature_key
        ] = signature

        st.session_state[
            f"voice_last_transcription_{step}"
        ] = result

        st.rerun()

    except Exception as error:
        st.error(
            "Speech transcription failed. "
            "Select Record Again or type the response manually."
        )
        st.caption(
            str(error)
        )


def render_welcome_screen() -> None:
    st.markdown("## Guided Voice Reporting")

    st.info(
        "The assistant will guide you through 18 incident fields. "
        "Record one answer at a time, review the transcript and confirm it "
        "before continuing."
    )

    if st.button(
        "Start Guided Voice Report",
        type="primary",
        use_container_width=True,
    ):
        st.session_state.voice_stage = "capture"
        st.session_state.voice_step = 0
        prepare_step_transcript(0)
        st.rerun()


def render_capture_screen() -> None:
    step = int(
        st.session_state.voice_step
    )
    total = len(VOICE_FIELDS)
    field = VOICE_FIELDS[step]

    consume_pending_recording_reset(
        step
    )

    completed = len(
        st.session_state.voice_answers
    )

    st.markdown("## Guided Voice Reporting")

    st.progress(
        completed / total,
        text=(
            f"{completed} of {total} fields completed"
        ),
    )

    left_column, right_column = st.columns(
        [1.55, 1],
        gap="large",
    )

    with left_column:
        render_question_card(
            field=field,
            step=step,
            total=total,
        )

        st.markdown("")
        st.markdown("### 🎤 Voice Assistant")
        st.caption(
            "Press the microphone, speak your response and stop recording "
            "when finished."
        )

        audio_value = st.audio_input(
            f"Record {field['label']}",
            sample_rate=16000,
            key=current_audio_key(step),
            help=(
                "Use the microphone attached to your device for clearer "
                "recording input."
            ),
        )

        process_audio(
            audio_value=audio_value,
            step=step,
        )

        transcription_metadata = st.session_state.get(
            f"voice_last_transcription_{step}"
        )

        if transcription_metadata:
            status_columns = st.columns(
                2
            )

            status_columns[0].success(
                "Recording transcribed"
            )

            selected_audio = str(
                transcription_metadata.get("selected_audio", "original")
            )
            noise_status = (
                "Cleaned audio selected"
                if selected_audio == "cleaned"
                else "Original audio selected"
            )

            status_columns[1].info(
                noise_status
            )

        st.markdown("#### Review Transcript")

        transcript = st.text_area(
            "Review and edit the recognized response",
            key=transcript_key(step),
            height=(
                175
                if field["key"] == "Final Narrative"
                else 110
            ),
            placeholder=str(
                field["example"]
            ),
            help=(
                "Correct any speech-to-text errors before confirming."
            ),
            label_visibility="visible",
        )

        recording_controls = st.columns(
            2,
            gap="small",
        )

        with recording_controls[0]:
            record_again = st.button(
                "🔁 Record Again",
                use_container_width=True,
                key=f"voice_record_again_{step}",
            )

        with recording_controls[1]:
            use_transcript = st.button(
                "✓ Confirm Answer",
                type="primary",
                use_container_width=True,
                key=f"voice_use_transcript_{step}",
            )

        if record_again:
            st.session_state[
                audio_version_key(step)
            ] = int(
                st.session_state.get(
                    audio_version_key(step),
                    0,
                )
            ) + 1

            st.session_state[
                pending_reset_key(step)
            ] = True

            st.session_state.pop(
                f"voice_last_transcription_{step}",
                None,
            )

            st.rerun()

        if use_transcript:
            normalized_value, error = validate_response(
                transcript,
                field,
            )

            if error:
                st.error(
                    error
                )
            else:
                st.session_state.voice_answers[
                    field["key"]
                ] = normalized_value

                if step == total - 1:
                    st.session_state.voice_stage = "review"
                else:
                    next_step = step + 1
                    st.session_state.voice_step = next_step
                    prepare_step_transcript(
                        next_step
                    )

                st.rerun()

        navigation_columns = st.columns(
            3,
            gap="small",
        )

        with navigation_columns[0]:
            previous_clicked = st.button(
                "← Previous",
                use_container_width=True,
                disabled=step == 0,
                key=f"voice_previous_{step}",
            )

        with navigation_columns[1]:
            skip_clicked = st.button(
                "Skip Optional",
                use_container_width=True,
                disabled=bool(
                    field["required"]
                ),
                key=f"voice_skip_{step}",
            )

        with navigation_columns[2]:
            restart_clicked = st.button(
                "Start Again",
                use_container_width=True,
                key=f"voice_restart_{step}",
            )

        if previous_clicked:
            target_step = step - 1
            st.session_state.voice_step = target_step
            prepare_step_transcript(
                target_step
            )
            st.rerun()

        if skip_clicked:
            st.session_state.voice_answers[
                field["key"]
            ] = ""

            target_step = step + 1

            if target_step < total:
                st.session_state.voice_step = target_step
                prepare_step_transcript(
                    target_step
                )

            st.rerun()

        if restart_clicked:
            reset_voice_workflow()
            st.rerun()

    with right_column:
        render_captured_information()


def render_review_screen() -> None:
    st.progress(
        1.0,
        text=f"All {len(VOICE_FIELDS)} fields completed",
    )

    st.markdown("## Final Review")
    st.caption(
        "Review and edit all captured details before classification."
    )

    edited_values: Dict[str, str] = {}

    with st.form(
        "voice_final_review_form",
    ):
        review_columns = st.columns(
            2,
            gap="large",
        )

        for index, field in enumerate(
            VOICE_FIELDS
        ):
            current_value = str(
                st.session_state.voice_answers.get(
                    field["key"],
                    "",
                )
            )

            with review_columns[
                index % 2
            ]:
                if field["type"] == "narrative":
                    edited_value = st.text_area(
                        str(field["label"]),
                        value=current_value,
                        height=170,
                    )
                elif field["type"] == "yes_no":
                    options = [
                        "",
                        "Yes",
                        "No",
                    ]
                    edited_value = st.selectbox(
                        str(field["label"]),
                        options=options,
                        index=(
                            options.index(
                                current_value
                            )
                            if current_value in options
                            else 0
                        ),
                    )
                elif field["type"] == "federal_state":
                    options = [
                        "",
                        "Federal",
                        "State",
                    ]
                    edited_value = st.selectbox(
                        str(field["label"]),
                        options=options,
                        index=(
                            options.index(
                                current_value
                            )
                            if current_value in options
                            else 0
                        ),
                    )
                else:
                    edited_value = st.text_input(
                        str(field["label"]),
                        value=current_value,
                    )

                edited_values[
                    str(field["key"])
                ] = edited_value

        submit_review = st.form_submit_button(
            "Classify Voice Incident",
            type="primary",
            use_container_width=True,
        )

    action_columns = st.columns(
        2,
        gap="medium",
    )

    with action_columns[0]:
        if st.button(
            "← Return to Last Question",
            use_container_width=True,
        ):
            target_step = len(
                VOICE_FIELDS
            ) - 1

            st.session_state.voice_stage = "capture"
            st.session_state.voice_step = target_step
            prepare_step_transcript(
                target_step
            )
            st.rerun()

    with action_columns[1]:
        if st.button(
            "Discard and Start New",
            use_container_width=True,
        ):
            reset_voice_workflow()
            st.rerun()

    if submit_review:
        normalized_answers: Dict[str, str] = {}
        errors: List[str] = []

        for field in VOICE_FIELDS:
            normalized_value, error = validate_response(
                str(
                    edited_values.get(
                        str(field["key"]),
                        "",
                    )
                ),
                field,
            )

            normalized_answers[
                str(field["key"])
            ] = normalized_value

            if error:
                errors.append(
                    f"{field['label']}: {error}"
                )

        if errors:
            for error in errors:
                st.error(
                    error
                )
        else:
            st.session_state.voice_answers = (
                normalized_answers
            )
            st.session_state.voice_stage = "classify"
            st.rerun()


def render_classification_results() -> None:
    if st.session_state.voice_prediction is None:
        try:
            with st.spinner(
                "Loading the model and classifying the voice incident..."
            ):
                predictor = load_predictor()

                prediction = predictor.predict(
                    narrative=st.session_state.voice_answers[
                        "Final Narrative"
                    ],
                    include_top_predictions=True,
                    top_k=3,
                )

                report_package = generate_report(
                    incident_details=st.session_state.voice_answers,
                    prediction_result=prediction,
                )

                # Store the generated result before persistence so a temporary
                # incident-store failure does not discard a valid prediction.
                st.session_state.voice_prediction = prediction
                st.session_state.voice_report_package = report_package

                if not st.session_state.voice_saved:
                    try:
                        save_incident_record(
                            report_package
                        )
                        st.session_state.voice_saved = True
                    except Exception as save_error:
                        st.session_state.voice_save_error = str(save_error)

        except Exception as error:
            st.exception(
                error
            )

            if st.button(
                "Return to Final Review",
                use_container_width=True,
            ):
                st.session_state.voice_stage = "review"
                st.rerun()

            return

    render_prediction_results(
        st.session_state.voice_prediction,
        st.session_state.voice_report_package,
    )

    save_error = st.session_state.get(
        "voice_save_error"
    )
    if save_error:
        st.warning(
            "The report was classified successfully, but it could not be "
            "saved to the incident store."
        )
        st.caption(save_error)

    st.markdown("")

    if st.button(
        "Start New Voice Report",
        type="primary",
        use_container_width=True,
    ):
        reset_voice_workflow()
        st.rerun()


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
            "input, speak clearly in a quiet environment, and review each "
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

    elif stage == "classify":
        render_classification_results()

    else:
        reset_voice_workflow()
        st.rerun()
