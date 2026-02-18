"""
Locust load test: simulate concurrent validation requests.
Run: locust -f tests/locustfile.py --host=http://localhost:8000
Then open http://localhost:8089 and spawn 500 users for validation endpoint.
"""

import time
from locust import HttpUser, task, between

# These must match a real license key and server signing secret for "valid" requests.
# For load testing invalid requests (still hits the endpoint), we use a fixed body.
VALIDATION_PAYLOAD = {
    "license_key": "LIC-LOADTEST-00000000-0000000000000000",
    "app_id": "loadtest",
    "timestamp": int(time.time()),
    "signature": "invalid-signature-for-load-test",
}


class ValidationUser(HttpUser):
    """User that repeatedly calls POST /licenses/validate."""
    wait_time = between(0.5, 1.5)

    @task(10)
    def validate(self):
        payload = {
            **VALIDATION_PAYLOAD,
            "timestamp": int(time.time()),
        }
        self.client.post("/licenses/validate", json=payload, name="/licenses/validate")

    @task(1)
    def health(self):
        self.client.get("/health", name="/health")
