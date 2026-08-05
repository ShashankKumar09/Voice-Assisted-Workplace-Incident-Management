"""
Batch upload validation engine.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd


YES_VALUES = {
    "yes",
    "y",
    "1",
    "true",
}

NO_VALUES = {
    "no",
    "n",
    "0",
    "false",
}


def _safe_string(value: Any) -> str:

    if value is None:

        return ""

    try:

        if pd.isna(value):

            return ""

    except Exception:

        pass

    return str(value).strip()


def _normalize_column_name(
    column_name: Any,
) -> str:

    return (
        str(column_name)
        .strip()
        .lower()
        .replace("_", " ")
        .replace("-", " ")
    )


def _normalize_yes_no(
    value: Any,
) -> str | None:

    normalized = _safe_string(
        value
    ).lower()

    if normalized in YES_VALUES:

        return "Yes"

    if normalized in NO_VALUES:

        return "No"

    return None


class BatchValidator:
    """Validate and standardize an uploaded incident batch."""

    def __init__(
        self,
        application_root: str | Path,
    ) -> None:

        self.application_root = Path(
            application_root
        ).resolve()

        schema_path = (
            self.application_root
            / "batch"
            / "batch_input_schema.json"
        )

        if not schema_path.is_file():

            raise FileNotFoundError(
                f"Batch schema was not found:\n{schema_path}"
            )

        with schema_path.open(
            "r",
            encoding="utf-8",
        ) as file:

            self.schema = json.load(
                file
            )

        self.required_columns = list(
            self.schema[
                "required_columns"
            ]
        )

        self.yes_no_columns = list(
            self.schema[
                "yes_no_columns"
            ]
        )

        self.maximum_records = int(
            self.schema[
                "maximum_batch_records"
            ]
        )

        self.minimum_narrative_characters = 15
        self.minimum_narrative_words = 4

    def validate(
        self,
        dataframe: pd.DataFrame,
    ) -> Dict[str, Any]:

        if not isinstance(
            dataframe,
            pd.DataFrame,
        ):

            raise TypeError(
                "Uploaded batch must be a pandas DataFrame."
            )

        original_df = dataframe.copy()

        file_errors = []
        file_warnings = []

        if original_df.empty:

            return {
                "status":
                    "failed",

                "is_valid":
                    False,

                "validated_dataframe":
                    original_df,

                "row_validation_results":
                    pd.DataFrame(),

                "file_level_errors": [
                    "The uploaded file does not contain any incident records."
                ],

                "file_level_warnings":
                    [],
            }

        total_records = len(
            original_df
        )

        if total_records > self.maximum_records:

            file_errors.append(
                f"The file contains {total_records:,} records. "
                f"The maximum supported batch size is "
                f"{self.maximum_records:,}."
            )

        uploaded_lookup = {
            _normalize_column_name(column):
                column
            for column in original_df.columns
        }

        required_lookup = {
            _normalize_column_name(column):
                column
            for column in self.required_columns
        }

        missing_columns = [
            required_column
            for normalized_name, required_column
            in required_lookup.items()
            if normalized_name
            not in uploaded_lookup
        ]

        extra_columns = [
            column
            for column in original_df.columns
            if _normalize_column_name(
                column
            )
            not in required_lookup
        ]

        if missing_columns:

            file_errors.append(
                "Missing required columns: "
                + ", ".join(
                    missing_columns
                )
            )

        if extra_columns:

            file_warnings.append(
                "Additional columns will be preserved: "
                + ", ".join(
                    extra_columns
                )
            )

        if missing_columns:

            return {
                "status":
                    "failed",

                "is_valid":
                    False,

                "validated_dataframe":
                    original_df,

                "row_validation_results":
                    pd.DataFrame(),

                "file_level_errors":
                    file_errors,

                "file_level_warnings":
                    file_warnings,
            }

        rename_map = {
            uploaded_lookup[
                normalized_name
            ]:
                required_column
            for normalized_name, required_column
            in required_lookup.items()
        }

        validated_df = original_df.rename(
            columns=rename_map
        ).copy()

        ordered_columns = (
            self.required_columns
            + [
                column
                for column in validated_df.columns
                if column
                not in self.required_columns
            ]
        )

        validated_df = validated_df[
            ordered_columns
        ]

        seen_ids = {}
        validation_rows = []

        for row_number, (
            dataframe_index,
            row,
        ) in enumerate(
            validated_df.iterrows(),
            start=1,
        ):

            errors = []
            warnings = []

            incident_id = _safe_string(
                row["ID"]
            )

            narrative = _safe_string(
                row["Final Narrative"]
            )

            if not incident_id:

                errors.append(
                    "ID is required."
                )

            else:

                normalized_id = (
                    incident_id.lower()
                )

                if normalized_id in seen_ids:

                    errors.append(
                        "Duplicate ID detected. "
                        f"The same ID appears in row "
                        f"{seen_ids[normalized_id]}."
                    )

                else:

                    seen_ids[
                        normalized_id
                    ] = row_number

            if not narrative:

                errors.append(
                    "Final Narrative is required for classification."
                )

            else:

                if (
                    len(narrative)
                    < self.minimum_narrative_characters
                ):

                    errors.append(
                        "Final Narrative is too short. "
                        f"Provide at least "
                        f"{self.minimum_narrative_characters} characters."
                    )

                elif (
                    len(
                        narrative.split()
                    )
                    < self.minimum_narrative_words
                ):

                    errors.append(
                        "Final Narrative is not descriptive enough. "
                        f"Provide at least "
                        f"{self.minimum_narrative_words} words."
                    )

            event_date_text = _safe_string(
                row["EventDate"]
            )

            if event_date_text:

                event_date = pd.to_datetime(
                    event_date_text,
                    errors="coerce",
                )

                if pd.isna(
                    event_date
                ):

                    errors.append(
                        "EventDate is invalid. "
                        "Use a recognized date such as YYYY-MM-DD."
                    )

                else:

                    validated_df.at[
                        dataframe_index,
                        "EventDate"
                    ] = event_date.strftime(
                        "%Y-%m-%d"
                    )

            else:

                warnings.append(
                    "EventDate is empty."
                )

            for coordinate_column, minimum, maximum in [
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

                coordinate_text = _safe_string(
                    row[
                        coordinate_column
                    ]
                )

                if coordinate_text:

                    coordinate_value = pd.to_numeric(
                        coordinate_text,
                        errors="coerce",
                    )

                    if pd.isna(
                        coordinate_value
                    ):

                        errors.append(
                            f"{coordinate_column} must be numeric."
                        )

                    elif not (
                        minimum
                        <= float(
                            coordinate_value
                        )
                        <= maximum
                    ):

                        errors.append(
                            f"{coordinate_column} must be between "
                            f"{minimum:g} and {maximum:g}."
                        )

                    else:

                        validated_df.at[
                            dataframe_index,
                            coordinate_column
                        ] = float(
                            coordinate_value
                        )

            for column in self.yes_no_columns:

                value_text = _safe_string(
                    row[column]
                )

                if not value_text:

                    warnings.append(
                        f"{column} is empty."
                    )

                    continue

                normalized_yes_no = _normalize_yes_no(
                    row[column]
                )

                if normalized_yes_no is None:

                    errors.append(
                        f"{column} must contain Yes or No."
                    )

                else:

                    validated_df.at[
                        dataframe_index,
                        column
                    ] = normalized_yes_no

            federal_state = _safe_string(
                row["FederalState"]
            )

            if federal_state:

                normalized_federal_state = (
                    federal_state.lower()
                )

                if normalized_federal_state not in {
                    "federal",
                    "state",
                }:

                    errors.append(
                        "FederalState must contain Federal or State."
                    )

                else:

                    validated_df.at[
                        dataframe_index,
                        "FederalState"
                    ] = (
                        normalized_federal_state.title()
                    )

            else:

                warnings.append(
                    "FederalState is empty."
                )

            validated_df.at[
                dataframe_index,
                "ID"
            ] = incident_id

            validated_df.at[
                dataframe_index,
                "Final Narrative"
            ] = narrative

            validation_rows.append({
                "Row Number":
                    row_number,

                "DataFrame Index":
                    dataframe_index,

                "ID":
                    incident_id,

                "Validation Status":
                    (
                        "Ready for Classification"
                        if not errors
                        else "Validation Failed"
                    ),

                "Error Count":
                    len(errors),

                "Warning Count":
                    len(warnings),

                "Validation Errors":
                    " | ".join(
                        errors
                    ),

                "Validation Warnings":
                    " | ".join(
                        warnings
                    ),
            })

        row_results = pd.DataFrame(
            validation_rows
        )

        result_index = row_results.set_index(
            "DataFrame Index"
        )

        validated_df[
            "Validation Status"
        ] = validated_df.index.map(
            result_index[
                "Validation Status"
            ]
        )

        validated_df[
            "Validation Errors"
        ] = validated_df.index.map(
            result_index[
                "Validation Errors"
            ]
        )

        validated_df[
            "Validation Warnings"
        ] = validated_df.index.map(
            result_index[
                "Validation Warnings"
            ]
        )

        ready_records = int(
            row_results[
                "Validation Status"
            ].eq(
                "Ready for Classification"
            ).sum()
        )

        failed_records = (
            total_records
            - ready_records
        )

        if (
            not file_errors
            and ready_records == total_records
        ):

            status = "ready"

        elif (
            not file_errors
            and ready_records > 0
        ):

            status = "partially_ready"

        else:

            status = "failed"

        return {
            "status":
                status,

            "is_valid":
                (
                    not file_errors
                    and ready_records > 0
                ),

            "validated_dataframe":
                validated_df,

            "row_validation_results":
                row_results,

            "file_level_errors":
                file_errors,

            "file_level_warnings":
                file_warnings,

            "ready_records":
                ready_records,

            "failed_records":
                failed_records,
        }


def load_uploaded_batch(
    uploaded_file,
) -> pd.DataFrame:
    """Read a CSV or Excel upload."""

    filename = str(
        uploaded_file.name
    ).lower()

    if filename.endswith(
        ".csv"
    ):

        return pd.read_csv(
            uploaded_file,
            low_memory=False,
        )

    if filename.endswith(
        ".xlsx"
    ):

        return pd.read_excel(
            uploaded_file,
            engine="openpyxl",
        )

    raise ValueError(
        "Unsupported file format. Upload a CSV or XLSX file."
    )
