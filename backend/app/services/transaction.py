from datetime import datetime
from uuid import UUID

from app.core.exceptions import NotFoundError
from app.core.sorting import decode_sort_cursor, paginate_sorted
from app.models.transaction import Transaction
from app.models.user import User
from app.repositories.audit_log import AuditLogRepository
from app.repositories.transaction import TRANSACTION_SORT_COLUMNS, TransactionRepository, parse_transaction_sort
from app.schemas.base import PaginatedResponse
from app.schemas.transaction import (
    TransactionAccountSummary,
    TransactionDetail,
    TransactionRead,
    TransactionStatusEvent,
)


def build_status_history(txn: Transaction) -> list[TransactionStatusEvent]:
    """Derive a lifecycle timeline from ledger fields (no separate history table in v1)."""
    events = [TransactionStatusEvent(status="initiated", occurred_at=txn.created_at)]

    if txn.status != "initiated":
        events.append(
            TransactionStatusEvent(
                status=txn.status,
                occurred_at=txn.settled_at or txn.updated_at,
            )
        )

    if txn.settled_at and txn.status == "settled":
        # Avoid duplicate if the block above already used settled_at.
        if not events or events[-1].status != "settled":
            events.append(TransactionStatusEvent(status="settled", occurred_at=txn.settled_at))

    return events


class TransactionService:
    def __init__(
        self,
        transaction_repo: TransactionRepository,
        audit_repo: AuditLogRepository,
    ) -> None:
        self.repo = transaction_repo
        self.audit_repo = audit_repo

    async def get_detail(self, transaction_id: UUID, *, viewer: User) -> TransactionDetail:
        txn = await self.repo.get_detail(transaction_id)
        if txn is None:
            raise NotFoundError("transaction", transaction_id)

        open_alert_count = await self.repo.count_open_alerts(transaction_id)
        open_case_count = await self.repo.count_open_cases(transaction_id)

        await self.audit_repo.record(
            actor_id=viewer.id,
            action="view",
            resource_type="transaction",
            resource_id=transaction_id,
        )

        return TransactionDetail(
            id=txn.id,
            created_at=txn.created_at,
            updated_at=txn.updated_at,
            account_id=txn.account_id,
            amount_cents=txn.amount_cents,
            currency=txn.currency,
            direction=txn.direction,
            channel=txn.channel,
            status=txn.status,
            counterparty_masked=txn.counterparty_masked,
            risk_score=txn.risk_score,
            settled_at=txn.settled_at,
            has_open_alert=open_alert_count > 0,
            has_open_case=open_case_count > 0,
            account=TransactionAccountSummary.model_validate(txn.account),
            status_history=build_status_history(txn),
            open_alert_count=open_alert_count,
            open_case_count=open_case_count,
        )

    async def search(
        self,
        *,
        query: str | None = None,
        customer_id: UUID | None = None,
        account_id: UUID | None = None,
        from_date: datetime | None = None,
        to_date: datetime | None = None,
        min_amount: int | None = None,
        max_amount: int | None = None,
        status: str | None = None,
        channel: str | None = None,
        direction: str | None = None,
        sort: str = "-created_at",
        limit: int = 25,
        cursor: str | None = None,
    ) -> PaginatedResponse[TransactionRead]:
        sort_spec = parse_transaction_sort(sort)
        parsed_cursor = (
            decode_sort_cursor(cursor, expected_sort=sort_spec.raw) if cursor else None
        )
        rows = await self.repo.search(
            query=query,
            customer_id=customer_id,
            account_id=account_id,
            from_date=from_date,
            to_date=to_date,
            min_amount=min_amount,
            max_amount=max_amount,
            status=status,
            channel=channel,
            direction=direction,
            sort=sort_spec,
            limit=limit,
            cursor=parsed_cursor,
        )
        column = TRANSACTION_SORT_COLUMNS[sort_spec.field]
        page_rows, next_cursor = paginate_sorted(
            rows,
            limit,
            sort=sort_spec.raw,
            get_sort_value=lambda row: getattr(row, column.key),
        )

        items: list[TransactionRead] = []
        for txn in page_rows:
            has_open_alert = await self.repo.has_open_alert(txn.id)
            has_open_case = await self.repo.has_open_case(txn.id)
            items.append(
                TransactionRead(
                    id=txn.id,
                    created_at=txn.created_at,
                    updated_at=txn.updated_at,
                    account_id=txn.account_id,
                    amount_cents=txn.amount_cents,
                    currency=txn.currency,
                    direction=txn.direction,
                    channel=txn.channel,
                    status=txn.status,
                    counterparty_masked=txn.counterparty_masked,
                    risk_score=txn.risk_score,
                    settled_at=txn.settled_at,
                    has_open_alert=has_open_alert,
                    has_open_case=has_open_case,
                )
            )

        return PaginatedResponse(items=items, next_cursor=next_cursor, limit=limit)
