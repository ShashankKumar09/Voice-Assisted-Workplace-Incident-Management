"""
Manual Incident Reporting with live backend integration.
"""

from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict

import pandas as pd
import streamlit as st

from ui.guide_components import (
    render_module_header,
    render_user_guide,
)


APP_ROOT = Path(__file__).resolve().parents[1]
INCIDENT_DATA_PATH = APP_ROOT / "data" / "incident_records.csv"


@st.cache_resource(show_spinner=False)
def load_predictor():
    """
    Load the packaged multi-task DeBERTa predictor only when classification
    is requested. Lazy loading keeps the rest of the application responsive.
    """
    from core.predictor import IncidentPredictor

    return IncidentPredictor(
        application_root=APP_ROOT,
        device="auto",
    )


def generate_report(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
) -> Dict[str, Any]:
    """
    Generate the packaged PDF and CSV report.
    """
    from reports.report_engine import generate_report_package

    return generate_report_package(
        incident_details=incident_details,
        prediction_result=prediction_result,
        reporting_channel="Manual Incident Reporting",
    )


def save_incident_record(report_package: Dict[str, Any]) -> None:
    """
    Append the completed record to the dashboard data store.
    Existing records with the same ID are replaced.
    """
    record_df = report_package["csv_dataframe"].copy()

    INCIDENT_DATA_PATH.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    if INCIDENT_DATA_PATH.is_file():
        existing_df = pd.read_csv(
            INCIDENT_DATA_PATH,
            low_memory=False,
        )
    else:
        existing_df = pd.DataFrame()

    incident_id = str(
        record_df.iloc[0].get("ID", "")
    ).strip()

    if (
        not existing_df.empty
        and "ID" in existing_df.columns
        and incident_id
    ):
        existing_df = existing_df[
            existing_df["ID"].astype(str).str.strip() != incident_id
        ]

    combined_df = pd.concat(
        [existing_df, record_df],
        ignore_index=True,
        sort=False,
    )

    combined_df.to_csv(
        INCIDENT_DATA_PATH,
        index=False,
    )


def _prediction_value(
    prediction: Dict[str, Any],
    task_name: str,
) -> Dict[str, Any]:
    return prediction["predictions"][task_name]


def render_prediction_results(
    prediction: Dict[str, Any],
    report_package: Dict[str, Any],
) -> None:
    st.success("Incident classification completed successfully.")

    st.markdown("### Classification Results")

    columns = st.columns(4, gap="medium")

    for column, task_name, label in zip(
        columns,
        ["nature", "body", "event", "source"],
        ["Nature", "Part of Body", "Event", "Source"],
    ):
        result = _prediction_value(
            prediction,
            task_name,
        )

        with column:
            st.metric(
                label=label,
                value=str(result["label"]),
                delta=(
                    f'{float(result["confidence_percent"]):.2f}% confidence'
                ),
                delta_color="off",
            )

    overall_confidence = float(
        prediction["incident_confidence"]["geometric_mean_percent"]
    )

    decision_tier = str(
        prediction["decision"]["tier"]
    )

    relationship = prediction[
        "relationship_validation"
    ]

    summary_columns = st.columns(3, gap="medium")

    summary_columns[0].metric(
        "Overall Confidence",
        f"{overall_confidence:.2f}%",
    )

    summary_columns[1].metric(
        "Decision Tier",
        decision_tier,
    )

    summary_columns[2].metric(
        "Historical Validation",
        str(
            relationship[
                "historical_validation_status"
            ]
        ),
    )

    with st.expander(
        "Historical Validation Details"
    ):
        st.write(
            relationship.get(
                "message",
                "Historical relationship validation completed.",
            )
        )

        details_df = pd.DataFrame(
            {
                "Measure": [
                    "Historical Validation Status",
                    "Historical Score",
                    "Weakest Historical Relationship",
                    "Weakest Relationship Score",
                ],
                "Value": [
                    relationship.get(
                        "historical_validation_status",
                        "",
                    ),
                    relationship.get(
                        "consistency_score",
                        "",
                    ),
                    relationship.get(
                        "weakest_relationship",
                        "",
                    ),
                    relationship.get(
                        "weakest_relationship_score",
                        "",
                    ),
                ],
            }
        )

        st.dataframe(
            details_df,
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("### Download Completed Report")

    download_columns = st.columns(2, gap="medium")

    with download_columns[0]:
        st.download_button(
            "Download PDF Report",
            data=report_package["pdf_bytes"],
            file_name=report_package["pdf_filename"],
            mime="application/pdf",
            use_container_width=True,
        )

    with download_columns[1]:
        st.download_button(
            "Download CSV Record",
            data=report_package["csv_bytes"],
            file_name=report_package["csv_filename"],
            mime="text/csv",
            use_container_width=True,
        )


def render() -> None:
    render_module_header(
        eyebrow="Structured Incident Entry",
        title="Manual Incident Reporting",
        description=(
            "Enter workplace incident details through a structured form, "
            "validate the information and generate a classified incident report."
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
            "Ensure the Final Narrative is complete and specific because it "
            "is the primary input used for classification."
        ),
    )

    if "manual_result" not in st.session_state:
        st.session_state.manual_result = None

    if "manual_report_package" not in st.session_state:
        st.session_state.manual_report_package = None

    st.markdown("## New Incident Report")
    st.caption(
        "Fields marked with * are required. The model is loaded only after submission."
    )

    with st.form(
        "manual_incident_form",
        clear_on_submit=False,
    ):
        st.markdown("### Incident Identification")

        c1, c2, c3 = st.columns(3)

        incident_id = c1.text_input(
            "Incident ID *",
            placeholder="INC-1001",
        )

        upa = c2.text_input(
            "UPA",
            placeholder="UPA-2501",
        )

        event_date = c3.date_input(
            "Event Date",
            value=date.today(),
        )

        st.markdown("### Employer and Location")

        c1, c2 = st.columns(2)

        employer = c1.text_input(
            "Employer",
            placeholder="ABC Manufacturing",
        )

        primary_naics = c2.text_input(
            "Primary NAICS",
            placeholder="332710",
        )

        address1 = st.text_input(
            "Address Line 1",
            placeholder="100 Industrial Road",
        )

        address2 = st.text_input(
            "Address Line 2",
            placeholder="Building B",
        )

        c1, c2, c3 = st.columns(3)

        city = c1.text_input(
            "City",
            placeholder="Bengaluru",
        )

        state = c2.text_input(
            "State",
            placeholder="Karnataka",
        )

        zip_code = c3.text_input(
            "ZIP / Postal Code",
            placeholder="560001",
        )

        c1, c2 = st.columns(2)

        latitude = c1.text_input(
            "Latitude",
            placeholder="12.9716",
        )

        longitude = c2.text_input(
            "Longitude",
            placeholder="77.5946",
        )

        st.markdown("### Incident Outcomes and References")

        c1, c2, c3 = st.columns(3)

        hospitalized = c1.selectbox(
            "Hospitalized",
            ["", "Yes", "No"],
        )

        amputation = c2.selectbox(
            "Amputation",
            ["", "Yes", "No"],
        )

        loss_of_eye = c3.selectbox(
            "Loss of Eye",
            ["", "Yes", "No"],
        )

        c1, c2 = st.columns(2)

        inspection = c1.text_input(
            "Inspection",
            placeholder="INS-45021",
        )

        federal_state = c2.selectbox(
            "Federal / State",
            ["", "Federal", "State"],
        )

        st.markdown("### Final Narrative")

        final_narrative = st.text_area(
            "Describe what happened *",
            height=170,
            placeholder=(
                "Example: An employee slipped on a wet floor, fell on the "
                "same level, and fractured the left ankle."
            ),
            help=(
                "Include the activity, event, injury, body part and source "
                "where known."
            ),
        )

        submitted = st.form_submit_button(
            "Validate and Classify Incident",
            type="primary",
            use_container_width=True,
        )

    if submitted:
        errors = []

        if not incident_id.strip():
            errors.append("Incident ID is required.")

        narrative_word_count = len(
            final_narrative.strip().split()
        )

        if (
            len(final_narrative.strip()) < 15
            or narrative_word_count < 4
        ):
            errors.append(
                "Final Narrative must contain a clear incident description."
            )

        for field_label, value, minimum, maximum in [
            ("Latitude", latitude, -90.0, 90.0),
            ("Longitude", longitude, -180.0, 180.0),
        ]:
            if value.strip():
                try:
                    numeric_value = float(value)
                except ValueError:
                    errors.append(
                        f"{field_label} must be numeric."
                    )
                else:
                    if not minimum <= numeric_value <= maximum:
                        errors.append(
                            f"{field_label} must be between "
                            f"{minimum:g} and {maximum:g}."
                        )

        if errors:
            for error in errors:
                st.error(error)
        else:
            incident_details = {
                "ID": incident_id.strip(),
                "UPA": upa.strip(),
                "EventDate": event_date.strftime("%Y-%m-%d"),
                "Employer": employer.strip(),
                "Address1": address1.strip(),
                "Address2": address2.strip(),
                "City": city.strip(),
                "State": state.strip(),
                "Zip": zip_code.strip(),
                "Latitude": latitude.strip(),
                "Longitude": longitude.strip(),
                "Primary NAICS": primary_naics.strip(),
                "Hospitalized": hospitalized,
                "Amputation": amputation,
                "Loss of Eye": loss_of_eye,
                "Inspection": inspection.strip(),
                "FederalState": federal_state,
                "Final Narrative": final_narrative.strip(),
            }

            try:
                with st.spinner(
                    "Loading the model and classifying the incident..."
                ):
                    predictor = load_predictor()

                    prediction = predictor.predict(
                        narrative=incident_details[
                            "Final Narrative"
                        ],
                        include_top_predictions=True,
                        top_k=3,
                    )

                    report_package = generate_report(
                        incident_details,
                        prediction,
                    )

                    save_incident_record(
                        report_package
                    )

                st.session_state.manual_result = prediction
                st.session_state.manual_report_package = report_package

            except Exception as error:
                st.exception(error)

    if (
        st.session_state.manual_result is not None
        and st.session_state.manual_report_package is not None
    ):
        render_prediction_results(
            st.session_state.manual_result,
            st.session_state.manual_report_package,
        )

        if st.button(
            "Start New Manual Report",
            use_container_width=True,
        ):
            st.session_state.manual_result = None
            st.session_state.manual_report_package = None
            st.rerun()
