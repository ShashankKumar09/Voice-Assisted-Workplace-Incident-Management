"""Interactive Safety Analytics Dashboard."""
from __future__ import annotations

import io
from pathlib import Path
from typing import Iterable

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from ui.guide_components import (
    render_dashboard_overview,
    render_module_header,
    render_section_header,
)


APP_ROOT = Path(__file__).resolve().parents[1]
INCIDENT_DATA_PATH = APP_ROOT / "data" / "incident_records.csv"

TITLE_COLUMNS = {
    "Nature": "NatureTitle",
    "Part of Body": "Part of Body Title",
    "Event": "EventTitle",
    "Source": "SourceTitle",
}
CONFIDENCE_COLUMNS = [
    "Nature Confidence (%)",
    "Part of Body Confidence (%)",
    "Event Confidence (%)",
    "Source Confidence (%)",
]

# Branded dashboard palette. Each analytical area has its own accent while
# remaining consistent with the navy/teal application theme.
CHART_COLORS = {
    "trend": "#247D94",
    "nature": "#2A9D8F",
    "body": "#5B7DB1",
    "event": "#E09F3E",
    "source": "#8F6BB3",
    "confidence": "#2F9EAA",
    "employer": "#D66A5E",
    "state": "#4C956C",
}
DECISION_COLORS = {
    "Auto Fill": "#2A9D8F",
    "Suggest Review": "#E9C46A",
    "Manual Review": "#E76F51",
}


def _clean_text(series: pd.Series) -> pd.Series:
    return series.fillna("").astype(str).str.strip()


def _load_records() -> pd.DataFrame:
    if not INCIDENT_DATA_PATH.is_file():
        return pd.DataFrame()
    try:
        dataframe = pd.read_csv(INCIDENT_DATA_PATH, low_memory=False)
    except Exception:
        return pd.DataFrame()

    for column in [
        "ID", "Employer", "City", "State", "FederalState", "Decision",
        "NatureTitle", "Part of Body Title", "EventTitle", "SourceTitle",
    ]:
        if column not in dataframe.columns:
            dataframe[column] = ""
        dataframe[column] = _clean_text(dataframe[column])

    if "EventDate" not in dataframe.columns:
        dataframe["EventDate"] = ""
    dataframe["EventDate Parsed"] = pd.to_datetime(
        dataframe["EventDate"], errors="coerce"
    )
    dataframe["Month"] = dataframe["EventDate Parsed"].dt.to_period("M").astype(str)
    dataframe.loc[dataframe["EventDate Parsed"].isna(), "Month"] = ""

    if "Overall Confidence (%)" not in dataframe.columns:
        available = [c for c in CONFIDENCE_COLUMNS if c in dataframe.columns]
        if available:
            numeric = dataframe[available].apply(pd.to_numeric, errors="coerce")
            dataframe["Overall Confidence (%)"] = numeric.mean(axis=1)
        else:
            dataframe["Overall Confidence (%)"] = np.nan
    dataframe["Overall Confidence (%)"] = pd.to_numeric(
        dataframe["Overall Confidence (%)"], errors="coerce"
    )
    return dataframe


def _options(dataframe: pd.DataFrame, column: str) -> list[str]:
    if column not in dataframe.columns:
        return []
    values = _clean_text(dataframe[column])
    return sorted(values[(values != "") & (values.str.lower() != "nan")].unique())


def _apply_multiselect(
    dataframe: pd.DataFrame,
    column: str,
    selected: Iterable[str],
) -> pd.DataFrame:
    selected_values = list(selected)
    if not selected_values:
        return dataframe
    return dataframe[dataframe[column].isin(selected_values)]


def _metric_card(label: str, value: str, caption: str) -> None:
    st.html(
        f"""
        <div style="height:100%;padding:1.1rem 1.15rem;border-radius:17px;
            border:1px solid #DCE6ED;background:#FFFFFF;
            box-shadow:0 8px 20px rgba(23,50,77,.055);">
            <div style="color:#667D8D;font-size:.72rem;font-weight:800;
                letter-spacing:.07em;text-transform:uppercase;">{label}</div>
            <div style="margin-top:.45rem;color:#17324D;font-size:1.55rem;
                font-weight:850;line-height:1.15;">{value}</div>
            <div style="margin-top:.38rem;color:#78909F;font-size:.74rem;
                line-height:1.45;">{caption}</div>
        </div>
        """
    )


def _distribution(dataframe: pd.DataFrame, column: str, top_n: int = 10) -> pd.DataFrame:
    if column not in dataframe.columns:
        return pd.DataFrame(columns=[column, "Incident Count"])
    values = _clean_text(dataframe[column])
    values = values[(values != "") & (values.str.lower() != "nan")]
    return (
        values.value_counts()
        .head(top_n)
        .rename_axis(column)
        .reset_index(name="Incident Count")
    )


def _style_chart(fig, height: int) -> None:
    """Apply a consistent polished appearance to Plotly charts."""
    fig.update_layout(
        margin=dict(l=10, r=10, t=55, b=10),
        height=height,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(247,250,252,0.75)",
        font=dict(color="#526B7C"),
        title_font=dict(color="#17324D", size=16),
        legend_title_text="",
    )
    fig.update_xaxes(
        gridcolor="#E3EBF0",
        linecolor="#D5E1E8",
        zerolinecolor="#D5E1E8",
    )
    fig.update_yaxes(
        gridcolor="rgba(227,235,240,0.45)",
        linecolor="#D5E1E8",
    )


def _excel_bytes(dataframe: pd.DataFrame) -> bytes:
    export_df = dataframe.drop(
        columns=["EventDate Parsed", "Month"], errors="ignore"
    ).copy()
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        export_df.to_excel(writer, sheet_name="Filtered Incidents", index=False)
        summary = pd.DataFrame(
            {
                "Metric": [
                    "Total Incidents", "Average Confidence (%)", "Auto Fill",
                    "Suggest Review", "Manual Review", "Unique Employers", "Unique States",
                ],
                "Value": [
                    len(dataframe),
                    round(float(dataframe["Overall Confidence (%)"].mean()), 2)
                    if dataframe["Overall Confidence (%)"].notna().any() else np.nan,
                    int(dataframe["Decision"].eq("Auto Fill").sum()),
                    int(dataframe["Decision"].eq("Suggest Review").sum()),
                    int(dataframe["Decision"].eq("Manual Review").sum()),
                    int(dataframe["Employer"].replace("", np.nan).nunique()),
                    int(dataframe["State"].replace("", np.nan).nunique()),
                ],
            }
        )
        summary.to_excel(writer, sheet_name="Executive Summary", index=False)
        for column, sheet in [
            ("NatureTitle", "Nature Distribution"),
            ("Part of Body Title", "Body Distribution"),
            ("EventTitle", "Event Distribution"),
            ("SourceTitle", "Source Distribution"),
            ("Decision", "Decision Distribution"),
        ]:
            _distribution(dataframe, column, 50).to_excel(
                writer, sheet_name=sheet, index=False
            )
    return buffer.getvalue()


def render() -> None:
    render_module_header(
        eyebrow="Management Safety Intelligence",
        title="Safety Analytics Dashboard",
        description=(
            "Explore incident trends, OSHA/OIICS classification distributions, "
            "confidence levels and decision tiers through interactive filters."
        ),
        icon="📊",
    )

    render_dashboard_overview(
        description=(
            "This dashboard converts completed manual, voice and batch incident reports "
            "into management-ready safety insights. All charts respond to the filters below."
        ),
        capabilities=[
            ("📈", "Incident Trends", "Review incident volume over time."),
            ("📋", "Classification Analysis", "Compare Nature, Body, Event and Source."),
            ("🎯", "Decision Analysis", "Track Auto Fill, Suggest Review and Manual Review."),
            ("🏢", "Organizational Insights", "Analyse incidents by employer and location."),
            ("📊", "Confidence Insights", "Review overall model confidence."),
            ("⬇️", "Downloadable Results", "Export filtered records and summaries."),
        ],
    )

    dataframe = _load_records()
    if dataframe.empty:
        st.info(
            "No completed incident records are available yet. Submit a Manual, Voice "
            "or Batch report first; saved records will appear here automatically."
        )
        return

    render_section_header(
        "1", "Filter Incident Records",
        "Select the period, employer, location or decision tier to focus the dashboard.",
        "🔎",
    )

    valid_dates = dataframe["EventDate Parsed"].dropna()
    min_date = valid_dates.min().date() if not valid_dates.empty else None
    max_date = valid_dates.max().date() if not valid_dates.empty else None

    f1, f2, f3, f4 = st.columns(4, gap="medium")
    with f1:
        date_range = st.date_input(
            "Event date range",
            value=(min_date, max_date) if min_date and max_date else (),
        )
    with f2:
        employers = st.multiselect("Employer", _options(dataframe, "Employer"))
    with f3:
        states = st.multiselect("State", _options(dataframe, "State"))
    with f4:
        decisions = st.multiselect(
            "Decision", ["Auto Fill", "Suggest Review", "Manual Review"]
        )

    filtered = dataframe.copy()
    if isinstance(date_range, (tuple, list)) and len(date_range) == 2:
        start_date, end_date = date_range
        parsed = filtered["EventDate Parsed"]
        filtered = filtered[
            parsed.isna()
            | ((parsed.dt.date >= start_date) & (parsed.dt.date <= end_date))
        ]
    filtered = _apply_multiselect(filtered, "Employer", employers)
    filtered = _apply_multiselect(filtered, "State", states)
    filtered = _apply_multiselect(filtered, "Decision", decisions)

    if filtered.empty:
        st.warning("No incidents match the selected filters.")
        return

    render_section_header(
        "2", "Executive Safety Overview",
        "Key indicators calculated from the currently filtered incident records.",
        "📌",
    )

    total = len(filtered)
    auto_count = int(filtered["Decision"].eq("Auto Fill").sum())
    suggest_count = int(filtered["Decision"].eq("Suggest Review").sum())
    manual_count = int(filtered["Decision"].eq("Manual Review").sum())
    average_confidence = filtered["Overall Confidence (%)"].mean()

    metrics = st.columns(5, gap="medium")
    with metrics[0]:
        _metric_card("Total Incidents", f"{total:,}", "Filtered incident records")
    with metrics[1]:
        _metric_card("Auto Fill", f"{auto_count:,}", f"{auto_count / total * 100:.1f}% of incidents")
    with metrics[2]:
        _metric_card("Suggest Review", f"{suggest_count:,}", f"{suggest_count / total * 100:.1f}% of incidents")
    with metrics[3]:
        _metric_card("Manual Review", f"{manual_count:,}", f"{manual_count / total * 100:.1f}% of incidents")
    with metrics[4]:
        _metric_card(
            "Average Confidence",
            f"{average_confidence:.2f}%" if pd.notna(average_confidence) else "N/A",
            "Overall prediction confidence",
        )

    render_section_header(
        "3", "Incident and Decision Trends",
        "Review incident volume over time and how reports are routed for action.",
        "📈",
    )

    left, right = st.columns(2, gap="large")
    with left:
        trend = (
            filtered[filtered["Month"] != ""]
            .groupby("Month", as_index=False)
            .size()
            .rename(columns={"size": "Incident Count"})
            .sort_values("Month")
        )
        if trend.empty:
            st.info("No valid event dates are available for the trend chart.")
        else:
            fig = px.line(
                trend,
                x="Month",
                y="Incident Count",
                markers=True,
                title="Monthly Incident Trend",
                color_discrete_sequence=[CHART_COLORS["trend"]],
            )
            fig.update_traces(line=dict(width=4), marker=dict(size=9))
            _style_chart(fig, 360)
            st.plotly_chart(fig, use_container_width=True)

    with right:
        decision_df = _distribution(filtered, "Decision", 10)
        if decision_df.empty:
            st.info("No decision values are available.")
        else:
            fig = px.pie(
                decision_df,
                names="Decision",
                values="Incident Count",
                hole=0.52,
                title="Decision Tier Distribution",
                color="Decision",
                color_discrete_map=DECISION_COLORS,
            )
            fig.update_traces(textposition="inside", textinfo="percent+label")
            _style_chart(fig, 360)
            st.plotly_chart(fig, use_container_width=True)

    render_section_header(
        "4", "OSHA/OIICS Classification Analysis",
        "Compare the most frequent injury, body-part, event and source classifications.",
        "📋",
    )

    chart_pairs = [
        ("NatureTitle", "Top Nature of Injury Classifications", CHART_COLORS["nature"]),
        ("Part of Body Title", "Top Part of Body Classifications", CHART_COLORS["body"]),
        ("EventTitle", "Top Event Classifications", CHART_COLORS["event"]),
        ("SourceTitle", "Top Source Classifications", CHART_COLORS["source"]),
    ]
    for index in range(0, len(chart_pairs), 2):
        columns = st.columns(2, gap="large")
        for container, (column, title, chart_color) in zip(
            columns, chart_pairs[index:index + 2]
        ):
            with container:
                dist = _distribution(filtered, column, 10).sort_values("Incident Count")
                if dist.empty:
                    st.info(f"No {column} values are available.")
                else:
                    fig = px.bar(
                        dist,
                        x="Incident Count",
                        y=column,
                        orientation="h",
                        title=title,
                        color_discrete_sequence=[chart_color],
                    )
                    fig.update_traces(
                        marker_line_color="rgba(255,255,255,0.7)",
                        marker_line_width=0.6,
                        hovertemplate="%{y}<br>Incidents: %{x}<extra></extra>",
                    )
                    _style_chart(fig, 410)
                    fig.update_layout(yaxis_title="")
                    st.plotly_chart(fig, use_container_width=True)

    render_section_header(
        "5", "Confidence and Organizational Insights",
        "Review model confidence and identify employers or locations with more incidents.",
        "🎯",
    )

    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        confidence_values = filtered["Overall Confidence (%)"].dropna()
        if confidence_values.empty:
            st.info("No confidence values are available.")
        else:
            fig = px.histogram(
                confidence_values.to_frame(),
                x="Overall Confidence (%)",
                nbins=12,
                title="Confidence Distribution",
                color_discrete_sequence=[CHART_COLORS["confidence"]],
            )
            _style_chart(fig, 350)
            st.plotly_chart(fig, use_container_width=True)
    with c2:
        employer_df = _distribution(filtered, "Employer", 10).sort_values("Incident Count")
        if employer_df.empty:
            st.info("No employer values are available.")
        else:
            fig = px.bar(
                employer_df,
                x="Incident Count",
                y="Employer",
                orientation="h",
                title="Incidents by Employer",
                color_discrete_sequence=[CHART_COLORS["employer"]],
            )
            _style_chart(fig, 350)
            fig.update_layout(yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)
    with c3:
        state_df = _distribution(filtered, "State", 10).sort_values("Incident Count")
        if state_df.empty:
            st.info("No state values are available.")
        else:
            fig = px.bar(
                state_df,
                x="Incident Count",
                y="State",
                orientation="h",
                title="Incidents by State",
                color_discrete_sequence=[CHART_COLORS["state"]],
            )
            _style_chart(fig, 350)
            fig.update_layout(yaxis_title="")
            st.plotly_chart(fig, use_container_width=True)

    render_section_header(
        "6", "Review and Export Filtered Results",
        "Download the filtered incident records and executive summary for further review.",
        "⬇️",
    )

    display_columns = [
        column for column in [
            "ID", "EventDate", "Employer", "City", "State", "Final Narrative",
            "Nature", "NatureTitle", "Part of Body", "Part of Body Title",
            "Event", "EventTitle", "Source", "SourceTitle",
            "Overall Confidence (%)", "Decision",
        ] if column in filtered.columns
    ]
    st.dataframe(
        filtered[display_columns],
        use_container_width=True,
        hide_index=True,
        height=360,
    )

    export_df = filtered.drop(columns=["EventDate Parsed", "Month"], errors="ignore")
    d1, d2 = st.columns(2, gap="medium")
    with d1:
        st.download_button(
            "Download Filtered CSV",
            data=export_df.to_csv(index=False).encode("utf-8-sig"),
            file_name="safety_analytics_filtered_records.csv",
            mime="text/csv",
            use_container_width=True,
        )
    with d2:
        st.download_button(
            "Download Analytics Excel",
            data=_excel_bytes(filtered),
            file_name="safety_analytics_summary.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
        )
