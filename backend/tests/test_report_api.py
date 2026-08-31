"""API tests for reporting endpoints."""

from datetime import UTC, datetime, timedelta

from app.core.security import create_access_token


def _bearer(user) -> dict[str, str]:
    token = create_access_token(
        user.id, extra_claims={"role": user.role.name, "tv": user.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_daily_transactions_report(client, make_user, make_transaction):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    await make_transaction(amount_cents=10_000, status="settled")
    await make_transaction(amount_cents=20_000, status="pending")

    response = await client.get(
        "/api/v1/reports/transactions",
        params={"group_by": "status"},
        headers=_bearer(analyst),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["report_type"] == "daily_transactions"
    assert body["total_count"] == 2
    assert body["total_amount_cents"] == 30_000
    groups = {row["group"]: row["count"] for row in body["rows"]}
    assert groups["settled"] == 1
    assert groups["pending"] == 1


async def test_case_volume_report(client, make_user, make_case):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    await make_case(status="new")
    await make_case(status="new")
    await make_case(status="in_progress")

    response = await client.get(
        "/api/v1/reports/cases",
        params={"group_by": "status"},
        headers=_bearer(investigator),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 3
    groups = {row["group"]: row["count"] for row in body["rows"]}
    assert groups["new"] == 2
    assert groups["in_progress"] == 1


async def test_alert_volume_report(client, make_user, make_alert):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    await make_alert(status="new", severity="high")
    await make_alert(status="resolved", severity="low", resolved_at=datetime.now(UTC))

    response = await client.get(
        "/api/v1/reports/alerts",
        params={"group_by": "status"},
        headers=_bearer(investigator),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_count"] == 2
    groups = {row["group"]: row["count"] for row in body["rows"]}
    assert groups["new"] == 1
    assert groups["resolved"] == 1


async def test_sla_performance_report(client, make_user, make_case):
    team_lead = await make_user(email="priya@example.com", role_name="team_lead")
    now = datetime.now(UTC)

    await make_case(
        status="closed_resolved",
        priority="critical",
        sla_due_at=now - timedelta(hours=1),
        closed_at=now - timedelta(hours=2),
    )
    await make_case(
        status="closed_resolved",
        priority="critical",
        sla_due_at=now - timedelta(hours=1),
        closed_at=now + timedelta(minutes=1),
    )

    response = await client.get(
        "/api/v1/reports/sla",
        params={"group_by": "priority"},
        headers=_bearer(team_lead),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["total_closed"] == 2
    assert body["met_sla"] == 1
    assert body["missed_sla"] == 1
    assert body["compliance_rate"] == 0.5


async def test_transaction_report_csv_export(client, make_user, make_transaction):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    await make_transaction()

    response = await client.get(
        "/api/v1/reports/transactions",
        params={"group_by": "status", "format": "csv"},
        headers=_bearer(analyst),
    )

    assert response.status_code == 200
    assert "text/csv" in response.headers["content-type"]
    assert "group,count,total_amount_cents" in response.text


async def test_case_report_pdf_export(client, make_user, make_case):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    await make_case()

    response = await client.get(
        "/api/v1/reports/cases",
        params={"group_by": "status", "format": "pdf"},
        headers=_bearer(investigator),
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/pdf"
    assert response.content.startswith(b"%PDF")


async def test_invalid_group_by_returns_422(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")

    response = await client.get(
        "/api/v1/reports/cases",
        params={"group_by": "owner_id"},
        headers=_bearer(analyst),
    )

    assert response.status_code == 422


async def test_compliance_auditor_can_read_reports(client, make_user):
    auditor = await make_user(email="auditor@example.com", role_name="compliance_auditor")

    response = await client.get("/api/v1/reports/alerts", headers=_bearer(auditor))

    assert response.status_code == 200
