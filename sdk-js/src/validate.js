import { computeSignature } from './signature.js';
import { ValidationFailedError } from './exceptions.js';

/**
 * POST to server /licenses/validate with signed body.
 * @param {object} opts
 * @param {string} opts.serverUrl - Base URL (no trailing slash)
 * @param {string} opts.licenseKey
 * @param {string} opts.appId
 * @param {string} opts.signingSecret
 * @param {number} [opts.timeoutMs=30000]
 * @returns {Promise<{ valid: boolean, status: string, expires_at?: string, message: string }>}
 * @throws {ValidationFailedError}
 */
export async function validate({
  serverUrl,
  licenseKey,
  appId,
  signingSecret,
  timeoutMs = 30000,
}) {
  const url = `${serverUrl.replace(/\/$/, '')}/licenses/validate`;
  const timestamp = Math.floor(Date.now() / 1000);
  const signature = computeSignature(licenseKey, appId, timestamp, signingSecret);
  const body = {
    license_key: licenseKey,
    app_id: appId,
    timestamp,
    signature,
  };
  try {
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    const res = await fetch(url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(body),
      signal: controller.signal,
    });
    clearTimeout(timeout);
    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }
    const data = await res.json();
    if (typeof data.valid !== 'boolean' || data.status == null || data.message == null) {
      throw new Error('Invalid response from server');
    }
    return data;
  } catch (err) {
    throw new ValidationFailedError(
      `Validation request failed: ${err?.message ?? err}`
    );
  }
}

/**
 * Call validate(); on failure retry up to retryCount times with retryBackoffMs delay.
 * @param {object} opts - Same as validate() plus:
 * @param {number} [opts.retryCount=3]
 * @param {number} [opts.retryBackoffMs=300000] - 5 min default
 */
export async function validateWithRetry(opts) {
  const {
    retryCount = 3,
    retryBackoffMs = 5 * 60 * 1000,
    ...validateOpts
  } = opts;
  let lastError;
  for (let attempt = 0; attempt < retryCount; attempt++) {
    try {
      return await validate(validateOpts);
    } catch (e) {
      lastError = e;
      if (attempt < retryCount - 1) {
        await new Promise((r) => setTimeout(r, retryBackoffMs));
      }
    }
  }
  throw lastError;
}
