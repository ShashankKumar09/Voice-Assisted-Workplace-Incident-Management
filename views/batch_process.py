"""
Batch Incident Processing page.
"""

from ui.guide_components import (
    render_backend_placeholder,
    render_module_header,
    render_user_guide,
)


def render() -> None:
    render_module_header(
        eyebrow='Bulk Incident Processing',
        title='Batch Incident Processing',
        description='Upload multiple incident records in CSV or Excel format, validate every row and export completed classification results.',
        icon='📂',
    )

    render_user_guide(
        steps=[('Download the template', 'Use the official CSV or Excel structure provided by the application.'), ('Prepare incident records', 'Enter one incident per row and preserve the required column names.'), ('Upload the file', 'Select the completed batch file for validation.'), ('Review validation results', 'Correct missing fields, invalid values or unsupported formats.'), ('Process and export', 'Run classification and download the completed batch output.')],
        note='Do not rename template columns. Each row must contain a usable Final Narrative.',
    )

    render_backend_placeholder(
        title='Batch processing integration is next',
        description='Template downloads, row-level validation, batch classification and CSV/Excel exports will be reconnected after this page structure is approved.',
    )
