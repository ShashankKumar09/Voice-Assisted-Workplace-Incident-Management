"""Batch Incident Processing page."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Dict, Any

import pandas as pd
import streamlit as st

from batch.classifier import BatchClassifier
from batch.validator import BatchValidator, load_uploaded_batch
from ui.guide_components import (
    render_module_header,
    render_section_header,
    render_user_guide,
)
from views.manual_report import load_predictor


APP_ROOT = Path(__file__).resolve().parents[1]
INCIDENT_DATA_PATH = APP_ROOT / "data" / "incident_records.csv"
TEMPLATE_COLUMNS = [
    "ID", "UPA", "EventDate", "Employer", "Address1", "Address2",
    "City", "State", "Zip", "Latitude", "Longitude", "Primary NAICS",
    "Hospitalized", "Amputation", "Loss of Eye", "Inspection",
    "FederalState", "Final Narrative",
]


def _template_dataframe() -> pd.DataFrame:
    """Return an empty official template containing headers only."""
    return pd.DataFrame(columns=TEMPLATE_COLUMNS)


def _excel_template_bytes() -> bytes:
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        _template_dataframe().to_excel(
            writer,
            sheet_name="Incident Template",
            index=False,
        )
    return buffer.getvalue()


def _save_batch_records(result: Dict[str, Any]) -> int:
    """Save successfully classified batch rows to the shared analytics store.

    Existing records with the same non-empty Incident ID are replaced, preventing
    duplicate dashboard entries when the same batch is processed more than once.
    """
    output_df = result.get("output_dataframe", pd.DataFrame()).copy()
    if output_df.empty:
        return 0

    # A classified row has a completed decision and at least one mapped title.
    decision_mask = (
        output_df.get("Decision", pd.Series("", index=output_df.index))
        .fillna("")
        .astype(str)
        .str.strip()
        .ne("")
    )
    title_columns = [
        column
        for column in [
            "NatureTitle",
            "Part of Body Title",
            "EventTitle",
            "SourceTitle",
        ]
        if column in output_df.columns
    ]
    if title_columns:
        title_mask = output_df[title_columns].fillna("").astype(str).apply(
            lambda row: any(value.strip() for value in row), axis=1
        )
        save_df = output_df.loc[decision_mask & title_mask].copy()
    else:
        save_df = output_df.loc[decision_mask].copy()

    if save_df.empty:
        return 0

    INCIDENT_DATA_PATH.parent.mkdir(parents=True, exist_ok=True)
    if INCIDENT_DATA_PATH.is_file():
        try:
            existing_df = pd.read_csv(INCIDENT_DATA_PATH, low_memory=False)
        except Exception:
            existing_df = pd.DataFrame()
    else:
        existing_df = pd.DataFrame()

    if "ID" in save_df.columns:
        save_df["ID"] = save_df["ID"].fillna("").astype(str).str.strip()
        non_empty_ids = set(save_df.loc[save_df["ID"].ne(""), "ID"])
        if (
            not existing_df.empty
            and "ID" in existing_df.columns
            and non_empty_ids
        ):
            existing_ids = existing_df["ID"].fillna("").astype(str).str.strip()
            existing_df = existing_df.loc[~existing_ids.isin(non_empty_ids)].copy()

    combined_df = pd.concat(
        [existing_df, save_df],
        ignore_index=True,
        sort=False,
    )
    combined_df.to_csv(INCIDENT_DATA_PATH, index=False)
    return len(save_df)


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
            "Yes/No fields are validated automatically. Successfully classified "
            "records are also added to Safety Analytics."
        ),
    )

    render_section_header(
        "1",
        "Download OSHA Batch Template",
        "Download the official blank template before preparing incident records.",
        "⬇️",
    )
    c1, c2 = st.columns(2, gap="medium")
    with c1:
        st.download_button(
            "Download CSV Template",
            data=_template_dataframe().to_csv(index=False).encode("utf-8-sig"),
            file_name="osha_batch_template.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with c2:
        st.download_button(
            "Download Excel Template",
            data=_excel_template_bytes(),
            file_name="osha_batch_template.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )

    render_section_header(
        "2",
        "Upload and Validate Batch File",
        "Upload a completed CSV or Excel file. Every row is checked before classification.",
        "📤",
    )
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
    summary_cols = st.columns(3, gap="medium")
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

    render_section_header(
        "3",
        "Run Multi-Task Classification",
        "Classify every eligible narrative and generate OSHA/OIICS codes, titles and confidence scores.",
        "⚙️",
    )
    st.caption(
        "Output columns include Nature, NatureTitle, Part of Body, Event, Source, "
        "confidence scores and Decision. Successfully classified rows will be "
        "available in Safety Analytics."
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
                saved_records = _save_batch_records(result)
                result["analytics_saved_records"] = saved_records
            st.session_state.batch_result = result
        except Exception as error:
            st.exception(error)

    result = st.session_state.get("batch_result")
    if not result:
        return

    render_section_header(
        "4",
        "Review and Export Results",
        "Review the processing summary and download completed OSHA/OIICS results.",
        "📊",
    )
    output_df = result["output_dataframe"]
    processing_summary = result["processing_summary"]

    if result["status"] == "completed":
        st.success("All uploaded records were classified successfully.")
    elif result["status"] == "partially_completed":
        st.warning("The batch completed with some validation or classification failures.")
    else:
        st.error("The batch could not be classified.")

    saved_records = int(result.get("analytics_saved_records", 0))
    if saved_records:
        st.success(
            f"{saved_records} classified batch record(s) were added to Safety Analytics."
        )
    else:
        st.info("No new classified records were added to Safety Analytics.")

    st.dataframe(processing_summary, use_container_width=True, hide_index=True)
    st.dataframe(output_df, use_container_width=True, hide_index=True)

    d1, d2 = st.columns(2, gap="medium")
    with d1:
        st.download_button(
            "Download Classified CSV",
            data=result["csv_bytes"],
            file_name="osha_batch_classified.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Download Classified Excel",
            data=result["excel_bytes"],
            file_name="osha_batch_classified.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
