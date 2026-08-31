from datetime import UTC, datetime
from uuid import uuid4

from app.repositories.customer import _escape_like
from app.schemas.customer import CustomerRead


def _base_kwargs(**overrides):
    now = datetime.now(UTC)
    kwargs = {
        "id": uuid4(),
        "created_at": now,
        "updated_at": now,
        "full_name": "Jon Smith",
        "email": "jon.smith@example.com",
        "phone": "555-123-4567",
        "kyc_status": "verified",
        "risk_tier": "low",
        "status": "active",
    }
    kwargs.update(overrides)
    return kwargs


def test_email_is_masked_but_domain_stays_readable():
    customer = CustomerRead(**_base_kwargs())
    assert customer.email == "j********@example.com"


def test_phone_keeps_only_last_four_digits():
    customer = CustomerRead(**_base_kwargs())
    assert customer.phone == "******4567"


def test_none_email_and_phone_stay_none():
    customer = CustomerRead(**_base_kwargs(email=None, phone=None))
    assert customer.email is None
    assert customer.phone is None


def test_short_phone_is_fully_masked_not_leaked():
    customer = CustomerRead(**_base_kwargs(phone="123"))
    assert customer.phone == "***"


def test_like_escape_neutralizes_wildcards():
    assert _escape_like("50% off_deal") == "50\\% off\\_deal"
    assert _escape_like(r"back\slash") == r"back\\slash"
    assert _escape_like("plain text") == "plain text"
