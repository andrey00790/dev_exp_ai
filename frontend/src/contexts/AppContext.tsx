/**
 * Context7 Global State Management
 * 
 * Enhanced AppContext with hexagonal architecture integration.
 * Provides centralized state management for the entire application.
 */

import React, { createContext, useContext, useReducer, ReactNode, useCallback, useEffect } from 'react';
import { User, UserPreferences } from '../domain/auth/entities';
import { localStorageAdapter } from '../adapters/auth/LocalStorageAdapter';

// ============================================================================
// Enhanced Types & Interfaces
// ============================================================================

interface GlobalSettings {
  apiUrl: string;
  version: string;
  environment: 'development' | 'staging' | 'production';
  features: {
    darkMode: boolean;
    aiAnalysis: boolean;
    realTimeUpdates: boolean;
    advancedSearch: boolean;
  };
}

interface AppState {
  // Authentication (integrates with AuthContext)
  user: User | null;
  isAuthenticated: boolean;
  
  // UI State
  isLoading: boolean;
  notifications: Notification[];
  
  // Global Settings
  settings: GlobalSettings;
  
  // Error handling
  error: string | null;
  
  // Performance monitoring
  performanceMetrics: {
    loadTime: number;
    apiLatency: number;
    memoryUsage: number;
  };
  
  // Real-time connection status
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
}

interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  autoClose?: boolean;
  duration?: number;
  actions?: NotificationAction[];
}

interface NotificationAction {
  label: string;
  action: () => void;
  style?: 'primary' | 'secondary' | 'danger';
}

// ============================================================================
// Action Types
// ============================================================================

type AppAction = 
  | { type: 'SET_USER'; payload: User | null }
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'ADD_NOTIFICATION'; payload: Omit<Notification, 'id' | 'timestamp'> }
  | { type: 'REMOVE_NOTIFICATION'; payload: string }
  | { type: 'CLEAR_ALL_NOTIFICATIONS' }
  | { type: 'UPDATE_PREFERENCES'; payload: Partial<UserPreferences> }
  | { type: 'UPDATE_SETTINGS'; payload: Partial<GlobalSettings> }
  | { type: 'UPDATE_PERFORMANCE_METRICS'; payload: Partial<AppState['performanceMetrics']> }
  | { type: 'SET_CONNECTION_STATUS'; payload: AppState['connectionStatus'] }
  | { type: 'RESET_STATE' };

// ============================================================================
// Initial State
// ============================================================================

const initialSettings: GlobalSettings = {
  apiUrl: process.env.REACT_APP_API_URL || 'http://localhost:8000',
  version: process.env.REACT_APP_VERSION || '1.0.0',
  environment: (process.env.NODE_ENV as any) || 'development',
  features: {
    darkMode: localStorageAdapter.getTheme() === 'dark',
    aiAnalysis: true,
    realTimeUpdates: true,
    advancedSearch: true,
  },
};

const initialState: AppState = {
  user: null,
  isAuthenticated: false,
  isLoading: false,
  notifications: [],
  settings: initialSettings,
  error: null,
  performanceMetrics: {
    loadTime: 0,
    apiLatency: 0,
    memoryUsage: 0,
  },
  connectionStatus: 'connected',
};

// ============================================================================
// Reducer
// ============================================================================

const appReducer = (state: AppState, action: AppAction): AppState => {
  switch (action.type) {
    case 'SET_USER':
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
      };
    
    case 'SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
    
    case 'SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
    
    case 'ADD_NOTIFICATION':
      const newNotification: Notification = {
        ...action.payload,
        id: `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
      };
      
      return {
        ...state,
        notifications: [...state.notifications, newNotification],
      };
    
    case 'REMOVE_NOTIFICATION':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
    
    case 'CLEAR_ALL_NOTIFICATIONS':
      return {
        ...state,
        notifications: [],
      };
    
    case 'UPDATE_PREFERENCES':
      if (!state.user) return state;
      
      const updatedPreferences = {
        ...state.user.preferences,
        ...action.payload,
      };
      
      // Sync to localStorage
      localStorageAdapter.setPreferences(updatedPreferences);
      
      return {
        ...state,
        user: {
          ...state.user,
          preferences: updatedPreferences,
        },
      };
    
    case 'UPDATE_SETTINGS':
      const updatedSettings = {
        ...state.settings,
        ...action.payload,
      };
      
      // Sync specific settings to localStorage
      if (action.payload.features?.darkMode !== undefined) {
        localStorageAdapter.setTheme(action.payload.features.darkMode ? 'dark' : 'light');
      }
      
      return {
        ...state,
        settings: updatedSettings,
      };
    
    case 'UPDATE_PERFORMANCE_METRICS':
      return {
        ...state,
        performanceMetrics: {
          ...state.performanceMetrics,
          ...action.payload,
        },
      };
    
    case 'SET_CONNECTION_STATUS':
      return {
        ...state,
        connectionStatus: action.payload,
      };
    
    case 'RESET_STATE':
      return {
        ...initialState,
        settings: state.settings, // Preserve settings
      };
    
    default:
      return state;
  }
};

// ============================================================================
// Context
// ============================================================================

interface AppContextType {
  state: AppState;
  actions: {
    setUser: (user: User | null) => void;
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    addNotification: (notification: Omit<Notification, 'id' | 'timestamp'>) => void;
    removeNotification: (id: string) => void;
    clearAllNotifications: () => void;
    updatePreferences: (preferences: Partial<UserPreferences>) => void;
    updateSettings: (settings: Partial<GlobalSettings>) => void;
    updatePerformanceMetrics: (metrics: Partial<AppState['performanceMetrics']>) => void;
    setConnectionStatus: (status: AppState['connectionStatus']) => void;
    resetState: () => void;
  };
}

const AppContext = createContext<AppContextType | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

interface AppProviderProps {
  children: ReactNode;
}

export const AppProvider: React.FC<AppProviderProps> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  // ============================================================================
  // Action Creators
  // ============================================================================

  const actions = {
    setUser: useCallback((user: User | null) => {
      dispatch({ type: 'SET_USER', payload: user });
    }, []),

    setLoading: useCallback((loading: boolean) => {
      dispatch({ type: 'SET_LOADING', payload: loading });
    }, []),

    setError: useCallback((error: string | null) => {
      dispatch({ type: 'SET_ERROR', payload: error });
    }, []),

    addNotification: useCallback((notification: Omit<Notification, 'id' | 'timestamp'>) => {
      dispatch({ type: 'ADD_NOTIFICATION', payload: notification });
      
      // Auto-remove notification if autoClose is not false
      if (notification.autoClose !== false) {
        const duration = notification.duration || 5000;
        setTimeout(() => {
          dispatch({ type: 'REMOVE_NOTIFICATION', payload: notification.id || '' });
        }, duration);
      }
    }, []),

    removeNotification: useCallback((id: string) => {
      dispatch({ type: 'REMOVE_NOTIFICATION', payload: id });
    }, []),

    clearAllNotifications: useCallback(() => {
      dispatch({ type: 'CLEAR_ALL_NOTIFICATIONS' });
    }, []),

    updatePreferences: useCallback((preferences: Partial<UserPreferences>) => {
      dispatch({ type: 'UPDATE_PREFERENCES', payload: preferences });
    }, []),

    updateSettings: useCallback((settings: Partial<GlobalSettings>) => {
      dispatch({ type: 'UPDATE_SETTINGS', payload: settings });
    }, []),

    updatePerformanceMetrics: useCallback((metrics: Partial<AppState['performanceMetrics']>) => {
      dispatch({ type: 'UPDATE_PERFORMANCE_METRICS', payload: metrics });
    }, []),

    setConnectionStatus: useCallback((status: AppState['connectionStatus']) => {
      dispatch({ type: 'SET_CONNECTION_STATUS', payload: status });
    }, []),

    resetState: useCallback(() => {
      dispatch({ type: 'RESET_STATE' });
    }, []),
  };

  // ============================================================================
  // Effects
  // ============================================================================

  // Performance monitoring
  useEffect(() => {
    const startTime = performance.now();
    
    const handleLoad = () => {
      const loadTime = performance.now() - startTime;
      actions.updatePerformanceMetrics({ loadTime });
    };

    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
      return () => window.removeEventListener('load', handleLoad);
    }
  }, [actions]);

  // Memory usage monitoring
  useEffect(() => {
    const monitorMemory = () => {
      if ('memory' in performance) {
        const memoryInfo = (performance as any).memory;
        const memoryUsage = memoryInfo.usedJSHeapSize / memoryInfo.totalJSHeapSize;
        actions.updatePerformanceMetrics({ memoryUsage });
      }
    };

    const interval = setInterval(monitorMemory, 30000); // Every 30 seconds
    return () => clearInterval(interval);
  }, [actions]);

  // Connection status monitoring
  useEffect(() => {
    const handleOnline = () => actions.setConnectionStatus('connected');
    const handleOffline = () => actions.setConnectionStatus('disconnected');

    window.addEventListener('online', handleOnline);
    window.addEventListener('offline', handleOffline);

    return () => {
      window.removeEventListener('online', handleOnline);
      window.removeEventListener('offline', handleOffline);
    };
  }, [actions]);

  // ============================================================================
  // Context Value
  // ============================================================================

  const contextValue: AppContextType = {
    state,
    actions,
  };

  return (
    <AppContext.Provider value={contextValue}>
      {children}
    </AppContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

export const useAppContext = (): AppContextType => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within an AppProvider');
  }
  return context;
};

// ============================================================================
// Enhanced Convenience Hooks
// ============================================================================

export const useUser = () => {
  const { state, actions } = useAppContext();
  return {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    setUser: actions.setUser,
  };
};

export const useNotifications = () => {
  const { state, actions } = useAppContext();
  return {
    notifications: state.notifications,
    addNotification: actions.addNotification,
    removeNotification: actions.removeNotification,
    clearAllNotifications: actions.clearAllNotifications,
    
    // Convenience methods
    addSuccessNotification: (title: string, message: string) => 
      actions.addNotification({ type: 'success', title, message }),
    addErrorNotification: (title: string, message: string) => 
      actions.addNotification({ type: 'error', title, message }),
    addWarningNotification: (title: string, message: string) => 
      actions.addNotification({ type: 'warning', title, message }),
    addInfoNotification: (title: string, message: string) => 
      actions.addNotification({ type: 'info', title, message }),
  };
};

export const useLoading = () => {
  const { state, actions } = useAppContext();
  return {
    isLoading: state.isLoading,
    setLoading: actions.setLoading,
  };
};

export const useError = () => {
  const { state, actions } = useAppContext();
  return {
    error: state.error,
    setError: actions.setError,
    clearError: () => actions.setError(null),
  };
};

export const useSettings = () => {
  const { state, actions } = useAppContext();
  return {
    settings: state.settings,
    updateSettings: actions.updateSettings,
    
    // Convenience methods
    toggleDarkMode: () => actions.updateSettings({
      features: { ...state.settings.features, darkMode: !state.settings.features.darkMode }
    }),
    setApiUrl: (apiUrl: string) => actions.updateSettings({ apiUrl }),
  };
};

export const usePerformance = () => {
  const { state } = useAppContext();
  return {
    metrics: state.performanceMetrics,
    connectionStatus: state.connectionStatus,
  };
};

export const usePreferences = () => {
  const { state, actions } = useAppContext();
  return {
    preferences: state.user?.preferences,
    updatePreferences: actions.updatePreferences,
  };
};

// Export types for use in other components
export type { 
  User, 
  UserPreferences, 
  AppState, 
  Notification, 
  NotificationAction,
  GlobalSettings 
}; 