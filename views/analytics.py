"""
Safety Analytics Dashboard page.
"""

from ui.guide_components import (
    render_backend_placeholder,
    render_module_header,
    render_user_guide,
)


def render() -> None:
    render_module_header(
        eyebrow='Management Safety Intelligence',
        title='Safety Analytics Dashboard',
        description='Explore incident trends, classification distributions, confidence levels and decision tiers through interactive filters and charts.',
        icon='📊',
    )

    render_user_guide(
        steps=[('Select the reporting period', 'Filter incidents by date, year, quarter or month.'), ('Apply business filters', 'Narrow results by employer, state, city or reporting channel.'), ('Review KPI summaries', 'Check incident volume, decision tiers and confidence measures.'), ('Explore category trends', 'Review Nature, Body, Event and Source distributions.'), ('Download filtered results', 'Export the selected incident records and analytics summaries.')],
        note='Dashboard results reflect the currently selected filters. Clear filters to return to the complete incident dataset.',
    )

    render_backend_placeholder(
        title='Analytics integration is next',
        description='The preserved analytics engine, filters, KPI cards, charts and downloadable summaries will be connected after the module guide is approved.',
    )
