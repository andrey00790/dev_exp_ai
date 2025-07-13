/**
 * Context7 AI Analysis Context
 * 
 * Specialized context for AI analysis operations.
 * Integrates with hexagonal architecture backend.
 */

import React, { createContext, useContext, useReducer, useCallback, useEffect, ReactNode } from 'react';

// ============================================================================
// Types
// ============================================================================

export enum AnalysisType {
  CODE_ANALYSIS = 'code_analysis',
  SECURITY_ANALYSIS = 'security_analysis',
  PERFORMANCE_ANALYSIS = 'performance_analysis',
  ARCHITECTURE_ANALYSIS = 'architecture_analysis',
  DOCUMENTATION_ANALYSIS = 'documentation_analysis',
  QUALITY_ANALYSIS = 'quality_analysis',
}

export enum AnalysisStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled',
}

export enum Priority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}

interface AnalysisResult {
  id: string;
  analysisType: AnalysisType;
  content: string;
  score: number;
  confidence: number;
  suggestions: string[];
  metadata: Record<string, any>;
  createdAt: Date;
}

interface AnalysisRequest {
  id: string;
  analysisType: AnalysisType;
  content: string;
  priority: Priority;
  parameters: Record<string, any>;
  userId?: string;
  projectId?: string;
  createdAt: Date;
}

interface AnalysisSession {
  id: string;
  request: AnalysisRequest;
  status: AnalysisStatus;
  results: AnalysisResult[];
  errorMessage?: string;
  startedAt?: Date;
  completedAt?: Date;
  createdAt: Date;
  updatedAt?: Date;
}

interface AIModel {
  id: string;
  name: string;
  version: string;
  modelType: string;
  capabilities: AnalysisType[];
  parameters: Record<string, any>;
  isActive: boolean;
  createdAt: Date;
}

interface AnalysisMetrics {
  analysisType: AnalysisType;
  totalAnalyses: number;
  successfulAnalyses: number;
  failedAnalyses: number;
  averageDuration: number;
  averageScore: number;
  averageConfidence: number;
  successRate: number;
}

interface AIAnalysisState {
  // Current analysis
  currentSession: AnalysisSession | null;
  
  // History
  sessions: AnalysisSession[];
  
  // Models
  availableModels: AIModel[];
  selectedModel: AIModel | null;
  
  // Metrics
  metrics: Record<AnalysisType, AnalysisMetrics>;
  
  // UI state
  isAnalyzing: boolean;
  error: string | null;
  
  // Real-time updates
  streamingResults: AnalysisResult[];
}

// ============================================================================
// Actions
// ============================================================================

type AIAnalysisAction = 
  | { type: 'START_ANALYSIS'; payload: { request: AnalysisRequest; model: AIModel } }
  | { type: 'ANALYSIS_PROGRESS'; payload: { sessionId: string; result: AnalysisResult } }
  | { type: 'ANALYSIS_COMPLETED'; payload: { sessionId: string; results: AnalysisResult[] } }
  | { type: 'ANALYSIS_FAILED'; payload: { sessionId: string; error: string } }
  | { type: 'CANCEL_ANALYSIS'; payload: { sessionId: string } }
  | { type: 'LOAD_MODELS'; payload: AIModel[] }
  | { type: 'SELECT_MODEL'; payload: AIModel }
  | { type: 'LOAD_SESSIONS'; payload: AnalysisSession[] }
  | { type: 'UPDATE_METRICS'; payload: Record<AnalysisType, AnalysisMetrics> }
  | { type: 'SET_ERROR'; payload: string | null }
  | { type: 'CLEAR_ERROR' }
  | { type: 'STREAMING_RESULT'; payload: AnalysisResult };

// ============================================================================
// Initial State
// ============================================================================

const initialState: AIAnalysisState = {
  currentSession: null,
  sessions: [],
  availableModels: [],
  selectedModel: null,
  metrics: {} as Record<AnalysisType, AnalysisMetrics>,
  isAnalyzing: false,
  error: null,
  streamingResults: [],
};

// ============================================================================
// Reducer
// ============================================================================

const aiAnalysisReducer = (state: AIAnalysisState, action: AIAnalysisAction): AIAnalysisState => {
  switch (action.type) {
    case 'START_ANALYSIS':
      const newSession: AnalysisSession = {
        id: Date.now().toString(),
        request: action.payload.request,
        status: AnalysisStatus.PENDING,
        results: [],
        createdAt: new Date(),
      };
      
      return {
        ...state,
        currentSession: newSession,
        sessions: [newSession, ...state.sessions],
        isAnalyzing: true,
        error: null,
        streamingResults: [],
      };
    
    case 'ANALYSIS_PROGRESS':
      const progressUpdatedSessions = state.sessions.map(session => 
        session.id === action.payload.sessionId 
          ? { 
              ...session, 
              status: AnalysisStatus.RUNNING,
              startedAt: session.startedAt || new Date(),
              results: [...session.results, action.payload.result],
              updatedAt: new Date()
            }
          : session
      );
      
      return {
        ...state,
        currentSession: state.currentSession?.id === action.payload.sessionId 
          ? progressUpdatedSessions.find(s => s.id === action.payload.sessionId) || state.currentSession
          : state.currentSession,
        sessions: progressUpdatedSessions,
      };
    
    case 'ANALYSIS_COMPLETED':
      const completedUpdatedSessions = state.sessions.map(session => 
        session.id === action.payload.sessionId 
          ? { 
              ...session, 
              status: AnalysisStatus.COMPLETED,
              results: action.payload.results,
              completedAt: new Date(),
              updatedAt: new Date()
            }
          : session
      );
      
      return {
        ...state,
        currentSession: state.currentSession?.id === action.payload.sessionId 
          ? completedUpdatedSessions.find(s => s.id === action.payload.sessionId) || state.currentSession
          : state.currentSession,
        sessions: completedUpdatedSessions,
        isAnalyzing: false,
        streamingResults: [],
      };
    
    case 'ANALYSIS_FAILED':
      const failedUpdatedSessions = state.sessions.map(session => 
        session.id === action.payload.sessionId 
          ? { 
              ...session, 
              status: AnalysisStatus.FAILED,
              errorMessage: action.payload.error,
              completedAt: new Date(),
              updatedAt: new Date()
            }
          : session
      );
      
      return {
        ...state,
        currentSession: state.currentSession?.id === action.payload.sessionId 
          ? failedUpdatedSessions.find(s => s.id === action.payload.sessionId) || state.currentSession
          : state.currentSession,
        sessions: failedUpdatedSessions,
        isAnalyzing: false,
        error: action.payload.error,
        streamingResults: [],
      };
    
    case 'CANCEL_ANALYSIS':
      const cancelledUpdatedSessions = state.sessions.map(session => 
        session.id === action.payload.sessionId 
          ? { 
              ...session, 
              status: AnalysisStatus.CANCELLED,
              completedAt: new Date(),
              updatedAt: new Date()
            }
          : session
      );
      
      return {
        ...state,
        currentSession: state.currentSession?.id === action.payload.sessionId 
          ? cancelledUpdatedSessions.find(s => s.id === action.payload.sessionId) || state.currentSession
          : state.currentSession,
        sessions: cancelledUpdatedSessions,
        isAnalyzing: false,
        streamingResults: [],
      };
    
    case 'LOAD_MODELS':
      return {
        ...state,
        availableModels: action.payload,
        selectedModel: state.selectedModel || action.payload.find(m => m.isActive) || null,
      };
    
    case 'SELECT_MODEL':
      return {
        ...state,
        selectedModel: action.payload,
      };
    
    case 'LOAD_SESSIONS':
      return {
        ...state,
        sessions: action.payload,
      };
    
    case 'UPDATE_METRICS':
      return {
        ...state,
        metrics: action.payload,
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
    
    case 'STREAMING_RESULT':
      return {
        ...state,
        streamingResults: [...state.streamingResults, action.payload],
      };
    
    default:
      return state;
  }
};

// ============================================================================
// Context
// ============================================================================

interface AIAnalysisContextType {
  state: AIAnalysisState;
  actions: {
    startAnalysis: (request: Partial<AnalysisRequest>) => Promise<string>;
    cancelAnalysis: (sessionId: string) => Promise<void>;
    loadModels: () => Promise<void>;
    selectModel: (model: AIModel) => void;
    loadSessions: () => Promise<void>;
    loadMetrics: () => Promise<void>;
    clearError: () => void;
  };
}

const AIAnalysisContext = createContext<AIAnalysisContextType | undefined>(undefined);

// ============================================================================
// Provider
// ============================================================================

interface AIAnalysisProviderProps {
  children: ReactNode;
  apiUrl?: string;
}

export const AIAnalysisProvider: React.FC<AIAnalysisProviderProps> = ({ 
  children, 
  apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000' 
}) => {
  const [state, dispatch] = useReducer(aiAnalysisReducer, initialState);

  // ============================================================================
  // API Helpers
  // ============================================================================

  const apiRequest = async (endpoint: string, options: RequestInit = {}) => {
    const url = `${apiUrl}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API Error: ${response.status} ${response.statusText}`);
    }

    return response.json();
  };

  // ============================================================================
  // Actions
  // ============================================================================

  const startAnalysis = useCallback(async (request: Partial<AnalysisRequest>): Promise<string> => {
    try {
      if (!state.selectedModel) {
        throw new Error('No model selected');
      }

      const analysisRequest: AnalysisRequest = {
        id: Date.now().toString(),
        analysisType: request.analysisType || AnalysisType.CODE_ANALYSIS,
        content: request.content || '',
        priority: request.priority || Priority.MEDIUM,
        parameters: request.parameters || {},
        userId: request.userId,
        projectId: request.projectId,
        createdAt: new Date(),
      };

      dispatch({ 
        type: 'START_ANALYSIS', 
        payload: { request: analysisRequest, model: state.selectedModel } 
      });

      // Start analysis via API
      const response = await apiRequest('/api/v1/ai-analysis/start', {
        method: 'POST',
        body: JSON.stringify({
          request: analysisRequest,
          model_id: state.selectedModel.id,
        }),
      });

      // Set up WebSocket for real-time updates
      const ws = new WebSocket(`ws://localhost:8000/api/v1/ai-analysis/ws/${response.session_id}`);
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'result') {
          dispatch({ 
            type: 'ANALYSIS_PROGRESS', 
            payload: { sessionId: response.session_id, result: data.result } 
          });
        } else if (data.type === 'completed') {
          dispatch({ 
            type: 'ANALYSIS_COMPLETED', 
            payload: { sessionId: response.session_id, results: data.results } 
          });
          ws.close();
        } else if (data.type === 'error') {
          dispatch({ 
            type: 'ANALYSIS_FAILED', 
            payload: { sessionId: response.session_id, error: data.error } 
          });
          ws.close();
        }
      };

      return response.session_id;
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Analysis failed' 
      });
      throw error;
    }
  }, [state.selectedModel]);

  const cancelAnalysis = useCallback(async (sessionId: string): Promise<void> => {
    try {
      await apiRequest(`/api/v1/ai-analysis/cancel/${sessionId}`, {
        method: 'POST',
      });

      dispatch({ type: 'CANCEL_ANALYSIS', payload: { sessionId } });
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Cancel failed' 
      });
    }
  }, []);

  const loadModels = useCallback(async (): Promise<void> => {
    try {
      const models = await apiRequest('/api/v1/ai-analysis/models');
      dispatch({ type: 'LOAD_MODELS', payload: models });
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Failed to load models' 
      });
    }
  }, []);

  const selectModel = useCallback((model: AIModel): void => {
    dispatch({ type: 'SELECT_MODEL', payload: model });
  }, []);

  const loadSessions = useCallback(async (): Promise<void> => {
    try {
      const sessions = await apiRequest('/api/v1/ai-analysis/sessions');
      dispatch({ type: 'LOAD_SESSIONS', payload: sessions });
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Failed to load sessions' 
      });
    }
  }, []);

  const loadMetrics = useCallback(async (): Promise<void> => {
    try {
      const metrics = await apiRequest('/api/v1/ai-analysis/metrics');
      dispatch({ type: 'UPDATE_METRICS', payload: metrics });
    } catch (error) {
      dispatch({ 
        type: 'SET_ERROR', 
        payload: error instanceof Error ? error.message : 'Failed to load metrics' 
      });
    }
  }, []);

  const clearError = useCallback(() => {
    dispatch({ type: 'CLEAR_ERROR' });
  }, []);

  // ============================================================================
  // Effects
  // ============================================================================

  useEffect(() => {
    loadModels();
    loadSessions();
    loadMetrics();
  }, [loadModels, loadSessions, loadMetrics]);

  // ============================================================================
  // Context Value
  // ============================================================================

  const contextValue: AIAnalysisContextType = {
    state,
    actions: {
      startAnalysis,
      cancelAnalysis,
      loadModels,
      selectModel,
      loadSessions,
      loadMetrics,
      clearError,
    },
  };

  return (
    <AIAnalysisContext.Provider value={contextValue}>
      {children}
    </AIAnalysisContext.Provider>
  );
};

// ============================================================================
// Hook
// ============================================================================

export const useAIAnalysis = (): AIAnalysisContextType => {
  const context = useContext(AIAnalysisContext);
  if (!context) {
    throw new Error('useAIAnalysis must be used within an AIAnalysisProvider');
  }
  return context;
};

// ============================================================================
// Convenience Hooks
// ============================================================================

export const useCurrentAnalysis = () => {
  const { state } = useAIAnalysis();
  return state.currentSession;
};

export const useAnalysisHistory = () => {
  const { state } = useAIAnalysis();
  return state.sessions;
};

export const useAnalysisModels = () => {
  const { state, actions } = useAIAnalysis();
  return {
    models: state.availableModels,
    selectedModel: state.selectedModel,
    selectModel: actions.selectModel,
  };
};

export const useAnalysisMetrics = () => {
  const { state } = useAIAnalysis();
  return state.metrics;
}; 