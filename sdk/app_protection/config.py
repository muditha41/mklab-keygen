"""SDK configuration: server URL, retry, grace period."""

import os
from dataclasses import dataclass
from typing import Callable


@dataclass
class ProtectionConfig:
    """Runtime config for the protection client."""

    server_url: str
    license_key: str
    signing_secret: str  # Must match server LICENSE_HMAC_SECRET for validation requests
    app_id: str = "default"
    on_invalid: Callable[[], None] | None = None
    grace_period_hours: int = 48
    retry_count: int = 3
    retry_backoff_minutes: int = 5

    @classmethod
    def from_env(cls) -> "ProtectionConfig | None":
        """Build config from environment (SWAPS_SERVER_URL, SWAPS_LICENSE_KEY, SWAPS_SIGNING_SECRET)."""
        url = os.environ.get("SWAPS_SERVER_URL")
        key = os.environ.get("SWAPS_LICENSE_KEY")
        secret = os.environ.get("SWAPS_SIGNING_SECRET")
        if not url or not key or not secret:
            return None
        return cls(
            server_url=url.rstrip("/"),
            license_key=key,
            signing_secret=secret,
            app_id=os.environ.get("SWAPS_APP_ID", "default"),
            grace_period_hours=int(os.environ.get("SWAPS_GRACE_PERIOD_HOURS", "48")),
            retry_count=int(os.environ.get("SWAPS_RETRY_COUNT", "3")),
            retry_backoff_minutes=int(os.environ.get("SWAPS_RETRY_BACKOFF_MINUTES", "5")),
        )
