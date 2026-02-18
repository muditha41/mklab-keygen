"""SDK exceptions."""


class LicenseError(Exception):
    """Base exception for license/validation errors."""


class LicenseExpiredError(LicenseError):
    """License has passed its expiry date."""


class LicenseInvalidError(LicenseError):
    """License key is invalid or revoked."""


class ValidationFailedError(LicenseError):
    """Validation request failed (network, server error)."""
