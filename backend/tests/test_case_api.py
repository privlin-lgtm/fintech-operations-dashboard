"""API tests for Case Management workflow and RBAC."""

from app.core.security import create_access_token
from app.models.enums import CaseType


def _bearer(user) -> dict[str, str]:
    token = create_access_token(
        user.id, extra_claims={"role": user.role.name, "tv": user.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_full_case_lifecycle(client, make_user, make_customer):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    team_lead = await make_user(email="priya@example.com", role_name="team_lead")
    customer = await make_customer(full_name="Case Subject")

    headers = _bearer(investigator)

    create = await client.post(
        "/api/v1/cases",
        json={
            "customer_id": str(customer.id),
            "case_type": CaseType.FRAUD.value,
            "priority": "high",
        },
        headers=headers,
    )
    assert create.status_code == 201
    case_id = create.json()["id"]
    assert create.json()["status"] == "new"

    note = await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"body": "Initial review started."},
        headers=headers,
    )
    assert note.status_code == 200
    bodies = [n["body"] for n in note.json()["notes"]]
    assert "Initial review started." in bodies

    status = await client.patch(
        f"/api/v1/cases/{case_id}",
        json={"status": "in_progress"},
        headers=headers,
    )
    assert status.status_code == 200
    assert status.json()["status"] == "in_progress"

    assignee = await make_user(email="ava@example.com", role_name="analyst")
    reassign = await client.post(
        f"/api/v1/cases/{case_id}/reassign",
        json={"owner_id": str(assignee.id), "reason": "Specialist coverage"},
        headers=_bearer(team_lead),
    )
    assert reassign.status_code == 200
    assert reassign.json()["owner_id"] == str(assignee.id)

    close = await client.post(
        f"/api/v1/cases/{case_id}/close",
        json={
            "resolution_code": "fraud_confirmed",
            "closing_summary": "Account frozen and customer notified.",
            "status": "closed_resolved",
        },
        headers=headers,
    )
    assert close.status_code == 200
    assert close.json()["status"] == "closed_resolved"
    assert close.json()["closed_at"] is not None


async def test_analyst_cannot_close_case(client, make_user, make_customer):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    customer = await make_customer()

    create = await client.post(
        "/api/v1/cases",
        json={"customer_id": str(customer.id), "case_type": "dispute"},
        headers=_bearer(analyst),
    )
    case_id = create.json()["id"]

    close = await client.post(
        f"/api/v1/cases/{case_id}/close",
        json={
            "resolution_code": "no_action",
            "closing_summary": "Should fail.",
            "status": "closed_no_action",
        },
        headers=_bearer(analyst),
    )
    assert close.status_code == 403


async def test_analyst_cannot_reassign(client, make_user, make_customer):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    other = await make_user(email="other@example.com", role_name="analyst")
    customer = await make_customer()

    create = await client.post(
        "/api/v1/cases",
        json={"customer_id": str(customer.id), "case_type": "dispute"},
        headers=_bearer(analyst),
    )
    case_id = create.json()["id"]

    response = await client.post(
        f"/api/v1/cases/{case_id}/reassign",
        json={"owner_id": str(other.id), "reason": "Not allowed"},
        headers=_bearer(analyst),
    )
    assert response.status_code == 403


async def test_compliance_auditor_is_read_only(client, make_user, make_customer):
    auditor = await make_user(email="audit@example.com", role_name="compliance_auditor")
    customer = await make_customer()

    create = await client.post(
        "/api/v1/cases",
        json={"customer_id": str(customer.id), "case_type": "aml_review"},
        headers=_bearer(auditor),
    )
    assert create.status_code == 403


async def test_case_detail_includes_owner_name(client, db_session, make_user, make_customer):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    investigator.full_name = "Marcus Reed"
    await db_session.flush()
    customer = await make_customer(full_name="Owner Name Subject")

    create = await client.post(
        "/api/v1/cases",
        json={"customer_id": str(customer.id), "case_type": CaseType.FRAUD.value},
        headers=_bearer(investigator),
    )
    assert create.status_code == 201
    case_id = create.json()["id"]

    detail = await client.get(f"/api/v1/cases/{case_id}", headers=_bearer(investigator))
    assert detail.status_code == 200
    assert detail.json()["owner_id"] == str(investigator.id)
    assert detail.json()["owner_name"] == "Marcus Reed"

    note = await client.post(
        f"/api/v1/cases/{case_id}/notes",
        json={"body": "Checking the owner name survives a note."},
        headers=_bearer(investigator),
    )
    assert note.status_code == 200
    assert note.json()["owner_name"] == "Marcus Reed"


async def test_close_note_reads_resolution_in_plain_words(client, make_user, make_case):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")
    case = await make_case(owner_id=investigator.id)
    headers = _bearer(investigator)

    close = await client.post(
        f"/api/v1/cases/{case.id}/close",
        json={
            "resolution_code": "activity_explained",
            "closing_summary": "Supporting documents reconcile with the wire activity.",
            "status": "closed_no_action",
        },
        headers=headers,
    )
    assert close.status_code == 200
    # The code itself is stored as sent; only the human-read note uses words.
    assert close.json()["resolution_code"] == "activity_explained"

    detail = await client.get(f"/api/v1/cases/{case.id}", headers=headers)
    system_notes = [n["body"] for n in detail.json()["notes"] if n["is_system"]]
    assert "Case closed: Activity explained" in system_notes
    assert not any("activity_explained" in body for body in system_notes)
