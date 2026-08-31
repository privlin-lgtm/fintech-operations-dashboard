import csv
import io
from typing import Any

from fastapi.responses import Response, StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

_FORMULA_TRIGGER_CHARS = ("=", "+", "-", "@", "\t", "\r")


def _escape_csv_formula(value: Any) -> Any:
    """Neutralize CSV/formula injection: a leading =, +, -, @ (or tab/CR) is
    interpreted as a formula by Excel/Sheets when the file is opened, so
    prefix such values with a literal-text marker."""
    if isinstance(value, str) and value.startswith(_FORMULA_TRIGGER_CHARS):
        return "'" + value
    return value


def rows_to_csv(rows: list[dict[str, Any]], fieldnames: list[str]) -> StreamingResponse:
    buffer = io.StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames, extrasaction="ignore")
    writer.writeheader()
    for row in rows:
        writer.writerow({key: _escape_csv_formula(row.get(key)) for key in fieldnames})
    buffer.seek(0)
    return StreamingResponse(
        iter([buffer.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=report.csv"},
    )


def rows_to_pdf(
    *,
    title: str,
    columns: list[str],
    rows: list[dict[str, Any]],
    filename: str = "report.pdf",
) -> Response:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    elements: list[Any] = [Paragraph(title, styles["Title"]), Spacer(1, 12)]

    table_data = [columns]
    for row in rows:
        table_data.append([str(row.get(column, "")) for column in columns])

    table = Table(table_data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a5f")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f5f7fa")]),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return Response(
        content=buffer.getvalue(),
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
