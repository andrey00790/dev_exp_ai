import axios, { AxiosInstance, AxiosResponse } from 'axios';
import toast from 'react-hot-toast';

// API Configuration
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

// Create axios instance
const apiClient: AxiosInstance = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Add auth token if available
    const token = localStorage.getItem('auth_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

// Response interceptor
apiClient.interceptors.response.use(
  (response: AxiosResponse) => {
    return response;
  },
  (error) => {
    // Handle common errors
    if (error.response?.status === 401) {
      localStorage.removeItem('auth_token');
      toast.error('Authentication expired. Please login again.');
    } else if (error.response?.status === 500) {
      toast.error('Server error. Please try again later.');
    } else if (error.code === 'ECONNABORTED') {
      toast.error('Request timeout. Please try again.');
    } else if (!error.response) {
      toast.error('Network error. Please check your connection.');
    }
    
    return Promise.reject(error);
  }
);

// API Types
export interface SearchRequest {
  query: string;
  sources?: string[];
  limit?: number;
  offset?: number;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  url?: string;
  score: number;
  metadata?: Record<string, any>;
}

export interface SearchResponse {
  results: SearchResult[];
  total: number;
  query: string;
  took: number;
}

export interface GenerateRFCRequest {
  title: string;
  description?: string;
  template?: string;
  context?: string;
}

export interface GenerateRFCResponse {
  session_id: string;
  rfc_content?: string;
  questions?: string[];
  status: 'started' | 'questions' | 'generating' | 'completed' | 'error';
}

export interface DocumentationRequest {
  files: File[];
  project_name?: string;
  doc_type?: 'readme' | 'api' | 'technical';
}

export interface DocumentationResponse {
  documentation: string;
  analysis: {
    files_processed: number;
    languages_detected: string[];
    architecture_patterns: string[];
  };
}

// API Methods
export const api = {
  // Health check
  health: async (): Promise<{ status: string }> => {
    const response = await apiClient.get('/health');
    return response.data;
  },

  // Search
  search: async (params: SearchRequest): Promise<SearchResponse> => {
    const response = await apiClient.post('/api/v1/search', params);
    return response.data;
  },

  vectorSearch: async (params: SearchRequest): Promise<SearchResponse> => {
    const response = await apiClient.post('/api/v1/vector-search', params);
    return response.data;
  },

  // RFC Generation
  generateRFC: async (params: GenerateRFCRequest): Promise<GenerateRFCResponse> => {
    const response = await apiClient.post('/api/v1/generate', params);
    return response.data;
  },

  getRFCSession: async (sessionId: string): Promise<GenerateRFCResponse> => {
    const response = await apiClient.get(`/api/v1/generate/${sessionId}`);
    return response.data;
  },

  answerRFCQuestions: async (sessionId: string, answers: Record<string, string>): Promise<GenerateRFCResponse> => {
    const response = await apiClient.post(`/api/v1/generate/${sessionId}/answers`, { answers });
    return response.data;
  },

  // Documentation
  generateDocumentation: async (params: DocumentationRequest): Promise<DocumentationResponse> => {
    const formData = new FormData();
    params.files.forEach((file) => {
      formData.append('files', file);
    });
    if (params.project_name) {
      formData.append('project_name', params.project_name);
    }
    if (params.doc_type) {
      formData.append('doc_type', params.doc_type);
    }

    const response = await apiClient.post('/api/v1/documentation', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  },

  // User Settings
  getUserSettings: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/users/settings');
    return response.data;
  },

  updateUserSettings: async (settings: any): Promise<any> => {
    const response = await apiClient.put('/api/v1/users/settings', settings);
    return response.data;
  },

  // Data Sources
  getDataSources: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/users/data-sources');
    return response.data;
  },

  updateDataSources: async (sources: any): Promise<any> => {
    const response = await apiClient.put('/api/v1/users/data-sources', sources);
    return response.data;
  },

  // Sync
  syncDataSources: async (): Promise<any> => {
    const response = await apiClient.post('/api/v1/sync');
    return response.data;
  },

  getSyncStatus: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/sync/status');
    return response.data;
  },

  // Monitoring
  getMetrics: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/monitoring/metrics');
    return response.data;
  },

  getSystemHealth: async (): Promise<any> => {
    const response = await apiClient.get('/api/v1/monitoring/health');
    return response.data;
  },
};

export default api;
