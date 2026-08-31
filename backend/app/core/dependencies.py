from typing import Annotated
from uuid import UUID

from fastapi import Depends, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthenticationError, AuthorizationError
from app.core.security import verify_token
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.account import AccountRepository
from app.repositories.alert import AlertRepository
from app.repositories.audit_log import AuditLogRepository
from app.repositories.case import CaseRepository
from app.repositories.customer import CustomerRepository
from app.repositories.refresh_token import RefreshTokenRepository
from app.repositories.report import ReportRepository
from app.repositories.transaction import TransactionRepository
from app.repositories.user import UserRepository
from app.services.alert import AlertService
from app.services.auth import AuthService
from app.services.case import CaseService
from app.services.customer import CustomerService
from app.services.report import ReportService
from app.services.transaction import TransactionService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session(session: Annotated[AsyncSession, Depends(get_db_session)]) -> AsyncSession:
    return session


SessionDep = Annotated[AsyncSession, Depends(get_session)]


# ---------------------------------------------------------------------------
# Repositories — one factory per repo, all sharing the request's single
# AsyncSession via FastAPI's per-request dependency cache.
# ---------------------------------------------------------------------------


def get_user_repository(session: SessionDep) -> UserRepository:
    return UserRepository(session)


def get_refresh_token_repository(session: SessionDep) -> RefreshTokenRepository:
    return RefreshTokenRepository(session)


def get_audit_log_repository(session: SessionDep, request: Request) -> AuditLogRepository:
    # Captured once here so every _audit()/record() call anywhere in the
    # request gets a real IP address without every service method needing to
    # accept and thread through a Request object.
    client_host = request.client.host if request.client else None
    return AuditLogRepository(session, ip_address=client_host)


def get_customer_repository(session: SessionDep) -> CustomerRepository:
    return CustomerRepository(session)


def get_account_repository(session: SessionDep) -> AccountRepository:
    return AccountRepository(session)


def get_case_repository(session: SessionDep) -> CaseRepository:
    return CaseRepository(session)


def get_alert_repository(session: SessionDep) -> AlertRepository:
    return AlertRepository(session)


def get_transaction_repository(session: SessionDep) -> TransactionRepository:
    return TransactionRepository(session)


def get_report_repository(session: SessionDep) -> ReportRepository:
    return ReportRepository(session)


UserRepoDep = Annotated[UserRepository, Depends(get_user_repository)]
RefreshTokenRepoDep = Annotated[RefreshTokenRepository, Depends(get_refresh_token_repository)]
AuditLogRepoDep = Annotated[AuditLogRepository, Depends(get_audit_log_repository)]
CustomerRepoDep = Annotated[CustomerRepository, Depends(get_customer_repository)]
AccountRepoDep = Annotated[AccountRepository, Depends(get_account_repository)]
CaseRepoDep = Annotated[CaseRepository, Depends(get_case_repository)]
AlertRepoDep = Annotated[AlertRepository, Depends(get_alert_repository)]
TransactionRepoDep = Annotated[TransactionRepository, Depends(get_transaction_repository)]
ReportRepoDep = Annotated[ReportRepository, Depends(get_report_repository)]


# ---------------------------------------------------------------------------
# Services — each takes its collaborators via constructor injection rather
# than building them from a raw session, so a service can be unit-tested
# with fake repositories instead of a real database.
# ---------------------------------------------------------------------------


def get_auth_service(
    user_repo: UserRepoDep,
    refresh_token_repo: RefreshTokenRepoDep,
    audit_repo: AuditLogRepoDep,
) -> AuthService:
    return AuthService(user_repo, refresh_token_repo, audit_repo)


def get_transaction_service(
    transaction_repo: TransactionRepoDep,
    audit_repo: AuditLogRepoDep,
) -> TransactionService:
    return TransactionService(transaction_repo, audit_repo)


def get_case_service(
    case_repo: CaseRepoDep,
    audit_repo: AuditLogRepoDep,
    customer_repo: CustomerRepoDep,
    user_repo: UserRepoDep,
) -> CaseService:
    return CaseService(case_repo, audit_repo, customer_repo, user_repo)


def get_alert_service(
    alert_repo: AlertRepoDep,
    case_repo: CaseRepoDep,
    audit_repo: AuditLogRepoDep,
    customer_repo: CustomerRepoDep,
    user_repo: UserRepoDep,
) -> AlertService:
    return AlertService(alert_repo, case_repo, audit_repo, customer_repo, user_repo)


def get_report_service(
    report_repo: ReportRepoDep, alert_repo: AlertRepoDep, audit_repo: AuditLogRepoDep
) -> ReportService:
    return ReportService(report_repo, alert_repo, audit_repo)


def get_customer_service(
    customer_repo: CustomerRepoDep,
    account_repo: AccountRepoDep,
    case_repo: CaseRepoDep,
    alert_repo: AlertRepoDep,
    audit_repo: AuditLogRepoDep,
    case_service: Annotated[CaseService, Depends(get_case_service)],
    alert_service: Annotated[AlertService, Depends(get_alert_service)],
) -> CustomerService:
    return CustomerService(
        customer_repo=customer_repo,
        account_repo=account_repo,
        case_repo=case_repo,
        alert_repo=alert_repo,
        audit_repo=audit_repo,
        case_service=case_service,
        alert_service=alert_service,
    )


AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
TransactionServiceDep = Annotated[TransactionService, Depends(get_transaction_service)]
CaseServiceDep = Annotated[CaseService, Depends(get_case_service)]
AlertServiceDep = Annotated[AlertService, Depends(get_alert_service)]
ReportServiceDep = Annotated[ReportService, Depends(get_report_service)]
CustomerServiceDep = Annotated[CustomerService, Depends(get_customer_service)]


# ---------------------------------------------------------------------------
# Auth
# ---------------------------------------------------------------------------


async def get_current_user(
    request: Request,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer_scheme)],
    user_repo: UserRepoDep,
    audit_repo: AuditLogRepoDep,
) -> User:
    async def _deny(message: str, *, actor_id: UUID | None = None) -> None:
        # Every rejection here is logged — this is the one place a probing or
        # replay attempt against an invalid/expired/revoked token would
        # otherwise leave zero trace anywhere in the system.
        await audit_repo.record(
            actor_id=actor_id,
            action="access_denied",
            resource_type="auth",
            resource_id=actor_id or UUID(int=0),
            metadata={"reason": message, "path": request.url.path},
        )

    if credentials is None or credentials.scheme.lower() != "bearer":
        await _deny("not_authenticated")
        raise AuthenticationError("Not authenticated")

    try:
        payload = verify_token(credentials.credentials, expected_type="access")
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        await _deny("invalid_or_expired_token")
        raise AuthenticationError("Invalid or expired token") from exc

    user = await user_repo.get_active_by_id(user_id)
    if user is None:
        await _deny("user_not_found_or_inactive", actor_id=user_id)
        raise AuthenticationError("User not found or inactive")

    # Bumped on logout — a token minted before that point stops working on
    # the very next request instead of riding out its remaining lifetime.
    if payload.get("tv") != user.token_version:
        await _deny("session_invalidated", actor_id=user.id)
        raise AuthenticationError("Session has been invalidated, please log in again")

    return user


CurrentUserDep = Annotated[User, Depends(get_current_user)]


def require_roles(*allowed_roles: str):
    async def _checker(
        request: Request,
        current_user: CurrentUserDep,
        audit_repo: AuditLogRepoDep,
    ) -> User:
        if current_user.role.name not in allowed_roles:
            await audit_repo.record(
                actor_id=current_user.id,
                action="access_denied",
                resource_type="auth",
                resource_id=current_user.id,
                metadata={
                    "reason": "insufficient_role",
                    "path": request.url.path,
                    "actual_role": current_user.role.name,
                    "required_roles": list(allowed_roles),
                },
            )
            raise AuthorizationError("Insufficient permissions")
        return current_user

    return _checker
