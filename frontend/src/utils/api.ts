// Context7 pattern: API utility with automatic JWT token injection for authenticated requests
// Following explicit export patterns for better tree-shaking and compatibility

export class ApiClient {
  private static getAuthToken(): string | null {
    return localStorage.getItem('auth_token');
  }

  static async fetch(url: string, options: RequestInit = {}): Promise<Response> {
    const token = this.getAuthToken();
    
    // Don't add auth header for auth endpoints
    const isAuthEndpoint = url.startsWith('/auth/');
    
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      ...(options.headers as Record<string, string> || {}),
    };

    // Add Authorization header if token exists and not auth endpoint
    if (token && !isAuthEndpoint) {
      headers['Authorization'] = `Bearer ${token}`;
    }

    const config: RequestInit = {
      ...options,
      headers,
    };

    try {
      const response = await fetch(url, config);
      
      // If 401 Unauthorized, clear token and redirect to login
      if (response.status === 401 && !isAuthEndpoint) {
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
        window.location.href = '/login';
        throw new Error('Authentication required');
      }

      return response;
    } catch (error) {
      console.error('API request failed:', error);
      throw error;
    }
  }

  static async get(url: string, options: RequestInit = {}): Promise<Response> {
    return this.fetch(url, { ...options, method: 'GET' });
  }

  static async post(url: string, data?: any, options: RequestInit = {}): Promise<Response> {
    return this.fetch(url, {
      ...options,
      method: 'POST',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  static async put(url: string, data?: any, options: RequestInit = {}): Promise<Response> {
    return this.fetch(url, {
      ...options,
      method: 'PUT',
      body: data ? JSON.stringify(data) : undefined,
    });
  }

  static async delete(url: string, options: RequestInit = {}): Promise<Response> {
    return this.fetch(url, { ...options, method: 'DELETE' });
  }
}

// Context7 pattern: Named exports for explicit imports
export { ApiClient as apiClient };

// Convenience function to maintain backward compatibility
export const apiFetch = ApiClient.fetch;

// Default export for backward compatibility  
export default ApiClient;
