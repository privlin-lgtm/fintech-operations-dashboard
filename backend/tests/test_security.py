import pyotp
import pytest
from pydantic import ValidationError

from app.core.config import Settings
from app.core.security import (
    create_access_token,
    create_refresh_token,
    generate_mfa_secret,
    hash_password,
    hash_token,
    verify_mfa_code,
    verify_password,
    verify_token,
)


def test_password_hash_roundtrip():
    hashed = hash_password("correct-horse-battery")
    assert verify_password("correct-horse-battery", hashed)
    assert not verify_password("wrong-password", hashed)


def test_access_token_roundtrip_and_claims():
    token = create_access_token("user-123", extra_claims={"role": "analyst", "tv": 2})
    payload = verify_token(token, expected_type="access")

    assert payload["sub"] == "user-123"
    assert payload["type"] == "access"
    assert payload["role"] == "analyst"
    assert payload["tv"] == 2


def test_refresh_token_has_unique_jti_and_hashable():
    token_a, jti_a, _ = create_refresh_token("user-123")
    token_b, jti_b, _ = create_refresh_token("user-123")

    assert jti_a != jti_b
    assert token_a != token_b
    assert hash_token(token_a) != hash_token(token_b)
    # hashing is deterministic — needed to look a token up by its hash later
    assert hash_token(token_a) == hash_token(token_a)


def test_verify_token_rejects_wrong_type():
    access = create_access_token("user-123")
    with pytest.raises(ValueError):
        verify_token(access, expected_type="refresh")


def test_verify_token_rejects_expired_token():
    from datetime import timedelta

    token = create_access_token("user-123", expires_delta=timedelta(seconds=-1))
    with pytest.raises(ValueError):
        verify_token(token, expected_type="access")


def test_verify_token_rejects_bad_signature():
    token = create_access_token("user-123")
    tampered = token[:-1] + ("A" if token[-1] != "A" else "B")
    with pytest.raises(ValueError):
        verify_token(tampered, expected_type="access")


def test_mfa_code_roundtrip():
    secret = generate_mfa_secret()
    code = pyotp.TOTP(secret).now()
    assert verify_mfa_code(secret, code)
    assert not verify_mfa_code(secret, "000000" if code != "000000" else "111111")


def test_jwt_algorithm_is_restricted():
    with pytest.raises(ValidationError):
        Settings(jwt_algorithm="none", jwt_secret_key="x" * 40)


def test_jwt_algorithm_allows_hmac_variants():
    settings = Settings(jwt_algorithm="HS512", jwt_secret_key="x" * 40)
    assert settings.jwt_algorithm == "HS512"


def test_production_env_rejects_default_secret():
    with pytest.raises(ValidationError):
        Settings(app_env="production", debug=False)


def test_production_env_rejects_debug_true():
    with pytest.raises(ValidationError):
        Settings(app_env="production", debug=True, jwt_secret_key="a-real-random-secret-value-not-default")


def test_production_env_accepts_real_secret_and_debug_off():
    settings = Settings(
        app_env="production", debug=False, jwt_secret_key="a-real-random-secret-value-not-default"
    )
    assert settings.app_env == "production"
