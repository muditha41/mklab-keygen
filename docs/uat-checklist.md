# SWAPS UAT Checklist (Sprint 8)

Use this checklist for User Acceptance Testing with stakeholders before go-live.

## Admin dashboard

- [ ] Log in at `/admin/login` with seeded admin credentials.
- [ ] Create a new license; copy and store the displayed license key (shown once).
- [ ] List licenses; filter by status and client name and expiry range.
- [ ] Edit a license (change status, expiry, client name); save and confirm changes.
- [ ] Deactivate a license; confirm it no longer validates successfully.
- [ ] Open validation history for a license; confirm entries show time, IP, result, error.
- [ ] Open Audit log; confirm all validation attempts are listed with app/client/IP/result.
- [ ] Dashboard summary shows correct active count, expiring soon, recent failures.

## API (Swagger at `/docs`)

- [ ] **POST /auth/login** with valid admin → returns `access_token` and `refresh_token`.
- [ ] **POST /auth/login** with invalid credentials → 401.
- [ ] **GET /licenses/** with Bearer token → list of licenses.
- [ ] **GET /licenses/** without token → 401.
- [ ] **POST /licenses/** with valid body and token → 201 and response includes `license_key` once.
- [ ] **POST /licenses/validate** with valid signature and existing active license → `valid: true`.
- [ ] **POST /licenses/validate** with invalid signature or unknown key → `valid: false`, appropriate status/message.
- [ ] **PATCH /licenses/{id}** and **DELETE /licenses/{id}** require auth and behave as expected.

## Client SDK

- [ ] Install SDK (`pip install -e sdk/`); run a small script that calls `protect(license_key=..., server_url=..., signing_secret=...)` with a valid key → no error, app continues.
- [ ] Use an invalid or expired key (or wrong signing secret) → after grace period (or immediately depending on flow), `on_invalid` is called or `require_valid()` raises.
- [ ] Optional: confirm validation runs on the 26th (or trigger manually via `validate_now()`).

## Deployment and security

- [ ] Deploy with Docker Compose (runbook); API and admin are reachable.
- [ ] HTTPS works when certificates are configured (optional for UAT).
- [ ] Rate limiting: 100 req/min per IP and 10 validations/hour per key are enforced (optional spot check).

## Sign-off

| Role        | Name | Date | Notes |
|------------|------|------|-------|
| Product    |      |      |       |
| Engineering|      |      |       |
| Security   |      |      |       |
