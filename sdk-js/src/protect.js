import { validateWithRetry } from './validate.js';
import { Enforcer } from './enforcer.js';
import { LicenseInvalidError } from './exceptions.js';

let _config = null;
let _enforcer = null;
let _dailyCheckInterval = null;

const ONE_DAY_MS = 24 * 60 * 60 * 1000;

function runValidationAndUpdateEnforcer() {
  if (!_config || !_enforcer) return;
  const backoffMs = (_config.retryBackoffMinutes ?? 5) * 60 * 1000;
  validateWithRetry({
    serverUrl: _config.serverUrl,
    licenseKey: _config.licenseKey,
    appId: _config.appId,
    signingSecret: _config.signingSecret,
    retryCount: _config.retryCount ?? 3,
    retryBackoffMs: backoffMs,
  })
    .then((data) => {
      if (data.valid === true) _enforcer.recordSuccess();
      else _enforcer.recordFailure();
    })
    .catch(() => {
      _enforcer.recordFailure();
    });
}

function is26th() {
  const d = new Date();
  return d.getDate() === 26;
}

function startMonthlySchedule() {
  if (_dailyCheckInterval != null) return;
  _dailyCheckInterval = setInterval(() => {
    if (is26th()) runValidationAndUpdateEnforcer();
  }, ONE_DAY_MS);
}

function stopMonthlySchedule() {
  if (_dailyCheckInterval != null) {
    clearInterval(_dailyCheckInterval);
    _dailyCheckInterval = null;
  }
}

/**
 * Call at app startup. Validates the license once, then schedules a daily check:
 * on the 26th of each month, re-validates. If validation fails (or server unreachable),
 * starts a grace period; after gracePeriodHours, calls onInvalid.
 *
 * @param {object} opts
 * @param {string} opts.licenseKey
 * @param {string} opts.serverUrl - Base URL (e.g. https://protection.example.com)
 * @param {string} opts.signingSecret - Same as server LICENSE_HMAC_SECRET
 * @param {string} [opts.appId='default']
 * @param {() => void} [opts.onInvalid] - Callback when invalid and grace period ended
 * @param {number} [opts.gracePeriodHours=48]
 * @param {number} [opts.retryCount=3]
 * @param {number} [opts.retryBackoffMinutes=5]
 */
export function protect(opts) {
  const {
    licenseKey,
    serverUrl,
    signingSecret,
    appId = 'default',
    onInvalid,
    gracePeriodHours = 48,
    retryCount = 3,
    retryBackoffMinutes = 5,
  } = opts;
  _config = {
    serverUrl: serverUrl.replace(/\/$/, ''),
    licenseKey,
    signingSecret,
    appId,
    onInvalid,
    gracePeriodHours,
    retryCount,
    retryBackoffMinutes,
  };
  _enforcer = new Enforcer(onInvalid, gracePeriodHours);
  runValidationAndUpdateEnforcer();
  startMonthlySchedule();
}

/**
 * Run validation once using the config from a previous protect() call.
 * Returns the server response or null if protect() was never called.
 * @returns {Promise<{ valid: boolean, status: string, expires_at?: string, message: string } | null>}
 */
export async function validateNow() {
  if (_config == null) return null;
  if (_enforcer == null) {
    _enforcer = new Enforcer(_config.onInvalid, _config.gracePeriodHours ?? 48);
  }
  const backoffMs = (_config.retryBackoffMinutes ?? 5) * 60 * 1000;
  try {
    const data = await validateWithRetry({
      serverUrl: _config.serverUrl,
      licenseKey: _config.licenseKey,
      appId: _config.appId,
      signingSecret: _config.signingSecret,
      retryCount: _config.retryCount ?? 3,
      retryBackoffMs: backoffMs,
    });
    if (data.valid === true) _enforcer.recordSuccess();
    else _enforcer.recordFailure();
    return data;
  } catch (e) {
    _enforcer.recordFailure();
    throw e;
  }
}

/**
 * Throw LicenseInvalidError if the license is not valid and grace period has ended.
 * Call at startup (after protect()) or before sensitive code.
 */
export function requireValid() {
  if (_enforcer == null) {
    throw new LicenseInvalidError('License has not been validated. Call protect() first.');
  }
  _enforcer.requireValid();
}

/**
 * Stop the monthly validation scheduler (e.g. at app exit).
 */
export function shutdownScheduler() {
  stopMonthlySchedule();
}
