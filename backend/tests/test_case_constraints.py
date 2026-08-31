import pytest
from sqlalchemy.exc import IntegrityError

from app.models.case import Case
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.schemas.case import CaseClose, CaseCreate
from app.services.case import CaseService


async def test_db_rejects_closed_case_without_resolution(db_session, make_customer):
    """CaseService.close() already requires these fields via Pydantic — this
    proves the database itself enforces it too (ck_case_closed_requires_resolution),
    so a write path that bypasses the service can't violate the invariant."""
    customer = await make_customer()
    repo = CaseRepository(db_session)
    case_number = await repo.next_case_number()

    bad_case = Case(
        case_number=case_number,
        customer_id=customer.id,
        case_type="dispute",
        status="closed_resolved",
        resolution_code=None,
        closing_summary=None,
    )
    db_session.add(bad_case)

    with pytest.raises(IntegrityError):
        await db_session.flush()


async def test_db_accepts_closed_case_with_resolution(db_session, make_customer):
    customer = await make_customer()
    repo = CaseRepository(db_session)
    case_number = await repo.next_case_number()

    good_case = Case(
        case_number=case_number,
        customer_id=customer.id,
        case_type="dispute",
        status="closed_resolved",
        resolution_code="resolved_in_favor_of_customer",
        closing_summary="Refund issued after reviewing merchant records.",
    )
    db_session.add(good_case)

    await db_session.flush()

    assert good_case.id is not None


async def test_case_service_close_enforces_the_same_rule_end_to_end(
    db_session, make_customer, make_user
):
    from app.repositories.customer import CustomerRepository
    from app.repositories.user import UserRepository

    customer = await make_customer()
    actor = await make_user(role_name="investigator")
    service = CaseService(
        CaseRepository(db_session),
        AuditLogRepository(db_session),
        CustomerRepository(db_session),
        UserRepository(db_session),
    )

    created = await service.create(
        CaseCreate(customer_id=customer.id, case_type="dispute", priority="medium"), actor
    )

    closed = await service.close(
        created.id,
        CaseClose(
            resolution_code="resolved",
            closing_summary="Closed after review.",
            status="closed_no_action",
        ),
        actor,
    )

    assert closed.status == "closed_no_action"
    assert closed.closed_at is not None
