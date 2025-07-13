/**
 * Context7 Auth Context - Enhanced Authentication Management
 * 
 * Integrates with hexagonal architecture backend.
 * Provides comprehensive authentication state management.
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, ReactNode } from 'react';
import { User, UserPreferences } from '../domain/auth/entities';

// ============================================================================
// Enhanced Types
// ============================================================================

interface AuthSession {
  id: string;
  token: string;
  refreshToken: string;
  expiresAt: Date;
  isActive: boolean;
}

interface AuthState {
  user: User | null;
  session: AuthSession | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  lastActivity: Date | null;
  sessionExpiry: Date | null;
}

interface LoginCredentials {
  email: string;
  password: string;
}

interface RegisterData {
  email: string;
  name: string;
  password: string;
}

// ============================================================================
// Actions
// ============================================================================

type AuthAction = 
  | { type: 'LOGIN_START' }
  | { type: 'LOGIN_SUCCESS'; payload: { user: User; session: AuthSession } }
  | { type: 'LOGIN_FAILURE'; payload: string }
  | { type: 'LOGOUT' }
  | { type: 'REGISTER_START' }
  | { type: 'REGISTER_SUCCESS'; payload: { user: User; session: AuthSession } }
  | { type: 'REGISTER_FAILURE'; payload: string }
  | { type: 'TOKEN_REFRESH_SUCCESS'; payload: { session: AuthSession } }
  | { type: 'TOKEN_REFRESH_FAILURE'; payload: string }
  | { type: 'UPDATE_USER'; payload: User }
  | { type: 'UPDATE_LAST_ACTIVITY' }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' };

// ============================================================================
// Initial State
// ============================================================================

const initialState: AuthState = {
  user: null,
  session: null,
  isAuthenticated: false,
  isLoading: false,
  error: null,
  lastActivity: null,
  sessionExpiry: null,
};

// ============================================================================
// Reducer
// ============================================================================

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case 'LOGIN_START':
    case 'REGISTER_START':
      return {
        ...state,
        isLoading: true,
        error: null,
      };
    
    case 'LOGIN_SUCCESS':
    case 'REGISTER_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        session: action.payload.session,
        isAuthenticated: true,
        isLoading: false,
        error: null,
        lastActivity: new Date(),
        sessionExpiry: action.payload.session.expiresAt,
      };
    
    case 'LOGIN_FAILURE':
    case 'REGISTER_FAILURE':
      return {
        ...state,
        user: null,
        session: null,
        isAuthenticated: false,
        isLoading: false,
        error: action.payload,
        lastActivity: null,
        sessionExpiry: null,
      };
    
    case 'LOGOUT':
      return {
        ...initialState,
        lastActivity: state.lastActivity,
      };
    
    case 'TOKEN_REFRESH_SUCCESS':
      return {
        ...state,
        session: action.payload.session,
        sessionExpiry: action.payload.session.expiresAt,
        error: null,
      };
    
    case 'TOKEN_REFRESH_FAILURE':
      return {
        ...state,
        error: action.payload,
        // Don't logout immediately, let user handle it
      };
    
    case 'UPDATE_USER':
      return {
        ...state,
        user: action.payload,
        lastActivity: new Date(),
      };
    
    case 'UPDATE_LAST_ACTIVITY':
      return {
        ...state,
        lastActivity: new Date(),
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    
    case 'CLEAR_ERROR':
      return {
        ...state,
        error: null,
      };
    
    default:
      return state;
  }
};

// ============================================================================
// Context & Provider
// ============================================================================

interface AuthContextType {
  state: AuthState;
  actions: {
    login: (credentials: LoginCredentials) => Promise<boolean>;
    register: (data: RegisterData) => Promise<boolean>;
    logout: () => Promise<void>;
    refreshToken: () => Promise<boolean>;
    updateUser: (user: Partial<User>) => Promise<boolean>;
    updatePreferences: (preferences: Partial<UserPreferences>) => Promise<boolean>;
    checkPermission: (permission: string) => boolean;
    checkRole: (role: string) => boolean;
    clearError: () => void;
    updateActivity: () => void;
  };
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

interface AuthProviderProps {
  children: ReactNode;
  apiUrl?: string;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ 
  children, 
  apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000' 
}) => {
  const [state, dispatch] = useReducer(authReducer, initialState);

  // ============================================================================
  // API Helpers
  // ============================================================================

  const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
    const url = `${apiUrl}${endpoint}`;
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...options.headers,
    };

    if (state.session?.token) {
      headers.Authorization = `Bearer ${state.session.token}`;
    }

    const response = await fetch(url, {
      ...options,
      headers,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  };

  // ============================================================================
  // Actions
  // ============================================================================

  const login = useCallback(async (credentials: LoginCredentials): Promise<boolean> => {
    try {
      dispatch({ type: 'LOGIN_START' });
      
      const response = await apiRequest('/api/v1/auth/login', {
        method: 'POST',
        body: JSON.stringify(credentials),
      });

      const session: AuthSession = {
        id: response.session.id,
        token: response.session.token,
        refreshToken: response.session.refresh_token,
        expiresAt: new Date(response.session.expires_at),
        isActive: response.session.is_active,
      };

      dispatch({ 
        type: 'LOGIN_SUCCESS', 
        payload: { user: response.user, session } 
      });

      // Store session in localStorage
      localStorage.setItem('auth_session', JSON.stringify(session));
      
      return true;
    } catch (error) {
      dispatch({ 
        type: 'LOGIN_FAILURE', 
        payload: error instanceof Error ? error.message : 'Login failed' 
      });
      return false;
    }
  }, [apiUrl]);

  const register = useCallback(async (data: RegisterData): Promise<boolean> => {
    try {
      dispatch({ type: 'REGISTER_START' });
      
      const response = await apiRequest('/api/v1/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
      });

      const session: AuthSession = {
        id: response.session.id,
        token: response.session.token,
        refreshToken: response.session.refresh_token,
        expiresAt: new Date(response.session.expires_at),
        isActive: response.session.is_active,
      };

      dispatch({ 
        type: 'REGISTER_SUCCESS', 
        payload: { user: response.user, session } 
      });

      // Store session in localStorage
      localStorage.setItem('auth_session', JSON.stringify(session));
      
      return true;
    } catch (error) {
      dispatch({ 
        type: 'REGISTER_FAILURE', 
        payload: error instanceof Error ? error.message : 'Registration failed' 
      });
      return false;
    }
  }, [apiUrl]);

  const logout = useCallback(async (): Promise<void> => {
    try {
      if (state.session?.token) {
        await apiRequest('/api/v1/auth/logout', {
          method: 'POST',
        });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      dispatch({ type: 'LOGOUT' });
      localStorage.removeItem('auth_session');
    }
  }, [state.session?.token]);

  const refreshToken = useCallback(async (): Promise<boolean> => {
    try {
      if (!state.session?.refreshToken) {
        return false;
      }

      const response = await apiRequest('/api/v1/auth/refresh', {
        method: 'POST',
        body: JSON.stringify({
          refresh_token: state.session.refreshToken,
        }),
      });

      const session: AuthSession = {
        id: response.session.id,
        token: response.session.token,
        refreshToken: response.session.refresh_token,
        expiresAt: new Date(response.session.expires_at),
        isActive: response.session.is_active,
      };

      dispatch({ 
        type: 'TOKEN_REFRESH_SUCCESS', 
        payload: { session } 
      });

      // Update stored session
      localStorage.setItem('auth_session', JSON.stringify(session));
      
      return true;
    } catch (error) {
      dispatch({ 
        type: 'TOKEN_REFRESH_FAILURE', 
        payload: error instanceof Error ? error.message : 'Token refresh failed' 
      });
      return false;
    }
  }, [state.session?.refreshToken]);

  const updateUser = useCallback(async (userData: Partial<User>): Promise<boolean> => {
    try {
      const response = await apiRequest('/api/v1/auth/profile', {
        method: 'PUT',
        body: JSON.stringify(userData),
      });

      dispatch({ type: 'UPDATE_USER', payload: response.user });
      return true;
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Profile update failed' 
      });
      return false;
    }
  }, []);

  const updatePreferences = useCallback(async (preferences: Partial<UserPreferences>): Promise<boolean> => {
    try {
      const response = await apiRequest('/api/v1/auth/preferences', {
        method: 'PUT',
        body: JSON.stringify(preferences),
      });

      dispatch({ type: 'UPDATE_USER', payload: response.user });
      return true;
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Preferences update failed' 
      });
      return false;
    }
  }, []);

  const checkPermission = useCallback((permission: string): boolean => {
    return state.user?.permissions?.includes(permission) || false;
  }, [state.user]);

  const checkRole = useCallback((role: string): boolean => {
    return state.user?.roles?.some(r => r.name === role) || false;
  }, [state.user]);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  const updateActivity = useCallback(() => {
    dispatch({ type: 'UPDATE_LAST_ACTIVITY' });
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  // Initialize session from localStorage
  useEffect(() => {
    const storedSession = localStorage.getItem('auth_session');
    if (storedSession) {
      try {
        const session: AuthSession = JSON.parse(storedSession);
        if (new Date(session.expiresAt) > new Date()) {
          // Session is still valid, fetch user data
          apiRequest('/api/v1/auth/me')
            .then(response => {
              dispatch({ 
                type: 'LOGIN_SUCCESS', 
                payload: { user: response.user, session } 
              });
            })
            .catch(() => {
              localStorage.removeItem('auth_session');
            });
        } else {
          localStorage.removeItem('auth_session');
        }
      } catch {
        localStorage.removeItem('auth_session');
      }
    }
  }, []);

  // Auto-refresh token before expiry
  useEffect(() => {
    if (state.sessionExpiry && state.session?.refreshToken) {
      const timeToExpiry = state.sessionExpiry.getTime() - Date.now();
      const refreshTime = timeToExpiry - 5 * 60 * 1000; // 5 minutes before expiry

      if (refreshTime > 0) {
        const timer = setTimeout(refreshToken, refreshTime);
        return () => clearTimeout(timer);
      }
    }
  }, [state.sessionExpiry, refreshToken]);

  // ============================================================================
  // Context Value
  // ============================================================================

  const contextValue: AuthContextType = {
    state,
    actions: {
      login,
      register,
      logout,
      refreshToken,
      updateUser,
      updatePreferences,
      checkPermission,
      checkRole,
      clearError,
      updateActivity,
    },
  };

  return (
    <AuthContext.Provider value={contextValue}>
      {children}
    </AuthContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

export const useAuth = (): AuthContextType => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

// ============================================================================
// Convenience Hooks
// ============================================================================

export const useAuthUser = () => {
  const { state } = useAuth();
  return state.user;
};

export const useAuthSession = () => {
  const { state } = useAuth();
  return state.session;
};

export const useAuthStatus = () => {
  const { state } = useAuth();
  return {
    isAuthenticated: state.isAuthenticated,
    isLoading: state.isLoading,
    error: state.error,
  };
};

export const usePermissions = () => {
  const { actions } = useAuth();
  return {
    checkPermission: actions.checkPermission,
    checkRole: actions.checkRole,
  };
};

// Export types
export type { AuthState, AuthSession, LoginCredentials, RegisterData };
