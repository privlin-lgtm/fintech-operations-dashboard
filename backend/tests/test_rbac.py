from app.core.security import create_access_token


def _bearer(user) -> dict[str, str]:
    token = create_access_token(user.id, extra_claims={"role": user.role.name, "tv": user.token_version})
    return {"Authorization": f"Bearer {token}"}


async def test_analyst_cannot_create_report_schedule(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")

    response = await client.post(
        "/api/v1/reports/schedules",
        json={"report_type": "case_volume", "cadence": "weekly", "recipients": ["lead@example.com"]},
        headers=_bearer(analyst),
    )

    assert response.status_code == 403
    assert response.headers["content-type"] == "application/problem+json"


async def test_team_lead_can_create_report_schedule(client, make_user):
    lead = await make_user(email="priya@example.com", role_name="team_lead")

    response = await client.post(
        "/api/v1/reports/schedules",
        json={"report_type": "case_volume", "cadence": "weekly", "recipients": ["lead@example.com"]},
        headers=_bearer(lead),
    )

    assert response.status_code == 201


async def test_analyst_can_still_read_the_dashboard(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")

    response = await client.get("/api/v1/reports/dashboard", headers=_bearer(analyst))

    assert response.status_code == 200
