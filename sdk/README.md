# app-protection — SWAPS Client SDK

Embed license validation in your Python app. Validates once at startup and on the **26th of each month at 00:00** local time.

**Full guide:** [docs/integration-guide.md](../docs/integration-guide.md) (step-by-step integration).

## Install

From repo root (editable):

```bash
pip install -e sdk/
```

Or add to your project: `app-protection` depends on `httpx`, `apscheduler`, `keyring`.

## Usage (3 lines)

```python
from app_protection import protect

protect(
    license_key="LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C",
    server_url="https://protection.yourserver.com",
    signing_secret="your-hmac-secret",  # same as server LICENSE_HMAC_SECRET
    on_invalid=lambda: exit(1),  # or disable features, show dialog, etc.
)
# App continues; if validation fails, on_invalid is called after a 48h grace period
```

## Parameters

| Parameter | Description |
|-----------|-------------|
| `license_key` | The license key (from admin dashboard). |
| `server_url` | Base URL of the SWAPS server. |
| `signing_secret` | Secret for signing requests (must match server `LICENSE_HMAC_SECRET`). |
| `app_id` | Optional; sent to server (default `"default"`). |
| `on_invalid` | Callback when license is invalid and grace period has ended. |
| `grace_period_hours` | Hours to allow operation when server unreachable (default 48). |

## Environment (optional)

Instead of passing args to `protect()`, you can set:

- `SWAPS_SERVER_URL` — server base URL  
- `SWAPS_LICENSE_KEY` — license key  
- `SWAPS_SIGNING_SECRET` — signing secret  
- `SWAPS_APP_ID` — app id (default `default`)  
- `SWAPS_GRACE_PERIOD_HOURS` — default 48  

Then call `validate_now()` to run validation using env + stored key.

## Manual validation

```python
from app_protection import validate_now

data = validate_now()  # dict with valid, status, expires_at, message; or None
```

## Enforcement (block if invalid)

After `protect()`, call `require_valid()` before starting the app or before sensitive code. It raises `LicenseInvalidError` if the license is invalid and the grace period has ended:

```python
from app_protection import protect, require_valid

protect(license_key="...", server_url="...", signing_secret="...", on_invalid=lambda: exit(1))
require_valid()  # exit if invalid/expired (after grace period)
# ... run your app
```

## Exceptions

- `ValidationFailedError` — network or server error during validation  
- `LicenseInvalidError` — license invalid/expired (e.g. from `enforcer.require_valid()`)  
- `LicenseExpiredError`, `LicenseInvalidError` — subclasses of `LicenseError`
