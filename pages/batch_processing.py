"""
Professional Batch Incident Processing module.
"""

from __future__ import annotations

from html import escape
from pathlib import Path
from typing import Any, Callable, Dict

import pandas as pd
import streamlit as st

from batch.classifier import (
    BatchClassifier
)

from batch.validator import (
    BatchValidator,
    load_uploaded_batch
)


def initialize_batch_state() -> None:

    defaults = {
        "batch_uploaded_dataframe":
            None,

        "batch_validation_result":
            None,

        "batch_classification_result":
            None,

        "batch_saved_to_store":
            False,

        "batch_uploaded_filename":
            None,
    }

    for key, value in defaults.items():

        if key not in st.session_state:

            st.session_state[
                key
            ] = value


def reset_batch_workflow() -> None:

    keys = [
        "batch_uploaded_dataframe",
        "batch_validation_result",
        "batch_classification_result",
        "batch_saved_to_store",
        "batch_uploaded_filename",
    ]

    for key in keys:

        st.session_state.pop(
            key,
            None,
        )

    initialize_batch_state()


def save_batch_to_incident_store(
    incident_data_path: Path,
    classification_result: Dict[str, Any],
) -> None:

    classified_df = classification_result[
        "output_dataframe"
    ].copy()

    successful_df = classified_df[
        classified_df[
            "Processing Status"
        ].eq(
            "Classified Successfully"
        )
    ].copy()

    if successful_df.empty:

        return

    successful_df[
        "Reporting Channel"
    ] = "Batch Incident Processing"

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

    if (
        not existing_df.empty
        and "ID" in existing_df.columns
        and "ID" in successful_df.columns
    ):

        incoming_ids = set(
            successful_df[
                "ID"
            ].astype(
                str
            ).str.strip()
        )

        existing_df = existing_df[
            ~existing_df[
                "ID"
            ].astype(
                str
            ).str.strip()
            .isin(
                incoming_ids
            )
        ]

    combined_df = pd.concat(
        [
            existing_df,
            successful_df,
        ],
        ignore_index=True,
        sort=False,
    )

    combined_df.to_csv(
        incident_data_path,
        index=False,
    )


def render_batch_header() -> None:

    st.markdown(
        """
        <div class="hero-shell"
             style="padding:2.4rem 2.6rem">

            <div class="hero-eyebrow">
                Multi-Record Incident Processing
            </div>

            <div class="hero-title"
                 style="font-size:2.65rem">
                📂 Batch Incident Processing
            </div>

            <div class="hero-subtitle">
                Download the official template, upload completed
                CSV or Excel records, validate every row, classify
                valid incidents and export the completed results.
            </div>

            <div class="hero-pill-row">

                <div class="hero-pill">
                    CSV and Excel templates
                </div>

                <div class="hero-pill">
                    Row-level validation
                </div>

                <div class="hero-pill">
                    Partial batch processing
                </div>

                <div class="hero-pill">
                    CSV and Excel exports
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_template_downloads(
    application_root: Path,
) -> None:

    st.markdown(
        """
        <div class="section-kicker">
            Step 1
        </div>

        <div class="section-title">
            Download the official batch template
        </div>

        <div class="section-description">
            Use the locked 18-column structure.
            Do not rename or remove the required columns.
        </div>
        """,
        unsafe_allow_html=True,
    )

    csv_template_path = (
        application_root
        / "batch"
        / "workplace_incident_batch_template.csv"
    )

    excel_template_path = (
        application_root
        / "batch"
        / "workplace_incident_batch_template.xlsx"
    )

    example_path = (
        application_root
        / "batch"
        / "workplace_incident_batch_example.csv"
    )

    template_columns = st.columns(
        3,
        gap="medium",
    )

    with template_columns[0]:

        st.download_button(
            "Download CSV Template",
            data=csv_template_path.read_bytes(),
            file_name=csv_template_path.name,
            mime="text/csv",
            use_container_width=True,
        )

    with template_columns[1]:

        st.download_button(
            "Download Excel Template",
            data=excel_template_path.read_bytes(),
            file_name=excel_template_path.name,
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    with template_columns[2]:

        st.download_button(
            "Download Example File",
            data=example_path.read_bytes(),
            file_name=example_path.name,
            mime="text/csv",
            use_container_width=True,
        )

    with st.expander(
        "View required batch columns",
        expanded=False,
    ):

        required_columns = [
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

        columns_df = pd.DataFrame({
            "Position":
                range(
                    1,
                    len(
                        required_columns
                    ) + 1
                ),

            "Required Column":
                required_columns,
        })

        st.dataframe(
            columns_df,
            hide_index=True,
            use_container_width=True,
        )


def render_upload_and_validation(
    application_root: Path,
) -> None:

    st.markdown(
        """
        <div class="section-kicker">
            Step 2
        </div>

        <div class="section-title">
            Upload and validate incident records
        </div>

        <div class="section-description">
            Upload a completed CSV or Excel file.
            The system checks file structure and every
            row before classification begins.
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader(
        "Upload batch incident file",
        type=[
            "csv",
            "xlsx",
        ],
        accept_multiple_files=False,
        help=(
            "Maximum supported batch size: "
            "5,000 incident records."
        ),
    )

    if uploaded_file is not None:

        uploaded_signature = (
            uploaded_file.name,
            uploaded_file.size,
        )

        previous_signature = (
            st.session_state.get(
                "batch_uploaded_signature"
            )
        )

        if (
            uploaded_signature
            != previous_signature
        ):

            try:

                uploaded_df = load_uploaded_batch(
                    uploaded_file
                )

                validator = BatchValidator(
                    application_root=(
                        application_root
                    )
                )

                validation_result = (
                    validator.validate(
                        uploaded_df
                    )
                )

                st.session_state[
                    "batch_uploaded_dataframe"
                ] = uploaded_df

                st.session_state[
                    "batch_validation_result"
                ] = validation_result

                st.session_state[
                    "batch_classification_result"
                ] = None

                st.session_state[
                    "batch_saved_to_store"
                ] = False

                st.session_state[
                    "batch_uploaded_filename"
                ] = uploaded_file.name

                st.session_state[
                    "batch_uploaded_signature"
                ] = uploaded_signature

            except Exception as error:

                st.error(
                    "The uploaded file could not be read. "
                    f"Details: {error}"
                )

                return

    validation_result = st.session_state.get(
        "batch_validation_result"
    )

    if validation_result is None:

        st.markdown(
            """
            <div class="info-panel">
                Upload a CSV or Excel file to begin validation.
                Classification will remain disabled until at least
                one record is ready for processing.
            </div>
            """,
            unsafe_allow_html=True,
        )

        return

    # --------------------------------------------------------------------------
    # File-level validation messages
    # --------------------------------------------------------------------------

    for error in validation_result.get(
        "file_level_errors",
        [],
    ):

        st.error(
            error
        )

    for warning in validation_result.get(
        "file_level_warnings",
        [],
    ):

        st.warning(
            warning
        )

    validated_df = validation_result[
        "validated_dataframe"
    ]

    total_records = len(
        validated_df
    )

    ready_records = int(
        validation_result.get(
            "ready_records",
            0,
        )
    )

    failed_records = int(
        validation_result.get(
            "failed_records",
            total_records,
        )
    )

    readiness_rate = (
        ready_records
        / total_records
        * 100
        if total_records
        else 0
    )

    validation_rows = validation_result[
        "row_validation_results"
    ]

    records_with_warnings = (
        int(
            validation_rows[
                "Warning Count"
            ].gt(
                0
            ).sum()
        )
        if not validation_rows.empty
        else 0
    )

    # --------------------------------------------------------------------------
    # Validation KPI cards
    # --------------------------------------------------------------------------

    kpi_columns = st.columns(
        5,
        gap="medium",
    )

    validation_metrics = [
        (
            "Uploaded Records",
            f"{total_records:,}",
            "Rows detected in the file",
        ),
        (
            "Ready",
            f"{ready_records:,}",
            "Eligible for classification",
        ),
        (
            "Validation Failed",
            f"{failed_records:,}",
            "Rows blocked from classification",
        ),
        (
            "Warnings",
            f"{records_with_warnings:,}",
            "Rows requiring attention",
        ),
        (
            "Readiness Rate",
            f"{readiness_rate:.1f}%",
            "Share ready for classification",
        ),
    ]

    for column, (
        label,
        value,
        caption,
    ) in zip(
        kpi_columns,
        validation_metrics,
    ):

        with column:

            st.markdown(
                f"""
                <div class="kpi-card">

                    <div class="kpi-label">
                        {escape(label)}
                    </div>

                    <div class="kpi-value">
                        {escape(value)}
                    </div>

                    <div class="kpi-caption">
                        {escape(caption)}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "<div style='height:1rem'></div>",
        unsafe_allow_html=True,
    )

    if validation_result[
        "status"
    ] == "ready":

        st.success(
            f"All {ready_records:,} records are "
            "ready for classification."
        )

    elif validation_result[
        "status"
    ] == "partially_ready":

        st.warning(
            f"{ready_records:,} records are ready. "
            f"{failed_records:,} records will remain "
            "unclassified with validation errors."
        )

    else:

        st.error(
            "The batch cannot be classified until "
            "the file-level issues are corrected."
        )

    # --------------------------------------------------------------------------
    # Validation details
    # --------------------------------------------------------------------------

    tab_summary, tab_errors, tab_data = st.tabs([
        "Validation Summary",
        "Failed Records",
        "Uploaded Data",
    ])

    with tab_summary:

        if validation_rows.empty:

            st.info(
                "No row-level validation details are available."
            )

        else:

            st.dataframe(
                validation_rows,
                hide_index=True,
                use_container_width=True,
                height=360,
            )

    with tab_errors:

        if validation_rows.empty:

            st.info(
                "No failed records are available."
            )

        else:

            failed_validation_df = (
                validation_rows[
                    validation_rows[
                        "Validation Status"
                    ].eq(
                        "Validation Failed"
                    )
                ]
            )

            if failed_validation_df.empty:

                st.success(
                    "No row-level validation failures were found."
                )

            else:

                st.dataframe(
                    failed_validation_df,
                    hide_index=True,
                    use_container_width=True,
                    height=360,
                )

    with tab_data:

        st.dataframe(
            validated_df.head(
                200
            ),
            hide_index=True,
            use_container_width=True,
            height=420,
        )

        if len(
            validated_df
        ) > 200:

            st.caption(
                "Preview limited to the first 200 records."
            )


def render_batch_classification(
    application_root: Path,
    predictor_loader: Callable[[], Any],
    incident_data_path: Path,
) -> None:

    validation_result = st.session_state.get(
        "batch_validation_result"
    )

    if validation_result is None:

        return

    ready_records = int(
        validation_result.get(
            "ready_records",
            0,
        )
    )

    st.markdown(
        """
        <div class="section-kicker">
            Step 3
        </div>

        <div class="section-title">
            Classify validated incidents
        </div>

        <div class="section-description">
            Only rows marked Ready for Classification
            will be sent to the model. Invalid rows remain
            in the downloadable output with their errors.
        </div>
        """,
        unsafe_allow_html=True,
    )

    classify_columns = st.columns(
        [1.3, 1, 1],
        gap="medium",
    )

    with classify_columns[0]:

        start_classification = st.button(
            (
                f"Classify {ready_records:,} "
                "Ready Records"
            ),
            type="primary",
            use_container_width=True,
            disabled=(
                ready_records == 0
            ),
        )

    with classify_columns[1]:

        if st.button(
            "Reset Batch",
            use_container_width=True,
        ):

            reset_batch_workflow()
            st.rerun()

    with classify_columns[2]:

        uploaded_name = (
            st.session_state.get(
                "batch_uploaded_filename"
            )
            or "No file uploaded"
        )

        st.markdown(
            f"""
            <div class="info-panel"
                 style="padding:.72rem 1rem">
                <b>Current file:</b><br/>
                {escape(uploaded_name)}
            </div>
            """,
            unsafe_allow_html=True,
        )

    if start_classification:

        with st.spinner(
            "Loading the model and classifying "
            "the validated incident records..."
        ):

            try:

                predictor = (
                    predictor_loader()
                )

                validator = BatchValidator(
                    application_root=(
                        application_root
                    )
                )

                classifier = BatchClassifier(
                    predictor=(
                        predictor
                    ),
                    validator=(
                        validator
                    ),
                )

                classification_result = (
                    classifier.classify(
                        dataframe=(
                            st.session_state[
                                "batch_uploaded_dataframe"
                            ]
                        ),
                        continue_on_error=True,
                    )
                )

                st.session_state[
                    "batch_classification_result"
                ] = classification_result

                if (
                    not st.session_state[
                        "batch_saved_to_store"
                    ]
                ):

                    save_batch_to_incident_store(
                        incident_data_path=(
                            incident_data_path
                        ),
                        classification_result=(
                            classification_result
                        ),
                    )

                    st.session_state[
                        "batch_saved_to_store"
                    ] = True

                st.rerun()

            except Exception as error:

                st.error(
                    "Batch classification failed. "
                    f"Details: {error}"
                )

    classification_result = (
        st.session_state.get(
            "batch_classification_result"
        )
    )

    if classification_result is None:

        return

    # --------------------------------------------------------------------------
    # Classification result
    # --------------------------------------------------------------------------

    if classification_result[
        "status"
    ] == "completed":

        st.success(
            "Batch classification completed successfully."
        )

    elif classification_result[
        "status"
    ] == "partially_completed":

        st.warning(
            "Batch classification partially completed. "
            "Review validation and processing errors."
        )

    else:

        st.error(
            "No incident records were classified."
        )

    summary_df = classification_result[
        "processing_summary"
    ]

    summary_lookup = dict(
        zip(
            summary_df[
                "Metric"
            ],
            summary_df[
                "Value"
            ],
        )
    )

    result_kpis = st.columns(
        5,
        gap="medium",
    )

    result_metrics = [
        (
            "Classified",
            int(
                summary_lookup.get(
                    "Classified Successfully",
                    0,
                )
            ),
        ),
        (
            "Classification Failed",
            int(
                summary_lookup.get(
                    "Classification Failed",
                    0,
                )
            ),
        ),
        (
            "Auto Fill",
            int(
                summary_lookup.get(
                    "Auto Fill",
                    0,
                )
            ),
        ),
        (
            "Suggest Review",
            int(
                summary_lookup.get(
                    "Suggest Review",
                    0,
                )
            ),
        ),
        (
            "Manual Review",
            int(
                summary_lookup.get(
                    "Manual Review",
                    0,
                )
            ),
        ),
    ]

    for column, (
        label,
        value,
    ) in zip(
        result_kpis,
        result_metrics,
    ):

        with column:

            st.markdown(
                f"""
                <div class="kpi-card">

                    <div class="kpi-label">
                        {escape(label)}
                    </div>

                    <div class="kpi-value">
                        {value:,}
                    </div>

                </div>
                """,
                unsafe_allow_html=True,
            )

    st.markdown(
        "<div style='height:1rem'></div>",
        unsafe_allow_html=True,
    )

    result_tabs = st.tabs([
        "Processing Summary",
        "Classification Results",
        "Processing Errors",
    ])

    output_df = classification_result[
        "output_dataframe"
    ]

    with result_tabs[0]:

        st.dataframe(
            summary_df,
            hide_index=True,
            use_container_width=True,
        )

    with result_tabs[1]:

        display_columns = [
            column
            for column in [
                "ID",
                "Employer",
                "EventDate",
                "Final Narrative",
                "Nature Predicted Label",
                "Nature Confidence (%)",
                "Body Predicted Label",
                "Body Confidence (%)",
                "Event Predicted Label",
                "Event Confidence (%)",
                "Source Predicted Label",
                "Source Confidence (%)",
                "Geometric Mean Confidence (%)",
                "Decision",
                "Historical Validation Status",
                "Historical Score",
                "Processing Status",
            ]
            if column in output_df.columns
        ]

        st.dataframe(
            output_df[
                display_columns
            ],
            hide_index=True,
            use_container_width=True,
            height=460,
        )

    with result_tabs[2]:

        failed_processing_df = output_df[
            ~output_df[
                "Processing Status"
            ].eq(
                "Classified Successfully"
            )
        ]

        if failed_processing_df.empty:

            st.success(
                "No validation or classification "
                "failures were found."
            )

        else:

            error_columns = [
                column
                for column in [
                    "ID",
                    "Validation Status",
                    "Validation Errors",
                    "Validation Warnings",
                    "Processing Status",
                    "Processing Error",
                ]
                if column
                in failed_processing_df.columns
            ]

            st.dataframe(
                failed_processing_df[
                    error_columns
                ],
                hide_index=True,
                use_container_width=True,
                height=360,
            )

    # --------------------------------------------------------------------------
    # Download area
    # --------------------------------------------------------------------------

    st.markdown(
        """
        <div class="section-kicker">
            Step 4
        </div>

        <div class="section-title">
            Download classified batch results
        </div>

        <div class="section-description">
            The Excel output contains Classified Incidents,
            Processing Summary and Validation Details sheets.
        </div>
        """,
        unsafe_allow_html=True,
    )

    source_name = (
        st.session_state.get(
            "batch_uploaded_filename"
        )
        or "batch_incidents"
    )

    source_stem = Path(
        source_name
    ).stem

    download_columns = st.columns(
        3,
        gap="medium",
    )

    with download_columns[0]:

        st.download_button(
            "Download Classified CSV",
            data=classification_result[
                "csv_bytes"
            ],
            file_name=(
                f"{source_stem}_classified.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    with download_columns[1]:

        st.download_button(
            "Download Classified Excel",
            data=classification_result[
                "excel_bytes"
            ],
            file_name=(
                f"{source_stem}_classified.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    with download_columns[2]:

        summary_csv_bytes = (
            summary_df.to_csv(
                index=False
            ).encode(
                "utf-8-sig"
            )
        )

        st.download_button(
            "Download Processing Summary",
            data=summary_csv_bytes,
            file_name=(
                f"{source_stem}_processing_summary.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )


def render_batch_processing_page(
    application_root: Path,
    predictor_loader: Callable[[], Any],
    incident_data_path: Path,
) -> None:

    initialize_batch_state()
    render_batch_header()

    render_template_downloads(
        application_root=(
            application_root
        )
    )

    st.markdown(
        "<div style='height:1.8rem'></div>",
        unsafe_allow_html=True,
    )

    render_upload_and_validation(
        application_root=(
            application_root
        )
    )

    st.markdown(
        "<div style='height:1.8rem'></div>",
        unsafe_allow_html=True,
    )

    render_batch_classification(
        application_root=(
            application_root
        ),
        predictor_loader=(
            predictor_loader
        ),
        incident_data_path=(
            incident_data_path
        ),
    )
