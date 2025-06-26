/**
 * Testing utilities for AI Assistant Frontend
 * Provides custom render function with providers and common test helpers
 */

import React, { ReactElement } from 'react';
import { render, RenderOptions } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { AuthProvider } from '../../src/contexts/AuthContext';

// Create a custom render function that includes providers
const AllTheProviders: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
        cacheTime: 0,
        staleTime: 0,
      },
    },
  });

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <AuthProvider>
          {children}
        </AuthProvider>
      </BrowserRouter>
    </QueryClientProvider>
  );
};

const customRender = (
  ui: ReactElement,
  options?: Omit<RenderOptions, 'wrapper'>
) => render(ui, { wrapper: AllTheProviders, ...options });

export * from '@testing-library/react';
export { customRender as render };

// Mock user data for testing
export const mockUser = {
  id: 1,
  email: 'test@example.com',
  name: 'Test User',
  role: 'user',
  is_active: true,
  current_usage: 50.0,
  budget_limit: 100.0,
  created_at: '2023-01-01T00:00:00Z',
  updated_at: '2023-01-01T00:00:00Z'
};

// Mock API responses
export const mockApiResponses = {
  auth: {
    login: {
      access_token: 'mock-token',
      token_type: 'bearer',
      user: mockUser
    },
    user: mockUser
  },
  
  search: {
    results: [
      {
        id: '1',
        title: 'Test Result',
        content: 'Test content',
        score: 0.95,
        metadata: { source: 'test' }
      }
    ]
  },
  
  analytics: {
    summary: {
      total_requests: 1000,
      active_models: 4,
      active_users: 50,
      data_points_collected: 10000
    }
  },
  
  monitoring: {
    alerts_summary: {
      total: 5,
      critical: 1,
      high: 2,
      medium: 2,
      low: 0
    }
  }
};

// Helper function to mock fetch responses
export const mockFetch = (response: any, status = 200) => {
  return jest.fn().mockResolvedValue({
    ok: status >= 200 && status < 300,
    status,
    json: jest.fn().mockResolvedValue(response),
  });
};

// Helper function to mock failed fetch
export const mockFetchError = (error: string) => {
  return jest.fn().mockRejectedValue(new Error(error));
};

// Helper function to wait for async operations
export const waitForAsync = () => new Promise(resolve => setTimeout(resolve, 0));

// Common test IDs
export const testIds = {
  // Layout
  sidebar: 'sidebar',
  mainContent: 'main-content',
  navigation: 'navigation',
  
  // Auth
  loginForm: 'login-form',
  emailInput: 'email-input',
  passwordInput: 'password-input',
  loginButton: 'login-button',
  
  // Dashboard
  summaryCards: 'summary-cards',
  chartContainer: 'chart-container',
  metricsTable: 'metrics-table',
  
  // Monitoring
  alertsList: 'alerts-list',
  anomaliesList: 'anomalies-list',
  slaStatus: 'sla-status',
  
  // Analytics
  trendsChart: 'trends-chart',
  usagePatterns: 'usage-patterns',
  costInsights: 'cost-insights',
};

// Helper to create mock WebSocket
export const createMockWebSocket = () => {
  const mockWS = {
    send: jest.fn(),
    close: jest.fn(),
    addEventListener: jest.fn(),
    removeEventListener: jest.fn(),
    readyState: WebSocket.OPEN,
    CONNECTING: WebSocket.CONNECTING,
    OPEN: WebSocket.OPEN,
    CLOSING: WebSocket.CLOSING,
    CLOSED: WebSocket.CLOSED,
  };
  
  return mockWS;
}; 