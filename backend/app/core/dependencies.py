from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import verify_token
from app.db.session import get_db_session
from app.models.user import User
from app.repositories.user import UserRepository
from app.services.alert import AlertService
from app.services.auth import AuthService
from app.services.case import CaseService
from app.services.customer import CustomerService
from app.services.report import ReportService
from app.services.transaction import TransactionService

bearer_scheme = HTTPBearer(auto_error=False)


async def get_session(
    session: AsyncSession = Depends(get_db_session),
) -> AsyncSession:
    return session


def get_auth_service(
    session: AsyncSession = Depends(get_session),
) -> AuthService:
    return AuthService(session)


def get_user_repository(
    session: AsyncSession = Depends(get_session),
) -> UserRepository:
    return UserRepository(session)


def get_customer_service(
    session: AsyncSession = Depends(get_session),
) -> CustomerService:
    return CustomerService(session)


def get_transaction_service(
    session: AsyncSession = Depends(get_session),
) -> TransactionService:
    return TransactionService(session)


def get_case_service(
    session: AsyncSession = Depends(get_session),
) -> CaseService:
    return CaseService(session)


def get_alert_service(
    session: AsyncSession = Depends(get_session),
) -> AlertService:
    return AlertService(session)


def get_report_service(
    session: AsyncSession = Depends(get_session),
) -> ReportService:
    return ReportService(session)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    user_repo: UserRepository = Depends(get_user_repository),
) -> User:
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(credentials.credentials, expected_type="access")
        user_id = UUID(payload["sub"])
    except (ValueError, KeyError) as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    user = await user_repo.get_active_by_id(user_id)
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return user


def require_roles(*allowed_roles: str):
    async def _checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role.name not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return current_user

    return _checker
