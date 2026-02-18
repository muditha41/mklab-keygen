# Software & Web Application Protection System (SWAPS)
### License Verification System — Project Plan & MVP Specification
> Version 1.0 | February 2026 | Confidential

---

## Table of Contents
1. [Executive Summary](#executive-summary)
2. [Project Overview](#project-overview)
3. [MVP Specification](#mvp-specification)
4. [Sprint Plan](#sprint-plan)
5. [Technical Specifications](#technical-specifications)
6. [Functional Requirements](#functional-requirements)
7. [Risk Register](#risk-register)
8. [Post-MVP Roadmap](#post-mvp-roadmap)
9. [Success Metrics](#success-metrics)
10. [Appendix](#appendix)

---

## Executive Summary

The **Software & Web Application Protection System (SWAPS)** is a centralized license validation platform designed to protect desktop and web applications from unauthorized use.

| | | | |
|---|---|---|---|
| **Project Duration** | 16 Weeks | **MVP Delivery** | Week 8 |
| **Total Sprints** | 8 Sprints | **Tech Stack** | FastAPI + PostgreSQL |

### What the System Does
- Generates unique, cryptographically-secure license keys
- Allows developers to embed the key into their apps with minimal effort (3 lines of code)
- Automatically validates license status on the **26th of each month at 12:00 AM** via secure API
- Disables or restricts application functionality when a license becomes invalid or expired
- Provides a full admin dashboard for license lifecycle management

---

## Project Overview

### 1.1 Objectives

- Generate unique HMAC-SHA256 license keys for each application deployment
- Allow developers to embed a secret key directly into their applications with minimal integration effort
- Automatically validate license status every month via a secure API call to the Protection Server
- Disable or restrict application functionality when a license becomes invalid, expired, or revoked
- Provide a full admin dashboard for license lifecycle management

### 1.2 System Architecture

```
Protected Application (Desktop / Web)
            │
            │  Monthly Validation Request (HTTPS + HMAC)
            │  26th of each month — 12:00 AM
            ▼
 ┌──────────────────────────────┐
 │  Protection Server (FastAPI) │
 │  REST API + Admin Dashboard  │
 └──────────────┬───────────────┘
                │  Validate Key + Expiry + Status
                ▼
 ┌──────────────────────────────┐
 │  PostgreSQL Database         │
 │  License Storage + Audit Log │
 └──────────────────────────────┘
```

### 1.3 Core Components

| Component | Description |
|-----------|-------------|
| **License Management Server** | FastAPI backend that generates, stores, and validates license keys. Central authority for all license decisions. |
| **Admin Dashboard** | Web-based management interface for creating, editing, and monitoring licenses and validation history. |
| **Client SDK (Python Package)** | Lightweight Python package embedded in protected apps. Handles scheduled validation, key storage, and enforcement. |
| **PostgreSQL Database** | Stores license records, client info, validation history, and audit logs with full encryption at rest. |
| **Scheduler / CRON Engine** | Triggers validation calls on the 26th of each month at 12:00 AM in the client app's local timezone. |

---

## MVP Specification

The MVP focuses on delivering a **fully functional, end-to-end license validation system in 8 weeks**. Post-MVP enhancements add analytics, multi-app support, and advanced security features.

### 3.1 MVP Feature Set

| Feature | Priority | Sprint | Effort |
|---------|----------|--------|--------|
| License Key Generation (HMAC-SHA256) | 🔴 Critical | S1 | 3 days |
| License CRUD API (Create, Read, Update, Deactivate) | 🔴 Critical | S1–S2 | 4 days |
| PostgreSQL Schema + Migrations (Alembic) | 🔴 Critical | S1 | 2 days |
| JWT Admin Authentication | 🔴 Critical | S2 | 3 days |
| License Validation Endpoint (`/validate`) | 🔴 Critical | S2 | 3 days |
| Client SDK — Core (Python Package) | 🔴 Critical | S3 | 5 days |
| Client SDK — Scheduler (26th/month trigger) | 🔴 Critical | S3 | 2 days |
| Client SDK — App Lock / Restriction Logic | 🟠 High | S4 | 3 days |
| Admin Dashboard — License Management UI | 🟠 High | S4–S5 | 5 days |
| Validation History & Audit Log | 🟠 High | S5 | 3 days |
| HTTPS + SSL (Let's Encrypt via Nginx) | 🟠 High | S6 | 1 day |
| Docker Compose Deployment | 🟠 High | S6 | 2 days |
| Unit Tests (80% coverage target) | 🟠 High | S7 | 4 days |
| Integration Tests & Validation Scenarios | 🟠 High | S7 | 3 days |
| Developer Integration Guide & SDK Docs | 🟠 High | S8 | 2 days |
| UAT + Bug Fixes | 🟠 High | S8 | 3 days |

### 3.2 Out of Scope (MVP)

The following features are excluded from the MVP and planned for post-launch iterations:

- Multi-tenant architecture (multiple admin organizations)
- Real-time analytics dashboard with usage graphs
- Webhook notifications on license events
- SDK clients for languages other than Python (Node.js, .NET, Java, Go)
- Offline grace period with cryptographic offline tokens
- Hardware fingerprint / machine binding
- White-label / customizable branding per client

---

## Sprint Plan

> **8 two-week sprints | 16 weeks total**
> Sprints 1–4 build core infrastructure. Sprints 5–6 complete the full feature set. Sprints 7–8 cover testing, deployment, and documentation.

| Sprint | Name | Weeks | Focus |
|--------|------|-------|-------|
| Sprint 1 | Foundation & Database | 1–2 | Project setup, DB schema, key generation, core models |
| Sprint 2 | API Core & Auth | 3–4 | JWT auth, license CRUD APIs, validation endpoint |
| Sprint 3 | Client SDK | 5–6 | Python SDK, scheduler, key storage, API integration |
| Sprint 4 | Enforcement & Dashboard | 7–8 | App lock logic, admin UI — **MVP milestone** |
| Sprint 5 | Admin Dashboard II | 9–10 | Audit logs, validation history, license search/filter |
| Sprint 6 | Deployment & Security | 11–12 | Docker, Nginx, SSL, rate limiting, security hardening |
| Sprint 7 | Testing | 13–14 | Unit tests, integration tests, load testing, security scan |
| Sprint 8 | Docs & Release | 15–16 | SDK docs, dev guide, UAT, production deployment |

---

### Sprint 1 — Foundation & Database (Weeks 1–2)

**Goals:**
- Initialize project repository with Git branching strategy (`main / develop / feature/*`)
- Set up FastAPI project skeleton with dependency management (Poetry)
- Design and implement PostgreSQL schema with Alembic migration tooling
- Implement HMAC-SHA256 license key generation algorithm
- Configure Docker development environment

**Database Schema — Core Tables:**

| Table | Key Fields |
|-------|------------|
| `licenses` | id, license_key (hashed), app_name, client_name, expiry_date, status, monthly_renewal, created_at |
| `applications` | id, name, description, owner_email, created_at |
| `validation_logs` | id, license_id, validated_at, ip_address, result (success/fail), error_reason |
| `admins` | id, email, password_hash, role, last_login, is_active |

---

### Sprint 2 — API Core & Authentication (Weeks 3–4)

**API Endpoints (MVP):**

| Endpoint | Description |
|----------|-------------|
| `POST /auth/login` | Admin login — returns JWT access + refresh tokens |
| `POST /licenses/` | Create a new license (admin only) |
| `GET /licenses/` | List all licenses with filters (admin only) |
| `GET /licenses/{id}` | Get single license details |
| `PATCH /licenses/{id}` | Update license fields (status, expiry, etc.) |
| `DELETE /licenses/{id}` | Soft-delete / deactivate a license |
| `POST /licenses/validate` | **Public** — validates a license key (called by SDK) |
| `GET /licenses/{id}/history` | Get validation history for a license |

---

### Sprint 3 — Client SDK (Weeks 5–6)

**SDK Package Structure:**

```
app_protection/
  __init__.py          # Public API: protect(), validate_now()
  client.py            # HTTP client for validation API
  scheduler.py         # APScheduler: 26th/month 12:00 AM trigger
  storage.py           # Secure local key storage (keyring / env)
  enforcer.py          # App lock / restriction logic
  exceptions.py        # LicenseExpiredError, ValidationFailedError
  config.py            # Server URL, retry settings, grace period
setup.py               # Package distribution
```

**Developer Integration — 3 Lines of Code:**

```python
from app_protection import protect

# Called at app startup — validates once, then schedules monthly checks
protect(
    license_key="LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C",
    server_url="https://protection.yourserver.com",
    on_invalid=lambda: disable_app_features()  # Your enforcement callback
)
```

---

### Sprint 4 — Enforcement & Dashboard (Weeks 7–8) — ✅ MVP Milestone

- App lock / restriction enforcement via the `on_invalid` callback
- Admin dashboard: license list, create/edit/deactivate forms
- End-to-end test: key generation → embedding → validation → enforcement

---

### Sprint 5 — Admin Dashboard II (Weeks 9–10)

- Validation history table per license
- Full audit log with IP, timestamp, result, and error detail
- License search and filter (by status, client, expiry date range)
- Dashboard summary: active licenses count, recent failures, expiring soon

---

### Sprint 6 — Deployment & Security (Weeks 11–12)

- Docker Compose: `api`, `db`, `nginx` services
- Nginx reverse proxy config with SSL termination
- Let's Encrypt certificate via Certbot (auto-renewal cron)
- Rate limiting: 100 req/min per IP globally; 10 validations/hour per license key
- Environment variable management via `.env` + Docker secrets

---

### Sprint 7 — Testing (Weeks 13–14)

- Unit tests: all service layer functions (target 80%+ coverage via `pytest-cov`)
- Integration tests: full request/response cycle using `httpx` async client
- Validation scenario tests: expired license, invalid key, suspended, network timeout
- Load test: simulate 500 concurrent validation requests (locust)
- Security scan: OWASP ZAP baseline scan on the API

---

### Sprint 8 — Docs & Release (Weeks 15–16)

- Developer SDK integration guide (Markdown + hosted on README)
- API reference documentation (auto-generated via FastAPI's OpenAPI/Swagger)
- Deployment runbook (step-by-step from zero to production)
- User Acceptance Testing with stakeholders
- Production deployment and go-live

---

## Technical Specifications

### 5.1 Technology Stack

| Layer | Technology & Rationale |
|-------|----------------------|
| **Backend Framework** | FastAPI (Python 3.11+) — async-first, auto-generated OpenAPI docs, high performance |
| **Database** | PostgreSQL 15 — ACID compliance, JSON support, mature ecosystem |
| **ORM** | SQLAlchemy 2.0 + Alembic — async ORM with migration support |
| **Authentication** | JWT (access: 15 min, refresh: 7 days) via `python-jose` + `passlib` |
| **Key Security** | HMAC-SHA256 for key generation; keys stored as salted hashes, never plaintext |
| **Client Scheduler** | APScheduler 3.x — lightweight Python scheduler with cron-style triggers |
| **Local Key Storage** | Python `keyring` library — OS-native secure storage (Keychain / Credential Manager) |
| **Containerization** | Docker + Docker Compose — reproducible environments across dev/staging/prod |
| **Reverse Proxy** | Nginx — SSL termination, rate limiting, static file serving |
| **SSL** | Let's Encrypt via Certbot — free, auto-renewing certificates |
| **Admin UI** | Jinja2 templates + HTMX — server-side rendered, minimal JS complexity |
| **Testing** | pytest + httpx (async) + pytest-cov — targeting 80%+ coverage |
| **CI/CD** | GitHub Actions — lint (ruff), test, build Docker image on push |

---

### 5.2 Security Design

#### License Key Format

```
LIC-{APP_CODE}-{TIMESTAMP_HEX}-{HMAC_TRUNCATED}

Example: LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C

Generation:  HMAC-SHA256(secret_seed + app_id + timestamp)
             → truncated to 16 hex chars
Storage:     Only SHA256 hash of key stored in DB
             Original key shown ONCE at generation time, never again
```

#### Validation Request Security

Every validation request from the SDK is signed to prevent tampering and replay attacks:

```
Request Body:
{
  "license_key": "LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C",
  "app_id": "myapp-v2",
  "timestamp": 1740614400,
  "signature": HMAC-SHA256(license_key + app_id + timestamp, shared_secret)
}
```

**Security Controls:**
- All traffic over HTTPS (TLS 1.2 minimum, TLS 1.3 preferred)
- Timestamp in request must be within a **5-minute window** (replay attack prevention)
- Rate limiting: **10 validation requests per license key per hour**
- Validation endpoint returns minimal data to prevent enumeration
- Database fields encrypted at rest; VPC-isolated infrastructure

---

## Functional Requirements

### 6.1 License Lifecycle

| Status | Behavior |
|--------|----------|
| **Active** | Validation passes — application runs normally |
| **Inactive** | Validation fails immediately — application blocked |
| **Expired** | Validation fails if past `expiry_date` — application blocked |
| **Suspended** | Temporary block — reactivatable by admin without a new key |
| **Pending** | Created but not yet activated — validation returns pending state |

### 6.2 Admin License Fields

When creating a license, the admin defines:

- **Application Name** — which application this license covers
- **Client Name** — the customer or organization receiving the license
- **Expiry Date** — when the license becomes invalid
- **Status** — Active / Inactive / Suspended / Pending
- **Monthly Renewal Flag** — whether the license requires re-validation on the 26th

### 6.3 Validation Flow (Step-by-Step)

```
1. SDK scheduler triggers on the 26th of the month at 12:00 AM local time
2. SDK retrieves stored license key from OS keyring / environment variable
3. SDK builds signed request: {license_key, timestamp, app_id, HMAC_signature}
4. HTTPS POST sent to /licenses/validate on the Protection Server
5. Server verifies HMAC signature and timestamp freshness (5-min window)
6. Server queries DB: checks key hash, status, and expiry_date
7. Server records result in validation_logs (success or failure)
8. Server returns:
   {
     "valid": true | false,
     "status": "active" | "expired" | "suspended" | ...,
     "expires_at": "2026-12-31T00:00:00Z",
     "message": "License valid"
   }
9. SDK response handling:
   → valid=true:  schedule next check, app runs normally
   → valid=false: call on_invalid() callback, restrict/block app
10. Network failure handling:
   → Retry 3x with 5-minute backoff
   → Enter 48-hour grace period if still unreachable
   → Block app after grace period expires
```

---

## Risk Register

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| License key interception during transit | 🟢 Low | 🔴 High | HTTPS + HMAC signing; key never transmitted in plaintext after generation |
| Validation server downtime blocks clients | 🟠 Medium | 🔴 High | 48-hour grace period in SDK; load balancing; uptime monitoring with alerts |
| SDK reverse engineering exposes secret | 🟠 Medium | 🟠 Medium | Server-side validation is authoritative; bypassing SDK still requires valid HMAC |
| Database breach exposes license data | 🟢 Low | 🔴 High | Keys stored as hashes; DB encrypted at rest; VPC isolation; least-privilege access |
| Scope creep extends timeline | 🔴 High | 🟠 Medium | Strict MVP scope lock; feature requests logged to backlog; bi-weekly reviews |
| Developer adoption friction | 🟠 Medium | 🟠 Medium | 3-line SDK integration; comprehensive docs; example projects provided |

---

## Post-MVP Roadmap

### Phase 2 — Enhanced Security & Analytics (Months 5–6)

- Hardware fingerprint / machine binding for stricter enforcement
- Offline cryptographic tokens (signed JWT with TTL for air-gapped environments)
- Real-time analytics dashboard: validation rate, geographic distribution, failure trends
- Webhook system: POST to developer-defined URLs on license events (expiry, failure, renewal)

### Phase 3 — Multi-Language SDK & Scalability (Months 7–9)

- SDK clients for Node.js, Java, .NET, Go, and PHP
- Multi-tenant architecture: separate organizations with isolated license namespaces
- Horizontal scaling: Redis caching for validation results, PostgreSQL read replicas
- SLA: 99.9% uptime target with automated failover

### Phase 4 — Enterprise Features (Months 10–12)

- White-label dashboard with custom branding per enterprise client
- SAML / SSO integration for enterprise admin authentication
- License metering / usage-based licensing (API call counting)
- Compliance reporting: SOC 2 audit log export, GDPR data management tools

---

## Success Metrics

### 9.1 MVP Acceptance Criteria

- [ ] License key generation produces unique, non-guessable keys 100% of the time
- [ ] Validation API responds in under **200ms (p95)** under normal load
- [ ] Client SDK successfully triggers validation on the 26th within a 1-minute window
- [ ] Admin can perform full license lifecycle management via dashboard without engineering support
- [ ] System correctly blocks application access within **60 seconds** of license invalidation
- [ ] All API endpoints protected by JWT with proper role enforcement
- [ ] **80%+** unit test coverage on server-side code
- [ ] Deployment reproducible from scratch in under **30 minutes** using Docker Compose

### 9.2 Technical KPIs

| Metric | Target |
|--------|--------|
| Validation API latency (p95) | < 200ms |
| System uptime | > 99.5% |
| Test coverage | > 80% |
| SDK integration time (developer) | < 30 minutes |
| License key collision probability | < 1 in 10³⁸ (cryptographically negligible) |
| Validation replay window | 5 minutes maximum |
| Grace period on server unreachable | 48 hours |

---

## Appendix

### Repository Structure

```
swaps/
├── server/                        # FastAPI backend
│   ├── app/
│   │   ├── api/
│   │   │   └── routes/            # Endpoint handlers (licenses, auth, admin)
│   │   ├── core/                  # Config, security utils, DB connection
│   │   ├── models/                # SQLAlchemy ORM models
│   │   ├── schemas/               # Pydantic request/response schemas
│   │   ├── services/              # Business logic (license service, key gen)
│   │   └── templates/             # Jinja2 admin dashboard templates
│   ├── migrations/                # Alembic DB migrations
│   └── tests/                     # pytest test suite
│       ├── unit/
│       └── integration/
├── sdk/                           # Python client SDK
│   └── app_protection/
│       ├── __init__.py
│       ├── client.py
│       ├── scheduler.py
│       ├── storage.py
│       ├── enforcer.py
│       ├── exceptions.py
│       └── config.py
├── deploy/                        # Infrastructure configs
│   ├── docker-compose.yml
│   ├── docker-compose.prod.yml
│   ├── nginx/
│   │   └── nginx.conf
│   └── certbot/
├── docs/                          # Developer guides & API reference
│   ├── integration-guide.md
│   ├── api-reference.md
│   └── deployment-runbook.md
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD pipeline
├── pyproject.toml
└── README.md
```

### Environment Variables

```env
# Server
DATABASE_URL=postgresql+asyncpg://user:pass@db:5432/swaps
SECRET_KEY=your-super-secret-key-min-32-chars
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=15
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7
LICENSE_HMAC_SECRET=your-hmac-secret-for-key-generation

# Client SDK
SWAPS_SERVER_URL=https://protection.yourserver.com
SWAPS_LICENSE_KEY=LIC-XXXX-XXXX-XXXX-XXXX
SWAPS_GRACE_PERIOD_HOURS=48
```

### Docker Compose (Simplified)

```yaml
version: "3.9"
services:
  api:
    build: ./server
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - SECRET_KEY=${SECRET_KEY}
    depends_on: [db]
    
  db:
    image: postgres:15
    volumes:
      - pgdata:/var/lib/postgresql/data
    environment:
      - POSTGRES_DB=swaps
      - POSTGRES_USER=${DB_USER}
      - POSTGRES_PASSWORD=${DB_PASSWORD}
      
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./deploy/certbot/conf:/etc/letsencrypt
    depends_on: [api]

volumes:
  pgdata:
```

---

*SWAPS — Software & Web Application Protection System | v1.0 | February 2026*
