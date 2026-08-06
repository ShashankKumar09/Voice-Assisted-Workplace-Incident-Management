"""Batch Incident Processing page."""
from __future__ import annotations

import io
from pathlib import Path

import pandas as pd
import streamlit as st

from batch.classifier import BatchClassifier
from batch.validator import BatchValidator, load_uploaded_batch
from ui.guide_components import render_module_header, render_user_guide
from views.manual_report import load_predictor


APP_ROOT = Path(__file__).resolve().parents[1]
TEMPLATE_COLUMNS = [
    "ID", "UPA", "EventDate", "Employer", "Address1", "Address2",
    "City", "State", "Zip", "Latitude", "Longitude", "Primary NAICS",
    "Hospitalized", "Amputation", "Loss of Eye", "Inspection",
    "FederalState", "Final Narrative",
]


def _template_dataframe() -> pd.DataFrame:
    return pd.DataFrame([
        {
            "ID": "INC-1001",
            "UPA": "UPA-2501",
            "EventDate": "2026-08-06",
            "Employer": "ABC Manufacturing",
            "Address1": "100 Industrial Road",
            "Address2": "",
            "City": "Bengaluru",
            "State": "Karnataka",
            "Zip": "560001",
            "Latitude": "12.9716",
            "Longitude": "77.5946",
            "Primary NAICS": "332710",
            "Hospitalized": "No",
            "Amputation": "No",
            "Loss of Eye": "No",
            "Inspection": "",
            "FederalState": "State",
            "Final Narrative": (
                "An employee slipped on a wet floor, fell on the same level, "
                "and fractured the left ankle."
            ),
        }
    ], columns=TEMPLATE_COLUMNS)


def _excel_template_bytes() -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        _template_dataframe().to_excel(writer, sheet_name="Incident Template", index=False)
    return buffer.getvalue()


def render() -> None:
    render_module_header(
        eyebrow="Bulk Incident Processing",
        title="Batch Incident Processing",
        description=(
            "Upload multiple incident records, validate every row, classify all "
            "eligible narratives and export standardized OSHA/OIICS results."
        ),
        icon="📂",
    )

    render_user_guide(
        title="How to Use Batch Incident Processing",
        steps=[
            ("Download the template", "Use the official CSV or Excel structure."),
            ("Prepare incident records", "Enter one incident per row."),
            ("Upload the file", "Upload a CSV or XLSX file with up to 5,000 rows."),
            ("Review validation", "Correct invalid rows before classification."),
            ("Process and export", "Download standardized CSV or Excel results."),
        ],
        note=(
            "ID and Final Narrative are required. Latitude, Longitude, dates and "
            "Yes/No fields are validated automatically."
        ),
    )

    st.markdown("## 1. Download Batch Template")
    c1, c2 = st.columns(2)
    with c1:
        st.download_button(
            "⬇️ Download CSV Template",
            data=_template_dataframe().to_csv(index=False).encode("utf-8-sig"),
            file_name="osha_batch_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "⬇️ Download Excel Template",
            data=_excel_template_bytes(),
            file_name="osha_batch_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    st.markdown("## 2. Upload and Validate")
    uploaded_file = st.file_uploader(
        "Upload completed batch file",
        type=["csv", "xlsx"],
        help="Maximum 5,000 incident records.",
    )

    if uploaded_file is None:
        st.info("Upload a CSV or XLSX file to begin validation.")
        return

    try:
        uploaded_df = load_uploaded_batch(uploaded_file)
        validator = BatchValidator(APP_ROOT)
        validation = validator.validate(uploaded_df)
    except Exception as error:
        st.exception(error)
        return

    st.caption(f"Uploaded file: {uploaded_file.name}")
    summary_cols = st.columns(3)
    summary_cols[0].metric("Uploaded Records", len(uploaded_df))
    summary_cols[1].metric("Ready", int(validation.get("ready_records", 0)))
    summary_cols[2].metric("Validation Failed", int(validation.get("failed_records", 0)))

    for message in validation.get("file_level_errors", []):
        st.error(message)
    for message in validation.get("file_level_warnings", []):
        st.warning(message)

    row_results = validation.get("row_validation_results", pd.DataFrame())
    if not row_results.empty:
        st.markdown("### Row Validation Results")
        st.dataframe(
            row_results[
                [
                    "Row Number", "ID", "Validation Status", "Error Count",
                    "Warning Count", "Validation Errors", "Validation Warnings",
                ]
            ],
            use_container_width=True,
            hide_index=True,
        )

    if not validation.get("is_valid", False):
        st.error("No records are currently ready for classification.")
        return

    st.markdown("## 3. Classify Eligible Records")
    st.caption(
        "The output uses standard OSHA/OIICS columns: Nature, NatureTitle, "
        "Part of Body, Event, Source, confidence scores and Decision."
    )

    if st.button(
        "Run Batch Classification",
        type="primary",
        use_container_width=True,
    ):
        try:
            with st.spinner("Loading the model and classifying eligible records..."):
                classifier = BatchClassifier(
                    predictor=load_predictor(),
                    validator=validator,
                )
                result = classifier.classify(uploaded_df, continue_on_error=True)
            st.session_state.batch_result = result
        except Exception as error:
            st.exception(error)

    result = st.session_state.get("batch_result")
    if not result:
        return

    st.markdown("## 4. Processing Results")
    output_df = result["output_dataframe"]
    processing_summary = result["processing_summary"]

    if result["status"] == "completed":
        st.success("All uploaded records were classified successfully.")
    elif result["status"] == "partially_completed":
        st.warning("The batch completed with some validation or classification failures.")
    else:
        st.error("The batch could not be classified.")

    st.dataframe(processing_summary, use_container_width=True, hide_index=True)
    st.dataframe(output_df, use_container_width=True, hide_index=True)

    d1, d2 = st.columns(2)
    with d1:
        st.download_button(
            "⬇️ Download Classified CSV",
            data=result["csv_bytes"],
            file_name="osha_batch_classified.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "⬇️ Download Classified Excel",
            data=result["excel_bytes"],
            file_name="osha_batch_classified.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
