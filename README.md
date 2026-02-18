# SWAPS — Software & Web Application Protection System

License verification platform: generate and validate license keys, enforce monthly checks, and manage licenses via an admin dashboard.

## Tech stack

- **Backend:** FastAPI, SQLAlchemy 2 (async), PostgreSQL 15, Alembic
- **Auth:** JWT (Sprint 2)
- **Client SDK:** Python package with APScheduler, keyring, httpx (Sprint 3)
- **Deploy:** Docker Compose, Nginx, SSL (Sprint 6)

## Repository structure

```
├── server/                 # FastAPI backend
│   ├── app/
│   │   ├── api/routes/     # auth, licenses
│   │   ├── core/           # config, database, security
│   │   ├── models/         # SQLAlchemy ORM
│   │   ├── schemas/        # Pydantic
│   │   ├── services/      # License key gen, CRUD, validation
│   │   └── templates/     # Admin dashboard (Jinja2)
│   └── migrations/        # Alembic
├── sdk/                    # Python client SDK (app_protection)
├── deploy/                 # Docker Compose, Nginx
├── docs/
├── pyproject.toml
└── alembic.ini
```

## Quick start (development)

1. **Create virtualenv and install dependencies**
   ```bash
   poetry install
   ```

2. **Start PostgreSQL (Docker)**
   ```bash
   docker compose -f deploy/docker-compose.yml up -d db
   ```

3. **Run migrations**
   ```bash
   cd server && alembic -c ../alembic.ini upgrade head
   ```
   (From repo root, ensure `PYTHONPATH` includes `server` or run from `server` with `alembic.ini` in parent.)

4. **Seed first admin** (once)
   ```bash
   cd server && python -m scripts.seed_admin
   ```
   Set `DEFAULT_ADMIN_EMAIL` and `DEFAULT_ADMIN_PASSWORD` in `.env`, or enter when prompted.

5. **Run the API**
   ```bash
   cd server && uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
   ```
   Health: [http://localhost:8000/health](http://localhost:8000/health), Docs: [http://localhost:8000/docs](http://localhost:8000/docs).

## API (Sprint 2)

- **POST /auth/login** — Body: `{ "email", "password" }` → returns `access_token`, `refresh_token`.
- **POST /auth/refresh** — Body: `{ "refresh_token" }` → new tokens.
- **POST /licenses/** — Create license (Bearer token). Response includes `license_key` **once**.
- **GET /licenses/** — List licenses (optional `status`, `client_name`, `skip`, `limit`).
- **GET /licenses/{id}**, **PATCH /licenses/{id}**, **DELETE /licenses/{id}** — Get, update, deactivate (admin).
- **POST /licenses/validate** — **Public.** Body: `license_key`, `app_id`, `timestamp`, `signature` (HMAC). Returns `valid`, `status`, `expires_at`, `message`.
- **GET /licenses/{id}/history** — Validation log for a license (admin).

Use the **Authorize** button in Swagger with the `access_token` for protected endpoints.

## Documentation

- **[Developer integration guide](docs/integration-guide.md)** — Step-by-step SDK integration (under 30 min).
- **[API reference](docs/api-reference.md)** — Endpoints summary; live docs at `/docs` and `/redoc` when the API is running.
- **[Deployment runbook](docs/deployment-runbook.md)** — From zero to production with Docker Compose.
- **[UAT checklist](docs/uat-checklist.md)** — User acceptance testing and go-live sign-off.

## Deployment (Sprint 6)

- **Docker Compose:** `docker compose -f deploy/docker-compose.yml up -d` — starts db, api, nginx. Nginx listens on port 80 and proxies to the API.
- **Rate limiting:** 100 requests/minute per IP (FastAPI middleware + Nginx); 10 validations/hour per license key (validation endpoint).
- **HTTPS:** See `deploy/certbot/README.md` for Let's Encrypt and `deploy/nginx/nginx.ssl.conf` for the HTTPS server block.
- **Runbook:** [docs/deployment-runbook.md](docs/deployment-runbook.md) — from scratch to running in under 30 minutes.

## Environment

Copy `.env.example` to `.env` and set at least `SECRET_KEY`, `LICENSE_HMAC_SECRET`, and `DATABASE_URL` for production.

## Testing (Sprint 7)

**1. Install dependencies** (required for pytest; from repo root):

```powershell
cd F:\git\mklab-keygen
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
pip install pytest pytest-asyncio pytest-cov httpx
```

**2. Run tests** (from repo root so `app` and server deps resolve):

```powershell
cd F:\git\mklab-keygen
$env:PYTHONPATH = "server"
pytest server/tests -v
```

For coverage, install pytest-cov then run:

```powershell
pip install pytest-cov
pytest server/tests -v --cov=server/app --cov-report=term-missing --cov-fail-under=60
```

**3. Load test (Locust)** — install then run from repo root:

```powershell
pip install locust
cd F:\git\mklab-keygen
locust -f tests/locustfile.py --host=http://localhost:8000
```

Then open http://localhost:8089 and spawn users (e.g. 500 for validation load).

**Troubleshooting:** If you see `ModuleNotFoundError: No module named 'sqlalchemy'`, install deps: `pip install -r requirements.txt` (from repo root). If `locust` is not recognized, run `pip install locust` and use the same venv.

**4. Security scan:** [docs/security-scan.md](docs/security-scan.md) — OWASP ZAP baseline.

## Project plan

See [SWAPS_Project_Plan_MVP.md](SWAPS_Project_Plan_MVP.md) for MVP scope, sprint plan, and technical specs.

**Current status:** Sprint 8 done — Developer integration guide, API reference, GitHub Actions CI, UAT checklist, go-live section. MVP complete.

### Admin dashboard (Sprint 4 & 5)

- **http://localhost:8000/admin** — License list with **summary** (active count, expiring in 30 days, recent validation failures). Filter by status, client, and **expiry date range**. Create, edit, deactivate; **History** per license.
- **http://localhost:8000/admin/audit** — Full **audit log**: all validation attempts with IP, timestamp, result, error.
- **http://localhost:8000/admin/licenses/{id}/history** — Validation history table for one license.
- **http://localhost:8000/admin/login** — Admin login (same credentials as API `/auth/login`). Session stored in HTTP-only cookie.

### Client SDK (Sprint 3)

Install and use in your app:

```bash
pip install -e sdk/
```

```python
from app_protection import protect

protect(
    license_key="LIC-MYAPP-...",
    server_url="https://protection.yourserver.com",
    signing_secret="same-as-server-LICENSE_HMAC_SECRET",
    on_invalid=lambda: exit(1),
)
```

- **Full integration guide:** [docs/integration-guide.md](docs/integration-guide.md)  
- **SDK options and env:** [sdk/README.md](sdk/README.md)
