"""
Professional Manual Incident Reporting module.
"""

from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
from typing import Any, Callable, Dict, List, Tuple

import pandas as pd
import streamlit as st

from reports.report_engine import (
    generate_report_package
)


MANUAL_FIELDS = [
    "ID",
    "UPA",
    "EventDate",
    "Employer",
    "Address1",
    "Address2",
    "City",
    "State",
    "Zip",
    "Latitude",
    "Longitude",
    "Primary NAICS",
    "Hospitalized",
    "Amputation",
    "Loss of Eye",
    "Inspection",
    "FederalState",
    "Final Narrative",
]


def initialize_manual_state() -> None:

    defaults = {
        "manual_stage":
            "form",

        "manual_data":
            {},

        "manual_prediction":
            None,

        "manual_report_package":
            None,

        "manual_saved":
            False,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


def reset_manual_workflow() -> None:

    keys = [
        "manual_stage",
        "manual_data",
        "manual_prediction",
        "manual_report_package",
        "manual_saved",
    ]

    for key in keys:

        st.session_state.pop(
            key,
            None,
        )

    initialize_manual_state()


def clean_text(
    value: Any,
) -> str:

    if value is None:

        return ""

    try:

        if pd.isna(
            value
        ):

            return ""

    except Exception:

        pass

    return str(
        value
    ).strip()


def validate_manual_incident(
    incident_data: Dict[str, Any],
) -> Tuple[
    Dict[str, Any],
    List[str],
    List[str],
]:

    normalized_data = {
        field:
            clean_text(
                incident_data.get(
                    field,
                    "",
                )
            )
        for field in MANUAL_FIELDS
    }

    errors = []
    warnings = []

    # --------------------------------------------------------------------------
    # Required fields
    # --------------------------------------------------------------------------

    if not normalized_data[
        "ID"
    ]:

        errors.append(
            "Incident ID is required."
        )

    narrative = normalized_data[
        "Final Narrative"
    ]

    if not narrative:

        errors.append(
            "Final Narrative is required."
        )

    elif (
        len(narrative) < 15
        or len(
            narrative.split()
        ) < 4
    ):

        errors.append(
            "Final Narrative must contain at least "
            "15 characters and four words."
        )

    # --------------------------------------------------------------------------
    # Event date
    # --------------------------------------------------------------------------

    event_date = normalized_data[
        "EventDate"
    ]

    if not event_date:

        warnings.append(
            "Event Date is empty."
        )

    # --------------------------------------------------------------------------
    # Coordinates
    # --------------------------------------------------------------------------

    for column, minimum, maximum in [
        (
            "Latitude",
            -90.0,
            90.0,
        ),
        (
            "Longitude",
            -180.0,
            180.0,
        ),
    ]:

        coordinate_text = normalized_data[
            column
        ]

        if coordinate_text:

            try:

                coordinate_value = float(
                    coordinate_text
                )

            except ValueError:

                errors.append(
                    f"{column} must be numeric."
                )

                continue

            if not (
                minimum
                <= coordinate_value
                <= maximum
            ):

                errors.append(
                    f"{column} must be between "
                    f"{minimum:g} and {maximum:g}."
                )

            else:

                normalized_data[
                    column
                ] = str(
                    coordinate_value
                )

    if bool(
        normalized_data[
            "Latitude"
        ]
    ) != bool(
        normalized_data[
            "Longitude"
        ]
    ):

        warnings.append(
            "Latitude and Longitude should normally "
            "be provided together."
        )

    # --------------------------------------------------------------------------
    # Controlled values
    # --------------------------------------------------------------------------

    for yes_no_column in [
        "Hospitalized",
        "Amputation",
        "Loss of Eye",
    ]:

        value = normalized_data[
            yes_no_column
        ]

        if value not in {
            "",
            "Yes",
            "No",
        }:

            errors.append(
                f"{yes_no_column} must contain Yes or No."
            )

    federal_state = normalized_data[
        "FederalState"
    ]

    if federal_state not in {
        "",
        "Federal",
        "State",
    }:

        errors.append(
            "Federal / State must contain Federal or State."
        )

    return (
        normalized_data,
        errors,
        warnings,
    )


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


def render_manual_header() -> None:

    st.markdown(
        """
        <div class="hero-shell"
             style="padding:2.4rem 2.6rem">

            <div class="hero-eyebrow">
                Structured Incident Capture
            </div>

            <div class="hero-title"
                 style="font-size:2.65rem">
                📝 Manual Incident Reporting
            </div>

            <div class="hero-subtitle">
                Complete the structured incident form,
                review the captured details and classify
                the Final Narrative using the shared
                multi-task incident-classification engine.
            </div>

            <div class="hero-pill-row">

                <div class="hero-pill">
                    18 incident fields
                </div>

                <div class="hero-pill">
                    Input validation
                </div>

                <div class="hero-pill">
                    Four classifications
                </div>

                <div class="hero-pill">
                    PDF and CSV downloads
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_manual_form() -> None:

    st.markdown(
        """
        <div class="section-kicker">
            Incident Information
        </div>

        <div class="section-title">
            Enter the workplace incident details
        </div>

        <div class="section-description">
            Incident ID and Final Narrative are required.
            Other fields may be completed where the
            information is available.
        </div>
        """,
        unsafe_allow_html=True,
    )

    saved_data = st.session_state[
        "manual_data"
    ]

    with st.form(
        "manual_incident_form",
        clear_on_submit=False,
    ):

        # ----------------------------------------------------------------------
        # Reference information
        # ----------------------------------------------------------------------

        st.markdown(
            "#### Reference Information"
        )

        reference_columns = st.columns(
            3,
            gap="large",
        )

        with reference_columns[0]:

            incident_id = st.text_input(
                "Incident ID *",
                value=saved_data.get(
                    "ID",
                    "",
                ),
                placeholder="INC-1001",
                help=(
                    "A unique identifier for the incident."
                ),
            )

        with reference_columns[1]:

            upa = st.text_input(
                "UPA",
                value=saved_data.get(
                    "UPA",
                    "",
                ),
                placeholder="UPA-2501",
            )

        with reference_columns[2]:

            saved_event_date = saved_data.get(
                "EventDate",
                "",
            )

            try:

                event_date_default = (
                    pd.to_datetime(
                        saved_event_date
                    ).date()
                    if saved_event_date
                    else None
                )

            except Exception:

                event_date_default = None

            event_date = st.date_input(
                "Event Date",
                value=event_date_default,
                format="YYYY-MM-DD",
            )

        # ----------------------------------------------------------------------
        # Employer and location
        # ----------------------------------------------------------------------

        st.markdown(
            "#### Employer and Location"
        )

        employer_columns = st.columns(
            2,
            gap="large",
        )

        with employer_columns[0]:

            employer = st.text_input(
                "Employer",
                value=saved_data.get(
                    "Employer",
                    "",
                ),
                placeholder="ABC Manufacturing",
            )

        with employer_columns[1]:

            primary_naics = st.text_input(
                "Primary NAICS",
                value=saved_data.get(
                    "Primary NAICS",
                    "",
                ),
                placeholder="332710",
            )

        address_columns = st.columns(
            2,
            gap="large",
        )

        with address_columns[0]:

            address_1 = st.text_input(
                "Address Line 1",
                value=saved_data.get(
                    "Address1",
                    "",
                ),
                placeholder="100 Industrial Road",
            )

        with address_columns[1]:

            address_2 = st.text_input(
                "Address Line 2",
                value=saved_data.get(
                    "Address2",
                    "",
                ),
                placeholder="Building B",
            )

        location_columns = st.columns(
            3,
            gap="large",
        )

        with location_columns[0]:

            city = st.text_input(
                "City",
                value=saved_data.get(
                    "City",
                    "",
                ),
                placeholder="Bengaluru",
            )

        with location_columns[1]:

            state = st.text_input(
                "State",
                value=saved_data.get(
                    "State",
                    "",
                ),
                placeholder="Karnataka",
            )

        with location_columns[2]:

            zip_code = st.text_input(
                "ZIP / Postal Code",
                value=saved_data.get(
                    "Zip",
                    "",
                ),
                placeholder="560001",
            )

        coordinate_columns = st.columns(
            2,
            gap="large",
        )

        with coordinate_columns[0]:

            latitude = st.text_input(
                "Latitude",
                value=saved_data.get(
                    "Latitude",
                    "",
                ),
                placeholder="12.9716",
                help=(
                    "Valid range: -90 to 90."
                ),
            )

        with coordinate_columns[1]:

            longitude = st.text_input(
                "Longitude",
                value=saved_data.get(
                    "Longitude",
                    "",
                ),
                placeholder="77.5946",
                help=(
                    "Valid range: -180 to 180."
                ),
            )

        # ----------------------------------------------------------------------
        # Incident indicators
        # ----------------------------------------------------------------------

        st.markdown(
            "#### Incident Indicators"
        )

        indicator_columns = st.columns(
            4,
            gap="large",
        )

        yes_no_options = [
            "",
            "Yes",
            "No",
        ]

        with indicator_columns[0]:

            current_value = saved_data.get(
                "Hospitalized",
                "",
            )

            hospitalized = st.selectbox(
                "Hospitalized",
                options=yes_no_options,
                index=(
                    yes_no_options.index(
                        current_value
                    )
                    if current_value
                    in yes_no_options
                    else 0
                ),
            )

        with indicator_columns[1]:

            current_value = saved_data.get(
                "Amputation",
                "",
            )

            amputation = st.selectbox(
                "Amputation",
                options=yes_no_options,
                index=(
                    yes_no_options.index(
                        current_value
                    )
                    if current_value
                    in yes_no_options
                    else 0
                ),
            )

        with indicator_columns[2]:

            current_value = saved_data.get(
                "Loss of Eye",
                "",
            )

            loss_of_eye = st.selectbox(
                "Loss of Eye",
                options=yes_no_options,
                index=(
                    yes_no_options.index(
                        current_value
                    )
                    if current_value
                    in yes_no_options
                    else 0
                ),
            )

        with indicator_columns[3]:

            federal_state_options = [
                "",
                "Federal",
                "State",
            ]

            current_value = saved_data.get(
                "FederalState",
                "",
            )

            federal_state = st.selectbox(
                "Federal / State",
                options=federal_state_options,
                index=(
                    federal_state_options.index(
                        current_value
                    )
                    if current_value
                    in federal_state_options
                    else 0
                ),
            )

        inspection = st.text_input(
            "Inspection",
            value=saved_data.get(
                "Inspection",
                "",
            ),
            placeholder="INS-45021",
        )

        # ----------------------------------------------------------------------
        # Narrative
        # ----------------------------------------------------------------------

        st.markdown(
            "#### Final Narrative"
        )

        st.info(
            "Describe the activity being performed, "
            "what happened, the resulting injury, "
            "the affected body part and the source "
            "or object involved, where known."
        )

        final_narrative = st.text_area(
            "Final Narrative *",
            value=saved_data.get(
                "Final Narrative",
                "",
            ),
            height=190,
            placeholder=(
                "An employee slipped on a wet floor, "
                "fell on the same level, and fractured "
                "the left ankle."
            ),
        )

        submit_form = (
            st.form_submit_button(
                "Review Incident Details",
                type="primary",
                use_container_width=True,
            )
        )

    reset_column, info_column = st.columns(
        [1, 2],
        gap="large",
    )

    with reset_column:

        if st.button(
            "Clear Form",
            use_container_width=True,
        ):

            reset_manual_workflow()
            st.rerun()

    with info_column:

        st.markdown(
            """
            <div class="info-panel">
                The model uses only the Final Narrative
                for classification. All other fields are
                preserved in the incident report and
                analytics data.
            </div>
            """,
            unsafe_allow_html=True,
        )

    if submit_form:

        incident_data = {
            "ID":
                incident_id,

            "UPA":
                upa,

            "EventDate":
                (
                    event_date.strftime(
                        "%Y-%m-%d"
                    )
                    if event_date
                    else ""
                ),

            "Employer":
                employer,

            "Address1":
                address_1,

            "Address2":
                address_2,

            "City":
                city,

            "State":
                state,

            "Zip":
                zip_code,

            "Latitude":
                latitude,

            "Longitude":
                longitude,

            "Primary NAICS":
                primary_naics,

            "Hospitalized":
                hospitalized,

            "Amputation":
                amputation,

            "Loss of Eye":
                loss_of_eye,

            "Inspection":
                inspection,

            "FederalState":
                federal_state,

            "Final Narrative":
                final_narrative,
        }

        (
            normalized_data,
            errors,
            warnings,
        ) = validate_manual_incident(
            incident_data
        )

        if errors:

            for error in errors:

                st.error(
                    error
                )

        else:

            st.session_state[
                "manual_data"
            ] = normalized_data

            st.session_state[
                "manual_stage"
            ] = "review"

            st.session_state[
                "manual_form_warnings"
            ] = warnings

            st.rerun()


def render_manual_review() -> None:

    st.markdown(
        """
        <div class="section-kicker">
            Final Review
        </div>

        <div class="section-title">
            Confirm the incident details
        </div>

        <div class="section-description">
            Review the information below before the
            Final Narrative is submitted for classification.
        </div>
        """,
        unsafe_allow_html=True,
    )

    warnings = st.session_state.get(
        "manual_form_warnings",
        [],
    )

    for warning in warnings:

        st.warning(
            warning
        )

    incident_data = st.session_state[
        "manual_data"
    ]

    structured_fields = [
        ("Incident ID", "ID"),
        ("UPA", "UPA"),
        ("Event Date", "EventDate"),
        ("Employer", "Employer"),
        ("Address Line 1", "Address1"),
        ("Address Line 2", "Address2"),
        ("City", "City"),
        ("State", "State"),
        ("ZIP / Postal Code", "Zip"),
        ("Latitude", "Latitude"),
        ("Longitude", "Longitude"),
        ("Primary NAICS", "Primary NAICS"),
        ("Hospitalized", "Hospitalized"),
        ("Amputation", "Amputation"),
        ("Loss of Eye", "Loss of Eye"),
        ("Inspection", "Inspection"),
        ("Federal / State", "FederalState"),
    ]

    review_rows = []

    for label, key in structured_fields:

        value = incident_data.get(
            key,
            "",
        )

        review_rows.append({
            "Field":
                label,

            "Value":
                value
                if value
                else "Not provided",
        })

    review_df = pd.DataFrame(
        review_rows
    )

    st.dataframe(
        review_df,
        hide_index=True,
        use_container_width=True,
        height=470,
    )

    st.markdown(
        "#### Final Narrative"
    )

    st.markdown(
        f"""
        <div class="info-panel">
            {escape(
                incident_data[
                    "Final Narrative"
                ]
            )}
        </div>
        """,
        unsafe_allow_html=True,
    )

    action_columns = st.columns(
        3,
        gap="medium",
    )

    with action_columns[0]:

        if st.button(
            "Edit Incident",
            use_container_width=True,
        ):

            st.session_state[
                "manual_stage"
            ] = "form"

            st.rerun()

    with action_columns[1]:

        if st.button(
            "Discard Incident",
            use_container_width=True,
        ):

            reset_manual_workflow()
            st.rerun()

    with action_columns[2]:

        if st.button(
            "Classify Incident",
            type="primary",
            use_container_width=True,
        ):

            st.session_state[
                "manual_stage"
            ] = "classify"

            st.rerun()


def render_manual_results(
    predictor_loader: Callable[[], Any],
    incident_data_path: Path,
) -> None:

    if (
        st.session_state[
            "manual_prediction"
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
                            "manual_data"
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
                                "manual_data"
                            ]
                        ),
                        prediction_result=prediction,
                        reporting_channel=(
                            "Manual Incident Reporting"
                        ),
                    )
                )

                st.session_state[
                    "manual_prediction"
                ] = prediction

                st.session_state[
                    "manual_report_package"
                ] = report_package

                if not st.session_state[
                    "manual_saved"
                ]:

                    save_to_incident_store(
                        incident_data_path=(
                            incident_data_path
                        ),
                        report_package=(
                            report_package
                        ),
                    )

                    st.session_state[
                        "manual_saved"
                    ] = True

            except Exception as error:

                st.error(
                    "The incident could not be classified. "
                    f"Details: {error}"
                )

                if st.button(
                    "Return to Review"
                ):

                    st.session_state[
                        "manual_stage"
                    ] = "review"

                    st.rerun()

                return

    prediction = st.session_state[
        "manual_prediction"
    ]

    report_package = st.session_state[
        "manual_report_package"
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

        <div class="section-description">
            The Decision Tier is the final business
            outcome. Historical Validation is an
            additional supporting indicator.
        </div>
        """,
        unsafe_allow_html=True,
    )

    result_columns = st.columns(
        4,
        gap="medium",
    )

    for column, task_name in zip(
        result_columns,
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
                     style="min-height:215px">

                    <div class="module-title">
                        {escape(
                            task_name.title()
                        )}
                    </div>

                    <div class="module-description"
                         style="min-height:80px">

                        <b>
                            {escape(
                                task_result[
                                    "label"
                                ]
                            )}
                        </b>

                    </div>

                    <div class="module-footer">
                        Confidence:
                        {
                            task_result[
                                "confidence_percent"
                            ]
                        :.2f}%
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "<div style='height:1rem'></div>",
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
        3,
        gap="medium",
    )

    summary_items = [
        (
            "Overall Confidence",
            f"{overall_confidence:.2f}%",
            (
                "Combined confidence across "
                "all four predictions"
            ),
        ),
        (
            "Decision Tier — Final Outcome",
            decision_tier,
            (
                "Final recommended business action"
            ),
        ),
        (
            "Historical Validation",
            historical[
                "historical_validation_status"
            ],
            (
                "Support from historical relationships"
            ),
        ),
    ]

    for column, (
        label,
        value,
        caption,
    ) in zip(
        summary_columns,
        summary_items,
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

                    <div class="kpi-caption">
                        {escape(caption)}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander(
        "Historical Validation details",
        expanded=False,
    ):

        st.info(
            "Historical Validation checks whether "
            "the predicted Nature, Body, Event and "
            "Source classifications have been observed "
            "together in historical workplace incident "
            "records. It does not change the predicted "
            "classifications or the Decision Tier."
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
            Download the completed incident report
        </div>
        """,
        unsafe_allow_html=True,
    )

    download_columns = st.columns(
        3,
        gap="medium",
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
            "Start New Manual Report",
            type="primary",
            use_container_width=True,
        ):

            reset_manual_workflow()
            st.rerun()


def render_manual_reporting_page(
    predictor_loader: Callable[[], Any],
    incident_data_path: Path,
) -> None:

    initialize_manual_state()
    render_manual_header()

    stage = st.session_state[
        "manual_stage"
    ]

    if stage == "form":

        render_manual_form()

    elif stage == "review":

        render_manual_review()

    elif stage == "classify":

        render_manual_results(
            predictor_loader=(
                predictor_loader
            ),
            incident_data_path=(
                incident_data_path
            ),
        )

    else:

        reset_manual_workflow()
        st.rerun()
