import pytest
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token
from app.models.case import Case
from app.models.customer import Customer
from app.repositories.case import CaseRepository


def _bearer(user) -> dict[str, str]:
    token = create_access_token(user.id, extra_claims={"role": user.role.name, "tv": user.token_version})
    return {"Authorization": f"Bearer {token}"}


async def test_db_rejects_duplicate_customer_email(db_session, make_customer):
    """ux_customers_email_active is the real guard — the service-level
    get_by_email() pre-check is only a fast path, not the source of truth."""
    await make_customer(email="dup@example.com")

    dupe = Customer(full_name="Someone Else", email="dup@example.com")
    db_session.add(dupe)

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_create_customer_endpoint_rejects_duplicate_email_without_leaking_it(
    client, make_user
):
    admin = await make_user(email="admin@example.com", role_name="admin")
    headers = _bearer(admin)
    payload = {"full_name": "Ada Lovelace", "email": "ada@example.com"}

    first = await client.post("/api/v1/customers", json=payload, headers=headers)
    assert first.status_code == 201

    second = await client.post("/api/v1/customers", json=payload, headers=headers)
    assert second.status_code == 409
    assert "ada@example.com" not in second.text


async def test_analyst_cannot_create_customer(client, make_user):
    analyst = await make_user(email="ava@example.com", role_name="analyst")

    response = await client.post(
        "/api/v1/customers",
        json={"full_name": "Ada Lovelace", "email": "ada@example.com"},
        headers=_bearer(analyst),
    )

    assert response.status_code == 403


async def test_delete_customer_blocked_by_open_case(client, make_user, make_customer, db_session):
    admin = await make_user(email="admin@example.com", role_name="admin")
    customer = await make_customer(full_name="Jon Smith")

    case_repo = CaseRepository(db_session)
    case_number = await case_repo.next_case_number()
    db_session.add(
        Case(case_number=case_number, customer_id=customer.id, case_type="dispute", status="new")
    )
    await db_session.flush()

    response = await client.delete(f"/api/v1/customers/{customer.id}", headers=_bearer(admin))

    assert response.status_code == 409


async def test_delete_customer_succeeds_without_open_cases(client, make_user, make_customer):
    admin = await make_user(email="admin@example.com", role_name="admin")
    customer = await make_customer(full_name="Jon Smith")

    response = await client.delete(f"/api/v1/customers/{customer.id}", headers=_bearer(admin))

    assert response.status_code == 204
