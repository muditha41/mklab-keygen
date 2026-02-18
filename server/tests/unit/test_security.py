"""Unit tests for security: password hashing, JWT, validation signature."""

import pytest

from app.core.security import (
    compute_validation_signature,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
    verify_validation_signature,
)


def test_hash_password_verify_roundtrip():
    p = "my-secure-password"
    h = hash_password(p)
    assert h != p
    assert verify_password(p, h) is True


def test_verify_password_wrong_fails():
    h = hash_password("correct")
    assert verify_password("wrong", h) is False


def test_jwt_access_token_roundtrip(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.secret_key", "test-secret-32-chars-long!!!")
    token = create_access_token("user@test.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "user@test.com"
    assert payload.get("type") == "access"


def test_jwt_refresh_token_roundtrip(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.secret_key", "test-secret-32-chars-long!!!")
    token = create_refresh_token("user@test.com")
    payload = decode_token(token)
    assert payload is not None
    assert payload.get("sub") == "user@test.com"
    assert payload.get("type") == "refresh"


def test_decode_token_invalid_returns_none():
    assert decode_token("invalid.jwt.here") is None


def test_compute_validation_signature_deterministic(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.license_hmac_secret", "hmac-secret")
    sig1 = compute_validation_signature("LIC-K-1-ABC", "app1", 12345)
    sig2 = compute_validation_signature("LIC-K-1-ABC", "app1", 12345)
    assert sig1 == sig2
    assert len(sig1) > 0


def test_verify_validation_signature_valid(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.license_hmac_secret", "hmac-secret")
    sig = compute_validation_signature("LIC-K-1-ABC", "app1", 12345)
    assert verify_validation_signature("LIC-K-1-ABC", "app1", 12345, sig) is True


def test_verify_validation_signature_tampered_fails(monkeypatch):
    monkeypatch.setattr("app.core.security.settings.license_hmac_secret", "hmac-secret")
    sig = compute_validation_signature("LIC-K-1-ABC", "app1", 12345)
    assert verify_validation_signature("LIC-K-1-ABC", "app1", 12346, sig) is False
    assert verify_validation_signature("LIC-K-1-XYZ", "app1", 12345, sig) is False
