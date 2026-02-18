export class LicenseError extends Error {
  constructor(message) {
    super(message);
    this.name = 'LicenseError';
  }
}

export class LicenseExpiredError extends LicenseError {
  constructor(message = 'License has expired.') {
    super(message);
    this.name = 'LicenseExpiredError';
  }
}

export class LicenseInvalidError extends LicenseError {
  constructor(message = 'License is invalid or revoked.') {
    super(message);
    this.name = 'LicenseInvalidError';
  }
}

export class ValidationFailedError extends LicenseError {
  constructor(message = 'Validation request failed.') {
    super(message);
    this.name = 'ValidationFailedError';
  }
}
