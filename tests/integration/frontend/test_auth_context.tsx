/**
 * Integration Tests for AuthContext
 * 
 * Tests Context7 authentication context with mock API.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { AuthProvider, useAuth } from '../../../src/contexts/AuthContext';
import { User } from '../../../src/domain/auth/entities';

// Mock API adapter
jest.mock('../../../src/adapters/auth/AuthApiAdapter', () => ({
  authApiAdapter: {
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
    refreshToken: jest.fn(),
    getCurrentUser: jest.fn(),
    updateProfile: jest.fn(),
    updatePreferences: jest.fn(),
    changePassword: jest.fn(),
  },
}));

// Mock localStorage adapter
jest.mock('../../../src/adapters/auth/LocalStorageAdapter', () => ({
  localStorageAdapter: {
    getSession: jest.fn(),
    setSession: jest.fn(),
    removeSession: jest.fn(),
    isSessionValid: jest.fn(),
  },
}));

import { authApiAdapter } from '../../../src/adapters/auth/AuthApiAdapter';
import { localStorageAdapter } from '../../../src/adapters/auth/LocalStorageAdapter';

// Test component that uses auth context
const TestComponent: React.FC = () => {
  const { state, actions } = useAuth();

  return (
    <div>
      <div data-testid="auth-status">
        {state.isAuthenticated ? 'authenticated' : 'not-authenticated'}
      </div>
      <div data-testid="loading-status">
        {state.isLoading ? 'loading' : 'not-loading'}
      </div>
      <div data-testid="error-status">
        {state.error || 'no-error'}
      </div>
      {state.user && (
        <div data-testid="user-info">
          {state.user.name} - {state.user.email}
        </div>
      )}
      
      <button
        data-testid="login-button"
        onClick={() => actions.login({ email: 'test@example.com', password: 'password123' })}
      >
        Login
      </button>
      
      <button
        data-testid="register-button"
        onClick={() => actions.register({ 
          email: 'test@example.com', 
          name: 'Test User',
          password: 'password123' 
        })}
      >
        Register
      </button>
      
      <button
        data-testid="logout-button"
        onClick={() => actions.logout()}
      >
        Logout
      </button>
      
      <button
        data-testid="clear-error-button"
        onClick={() => actions.clearError()}
      >
        Clear Error
      </button>
    </div>
  );
};

const renderWithAuthProvider = (component: React.ReactElement) => {
  return render(
    <AuthProvider>
      {component}
    </AuthProvider>
  );
};

describe('AuthContext Integration Tests', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    (localStorageAdapter.getSession as jest.Mock).mockReturnValue(null);
  });

  it('should render with initial state', () => {
    renderWithAuthProvider(<TestComponent />);

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('loading-status')).toHaveTextContent('not-loading');
    expect(screen.getByTestId('error-status')).toHaveTextContent('no-error');
    expect(screen.queryByTestId('user-info')).not.toBeInTheDocument();
  });

  it('should handle successful login', async () => {
    const mockUser: User = {
      id: 'user_123',
      email: 'test@example.com',
      name: 'Test User',
      roles: [],
      status: 'active' as any,
      createdAt: new Date(),
      profileData: {},
      preferences: {
        theme: 'light',
        language: 'en',
        notifications: true,
      },
    };

    const mockSession = {
      id: 'session_123',
      token: 'mock_token',
      refresh_token: 'mock_refresh_token',
      expires_at: new Date(Date.now() + 3600000).toISOString(), // 1 hour
      is_active: true,
    };

    (authApiAdapter.login as jest.Mock).mockResolvedValue({
      user: mockUser,
      session: mockSession,
    });

    renderWithAuthProvider(<TestComponent />);

    fireEvent.click(screen.getByTestId('login-button'));

    // Should show loading state
    expect(screen.getByTestId('loading-status')).toHaveTextContent('loading');

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('loading-status')).toHaveTextContent('not-loading');
    expect(screen.getByTestId('user-info')).toHaveTextContent('Test User - test@example.com');
    expect(localStorageAdapter.setSession).toHaveBeenCalledWith({
      id: 'session_123',
      token: 'mock_token',
      refreshToken: 'mock_refresh_token',
      expiresAt: expect.any(Date),
      isActive: true,
    });
  });

  it('should handle login failure', async () => {
    (authApiAdapter.login as jest.Mock).mockRejectedValue(
      new Error('Invalid credentials')
    );

    renderWithAuthProvider(<TestComponent />);

    fireEvent.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('error-status')).toHaveTextContent('Invalid credentials');
    });

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('loading-status')).toHaveTextContent('not-loading');
  });

  it('should handle successful registration', async () => {
    const mockUser: User = {
      id: 'user_123',
      email: 'test@example.com',
      name: 'Test User',
      roles: [],
      status: 'active' as any,
      createdAt: new Date(),
      profileData: {},
      preferences: {
        theme: 'light',
        language: 'en',
        notifications: true,
      },
    };

    const mockSession = {
      id: 'session_123',
      token: 'mock_token',
      refresh_token: 'mock_refresh_token',
      expires_at: new Date(Date.now() + 3600000).toISOString(),
      is_active: true,
    };

    (authApiAdapter.register as jest.Mock).mockResolvedValue({
      user: mockUser,
      session: mockSession,
    });

    renderWithAuthProvider(<TestComponent />);

    fireEvent.click(screen.getByTestId('register-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('user-info')).toHaveTextContent('Test User - test@example.com');
    expect(authApiAdapter.register).toHaveBeenCalledWith({
      email: 'test@example.com',
      name: 'Test User',
      password: 'password123',
    });
  });

  it('should handle logout', async () => {
    // Setup authenticated state first
    const mockUser: User = {
      id: 'user_123',
      email: 'test@example.com',
      name: 'Test User',
      roles: [],
      status: 'active' as any,
      createdAt: new Date(),
      profileData: {},
      preferences: {
        theme: 'light',
        language: 'en',
        notifications: true,
      },
    };

    const mockSession = {
      id: 'session_123',
      token: 'mock_token',
      refresh_token: 'mock_refresh_token',
      expires_at: new Date(Date.now() + 3600000).toISOString(),
      is_active: true,
    };

    (authApiAdapter.login as jest.Mock).mockResolvedValue({
      user: mockUser,
      session: mockSession,
    });

    (authApiAdapter.logout as jest.Mock).mockResolvedValue(undefined);

    renderWithAuthProvider(<TestComponent />);

    // Login first
    fireEvent.click(screen.getByTestId('login-button'));
    
    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    // Then logout
    fireEvent.click(screen.getByTestId('logout-button'));

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    });

    expect(screen.queryByTestId('user-info')).not.toBeInTheDocument();
    expect(localStorageAdapter.removeSession).toHaveBeenCalled();
  });

  it('should clear error when clearError is called', async () => {
    (authApiAdapter.login as jest.Mock).mockRejectedValue(
      new Error('Login failed')
    );

    renderWithAuthProvider(<TestComponent />);

    // Trigger an error
    fireEvent.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('error-status')).toHaveTextContent('Login failed');
    });

    // Clear the error
    fireEvent.click(screen.getByTestId('clear-error-button'));

    expect(screen.getByTestId('error-status')).toHaveTextContent('no-error');
  });

  it('should restore session from localStorage on mount', async () => {
    const mockStoredSession = {
      id: 'session_123',
      token: 'stored_token',
      refreshToken: 'stored_refresh_token',
      expiresAt: new Date(Date.now() + 3600000), // Valid future date
      isActive: true,
    };

    const mockUser: User = {
      id: 'user_123',
      email: 'test@example.com',
      name: 'Test User',
      roles: [],
      status: 'active' as any,
      createdAt: new Date(),
      profileData: {},
      preferences: {
        theme: 'light',
        language: 'en',
        notifications: true,
      },
    };

    (localStorageAdapter.getSession as jest.Mock).mockReturnValue(mockStoredSession);
    (authApiAdapter.getCurrentUser as jest.Mock).mockResolvedValue({
      user: mockUser,
    });

    renderWithAuthProvider(<TestComponent />);

    await waitFor(() => {
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
    });

    expect(screen.getByTestId('user-info')).toHaveTextContent('Test User - test@example.com');
    expect(authApiAdapter.getCurrentUser).toHaveBeenCalledWith('stored_token');
  });

  it('should not restore expired session from localStorage', () => {
    const expiredSession = {
      id: 'session_123',
      token: 'expired_token',
      refreshToken: 'expired_refresh_token',
      expiresAt: new Date(Date.now() - 3600000), // Expired 1 hour ago
      isActive: true,
    };

    (localStorageAdapter.getSession as jest.Mock).mockReturnValue(expiredSession);

    renderWithAuthProvider(<TestComponent />);

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    expect(localStorageAdapter.removeSession).toHaveBeenCalled();
  });

  it('should handle API errors gracefully', async () => {
    (authApiAdapter.login as jest.Mock).mockRejectedValue(
      new Error('Network error')
    );

    renderWithAuthProvider(<TestComponent />);

    fireEvent.click(screen.getByTestId('login-button'));

    await waitFor(() => {
      expect(screen.getByTestId('error-status')).toHaveTextContent('Network error');
    });

    expect(screen.getByTestId('auth-status')).toHaveTextContent('not-authenticated');
    expect(screen.getByTestId('loading-status')).toHaveTextContent('not-loading');
  });
});

// Test for useAuth hook error handling
describe('useAuth Hook Error Handling', () => {
  it('should throw error when used outside AuthProvider', () => {
    const TestComponent = () => {
      useAuth();
      return <div>Test</div>;
    };

    // Capture console.error to prevent test output pollution
    const originalError = console.error;
    console.error = jest.fn();

    expect(() => render(<TestComponent />)).toThrow(
      'useAuth must be used within an AuthProvider'
    );

    console.error = originalError;
  });
}); 