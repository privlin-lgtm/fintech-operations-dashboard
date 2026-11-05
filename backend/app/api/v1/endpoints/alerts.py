from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.alert_permissions import (
    ALERT_ASSIGN_ROLES,
    ALERT_CREATE_ROLES,
    ALERT_DELETE_ROLES,
    ALERT_ESCALATE_ROLES,
    ALERT_READ_ROLES,
    ALERT_RESOLVE_ROLES,
    ALERT_UPDATE_ROLES,
)
from app.core.dependencies import AlertServiceDep, require_roles
from app.models.user import User
from app.schemas.alert import (
    AlertAssign,
    AlertCreate,
    AlertDetail,
    AlertEscalate,
    AlertRead,
    AlertResolve,
    AlertSearchParams,
    AlertUpdate,
)
from app.schemas.base import PaginatedResponse

router = APIRouter(prefix="/alerts", tags=["alerts"])

AlertReaderDep = Annotated[User, Depends(require_roles(*ALERT_READ_ROLES))]
AlertCreatorDep = Annotated[User, Depends(require_roles(*ALERT_CREATE_ROLES))]
AlertUpdaterDep = Annotated[User, Depends(require_roles(*ALERT_UPDATE_ROLES))]
AlertAssignerDep = Annotated[User, Depends(require_roles(*ALERT_ASSIGN_ROLES))]
AlertEscalatorDep = Annotated[User, Depends(require_roles(*ALERT_ESCALATE_ROLES))]
AlertResolverDep = Annotated[User, Depends(require_roles(*ALERT_RESOLVE_ROLES))]
AlertDeleterDep = Annotated[User, Depends(require_roles(*ALERT_DELETE_ROLES))]


@router.post("", response_model=AlertRead, status_code=status.HTTP_201_CREATED)
async def create_alert(
    data: AlertCreate,
    current_user: AlertCreatorDep,
    service: AlertServiceDep,
) -> AlertRead:
    return await service.create(data, current_user)


@router.get("", response_model=PaginatedResponse[AlertRead])
async def list_alerts(
    params: Annotated[AlertSearchParams, Query()],
    current_user: AlertReaderDep,
    service: AlertServiceDep,
) -> PaginatedResponse[AlertRead]:
    return await service.list_alerts(
        actor=current_user,
        query=params.q,
        customer_id=params.customer_id,
        assignee_id=params.assignee_id,
        severity=params.severity.value if params.severity else None,
        status=params.status.value if params.status else None,
        alert_type=params.alert_type.value if params.alert_type else None,
        sort=params.sort,
        limit=params.limit,
        cursor=params.cursor,
    )


@router.get("/{alert_id}", response_model=AlertDetail)
async def get_alert(
    alert_id: UUID,
    current_user: AlertReaderDep,
    service: AlertServiceDep,
) -> AlertDetail:
    return await service.get_by_id(alert_id, viewer=current_user)


@router.patch("/{alert_id}", response_model=AlertRead)
async def update_alert(
    alert_id: UUID,
    data: AlertUpdate,
    current_user: AlertUpdaterDep,
    service: AlertServiceDep,
) -> AlertRead:
    return await service.update(alert_id, data, current_user)


@router.delete("/{alert_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_alert(
    alert_id: UUID,
    current_user: AlertDeleterDep,
    service: AlertServiceDep,
) -> None:
    await service.delete(alert_id, current_user)


@router.post("/{alert_id}/assign", response_model=AlertRead)
async def assign_alert(
    alert_id: UUID,
    data: AlertAssign,
    current_user: AlertAssignerDep,
    service: AlertServiceDep,
) -> AlertRead:
    return await service.assign(alert_id, data, current_user)


@router.post("/{alert_id}/escalate", response_model=AlertRead)
async def escalate_alert(
    alert_id: UUID,
    data: AlertEscalate,
    current_user: AlertEscalatorDep,
    service: AlertServiceDep,
) -> AlertRead:
    return await service.escalate(alert_id, data, current_user)


@router.post("/{alert_id}/resolve", response_model=AlertRead)
async def resolve_alert(
    alert_id: UUID,
    data: AlertResolve,
    current_user: AlertResolverDep,
    service: AlertServiceDep,
) -> AlertRead:
    return await service.resolve(alert_id, data, current_user)
