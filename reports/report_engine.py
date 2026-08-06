"""Professional single-incident PDF and standardized OSHA CSV report engine."""
from __future__ import annotations

import io
import re
import unicodedata
from datetime import datetime
from typing import Any, Dict

import pandas as pd
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    PageBreak,
)

from batch.classifier import flatten_prediction
from core.osha_codes import enrich_prediction_result


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

STANDARD_OUTPUT_FIELDS = [
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

NAVY = colors.HexColor("#17324D")
BLUE = colors.HexColor("#286A9B")
LIGHT_BLUE = colors.HexColor("#EAF3F8")
BORDER = colors.HexColor("#D8E1E8")
MUTED = colors.HexColor("#627486")
WHITE = colors.white

STYLES = getSampleStyleSheet()
TITLE_STYLE = ParagraphStyle(
    "ReportTitle",
    parent=STYLES["Title"],
    fontName="Helvetica-Bold",
    fontSize=20,
    leading=24,
    textColor=NAVY,
    spaceAfter=5 * mm,
)
SECTION_STYLE = ParagraphStyle(
    "Section",
    parent=STYLES["Heading2"],
    fontName="Helvetica-Bold",
    fontSize=13,
    leading=16,
    textColor=NAVY,
    spaceBefore=3 * mm,
    spaceAfter=3 * mm,
)
BODY_STYLE = ParagraphStyle(
    "Body",
    parent=STYLES["BodyText"],
    fontName="Helvetica",
    fontSize=9,
    leading=13,
    textColor=colors.HexColor("#243746"),
)
SMALL_STYLE = ParagraphStyle(
    "Small",
    parent=STYLES["BodyText"],
    fontName="Helvetica",
    fontSize=8,
    leading=11,
    textColor=MUTED,
)
CENTER_STYLE = ParagraphStyle(
    "Center",
    parent=BODY_STYLE,
    alignment=TA_CENTER,
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    try:
        if pd.isna(value):
            return ""
    except Exception:
        pass
    return str(value).strip()


def _escape(value: Any) -> str:
    return (
        _clean(value)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
    )


def _safe_filename(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value))
    text = re.sub(r"[^A-Za-z0-9_-]+", "_", text).strip("_")
    return text or "incident"


def build_flat_record(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
    reporting_channel: str,
) -> Dict[str, Any]:
    """Build a user-facing record with OSHA fields only."""
    enrich_prediction_result(prediction_result)
    record = {
        field: _clean(incident_details.get(field, ""))
        for field in INCIDENT_INPUT_FIELDS
    }
    standardized = flatten_prediction(prediction_result)
    record.update(
        {field: standardized.get(field, "") for field in STANDARD_OUTPUT_FIELDS}
    )
    return record


def _classification_rows(prediction_result: Dict[str, Any]):
    enrich_prediction_result(prediction_result)
    task_config = [
        ("nature", "Nature"),
        ("body", "Part of Body"),
        ("event", "Event"),
        ("source", "Source"),
    ]
    rows = [["Category", "OSHA/OIICS Code", "Title", "Confidence"]]
    for task_name, display_name in task_config:
        item = prediction_result["predictions"][task_name]
        rows.append(
            [
                display_name,
                _clean(item.get("code", "")),
                Paragraph(_escape(item.get("title", item.get("label", ""))), BODY_STYLE),
                f"{float(item.get('confidence_percent', 0.0)):.2f}%",
            ]
        )
    return rows


def generate_pdf(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
    reporting_channel: str,
) -> bytes:
    """Generate a concise professional PDF with codes and titles."""
    enrich_prediction_result(prediction_result)
    buffer = io.BytesIO()
    document = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=16 * mm,
        leftMargin=16 * mm,
        topMargin=16 * mm,
        bottomMargin=16 * mm,
        title="Workplace Incident Classification Report",
    )
    story = [
        Paragraph("Workplace Incident Report", TITLE_STYLE),
        Paragraph(
            f"Generated from {_escape(reporting_channel)} on "
            f"{datetime.now().strftime('%d %B %Y, %H:%M')}",
            SMALL_STYLE,
        ),
        Spacer(1, 4 * mm),
        Paragraph("Incident Information", SECTION_STYLE),
    ]

    info_rows = []
    structured_fields = [
        ("Incident ID", "ID"),
        ("UPA", "UPA"),
        ("Event Date", "EventDate"),
        ("Employer", "Employer"),
        ("Address", "Address1"),
        ("City", "City"),
        ("State", "State"),
        ("ZIP / Postal Code", "Zip"),
        ("Primary NAICS", "Primary NAICS"),
        ("Hospitalized", "Hospitalized"),
        ("Amputation", "Amputation"),
        ("Loss of Eye", "Loss of Eye"),
        ("Inspection", "Inspection"),
        ("Federal / State", "FederalState"),
    ]
    for label, key in structured_fields:
        info_rows.append(
            [
                Paragraph(f"<b>{_escape(label)}</b>", BODY_STYLE),
                Paragraph(_escape(incident_details.get(key, "")) or "Not provided", BODY_STYLE),
            ]
        )
    info_table = Table(info_rows, colWidths=[48 * mm, 126 * mm])
    info_table.setStyle(
        TableStyle(
            [
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("BACKGROUND", (0, 0), (0, -1), LIGHT_BLUE),
                ("VALIGN", (0, 0), (-1, -1), "TOP"),
                ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    story.extend([info_table, Spacer(1, 5 * mm)])

    story.extend(
        [
            Paragraph("Final Narrative", SECTION_STYLE),
            Paragraph(
                _escape(incident_details.get("Final Narrative", "")) or "Not provided",
                BODY_STYLE,
            ),
            Spacer(1, 5 * mm),
            Paragraph("OSHA/OIICS Classification Results", SECTION_STYLE),
        ]
    )

    result_table = Table(
        _classification_rows(prediction_result),
        colWidths=[31 * mm, 30 * mm, 88 * mm, 27 * mm],
        repeatRows=1,
    )
    result_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), NAVY),
                ("TEXTCOLOR", (0, 0), (-1, 0), WHITE),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("ALIGN", (1, 1), (1, -1), "CENTER"),
                ("ALIGN", (3, 1), (3, -1), "CENTER"),
                ("GRID", (0, 0), (-1, -1), 0.5, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
                ("LEFTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("RIGHTPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
            ]
        )
    )
    story.extend([result_table, Spacer(1, 6 * mm)])

    overall = float(
        prediction_result["incident_confidence"]["geometric_mean_percent"]
    )
    decision = _clean(prediction_result["decision"]["tier"])
    decision_table = Table(
        [
            [Paragraph("Overall Confidence", CENTER_STYLE), Paragraph("Decision", CENTER_STYLE)],
            [
                Paragraph(f"<b>{overall:.2f}%</b>", CENTER_STYLE),
                Paragraph(f"<b>{_escape(decision)}</b>", CENTER_STYLE),
            ],
        ],
        colWidths=[87 * mm, 87 * mm],
    )
    decision_table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), LIGHT_BLUE),
                ("GRID", (0, 0), (-1, -1), 0.6, BORDER),
                ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
                ("TOPPADDING", (0, 0), (-1, -1), 3 * mm),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3 * mm),
            ]
        )
    )
    story.append(decision_table)
    document.build(story)
    return buffer.getvalue()


def generate_report_package(
    incident_details: Dict[str, Any],
    prediction_result: Dict[str, Any],
    reporting_channel: str,
) -> Dict[str, Any]:
    """Generate the standardized PDF and CSV package used by manual and voice pages."""
    enrich_prediction_result(prediction_result)
    record = build_flat_record(
        incident_details=incident_details,
        prediction_result=prediction_result,
        reporting_channel=reporting_channel,
    )
    csv_dataframe = pd.DataFrame([record])
    csv_bytes = csv_dataframe.to_csv(index=False).encode("utf-8-sig")
    pdf_bytes = generate_pdf(
        incident_details=incident_details,
        prediction_result=prediction_result,
        reporting_channel=reporting_channel,
    )
    incident_id = _safe_filename(incident_details.get("ID", "incident"))
    return {
        "pdf_bytes": pdf_bytes,
        "csv_bytes": csv_bytes,
        "csv_dataframe": csv_dataframe,
        "pdf_filename": f"{incident_id}_incident_report.pdf",
        "csv_filename": f"{incident_id}_incident_record.csv",
    }
