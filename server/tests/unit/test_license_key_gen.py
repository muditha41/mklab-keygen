"""Unit tests for license key generation and hashing."""

import pytest

from app.core.security import generate_license_key, hash_license_key


def test_hash_license_key_deterministic():
    key = "LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C"
    h1 = hash_license_key(key)
    h2 = hash_license_key(key)
    assert h1 == h2
    assert len(h1) == 64
    assert all(c in "0123456789abcdef" for c in h1)


def test_generate_license_key_format():
    key = generate_license_key("MYAPP")
    assert key.startswith("LIC-MYAPP-")
    parts = key.split("-")
    assert len(parts) == 4
    assert parts[0] == "LIC"
    assert parts[1] == "MYAPP"
    assert len(parts[2]) == 8
    assert len(parts[3]) == 16
    assert all(c in "0123456789ABCDEF" for c in parts[2])
    assert all(c in "0123456789ABCDEF" for c in parts[3])


def test_generate_license_key_unique():
    keys = {generate_license_key("TEST") for _ in range(20)}
    assert len(keys) == 20
