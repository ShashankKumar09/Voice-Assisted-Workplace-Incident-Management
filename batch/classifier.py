"""Batch classification and standardized OSHA/OIICS export engine."""
from __future__ import annotations

import io
import time
from typing import Any, Dict

import numpy as np
import pandas as pd

from batch.validator import BatchValidator
from core.osha_codes import enrich_prediction_result
from core.predictor import IncidentPredictor


STANDARD_PREDICTION_COLUMNS = [
    "Nature",
    "NatureTitle",
    "Nature Confidence (%)",
    "Part of Body",
    "Part of Body Title",
    "Part of Body Confidence (%)",
    "Event",
    "EventTitle",
    "Event Confidence (%)",
    "Source",
    "SourceTitle",
    "Source Confidence (%)",
    "Decision",
    "Overall Confidence (%)",
]


def flatten_prediction(prediction_result: Dict[str, Any]) -> Dict[str, Any]:
    """Flatten one prediction using standard OSHA/OIICS output names."""
    prediction_result = enrich_prediction_result(prediction_result)
    predictions = prediction_result["predictions"]

    return {
        "Nature": predictions["nature"].get("code", ""),
        "NatureTitle": predictions["nature"].get(
            "title", predictions["nature"].get("label", "")
        ),
        "Nature Confidence (%)": round(
            float(predictions["nature"]["confidence_percent"]), 4
        ),
        "Part of Body": predictions["body"].get("code", ""),
        "Part of Body Title": predictions["body"].get(
            "title", predictions["body"].get("label", "")
        ),
        "Part of Body Confidence (%)": round(
            float(predictions["body"]["confidence_percent"]), 4
        ),
        "Event": predictions["event"].get("code", ""),
        "EventTitle": predictions["event"].get(
            "title", predictions["event"].get("label", "")
        ),
        "Event Confidence (%)": round(
            float(predictions["event"]["confidence_percent"]), 4
        ),
        "Source": predictions["source"].get("code", ""),
        "SourceTitle": predictions["source"].get(
            "title", predictions["source"].get("label", "")
        ),
        "Source Confidence (%)": round(
            float(predictions["source"]["confidence_percent"]), 4
        ),
        "Decision": prediction_result["decision"]["tier"],
        "Overall Confidence (%)": round(
            float(
                prediction_result["incident_confidence"][
                    "geometric_mean_percent"
                ]
            ),
            4,
        ),
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
        validation_result = self.validator.validate(dataframe)
        working_df = validation_result["validated_dataframe"].copy()

        if working_df.empty:
            return {
                "status": "failed",
                "output_dataframe": working_df,
                "validation_result": validation_result,
                "processing_summary": pd.DataFrame(),
                "csv_bytes": b"",
                "excel_bytes": b"",
            }

        for column in STANDARD_PREDICTION_COLUMNS:
            if column in {
                "NatureTitle",
                "Part of Body Title",
                "EventTitle",
                "SourceTitle",
                "Decision",
            }:
                working_df[column] = ""
            else:
                working_df[column] = np.nan

        working_df["_Processing Status"] = ""
        working_df["_Processing Error"] = ""

        ready_mask = working_df["Validation Status"].eq(
            "Ready for Classification"
        )
        invalid_mask = ~ready_mask
        working_df.loc[invalid_mask, "_Processing Status"] = (
            "Not Classified - Validation Failed"
        )
        working_df.loc[invalid_mask, "_Processing Error"] = working_df.loc[
            invalid_mask, "Validation Errors"
        ].fillna("")

        for dataframe_index in working_df.index[ready_mask]:
            narrative = str(
                working_df.at[dataframe_index, "Final Narrative"]
            ).strip()
            try:
                prediction_result = self.predictor.predict(
                    narrative=narrative,
                    include_top_predictions=False,
                    top_k=1,
                )
                flattened = flatten_prediction(prediction_result)
                for column, value in flattened.items():
                    working_df.at[dataframe_index, column] = value
                working_df.at[dataframe_index, "_Processing Status"] = (
                    "Classified Successfully"
                )
            except Exception as error:
                working_df.at[dataframe_index, "_Processing Status"] = (
                    "Classification Failed"
                )
                working_df.at[dataframe_index, "_Processing Error"] = str(error)
                if not continue_on_error:
                    raise

        classified_mask = working_df["_Processing Status"].eq(
            "Classified Successfully"
        )
        classified_records = int(classified_mask.sum())
        validation_failed_records = int(
            working_df["_Processing Status"]
            .eq("Not Classified - Validation Failed")
            .sum()
        )
        classification_failed_records = int(
            working_df["_Processing Status"]
            .eq("Classification Failed")
            .sum()
        )

        summary = pd.DataFrame(
            {
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
                    len(working_df),
                    int(ready_mask.sum()),
                    validation_failed_records,
                    classified_records,
                    classification_failed_records,
                    int(working_df["Decision"].eq("Auto Fill").sum()),
                    int(working_df["Decision"].eq("Suggest Review").sum()),
                    int(working_df["Decision"].eq("Manual Review").sum()),
                    (
                        round(
                            float(
                                working_df.loc[
                                    classified_mask,
                                    "Overall Confidence (%)",
                                ].mean()
                            ),
                            4,
                        )
                        if classified_records
                        else np.nan
                    ),
                    round(time.perf_counter() - batch_start, 2),
                ],
            }
        )

        internal_columns = {
            "Validation Status",
            "Validation Errors",
            "Validation Warnings",
            "_Processing Status",
            "_Processing Error",
        }
        original_columns = [
            column
            for column in dataframe.columns
            if column not in STANDARD_PREDICTION_COLUMNS
        ]
        export_columns = [
            column
            for column in original_columns + STANDARD_PREDICTION_COLUMNS
            if column in working_df.columns and column not in internal_columns
        ]
        export_columns = list(dict.fromkeys(export_columns))
        output_df = working_df.loc[:, export_columns].copy()

        csv_bytes = output_df.to_csv(index=False).encode("utf-8-sig")
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
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

        if classified_records == len(working_df):
            status = "completed"
        elif classified_records > 0:
            status = "partially_completed"
        else:
            status = "failed"

        return {
            "status": status,
            "output_dataframe": output_df,
            "validation_result": validation_result,
            "processing_summary": summary,
            "classified_records": classified_records,
            "validation_failed_records": validation_failed_records,
            "classification_failed_records": classification_failed_records,
            "csv_bytes": csv_bytes,
            "excel_bytes": excel_buffer.getvalue(),
        }
