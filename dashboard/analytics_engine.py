"""
Reusable analytics and dashboard-export engine.
"""

from __future__ import annotations

import io
from datetime import datetime
from typing import Any, Dict, List

import numpy as np
import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)


DECISION_ORDER = [
    "Auto Fill",
    "Suggest Review",
    "Manual Review",
]

HISTORICAL_ORDER = [
    "Strong Historical Support",
    "Moderate Historical Support",
    "Limited Historical Support",
]


def clean_dashboard_dataframe(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Standardize dashboard fields without changing source values.
    """

    dashboard_df = dataframe.copy()

    if dashboard_df.empty:

        return dashboard_df

    text_columns = [
        "ID",
        "Employer",
        "City",
        "State",
        "Nature Predicted Label",
        "Body Predicted Label",
        "Event Predicted Label",
        "Source Predicted Label",
        "Decision",
        "Historical Validation Status",
        "Reporting Channel",
        "Processing Status",
    ]

    for column in text_columns:

        if column not in dashboard_df.columns:

            dashboard_df[column] = ""

        dashboard_df[column] = (
            dashboard_df[column]
            .fillna("")
            .astype(str)
            .str.strip()
        )

    if "EventDate" not in dashboard_df.columns:

        dashboard_df["EventDate"] = pd.NaT

    dashboard_df[
        "EventDate Parsed"
    ] = pd.to_datetime(
        dashboard_df["EventDate"],
        errors="coerce",
    )

    dashboard_df[
        "Year"
    ] = dashboard_df[
        "EventDate Parsed"
    ].dt.year.astype(
        "Int64"
    )

    dashboard_df[
        "Month Number"
    ] = dashboard_df[
        "EventDate Parsed"
    ].dt.month.astype(
        "Int64"
    )

    dashboard_df[
        "Month"
    ] = dashboard_df[
        "EventDate Parsed"
    ].dt.month_name()

    dashboard_df[
        "Quarter"
    ] = dashboard_df[
        "EventDate Parsed"
    ].dt.quarter.apply(
        lambda value:
            f"Q{int(value)}"
            if pd.notna(value)
            else ""
    )

    dashboard_df[
        "Year-Month"
    ] = dashboard_df[
        "EventDate Parsed"
    ].dt.to_period(
        "M"
    ).astype(str)

    confidence_column = (
        "Geometric Mean Confidence (%)"
    )

    if confidence_column not in dashboard_df.columns:

        dashboard_df[
            confidence_column
        ] = np.nan

    dashboard_df[
        confidence_column
    ] = pd.to_numeric(
        dashboard_df[
            confidence_column
        ],
        errors="coerce",
    )

    historical_score_column = (
        "Historical Score"
    )

    if historical_score_column not in dashboard_df.columns:

        dashboard_df[
            historical_score_column
        ] = np.nan

    dashboard_df[
        historical_score_column
    ] = pd.to_numeric(
        dashboard_df[
            historical_score_column
        ],
        errors="coerce",
    )

    return dashboard_df


def unique_options(
    dataframe: pd.DataFrame,
    column: str,
) -> List[str]:
    """
    Return sorted, non-empty values for a dashboard filter.
    """

    if column not in dataframe.columns:

        return []

    values = (
        dataframe[column]
        .dropna()
        .astype(str)
        .str.strip()
    )

    values = values[
        values.ne("")
        & values.ne("nan")
        & values.ne("<NA>")
    ]

    return sorted(
        values.unique().tolist()
    )


def calculate_dashboard_metrics(
    dataframe: pd.DataFrame,
) -> Dict[str, Any]:
    """
    Calculate executive KPI values for filtered records.
    """

    total_records = len(
        dataframe
    )

    if total_records == 0:

        return {
            "total_incidents": 0,
            "auto_fill_count": 0,
            "suggest_review_count": 0,
            "manual_review_count": 0,
            "auto_fill_rate": 0.0,
            "suggest_review_rate": 0.0,
            "manual_review_rate": 0.0,
            "average_confidence": np.nan,
            "average_historical_score": np.nan,
            "strong_historical_rate": 0.0,
            "unique_employers": 0,
            "unique_states": 0,
        }

    decision_series = dataframe[
        "Decision"
    ].fillna("")

    auto_fill_count = int(
        decision_series.eq(
            "Auto Fill"
        ).sum()
    )

    suggest_review_count = int(
        decision_series.eq(
            "Suggest Review"
        ).sum()
    )

    manual_review_count = int(
        decision_series.eq(
            "Manual Review"
        ).sum()
    )

    historical_series = dataframe[
        "Historical Validation Status"
    ].fillna("")

    strong_historical_count = int(
        historical_series.eq(
            "Strong Historical Support"
        ).sum()
    )

    average_confidence = dataframe[
        "Geometric Mean Confidence (%)"
    ].mean()

    average_historical_score = dataframe[
        "Historical Score"
    ].mean()

    return {
        "total_incidents":
            total_records,

        "auto_fill_count":
            auto_fill_count,

        "suggest_review_count":
            suggest_review_count,

        "manual_review_count":
            manual_review_count,

        "auto_fill_rate":
            auto_fill_count
            / total_records
            * 100,

        "suggest_review_rate":
            suggest_review_count
            / total_records
            * 100,

        "manual_review_rate":
            manual_review_count
            / total_records
            * 100,

        "average_confidence":
            float(
                average_confidence
            )
            if pd.notna(
                average_confidence
            )
            else np.nan,

        "average_historical_score":
            float(
                average_historical_score
            )
            if pd.notna(
                average_historical_score
            )
            else np.nan,

        "strong_historical_rate":
            strong_historical_count
            / total_records
            * 100,

        "unique_employers":
            int(
                dataframe[
                    "Employer"
                ].replace(
                    "",
                    np.nan
                ).nunique()
            ),

        "unique_states":
            int(
                dataframe[
                    "State"
                ].replace(
                    "",
                    np.nan
                ).nunique()
            ),
    }


def create_excel_export(
    filtered_dataframe: pd.DataFrame,
    metrics: Dict[str, Any],
) -> bytes:
    """
    Create a multi-sheet dashboard Excel export.
    """

    excel_buffer = io.BytesIO()

    metrics_dataframe = pd.DataFrame({
        "Metric": [
            "Total Incidents",
            "Auto Fill Count",
            "Auto Fill Rate (%)",
            "Suggest Review Count",
            "Suggest Review Rate (%)",
            "Manual Review Count",
            "Manual Review Rate (%)",
            "Average Confidence (%)",
            "Average Historical Score",
            "Strong Historical Support Rate (%)",
            "Unique Employers",
            "Unique States",
        ],

        "Value": [
            metrics[
                "total_incidents"
            ],
            metrics[
                "auto_fill_count"
            ],
            round(
                metrics[
                    "auto_fill_rate"
                ],
                2,
            ),
            metrics[
                "suggest_review_count"
            ],
            round(
                metrics[
                    "suggest_review_rate"
                ],
                2,
            ),
            metrics[
                "manual_review_count"
            ],
            round(
                metrics[
                    "manual_review_rate"
                ],
                2,
            ),
            (
                round(
                    metrics[
                        "average_confidence"
                    ],
                    2,
                )
                if pd.notna(
                    metrics[
                        "average_confidence"
                    ]
                )
                else np.nan
            ),
            (
                round(
                    metrics[
                        "average_historical_score"
                    ],
                    6,
                )
                if pd.notna(
                    metrics[
                        "average_historical_score"
                    ]
                )
                else np.nan
            ),
            round(
                metrics[
                    "strong_historical_rate"
                ],
                2,
            ),
            metrics[
                "unique_employers"
            ],
            metrics[
                "unique_states"
            ],
        ],
    })

    with pd.ExcelWriter(
        excel_buffer,
        engine="openpyxl",
    ) as writer:

        filtered_dataframe.to_excel(
            writer,
            sheet_name="Filtered Incidents",
            index=False,
        )

        metrics_dataframe.to_excel(
            writer,
            sheet_name="Executive Summary",
            index=False,
        )

        for output_column, sheet_name in [
            (
                "Nature Predicted Label",
                "Nature Distribution",
            ),
            (
                "Body Predicted Label",
                "Body Distribution",
            ),
            (
                "Event Predicted Label",
                "Event Distribution",
            ),
            (
                "Source Predicted Label",
                "Source Distribution",
            ),
            (
                "Decision",
                "Decision Distribution",
            ),
            (
                "Historical Validation Status",
                "Historical Validation",
            ),
        ]:

            if output_column in filtered_dataframe.columns:

                distribution_df = (
                    filtered_dataframe[
                        output_column
                    ]
                    .replace(
                        "",
                        np.nan,
                    )
                    .dropna()
                    .value_counts()
                    .rename_axis(
                        output_column
                    )
                    .reset_index(
                        name="Incident Count"
                    )
                )

                distribution_df.to_excel(
                    writer,
                    sheet_name=sheet_name[
                        :31
                    ],
                    index=False,
                )

    return excel_buffer.getvalue()


def create_executive_pdf(
    filtered_dataframe: pd.DataFrame,
    metrics: Dict[str, Any],
    filter_description: str,
) -> bytes:
    """
    Create a concise executive dashboard summary PDF.
    """

    buffer = io.BytesIO()

    document = SimpleDocTemplate(
        buffer,
        pagesize=landscape(
            A4
        ),
        leftMargin=15 * mm,
        rightMargin=15 * mm,
        topMargin=15 * mm,
        bottomMargin=15 * mm,
        title="Safety Analytics Executive Summary",
        author=(
            "Voice-Assisted Workplace "
            "Incident Management System"
        ),
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        name="DashboardTitle",
        parent=styles["Title"],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor(
            "#17324D"
        ),
        alignment=TA_LEFT,
    )

    subtitle_style = ParagraphStyle(
        name="DashboardSubtitle",
        parent=styles["Normal"],
        fontSize=9,
        leading=13,
        textColor=colors.HexColor(
            "#627486"
        ),
    )

    section_style = ParagraphStyle(
        name="DashboardSection",
        parent=styles["Heading2"],
        fontSize=12,
        leading=16,
        textColor=colors.HexColor(
            "#17324D"
        ),
    )

    body_style = ParagraphStyle(
        name="DashboardBody",
        parent=styles["BodyText"],
        fontSize=8,
        leading=11,
        textColor=colors.HexColor(
            "#243746"
        ),
    )

    story = [
        Paragraph(
            "Safety Analytics Executive Summary",
            title_style,
        ),
        Paragraph(
            (
                "Voice-Assisted Workplace Incident "
                "Management System"
            ),
            subtitle_style,
        ),
        Spacer(
            1,
            3 * mm,
        ),
        Paragraph(
            (
                f"<b>Generated:</b> "
                f"{datetime.now().strftime('%d %B %Y, %H:%M')}"
                f"<br/><b>Applied Filters:</b> "
                f"{filter_description}"
            ),
            subtitle_style,
        ),
        Spacer(
            1,
            6 * mm,
        ),
    ]

    confidence_text = (
        f"{metrics['average_confidence']:.2f}%"
        if pd.notna(
            metrics[
                "average_confidence"
            ]
        )
        else "Not available"
    )

    historical_score_text = (
        f"{metrics['average_historical_score']:.6f}"
        if pd.notna(
            metrics[
                "average_historical_score"
            ]
        )
        else "Not available"
    )

    metric_data = [
        [
            "Total Incidents",
            "Auto Fill",
            "Suggest Review",
            "Manual Review",
            "Average Confidence",
            "Average Historical Score",
        ],
        [
            f"{metrics['total_incidents']:,}",
            (
                f"{metrics['auto_fill_count']:,} "
                f"({metrics['auto_fill_rate']:.1f}%)"
            ),
            (
                f"{metrics['suggest_review_count']:,} "
                f"({metrics['suggest_review_rate']:.1f}%)"
            ),
            (
                f"{metrics['manual_review_count']:,} "
                f"({metrics['manual_review_rate']:.1f}%)"
            ),
            confidence_text,
            historical_score_text,
        ],
    ]

    metric_table = Table(
        metric_data,
        colWidths=[
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
            42 * mm,
            48 * mm,
        ],
    )

    metric_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor(
                    "#17324D"
                ),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "BACKGROUND",
                (0, 1),
                (-1, 1),
                colors.HexColor(
                    "#F4F7FA"
                ),
            ),
            (
                "TEXTCOLOR",
                (0, 1),
                (-1, 1),
                colors.HexColor(
                    "#243746"
                ),
            ),
            (
                "ALIGN",
                (0, 0),
                (-1, -1),
                "CENTER",
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTNAME",
                (0, 1),
                (-1, 1),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor(
                    "#D8E1E8"
                ),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor(
                    "#D8E1E8"
                ),
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                4 * mm,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                4 * mm,
            ),
        ])
    )

    story.extend([
        metric_table,
        Spacer(
            1,
            7 * mm,
        ),
        Paragraph(
            "Leading Classification Results",
            section_style,
        ),
    ])

    summary_columns = [
        (
            "Nature Predicted Label",
            "Top Nature",
        ),
        (
            "Body Predicted Label",
            "Top Body Part",
        ),
        (
            "Event Predicted Label",
            "Top Event",
        ),
        (
            "Source Predicted Label",
            "Top Source",
        ),
    ]

    summary_rows = [
        [
            "Category",
            "Leading Classification",
            "Incident Count",
            "Share of Filtered Incidents",
        ]
    ]

    for column_name, category_name in summary_columns:

        if (
            column_name
            in filtered_dataframe.columns
            and not filtered_dataframe.empty
        ):

            counts = (
                filtered_dataframe[
                    column_name
                ]
                .replace(
                    "",
                    np.nan
                )
                .dropna()
                .value_counts()
            )

            if not counts.empty:

                leading_label = str(
                    counts.index[0]
                )

                leading_count = int(
                    counts.iloc[0]
                )

                share = (
                    leading_count
                    / len(
                        filtered_dataframe
                    )
                    * 100
                )

            else:

                leading_label = (
                    "Not available"
                )

                leading_count = 0
                share = 0.0

        else:

            leading_label = (
                "Not available"
            )

            leading_count = 0
            share = 0.0

        summary_rows.append([
            category_name,
            Paragraph(
                leading_label,
                body_style,
            ),
            f"{leading_count:,}",
            f"{share:.1f}%",
        ])

    summary_table = Table(
        summary_rows,
        colWidths=[
            45 * mm,
            125 * mm,
            40 * mm,
            50 * mm,
        ],
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, 0),
                colors.HexColor(
                    "#286A9B"
                ),
            ),
            (
                "TEXTCOLOR",
                (0, 0),
                (-1, 0),
                colors.white,
            ),
            (
                "FONTNAME",
                (0, 0),
                (-1, 0),
                "Helvetica-Bold",
            ),
            (
                "FONTSIZE",
                (0, 0),
                (-1, -1),
                8,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                colors.HexColor(
                    "#D8E1E8"
                ),
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.4,
                colors.HexColor(
                    "#D8E1E8"
                ),
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                2.5 * mm,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                2.5 * mm,
            ),
        ])
    )

    story.extend([
        summary_table,
        Spacer(
            1,
            7 * mm,
        ),
        Paragraph(
            "Management Interpretation",
            section_style,
        ),
        Paragraph(
            (
                "The Decision Tier is the final business routing outcome. "
                "Historical Validation is an additional supporting indicator "
                "that checks whether the predicted classification combination "
                "has been observed in historical incident relationships. "
                "It does not modify the predicted classifications or the "
                "Decision Tier."
            ),
            body_style,
        ),
    ])

    document.build(
        story
    )

    return buffer.getvalue()
