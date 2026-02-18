# SWAPS Deployment Runbook

Reproducible deployment from scratch in under 30 minutes using Docker Compose.

## Prerequisites

- Docker and Docker Compose (v2+)
- (Optional) Domain and DNS pointing to the server for HTTPS

## 1. Clone and configure

```bash
git clone <repo-url> swaps && cd swaps
cp .env.example .env
```

Edit `.env` and set at least:

- `SECRET_KEY` — random string, min 32 characters
- `LICENSE_HMAC_SECRET` — secret for key generation and validation signing
- `DB_PASSWORD` — PostgreSQL password (and `DB_USER` if changed)

For production, do **not** leave default values for `SECRET_KEY` or `LICENSE_HMAC_SECRET`.

## 2. Start stack (dev: API + DB + Nginx)

```bash
docker compose -f deploy/docker-compose.yml up -d
```

This starts:

- **db** — PostgreSQL 15 on host port 5432
- **api** — FastAPI on host port 8000 (and reachable via nginx)
- **nginx** — Reverse proxy on host port 80 → `http://api:8000`

Health: `curl http://localhost:80/health` or `curl http://localhost:8000/health`.

## 3. Run migrations

```bash
# From repo root, with app on Python path
cd server
export PYTHONPATH=.
# Use DATABASE_URL from .env (point to db host; from host use localhost:5432)
pip install -r ../requirements.txt   # or poetry install
alembic -c ../alembic.ini upgrade head
```

If DB is in Docker and you run Alembic on the host, set `DATABASE_URL=postgresql+asyncpg://swaps:YOUR_DB_PASSWORD@localhost:5432/swaps`.

Alternatively run migrations inside the API container (uses same DATABASE_URL as api service):

```bash
docker compose -f deploy/docker-compose.yml run --rm api \
  sh -c "cd /app && alembic -c alembic.ini upgrade head"
```

## 4. Create first admin

```bash
cd server
DEFAULT_ADMIN_EMAIL=admin@example.com DEFAULT_ADMIN_PASSWORD=your-secure-password python -m scripts.seed_admin
```

Or run the seed script interactively and enter email/password when prompted. Use the same `DATABASE_URL` as the API (e.g. `localhost:5432` when DB is in Docker).

## 5. Verify

- Dashboard: http://localhost:80/admin (or http://localhost:8000/admin) — log in with the admin you created.
- API docs: http://localhost:80/docs (or :8000/docs).

## Production override

- Use the prod override so the API is not exposed on the host and only Nginx is public:

  ```bash
  docker compose -f deploy/docker-compose.yml -f deploy/docker-compose.prod.yml up -d
  ```

- Ensure `.env` has strong `SECRET_KEY`, `LICENSE_HMAC_SECRET`, and `DB_PASSWORD` (no defaults).

## Environment variables and secrets

- **Development:** Use a `.env` file (copy from `.env.example`); never commit `.env`.
- **Production:** Prefer loading secrets from the environment (CI or host) or Docker secrets. Example with Docker secrets:
  - Create secrets: `echo -n "your-secret" | docker secret create swaps_secret_key -`
  - In `docker-compose.prod.yml`, add `secrets: [swaps_secret_key]` to the api service and `environment: SECRET_KEY: /run/secrets/swaps_secret_key` (or use a wrapper that reads the file). Standard Compose doesn’t support reading secret into env in one line; use a script or stack deploy with long syntax.
- For simplicity, many deployments use a `.env` on the server with restricted permissions (`chmod 600 .env`).

## HTTPS (Let's Encrypt)

1. Point your domain (e.g. `protection.yourserver.com`) to the server.
2. Mount certbot volumes and get a cert — see `deploy/certbot/README.md`.
3. Add the HTTPS server block to `deploy/nginx/nginx.conf` (see `deploy/nginx/nginx.ssl.conf`) and reload Nginx.
4. Set up cert renewal (cron or systemd) as in `deploy/certbot/README.md`.

## Rate limiting

- **Global:** 100 requests per minute per IP (FastAPI middleware + Nginx `limit_req`).
- **Validation endpoint:** 10 validations per hour per license key (in-app).

## Troubleshooting

- **502 Bad Gateway** — API not ready or crashed. Check `docker compose -f deploy/docker-compose.yml logs api`.
- **DB connection refused** — Wait for DB healthcheck, or check `DATABASE_URL` and that port 5432 is reachable.
- **429 Too Many Requests** — Rate limit exceeded; wait 60 seconds or increase `RATE_LIMIT_PER_MINUTE_PER_IP` in `.env` (default 100).

## Go-live checklist

Before production release:

1. **Secrets** — `SECRET_KEY`, `LICENSE_HMAC_SECRET`, and `DB_PASSWORD` are strong and not defaults.
2. **Migrations** — `alembic upgrade head` has been run on the production DB.
3. **First admin** — At least one admin account created via `scripts/seed_admin`.
4. **HTTPS** — Certificates installed and Nginx configured for 443 (see Certbot section).
5. **UAT** — [docs/uat-checklist.md](uat-checklist.md) signed off by stakeholders.
6. **Monitoring** — Health endpoint (`/health`) monitored; alerts on 5xx or downtime.
7. **Backups** — PostgreSQL backup strategy in place (e.g. daily dumps or managed DB backups).
