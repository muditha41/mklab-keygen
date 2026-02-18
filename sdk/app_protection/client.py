"""HTTP client for the SWAPS validation API."""

import hashlib
import hmac
import time
from base64 import b64encode
from typing import Any

import httpx

from app_protection.exceptions import ValidationFailedError


def compute_signature(license_key: str, app_id: str, timestamp: int, secret: str) -> str:
    """Compute request signature (must match server: payload = license_key|app_id|timestamp)."""
    payload = f"{license_key}|{app_id}|{timestamp}"
    sig = hmac.new(
        secret.encode("utf-8"),
        payload.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return b64encode(sig).decode("ascii").rstrip("=")


def validate(
    server_url: str,
    license_key: str,
    app_id: str,
    signing_secret: str,
    *,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """
    POST to server /licenses/validate with signed body. Returns response dict with
    valid, status, expires_at, message. Raises ValidationFailedError on network/HTTP errors.
    """
    url = f"{server_url.rstrip('/')}/licenses/validate"
    timestamp = int(time.time())
    signature = compute_signature(license_key, app_id, timestamp, signing_secret)
    body = {
        "license_key": license_key,
        "app_id": app_id,
        "timestamp": timestamp,
        "signature": signature,
    }
    try:
        with httpx.Client(timeout=timeout) as client:
            r = client.post(url, json=body)
            r.raise_for_status()
            data = r.json()
    except (httpx.HTTPError, httpx.RequestError, KeyError) as e:
        raise ValidationFailedError(f"Validation request failed: {e}") from e
    if "valid" not in data or "status" not in data or "message" not in data:
        raise ValidationFailedError("Invalid response from server")
    return data


def validate_with_retry(
    server_url: str,
    license_key: str,
    app_id: str,
    signing_secret: str,
    *,
    retry_count: int = 3,
    retry_backoff_seconds: int = 300,
    timeout: float = 30.0,
) -> dict[str, Any]:
    """Call validate(); on failure retry up to retry_count times with retry_backoff_seconds delay."""
    last_error: Exception | None = None
    for attempt in range(retry_count):
        try:
            return validate(
                server_url,
                license_key,
                app_id,
                signing_secret,
                timeout=timeout,
            )
        except ValidationFailedError as e:
            last_error = e
            if attempt < retry_count - 1:
                time.sleep(retry_backoff_seconds)
    raise last_error  # type: ignore[misc]
