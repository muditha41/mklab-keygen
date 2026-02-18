/**
 * SWAPS Client SDK — license validation for Node.js
 * @see https://github.com/your-org/mklab-keygen
 */

import { computeSignature } from './signature.js';
import { validate, validateWithRetry } from './validate.js';
import { protect, validateNow, requireValid, shutdownScheduler } from './protect.js';
import {
  LicenseError,
  LicenseExpiredError,
  LicenseInvalidError,
  ValidationFailedError,
} from './exceptions.js';

export {
  computeSignature,
  validate,
  validateWithRetry,
  protect,
  validateNow,
  requireValid,
  shutdownScheduler,
  LicenseError,
  LicenseExpiredError,
  LicenseInvalidError,
  ValidationFailedError,
};

export const version = '0.1.0';
