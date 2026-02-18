# @mklab/swaps-client

SWAPS license validation client for **Node.js**. Validates your app against the SWAPS protection server (same API as the Python SDK).

- **Validate once** or **protect** your app: validate at startup and on the **26th of each month**.
- **Grace period**: if the server is unreachable, the app keeps running for a configurable period (default 48h) before calling your `onInvalid` callback.

**Requires Node 18+** (uses native `fetch` and `crypto`).

## Install

From repo root (local):

```bash
npm install ./sdk-js
```

Or from npm (when published):

```bash
npm install @mklab/swaps-client
```

## Usage (3 lines)

```js
import { protect, requireValid } from '@mklab/swaps-client';

protect({
  licenseKey: 'LIC-MYAPP-018E2F3A-7B9D2C1E4F5A6B8C',
  serverUrl: 'https://protection.yourserver.com',
  signingSecret: 'your-hmac-secret',  // same as server LICENSE_HMAC_SECRET
  onInvalid: () => process.exit(1),
});

requireValid();  // throws if invalid after grace period
// ... run your app
```

## API

### `protect(options)`

Call at app startup. Validates once, then re-validates on the **26th of each month**.

| Option | Type | Description |
|--------|------|-------------|
| `licenseKey` | string | The license key (from admin dashboard). |
| `serverUrl` | string | Base URL of the SWAPS server. |
| `signingSecret` | string | Must match server `LICENSE_HMAC_SECRET`. |
| `appId` | string | Optional; default `"default"`. |
| `onInvalid` | () => void | Callback when license is invalid and grace period has ended. |
| `gracePeriodHours` | number | Default `48`. |
| `retryCount` | number | Default `3`. |
| `retryBackoffMinutes` | number | Default `5`. |

### `requireValid()`

Call after `protect()` (e.g. at startup or before sensitive code). **Throws** `LicenseInvalidError` if the license is invalid and the grace period has ended.

### `validateNow()`

Run validation once using the config from a previous `protect()` call. Returns a Promise of the server response `{ valid, status, expires_at, message }` or `null` if `protect()` was never called.

### `validate(options)`

Low-level: POST to `/licenses/validate` with signed body. Options: `serverUrl`, `licenseKey`, `appId`, `signingSecret`, `timeoutMs` (default 30000). Returns Promise of `{ valid, status, expires_at?, message }`. Throws `ValidationFailedError` on network/HTTP errors.

### `validateWithRetry(options)`

Like `validate()` but retries with backoff. Options include `retryCount` (default 3), `retryBackoffMs` (default 5 min).

### `shutdownScheduler()`

Stop the monthly validation timer (e.g. on process exit).

## Environment (optional)

You can configure via env and then call `validateNow()` without calling `protect()` first (e.g. in a script):

- `SWAPS_SERVER_URL` — server base URL  
- `SWAPS_LICENSE_KEY` — license key  
- `SWAPS_SIGNING_SECRET` — signing secret  
- `SWAPS_APP_ID` — default `default`  
- `SWAPS_GRACE_PERIOD_HOURS` — default 48  

(Loading from env in `validateNow()` is not implemented in this version; pass options to `protect()` or `validate()`.)

## Exceptions

- `ValidationFailedError` — network or server error during validation  
- `LicenseInvalidError` — license invalid/expired (e.g. from `requireValid()`)  
- `LicenseExpiredError`, `LicenseError` — base types  

## Integration guide

See the main repo: [docs/integration-guide.md](../docs/integration-guide.md) (concepts apply; use this package’s API as above).
