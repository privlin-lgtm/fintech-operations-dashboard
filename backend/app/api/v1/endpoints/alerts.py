from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query

from app.core.dependencies import AlertServiceDep, CurrentUserDep
from app.schemas.alert import AlertDismiss, AlertEscalate, AlertRead
from app.schemas.base import PaginatedResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=PaginatedResponse[AlertRead])
async def list_alerts(
    _user: CurrentUserDep,
    service: AlertServiceDep,
    severity: Annotated[str | None, Query()] = None,
    status_filter: Annotated[str | None, Query(alias="status")] = None,
    alert_type: Annotated[str | None, Query(alias="type")] = None,
    limit: Annotated[int, Query(ge=1, le=200)] = 25,
    cursor: Annotated[str | None, Query()] = None,
) -> PaginatedResponse[AlertRead]:
    return await service.list_alerts(
        severity=severity,
        status=status_filter,
        alert_type=alert_type,
        limit=limit,
        cursor=cursor,
    )


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(alert_id: UUID, _user: CurrentUserDep, service: AlertServiceDep) -> AlertRead:
    return await service.get_by_id(alert_id)


@router.post("/{alert_id}/dismiss", response_model=AlertRead)
async def dismiss_alert(
    alert_id: UUID, data: AlertDismiss, current_user: CurrentUserDep, service: AlertServiceDep
) -> AlertRead:
    return await service.dismiss(alert_id, data, current_user)


@router.post("/{alert_id}/escalate", response_model=AlertRead)
async def escalate_alert(
    alert_id: UUID, data: AlertEscalate, current_user: CurrentUserDep, service: AlertServiceDep
) -> AlertRead:
    return await service.escalate(alert_id, data, current_user)
