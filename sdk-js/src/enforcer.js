import { LicenseInvalidError } from './exceptions.js';

/**
 * Tracks license validity. On validation failure, starts grace period; when grace
 * period expires, calls onInvalid once and marks app as restricted.
 */
export class Enforcer {
  /**
   * @param {() => void} [onInvalid]
   * @param {number} [gracePeriodHours=48]
   */
  constructor(onInvalid, gracePeriodHours = 48) {
    this.onInvalid = onInvalid;
    this.gracePeriodMs = gracePeriodHours * 3600 * 1000;
    this._valid = null; // null = not yet determined
    this._failureTime = null;
    this._invalidCalled = false;
  }

  get isValid() {
    return this._valid;
  }

  get isRestricted() {
    if (this._valid === true) return false;
    if (this._invalidCalled) return true;
    if (this._failureTime == null) return false;
    return Date.now() - this._failureTime >= this.gracePeriodMs;
  }

  recordSuccess() {
    this._valid = true;
    this._failureTime = null;
  }

  recordFailure() {
    if (this._failureTime == null) this._failureTime = Date.now();
    this._valid = false;
    if (this._invalidCalled) return;
    if (Date.now() - this._failureTime >= this.gracePeriodMs) {
      this._invalidCalled = true;
      if (this.onInvalid) this.onInvalid();
    }
  }

  checkGracePeriod() {
    if (this._valid === true || this._failureTime == null || this._invalidCalled) return;
    if (Date.now() - this._failureTime >= this.gracePeriodMs) {
      this._invalidCalled = true;
      if (this.onInvalid) this.onInvalid();
    }
  }

  requireValid() {
    this.checkGracePeriod();
    if (this._invalidCalled) {
      throw new LicenseInvalidError('Application access is restricted (invalid or expired license).');
    }
    if (this._valid === false && this.isRestricted) {
      throw new LicenseInvalidError('Application access is restricted.');
    }
    if (this._valid === null) {
      throw new LicenseInvalidError('License has not been validated yet.');
    }
  }
}
