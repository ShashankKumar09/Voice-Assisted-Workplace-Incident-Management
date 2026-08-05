"""
Batch classification and export engine.
"""

from __future__ import annotations

import io
import time
from pathlib import Path
from typing import Any, Dict

import numpy as np
import pandas as pd

from batch.validator import BatchValidator
from core.predictor import IncidentPredictor


PREDICTION_COLUMNS = [
    "Nature Predicted Label",
    "Nature Label ID",
    "Nature Confidence (%)",
    "Body Predicted Label",
    "Body Label ID",
    "Body Confidence (%)",
    "Event Predicted Label",
    "Event Label ID",
    "Event Confidence (%)",
    "Source Predicted Label",
    "Source Label ID",
    "Source Confidence (%)",
    "Geometric Mean Confidence (%)",
    "Minimum Task Confidence (%)",
    "Mean Task Confidence (%)",
    "Decision",
    "Historical Validation Status",
    "Historical Score",
    "Weakest Historical Relationship",
    "Weakest Historical Relationship Score",
    "Token Count",
    "Narrative Truncated",
    "Inference Time (ms)",
    "Processing Status",
    "Processing Error",
]


def flatten_prediction(
    prediction_result: Dict[str, Any],
) -> Dict[str, Any]:

    predictions = prediction_result[
        "predictions"
    ]

    confidence = prediction_result[
        "incident_confidence"
    ]

    historical = prediction_result[
        "relationship_validation"
    ]

    return {
        "Nature Predicted Label":
            predictions["nature"]["label"],

        "Nature Label ID":
            predictions["nature"]["label_id"],

        "Nature Confidence (%)":
            round(
                predictions["nature"][
                    "confidence_percent"
                ],
                4,
            ),

        "Body Predicted Label":
            predictions["body"]["label"],

        "Body Label ID":
            predictions["body"]["label_id"],

        "Body Confidence (%)":
            round(
                predictions["body"][
                    "confidence_percent"
                ],
                4,
            ),

        "Event Predicted Label":
            predictions["event"]["label"],

        "Event Label ID":
            predictions["event"]["label_id"],

        "Event Confidence (%)":
            round(
                predictions["event"][
                    "confidence_percent"
                ],
                4,
            ),

        "Source Predicted Label":
            predictions["source"]["label"],

        "Source Label ID":
            predictions["source"]["label_id"],

        "Source Confidence (%)":
            round(
                predictions["source"][
                    "confidence_percent"
                ],
                4,
            ),

        "Geometric Mean Confidence (%)":
            round(
                confidence[
                    "geometric_mean_percent"
                ],
                4,
            ),

        "Minimum Task Confidence (%)":
            round(
                confidence[
                    "minimum_task_confidence_percent"
                ],
                4,
            ),

        "Mean Task Confidence (%)":
            round(
                confidence[
                    "mean_task_confidence_percent"
                ],
                4,
            ),

        "Decision":
            prediction_result[
                "decision"
            ]["tier"],

        "Historical Validation Status":
            historical[
                "historical_validation_status"
            ],

        "Historical Score":
            round(
                historical[
                    "consistency_score"
                ],
                6,
            ),

        "Weakest Historical Relationship":
            historical[
                "weakest_relationship"
            ],

        "Weakest Historical Relationship Score":
            round(
                historical[
                    "weakest_relationship_score"
                ],
                6,
            ),

        "Token Count":
            prediction_result[
                "token_count"
            ],

        "Narrative Truncated":
            prediction_result[
                "was_truncated"
            ],

        "Inference Time (ms)":
            round(
                prediction_result[
                    "inference_time_ms"
                ],
                2,
            ),

        "Processing Status":
            "Classified Successfully",

        "Processing Error":
            "",
    }


class BatchClassifier:
    """Validate, classify and export incident batches."""

    def __init__(
        self,
        predictor: IncidentPredictor,
        validator: BatchValidator,
    ) -> None:

        self.predictor = predictor
        self.validator = validator

    def classify(
        self,
        dataframe: pd.DataFrame,
        continue_on_error: bool = True,
    ) -> Dict[str, Any]:

        batch_start = time.perf_counter()

        validation_result = self.validator.validate(
            dataframe
        )

        output_df = validation_result[
            "validated_dataframe"
        ].copy()

        if output_df.empty:

            return {
                "status":
                    "failed",

                "output_dataframe":
                    output_df,

                "validation_result":
                    validation_result,

                "processing_summary":
                    pd.DataFrame(),

                "csv_bytes":
                    b"",

                "excel_bytes":
                    b"",
            }

        text_columns = [
            column
            for column in PREDICTION_COLUMNS
            if column in {
                "Nature Predicted Label",
                "Body Predicted Label",
                "Event Predicted Label",
                "Source Predicted Label",
                "Decision",
                "Historical Validation Status",
                "Weakest Historical Relationship",
                "Processing Status",
                "Processing Error",
            }
        ]

        boolean_columns = [
            "Narrative Truncated"
        ]

        numeric_columns = [
            column
            for column in PREDICTION_COLUMNS
            if (
                column not in text_columns
                and column not in boolean_columns
            )
        ]

        for column in text_columns:

            output_df[column] = ""

        for column in numeric_columns:

            output_df[column] = np.nan

        for column in boolean_columns:

            output_df[column] = False

        ready_mask = output_df[
            "Validation Status"
        ].eq(
            "Ready for Classification"
        )

        invalid_mask = ~ready_mask

        output_df.loc[
            invalid_mask,
            "Processing Status"
        ] = (
            "Not Classified - Validation Failed"
        )

        output_df.loc[
            invalid_mask,
            "Processing Error"
        ] = output_df.loc[
            invalid_mask,
            "Validation Errors"
        ].fillna("")

        for dataframe_index in output_df.index[
            ready_mask
        ]:

            narrative = str(
                output_df.at[
                    dataframe_index,
                    "Final Narrative"
                ]
            ).strip()

            try:

                prediction_result = self.predictor.predict(
                    narrative=narrative,
                    include_top_predictions=False,
                    top_k=1,
                )

                flattened = flatten_prediction(
                    prediction_result
                )

                for column, value in flattened.items():

                    output_df.at[
                        dataframe_index,
                        column
                    ] = value

            except Exception as error:

                output_df.at[
                    dataframe_index,
                    "Processing Status"
                ] = "Classification Failed"

                output_df.at[
                    dataframe_index,
                    "Processing Error"
                ] = str(error)

                if not continue_on_error:

                    raise

        classified_mask = output_df[
            "Processing Status"
        ].eq(
            "Classified Successfully"
        )

        classified_records = int(
            classified_mask.sum()
        )

        validation_failed_records = int(
            output_df[
                "Processing Status"
            ].eq(
                "Not Classified - Validation Failed"
            ).sum()
        )

        classification_failed_records = int(
            output_df[
                "Processing Status"
            ].eq(
                "Classification Failed"
            ).sum()
        )

        summary = pd.DataFrame({
            "Metric": [
                "Uploaded Records",
                "Ready for Classification",
                "Validation Failed",
                "Classified Successfully",
                "Classification Failed",
                "Auto Fill",
                "Suggest Review",
                "Manual Review",
                "Average Overall Confidence (%)",
                "Total Processing Time (seconds)",
            ],

            "Value": [
                len(output_df),
                int(
                    ready_mask.sum()
                ),
                validation_failed_records,
                classified_records,
                classification_failed_records,
                int(
                    output_df[
                        "Decision"
                    ].eq(
                        "Auto Fill"
                    ).sum()
                ),
                int(
                    output_df[
                        "Decision"
                    ].eq(
                        "Suggest Review"
                    ).sum()
                ),
                int(
                    output_df[
                        "Decision"
                    ].eq(
                        "Manual Review"
                    ).sum()
                ),
                (
                    round(
                        float(
                            output_df.loc[
                                classified_mask,
                                "Geometric Mean Confidence (%)"
                            ].mean()
                        ),
                        4,
                    )
                    if classified_records
                    else np.nan
                ),
                round(
                    time.perf_counter()
                    - batch_start,
                    2,
                ),
            ],
        })

        csv_bytes = output_df.to_csv(
            index=False
        ).encode(
            "utf-8-sig"
        )

        excel_buffer = io.BytesIO()

        with pd.ExcelWriter(
            excel_buffer,
            engine="openpyxl",
        ) as writer:

            output_df.to_excel(
                writer,
                sheet_name="Classified Incidents",
                index=False,
            )

            summary.to_excel(
                writer,
                sheet_name="Processing Summary",
                index=False,
            )

            validation_result[
                "row_validation_results"
            ].to_excel(
                writer,
                sheet_name="Validation Details",
                index=False,
            )

        if classified_records == len(
            output_df
        ):

            status = "completed"

        elif classified_records > 0:

            status = "partially_completed"

        else:

            status = "failed"

        return {
            "status":
                status,

            "output_dataframe":
                output_df,

            "validation_result":
                validation_result,

            "processing_summary":
                summary,

            "classified_records":
                classified_records,

            "validation_failed_records":
                validation_failed_records,

            "classification_failed_records":
                classification_failed_records,

            "csv_bytes":
                csv_bytes,

            "excel_bytes":
                excel_buffer.getvalue(),
        }
