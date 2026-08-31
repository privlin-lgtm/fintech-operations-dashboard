"""Unit tests for report aggregation logic."""

from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock

import pytest

from app.repositories.report import ReportRepository
from app.services.report import ReportService


@pytest.fixture
def report_repo():
    return AsyncMock(spec=ReportRepository)


@pytest.fixture
def report_service(report_repo):
    return ReportService(report_repo, AsyncMock(), AsyncMock())


async def test_transaction_report_totals(report_service, report_repo):
    report_repo.transaction_volume_by_group.return_value = [
        {"group": "2026-08-01", "count": 3, "total_amount_cents": 30_000},
        {"group": "2026-08-02", "count": 2, "total_amount_cents": 15_000},
    ]

    report = await report_service.transaction_report(
        from_date=None, to_date=None, group_by="day"
    )

    assert report.total_count == 5
    assert report.total_amount_cents == 45_000
    assert len(report.rows) == 2


async def test_case_report_totals(report_service, report_repo):
    report_repo.case_volume_by_group.return_value = [
        {"group": "new", "count": 4},
        {"group": "in_progress", "count": 1},
    ]

    report = await report_service.case_report(from_date=None, to_date=None, group_by="status")

    assert report.total_count == 5
    assert report.group_by == "status"


async def test_alert_report_totals(report_service, report_repo):
    report_repo.alert_volume_by_group.return_value = [{"group": "new", "count": 7}]

    report = await report_service.alert_report(from_date=None, to_date=None, group_by="status")

    assert report.total_count == 7


async def test_sla_report_maps_repository_payload(report_service, report_repo):
    report_repo.sla_performance.return_value = {
        "total_closed": 10,
        "met_sla": 8,
        "missed_sla": 2,
        "currently_at_risk": 3,
        "compliance_rate": 0.8,
        "breakdown": [{"group": "high", "closed": 5, "met_sla": 4, "missed_sla": 1}],
    }

    report = await report_service.sla_report(from_date=None, to_date=None, group_by="priority")

    assert report.compliance_rate == 0.8
    assert report.breakdown[0].group == "high"


def test_render_volume_export_csv(report_service):
    response = report_service.render_volume_export(
        title="Test",
        filename="test.pdf",
        export_format="csv",
        columns=["group", "count"],
        rows=[{"group": "new", "count": 2}],
    )

    assert response is not None
    assert response.media_type == "text/csv"


def test_render_volume_export_pdf(report_service):
    response = report_service.render_volume_export(
        title="Test",
        filename="test.pdf",
        export_format="pdf",
        columns=["group", "count"],
        rows=[{"group": "new", "count": 2}],
    )

    assert response is not None
    assert response.media_type == "application/pdf"
    assert response.body.startswith(b"%PDF")


async def test_sla_performance_aggregation(db_session, make_case):
    repo = ReportRepository(db_session)
    now = datetime.now(UTC)

    await make_case(
        status="closed_resolved",
        priority="high",
        sla_due_at=now - timedelta(hours=1),
        closed_at=now - timedelta(hours=2),
    )
    await make_case(
        status="closed_resolved",
        priority="high",
        sla_due_at=now - timedelta(hours=1),
        closed_at=now + timedelta(minutes=5),
    )
    await make_case(
        status="in_progress",
        priority="medium",
        sla_due_at=now - timedelta(minutes=30),
    )

    result = await repo.sla_performance(from_date=None, to_date=None, group_by="priority")

    assert result["total_closed"] == 2
    assert result["met_sla"] == 1
    assert result["missed_sla"] == 1
    assert result["currently_at_risk"] == 1
    assert result["compliance_rate"] == 0.5
