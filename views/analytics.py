"""
Safety Analytics Dashboard page.
"""

from ui.guide_components import (
    render_backend_placeholder,
    render_dashboard_overview,
    render_module_header,
)


def render() -> None:
    render_module_header(
        eyebrow="Management Safety Intelligence",
        title="Safety Analytics Dashboard",
        description=(
            "Explore incident trends, classification distributions, confidence "
            "levels and decision tiers through interactive filters and charts."
        ),
        icon="📊",
    )

    render_dashboard_overview(
        description=(
            "The dashboard provides a consolidated view of workplace incident "
            "activity and classification outcomes. Users will be able to apply "
            "filters, compare trends and download selected results for further review."
        ),
        capabilities=[
            (
                "📈",
                "Incident Trends",
                "Review incident volume across dates, months, quarters and years.",
            ),
            (
                "📋",
                "Classification Analysis",
                "Explore Nature, Body, Event and Source distributions.",
            ),
            (
                "🎯",
                "Decision Analysis",
                "Compare Auto Fill, Suggest Review and Manual Review outcomes.",
            ),
            (
                "🏢",
                "Organizational Insights",
                "Analyse results by employer, state, city and reporting channel.",
            ),
            (
                "📊",
                "Confidence Insights",
                "Review confidence levels and the distribution of decision tiers.",
            ),
            (
                "⬇️",
                "Downloadable Results",
                "Export filtered records and management-ready analytical summaries.",
            ),
        ],
    )

    render_backend_placeholder(
        title="Analytics integration is next",
        description=(
            "The preserved analytics engine, filters, KPI cards, charts and "
            "downloadable summaries will be connected after this overview is approved."
        ),
    )
