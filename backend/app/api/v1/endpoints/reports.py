from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query, status

from app.core.dependencies import ReportServiceDep, require_roles
from app.models.user import User
from app.schemas.report import DashboardSummary, ReportRead, ReportScheduleCreate

router = APIRouter(prefix="/reports", tags=["reports"])

# RPT-5: an Analyst's report never surfaces case detail outside their team —
# read access matches the customer-module's role set. Scheduling a recurring
# report to external recipients is a lead/compliance action, not an analyst one.
REPORT_READ_ROLES = ("analyst", "investigator", "team_lead", "compliance_auditor", "admin")
REPORT_SCHEDULE_ROLES = ("team_lead", "compliance_auditor", "admin")
ReportReaderDep = Annotated[User, Depends(require_roles(*REPORT_READ_ROLES))]
ReportSchedulerDep = Annotated[User, Depends(require_roles(*REPORT_SCHEDULE_ROLES))]


@router.get("/dashboard", response_model=DashboardSummary)
async def get_dashboard(_user: ReportReaderDep, service: ReportServiceDep) -> DashboardSummary:
    return await service.dashboard()


@router.get("/cases")
async def get_case_report(
    _user: ReportReaderDep,
    service: ReportServiceDep,
    from_date: Annotated[datetime | None, Query(alias="from")] = None,
    to_date: Annotated[datetime | None, Query(alias="to")] = None,
    group_by: Annotated[str, Query()] = "status",
) -> list[dict]:
    return await service.case_report(from_date=from_date, to_date=to_date, group_by=group_by)


@router.post("/schedules", response_model=ReportRead, status_code=status.HTTP_201_CREATED)
async def create_report_schedule(
    data: ReportScheduleCreate, current_user: ReportSchedulerDep, service: ReportServiceDep
) -> ReportRead:
    return await service.create_schedule(data, current_user)
