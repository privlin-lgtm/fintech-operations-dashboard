from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from app.core.case_permissions import (
    CASE_ASSIGN_ROLES,
    CASE_CLOSE_ROLES,
    CASE_CREATE_ROLES,
    CASE_NOTE_ROLES,
    CASE_READ_ROLES,
    CASE_REASSIGN_ROLES,
    CASE_STATUS_ROLES,
)
from app.core.dependencies import CaseServiceDep, require_roles
from app.models.user import User
from app.schemas.base import PaginatedResponse
from app.schemas.case import (
    CaseAssign,
    CaseClose,
    CaseCreate,
    CaseDetail,
    CaseLinkCreate,
    CaseNoteCreate,
    CaseRead,
    CaseReassign,
    CaseSearchParams,
    CaseUpdate,
)

router = APIRouter(prefix="/cases", tags=["cases"])

CaseReaderDep = Annotated[User, Depends(require_roles(*CASE_READ_ROLES))]
CaseCreatorDep = Annotated[User, Depends(require_roles(*CASE_CREATE_ROLES))]
CaseNoteWriterDep = Annotated[User, Depends(require_roles(*CASE_NOTE_ROLES))]
CaseStatusWriterDep = Annotated[User, Depends(require_roles(*CASE_STATUS_ROLES))]
CaseAssignerDep = Annotated[User, Depends(require_roles(*CASE_ASSIGN_ROLES))]
CaseCloserDep = Annotated[User, Depends(require_roles(*CASE_CLOSE_ROLES))]
CaseReassignerDep = Annotated[User, Depends(require_roles(*CASE_REASSIGN_ROLES))]


@router.post("", response_model=CaseRead, status_code=status.HTTP_201_CREATED)
async def create_case(
    data: CaseCreate,
    current_user: CaseCreatorDep,
    service: CaseServiceDep,
) -> CaseRead:
    return await service.create(data, current_user)


@router.get("", response_model=PaginatedResponse[CaseRead])
async def list_cases(
    params: Annotated[CaseSearchParams, Query()],
    current_user: CaseReaderDep,
    service: CaseServiceDep,
) -> PaginatedResponse[CaseRead]:
    return await service.list_cases(
        actor=current_user,
        status=params.status.value if params.status else None,
        priority=params.priority.value if params.priority else None,
        assignee=params.assignee,
        sla_risk=params.sla_risk,
        limit=params.limit,
        cursor=params.cursor,
    )


@router.get("/{case_id}", response_model=CaseDetail)
async def get_case(
    case_id: UUID,
    current_user: CaseReaderDep,
    service: CaseServiceDep,
) -> CaseDetail:
    return await service.get_detail(case_id, viewer=current_user)


@router.patch("/{case_id}", response_model=CaseRead)
async def update_case(
    case_id: UUID,
    data: CaseUpdate,
    current_user: CaseStatusWriterDep,
    service: CaseServiceDep,
) -> CaseRead:
    return await service.update(case_id, data, current_user)


@router.post("/{case_id}/assign", response_model=CaseRead)
async def assign_case(
    case_id: UUID,
    data: CaseAssign,
    current_user: CaseAssignerDep,
    service: CaseServiceDep,
) -> CaseRead:
    return await service.assign(case_id, data, current_user)


@router.post("/{case_id}/notes", response_model=CaseDetail)
async def add_case_note(
    case_id: UUID,
    data: CaseNoteCreate,
    current_user: CaseNoteWriterDep,
    service: CaseServiceDep,
) -> CaseDetail:
    return await service.add_note(case_id, data, current_user)


@router.post("/{case_id}/links", response_model=CaseDetail)
async def link_case_evidence(
    case_id: UUID,
    data: CaseLinkCreate,
    current_user: CaseStatusWriterDep,
    service: CaseServiceDep,
) -> CaseDetail:
    return await service.link(case_id, data, current_user)


@router.post("/{case_id}/reassign", response_model=CaseRead)
async def reassign_case(
    case_id: UUID,
    data: CaseReassign,
    current_user: CaseReassignerDep,
    service: CaseServiceDep,
) -> CaseRead:
    return await service.reassign(case_id, data, current_user)


@router.post("/{case_id}/close", response_model=CaseRead)
async def close_case(
    case_id: UUID,
    data: CaseClose,
    current_user: CaseCloserDep,
    service: CaseServiceDep,
) -> CaseRead:
    return await service.close(case_id, data, current_user)
