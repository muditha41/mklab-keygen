"""Secure local storage for the license key (keyring with env fallback)."""

import os
from typing import Optional

# Keyring is optional; fallback to env only if import fails
try:
    import keyring
    _KEYRING_AVAILABLE = True
except Exception:  # noqa: BLE001
    _KEYRING_AVAILABLE = False

_SERVICE_NAME = "swaps"
_KEY_NAME = "license_key"


def get_stored_key(app_id: str = "default") -> Optional[str]:
    """
    Retrieve the stored license key. Tries keyring first (service=swaps, key=license_key),
    then environment SWAPS_LICENSE_KEY. Returns None if not found.
    """
    env_key = os.environ.get("SWAPS_LICENSE_KEY")
    if env_key and env_key.strip():
        return env_key.strip()
    if _KEYRING_AVAILABLE:
        try:
            stored = keyring.get_password(_SERVICE_NAME, f"{_KEY_NAME}:{app_id}")
            if stored:
                return stored
        except Exception:  # noqa: BLE001
            pass
    return None


def set_stored_key(license_key: str, app_id: str = "default") -> None:
    """
    Store the license key. Prefers keyring; if unavailable, does nothing (caller can rely on
    passing key to protect() or SWAPS_LICENSE_KEY env).
    """
    if _KEYRING_AVAILABLE:
        try:
            keyring.set_password(_SERVICE_NAME, f"{_KEY_NAME}:{app_id}", license_key)
        except Exception:  # noqa: BLE001
            pass
    # Never write to os.environ from library code; user sets SWAPS_LICENSE_KEY if needed.


def clear_stored_key(app_id: str = "default") -> None:
    """Remove stored key from keyring (if used)."""
    if _KEYRING_AVAILABLE:
        try:
            keyring.delete_password(_SERVICE_NAME, f"{_KEY_NAME}:{app_id}")
        except Exception:  # noqa: BLE001 (e.g. PasswordDeleteError, keyring backend errors)
            pass
