from datetime import datetime

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import get_current_user, get_report_service
from app.models.user import User
from app.schemas.report import DashboardSummary, ReportRead, ReportScheduleCreate
from app.services.report import ReportService

router = APIRouter(prefix="/reports", tags=["reports"])
schedule_router = APIRouter(tags=["reports"])


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(
    _user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> DashboardSummary:
    return await service.dashboard()


@router.get("/cases")
async def get_case_report(
    from_date: datetime | None = Query(default=None, alias="from"),
    to_date: datetime | None = Query(default=None, alias="to"),
    group_by: str = Query(default="status"),
    _user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> list[dict]:
    return await service.case_report(
        from_date=from_date, to_date=to_date, group_by=group_by
    )


@schedule_router.post("/report-schedules", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report_schedule(
    data: ReportScheduleCreate,
    current_user: User = Depends(get_current_user),
    service: ReportService = Depends(get_report_service),
) -> ReportRead:
    return await service.create_schedule(data, current_user)
