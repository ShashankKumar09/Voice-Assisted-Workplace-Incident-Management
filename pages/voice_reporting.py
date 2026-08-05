"""
Guided field-by-field Voice Incident Reporting module.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Callable, Dict, Tuple

import pandas as pd
import streamlit as st

from dateutil import parser as date_parser

from reports.report_engine import (
    generate_report_package
)

from voice.speech_engine import (
    SpeechRecognitionEngine
)


VOICE_FIELDS = [
    {
        "key": "ID",
        "label": "Incident ID",
        "question": "Please say the Incident ID.",
        "required": True,
        "type": "text",
        "example": "INC-1001",
    },
    {
        "key": "UPA",
        "label": "UPA",
        "question": "Please say the UPA.",
        "required": False,
        "type": "text",
        "example": "UPA-2501",
    },
    {
        "key": "EventDate",
        "label": "Event Date",
        "question": (
            "Please say the date when the incident occurred."
        ),
        "required": False,
        "type": "date",
        "example": "5 August 2026",
    },
    {
        "key": "Employer",
        "label": "Employer",
        "question": "Please say the employer name.",
        "required": False,
        "type": "text",
        "example": "ABC Manufacturing",
    },
    {
        "key": "Address1",
        "label": "Address Line 1",
        "question": "Please say Address Line 1.",
        "required": False,
        "type": "text",
        "example": "100 Industrial Road",
    },
    {
        "key": "Address2",
        "label": "Address Line 2",
        "question": (
            "Please say Address Line 2, "
            "or skip this field."
        ),
        "required": False,
        "type": "text",
        "example": "Building B",
    },
    {
        "key": "City",
        "label": "City",
        "question": "Please say the city.",
        "required": False,
        "type": "text",
        "example": "Bengaluru",
    },
    {
        "key": "State",
        "label": "State",
        "question": "Please say the state.",
        "required": False,
        "type": "text",
        "example": "Karnataka",
    },
    {
        "key": "Zip",
        "label": "ZIP / Postal Code",
        "question": (
            "Please say the ZIP or postal code."
        ),
        "required": False,
        "type": "text",
        "example": "560001",
    },
    {
        "key": "Latitude",
        "label": "Latitude",
        "question": (
            "Please say the latitude, "
            "or skip this field."
        ),
        "required": False,
        "type": "latitude",
        "example": "12.9716",
    },
    {
        "key": "Longitude",
        "label": "Longitude",
        "question": (
            "Please say the longitude, "
            "or skip this field."
        ),
        "required": False,
        "type": "longitude",
        "example": "77.5946",
    },
    {
        "key": "Primary NAICS",
        "label": "Primary NAICS",
        "question": (
            "Please say the Primary NAICS code."
        ),
        "required": False,
        "type": "text",
        "example": "332710",
    },
    {
        "key": "Hospitalized",
        "label": "Hospitalized",
        "question": (
            "Was the employee hospitalized? "
            "Please say Yes or No."
        ),
        "required": False,
        "type": "yes_no",
        "example": "Yes",
    },
    {
        "key": "Amputation",
        "label": "Amputation",
        "question": (
            "Did the incident involve an amputation? "
            "Please say Yes or No."
        ),
        "required": False,
        "type": "yes_no",
        "example": "No",
    },
    {
        "key": "Loss of Eye",
        "label": "Loss of Eye",
        "question": (
            "Did the incident involve loss of an eye? "
            "Please say Yes or No."
        ),
        "required": False,
        "type": "yes_no",
        "example": "No",
    },
    {
        "key": "Inspection",
        "label": "Inspection",
        "question": (
            "Please say the inspection reference."
        ),
        "required": False,
        "type": "text",
        "example": "INS-45021",
    },
    {
        "key": "FederalState",
        "label": "Federal / State",
        "question": (
            "Please say Federal or State."
        ),
        "required": False,
        "type": "federal_state",
        "example": "State",
    },
    {
        "key": "Final Narrative",
        "label": "Final Narrative",
        "question": (
            "Please describe what happened. "
            "Include the activity, event, injury, "
            "body part and source where known."
        ),
        "required": True,
        "type": "narrative",
        "example": (
            "An employee slipped on a wet floor, "
            "fell on the same level, and fractured "
            "the left ankle."
        ),
    },
]


def initialize_voice_state() -> None:

    defaults = {
        "voice_stage":
            "welcome",

        "voice_step":
            0,

        "voice_data":
            {},

        "voice_draft":
            "",

        "voice_prediction":
            None,

        "voice_report_package":
            None,

        "voice_saved":
            False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


def reset_voice_workflow() -> None:

    keys = [
        "voice_stage",
        "voice_step",
        "voice_data",
        "voice_draft",
        "voice_prediction",
        "voice_report_package",
        "voice_saved",
        "voice_audio_signature",
    ]

    for key in keys:

        st.session_state.pop(
            key,
            None,
        )

    initialize_voice_state()


@st.cache_resource(
    show_spinner=False
)
def load_speech_engine():

    # Run Whisper on CPU to avoid competing
    # with DeBERTa for GPU memory.
    return SpeechRecognitionEngine(
        model_size="tiny.en",
        device="cpu",
        compute_type="int8",
    )


def normalize_value(
    raw_value: Any,
    field: Dict[str, Any],
) -> Tuple[str, str | None]:

    text = (
        ""
        if raw_value is None
        else str(raw_value).strip()
    )

    if not text:

        if field["required"]:

            return (
                "",
                f"{field['label']} is required."
            )

        return "", None

    field_type = field[
        "type"
    ]

    if field_type == "yes_no":

        normalized = (
            text.lower()
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

        return (
            "",
            "Please answer Yes or No."
        )

    if field_type == "federal_state":

        normalized = (
            text.lower()
            .strip()
        )

        if "federal" in normalized:

            return "Federal", None

        if (
            normalized == "state"
            or normalized.endswith(
                " state"
            )
        ):

            return "State", None

        return (
            "",
            "Please provide Federal or State."
        )

    if field_type == "date":

        try:

            parsed_date = date_parser.parse(
                text,
                fuzzy=True,
                dayfirst=False,
            )

            return (
                parsed_date.strftime(
                    "%Y-%m-%d"
                ),
                None,
            )

        except (
            ValueError,
            OverflowError,
        ):

            return (
                "",
                "The Event Date was not recognized."
            )

    if field_type in {
        "latitude",
        "longitude",
    }:

        numeric_text = (
            text.lower()
            .replace(
                "minus ",
                "-"
            )
            .replace(
                "negative ",
                "-"
            )
            .replace(
                ",",
                "."
            )
        )

        try:

            numeric_value = float(
                numeric_text
            )

        except ValueError:

            return (
                "",
                f"{field['label']} must be numeric."
            )

        minimum, maximum = (
            (-90.0, 90.0)
            if field_type == "latitude"
            else (-180.0, 180.0)
        )

        if not (
            minimum
            <= numeric_value
            <= maximum
        ):

            return (
                "",
                f"{field['label']} must be between "
                f"{minimum:g} and {maximum:g}."
            )

        return (
            str(
                numeric_value
            ),
            None,
        )

    if field_type == "narrative":

        if (
            len(text) < 15
            or len(
                text.split()
            ) < 4
        ):

            return (
                "",
                "Please provide a more descriptive "
                "incident narrative."
            )

    return text, None


def save_to_incident_store(
    incident_data_path: Path,
    report_package: Dict[str, Any],
) -> None:

    new_record_df = report_package[
        "csv_dataframe"
    ].copy()

    incident_data_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if incident_data_path.is_file():

        existing_df = pd.read_csv(
            incident_data_path,
            low_memory=False,
        )

    else:

        existing_df = pd.DataFrame()

    incident_id = str(
        new_record_df
        .iloc[0]
        .get(
            "ID",
            "",
        )
    ).strip()

    if (
        not existing_df.empty
        and "ID" in existing_df.columns
        and incident_id
    ):

        existing_df = existing_df[
            existing_df[
                "ID"
            ].astype(
                str
            ).str.strip()
            != incident_id
        ]

    combined_df = pd.concat(
        [
            existing_df,
            new_record_df,
        ],
        ignore_index=True,
        sort=False,
    )

    combined_df.to_csv(
        incident_data_path,
        index=False,
    )


def render_header() -> None:

    st.markdown(
        """
        <div class="hero-shell"
             style="padding:2.4rem 2.6rem">

            <div class="hero-eyebrow">
                Guided Incident Capture
            </div>

            <div class="hero-title"
                 style="font-size:2.65rem">
                🎤 Voice Incident Reporting
            </div>

            <div class="hero-subtitle">
                Record one response at a time,
                review the recognized text, confirm
                the value and continue until the
                incident report is complete.
            </div>

            <div class="hero-pill-row">
                <div class="hero-pill">
                    18 guided fields
                </div>

                <div class="hero-pill">
                    Editable transcript
                </div>

                <div class="hero-pill">
                    Classification & routing
                </div>

                <div class="hero-pill">
                    PDF and CSV downloads
                </div>
            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_welcome() -> None:

    st.markdown(
        """
        <div class="info-panel">
            <b>How it works</b><br/>
            The assistant asks one question at a time.
            Record your response, correct the recognized
            text where needed, and confirm it before
            moving to the next field.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        "<div style='height:1rem'></div>",
        unsafe_allow_html=True,
    )

    if st.button(
        "Start Guided Voice Report",
        type="primary",
        use_container_width=True,
    ):

        st.session_state[
            "voice_stage"
        ] = "capture"

        st.rerun()


def render_capture() -> None:

    step = int(
        st.session_state[
            "voice_step"
        ]
    )

    field = VOICE_FIELDS[
        step
    ]

    completed = len(
        st.session_state[
            "voice_data"
        ]
    )

    total = len(
        VOICE_FIELDS
    )

    st.progress(
        completed / total,
        text=(
            f"{completed} of "
            f"{total} fields completed"
        ),
    )

    left_column, right_column = (
        st.columns(
            [1.55, 1],
            gap="large",
        )
    )

    with left_column:

        st.markdown(
            f"""
            <div class="module-card"
                 style="min-height:auto">

                <div class="section-kicker">
                    Field {step + 1} of {total}
                </div>

                <div class="section-title">
                    {escape(field["label"])}
                </div>

                <div class="section-description">
                    {escape(field["question"])}
                </div>

                <div class="info-panel">
                    <b>Example:</b>
                    {escape(field["example"])}
                </div>

            </div>
            """,
            unsafe_allow_html=True,
        )

        audio_value = st.audio_input(
            f"Record {field['label']}",
            sample_rate=16000,
            key=f"voice_audio_{step}",
            help=(
                "Speak clearly and stop recording "
                "when finished."
            ),
        )

        if audio_value is not None:

            audio_bytes = (
                audio_value.getvalue()
            )

            audio_signature = (
                step,
                len(audio_bytes),
                hash(
                    audio_bytes[:512]
                ),
            )

            previous_signature = (
                st.session_state.get(
                    "voice_audio_signature"
                )
            )

            if (
                previous_signature
                != audio_signature
            ):

                with st.spinner(
                    "Transcribing your response..."
                ):

                    try:

                        transcription = (
                            load_speech_engine()
                            .transcribe_bytes(
                                audio_bytes,
                                language="en",
                            )
                        )

                        st.session_state[
                            "voice_draft"
                        ] = transcription[
                            "transcript"
                        ]

                        st.session_state[
                            "voice_audio_signature"
                        ] = audio_signature

                    except Exception as error:

                        st.error(
                            "Transcription failed: "
                            f"{error}"
                        )

        draft_value = st.text_area(
            "Recognized response",
            value=st.session_state.get(
                "voice_draft",
                "",
            ),
            key=f"voice_text_{step}",
            height=(
                150
                if field["type"]
                == "narrative"
                else 90
            ),
            placeholder=field[
                "example"
            ],
            help=(
                "Edit the transcript before "
                "confirming it."
            ),
        )

        st.session_state[
            "voice_draft"
        ] = draft_value

        action_columns = st.columns(
            3
        )

        with action_columns[0]:

            if st.button(
                "Confirm & Continue",
                type="primary",
                use_container_width=True,
                key=f"confirm_{step}",
            ):

                value, error = normalize_value(
                    draft_value,
                    field,
                )

                if error:

                    st.error(
                        error
                    )

                else:

                    st.session_state[
                        "voice_data"
                    ][field["key"]] = value

                    st.session_state[
                        "voice_draft"
                    ] = ""

                    st.session_state.pop(
                        "voice_audio_signature",
                        None,
                    )

                    if (
                        step
                        == total - 1
                    ):

                        st.session_state[
                            "voice_stage"
                        ] = "review"

                    else:

                        st.session_state[
                            "voice_step"
                        ] = step + 1

                    st.rerun()

        with action_columns[1]:

            if st.button(
                "Skip Optional",
                use_container_width=True,
                disabled=field[
                    "required"
                ],
                key=f"skip_{step}",
            ):

                st.session_state[
                    "voice_data"
                ][field["key"]] = ""

                st.session_state[
                    "voice_draft"
                ] = ""

                st.session_state.pop(
                    "voice_audio_signature",
                    None,
                )

                st.session_state[
                    "voice_step"
                ] = step + 1

                st.rerun()

        with action_columns[2]:

            if st.button(
                "Start Again",
                use_container_width=True,
                key=f"reset_{step}",
            ):

                reset_voice_workflow()
                st.rerun()

        if (
            step > 0
            and st.button(
                "← Previous Field",
                use_container_width=True,
                key=f"previous_{step}",
            )
        ):

            previous_step = (
                step - 1
            )

            previous_field = (
                VOICE_FIELDS[
                    previous_step
                ]
            )

            st.session_state[
                "voice_step"
            ] = previous_step

            st.session_state[
                "voice_draft"
            ] = st.session_state[
                "voice_data"
            ].get(
                previous_field[
                    "key"
                ],
                "",
            )

            st.session_state[
                "voice_data"
            ].pop(
                previous_field[
                    "key"
                ],
                None,
            )

            st.session_state.pop(
                "voice_audio_signature",
                None,
            )

            st.rerun()

    with right_column:

        st.markdown(
            """
            <div class="section-kicker">
                Report Progress
            </div>

            <div class="section-title"
                 style="font-size:1.25rem">
                Confirmed responses
            </div>
            """,
            unsafe_allow_html=True,
        )

        if not st.session_state[
            "voice_data"
        ]:

            st.info(
                "Confirmed responses "
                "will appear here."
            )

        for saved_field in VOICE_FIELDS:

            field_key = saved_field[
                "key"
            ]

            if (
                field_key
                in st.session_state[
                    "voice_data"
                ]
            ):

                field_value = (
                    st.session_state[
                        "voice_data"
                    ][field_key]
                    or "Skipped"
                )

                st.markdown(
                    f"""
                    <div class="kpi-card"
                         style="
                             padding:.8rem 1rem;
                             margin-bottom:.55rem;
                         ">

                        <div class="kpi-label">
                            {escape(saved_field["label"])}
                        </div>

                        <div style="
                            font-size:.82rem;
                            color:#243746;
                            margin-top:.25rem;
                        ">
                            {escape(str(field_value))}
                        </div>

                    </div>
                    """,
                    unsafe_allow_html=True,
                )


def render_review() -> None:

    st.progress(
        1.0,
        text="All 18 fields captured",
    )

    st.markdown(
        """
        <div class="section-kicker">
            Final Review
        </div>

        <div class="section-title">
            Review the incident details
        </div>

        <div class="section-description">
            Correct any field before submitting
            the Final Narrative for classification.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.form(
        "voice_review_form"
    ):

        columns = st.columns(
            2,
            gap="large",
        )

        edited_data = {}

        for index, field in enumerate(
            VOICE_FIELDS
        ):

            with columns[
                index % 2
            ]:

                current_value = (
                    st.session_state[
                        "voice_data"
                    ].get(
                        field["key"],
                        "",
                    )
                )

                if (
                    field["type"]
                    == "narrative"
                ):

                    edited_value = (
                        st.text_area(
                            field["label"],
                            value=current_value,
                            height=160,
                        )
                    )

                elif (
                    field["type"]
                    == "yes_no"
                ):

                    options = [
                        "",
                        "Yes",
                        "No",
                    ]

                    edited_value = (
                        st.selectbox(
                            field["label"],
                            options=options,
                            index=(
                                options.index(
                                    current_value
                                )
                                if current_value
                                in options
                                else 0
                            ),
                        )
                    )

                elif (
                    field["type"]
                    == "federal_state"
                ):

                    options = [
                        "",
                        "Federal",
                        "State",
                    ]

                    edited_value = (
                        st.selectbox(
                            field["label"],
                            options=options,
                            index=(
                                options.index(
                                    current_value
                                )
                                if current_value
                                in options
                                else 0
                            ),
                        )
                    )

                else:

                    edited_value = (
                        st.text_input(
                            field["label"],
                            value=current_value,
                        )
                    )

                edited_data[
                    field["key"]
                ] = edited_value

        submitted = (
            st.form_submit_button(
                "Submit and Classify Incident",
                type="primary",
                use_container_width=True,
            )
        )

    control_columns = st.columns(
        2
    )

    with control_columns[0]:

        if st.button(
            "← Return to Last Field",
            use_container_width=True,
        ):

            st.session_state[
                "voice_stage"
            ] = "capture"

            st.session_state[
                "voice_step"
            ] = len(
                VOICE_FIELDS
            ) - 1

            st.session_state[
                "voice_draft"
            ] = st.session_state[
                "voice_data"
            ].get(
                "Final Narrative",
                "",
            )

            st.session_state[
                "voice_data"
            ].pop(
                "Final Narrative",
                None,
            )

            st.rerun()

    with control_columns[1]:

        if st.button(
            "Discard and Start New",
            use_container_width=True,
        ):

            reset_voice_workflow()
            st.rerun()

    if submitted:

        normalized_data = {}
        validation_errors = []

        for field in VOICE_FIELDS:

            value, error = normalize_value(
                edited_data.get(
                    field["key"],
                    "",
                ),
                field,
            )

            normalized_data[
                field["key"]
            ] = value

            if error:

                validation_errors.append(
                    f"{field['label']}: {error}"
                )

        if validation_errors:

            for validation_error in (
                validation_errors
            ):

                st.error(
                    validation_error
                )

        else:

            st.session_state[
                "voice_data"
            ] = normalized_data

            st.session_state[
                "voice_stage"
            ] = "classify"

            st.rerun()


def render_results(
    predictor_loader: Callable[[], Any],
    incident_data_path: Path,
) -> None:

    if (
        st.session_state[
            "voice_prediction"
        ]
        is None
    ):

        with st.spinner(
            "Loading the model and "
            "classifying the incident..."
        ):

            try:

                predictor = (
                    predictor_loader()
                )

                prediction = predictor.predict(
                    narrative=(
                        st.session_state[
                            "voice_data"
                        ][
                            "Final Narrative"
                        ]
                    ),
                    include_top_predictions=True,
                    top_k=3,
                )

                report_package = (
                    generate_report_package(
                        incident_details=(
                            st.session_state[
                                "voice_data"
                            ]
                        ),
                        prediction_result=prediction,
                        reporting_channel=(
                            "Voice Incident Reporting"
                        ),
                    )
                )

                st.session_state[
                    "voice_prediction"
                ] = prediction

                st.session_state[
                    "voice_report_package"
                ] = report_package

                if not st.session_state[
                    "voice_saved"
                ]:

                    save_to_incident_store(
                        incident_data_path,
                        report_package,
                    )

                    st.session_state[
                        "voice_saved"
                    ] = True

            except Exception as error:

                st.error(
                    "Classification failed: "
                    f"{error}"
                )

                if st.button(
                    "Return to Review"
                ):

                    st.session_state[
                        "voice_stage"
                    ] = "review"

                    st.rerun()

                return

    prediction = st.session_state[
        "voice_prediction"
    ]

    report_package = st.session_state[
        "voice_report_package"
    ]

    st.success(
        "Incident classification "
        "completed successfully."
    )

    st.markdown(
        """
        <div class="section-kicker">
            Classification Results
        </div>

        <div class="section-title">
            Four-target incident classification
        </div>
        """,
        unsafe_allow_html=True,
    )

    prediction_columns = st.columns(
        4
    )

    for column, task_name in zip(
        prediction_columns,
        [
            "nature",
            "body",
            "event",
            "source",
        ],
    ):

        task_result = prediction[
            "predictions"
        ][task_name]

        with column:

            st.markdown(
                f"""
                <div class="module-card"
                     style="min-height:210px">

                    <div class="module-title">
                        {escape(task_name.title())}
                    </div>

                    <div class="module-description">
                        <b>
                            {escape(task_result["label"])}
                        </b>
                    </div>

                    <div class="module-footer">
                        Confidence:
                        {task_result["confidence_percent"]:.2f}%
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    overall_confidence = prediction[
        "incident_confidence"
    ][
        "geometric_mean_percent"
    ]

    decision_tier = prediction[
        "decision"
    ][
        "tier"
    ]

    historical = prediction[
        "relationship_validation"
    ]

    summary_columns = st.columns(
        3
    )

    summary_values = [
        (
            "Overall Confidence",
            f"{overall_confidence:.2f}%",
        ),
        (
            "Decision Tier — Final Outcome",
            decision_tier,
        ),
        (
            "Historical Validation",
            historical[
                "historical_validation_status"
            ],
        ),
    ]

    for column, (
        label,
        value,
    ) in zip(
        summary_columns,
        summary_values,
    ):

        with column:

            st.markdown(
                f"""
                <div class="kpi-card">

                    <div class="kpi-label">
                        {escape(label)}
                    </div>

                    <div class="kpi-value"
                         style="font-size:1.25rem">
                        {escape(str(value))}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander(
        "Historical Validation details"
    ):

        st.info(
            "Historical Validation checks whether "
            "the predicted Nature, Body, Event and "
            "Source classifications have been observed "
            "together in historical incident records. "
            "It does not change the classifications or "
            "the Decision Tier."
        )

        historical_df = pd.DataFrame({
            "Measure": [
                "Historical Validation Status",
                "Historical Score",
                "Weakest Historical Relationship",
                "Weakest Relationship Score",
                "Interpretation",
            ],
            "Value": [
                historical[
                    "historical_validation_status"
                ],
                (
                    f"{historical['consistency_score']:.6f}"
                ),
                historical[
                    "weakest_relationship"
                ],
                (
                    f"{historical['weakest_relationship_score']:.6f}"
                ),
                historical[
                    "message"
                ],
            ],
        })

        st.dataframe(
            historical_df,
            hide_index=True,
            use_container_width=True,
        )

    st.markdown(
        """
        <div class="section-kicker">
            Report Downloads
        </div>

        <div class="section-title"
             style="font-size:1.35rem">
            Download the completed report
        </div>
        """,
        unsafe_allow_html=True,
    )

    download_columns = st.columns(
        3
    )

    with download_columns[0]:

        st.download_button(
            "Download PDF Report",
            data=report_package[
                "pdf_bytes"
            ],
            file_name=report_package[
                "pdf_filename"
            ],
            mime="application/pdf",
            use_container_width=True,
        )

    with download_columns[1]:

        st.download_button(
            "Download CSV Record",
            data=report_package[
                "csv_bytes"
            ],
            file_name=report_package[
                "csv_filename"
            ],
            mime="text/csv",
            use_container_width=True,
        )

    with download_columns[2]:

        if st.button(
            "Start New Voice Report",
            type="primary",
            use_container_width=True,
        ):

            reset_voice_workflow()
            st.rerun()


def render_voice_reporting_page(
    predictor_loader: Callable[[], Any],
    incident_data_path: Path,
) -> None:

    initialize_voice_state()
    render_header()

    stage = st.session_state[
        "voice_stage"
    ]

    if stage == "welcome":

        render_welcome()

    elif stage == "capture":

        render_capture()

    elif stage == "review":

        render_review()

    elif stage == "classify":

        render_results(
            predictor_loader,
            incident_data_path,
        )

    else:

        reset_voice_workflow()
        st.rerun()
