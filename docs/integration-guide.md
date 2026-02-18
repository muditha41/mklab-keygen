# SWAPS Developer Integration Guide

This guide walks you through integrating the SWAPS client SDK into your Python application in under 30 minutes.

## Prerequisites

- Python 3.11+
- A SWAPS protection server (your own deployment or a provided URL)
- A license key and signing secret from your license administrator

## Step 1: Get a license key

1. Your admin creates a license in the SWAPS dashboard: **Admin** → **Create license** (app name, client name, expiry, status).
2. The dashboard shows the **license key once** (e.g. `LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C`). Copy and store it securely.
3. Obtain the **signing secret** (same value as the server’s `LICENSE_HMAC_SECRET`). Your admin or DevOps provides this; it is used to sign validation requests.

## Step 2: Install the SDK

From your project directory:

```bash
pip install -e /path/to/swaps/sdk/
```

Or add to your `requirements.txt` or `pyproject.toml` the dependency on the `app-protection` package (and ensure `httpx`, `apscheduler`, `keyring` are available).

## Step 3: Add protection at startup (3 lines)

At your application’s entry point (e.g. `main.py` or `__main__.py`):

```python
from app_protection import protect

protect(
    license_key="LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C",
    server_url="https://protection.yourserver.com",
    signing_secret="your-hmac-secret",
    on_invalid=lambda: exit(1),
)
# Your app continues; if the license becomes invalid, on_invalid runs after a 48h grace period
```

- **license_key** — The key from the dashboard (Step 1).
- **server_url** — Base URL of the SWAPS API (no trailing slash).
- **signing_secret** — Must match the server’s `LICENSE_HMAC_SECRET`.
- **on_invalid** — Callback when the license is invalid and the grace period has ended (e.g. show a message and exit, or disable features).

Optional parameters:

| Parameter | Default | Description |
|-----------|---------|-------------|
| `app_id` | `"default"` | Identifier sent to the server with each validation. |
| `grace_period_hours` | `48` | Hours the app keeps running when the server is unreachable before calling `on_invalid`. |
| `store_key` | `True` | Whether to store the key in the OS keyring for `validate_now()`. |

## Step 4 (optional): Block until valid

If you want to refuse to start when the license is invalid (after grace period):

```python
from app_protection import protect, require_valid

protect(license_key="...", server_url="...", signing_secret="...", on_invalid=lambda: exit(1))
require_valid()  # Raises LicenseInvalidError if invalid; exit before starting the app
# ... rest of your app
```

## Step 5 (optional): Use environment variables

Instead of hardcoding the key and secret, use environment variables:

- `SWAPS_SERVER_URL` — Server base URL  
- `SWAPS_LICENSE_KEY` — License key  
- `SWAPS_SIGNING_SECRET` — Signing secret  
- `SWAPS_APP_ID` — App id (default `default`)  
- `SWAPS_GRACE_PERIOD_HOURS` — Grace period in hours (default `48`)

Then you can call `validate_now()` to run a one-off validation using the stored key and env config.

## How validation works

1. **At startup** — The SDK validates the license once against the server.
2. **On the 26th of each month at 00:00** (local time) — The SDK runs validation again automatically.
3. **If the server is unreachable** — The SDK retries (configurable); after the **grace period** it calls `on_invalid`.
4. **If the server returns invalid/expired/suspended** — The SDK calls `on_invalid` (after grace period if you use it).

The server validates the request using a signed payload (HMAC). Never expose the signing secret in client-side or public code; treat it like a server-side secret that only your deployed apps use.

## Handling errors

Catch SDK exceptions if you want to handle them yourself:

```python
from app_protection import protect, require_valid, ValidationFailedError, LicenseInvalidError

try:
    protect(...)
    require_valid()
except ValidationFailedError as e:
    # Network or server error
    log_error(e)
    exit(1)
except LicenseInvalidError as e:
    # Invalid or expired license
    show_message("License invalid.")
    exit(1)
```

## Security notes

- Store the **license key** and **signing secret** securely (env vars, secret manager, or OS keyring). Do not commit them to source control.
- The signing secret must match the server; it is used to sign every validation request so the server can reject tampering.
- Validation requests are rate-limited (e.g. 10 per hour per key); avoid calling validation in a tight loop.

## Next steps

- **API reference:** [api-reference.md](api-reference.md) and the live docs at `https://your-server/docs`.
- **Deployment:** [deployment-runbook.md](deployment-runbook.md) for running the SWAPS server.
