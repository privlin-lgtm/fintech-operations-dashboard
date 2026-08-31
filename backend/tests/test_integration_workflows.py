"""Cross-module integration tests using realistic fintech operations workflows.

Each test exercises multiple API surfaces in sequence — mirroring how an
analyst/investigator would move through auth, customer lookup, transaction
review, alert triage, case investigation, and operational reporting.
"""

from datetime import UTC, datetime, timedelta

import pytest

from tests.helpers import (
    DEFAULT_PASSWORD,
    auth_headers_from_tokens,
    bearer_headers,
    login,
)


@pytest.fixture
async def ops_team(make_user):
    """Standard operations desk roles used across integration scenarios."""
    return {
        "admin": await make_user(email="admin@example.com", role_name="admin"),
        "investigator": await make_user(email="marcus@example.com", role_name="investigator"),
        "analyst": await make_user(email="ava@example.com", role_name="analyst"),
        "team_lead": await make_user(email="priya@example.com", role_name="team_lead"),
        "auditor": await make_user(
            email="auditor@example.com", role_name="compliance_auditor"
        ),
    }


# ---------------------------------------------------------------------------
# Authentication
# ---------------------------------------------------------------------------


async def test_auth_session_lifecycle(client, ops_team):
    """Analyst signs in, refreshes tokens, accesses /me, then logs out."""
    analyst = ops_team["analyst"]

    tokens = await login(client, email=analyst.email)
    headers = auth_headers_from_tokens(tokens)

    me = await client.get("/api/v1/auth/me", headers=headers)
    assert me.status_code == 200
    assert me.json()["email"] == analyst.email
    assert me.json()["role"]["name"] == "analyst"

    old_refresh_cookie = client.cookies.get("refresh_token")

    refreshed = await client.post("/api/v1/auth/refresh")
    assert refreshed.status_code == 200
    new_tokens = refreshed.json()
    assert client.cookies.get("refresh_token") != old_refresh_cookie

    logout = await client.post(
        "/api/v1/auth/logout",
        headers=auth_headers_from_tokens(new_tokens),
    )
    assert logout.status_code == 204

    stale = await client.get("/api/v1/auth/me", headers=auth_headers_from_tokens(new_tokens))
    assert stale.status_code == 401


async def test_invalid_credentials_rejected_before_any_module_access(client, make_user):
    await make_user(email="ava@example.com", password=DEFAULT_PASSWORD)

    login_resp = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "wrong-password"},
    )
    assert login_resp.status_code == 401

    protected = await client.get("/api/v1/customers")
    assert protected.status_code == 401


# ---------------------------------------------------------------------------
# Customer search
# ---------------------------------------------------------------------------


async def test_customer_onboarding_and_search_workflow(client, ops_team):
    """Team lead onboards a customer; analyst searches and opens the profile."""
    admin = ops_team["admin"]
    analyst = ops_team["analyst"]

    created = await client.post(
        "/api/v1/customers",
        json={
            "full_name": "Meridian Capital LLC",
            "email": "treasury@meridian-capital.example",
            "phone": "555-010-2000",
            "risk_tier": "high",
            "kyc_status": "verified",
        },
        headers=bearer_headers(admin),
    )
    assert created.status_code == 201
    customer_id = created.json()["id"]
    assert created.json()["email"].startswith("t")

    search = await client.get(
        "/api/v1/customers",
        params={"q": "Meridian", "risk_tier": "high", "sort": "full_name"},
        headers=bearer_headers(analyst),
    )
    assert search.status_code == 200
    assert any(item["id"] == customer_id for item in search.json()["items"])

    profile = await client.get(
        f"/api/v1/customers/{customer_id}",
        headers=bearer_headers(analyst),
    )
    assert profile.status_code == 200
    body = profile.json()
    assert body["full_name"] == "Meridian Capital LLC"
    assert body["risk_tier"] == "high"
    assert body["account_count"] == 0


# ---------------------------------------------------------------------------
# Transaction lookup
# ---------------------------------------------------------------------------


async def test_transaction_lookup_for_suspicious_wire(
    client, ops_team, make_customer, make_account, make_transaction
):
    """Analyst traces a large outbound wire back to the customer account."""
    analyst = ops_team["analyst"]
    customer = await make_customer(full_name="Meridian Capital LLC", risk_tier="high")
    account = await make_account(
        customer_id=customer.id,
        account_type="checking",
        masked_number="**** 8821",
    )
    txn = await make_transaction(
        account_id=account.id,
        amount_cents=750_000_00,
        direction="debit",
        channel="wire",
        status="pending",
        counterparty_masked="OFFSHORE HOLDINGS **** 3399",
        risk_score=92.5,
    )

    search = await client.get(
        "/api/v1/transactions",
        params={
            "customer_id": str(customer.id),
            "channel": "wire",
            "min_amount": 500_000_00,
            "sort": "-amount_cents",
        },
        headers=bearer_headers(analyst),
    )
    assert search.status_code == 200
    items = search.json()["items"]
    assert items[0]["id"] == str(txn.id)
    assert items[0]["amount_cents"] == 750_000_00

    counterparty_search = await client.get(
        "/api/v1/transactions",
        params={"q": "OFFSHORE", "sort": "-created_at"},
        headers=bearer_headers(analyst),
    )
    assert any(item["id"] == str(txn.id) for item in counterparty_search.json()["items"])

    detail = await client.get(
        f"/api/v1/transactions/{txn.id}",
        headers=bearer_headers(analyst),
    )
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["account"]["customer_id"] == str(customer.id)
    assert payload["account"]["masked_number"] == "**** 8821"
    assert payload["status_history"]


# ---------------------------------------------------------------------------
# Case management
# ---------------------------------------------------------------------------


async def test_case_investigation_workflow(
    client, ops_team, make_customer, make_account, make_transaction
):
    """Investigator opens a fraud case, links transaction evidence, and closes it."""
    investigator = ops_team["investigator"]
    team_lead = ops_team["team_lead"]
    analyst = ops_team["analyst"]
    customer = await make_customer(full_name="Case Subject Corp")
    account = await make_account(customer_id=customer.id)
    txn = await make_transaction(
        account_id=account.id,
        amount_cents=125_000_00,
        channel="card",
        status="settled",
    )
    headers = bearer_headers(investigator)

    opened = await client.post(
        "/api/v1/cases",
        json={
            "customer_id": str(customer.id),
            "case_type": "fraud",
            "priority": "high",
        },
        headers=headers,
    )
    assert opened.status_code == 201
    case_id = opened.json()["id"]
    assert opened.json()["sla_due_at"] is not None

    await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"body": "Card-not-present pattern matches prior fraud ring."},
        headers=headers,
    )
    await client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "in_progress"},
        headers=headers,
    )
    await client.post(
        f"/api/v1/cases/{case_id}/links",
        json={"transaction_id": str(txn.id)},
        headers=headers,
    )
    await client.post(
        f"/api/v1/cases/{case_id}/reassign",
        json={"owner_id": str(analyst.id), "reason": "Card fraud specialist"},
        headers=bearer_headers(team_lead),
    )

    closed = await client.post(
        f"/api/v1/cases/{case_id}/close",
        json={
            "resolution_code": "fraud_confirmed",
            "closing_summary": "Confirmed unauthorized card use; account restricted.",
            "status": "closed_resolved",
        },
        headers=headers,
    )
    assert closed.status_code == 200
    assert closed.json()["status"] == "closed_resolved"

    detail = await client.get(f"/api/v1/cases/{case_id}", headers=headers)
    assert detail.status_code == 200
    assert len(detail.json()["notes"]) >= 2


# ---------------------------------------------------------------------------
# Alerts
# ---------------------------------------------------------------------------


async def test_alert_triage_and_resolution_workflow(client, ops_team, make_customer):
    """Investigator triages a sanctions alert through assign → escalate → resolve."""
    investigator = ops_team["investigator"]
    analyst = ops_team["analyst"]
    customer = await make_customer(full_name="Global Trade Partners")

    create = await client.post(
        "/api/v1/alerts",
        json={
            "customer_id": str(customer.id),
            "alert_type": "sanctions_match",
            "severity": "critical",
            "triggering_reason": "Potential OFAC match on beneficiary name",
        },
        headers=bearer_headers(investigator),
    )
    assert create.status_code == 201
    alert_id = create.json()["id"]

    assigned = await client.post(
        f"/api/v1/alerts/{alert_id}/assign",
        json={"assignee_id": str(analyst.id)},
        headers=bearer_headers(investigator),
    )
    assert assigned.json()["status"] == "assigned"

    escalated = await client.post(
        f"/api/v1/alerts/{alert_id}/escalate",
        json={"create_case": True, "case_type": "aml_review", "priority": "critical"},
        headers=bearer_headers(investigator),
    )
    assert escalated.status_code == 200
    assert escalated.json()["status"] == "escalated"
    case_id = escalated.json()["case_id"]
    assert case_id is not None

    resolved = await client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"reason": "False positive — beneficiary cleared against OFAC SDN list"},
        headers=bearer_headers(investigator),
    )
    assert resolved.status_code == 200
    assert resolved.json()["status"] == "resolved"

    queue = await client.get(
        "/api/v1/alerts",
        params={"status": "resolved", "q": "OFAC"},
        headers=bearer_headers(investigator),
    )
    assert any(item["id"] == alert_id for item in queue.json()["items"])

    case_detail = await client.get(
        f"/api/v1/cases/{case_id}",
        headers=bearer_headers(investigator),
    )
    assert case_detail.status_code == 200


# ---------------------------------------------------------------------------
# Reports
# ---------------------------------------------------------------------------


async def test_operational_reports_snapshot(
    client, ops_team, make_customer, make_account, make_transaction, make_case, make_alert
):
    """Team lead reviews dashboard KPIs and volume reports after desk activity."""
    team_lead = ops_team["team_lead"]
    headers = bearer_headers(team_lead)
    now = datetime.now(UTC)

    customer = await make_customer(full_name="Report Subject", risk_tier="medium")
    account = await make_account(customer_id=customer.id)
    await make_transaction(account_id=account.id, amount_cents=50_000, status="settled")
    await make_transaction(account_id=account.id, amount_cents=15_000, status="pending")
    await make_case(status="in_progress", priority="high", customer_id=customer.id)
    await make_case(
        status="closed_resolved",
        priority="critical",
        customer_id=customer.id,
        sla_due_at=now - timedelta(hours=2),
        closed_at=now - timedelta(hours=3),
    )
    await make_alert(status="new", severity="high", customer_id=customer.id)
    await make_alert(
        status="resolved",
        severity="low",
        customer_id=customer.id,
        resolved_at=now,
    )

    dashboard = await client.get("/api/v1/reports/dashboard", headers=headers)
    assert dashboard.status_code == 200
    dash = dashboard.json()
    assert dash["open_cases"] >= 1
    assert dash["new_alerts"] >= 1

    txn_report = await client.get(
        "/api/v1/reports/transactions",
        params={"group_by": "status"},
        headers=headers,
    )
    assert txn_report.status_code == 200
    assert txn_report.json()["total_count"] >= 2

    case_report = await client.get(
        "/api/v1/reports/cases",
        params={"group_by": "status"},
        headers=headers,
    )
    assert case_report.status_code == 200
    assert case_report.json()["total_count"] >= 2

    alert_report = await client.get(
        "/api/v1/reports/alerts",
        params={"group_by": "status"},
        headers=headers,
    )
    assert alert_report.status_code == 200
    assert alert_report.json()["total_count"] >= 2

    sla_report = await client.get(
        "/api/v1/reports/sla",
        params={"group_by": "priority"},
        headers=headers,
    )
    assert sla_report.status_code == 200
    assert sla_report.json()["total_closed"] >= 1

    csv_export = await client.get(
        "/api/v1/reports/transactions",
        params={"group_by": "status", "format": "csv"},
        headers=headers,
    )
    assert csv_export.status_code == 200
    assert "text/csv" in csv_export.headers["content-type"]

    auditor_headers = bearer_headers(ops_team["auditor"])
    auditor_dashboard = await client.get("/api/v1/reports/dashboard", headers=auditor_headers)
    assert auditor_dashboard.status_code == 200


# ---------------------------------------------------------------------------
# End-to-end fraud investigation
# ---------------------------------------------------------------------------


async def test_end_to_end_suspicious_wire_investigation(
    client, ops_team, make_account, make_transaction
):
    """Full desk workflow: onboard → wire review → alert → case → reports."""
    admin = ops_team["admin"]
    investigator = ops_team["investigator"]
    analyst = ops_team["analyst"]
    team_lead = ops_team["team_lead"]

    tokens = await login(client, email=investigator.email)
    inv_headers = auth_headers_from_tokens(tokens)

    onboarded = await client.post(
        "/api/v1/customers",
        json={
            "full_name": "Apex Import Export Ltd",
            "email": "payments@apex-import.example",
            "risk_tier": "high",
            "kyc_status": "verified",
        },
        headers=bearer_headers(admin),
    )
    assert onboarded.status_code == 201
    customer_id = onboarded.json()["id"]

    account = await make_account(
        customer_id=customer_id,
        masked_number="**** 7102",
        account_type="checking",
    )
    wire = await make_transaction(
        account_id=account.id,
        amount_cents=980_000_00,
        direction="debit",
        channel="wire",
        status="pending",
        counterparty_masked="SHELL TRADING **** 1100",
        risk_score=88.0,
    )

    customer_search = await client.get(
        "/api/v1/customers",
        params={"q": "Apex", "risk_tier": "high"},
        headers=bearer_headers(analyst),
    )
    assert any(item["id"] == customer_id for item in customer_search.json()["items"])

    txn_search = await client.get(
        "/api/v1/transactions",
        params={
            "customer_id": customer_id,
            "channel": "wire",
            "min_amount": 500_000_00,
            "sort": "-amount_cents",
        },
        headers=bearer_headers(analyst),
    )
    assert txn_search.json()["items"][0]["id"] == str(wire.id)

    alert_resp = await client.post(
        "/api/v1/alerts",
        json={
            "customer_id": customer_id,
            "transaction_id": str(wire.id),
            "alert_type": "high_risk_txn",
            "severity": "critical",
            "triggering_reason": "Outbound wire exceeds daily threshold to high-risk corridor",
        },
        headers=inv_headers,
    )
    assert alert_resp.status_code == 201
    alert_id = alert_resp.json()["id"]

    await client.post(
        f"/api/v1/alerts/{alert_id}/assign",
        json={"assignee_id": str(analyst.id)},
        headers=inv_headers,
    )
    escalated = await client.post(
        f"/api/v1/alerts/{alert_id}/escalate",
        json={"create_case": True, "case_type": "fraud", "priority": "critical"},
        headers=inv_headers,
    )
    case_id = escalated.json()["case_id"]

    await client.post(
        f"/api/v1/cases/{case_id}/links",
        json={"transaction_id": str(wire.id), "alert_id": alert_id},
        headers=inv_headers,
    )
    await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"body": "Beneficiary account flagged in prior shell-company investigation."},
        headers=inv_headers,
    )
    await client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "in_progress"},
        headers=inv_headers,
    )
    await client.post(
        f"/api/v1/cases/{case_id}/close",
        json={
            "resolution_code": "fraud_confirmed",
            "closing_summary": "Wire blocked; customer account suspended pending review.",
            "status": "closed_resolved",
        },
        headers=inv_headers,
    )
    await client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"reason": "Wire blocked and case closed — confirmed fraud typology"},
        headers=inv_headers,
    )

    profile = await client.get(
        f"/api/v1/customers/{customer_id}",
        headers=bearer_headers(analyst),
    )
    assert profile.json()["open_alert_count"] == 0
    assert profile.json()["total_case_count"] >= 1
    assert len(profile.json()["recent_alerts"]) >= 1

    txn_detail = await client.get(
        f"/api/v1/transactions/{wire.id}",
        headers=bearer_headers(analyst),
    )
    assert txn_detail.json()["has_open_case"] is False

    dashboard = await client.get("/api/v1/reports/dashboard", headers=bearer_headers(team_lead))
    assert dashboard.status_code == 200
    assert dashboard.json()["cases_closed_today"] >= 1

    case_volume = await client.get(
        "/api/v1/reports/cases",
        params={"group_by": "case_type"},
        headers=bearer_headers(team_lead),
    )
    assert case_volume.json()["total_count"] >= 1

    alert_volume = await client.get(
        "/api/v1/reports/alerts",
        params={"group_by": "severity"},
        headers=bearer_headers(team_lead),
    )
    assert alert_volume.json()["total_count"] >= 1
