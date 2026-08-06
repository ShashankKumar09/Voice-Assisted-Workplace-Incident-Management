"""
Professional single-incident PDF and CSV report engine.
"""

from __future__ import annotations

import io
import re
import unicodedata
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

import pandas as pd

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import (
    ParagraphStyle,
    getSampleStyleSheet,
)
from reportlab.lib.units import mm
from reportlab.platypus import (
    BaseDocTemplate,
    Frame,
    HRFlowable,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from batch.classifier import flatten_prediction


INCIDENT_INPUT_FIELDS = [
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


BRAND_NAVY = colors.HexColor(
    "#17324D"
)

BRAND_BLUE = colors.HexColor(
    "#286A9B"
)

BRAND_LIGHT_BLUE = colors.HexColor(
    "#EAF3F8"
)

TEXT_DARK = colors.HexColor(
    "#243746"
)

TEXT_MUTED = colors.HexColor(
    "#627486"
)

SURFACE = colors.HexColor(
    "#F6F8FA"
)

BORDER = colors.HexColor(
    "#D8E1E8"
)

SUCCESS = colors.HexColor(
    "#218C74"
)

SUCCESS_LIGHT = colors.HexColor(
    "#E8F6F1"
)

WARNING = colors.HexColor(
    "#D79B22"
)

WARNING_LIGHT = colors.HexColor(
    "#FFF7E4"
)

DANGER = colors.HexColor(
    "#C94C4C"
)

DANGER_LIGHT = colors.HexColor(
    "#FDEEEE"
)

WHITE = colors.white

PAGE_WIDTH, PAGE_HEIGHT = A4

LEFT_MARGIN = 16 * mm
RIGHT_MARGIN = 16 * mm
TOP_MARGIN = 25 * mm
BOTTOM_MARGIN = 18 * mm

REGULAR_FONT = "Helvetica"
BOLD_FONT = "Helvetica-Bold"

base_styles = getSampleStyleSheet()

TITLE_STYLE = ParagraphStyle(
    name="ReportTitle",
    parent=base_styles["Title"],
    fontName=BOLD_FONT,
    fontSize=21,
    leading=26,
    textColor=BRAND_NAVY,
    alignment=TA_LEFT,
    spaceAfter=4 * mm,
)

SUBTITLE_STYLE = ParagraphStyle(
    name="ReportSubtitle",
    parent=base_styles["Normal"],
    fontName=REGULAR_FONT,
    fontSize=9.2,
    leading=13,
    textColor=TEXT_MUTED,
    spaceAfter=4 * mm,
)

SECTION_STYLE = ParagraphStyle(
    name="Section",
    parent=base_styles["Heading2"],
    fontName=BOLD_FONT,
    fontSize=13,
    leading=17,
    textColor=BRAND_NAVY,
    spaceBefore=2 * mm,
    spaceAfter=3 * mm,
)

LABEL_STYLE = ParagraphStyle(
    name="Label",
    parent=base_styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=8,
    leading=10,
    textColor=TEXT_MUTED,
)

VALUE_STYLE = ParagraphStyle(
    name="Value",
    parent=base_styles["Normal"],
    fontName=REGULAR_FONT,
    fontSize=9,
    leading=12,
    textColor=TEXT_DARK,
)

BODY_STYLE = ParagraphStyle(
    name="Body",
    parent=base_styles["BodyText"],
    fontName=REGULAR_FONT,
    fontSize=9.2,
    leading=14,
    textColor=TEXT_DARK,
)

CARD_TITLE_STYLE = ParagraphStyle(
    name="CardTitle",
    parent=base_styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=8,
    leading=10,
    textColor=TEXT_MUTED,
)

CARD_VALUE_STYLE = ParagraphStyle(
    name="CardValue",
    parent=base_styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=11,
    leading=14,
    textColor=BRAND_NAVY,
)

CARD_CONFIDENCE_STYLE = ParagraphStyle(
    name="CardConfidence",
    parent=base_styles["Normal"],
    fontName=REGULAR_FONT,
    fontSize=8,
    leading=10,
    textColor=BRAND_BLUE,
)

CENTER_LABEL_STYLE = ParagraphStyle(
    name="CenterLabel",
    parent=base_styles["Normal"],
    fontName=REGULAR_FONT,
    fontSize=8,
    leading=10,
    textColor=TEXT_MUTED,
    alignment=TA_CENTER,
)

CENTER_VALUE_STYLE = ParagraphStyle(
    name="CenterValue",
    parent=base_styles["Normal"],
    fontName=BOLD_FONT,
    fontSize=18,
    leading=22,
    textColor=BRAND_NAVY,
    alignment=TA_CENTER,
)


def clean_value(
    value: Any,
) -> str:

    if value is None:

        return "Not provided"

    try:

        if pd.isna(value):

            return "Not provided"

    except Exception:

        pass

    text = str(
        value
    ).strip()

    return text or "Not provided"


def escape_pdf_text(
    value: Any,
) -> str:

    return (
        clean_value(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def safe_filename(
    value: Any,
) -> str:

    text = unicodedata.normalize(
        "NFKD",
        clean_value(value),
    )

    text = re.sub(
        r"[^A-Za-z0-9_-]+",
        "_",
        text,
    ).strip("_")

    return text or "incident"


class IncidentReportDocument(
    BaseDocTemplate
):

    def __init__(
        self,
        filename,
        report_id: str,
        **kwargs,
    ):

        super().__init__(
            filename,
            pagesize=A4,
            leftMargin=LEFT_MARGIN,
            rightMargin=RIGHT_MARGIN,
            topMargin=TOP_MARGIN,
            bottomMargin=BOTTOM_MARGIN,
            **kwargs,
        )

        self.report_id = report_id

        frame = Frame(
            self.leftMargin,
            self.bottomMargin,
            self.width,
            self.height,
            id="normal",
        )

        self.addPageTemplates([
            PageTemplate(
                id="IncidentReport",
                frames=[frame],
                onPage=self._header_footer,
            )
        ])

    def _header_footer(
        self,
        canvas,
        document,
    ) -> None:

        canvas.saveState()

        canvas.setFillColor(
            BRAND_NAVY
        )

        canvas.rect(
            0,
            PAGE_HEIGHT - 15 * mm,
            PAGE_WIDTH,
            15 * mm,
            stroke=0,
            fill=1,
        )

        canvas.setFillColor(
            WHITE
        )

        canvas.setFont(
            BOLD_FONT,
            9,
        )

        canvas.drawString(
            LEFT_MARGIN,
            PAGE_HEIGHT - 9.5 * mm,
            "VOICE-ASSISTED WORKPLACE INCIDENT MANAGEMENT SYSTEM",
        )

        canvas.setFont(
            REGULAR_FONT,
            7,
        )

        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_MARGIN,
            PAGE_HEIGHT - 9.5 * mm,
            f"Report ID: {self.report_id}",
        )

        canvas.setStrokeColor(
            BORDER
        )

        canvas.line(
            LEFT_MARGIN,
            12 * mm,
            PAGE_WIDTH - RIGHT_MARGIN,
            12 * mm,
        )

        canvas.setFillColor(
            TEXT_MUTED
        )

        canvas.setFont(
            REGULAR_FONT,
            7,
        )

        canvas.drawString(
            LEFT_MARGIN,
            7.5 * mm,
            "Generated by the Voice-Assisted Workplace Incident Management System",
        )

        canvas.drawRightString(
            PAGE_WIDTH - RIGHT_MARGIN,
            7.5 * mm,
            f"Page {document.page}",
        )

        canvas.restoreState()


def _field_cell(
    label: str,
    value: Any,
):

    return [
        Paragraph(
            escape_pdf_text(
                label
            ),
            LABEL_STYLE,
        ),
        Spacer(
            1,
            1 * mm,
        ),
        Paragraph(
            escape_pdf_text(
                value
            ),
            VALUE_STYLE,
        ),
    ]


def _prediction_card(
    task_name: str,
    prediction: Dict[str, Any],
):

    card = Table(
        [[[
            Paragraph(
                task_name.upper(),
                CARD_TITLE_STYLE,
            ),
            Spacer(
                1,
                1 * mm,
            ),
            Paragraph(
                escape_pdf_text(
                    prediction[
                        "label"
                    ]
                ),
                CARD_VALUE_STYLE,
            ),
            Spacer(
                1,
                1.5 * mm,
            ),
            Paragraph(
                (
                    "Confidence: "
                    f"{prediction['confidence_percent']:.2f}%"
                ),
                CARD_CONFIDENCE_STYLE,
            ),
        ]]],
        colWidths=[
            82 * mm
        ],
        rowHeights=[
            31 * mm
        ],
    )

    card.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                WHITE,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.8,
                BORDER,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5 * mm,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5 * mm,
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

    return card


def _decision_colors(
    decision: str,
):

    if decision == "Auto Fill":

        return (
            SUCCESS,
            SUCCESS_LIGHT,
        )

    if decision == "Suggest Review":

        return (
            WARNING,
            WARNING_LIGHT,
        )

    return (
        DANGER,
        DANGER_LIGHT,
    )


def build_flat_record(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
    reporting_channel: str,
) -> Dict[str, Any]:

    record = {
        field:
            clean_value(
                incident_details.get(
                    field,
                    "",
                )
            )
        for field in INCIDENT_INPUT_FIELDS
    }

    flattened_prediction = flatten_prediction(
        prediction_result
    )

    excluded_fragments = (
        "historical",
        "relationship_validation",
        "consistency_score",
        "weakest_relationship",
    )

    record.update(
        {
            key: value
            for key, value in flattened_prediction.items()
            if not any(
                fragment in str(key).lower()
                for fragment in excluded_fragments
            )
        }
    )

    record[
        "Reporting Channel"
    ] = reporting_channel

    record[
        "Report Generated At"
    ] = datetime.now().strftime(
        "%Y-%m-%d %H:%M:%S"
    )

    return record


def generate_pdf(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
    reporting_channel: str,
) -> bytes:

    if prediction_result.get(
        "status"
    ) != "success":

        raise ValueError(
            "A successful prediction result is required."
        )

    incident_id = clean_value(
        incident_details.get(
            "ID",
            "incident",
        )
    )

    report_id = (
        f"{safe_filename(incident_id)}-"
        f"{datetime.now().strftime('%Y%m%d%H%M%S')}"
    )

    buffer = io.BytesIO()

    document = IncidentReportDocument(
        buffer,
        report_id=report_id,
        title="Workplace Incident Classification Report",
    )

    story = []

    story.append(
        Paragraph(
            "Workplace Incident Report",
            TITLE_STYLE,
        )
    )

    story.append(
        Paragraph(
            (
                f"Reporting channel: "
                f"{escape_pdf_text(reporting_channel)}"
                f"&nbsp;&nbsp;|&nbsp;&nbsp;"
                f"Generated: "
                f"{datetime.now().strftime('%d %B %Y, %H:%M')}"
            ),
            SUBTITLE_STYLE,
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=BRAND_BLUE,
            spaceAfter=5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Incident Information",
            SECTION_STYLE,
        )
    )

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

    field_rows = []

    for position in range(
        0,
        len(structured_fields),
        2,
    ):

        left_label, left_key = (
            structured_fields[
                position
            ]
        )

        left_cell = _field_cell(
            left_label,
            incident_details.get(
                left_key,
                "",
            ),
        )

        if position + 1 < len(
            structured_fields
        ):

            right_label, right_key = (
                structured_fields[
                    position + 1
                ]
            )

            right_cell = _field_cell(
                right_label,
                incident_details.get(
                    right_key,
                    "",
                ),
            )

        else:

            right_cell = []

        field_rows.append([
            left_cell,
            right_cell,
        ])

    field_table = Table(
        field_rows,
        colWidths=[
            86 * mm,
            86 * mm,
        ],
    )

    field_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                SURFACE,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.7,
                BORDER,
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                BORDER,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4 * mm,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4 * mm,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3 * mm,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3 * mm,
            ),
        ])
    )

    story.append(
        field_table
    )

    story.append(
        Spacer(
            1,
            5 * mm,
        )
    )

    story.append(
        Paragraph(
            "Final Narrative",
            SECTION_STYLE,
        )
    )

    narrative_table = Table(
        [[
            Paragraph(
                escape_pdf_text(
                    incident_details.get(
                        "Final Narrative",
                        "",
                    )
                ),
                BODY_STYLE,
            )
        ]],
        colWidths=[
            172 * mm
        ],
    )

    narrative_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                BRAND_LIGHT_BLUE,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.8,
                BRAND_BLUE,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5 * mm,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5 * mm,
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

    story.append(
        narrative_table
    )

    story.append(
        PageBreak()
    )

    story.append(
        Paragraph(
            "Classification Results",
            TITLE_STYLE,
        )
    )

    story.append(
        Paragraph(
            (
                "The incident narrative was evaluated across the Nature, "
                "Body, Event and Source classification categories."
            ),
            SUBTITLE_STYLE,
        )
    )

    story.append(
        HRFlowable(
            width="100%",
            thickness=1.2,
            color=BRAND_BLUE,
            spaceAfter=5 * mm,
        )
    )

    prediction_cards = [
        _prediction_card(
            task,
            prediction_result[
                "predictions"
            ][task],
        )
        for task in [
            "nature",
            "body",
            "event",
            "source",
        ]
    ]

    prediction_grid = Table(
        [
            [
                prediction_cards[0],
                prediction_cards[1],
            ],
            [
                prediction_cards[2],
                prediction_cards[3],
            ],
        ],
        colWidths=[
            86 * mm,
            86 * mm,
        ],
        rowHeights=[
            36 * mm,
            36 * mm,
        ],
    )

    prediction_grid.setStyle(
        TableStyle([
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                1.5 * mm,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                1.5 * mm,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                1.5 * mm,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                1.5 * mm,
            ),
        ])
    )

    story.append(
        prediction_grid
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    overall_confidence = prediction_result[
        "incident_confidence"
    ]["geometric_mean_percent"]

    decision = prediction_result[
        "decision"
    ]["tier"]

    decision_color, decision_background = (
        _decision_colors(
            decision
        )
    )

    decision_style = ParagraphStyle(
        name="DecisionValue",
        parent=CENTER_VALUE_STYLE,
        textColor=decision_color,
    )

    summary_table = Table(
        [[
            [
                Paragraph(
                    "OVERALL CONFIDENCE",
                    CENTER_LABEL_STYLE,
                ),
                Spacer(
                    1,
                    2 * mm,
                ),
                Paragraph(
                    f"{overall_confidence:.2f}%",
                    CENTER_VALUE_STYLE,
                ),
            ],
            [
                Paragraph(
                    "DECISION TIER - FINAL OUTCOME",
                    CENTER_LABEL_STYLE,
                ),
                Spacer(
                    1,
                    2 * mm,
                ),
                Paragraph(
                    decision.upper(),
                    decision_style,
                ),
            ],
        ]],
        colWidths=[
            86 * mm,
            86 * mm,
        ],
        rowHeights=[
            33 * mm
        ],
    )

    summary_table.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (0, 0),
                BRAND_LIGHT_BLUE,
            ),
            (
                "BACKGROUND",
                (1, 0),
                (1, 0),
                decision_background,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.8,
                BORDER,
            ),
            (
                "INNERGRID",
                (0, 0),
                (-1, -1),
                0.5,
                BORDER,
            ),
            (
                "VALIGN",
                (0, 0),
                (-1, -1),
                "MIDDLE",
            ),
        ])
    )

    story.append(
        summary_table
    )

    story.append(
        Spacer(
            1,
            6 * mm,
        )
    )

    story.append(
        Paragraph(
            "Decision Tier - Final Conclusion",
            SECTION_STYLE,
        )
    )

    if decision == "Auto Fill":

        conclusion = (
            "AUTO FILL is the final recommended outcome. "
            "The overall confidence met the frozen Auto Fill threshold, "
            "so the classifications may be populated automatically and "
            "remain available for reviewer confirmation."
        )

    elif decision == "Suggest Review":

        conclusion = (
            "SUGGEST REVIEW is the final recommended outcome. "
            "The classifications should be presented as recommendations "
            "and reviewed before submission."
        )

    else:

        conclusion = (
            "MANUAL REVIEW is the final recommended outcome. "
            "The classifications require manual verification and should "
            "not be accepted automatically."
        )

    decision_box = Table(
        [[
            Paragraph(
                (
                    "<b>The Decision Tier is the final business outcome "
                    "generated by the system.</b><br/>"
                    + escape_pdf_text(
                        conclusion
                    )
                    + "<br/><br/>"
                    "<b>Decision definitions:</b><br/>"
                    "<b>Auto Fill:</b> Predictions may be populated automatically "
                    "for reviewer confirmation.<br/>"
                    "<b>Suggest Review:</b> Predictions should be reviewed before "
                    "submission.<br/>"
                    "<b>Manual Review:</b> Predictions require manual verification "
                    "and should not be automatically accepted."
                ),
                BODY_STYLE,
            )
        ]],
        colWidths=[
            172 * mm
        ],
    )

    decision_box.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                decision_background,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.9,
                decision_color,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                5 * mm,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                5 * mm,
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

    story.append(
        decision_box
    )

    story.append(
        Spacer(
            1,
            4 * mm,
        )
    )

    notice_box = Table(
        [[
            Paragraph(
                (
                    "<b>Important Notice:</b> The classifications in this report "
                    "are generated by a machine-learning decision-support system. "
                    "Final regulatory, legal and organizational responsibility "
                    "remains with the authorized incident reviewer."
                ),
                BODY_STYLE,
            )
        ]],
        colWidths=[
            172 * mm
        ],
    )

    notice_box.setStyle(
        TableStyle([
            (
                "BACKGROUND",
                (0, 0),
                (-1, -1),
                SURFACE,
            ),
            (
                "BOX",
                (0, 0),
                (-1, -1),
                0.6,
                BORDER,
            ),
            (
                "LEFTPADDING",
                (0, 0),
                (-1, -1),
                4 * mm,
            ),
            (
                "RIGHTPADDING",
                (0, 0),
                (-1, -1),
                4 * mm,
            ),
            (
                "TOPPADDING",
                (0, 0),
                (-1, -1),
                3 * mm,
            ),
            (
                "BOTTOMPADDING",
                (0, 0),
                (-1, -1),
                3 * mm,
            ),
        ])
    )

    story.append(
        notice_box
    )

    document.build(
        story
    )

    return buffer.getvalue()


def generate_report_package(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
    reporting_channel: str,
) -> Dict[str, Any]:

    pdf_bytes = generate_pdf(
        incident_details=incident_details,
        prediction_result=prediction_result,
        reporting_channel=reporting_channel,
    )

    record = build_flat_record(
        incident_details=incident_details,
        prediction_result=prediction_result,
        reporting_channel=reporting_channel,
    )

    csv_dataframe = pd.DataFrame(
        [record]
    )

    csv_bytes = csv_dataframe.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    incident_id = safe_filename(
        incident_details.get(
            "ID",
            "incident",
        )
    )

    timestamp = datetime.now().strftime(
        "%Y%m%d_%H%M%S"
    )

    return {
        "status":
            "success",

        "pdf_bytes":
            pdf_bytes,

        "csv_bytes":
            csv_bytes,

        "csv_dataframe":
            csv_dataframe,

        "pdf_filename":
            (
                f"incident_report_"
                f"{incident_id}_"
                f"{timestamp}.pdf"
            ),

        "csv_filename":
            (
                f"incident_record_"
                f"{incident_id}_"
                f"{timestamp}.csv"
            ),

        "reporting_channel":
            reporting_channel,
    }
