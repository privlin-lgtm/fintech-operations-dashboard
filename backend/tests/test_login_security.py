"""Covers the security-audit remediation items that don't fit test_auth.py's
happy-path shape: login lockout, audit-log IP capture, and access_denied
logging on both unauthenticated and under-privileged requests."""

from sqlalchemy import select

from app.models.audit_log import AuditLog

WRONG_PASSWORD_ATTEMPTS = 5  # matches settings.login_lockout_threshold default


async def _fail_login(client, email: str, attempts: int) -> None:
    for _ in range(attempts):
        response = await client.post(
            "/api/v1/auth/login",
            json={"email": email, "password": "not-the-password"},
        )
        assert response.status_code == 401


async def test_account_locks_out_after_repeated_failed_logins(client, make_user):
    await make_user(email="ava@example.com", password="correct-horse-battery")

    await _fail_login(client, "ava@example.com", WRONG_PASSWORD_ATTEMPTS)

    # Even the *correct* password is now rejected — the account is locked,
    # not just still failing on bad credentials.
    locked_attempt = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )
    assert locked_attempt.status_code == 401
    assert "Too many failed attempts" in locked_attempt.json()["detail"]


async def test_successful_login_resets_failed_attempt_counter(client, make_user, db_session):
    user = await make_user(email="ava@example.com", password="correct-horse-battery")

    await _fail_login(client, "ava@example.com", WRONG_PASSWORD_ATTEMPTS - 1)

    ok = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )
    assert ok.status_code == 200

    await db_session.refresh(user)
    assert user.failed_login_attempts == 0
    assert user.locked_until is None


async def test_audit_log_captures_client_ip(client, make_user, db_session):
    await make_user(email="ava@example.com", password="correct-horse-battery")

    response = await client.post(
        "/api/v1/auth/login",
        json={"email": "ava@example.com", "password": "correct-horse-battery"},
    )
    assert response.status_code == 200

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "login").order_by(AuditLog.created_at.desc())
    )
    entry = result.scalars().first()
    assert entry is not None
    assert entry.ip_address is not None


async def test_missing_token_logs_access_denied(client, db_session):
    response = await client.get("/api/v1/auth/me")
    assert response.status_code == 401

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "access_denied")
    )
    entry = result.scalars().first()
    assert entry is not None
    assert entry.log_metadata["reason"] == "not_authenticated"


async def test_insufficient_role_logs_access_denied(client, make_user, db_session):
    from uuid import uuid4

    from tests.helpers import bearer_headers

    analyst = await make_user(email="ava@example.com", role_name="analyst")

    # Case reassignment is restricted to team_lead/admin; require_roles(...)
    # runs before the handler body, so a made-up case_id still 403s here
    # rather than 404ing on a lookup that never happens.
    response = await client.post(
        f"/api/v1/cases/{uuid4()}/reassign",
        json={"owner_id": str(uuid4()), "reason": "test"},
        headers=bearer_headers(analyst),
    )
    assert response.status_code == 403

    result = await db_session.execute(
        select(AuditLog).where(AuditLog.action == "access_denied")
    )
    entry = result.scalars().first()
    assert entry is not None
    assert entry.log_metadata["reason"] == "insufficient_role"
    assert entry.log_metadata["actual_role"] == "analyst"
