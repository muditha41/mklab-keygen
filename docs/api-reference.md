# SWAPS API Reference

The SWAPS API is a REST API for license management and validation. This page summarizes endpoints; for interactive docs and request/response schemas use the **live OpenAPI** UI.

## Live documentation

When the API is running:

- **Swagger UI:** `https://your-server/docs` — try endpoints from the browser.
- **ReDoc:** `https://your-server/redoc` — read-only API docs.
- **OpenAPI JSON:** `https://your-server/openapi.json` — machine-readable schema.

## Base URL and auth

- **Base URL:** Your deployment base (e.g. `https://protection.yourserver.com`).
- **Admin endpoints** require a JWT: send `Authorization: Bearer <access_token>`.
- **Validation** is public but requires a signed body (HMAC); the client SDK handles signing.

## Endpoints

### Health

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| GET | `/health` | No | Health check; returns `{"status":"ok","service":"swaps"}`. |

### Authentication

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/auth/login` | No | Login. Body: `{"email":"...","password":"..."}`. Returns `access_token`, `refresh_token`. |
| POST | `/auth/refresh` | No | Refresh tokens. Body: `{"refresh_token":"..."}`. Returns new `access_token`, `refresh_token`. |

### Licenses (admin)

All require `Authorization: Bearer <access_token>`.

| Method | Path | Description |
|--------|------|-------------|
| POST | `/licenses/` | Create license. Body: `app_name`, `client_name`, `expiry_date`, `status`, `monthly_renewal`. Response includes `license_key` **once**. |
| GET | `/licenses/` | List licenses. Query: `status`, `client_name`, `expiry_from`, `expiry_to`, `skip`, `limit`. |
| GET | `/licenses/{id}` | Get one license. |
| PATCH | `/licenses/{id}` | Update license. Body: optional `app_name`, `client_name`, `expiry_date`, `status`, `monthly_renewal`. |
| DELETE | `/licenses/{id}` | Deactivate license (soft delete). |
| GET | `/licenses/{id}/history` | Validation history for the license. |

### Validation (public)

| Method | Path | Auth | Description |
|--------|------|------|-------------|
| POST | `/licenses/validate` | No (signed body) | Validate a license. Body: `license_key`, `app_id`, `timestamp` (Unix s), `signature` (HMAC). Returns `valid`, `status`, `expires_at`, `message`. |

**Validation request body:**

```json
{
  "license_key": "LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C",
  "app_id": "default",
  "timestamp": 1740614400,
  "signature": "<HMAC-SHA256 base64>"
}
```

**Validation response:**

```json
{
  "valid": true,
  "status": "active",
  "expires_at": "2026-12-31T00:00:00Z",
  "message": "License valid"
}
```

`status` can be: `active`, `expired`, `suspended`, `inactive`, `pending`, `invalid`, `rate_limited`.

## Rate limits

- **Global:** 100 requests per minute per IP.
- **Validation:** 10 validation requests per license key per hour.

## Errors

- **401** — Missing or invalid JWT (admin endpoints).
- **403** — Inactive admin or forbidden.
- **404** — License or resource not found.
- **422** — Validation error (invalid body or query).
- **429** — Too many requests (rate limit).

Use the **Swagger UI** at `/docs` for exact request/response schemas and error models.
