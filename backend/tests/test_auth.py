import pyotp

# pytest-asyncio runs in "auto" mode (pyproject.toml) — every async def test
# here is collected and awaited without needing an explicit marker.


async def test_login_succeeds_with_correct_credentials(client, make_user):
    await make_user(email="ava@example.com", password="correct-horse-battery")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )

    assert response.status_code == 200
    body = response.json()
    assert body["access_token"]
    assert body["refresh_token"]
    assert body["token_type"] == "bearer"


async def test_login_rejects_wrong_password(client, make_user):
    await make_user(email="ava@example.com", password="correct-horse-battery")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "wrong-password"},
    )

    assert response.status_code == 401
    assert response.headers["content-type"] == "application/problem+json"


async def test_deactivated_user_cannot_login(client, make_user, db_session):
    user = await make_user(email="ava@example.com", password="correct-horse-battery")
    user.status = "deactivated"
    await db_session.flush()

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )

    assert response.status_code == 401


async def test_mfa_enabled_user_must_supply_code(client, make_user):
    secret = pyotp.random_base32()
    await make_user(
        email="marcus@example.com",
        password="correct-horse-battery",
        mfa_enabled=True,
        mfa_secret=secret,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "marcus@example.com", "password": "correct-horse-battery"},
    )

    assert response.status_code == 401
    assert "MFA" in response.json()["detail"]


async def test_mfa_enabled_user_rejects_wrong_code(client, make_user):
    secret = pyotp.random_base32()
    await make_user(
        email="marcus@example.com",
        password="correct-horse-battery",
        mfa_enabled=True,
        mfa_secret=secret,
    )

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "marcus@example.com",
            "password": "correct-horse-battery",
            "mfa_code": "000000",
        },
    )

    assert response.status_code == 401


async def test_mfa_enabled_user_logs_in_with_correct_code(client, make_user):
    secret = pyotp.random_base32()
    await make_user(
        email="marcus@example.com",
        password="correct-horse-battery",
        mfa_enabled=True,
        mfa_secret=secret,
    )
    code = pyotp.TOTP(secret).now()

    response = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "marcus@example.com",
            "password": "correct-horse-battery",
            "mfa_code": code,
        },
    )

    assert response.status_code == 200


async def test_refresh_rotates_token_and_old_one_becomes_unusable(client, make_user):
    await make_user(email="ava@example.com", password="correct-horse-battery")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )
    old_refresh = login.json()["refresh_token"]

    first_refresh = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert first_refresh.status_code == 200
    assert first_refresh.json()["refresh_token"] != old_refresh

    # Replaying the now-rotated-out token must fail — this is what makes a
    # stolen-and-replayed refresh token detectable instead of silently working.
    reuse_attempt = await client.post("/api/v1/auth/refresh", json={"refresh_token": old_refresh})
    assert reuse_attempt.status_code == 401


async def test_logout_invalidates_the_access_token_immediately(client, make_user):
    await make_user(email="ava@example.com", password="correct-horse-battery")
    login = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )
    tokens = login.json()
    headers = {"Authorization": f"Bearer {tokens['access_token']}"}

    me_before = await client.get("/api/v1/auth/me", headers=headers)
    assert me_before.status_code == 200

    logout = await client.post(
        "/api/v1/auth/logout",
        json={"refresh_token": tokens["refresh_token"]},
        headers=headers,
    )
    assert logout.status_code == 204

    # Same access token, still within its 30-minute expiry — but token_version
    # was bumped, so it must be rejected on the very next request.
    me_after = await client.get("/api/v1/auth/me", headers=headers)
    assert me_after.status_code == 401


async def test_unauthenticated_request_is_rejected(client):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401
    assert response.headers["www-authenticate"] == "Bearer"
