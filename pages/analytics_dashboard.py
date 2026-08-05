"""
Professional Safety Analytics Dashboard.
"""

from __future__ import annotations

from datetime import date
from html import escape
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
import pandas as pd
import plotly.express as px
import streamlit as st

from dashboard.analytics_engine import (
    DECISION_ORDER,
    HISTORICAL_ORDER,
    calculate_dashboard_metrics,
    clean_dashboard_dataframe,
    create_excel_export,
    create_executive_pdf,
    unique_options,
)


PLOTLY_CONFIG = {
    "displayModeBar": False,
    "responsive": True,
}


def render_dashboard_header() -> None:

    st.markdown(
        """
        <div class="hero-shell"
             style="padding:2.4rem 2.6rem">

            <div class="hero-eyebrow">
                Enterprise Safety Intelligence
            </div>

            <div class="hero-title"
                 style="font-size:2.65rem">
                📊 Safety Analytics Dashboard
            </div>

            <div class="hero-subtitle">
                Monitor incident trends, classification outcomes,
                Decision Tier routing and Historical Validation
                using dynamic filters and management-ready reports.
            </div>

            <div class="hero-pill-row">

                <div class="hero-pill">
                    Date and year analysis
                </div>

                <div class="hero-pill">
                    Classification trends
                </div>

                <div class="hero-pill">
                    Decision Tier monitoring
                </div>

                <div class="hero-pill">
                    Downloadable reports
                </div>

            </div>

        </div>
        """,
        unsafe_allow_html=True,
    )


def render_empty_dashboard() -> None:

    st.markdown(
        """
        <div class="info-panel">
            <b>No incident records are currently available.</b><br/>
            Complete a Voice, Manual or Batch incident report.
            Successfully classified incidents will automatically
            appear in this dashboard.
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_filter_multiselect(
    label: str,
    dataframe: pd.DataFrame,
    column: str,
    key: str,
) -> List[str]:

    return st.multiselect(
        label,
        options=unique_options(
            dataframe,
            column,
        ),
        default=[],
        key=key,
    )


def apply_dashboard_filters(
    dashboard_df: pd.DataFrame,
    selected_filters: Dict[str, Any],
) -> pd.DataFrame:

    filtered_df = dashboard_df.copy()

    date_range = selected_filters.get(
        "date_range"
    )

    if (
        date_range
        and isinstance(
            date_range,
            (
                tuple,
                list,
            )
        )
        and len(
            date_range
        ) == 2
    ):

        start_date, end_date = (
            date_range
        )

        date_mask = (
            filtered_df[
                "EventDate Parsed"
            ].isna()
            | (
                (
                    filtered_df[
                        "EventDate Parsed"
                    ].dt.date
                    >= start_date
                )
                & (
                    filtered_df[
                        "EventDate Parsed"
                    ].dt.date
                    <= end_date
                )
            )
        )

        filtered_df = filtered_df[
            date_mask
        ]

    filter_mapping = {
        "year":
            "Year",

        "quarter":
            "Quarter",

        "month":
            "Month",

        "employer":
            "Employer",

        "state":
            "State",

        "city":
            "City",

        "reporting_channel":
            "Reporting Channel",

        "nature":
            "Nature Predicted Label",

        "body":
            "Body Predicted Label",

        "event":
            "Event Predicted Label",

        "source":
            "Source Predicted Label",

        "decision":
            "Decision",

        "historical_validation":
            "Historical Validation Status",
    }

    for filter_key, column_name in (
        filter_mapping.items()
    ):

        selected_values = (
            selected_filters.get(
                filter_key,
                []
            )
        )

        if selected_values:

            filtered_df = filtered_df[
                filtered_df[
                    column_name
                ].isin(
                    selected_values
                )
            ]

    search_text = str(
        selected_filters.get(
            "incident_search",
            "",
        )
    ).strip()

    if search_text:

        search_mask = pd.Series(
            False,
            index=filtered_df.index,
        )

        for search_column in [
            "ID",
            "Employer",
            "Final Narrative",
        ]:

            if search_column in filtered_df.columns:

                search_mask = (
                    search_mask
                    | filtered_df[
                        search_column
                    ].fillna(
                        ""
                    ).astype(
                        str
                    ).str.contains(
                        search_text,
                        case=False,
                        regex=False,
                    )
                )

        filtered_df = filtered_df[
            search_mask
        ]

    confidence_range = selected_filters.get(
        "confidence_range",
        (
            0.0,
            100.0,
        ),
    )

    if (
        confidence_range
        and len(
            confidence_range
        ) == 2
    ):

        lower_confidence, upper_confidence = (
            confidence_range
        )

        confidence_mask = (
            filtered_df[
                "Geometric Mean Confidence (%)"
            ].isna()
            | filtered_df[
                "Geometric Mean Confidence (%)"
            ].between(
                lower_confidence,
                upper_confidence,
                inclusive="both",
            )
        )

        filtered_df = filtered_df[
            confidence_mask
        ]

    return filtered_df


def render_kpi_card(
    label: str,
    value: str,
    caption: str,
) -> None:

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


def render_dashboard_kpis(
    metrics: Dict[str, Any],
) -> None:

    first_kpi_row = st.columns(
        5,
        gap="medium",
    )

    first_row_values = [
        (
            "Total Incidents",
            f"{metrics['total_incidents']:,}",
            "Filtered incident records",
        ),
        (
            "Auto Fill",
            (
                f"{metrics['auto_fill_count']:,} "
                f"({metrics['auto_fill_rate']:.1f}%)"
            ),
            "High-confidence routing",
        ),
        (
            "Suggest Review",
            (
                f"{metrics['suggest_review_count']:,} "
                f"({metrics['suggest_review_rate']:.1f}%)"
            ),
            "Reviewer confirmation required",
        ),
        (
            "Manual Review",
            (
                f"{metrics['manual_review_count']:,} "
                f"({metrics['manual_review_rate']:.1f}%)"
            ),
            "Full reviewer attention required",
        ),
        (
            "Average Confidence",
            (
                f"{metrics['average_confidence']:.2f}%"
                if pd.notna(
                    metrics[
                        "average_confidence"
                    ]
                )
                else "N/A"
            ),
            "Geometric mean confidence",
        ),
    ]

    for column, item in zip(
        first_kpi_row,
        first_row_values,
    ):

        with column:

            render_kpi_card(
                *item
            )

    st.markdown(
        "<div style='height:.8rem'></div>",
        unsafe_allow_html=True,
    )

    second_kpi_row = st.columns(
        4,
        gap="medium",
    )

    second_row_values = [
        (
            "Average Historical Score",
            (
                f"{metrics['average_historical_score']:.4f}"
                if pd.notna(
                    metrics[
                        "average_historical_score"
                    ]
                )
                else "N/A"
            ),
            "Mean historical relationship score",
        ),
        (
            "Strong Historical Support",
            (
                f"{metrics['strong_historical_rate']:.1f}%"
            ),
            "Share with strong historical support",
        ),
        (
            "Employers",
            f"{metrics['unique_employers']:,}",
            "Unique employers represented",
        ),
        (
            "States",
            f"{metrics['unique_states']:,}",
            "Unique states represented",
        ),
    ]

    for column, item in zip(
        second_kpi_row,
        second_row_values,
    ):

        with column:

            render_kpi_card(
                *item
            )


def create_bar_chart(
    dataframe: pd.DataFrame,
    column: str,
    title: str,
    maximum_categories: int = 12,
):

    if (
        column not in dataframe.columns
        or dataframe.empty
    ):

        return None

    distribution = (
        dataframe[
            column
        ]
        .replace(
            "",
            np.nan
        )
        .dropna()
        .value_counts()
        .head(
            maximum_categories
        )
        .rename_axis(
            column
        )
        .reset_index(
            name="Incident Count"
        )
    )

    if distribution.empty:

        return None

    figure = px.bar(
        distribution.sort_values(
            "Incident Count"
        ),
        x="Incident Count",
        y=column,
        orientation="h",
        title=title,
        text="Incident Count",
    )

    figure.update_layout(
        height=420,
        margin=dict(
            l=10,
            r=20,
            t=55,
            b=20,
        ),
        title_font=dict(
            size=17,
        ),
        xaxis_title="Incident Count",
        yaxis_title="",
    )

    figure.update_traces(
        textposition="outside",
        cliponaxis=False,
    )

    return figure


def render_dashboard_charts(
    filtered_df: pd.DataFrame,
) -> None:

    st.markdown(
        """
        <div class="section-kicker">
            Trend Analysis
        </div>

        <div class="section-title">
            Incident volume and routing trends
        </div>

        <div class="section-description">
            Explore how incidents and Decision Tier outcomes
            change over the selected reporting period.
        </div>
        """,
        unsafe_allow_html=True,
    )

    chart_columns = st.columns(
        2,
        gap="large",
    )

    with chart_columns[0]:

        dated_df = filtered_df[
            filtered_df[
                "EventDate Parsed"
            ].notna()
        ].copy()

        if dated_df.empty:

            st.info(
                "No valid Event Date values are available "
                "for the incident trend chart."
            )

        else:

            trend_df = (
                dated_df.groupby(
                    "Year-Month",
                    dropna=False,
                )
                .size()
                .reset_index(
                    name="Incident Count"
                )
                .sort_values(
                    "Year-Month"
                )
            )

            trend_figure = px.line(
                trend_df,
                x="Year-Month",
                y="Incident Count",
                markers=True,
                title="Incident Trend by Month",
            )

            trend_figure.update_layout(
                height=400,
                margin=dict(
                    l=10,
                    r=20,
                    t=55,
                    b=20,
                ),
                xaxis_title="Month",
                yaxis_title="Incident Count",
            )

            st.plotly_chart(
                trend_figure,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    with chart_columns[1]:

        decision_counts = (
            filtered_df[
                "Decision"
            ]
            .replace(
                "",
                np.nan
            )
            .dropna()
            .value_counts()
            .reindex(
                DECISION_ORDER,
                fill_value=0,
            )
            .rename_axis(
                "Decision Tier"
            )
            .reset_index(
                name="Incident Count"
            )
        )

        if decision_counts[
            "Incident Count"
        ].sum() == 0:

            st.info(
                "No Decision Tier values are available."
            )

        else:

            decision_figure = px.donut(
                decision_counts,
                names="Decision Tier",
                values="Incident Count",
                title="Decision Tier Distribution",
                hole=0.58,
            )

            decision_figure.update_layout(
                height=400,
                margin=dict(
                    l=10,
                    r=20,
                    t=55,
                    b=20,
                ),
                legend_title="Decision Tier",
            )

            st.plotly_chart(
                decision_figure,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    st.markdown(
        """
        <div class="section-kicker">
            Classification Analysis
        </div>

        <div class="section-title">
            Leading incident classifications
        </div>

        <div class="section-description">
            Compare the most frequent Nature, Body, Event
            and Source classifications in the filtered data.
        </div>
        """,
        unsafe_allow_html=True,
    )

    classification_charts = [
        (
            "Nature Predicted Label",
            "Nature of Injury",
        ),
        (
            "Body Predicted Label",
            "Body Part",
        ),
        (
            "Event Predicted Label",
            "Event / Exposure",
        ),
        (
            "Source Predicted Label",
            "Source of Injury",
        ),
    ]

    for chart_row_start in [
        0,
        2,
    ]:

        chart_row = st.columns(
            2,
            gap="large",
        )

        for offset, column in enumerate(
            chart_row
        ):

            chart_column, title = (
                classification_charts[
                    chart_row_start
                    + offset
                ]
            )

            with column:

                figure = create_bar_chart(
                    dataframe=filtered_df,
                    column=chart_column,
                    title=(
                        f"Top {title} Classifications"
                    ),
                )

                if figure is None:

                    st.info(
                        f"No {title} values are available."
                    )

                else:

                    st.plotly_chart(
                        figure,
                        use_container_width=True,
                        config=PLOTLY_CONFIG,
                    )

    st.markdown(
        """
        <div class="section-kicker">
            Historical and Organizational Analysis
        </div>

        <div class="section-title">
            Historical support, employers and locations
        </div>
        """,
        unsafe_allow_html=True,
    )

    organization_columns = st.columns(
        3,
        gap="large",
    )

    with organization_columns[0]:

        historical_counts = (
            filtered_df[
                "Historical Validation Status"
            ]
            .replace(
                "",
                np.nan
            )
            .dropna()
            .value_counts()
            .reindex(
                HISTORICAL_ORDER,
                fill_value=0,
            )
            .rename_axis(
                "Historical Validation"
            )
            .reset_index(
                name="Incident Count"
            )
        )

        if historical_counts[
            "Incident Count"
        ].sum() == 0:

            st.info(
                "No Historical Validation values "
                "are available."
            )

        else:

            historical_figure = px.bar(
                historical_counts,
                x="Historical Validation",
                y="Incident Count",
                title="Historical Validation Distribution",
                text="Incident Count",
            )

            historical_figure.update_layout(
                height=400,
                margin=dict(
                    l=10,
                    r=20,
                    t=55,
                    b=80,
                ),
                xaxis_title="",
                yaxis_title="Incident Count",
            )

            historical_figure.update_xaxes(
                tickangle=-20,
            )

            st.plotly_chart(
                historical_figure,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    with organization_columns[1]:

        employer_figure = create_bar_chart(
            dataframe=filtered_df,
            column="Employer",
            title="Top Employers by Incident Count",
            maximum_categories=10,
        )

        if employer_figure is None:

            st.info(
                "No Employer values are available."
            )

        else:

            st.plotly_chart(
                employer_figure,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )

    with organization_columns[2]:

        state_figure = create_bar_chart(
            dataframe=filtered_df,
            column="State",
            title="Top States by Incident Count",
            maximum_categories=10,
        )

        if state_figure is None:

            st.info(
                "No State values are available."
            )

        else:

            st.plotly_chart(
                state_figure,
                use_container_width=True,
                config=PLOTLY_CONFIG,
            )


def build_filter_description(
    selected_filters: Dict[str, Any],
) -> str:

    filter_parts = []

    for key, label in [
        (
            "year",
            "Year",
        ),
        (
            "quarter",
            "Quarter",
        ),
        (
            "month",
            "Month",
        ),
        (
            "employer",
            "Employer",
        ),
        (
            "state",
            "State",
        ),
        (
            "city",
            "City",
        ),
        (
            "reporting_channel",
            "Reporting Channel",
        ),
        (
            "nature",
            "Nature",
        ),
        (
            "body",
            "Body",
        ),
        (
            "event",
            "Event",
        ),
        (
            "source",
            "Source",
        ),
        (
            "decision",
            "Decision Tier",
        ),
        (
            "historical_validation",
            "Historical Validation",
        ),
    ]:

        selected_values = (
            selected_filters.get(
                key,
                []
            )
        )

        if selected_values:

            filter_parts.append(
                f"{label}: "
                + ", ".join(
                    str(value)
                    for value
                    in selected_values
                )
            )

    search_value = selected_filters.get(
        "incident_search"
    )

    if search_value:

        filter_parts.append(
            f"Search: {search_value}"
        )

    return (
        " | ".join(
            filter_parts
        )
        if filter_parts
        else "All available incident records"
    )


def render_incident_table_and_downloads(
    filtered_df: pd.DataFrame,
    metrics: Dict[str, Any],
    selected_filters: Dict[str, Any],
) -> None:

    st.markdown(
        """
        <div class="section-kicker">
            Incident Records
        </div>

        <div class="section-title">
            Filtered incident register
        </div>

        <div class="section-description">
            Review recent incidents and download the
            filtered records or executive summary.
        </div>
        """,
        unsafe_allow_html=True,
    )

    table_columns = [
        column
        for column in [
            "ID",
            "EventDate",
            "Employer",
            "City",
            "State",
            "Nature Predicted Label",
            "Body Predicted Label",
            "Event Predicted Label",
            "Source Predicted Label",
            "Geometric Mean Confidence (%)",
            "Decision",
            "Historical Validation Status",
            "Reporting Channel",
            "Processing Status",
        ]
        if column
        in filtered_df.columns
    ]

    display_df = filtered_df.sort_values(
        "EventDate Parsed",
        ascending=False,
        na_position="last",
    )

    st.dataframe(
        display_df[
            table_columns
        ],
        hide_index=True,
        use_container_width=True,
        height=470,
    )

    filter_description = (
        build_filter_description(
            selected_filters
        )
    )

    csv_bytes = filtered_df.to_csv(
        index=False
    ).encode(
        "utf-8-sig"
    )

    excel_bytes = create_excel_export(
        filtered_dataframe=filtered_df,
        metrics=metrics,
    )

    pdf_bytes = create_executive_pdf(
        filtered_dataframe=filtered_df,
        metrics=metrics,
        filter_description=filter_description,
    )

    download_columns = st.columns(
        3,
        gap="medium",
    )

    with download_columns[0]:

        st.download_button(
            "Download Filtered CSV",
            data=csv_bytes,
            file_name=(
                "safety_analytics_filtered_incidents.csv"
            ),
            mime="text/csv",
            use_container_width=True,
        )

    with download_columns[1]:

        st.download_button(
            "Download Analytics Excel",
            data=excel_bytes,
            file_name=(
                "safety_analytics_report.xlsx"
            ),
            mime=(
                "application/vnd.openxmlformats-"
                "officedocument.spreadsheetml.sheet"
            ),
            use_container_width=True,
        )

    with download_columns[2]:

        st.download_button(
            "Download Executive PDF",
            data=pdf_bytes,
            file_name=(
                "safety_analytics_executive_summary.pdf"
            ),
            mime="application/pdf",
            use_container_width=True,
        )


def render_analytics_dashboard_page(
    incident_data_path: Path,
) -> None:

    render_dashboard_header()

    if not incident_data_path.is_file():

        render_empty_dashboard()
        return

    try:

        raw_incident_df = pd.read_csv(
            incident_data_path,
            low_memory=False,
        )

    except Exception as error:

        st.error(
            "The incident data store could not be read. "
            f"Details: {error}"
        )

        return

    if raw_incident_df.empty:

        render_empty_dashboard()
        return

    dashboard_df = (
        clean_dashboard_dataframe(
            raw_incident_df
        )
    )

    st.markdown(
        """
        <div class="section-kicker">
            Dashboard Filters
        </div>

        <div class="section-title">
            Refine the safety analysis
        </div>

        <div class="section-description">
            Apply one or more filters. All KPI cards,
            charts, tables and downloads update together.
        </div>
        """,
        unsafe_allow_html=True,
    )

    with st.expander(
        "Open Dashboard Filters",
        expanded=True,
    ):

        filter_row_1 = st.columns(
            4,
            gap="medium",
        )

        valid_dates = dashboard_df[
            "EventDate Parsed"
        ].dropna()

        with filter_row_1[0]:

            if valid_dates.empty:

                date_range = None

                st.date_input(
                    "Event Date Range",
                    value=None,
                    disabled=True,
                )

            else:

                minimum_date = (
                    valid_dates.min().date()
                )

                maximum_date = (
                    valid_dates.max().date()
                )

                date_range = st.date_input(
                    "Event Date Range",
                    value=(
                        minimum_date,
                        maximum_date,
                    ),
                    min_value=minimum_date,
                    max_value=maximum_date,
                )

        with filter_row_1[1]:

            year_values = [
                int(value)
                for value in dashboard_df[
                    "Year"
                ].dropna().unique()
            ]

            selected_years = st.multiselect(
                "Year",
                options=sorted(
                    year_values
                ),
                default=[],
            )

        with filter_row_1[2]:

            selected_quarters = (
                render_filter_multiselect(
                    "Quarter",
                    dashboard_df,
                    "Quarter",
                    "dashboard_quarter_filter",
                )
            )

        with filter_row_1[3]:

            month_options = [
                month
                for month in [
                    "January",
                    "February",
                    "March",
                    "April",
                    "May",
                    "June",
                    "July",
                    "August",
                    "September",
                    "October",
                    "November",
                    "December",
                ]
                if month
                in unique_options(
                    dashboard_df,
                    "Month",
                )
            ]

            selected_months = st.multiselect(
                "Month",
                options=month_options,
                default=[],
            )

        filter_row_2 = st.columns(
            4,
            gap="medium",
        )

        with filter_row_2[0]:

            selected_employers = (
                render_filter_multiselect(
                    "Employer",
                    dashboard_df,
                    "Employer",
                    "dashboard_employer_filter",
                )
            )

        with filter_row_2[1]:

            selected_states = (
                render_filter_multiselect(
                    "State",
                    dashboard_df,
                    "State",
                    "dashboard_state_filter",
                )
            )

        with filter_row_2[2]:

            selected_cities = (
                render_filter_multiselect(
                    "City",
                    dashboard_df,
                    "City",
                    "dashboard_city_filter",
                )
            )

        with filter_row_2[3]:

            selected_channels = (
                render_filter_multiselect(
                    "Reporting Channel",
                    dashboard_df,
                    "Reporting Channel",
                    "dashboard_channel_filter",
                )
            )

        filter_row_3 = st.columns(
            4,
            gap="medium",
        )

        with filter_row_3[0]:

            selected_nature = (
                render_filter_multiselect(
                    "Nature",
                    dashboard_df,
                    "Nature Predicted Label",
                    "dashboard_nature_filter",
                )
            )

        with filter_row_3[1]:

            selected_body = (
                render_filter_multiselect(
                    "Body",
                    dashboard_df,
                    "Body Predicted Label",
                    "dashboard_body_filter",
                )
            )

        with filter_row_3[2]:

            selected_event = (
                render_filter_multiselect(
                    "Event",
                    dashboard_df,
                    "Event Predicted Label",
                    "dashboard_event_filter",
                )
            )

        with filter_row_3[3]:

            selected_source = (
                render_filter_multiselect(
                    "Source",
                    dashboard_df,
                    "Source Predicted Label",
                    "dashboard_source_filter",
                )
            )

        filter_row_4 = st.columns(
            4,
            gap="medium",
        )

        with filter_row_4[0]:

            decision_options = [
                decision
                for decision in DECISION_ORDER
                if decision
                in unique_options(
                    dashboard_df,
                    "Decision",
                )
            ]

            selected_decisions = (
                st.multiselect(
                    "Decision Tier",
                    options=decision_options,
                    default=[],
                )
            )

        with filter_row_4[1]:

            historical_options = [
                historical_status
                for historical_status
                in HISTORICAL_ORDER
                if historical_status
                in unique_options(
                    dashboard_df,
                    "Historical Validation Status",
                )
            ]

            selected_historical = (
                st.multiselect(
                    "Historical Validation",
                    options=historical_options,
                    default=[],
                )
            )

        with filter_row_4[2]:

            confidence_range = st.slider(
                "Overall Confidence (%)",
                min_value=0.0,
                max_value=100.0,
                value=(
                    0.0,
                    100.0,
                ),
                step=1.0,
            )

        with filter_row_4[3]:

            incident_search = st.text_input(
                "Search Incident",
                placeholder=(
                    "Incident ID, employer or narrative"
                ),
            )

    selected_filters = {
        "date_range":
            date_range,

        "year":
            selected_years,

        "quarter":
            selected_quarters,

        "month":
            selected_months,

        "employer":
            selected_employers,

        "state":
            selected_states,

        "city":
            selected_cities,

        "reporting_channel":
            selected_channels,

        "nature":
            selected_nature,

        "body":
            selected_body,

        "event":
            selected_event,

        "source":
            selected_source,

        "decision":
            selected_decisions,

        "historical_validation":
            selected_historical,

        "confidence_range":
            confidence_range,

        "incident_search":
            incident_search,
    }

    filtered_df = apply_dashboard_filters(
        dashboard_df=dashboard_df,
        selected_filters=selected_filters,
    )

    if filtered_df.empty:

        st.warning(
            "No incident records match the selected filters."
        )

        return

    metrics = calculate_dashboard_metrics(
        filtered_df
    )

    st.markdown(
        """
        <div class="section-kicker">
            Executive Overview
        </div>

        <div class="section-title">
            Filtered safety performance summary
        </div>
        """,
        unsafe_allow_html=True,
    )

    render_dashboard_kpis(
        metrics
    )

    st.markdown(
        "<div style='height:1.5rem'></div>",
        unsafe_allow_html=True,
    )

    render_dashboard_charts(
        filtered_df
    )

    st.markdown(
        "<div style='height:1.5rem'></div>",
        unsafe_allow_html=True,
    )

    render_incident_table_and_downloads(
        filtered_df=filtered_df,
        metrics=metrics,
        selected_filters=selected_filters,
    )
