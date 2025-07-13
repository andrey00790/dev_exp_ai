/**
 * Context7 Central Provider - Unified Global State Management
 * 
 * Центральный провайдер состояния для всего приложения AI Assistant MVP.
 * Объединяет auth, roles, LLM-сессии, feature-flags и другие состояния
 * в единый Context7 паттерн для максимальной производительности.
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, useMemo } from 'react';
import { User, UserRole, UserPreferences } from '../domain/auth/entities';

// ============================================================================
// Core State Types
// ============================================================================

interface LLMSession {
  id: string;
  modelName: string;
  provider: 'openai' | 'anthropic' | 'ollama' | 'mock';
  isActive: boolean;
  startedAt: Date;
  lastActivity: Date;
  tokensUsed: number;
  cost: number;
  messages: Array<{
    id: string;
    role: 'user' | 'assistant' | 'system';
    content: string;
    timestamp: Date;
  }>;
}

interface FeatureFlags {
  // Core features
  aiAnalysis: boolean;
  realTimeUpdates: boolean;
  advancedSearch: boolean;
  vectorSearch: boolean;
  
  // UI Features
  darkMode: boolean;
  compactMode: boolean;
  debugMode: boolean;
  
  // Integrations
  vkTeams: boolean;
  githubIntegration: boolean;
  confluenceIntegration: boolean;
  
  // Experimental
  experimentalFeatures: boolean;
  betaFeatures: boolean;
  
  // Performance
  performanceMonitoring: boolean;
  memoryOptimization: boolean;
  
  // Security
  enhancedSecurity: boolean;
  auditLogging: boolean;
}

interface SystemMetrics {
  apiLatency: number;
  memoryUsage: number;
  cpuUsage: number;
  connectionStatus: 'connected' | 'disconnected' | 'reconnecting';
  uptime: number;
  lastSync: Date | null;
}

interface NotificationItem {
  id: string;
  type: 'info' | 'success' | 'warning' | 'error';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  persistent: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

// ============================================================================
// Central Context7 State
// ============================================================================

interface Context7State {
  // Authentication & Authorization
  user: User | null;
  isAuthenticated: boolean;
  userRoles: UserRole[];
  permissions: string[];
  sessionToken: string | null;
  sessionExpiry: Date | null;
  
  // LLM Session Management
  currentLLMSession: LLMSession | null;
  llmSessions: LLMSession[];
  availableModels: Array<{
    id: string;
    name: string;
    provider: string;
    isActive: boolean;
    cost: number;
  }>;
  
  // Feature Flags
  features: FeatureFlags;
  
  // System State
  isLoading: boolean;
  error: string | null;
  notifications: NotificationItem[];
  metrics: SystemMetrics;
  
  // UI State
  sidebarOpen: boolean;
  currentTheme: 'light' | 'dark' | 'system';
  currentLanguage: 'en' | 'ru';
  
  // Performance
  performanceMetrics: {
    loadTime: number;
    renderTime: number;
    bundleSize: number;
  };
}

// ============================================================================
// Actions
// ============================================================================

type Context7Action = 
  // Authentication
  | { type: 'AUTH_LOGIN_SUCCESS'; payload: { user: User; token: string; roles: UserRole[] } }
  | { type: 'AUTH_LOGOUT' }
  | { type: 'AUTH_REFRESH_TOKEN'; payload: { token: string; expiry: Date } }
  | { type: 'AUTH_UPDATE_USER'; payload: Partial<User> }
  | { type: 'AUTH_UPDATE_ROLES'; payload: UserRole[] }
  | { type: 'AUTH_UPDATE_PERMISSIONS'; payload: string[] }
  
  // LLM Sessions
  | { type: 'LLM_START_SESSION'; payload: { modelName: string; provider: string } }
  | { type: 'LLM_END_SESSION'; payload: { sessionId: string } }
  | { type: 'LLM_UPDATE_SESSION'; payload: { sessionId: string; updates: Partial<LLMSession> } }
  | { type: 'LLM_ADD_MESSAGE'; payload: { sessionId: string; message: LLMSession['messages'][0] } }
  | { type: 'LLM_LOAD_MODELS'; payload: Context7State['availableModels'] }
  
  // Feature Flags
  | { type: 'FEATURES_UPDATE'; payload: Partial<FeatureFlags> }
  | { type: 'FEATURES_TOGGLE'; payload: { key: keyof FeatureFlags; value: boolean } }
  | { type: 'FEATURES_RESET' }
  
  // System
  | { type: 'SYSTEM_SET_LOADING'; payload: boolean }
  | { type: 'SYSTEM_SET_ERROR'; payload: string | null }
  | { type: 'SYSTEM_UPDATE_METRICS'; payload: Partial<SystemMetrics> }
  | { type: 'SYSTEM_SET_CONNECTION_STATUS'; payload: SystemMetrics['connectionStatus'] }
  
  // Notifications
  | { type: 'NOTIFICATION_ADD'; payload: Omit<NotificationItem, 'id' | 'timestamp'> }
  | { type: 'NOTIFICATION_REMOVE'; payload: string }
  | { type: 'NOTIFICATION_MARK_READ'; payload: string }
  | { type: 'NOTIFICATION_CLEAR_ALL' }
  
  // UI
  | { type: 'UI_TOGGLE_SIDEBAR' }
  | { type: 'UI_SET_THEME'; payload: Context7State['currentTheme'] }
  | { type: 'UI_SET_LANGUAGE'; payload: Context7State['currentLanguage'] }
  
  // Performance
  | { type: 'PERFORMANCE_UPDATE'; payload: Partial<Context7State['performanceMetrics']> }
  
  // Global Reset
  | { type: 'GLOBAL_RESET' };

// ============================================================================
// Initial State
// ============================================================================

const initialFeatureFlags: FeatureFlags = {
  // Core features
  aiAnalysis: true,
  realTimeUpdates: true,
  advancedSearch: true,
  vectorSearch: true,
  
  // UI Features
  darkMode: localStorage.getItem('theme') === 'dark',
  compactMode: false,
  debugMode: process.env.NODE_ENV === 'development',
  
  // Integrations
  vkTeams: false,
  githubIntegration: false,
  confluenceIntegration: false,
  
  // Experimental
  experimentalFeatures: false,
  betaFeatures: false,
  
  // Performance
  performanceMonitoring: process.env.NODE_ENV === 'development',
  memoryOptimization: true,
  
  // Security
  enhancedSecurity: true,
  auditLogging: true,
};

const initialState: Context7State = {
  // Authentication & Authorization
  user: null,
  isAuthenticated: false,
  userRoles: [],
  permissions: [],
  sessionToken: null,
  sessionExpiry: null,
  
  // LLM Session Management
  currentLLMSession: null,
  llmSessions: [],
  availableModels: [],
  
  // Feature Flags
  features: initialFeatureFlags,
  
  // System State
  isLoading: false,
  error: null,
  notifications: [],
  metrics: {
    apiLatency: 0,
    memoryUsage: 0,
    cpuUsage: 0,
    connectionStatus: 'connected',
    uptime: 0,
    lastSync: null,
  },
  
  // UI State
  sidebarOpen: true,
  currentTheme: (localStorage.getItem('theme') as Context7State['currentTheme']) || 'system',
  currentLanguage: (localStorage.getItem('language') as Context7State['currentLanguage']) || 'en',
  
  // Performance
  performanceMetrics: {
    loadTime: 0,
    renderTime: 0,
    bundleSize: 0,
  },
};

// ============================================================================
// Reducer
// ============================================================================

const context7Reducer = (state: Context7State, action: Context7Action): Context7State => {
  switch (action.type) {
    // Authentication
    case 'AUTH_LOGIN_SUCCESS':
      return {
        ...state,
        user: action.payload.user,
        isAuthenticated: true,
        userRoles: action.payload.roles,
        permissions: action.payload.roles.flatMap(role => role.permissions),
        sessionToken: action.payload.token,
        sessionExpiry: new Date(Date.now() + 24 * 60 * 60 * 1000), // 24 hours
        error: null,
      };
      
    case 'AUTH_LOGOUT':
      localStorage.removeItem('auth_token');
      localStorage.removeItem('user_data');
      return {
        ...state,
        user: null,
        isAuthenticated: false,
        userRoles: [],
        permissions: [],
        sessionToken: null,
        sessionExpiry: null,
        currentLLMSession: null,
        llmSessions: [],
      };
      
    case 'AUTH_REFRESH_TOKEN':
      return {
        ...state,
        sessionToken: action.payload.token,
        sessionExpiry: action.payload.expiry,
      };
      
    case 'AUTH_UPDATE_USER':
      return {
        ...state,
        user: state.user ? { ...state.user, ...action.payload } : null,
      };
      
    case 'AUTH_UPDATE_ROLES':
      return {
        ...state,
        userRoles: action.payload,
        permissions: action.payload.flatMap(role => role.permissions),
      };
      
    case 'AUTH_UPDATE_PERMISSIONS':
      return {
        ...state,
        permissions: action.payload,
      };
      
    // LLM Sessions
    case 'LLM_START_SESSION':
      const newSession: LLMSession = {
        id: `session_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        modelName: action.payload.modelName,
        provider: action.payload.provider as LLMSession['provider'],
        isActive: true,
        startedAt: new Date(),
        lastActivity: new Date(),
        tokensUsed: 0,
        cost: 0,
        messages: [],
      };
      
      return {
        ...state,
        currentLLMSession: newSession,
        llmSessions: [newSession, ...state.llmSessions],
      };
      
    case 'LLM_END_SESSION':
      const endedSessions = state.llmSessions.map(session => 
        session.id === action.payload.sessionId
          ? { ...session, isActive: false }
          : session
      );
      
      return {
        ...state,
        llmSessions: endedSessions,
        currentLLMSession: state.currentLLMSession?.id === action.payload.sessionId 
          ? null 
          : state.currentLLMSession,
      };
      
    case 'LLM_UPDATE_SESSION':
      const updatedSessions = state.llmSessions.map(session =>
        session.id === action.payload.sessionId
          ? { ...session, ...action.payload.updates, lastActivity: new Date() }
          : session
      );
      
      return {
        ...state,
        llmSessions: updatedSessions,
        currentLLMSession: state.currentLLMSession?.id === action.payload.sessionId
          ? { ...state.currentLLMSession, ...action.payload.updates, lastActivity: new Date() }
          : state.currentLLMSession,
      };
      
    case 'LLM_ADD_MESSAGE':
      const sessionsWithMessage = state.llmSessions.map(session =>
        session.id === action.payload.sessionId
          ? { 
              ...session, 
              messages: [...session.messages, action.payload.message],
              lastActivity: new Date(),
              tokensUsed: session.tokensUsed + (action.payload.message.content.length / 4) // rough estimation
            }
          : session
      );
      
      return {
        ...state,
        llmSessions: sessionsWithMessage,
        currentLLMSession: state.currentLLMSession?.id === action.payload.sessionId
          ? { 
              ...state.currentLLMSession, 
              messages: [...state.currentLLMSession.messages, action.payload.message],
              lastActivity: new Date(),
              tokensUsed: state.currentLLMSession.tokensUsed + (action.payload.message.content.length / 4)
            }
          : state.currentLLMSession,
      };
      
    case 'LLM_LOAD_MODELS':
      return {
        ...state,
        availableModels: action.payload,
      };
      
    // Feature Flags
    case 'FEATURES_UPDATE':
      const updatedFeatures = { ...state.features, ...action.payload };
      
      // Sync theme to localStorage
      if (action.payload.darkMode !== undefined) {
        localStorage.setItem('theme', action.payload.darkMode ? 'dark' : 'light');
      }
      
      return {
        ...state,
        features: updatedFeatures,
      };
      
    case 'FEATURES_TOGGLE':
      const toggledFeatures = {
        ...state.features,
        [action.payload.key]: action.payload.value,
      };
      
      // Sync specific features to localStorage
      if (action.payload.key === 'darkMode') {
        localStorage.setItem('theme', action.payload.value ? 'dark' : 'light');
      }
      
      return {
        ...state,
        features: toggledFeatures,
      };
      
    case 'FEATURES_RESET':
      return {
        ...state,
        features: initialFeatureFlags,
      };
      
    // System
    case 'SYSTEM_SET_LOADING':
      return {
        ...state,
        isLoading: action.payload,
      };
      
    case 'SYSTEM_SET_ERROR':
      return {
        ...state,
        error: action.payload,
      };
      
    case 'SYSTEM_UPDATE_METRICS':
      return {
        ...state,
        metrics: { ...state.metrics, ...action.payload },
      };
      
    case 'SYSTEM_SET_CONNECTION_STATUS':
      return {
        ...state,
        metrics: { ...state.metrics, connectionStatus: action.payload },
      };
      
    // Notifications
    case 'NOTIFICATION_ADD':
      const newNotification: NotificationItem = {
        ...action.payload,
        id: `notification_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`,
        timestamp: new Date(),
        read: false,
      };
      
      return {
        ...state,
        notifications: [newNotification, ...state.notifications],
      };
      
    case 'NOTIFICATION_REMOVE':
      return {
        ...state,
        notifications: state.notifications.filter(n => n.id !== action.payload),
      };
      
    case 'NOTIFICATION_MARK_READ':
      return {
        ...state,
        notifications: state.notifications.map(n => 
          n.id === action.payload ? { ...n, read: true } : n
        ),
      };
      
    case 'NOTIFICATION_CLEAR_ALL':
      return {
        ...state,
        notifications: [],
      };
      
    // UI
    case 'UI_TOGGLE_SIDEBAR':
      return {
        ...state,
        sidebarOpen: !state.sidebarOpen,
      };
      
    case 'UI_SET_THEME':
      localStorage.setItem('theme', action.payload);
      return {
        ...state,
        currentTheme: action.payload,
        features: { ...state.features, darkMode: action.payload === 'dark' },
      };
      
    case 'UI_SET_LANGUAGE':
      localStorage.setItem('language', action.payload);
      return {
        ...state,
        currentLanguage: action.payload,
      };
      
    // Performance
    case 'PERFORMANCE_UPDATE':
      return {
        ...state,
        performanceMetrics: { ...state.performanceMetrics, ...action.payload },
      };
      
    // Global Reset
    case 'GLOBAL_RESET':
      return {
        ...initialState,
        currentTheme: state.currentTheme,
        currentLanguage: state.currentLanguage,
        features: { ...initialFeatureFlags, darkMode: state.features.darkMode },
      };
      
    default:
      return state;
  }
};

// ============================================================================
// Context
// ============================================================================

interface Context7ContextType {
  state: Context7State;
  actions: {
    // Authentication
    loginSuccess: (user: User, token: string, roles: UserRole[]) => void;
    logout: () => void;
    refreshToken: (token: string, expiry: Date) => void;
    updateUser: (updates: Partial<User>) => void;
    updateRoles: (roles: UserRole[]) => void;
    updatePermissions: (permissions: string[]) => void;
    
    // LLM Sessions
    startLLMSession: (modelName: string, provider: string) => void;
    endLLMSession: (sessionId: string) => void;
    updateLLMSession: (sessionId: string, updates: Partial<LLMSession>) => void;
    addLLMMessage: (sessionId: string, message: LLMSession['messages'][0]) => void;
    loadModels: (models: Context7State['availableModels']) => void;
    
    // Feature Flags
    updateFeatures: (features: Partial<FeatureFlags>) => void;
    toggleFeature: (key: keyof FeatureFlags, value: boolean) => void;
    resetFeatures: () => void;
    
    // System
    setLoading: (loading: boolean) => void;
    setError: (error: string | null) => void;
    updateMetrics: (metrics: Partial<SystemMetrics>) => void;
    setConnectionStatus: (status: SystemMetrics['connectionStatus']) => void;
    
    // Notifications
    addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp'>) => void;
    removeNotification: (id: string) => void;
    markNotificationRead: (id: string) => void;
    clearAllNotifications: () => void;
    
    // UI
    toggleSidebar: () => void;
    setTheme: (theme: Context7State['currentTheme']) => void;
    setLanguage: (language: Context7State['currentLanguage']) => void;
    
    // Performance
    updatePerformance: (metrics: Partial<Context7State['performanceMetrics']>) => void;
    
    // Global
    globalReset: () => void;
  };
  
  // Helper functions
  hasPermission: (permission: string) => boolean;
  hasRole: (roleName: string) => boolean;
  isFeatureEnabled: (feature: keyof FeatureFlags) => boolean;
  getCurrentLLMSession: () => LLMSession | null;
  getUnreadNotifications: () => NotificationItem[];
}

const Context7Context = createContext<Context7ContextType | undefined>(undefined);

// ============================================================================
// Provider Component
// ============================================================================

interface Context7ProviderProps {
  children: React.ReactNode;
  apiUrl?: string;
}

export const Context7Provider: React.FC<Context7ProviderProps> = ({ 
  children, 
  apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000' 
}) => {
  const [state, dispatch] = useReducer(context7Reducer, initialState);

  // ============================================================================
  // Action Creators
  // ============================================================================

  const actions = useMemo(() => ({
    // Authentication
    loginSuccess: (user: User, token: string, roles: UserRole[]) => {
      localStorage.setItem('auth_token', token);
      localStorage.setItem('user_data', JSON.stringify(user));
      dispatch({ type: 'AUTH_LOGIN_SUCCESS', payload: { user, token, roles } });
    },
    
    logout: () => {
      dispatch({ type: 'AUTH_LOGOUT' });
    },
    
    refreshToken: (token: string, expiry: Date) => {
      localStorage.setItem('auth_token', token);
      dispatch({ type: 'AUTH_REFRESH_TOKEN', payload: { token, expiry } });
    },
    
    updateUser: (updates: Partial<User>) => {
      dispatch({ type: 'AUTH_UPDATE_USER', payload: updates });
    },
    
    updateRoles: (roles: UserRole[]) => {
      dispatch({ type: 'AUTH_UPDATE_ROLES', payload: roles });
    },
    
    updatePermissions: (permissions: string[]) => {
      dispatch({ type: 'AUTH_UPDATE_PERMISSIONS', payload: permissions });
    },
    
    // LLM Sessions
    startLLMSession: (modelName: string, provider: string) => {
      dispatch({ type: 'LLM_START_SESSION', payload: { modelName, provider } });
    },
    
    endLLMSession: (sessionId: string) => {
      dispatch({ type: 'LLM_END_SESSION', payload: { sessionId } });
    },
    
    updateLLMSession: (sessionId: string, updates: Partial<LLMSession>) => {
      dispatch({ type: 'LLM_UPDATE_SESSION', payload: { sessionId, updates } });
    },
    
    addLLMMessage: (sessionId: string, message: LLMSession['messages'][0]) => {
      dispatch({ type: 'LLM_ADD_MESSAGE', payload: { sessionId, message } });
    },
    
    loadModels: (models: Context7State['availableModels']) => {
      dispatch({ type: 'LLM_LOAD_MODELS', payload: models });
    },
    
    // Feature Flags
    updateFeatures: (features: Partial<FeatureFlags>) => {
      dispatch({ type: 'FEATURES_UPDATE', payload: features });
    },
    
    toggleFeature: (key: keyof FeatureFlags, value: boolean) => {
      dispatch({ type: 'FEATURES_TOGGLE', payload: { key, value } });
    },
    
    resetFeatures: () => {
      dispatch({ type: 'FEATURES_RESET' });
    },
    
    // System
    setLoading: (loading: boolean) => {
      dispatch({ type: 'SYSTEM_SET_LOADING', payload: loading });
    },
    
    setError: (error: string | null) => {
      dispatch({ type: 'SYSTEM_SET_ERROR', payload: error });
    },
    
    updateMetrics: (metrics: Partial<SystemMetrics>) => {
      dispatch({ type: 'SYSTEM_UPDATE_METRICS', payload: metrics });
    },
    
    setConnectionStatus: (status: SystemMetrics['connectionStatus']) => {
      dispatch({ type: 'SYSTEM_SET_CONNECTION_STATUS', payload: status });
    },
    
    // Notifications
    addNotification: (notification: Omit<NotificationItem, 'id' | 'timestamp'>) => {
      dispatch({ type: 'NOTIFICATION_ADD', payload: notification });
    },
    
    removeNotification: (id: string) => {
      dispatch({ type: 'NOTIFICATION_REMOVE', payload: id });
    },
    
    markNotificationRead: (id: string) => {
      dispatch({ type: 'NOTIFICATION_MARK_READ', payload: id });
    },
    
    clearAllNotifications: () => {
      dispatch({ type: 'NOTIFICATION_CLEAR_ALL' });
    },
    
    // UI
    toggleSidebar: () => {
      dispatch({ type: 'UI_TOGGLE_SIDEBAR' });
    },
    
    setTheme: (theme: Context7State['currentTheme']) => {
      dispatch({ type: 'UI_SET_THEME', payload: theme });
    },
    
    setLanguage: (language: Context7State['currentLanguage']) => {
      dispatch({ type: 'UI_SET_LANGUAGE', payload: language });
    },
    
    // Performance
    updatePerformance: (metrics: Partial<Context7State['performanceMetrics']>) => {
      dispatch({ type: 'PERFORMANCE_UPDATE', payload: metrics });
    },
    
    // Global
    globalReset: () => {
      dispatch({ type: 'GLOBAL_RESET' });
    },
  }), []);

  // ============================================================================
  // Helper Functions
  // ============================================================================

  const hasPermission = useCallback((permission: string): boolean => {
    return state.permissions.includes(permission);
  }, [state.permissions]);

  const hasRole = useCallback((roleName: string): boolean => {
    return state.userRoles.some(role => role.name === roleName);
  }, [state.userRoles]);

  const isFeatureEnabled = useCallback((feature: keyof FeatureFlags): boolean => {
    return state.features[feature];
  }, [state.features]);

  const getCurrentLLMSession = useCallback((): LLMSession | null => {
    return state.currentLLMSession;
  }, [state.currentLLMSession]);

  const getUnreadNotifications = useCallback((): NotificationItem[] => {
    return state.notifications.filter(n => !n.read);
  }, [state.notifications]);

  // ============================================================================
  // Effects
  // ============================================================================

  // Initialize from localStorage
  useEffect(() => {
    const authToken = localStorage.getItem('auth_token');
    const userData = localStorage.getItem('user_data');
    
    if (authToken && userData) {
      try {
        const user = JSON.parse(userData);
        dispatch({ 
          type: 'AUTH_LOGIN_SUCCESS', 
          payload: { user, token: authToken, roles: user.roles || [] }
        });
      } catch (error) {
        console.error('Failed to parse user data from localStorage:', error);
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_data');
      }
    }
  }, []);

  // Monitor system metrics
  useEffect(() => {
    const interval = setInterval(() => {
      // Performance metrics
      if ('memory' in performance) {
        const memoryInfo = (performance as any).memory;
        const memoryUsage = memoryInfo.usedJSHeapSize / (1024 * 1024); // MB
        
        actions.updateMetrics({ 
          memoryUsage,
          uptime: Date.now() - (window as any).startTime || 0,
          lastSync: new Date()
        });
      }
    }, 30000); // Every 30 seconds

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

  const contextValue: Context7ContextType = useMemo(() => ({
    state,
    actions,
    hasPermission,
    hasRole,
    isFeatureEnabled,
    getCurrentLLMSession,
    getUnreadNotifications,
  }), [
    state,
    actions,
    hasPermission,
    hasRole,
    isFeatureEnabled,
    getCurrentLLMSession,
    getUnreadNotifications,
  ]);

  return (
    <Context7Context.Provider value={contextValue}>
      {children}
    </Context7Context.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

export const useContext7 = (): Context7ContextType => {
  const context = useContext(Context7Context);
  if (!context) {
    throw new Error('useContext7 must be used within a Context7Provider');
  }
  return context;
};

// ============================================================================
// Specialized Hooks
// ============================================================================

// Authentication hooks
export const useAuth = () => {
  const { state, actions, hasPermission, hasRole } = useContext7();
  return {
    user: state.user,
    isAuthenticated: state.isAuthenticated,
    roles: state.userRoles,
    permissions: state.permissions,
    sessionToken: state.sessionToken,
    loginSuccess: actions.loginSuccess,
    logout: actions.logout,
    updateUser: actions.updateUser,
    hasPermission,
    hasRole,
  };
};

// LLM Session hooks
export const useLLMSession = () => {
  const { state, actions, getCurrentLLMSession } = useContext7();
  return {
    currentSession: state.currentLLMSession,
    sessions: state.llmSessions,
    availableModels: state.availableModels,
    startSession: actions.startLLMSession,
    endSession: actions.endLLMSession,
    updateSession: actions.updateLLMSession,
    addMessage: actions.addLLMMessage,
    loadModels: actions.loadModels,
    getCurrentSession: getCurrentLLMSession,
  };
};

// Feature flags hooks
export const useFeatureFlags = () => {
  const { state, actions, isFeatureEnabled } = useContext7();
  return {
    features: state.features,
    updateFeatures: actions.updateFeatures,
    toggleFeature: actions.toggleFeature,
    resetFeatures: actions.resetFeatures,
    isEnabled: isFeatureEnabled,
  };
};

// Notifications hooks
export const useNotifications = () => {
  const { state, actions, getUnreadNotifications } = useContext7();
  return {
    notifications: state.notifications,
    addNotification: actions.addNotification,
    removeNotification: actions.removeNotification,
    markRead: actions.markNotificationRead,
    clearAll: actions.clearAllNotifications,
    unreadCount: getUnreadNotifications().length,
    getUnread: getUnreadNotifications,
  };
};

// UI hooks
export const useUI = () => {
  const { state, actions } = useContext7();
  return {
    sidebarOpen: state.sidebarOpen,
    theme: state.currentTheme,
    language: state.currentLanguage,
    toggleSidebar: actions.toggleSidebar,
    setTheme: actions.setTheme,
    setLanguage: actions.setLanguage,
  };
};

// System hooks
export const useSystem = () => {
  const { state, actions } = useContext7();
  return {
    isLoading: state.isLoading,
    error: state.error,
    metrics: state.metrics,
    setLoading: actions.setLoading,
    setError: actions.setError,
    updateMetrics: actions.updateMetrics,
    setConnectionStatus: actions.setConnectionStatus,
  };
};

export default Context7Provider; 