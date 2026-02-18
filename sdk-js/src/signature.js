import crypto from 'crypto';

/**
 * Compute request signature (must match server: payload = license_key|app_id|timestamp).
 * HMAC-SHA256, base64-encoded, trailing '=' stripped.
 * @param {string} licenseKey
 * @param {string} appId
 * @param {number} timestamp - Unix seconds
 * @param {string} secret - Same as server LICENSE_HMAC_SECRET
 * @returns {string}
 */
export function computeSignature(licenseKey, appId, timestamp, secret) {
  const payload = `${licenseKey}|${appId}|${timestamp}`;
  const sig = crypto
    .createHmac('sha256', Buffer.from(secret, 'utf8'))
    .update(payload, 'utf8')
    .digest();
  return sig.toString('base64').replace(/=+$/, '');
}
