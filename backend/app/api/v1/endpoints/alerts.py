from uuid import UUID

from fastapi import APIRouter, Depends, Query

from app.core.dependencies import get_alert_service, get_current_user
from app.models.user import User
from app.schemas.alert import AlertDismiss, AlertEscalate, AlertRead
from app.schemas.base import PaginatedResponse
from app.services.alert import AlertService

router = APIRouter(prefix="/alerts", tags=["alerts"])


@router.get("", response_model=PaginatedResponse[AlertRead])
async def list_alerts(
    severity: str | None = Query(default=None),
    status_filter: str | None = Query(default=None, alias="status"),
    alert_type: str | None = Query(default=None, alias="type"),
    limit: int = Query(default=25, ge=1, le=200),
    cursor: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> PaginatedResponse[AlertRead]:
    return await service.list_alerts(
        severity=severity,
        status=status_filter,
        alert_type=alert_type,
        limit=limit,
        cursor=cursor,
    )


@router.get("/{alert_id}", response_model=AlertRead)
async def get_alert(
    alert_id: UUID,
    _user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertRead:
    return await service.get_by_id(alert_id)


@router.post("/{alert_id}/dismiss", response_model=AlertRead)
async def dismiss_alert(
    alert_id: UUID,
    data: AlertDismiss,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertRead:
    return await service.dismiss(alert_id, data, current_user)


@router.post("/{alert_id}/escalate", response_model=AlertRead)
async def escalate_alert(
    alert_id: UUID,
    data: AlertEscalate,
    current_user: User = Depends(get_current_user),
    service: AlertService = Depends(get_alert_service),
) -> AlertRead:
    return await service.escalate(alert_id, data, current_user)
