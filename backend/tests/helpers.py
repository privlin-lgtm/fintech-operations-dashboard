"""Shared helpers for API and integration tests."""

from httpx import AsyncClient

from app.core.security import create_access_token
from app.models.user import User

DEFAULT_PASSWORD = "correct-horse-battery"


def bearer_headers(user: User) -> dict[str, str]:
    token = create_access_token(
        user.id, extra_claims={"role": user.role.name, "tv": user.token_version}
    )
    return {"Authorization": f"Bearer {token}"}


async def login(client: AsyncClient, *, email: str, password: str = DEFAULT_PASSWORD) -> dict:
    response = await client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200, response.text
    return response.json()


def auth_headers_from_tokens(tokens: dict) -> dict[str, str]:
    return {"Authorization": f"Bearer {tokens['access_token']}"}
