"""API tests for the assignable-users list behind the Reassign/Assign pickers."""

from datetime import UTC, datetime

from tests.helpers import bearer_headers

URL = "/api/v1/users/assignable"


async def _named_user(make_user, db_session, *, email: str, role_name: str, full_name: str):
    user = await make_user(email=email, role_name=role_name)
    user.full_name = full_name
    await db_session.flush()
    return user


async def test_lists_active_assignable_users_by_name(client, make_user, db_session):
    lead = await _named_user(make_user, db_session, email="lead@example.com", role_name="team_lead", full_name="Priya Lead")
    analyst = await _named_user(make_user, db_session, email="ava@example.com", role_name="analyst", full_name="Ava Analyst")
    investigator = await _named_user(
        make_user, db_session, email="marcus@example.com", role_name="investigator", full_name="Marcus Investigator"
    )

    response = await client.get(URL, headers=bearer_headers(lead))

    assert response.status_code == 200
    body = response.json()
    ours = [row for row in body if row["id"] in {str(lead.id), str(analyst.id), str(investigator.id)}]
    assert ours == [
        {"id": str(analyst.id), "full_name": "Ava Analyst", "role": "analyst"},
        {"id": str(investigator.id), "full_name": "Marcus Investigator", "role": "investigator"},
        {"id": str(lead.id), "full_name": "Priya Lead", "role": "team_lead"},
    ]
    # Only what a picker needs: no email, status or login data.
    assert set(body[0]) == {"id", "full_name", "role"}


async def test_excludes_inactive_deleted_and_read_only_users(client, make_user, db_session):
    lead = await make_user(email="lead@example.com", role_name="team_lead")
    auditor = await make_user(email="audit@example.com", role_name="compliance_auditor")
    deactivated = await make_user(email="gone@example.com", role_name="analyst")
    deactivated.status = "deactivated"
    deleted = await make_user(email="deleted@example.com", role_name="investigator")
    deleted.deleted_at = datetime.now(UTC)
    await db_session.flush()

    response = await client.get(URL, headers=bearer_headers(lead))

    assert response.status_code == 200
    ids = {row["id"] for row in response.json()}
    assert str(lead.id) in ids
    assert str(auditor.id) not in ids
    assert str(deactivated.id) not in ids
    assert str(deleted.id) not in ids


async def test_investigator_can_list_for_alert_assignment(client, make_user):
    investigator = await make_user(email="marcus@example.com", role_name="investigator")

    response = await client.get(URL, headers=bearer_headers(investigator))

    assert response.status_code == 200


async def test_analyst_and_auditor_are_forbidden(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    auditor = await make_user(email="audit@example.com", role_name="compliance_auditor")

    for user in (analyst, auditor):
        response = await client.get(URL, headers=bearer_headers(user))
        assert response.status_code == 403
        assert response.headers["content-type"] == "application/problem+json"


async def test_requires_authentication(client):
    response = await client.get(URL)

    assert response.status_code == 401
