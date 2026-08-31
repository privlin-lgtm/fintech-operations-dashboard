from datetime import datetime

from fastapi import APIRouter, Request, Response, status

from app.core.config import get_settings
from app.core.dependencies import AuthServiceDep, CurrentUserDep
from app.core.rate_limit import limiter
from app.models.user import User
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])
settings = get_settings()


def _set_refresh_cookie(response: Response, token: str, expires_at: datetime) -> None:
    response.set_cookie(
        key=settings.refresh_cookie_name,
        value=token,
        expires=expires_at,
        httponly=True,
        # Sent over plain HTTP in dev/test (there's no TLS to require); a real
        # deployment behind HTTPS gets the Secure flag automatically.
        secure=settings.is_production,
        samesite="lax",
        path=settings.refresh_cookie_path,
    )


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
@limiter.limit(settings.login_rate_limit)
async def login(
    request: Request,  # required by @limiter.limit, which reads it from kwargs
    credentials: LoginRequest,
    response: Response,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    tokens, refresh_token, expires_at = await auth_service.login(credentials)
    _set_refresh_cookie(response, refresh_token, expires_at)
    return tokens


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(
    request: Request,
    response: Response,
    auth_service: AuthServiceDep,
) -> TokenResponse:
    existing = request.cookies.get(settings.refresh_cookie_name)
    tokens, new_refresh_token, expires_at = await auth_service.refresh(existing)
    _set_refresh_cookie(response, new_refresh_token, expires_at)
    return tokens


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    request: Request,
    response: Response,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> None:
    existing = request.cookies.get(settings.refresh_cookie_name)
    await auth_service.logout(existing, current_user)
    response.delete_cookie(key=settings.refresh_cookie_name, path=settings.refresh_cookie_path)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUserDep) -> User:
    return current_user
