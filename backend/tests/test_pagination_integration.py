from datetime import UTC, datetime, timedelta

from app.core.security import create_access_token


def _bearer(user) -> dict[str, str]:
    token = create_access_token(user.id, extra_claims={"role": user.role.name, "tv": user.token_version})
    return {"Authorization": f"Bearer {token}"}


async def test_customer_search_keyset_pagination_covers_every_row_once(
    client, make_user, make_customer
):
    actor = await make_user()
    base = datetime.now(UTC)
    names = ["Customer E", "Customer D", "Customer C", "Customer B", "Customer A"]
    for i, name in enumerate(names):
        await make_customer(full_name=name, created_at=base - timedelta(seconds=i))

    headers = _bearer(actor)
    seen_names: list[str] = []
    cursor = None

    for _ in range(10):  # generous upper bound; a real bug would loop forever otherwise
        params = {"limit": 2}
        if cursor:
            params["cursor"] = cursor
        response = await client.get("/api/v1/customers", params=params, headers=headers)
        assert response.status_code == 200
        body = response.json()
        seen_names.extend(item["full_name"] for item in body["items"])
        cursor = body["next_cursor"]
        if cursor is None:
            break

    assert seen_names == names  # newest first, no duplicates, no gaps
    assert len(seen_names) == len(set(seen_names))


async def test_invalid_cursor_returns_400_not_500(client, make_user):
    actor = await make_user()
    response = await client.get(
        "/api/v1/customers", params={"cursor": "not-a-real-cursor"}, headers=_bearer(actor)
    )
    assert response.status_code == 400
    assert response.headers["content-type"] == "application/problem+json"
