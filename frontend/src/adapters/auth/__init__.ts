/**
 * Auth Adapters Module
 * 
 * Frontend adapters for authentication-related external services.
 */

export { AuthApiAdapter, authApiAdapter, ApiError } from './AuthApiAdapter';
export { LocalStorageAdapter, localStorageAdapter } from './LocalStorageAdapter';

export type {
  // Re-export types that might be useful
} from './AuthApiAdapter'; 