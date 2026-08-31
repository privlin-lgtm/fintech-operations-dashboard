"""API-level smoke tests for Customer Management CRUD + search."""

from app.core.security import create_access_token


def _bearer(user) -> dict[str, str]:
    token = create_access_token(
        user.id, extra_claims={"role": user.role.name, "tv": user.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_admin_can_create_list_update_delete_customer(client, make_user):
    admin = await make_user(email="admin@example.com", role_name="admin")
    headers = _bearer(admin)

    create = await client.post(
        "/api/v1/customers",
        json={
            "full_name": "Jon Smith",
            "email": "jon.smith@example.com",
            "phone": "555-123-4567",
            "risk_tier": "medium",
        },
        headers=headers,
    )
    assert create.status_code == 201
    body = create.json()
    customer_id = body["id"]
    assert body["full_name"] == "Jon Smith"
    assert body["email"] == "j********@example.com"
    assert body["risk_tier"] == "medium"

    listed = await client.get(
        "/api/v1/customers",
        params={"q": "Jon", "status": "active", "sort": "full_name", "limit": 10},
        headers=headers,
    )
    assert listed.status_code == 200
    assert any(item["id"] == customer_id for item in listed.json()["items"])

    updated = await client.patch(
        f"/api/v1/customers/{customer_id}",
        json={"status": "suspended", "risk_tier": "high"},
        headers=headers,
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "suspended"
    assert updated.json()["risk_tier"] == "high"

    deleted = await client.delete(f"/api/v1/customers/{customer_id}", headers=headers)
    assert deleted.status_code == 204

    missing = await client.get(f"/api/v1/customers/{customer_id}", headers=headers)
    assert missing.status_code == 404


async def test_analyst_cannot_create_customer(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")

    response = await client.post(
        "/api/v1/customers",
        json={"full_name": "Should Fail"},
        headers=_bearer(analyst),
    )

    assert response.status_code == 403


async def test_search_filters_by_risk_tier(client, make_user, make_customer):
    admin = await make_user(email="admin@example.com", role_name="admin")
    await make_customer(full_name="Low Risk", risk_tier="low")
    await make_customer(full_name="High Risk", risk_tier="high")

    response = await client.get(
        "/api/v1/customers",
        params={"risk_tier": "high", "sort": "-created_at"},
        headers=_bearer(admin),
    )

    assert response.status_code == 200
    names = [item["full_name"] for item in response.json()["items"]]
    assert "High Risk" in names
    assert "Low Risk" not in names
