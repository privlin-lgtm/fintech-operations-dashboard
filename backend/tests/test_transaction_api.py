"""API tests for Transaction lookup."""

from app.core.security import create_access_token


def _bearer(user) -> dict[str, str]:
    token = create_access_token(
        user.id, extra_claims={"role": user.role.name, "tv": user.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


async def test_search_and_get_transaction_detail(
    client, make_user, make_customer, make_account, make_transaction
):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    customer = await make_customer(full_name="Jon Smith")
    account = await make_account(customer_id=customer.id, masked_number="**** 9911")
    txn = await make_transaction(
        account_id=account.id,
        amount_cents=25_000,
        direction="debit",
        channel="card",
        status="settled",
        counterparty_masked="MERCHANT **** 8822",
    )

    headers = _bearer(analyst)

    search = await client.get(
        "/api/v1/transactions",
        params={
            "customer_id": str(customer.id),
            "channel": "card",
            "min_amount": 1000,
            "sort": "-amount_cents",
            "limit": 10,
        },
        headers=headers,
    )
    assert search.status_code == 200
    body = search.json()
    assert any(item["id"] == str(txn.id) for item in body["items"])
    assert body["items"][0]["amount_cents"] == 25_000

    detail = await client.get(f"/api/v1/transactions/{txn.id}", headers=headers)
    assert detail.status_code == 200
    payload = detail.json()
    assert payload["account"]["masked_number"] == "**** 9911"
    assert payload["account"]["customer_id"] == str(customer.id)
    assert payload["status_history"]
    assert payload["counterparty_masked"] == "MERCHANT **** 8822"


async def test_search_by_query_matches_counterparty(
    client, make_user, make_transaction
):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    txn = await make_transaction(counterparty_masked="ACME CORP **** 5544")

    response = await client.get(
        "/api/v1/transactions",
        params={"q": "ACME", "sort": "-created_at"},
        headers=_bearer(analyst),
    )

    assert response.status_code == 200
    ids = [item["id"] for item in response.json()["items"]]
    assert str(txn.id) in ids


async def test_get_transaction_not_found(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")
    from uuid import uuid4

    response = await client.get(
        f"/api/v1/transactions/{uuid4()}",
        headers=_bearer(analyst),
    )
    assert response.status_code == 404
