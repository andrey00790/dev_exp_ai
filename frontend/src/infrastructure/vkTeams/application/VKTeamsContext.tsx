/**
 * VK Teams Context7 State Management
 * 
 * Context7 pattern: Application layer context for VK Teams integration
 * Handles state management, API calls, and business logic coordination
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, ReactNode } from 'react';
import { 
  VKTeamsIntegrationState, 
  VKTeamsBotConfig, 
  VKTeamsBotStats,
  VKTeamsError,
  VKTeamsApiResponse,
  VKTeamsBotStatusResponse,
  VKTeamsBotConfigResponse 
} from '../domain/VKTeamsModels';

// ============================================================================
// State & Action Types
// ============================================================================

type VKTeamsAction = 
  | { type: 'SET_LOADING'; payload: boolean }
  | { type: 'SET_ERROR'; payload: string | undefined }
  | { type: 'SET_CONNECTION_STATUS'; payload: boolean }
  | { type: 'SET_CONFIG'; payload: VKTeamsBotConfig | undefined }
  | { type: 'SET_STATS'; payload: VKTeamsBotStats | undefined }
  | { type: 'SET_LAST_SYNC'; payload: Date }
  | { type: 'RESET_STATE' };

interface VKTeamsState extends VKTeamsIntegrationState {
  isLoading: boolean;
}

// ============================================================================
// Initial State
// ============================================================================

const initialState: VKTeamsState = {
  isLoading: false,
  isConnected: false,
  isConfigured: false,
  config: undefined,
  stats: undefined,
  lastError: undefined,
  lastSync: undefined,
};

// ============================================================================
// Reducer
// ============================================================================

const vkTeamsReducer = (state: VKTeamsState, action: VKTeamsAction): VKTeamsState => {
  switch (action.type) {
    case 'SET_LOADING':
      return { ...state, isLoading: action.payload };
    
    case 'SET_ERROR':
      return { ...state, lastError: action.payload };
    
    case 'SET_CONNECTION_STATUS':
      return { ...state, isConnected: action.payload };
    
    case 'SET_CONFIG':
      return { 
        ...state, 
        config: action.payload,
        isConfigured: !!action.payload,
        isConnected: action.payload?.isActive ?? false
      };
    
    case 'SET_STATS':
      return { ...state, stats: action.payload };
    
    case 'SET_LAST_SYNC':
      return { ...state, lastSync: action.payload };
    
    case 'RESET_STATE':
      return initialState;
    
    default:
      return state;
  }
};

// ============================================================================
// Context Interface
// ============================================================================

interface VKTeamsContextType {
  state: VKTeamsState;
  actions: {
    // Configuration
    fetchBotStatus: () => Promise<void>;
    configureBot: (config: Partial<VKTeamsBotConfig>) => Promise<void>;
    startBot: () => Promise<void>;
    stopBot: () => Promise<void>;
    
    // Statistics
    fetchStats: () => Promise<void>;
    
    // Connection
    testConnection: () => Promise<boolean>;
    
    // Health check
    checkHealth: () => Promise<boolean>;
    
    // Utilities
    resetState: () => void;
    clearError: () => void;
  };
}

const VKTeamsContext = createContext<VKTeamsContextType | undefined>(undefined);

// ============================================================================
// API Service
// ============================================================================

class VKTeamsApiService {
  private apiUrl: string;
  private token: string | null = null;

  constructor(apiUrl: string = process.env.REACT_APP_API_URL || 'http://localhost:8000') {
    this.apiUrl = apiUrl;
  }

  setToken(token: string | null) {
    this.token = token;
  }

  private getHeaders(): Record<string, string> {
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };
    
    if (this.token) {
      headers['Authorization'] = `Bearer ${this.token}`;
    }
    
    return headers;
  }

  async fetchBotStatus(): Promise<VKTeamsBotStatusResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/vk-teams/bot/status`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new VKTeamsError(`Failed to fetch bot status: ${response.statusText}`);
    }

    return response.json();
  }

  async configureBot(config: Partial<VKTeamsBotConfig>): Promise<VKTeamsBotConfigResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/vk-teams/bot/configure`, {
      method: 'POST',
      headers: this.getHeaders(),
      body: JSON.stringify(config),
    });

    if (!response.ok) {
      throw new VKTeamsError(`Failed to configure bot: ${response.statusText}`);
    }

    return response.json();
  }

  async startBot(): Promise<VKTeamsApiResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/vk-teams/bot/start`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new VKTeamsError(`Failed to start bot: ${response.statusText}`);
    }

    return response.json();
  }

  async stopBot(): Promise<VKTeamsApiResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/vk-teams/bot/stop`, {
      method: 'POST',
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new VKTeamsError(`Failed to stop bot: ${response.statusText}`);
    }

    return response.json();
  }

  async fetchStats(): Promise<VKTeamsApiResponse<VKTeamsBotStats>> {
    const response = await fetch(`${this.apiUrl}/api/v1/vk-teams/bot/stats`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new VKTeamsError(`Failed to fetch bot stats: ${response.statusText}`);
    }

    return response.json();
  }

  async checkHealth(): Promise<VKTeamsApiResponse> {
    const response = await fetch(`${this.apiUrl}/api/v1/vk-teams/bot/health`, {
      headers: this.getHeaders(),
    });

    if (!response.ok) {
      throw new VKTeamsError(`Failed to check bot health: ${response.statusText}`);
    }

    return response.json();
  }
}

// ============================================================================
// Provider Component
// ============================================================================

interface VKTeamsProviderProps {
  children: ReactNode;
  apiUrl?: string;
}

export const VKTeamsProvider: React.FC<VKTeamsProviderProps> = ({ 
  children, 
  apiUrl 
}) => {
  const [state, dispatch] = useReducer(vkTeamsReducer, initialState);
  const apiService = new VKTeamsApiService(apiUrl);

  // Set token when available
  useEffect(() => {
    const token = localStorage.getItem('authToken');
    if (token) {
      apiService.setToken(token);
    }
  }, []);

  // Action creators
  const actions = {
    fetchBotStatus: useCallback(async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const response = await apiService.fetchBotStatus();
        
        const config: VKTeamsBotConfig = {
          botId: response.bot_id,
          botName: response.bot_name,
          botToken: '', // Token not returned for security
          apiUrl: '',
          webhookUrl: response.webhook_url,
          isActive: response.is_active,
          allowedUsers: [],
          allowedChats: [],
          autoStart: response.is_active,
          created: new Date(),
          updated: new Date(),
        };

        dispatch({ type: 'SET_CONFIG', payload: config });
        dispatch({ type: 'SET_ERROR', payload: undefined });
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, []),

    configureBot: useCallback(async (config: Partial<VKTeamsBotConfig>) => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const response = await apiService.configureBot(config);
        
        if (response.success) {
          await actions.fetchBotStatus();
          dispatch({ type: 'SET_ERROR', payload: null });
        } else {
          throw new VKTeamsError(response.message);
        }
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, []),

    startBot: useCallback(async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        await apiService.startBot();
        await actions.fetchBotStatus();
        dispatch({ type: 'SET_ERROR', payload: null });
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, []),

    stopBot: useCallback(async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        await apiService.stopBot();
        await actions.fetchBotStatus();
        dispatch({ type: 'SET_ERROR', payload: null });
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, []),

    fetchStats: useCallback(async () => {
      dispatch({ type: 'SET_LOADING', payload: true });
      try {
        const response = await apiService.fetchStats();
        dispatch({ type: 'SET_STATS', payload: response.data || null });
        dispatch({ type: 'SET_ERROR', payload: null });
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
      } finally {
        dispatch({ type: 'SET_LOADING', payload: false });
      }
    }, []),

    testConnection: useCallback(async (): Promise<boolean> => {
      try {
        const response = await apiService.checkHealth();
        const isConnected = response.success;
        dispatch({ type: 'SET_CONNECTION_STATUS', payload: isConnected });
        return isConnected;
      } catch (error) {
        dispatch({ type: 'SET_CONNECTION_STATUS', payload: false });
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
        return false;
      }
    }, []),

    checkHealth: useCallback(async (): Promise<boolean> => {
      try {
        const response = await apiService.checkHealth();
        return response.success;
      } catch (error) {
        dispatch({ type: 'SET_ERROR', payload: error instanceof Error ? error.message : 'Unknown error' });
        return false;
      }
    }, []),

    resetState: useCallback(() => {
      dispatch({ type: 'RESET_STATE' });
    }, []),

    clearError: useCallback(() => {
      dispatch({ type: 'SET_ERROR', payload: null });
    }, []),
  };

  const contextValue = {
    state,
    actions,
  };

  return (
    <VKTeamsContext.Provider value={contextValue}>
      {children}
    </VKTeamsContext.Provider>
  );
};

// ============================================================================
// Hooks
// ============================================================================

export const useVKTeams = (): VKTeamsContextType => {
  const context = useContext(VKTeamsContext);
  if (!context) {
    throw new Error('useVKTeams must be used within a VKTeamsProvider');
  }
  return context;
};

// Convenience hooks
export const useVKTeamsConfig = () => {
  const { state, actions } = useVKTeams();
  return {
    config: state.config,
    isConfigured: state.isConfigured,
    fetchBotStatus: actions.fetchBotStatus,
    configureBot: actions.configureBot,
  };
};

export const useVKTeamsBot = () => {
  const { state, actions } = useVKTeams();
  return {
    isConnected: state.isConnected,
    isActive: state.config?.isActive ?? false,
    startBot: actions.startBot,
    stopBot: actions.stopBot,
    testConnection: actions.testConnection,
  };
};

export const useVKTeamsStats = () => {
  const { state, actions } = useVKTeams();
  return {
    stats: state.stats,
    fetchStats: actions.fetchStats,
  };
};

export const useVKTeamsError = () => {
  const { state, actions } = useVKTeams();
  return {
    error: state.lastError,
    clearError: actions.clearError,
  };
}; 