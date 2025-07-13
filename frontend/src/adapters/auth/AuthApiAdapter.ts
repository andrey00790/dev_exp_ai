/**
 * Auth API Adapter
 * 
 * Adapter for authentication API calls.
 * Implements the port pattern for external API communication.
 */

import { User, UserPreferences, Role } from '../../domain/auth/entities';

// ============================================================================
// Types
// ============================================================================

interface LoginRequest {
  email: string;
  password: string;
}

interface RegisterRequest {
  email: string;
  name: string;
  password: string;
}

interface AuthResponse {
  user: User;
  session: {
    id: string;
    token: string;
    refresh_token: string;
    expires_at: string;
    is_active: boolean;
  };
}

interface ApiError {
  message: string;
  code?: string;
  details?: Record<string, any>;
}

// ============================================================================
// Auth API Adapter
// ============================================================================

export class AuthApiAdapter {
  private baseUrl: string;
  private defaultHeaders: HeadersInit;

  constructor(baseUrl: string = process.env.REACT_APP_API_URL || 'http://localhost:8000') {
    this.baseUrl = baseUrl;
    this.defaultHeaders = {
      'Content-Type': 'application/json',
    };
  }

  // ============================================================================
  // Private Methods
  // ============================================================================

  private async makeRequest<T>(
    endpoint: string, 
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;
    
    const config: RequestInit = {
      ...options,
      headers: {
        ...this.defaultHeaders,
        ...options.headers,
      },
    };

    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({}));
        throw new ApiError(
          errorData.message || `HTTP ${response.status}: ${response.statusText}`,
          errorData.code,
          errorData.details
        );
      }

      return await response.json();
    } catch (error) {
      if (error instanceof ApiError) {
        throw error;
      }
      
      throw new ApiError(
        error instanceof Error ? error.message : 'Network request failed'
      );
    }
  }

  private getAuthHeaders(token: string): HeadersInit {
    return {
      ...this.defaultHeaders,
      Authorization: `Bearer ${token}`,
    };
  }

  // ============================================================================
  // Authentication Methods
  // ============================================================================

  async login(credentials: LoginRequest): Promise<AuthResponse> {
    return this.makeRequest<AuthResponse>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify(credentials),
    });
  }

  async register(data: RegisterRequest): Promise<AuthResponse> {
    return this.makeRequest<AuthResponse>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify(data),
    });
  }

  async logout(token: string): Promise<void> {
    await this.makeRequest('/api/v1/auth/logout', {
      method: 'POST',
      headers: this.getAuthHeaders(token),
    });
  }

  async refreshToken(refreshToken: string): Promise<AuthResponse> {
    return this.makeRequest<AuthResponse>('/api/v1/auth/refresh', {
      method: 'POST',
      body: JSON.stringify({
        refresh_token: refreshToken,
      }),
    });
  }

  async getCurrentUser(token: string): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/me', {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });
  }

  // ============================================================================
  // Profile Management
  // ============================================================================

  async updateProfile(token: string, userData: Partial<User>): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/profile', {
      method: 'PUT',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify(userData),
    });
  }

  async updatePreferences(
    token: string, 
    preferences: Partial<UserPreferences>
  ): Promise<User> {
    return this.makeRequest<User>('/api/v1/auth/preferences', {
      method: 'PUT',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify(preferences),
    });
  }

  async changePassword(
    token: string,
    oldPassword: string,
    newPassword: string
  ): Promise<void> {
    await this.makeRequest('/api/v1/auth/change-password', {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        old_password: oldPassword,
        new_password: newPassword,
      }),
    });
  }

  // ============================================================================
  // Password Reset
  // ============================================================================

  async requestPasswordReset(email: string): Promise<void> {
    await this.makeRequest('/api/v1/auth/password-reset/request', {
      method: 'POST',
      body: JSON.stringify({ email }),
    });
  }

  async resetPassword(token: string, newPassword: string): Promise<void> {
    await this.makeRequest('/api/v1/auth/password-reset/confirm', {
      method: 'POST',
      body: JSON.stringify({
        token,
        new_password: newPassword,
      }),
    });
  }

  // ============================================================================
  // Email Verification
  // ============================================================================

  async sendVerificationEmail(token: string): Promise<void> {
    await this.makeRequest('/api/v1/auth/verify-email/send', {
      method: 'POST',
      headers: this.getAuthHeaders(token),
    });
  }

  async verifyEmail(verificationToken: string): Promise<void> {
    await this.makeRequest('/api/v1/auth/verify-email/confirm', {
      method: 'POST',
      body: JSON.stringify({
        token: verificationToken,
      }),
    });
  }

  // ============================================================================
  // Role Management
  // ============================================================================

  async getUserRoles(token: string, userId: string): Promise<Role[]> {
    return this.makeRequest<Role[]>(`/api/v1/auth/users/${userId}/roles`, {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });
  }

  async assignRole(
    token: string,
    userId: string,
    roleName: string
  ): Promise<void> {
    await this.makeRequest(`/api/v1/auth/users/${userId}/roles`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({
        role_name: roleName,
      }),
    });
  }

  async revokeRole(
    token: string,
    userId: string,
    roleName: string
  ): Promise<void> {
    await this.makeRequest(`/api/v1/auth/users/${userId}/roles/${roleName}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });
  }

  // ============================================================================
  // Session Management
  // ============================================================================

  async getAllSessions(token: string): Promise<Array<{
    id: string;
    created_at: string;
    last_activity: string;
    ip_address?: string;
    user_agent?: string;
    is_current: boolean;
  }>> {
    return this.makeRequest('/api/v1/auth/sessions', {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });
  }

  async revokeSession(token: string, sessionId: string): Promise<void> {
    await this.makeRequest(`/api/v1/auth/sessions/${sessionId}`, {
      method: 'DELETE',
      headers: this.getAuthHeaders(token),
    });
  }

  async revokeAllSessions(token: string): Promise<void> {
    await this.makeRequest('/api/v1/auth/sessions/revoke-all', {
      method: 'POST',
      headers: this.getAuthHeaders(token),
    });
  }

  // ============================================================================
  // Permissions
  // ============================================================================

  async checkPermission(
    token: string,
    permission: string
  ): Promise<{ hasPermission: boolean }> {
    return this.makeRequest(`/api/v1/auth/permissions/check`, {
      method: 'POST',
      headers: this.getAuthHeaders(token),
      body: JSON.stringify({ permission }),
    });
  }

  async getUserPermissions(token: string): Promise<string[]> {
    return this.makeRequest('/api/v1/auth/permissions', {
      method: 'GET',
      headers: this.getAuthHeaders(token),
    });
  }
}

// ============================================================================
// Error Classes
// ============================================================================

export class ApiError extends Error {
  public code?: string;
  public details?: Record<string, any>;

  constructor(message: string, code?: string, details?: Record<string, any>) {
    super(message);
    this.name = 'ApiError';
    this.code = code;
    this.details = details;
  }
}

// ============================================================================
// Default Instance
// ============================================================================

export const authApiAdapter = new AuthApiAdapter(); 