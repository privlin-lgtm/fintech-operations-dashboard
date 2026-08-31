from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_case_service, get_current_user
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.case import (
    CaseClose,
    CaseCreate,
    CaseDetail,
    CaseLinkCreate,
    CaseNoteCreate,
    CaseRead,
    CaseReassign,
    CaseUpdate,
)
from app.services.case import CaseService

router = APIRouter(prefix="/cases", tags=["cases"])


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseRead:
    return await service.create(data, current_user)


@router.get("", response_model=PaginatedResponse[CaseRead])
async def list_cases(
    status_filter: str | None = Query(default=None, alias="status"),
    priority: str | None = Query(default=None),
    assignee: UUID | None = Query(default=None),
    sla_risk: bool | None = Query(default=None),
    limit: int = Query(default=25, ge=1, le=200),
    cursor: str | None = Query(default=None),
    _user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> PaginatedResponse[CaseRead]:
    return await service.list_cases(
        status=status_filter,
        priority=priority,
        assignee=assignee,
        sla_risk=sla_risk,
        limit=limit,
        cursor=cursor,
    )


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: UUID,
    _user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseDetail:
    return await service.get_detail(case_id)


@router.patch("/{case_id}", response_model=CaseRead)
async def update_case(
    case_id: UUID,
    data: CaseUpdate,
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseRead:
    return await service.update(case_id, data, current_user)


@router.post("/{case_id}/notes", response_model=CaseDetail)
async def add_case_note(
    case_id: UUID,
    data: CaseNoteCreate,
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseDetail:
    return await service.add_note(case_id, data, current_user)


@router.post("/{case_id}/links", response_model=CaseDetail)
async def link_case_evidence(
    case_id: UUID,
    data: CaseLinkCreate,
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseDetail:
    return await service.link(case_id, data, current_user)


@router.post("/{case_id}/reassign", response_model=CaseRead)
async def reassign_case(
    case_id: UUID,
    data: CaseReassign,
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseRead:
    return await service.reassign(case_id, data, current_user)


@router.post("/{case_id}/close", response_model=CaseRead)
async def close_case(
    case_id: UUID,
    data: CaseClose,
    current_user: User = Depends(get_current_user),
    service: CaseService = Depends(get_case_service),
) -> CaseRead:
    return await service.close(case_id, data, current_user)
