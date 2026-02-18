# OWASP ZAP Baseline Scan (Sprint 7)

Run a baseline scan against the SWAPS API to detect common vulnerabilities.

## Prerequisites

- Docker, or [ZAP](https://www.zaproxy.org/download/) installed locally
- API running (e.g. `http://localhost:8000`)

## Using Docker (ZAP baseline)

```bash
docker run -t owasp/zap2docker-stable zap-baseline.py \
  -t http://host.docker.internal:8000 \
  -r zap-report.html
```

On Linux use the host IP instead of `host.docker.internal`, e.g. `-t http://172.17.0.1:8000`.

## Using ZAP GUI

1. Start ZAP and run **Automated Scan**.
2. Enter the API URL (e.g. `http://localhost:8000`).
3. Optional: add the API docs URL for broader coverage: `http://localhost:8000/docs`.
4. Review **Alerts** after the scan.

## What to fix

- **High/Critical:** Fix before release.
- **Medium:** Plan fixes (e.g. missing security headers, cookie flags).
- **Low/Info:** Optional (e.g. missing HSTS when not using HTTPS in dev).

## CI

To run in CI, use the Docker baseline and fail the job if the report contains High/Critical alerts, or use `zap-baseline.py -I` to ignore only false positives.
