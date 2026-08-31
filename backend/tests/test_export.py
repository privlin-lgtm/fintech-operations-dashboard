from app.core.export import rows_to_csv


async def test_rows_to_csv_escapes_formula_injection_characters():
    rows = [
        {"name": "=cmd|'/c calc'!A1", "note": "+SUM(1,2)"},
        {"name": "-2+3", "note": "@SUM(A1:A2)"},
        {"name": "Ordinary Name", "note": "Nothing suspicious"},
    ]

    response = rows_to_csv(rows, fieldnames=["name", "note"])
    text = "".join([chunk async for chunk in response.body_iterator])

    assert "'=cmd" in text
    assert "'+SUM(1,2)" in text
    assert "'-2+3" in text
    assert "'@SUM(A1:A2)" in text
    # Values with no leading trigger character are left untouched.
    assert "Ordinary Name" in text
    assert "'Ordinary Name" not in text
