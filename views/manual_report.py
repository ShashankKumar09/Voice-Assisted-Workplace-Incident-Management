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


def _decision_display(
    decision_tier: str,
) -> tuple[str, str]:
    if decision_tier == "Auto Fill":
        return "🟢", "#216B58"

    if decision_tier == "Suggest Review":
        return "🟡", "#9A6B00"

    return "🔴", "#A83A3A"


def _historical_display(
    historical_status: str,
) -> tuple[str, str, str]:
    normalized = historical_status.lower()

    if "strong" in normalized:
        return "🟢", "Strong Historical Support", "#216B58"

    if "moderate" in normalized:
        return "🟡", "Moderate Historical Support", "#9A6B00"

    return "🔴", "Limited Historical Support", "#A83A3A"


def _render_prediction_card(
    title: str,
    label: str,
    confidence: float,
) -> None:
    confidence = max(0.0, min(float(confidence), 100.0))

    st.html(
        f"""
        <div style="
            min-height:220px; padding:1.25rem; border-radius:18px;
            border:1px solid #DCE6ED; background:linear-gradient(180deg,#FFFFFF 0%,#F8FBFD 100%);
            box-shadow:0 8px 22px rgba(26,58,79,0.06);
        ">
            <div style="color:#6A7F8F;font-size:.72rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;">
                {title}
            </div>
            <div style="min-height:72px;margin-top:.75rem;color:#17324D;font-size:1.15rem;line-height:1.35;font-weight:800;">
                {label}
            </div>
            <div style="height:9px;margin-top:1rem;border-radius:999px;overflow:hidden;background:#E7EEF2;">
                <div style="width:{confidence:.2f}%;height:100%;border-radius:999px;background:linear-gradient(90deg,#1F6A86,#2B8BA5);"></div>
            </div>
            <div style="display:flex;justify-content:space-between;gap:.5rem;margin-top:.65rem;">
                <span style="color:#2B7897;font-size:.82rem;font-weight:800;">{confidence:.2f}%</span>
                <span style="color:#7C8E9A;font-size:.73rem;">Confidence</span>
            </div>
        </div>
        """
    )


def _render_summary_card(
    label: str,
    value: str,
    caption: str,
    value_color: str = "#17324D",
) -> None:
    st.html(
        f"""
        <div style="
            min-height:148px; padding:1.2rem 1.25rem; border-radius:18px;
            border:1px solid #DCE6ED; background:#FFFFFF;
            box-shadow:0 8px 22px rgba(26,58,79,0.06);
        ">
            <div style="color:#6A7F8F;font-size:.72rem;font-weight:800;letter-spacing:.08em;text-transform:uppercase;">
                {label}
            </div>
            <div style="margin-top:.65rem;color:{value_color};font-size:1.32rem;line-height:1.3;font-weight:850;">
                {value}
            </div>
            <div style="margin-top:.45rem;color:#7C8E9A;font-size:.75rem;line-height:1.45;">
                {caption}
            </div>
        </div>
        """
    )


def render_prediction_results(
    prediction: Dict[str, Any],
    report_package: Dict[str, Any],
) -> None:
    st.success(
        "Classification completed successfully. "
        "Review the predicted categories before downloading the report."
    )

    st.markdown("## Classification Results")

    prediction_columns = st.columns(4, gap="medium")

    task_configuration = [
        ("nature", "Nature"),
        ("body", "Part of Body"),
        ("event", "Event"),
        ("source", "Source"),
    ]

    for column, (task_name, display_name) in zip(
        prediction_columns,
        task_configuration,
    ):
        task_result = _prediction_value(prediction, task_name)

        with column:
            _render_prediction_card(
                title=display_name,
                label=str(task_result["label"]),
                confidence=float(task_result["confidence_percent"]),
            )

    overall_confidence = float(
        prediction["incident_confidence"]["geometric_mean_percent"]
    )

    decision_tier = str(prediction["decision"]["tier"])
    relationship = prediction["relationship_validation"]
    historical_status = str(relationship["historical_validation_status"])

    decision_icon, decision_color = _decision_display(decision_tier)
    historical_icon, historical_label, historical_color = _historical_display(
        historical_status
    )

    st.markdown("")
    st.markdown("### Decision Summary")

    summary_columns = st.columns(3, gap="medium")

    with summary_columns[0]:
        _render_summary_card(
            label="Overall Confidence",
            value=f"{overall_confidence:.2f}%",
            caption="Geometric mean across Nature, Body, Event and Source.",
        )

    with summary_columns[1]:
        _render_summary_card(
            label="Decision Tier",
            value=f"{decision_icon} {decision_tier}",
            caption="Final routing based on the configured confidence thresholds.",
            value_color=decision_color,
        )

    with summary_columns[2]:
        _render_summary_card(
            label="Historical Validation",
            value=f"{historical_icon} {historical_label}",
            caption="Support observed across historical category relationships.",
            value_color=historical_color,
        )

    with st.expander("Historical Validation Details", expanded=False):
        st.info(
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
                    relationship.get("historical_validation_status", ""),
                    relationship.get("consistency_score", ""),
                    relationship.get("weakest_relationship", ""),
                    relationship.get("weakest_relationship_score", ""),
                ],
            }
        )

        st.dataframe(
            details_df,
            hide_index=True,
            use_container_width=True,
        )

    st.markdown("---")
    st.markdown("## Download Completed Report")
    st.caption("Download the classified incident record in PDF or CSV format.")

    download_columns = st.columns(2, gap="medium")

    with download_columns[0]:
        st.download_button(
            "📄 Download PDF Report",
            data=report_package["pdf_bytes"],
            file_name=report_package["pdf_filename"],
            mime="application/pdf",
            use_container_width=True,
        )

    with download_columns[1]:
        st.download_button(
            "📊 Download CSV Record",
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
