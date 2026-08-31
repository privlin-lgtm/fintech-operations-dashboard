from fastapi import APIRouter, status

from app.core.dependencies import AuthServiceDep, CurrentUserDep
from app.models.user import User
from app.schemas.auth import LoginRequest, LogoutRequest, RefreshTokenRequest, TokenResponse
from app.schemas.user import UserRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def login(credentials: LoginRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.login(credentials)


@router.post("/refresh", response_model=TokenResponse, status_code=status.HTTP_200_OK)
async def refresh_token(body: RefreshTokenRequest, auth_service: AuthServiceDep) -> TokenResponse:
    return await auth_service.refresh(body.refresh_token)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(
    body: LogoutRequest,
    current_user: CurrentUserDep,
    auth_service: AuthServiceDep,
) -> None:
    await auth_service.logout(body.refresh_token, current_user)


@router.get("/me", response_model=UserRead)
async def get_me(current_user: CurrentUserDep) -> User:
    return current_user
