/**
 * TypeScript Error Fixes and Compatibility Layer
 * Context7 pattern: Centralized type fixes and compatibility shims
 */

// Fix for process.env in browser environment
declare global {
  namespace NodeJS {
    interface ProcessEnv {
      NODE_ENV: 'development' | 'production' | 'test';
      REACT_APP_API_URL: string;
      REACT_APP_VERSION: string;
      REACT_APP_SENTRY_DSN?: string;
      REACT_APP_ANALYTICS_ID?: string;
    }
  }
}

// Enhanced fetch with better typing
interface EnhancedRequestInit extends RequestInit {
  headers?: HeadersInit & {
    'Content-Type'?: string;
    'Authorization'?: string;
    'X-Request-ID'?: string;
  };
}

// Enhanced Error with additional context
export interface EnhancedError extends Error {
  code?: string;
  status?: number;
  context?: Record<string, any>;
}

// React component props with children
export interface ComponentProps {
  children?: React.ReactNode;
  className?: string;
}

// API Response wrapper
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

// Form validation result
export interface ValidationResult {
  isValid: boolean;
  errors: string[];
  warnings?: string[];
}

// File upload types
export interface FileUploadResult {
  success: boolean;
  fileId?: string;
  url?: string;
  error?: string;
}

// Utility type for making all properties optional
export type Partial<T> = {
  [P in keyof T]?: T[P];
};

// Utility type for making specific properties required
export type RequiredFields<T, K extends keyof T> = T & Required<Pick<T, K>>;

// Context7 specific patterns
export interface Context7Store<T = any> {
  state: T;
  setState: (newState: Partial<T>) => void;
  reset: () => void;
}

export interface Context7Provider<T> {
  children: React.ReactNode;
  initialState?: Partial<T>;
}

// Export empty object to make this a module
export {}; 