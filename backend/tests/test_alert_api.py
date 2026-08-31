"""API tests for Alert Management workflow and RBAC."""

from app.core.security import create_access_token
from app.models.enums import AlertSeverity, AlertType


def _bearer(user) -> dict[str, str]:
    token = create_access_token(
        user.id, extra_claims={"role": user.role.name, "tv": user.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_alert_workflow_create_assign_escalate_resolve(
    client, make_user, make_customer
):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    customer = await make_customer(full_name="Alert Subject")

    create = await client.post(
        "/api/v1/alerts",
        json={
            "customer_id": str(customer.id),
            "alert_type": AlertType.HIGH_RISK_TXN.value,
            "severity": AlertSeverity.HIGH.value,
            "triggering_reason": "Transaction over threshold",
        },
        headers=_bearer(investigator),
    )
    assert create.status_code == 201
    alert_id = create.json()["id"]
    assert create.json()["status"] == "new"

    assign = await client.post(
        f"/api/v1/alerts/{alert_id}/assign",
        json={"assignee_id": str(analyst.id)},
        headers=_bearer(investigator),
    )
    assert assign.status_code == 200
    assert assign.json()["status"] == "assigned"
    assert assign.json()["assignee_id"] == str(analyst.id)

    escalate = await client.post(
        f"/api/v1/alerts/{alert_id}/escalate",
        json={"create_case": True, "case_type": "fraud", "priority": "high"},
        headers=_bearer(investigator),
    )
    assert escalate.status_code == 200
    assert escalate.json()["status"] == "escalated"
    assert escalate.json()["case_id"] is not None

    resolve = await client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"reason": "Investigation complete — no further action"},
        headers=_bearer(investigator),
    )
    assert resolve.status_code == 200
    assert resolve.json()["status"] == "resolved"
    assert resolve.json()["resolved_at"] is not None


async def test_analyst_cannot_create_alert(client, make_user, make_customer):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    customer = await make_customer()

    response = await client.post(
        "/api/v1/alerts",
        json={
            "customer_id": str(customer.id),
            "alert_type": "velocity",
            "severity": "medium",
            "triggering_reason": "Should fail",
        },
        headers=_bearer(analyst),
    )
    assert response.status_code == 403


async def test_search_alerts_by_severity(client, make_user, make_customer):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    customer = await make_customer()

    await client.post(
        "/api/v1/alerts",
        json={
            "customer_id": str(customer.id),
            "alert_type": "velocity",
            "severity": "critical",
            "triggering_reason": "Critical velocity breach",
        },
        headers=_bearer(investigator),
    )

    response = await client.get(
        "/api/v1/alerts",
        params={"severity": "critical", "q": "velocity", "sort": "-created_at"},
        headers=_bearer(investigator),
    )
    assert response.status_code == 200
    assert len(response.json()["items"]) >= 1
    assert response.json()["items"][0]["severity"] == "critical"


async def test_compliance_auditor_cannot_resolve(client, make_user, make_customer):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    auditor = await make_user(email="audit@example.com", role_name="compliance_auditor")
    customer = await make_customer()

    create = await client.post(
        "/api/v1/alerts",
        json={
            "customer_id": str(customer.id),
            "alert_type": "manual_watchlist",
            "severity": "low",
            "triggering_reason": "Watchlist hit",
        },
        headers=_bearer(investigator),
    )
    alert_id = create.json()["id"]

    response = await client.post(
        f"/api/v1/alerts/{alert_id}/resolve",
        json={"reason": "Should be blocked"},
        headers=_bearer(auditor),
    )
    assert response.status_code == 403
