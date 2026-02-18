"""Security utilities: hashing, HMAC, JWT, password hashing."""

import hashlib
import hmac
import secrets
from base64 import b64encode
from datetime import datetime, timedelta, timezone

import bcrypt
from jose import JWTError, jwt

from app.core.config import settings

# bcrypt has a 72-byte limit; longer passwords are hashed with SHA256 first
_BCRYPT_MAX_BYTES = 72


def _prepare_password(password: str) -> bytes:
    """Return bytes to pass to bcrypt (≤72 bytes)."""
    raw = password.encode("utf-8")
    if len(raw) <= _BCRYPT_MAX_BYTES:
        return raw
    return hashlib.sha256(raw).digest()  # 32 bytes


def hash_license_key(license_key: str) -> str:
    """SHA256 hash of the license key for storage. Never store plaintext."""
    return hashlib.sha256(license_key.encode("utf-8")).hexdigest()


def compute_validation_signature(license_key: str, app_id: str, timestamp: int) -> str:
    """HMAC-SHA256(license_key + app_id + timestamp, shared_secret) for validation requests."""
    payload = f"{license_key}|{app_id}|{timestamp}"
    sig = hmac.new(
        settings.license_hmac_secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return b64encode(sig).decode("ascii").rstrip("=")


def verify_validation_signature(
    license_key: str, app_id: str, timestamp: int, signature: str
) -> bool:
    """Verify HMAC signature from client. Constant-time comparison."""
    expected = compute_validation_signature(license_key, app_id, timestamp)
    return hmac.compare_digest(expected, signature)


def generate_license_key(app_code: str) -> str:
    """
    Generate a unique license key: LIC-{APP_CODE}-{TIMESTAMP_HEX}-{HMAC_TRUNCATED}.
    HMAC-SHA256(secret_seed + app_id + timestamp) truncated to 16 hex chars.
    """
    import time
    ts_hex = f"{int(time.time()):08X}"
    # Add entropy to avoid collision if same second
    nonce = secrets.token_hex(4)
    message = f"{settings.license_hmac_secret}|{app_code}|{ts_hex}|{nonce}"
    digest = hmac.new(
        settings.license_hmac_secret.encode("utf-8"),
        message.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()
    truncated = digest[:16].upper()
    return f"LIC-{app_code.upper()}-{ts_hex}-{truncated}"


# ---- Password hashing (bcrypt directly; avoids passlib/bcrypt 4.1+ incompatibility) ----
def hash_password(password: str) -> str:
    payload = _prepare_password(password)
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(payload, salt).decode("ascii")


def verify_password(plain: str, hashed: str) -> bool:
    payload = _prepare_password(plain)
    try:
        return bcrypt.checkpw(payload, hashed.encode("ascii"))
    except (ValueError, TypeError):
        return False


# ---- JWT ----
def create_access_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(minutes=settings.jwt_access_token_expire_minutes)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "access"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def create_refresh_token(subject: str) -> str:
    expire = datetime.now(timezone.utc) + timedelta(days=settings.jwt_refresh_token_expire_days)
    return jwt.encode(
        {"sub": subject, "exp": expire, "type": "refresh"},
        settings.secret_key,
        algorithm=settings.jwt_algorithm,
    )


def decode_token(token: str) -> dict | None:
    try:
        return jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.jwt_algorithm],
        )
    except JWTError:
        return None
