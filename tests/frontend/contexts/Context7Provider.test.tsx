/**
 * Context7Provider Tests
 * 
 * Comprehensive test suite for the central Context7 state management provider.
 * Tests all core functionality including auth, LLM sessions, feature flags, etc.
 */

import React from 'react';
import { render, screen, fireEvent, waitFor, act } from '@testing-library/react';
import { Context7Provider, useContext7, useAuth, useLLMSession, useFeatureFlags } from '../../../src/contexts/Context7Provider';
import { User, UserRole } from '../../../src/domain/auth/entities';

// Mock localStorage
const mockLocalStorage = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};

Object.defineProperty(window, 'localStorage', {
  value: mockLocalStorage,
});

// Mock performance API
Object.defineProperty(window, 'performance', {
  value: {
    now: jest.fn(() => Date.now()),
    memory: {
      usedJSHeapSize: 1024 * 1024,
      totalJSHeapSize: 2048 * 1024,
    },
  },
});

// Test components
const TestComponent: React.FC = () => {
  const { state, actions } = useContext7();
  
  return (
    <div>
      <div data-testid="authenticated">{state.isAuthenticated ? 'true' : 'false'}</div>
      <div data-testid="user-name">{state.user?.name || 'No user'}</div>
      <div data-testid="loading">{state.isLoading ? 'true' : 'false'}</div>
      <div data-testid="error">{state.error || 'No error'}</div>
      <div data-testid="dark-mode">{state.features.darkMode ? 'true' : 'false'}</div>
      <div data-testid="current-session">{state.currentLLMSession?.id || 'No session'}</div>
      <div data-testid="notifications-count">{state.notifications.length}</div>
      
      <button onClick={() => actions.setLoading(true)} data-testid="set-loading">
        Set Loading
      </button>
      <button onClick={() => actions.setError('Test error')} data-testid="set-error">
        Set Error
      </button>
      <button onClick={() => actions.toggleFeature('darkMode', true)} data-testid="toggle-dark">
        Toggle Dark Mode
      </button>
      <button onClick={() => actions.startLLMSession('gpt-4', 'openai')} data-testid="start-session">
        Start LLM Session
      </button>
      <button onClick={() => actions.addNotification({ type: 'info', title: 'Test', message: 'Test message', persistent: false })} data-testid="add-notification">
        Add Notification
      </button>
    </div>
  );
};

const AuthTestComponent: React.FC = () => {
  const { user, isAuthenticated, loginSuccess, logout, hasPermission } = useAuth();
  
  const handleLogin = () => {
    const mockUser: User = {
      id: 'test-user',
      name: 'Test User',
      email: 'test@example.com',
      avatar: null,
      preferences: {
        theme: 'light',
        language: 'en',
        notifications: true,
        autoSave: true,
        compactMode: false,
      },
      roles: [],
      permissions: ['read', 'write'],
      createdAt: new Date(),
      updatedAt: new Date(),
    };
    
    const mockRoles: UserRole[] = [
      {
        id: 'user-role',
        name: 'user',
        permissions: ['read', 'write'],
        description: 'Basic user role',
        createdAt: new Date(),
        updatedAt: new Date(),
      },
    ];
    
    loginSuccess(mockUser, 'test-token', mockRoles);
  };
  
  return (
    <div>
      <div data-testid="auth-status">{isAuthenticated ? 'authenticated' : 'not authenticated'}</div>
      <div data-testid="user-email">{user?.email || 'No email'}</div>
      <div data-testid="has-write-permission">{hasPermission('write') ? 'true' : 'false'}</div>
      <button onClick={handleLogin} data-testid="login">Login</button>
      <button onClick={logout} data-testid="logout">Logout</button>
    </div>
  );
};

const LLMSessionTestComponent: React.FC = () => {
  const { currentSession, sessions, startSession, endSession, addMessage } = useLLMSession();
  
  const handleAddMessage = () => {
    if (currentSession) {
      addMessage(currentSession.id, {
        id: 'test-message',
        role: 'user',
        content: 'Test message',
        timestamp: new Date(),
      });
    }
  };
  
  return (
    <div>
      <div data-testid="current-session-id">{currentSession?.id || 'No session'}</div>
      <div data-testid="sessions-count">{sessions.length}</div>
      <div data-testid="messages-count">{currentSession?.messages.length || 0}</div>
      <button onClick={() => startSession('gpt-4', 'openai')} data-testid="start-session">
        Start Session
      </button>
      <button onClick={() => currentSession && endSession(currentSession.id)} data-testid="end-session">
        End Session
      </button>
      <button onClick={handleAddMessage} data-testid="add-message">
        Add Message
      </button>
    </div>
  );
};

const FeatureFlagsTestComponent: React.FC = () => {
  const { features, toggleFeature, updateFeatures, isEnabled } = useFeatureFlags();
  
  return (
    <div>
      <div data-testid="dark-mode-enabled">{features.darkMode ? 'true' : 'false'}</div>
      <div data-testid="ai-analysis-enabled">{isEnabled('aiAnalysis') ? 'true' : 'false'}</div>
      <button onClick={() => toggleFeature('darkMode', !features.darkMode)} data-testid="toggle-dark-mode">
        Toggle Dark Mode
      </button>
      <button onClick={() => updateFeatures({ experimentalFeatures: true })} data-testid="enable-experimental">
        Enable Experimental
      </button>
    </div>
  );
};

// Helper to render with Context7Provider
const renderWithContext7 = (component: React.ReactElement) => {
  return render(
    <Context7Provider>
      {component}
    </Context7Provider>
  );
};

describe('Context7Provider', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockLocalStorage.getItem.mockReturnValue(null);
  });

  describe('Initial State', () => {
    it('should initialize with default state', () => {
      renderWithContext7(<TestComponent />);
      
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      expect(screen.getByTestId('user-name')).toHaveTextContent('No user');
      expect(screen.getByTestId('loading')).toHaveTextContent('false');
      expect(screen.getByTestId('error')).toHaveTextContent('No error');
      expect(screen.getByTestId('current-session')).toHaveTextContent('No session');
      expect(screen.getByTestId('notifications-count')).toHaveTextContent('0');
    });

    it('should initialize dark mode from localStorage', () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'theme') return 'dark';
        return null;
      });
      
      renderWithContext7(<TestComponent />);
      
      expect(screen.getByTestId('dark-mode')).toHaveTextContent('true');
    });
  });

  describe('System State Management', () => {
    it('should handle loading state', () => {
      renderWithContext7(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('set-loading'));
      
      expect(screen.getByTestId('loading')).toHaveTextContent('true');
    });

    it('should handle error state', () => {
      renderWithContext7(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('set-error'));
      
      expect(screen.getByTestId('error')).toHaveTextContent('Test error');
    });

    it('should handle notifications', () => {
      renderWithContext7(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('add-notification'));
      
      expect(screen.getByTestId('notifications-count')).toHaveTextContent('1');
    });
  });

  describe('Feature Flags', () => {
    it('should toggle feature flags', () => {
      renderWithContext7(<TestComponent />);
      
      fireEvent.click(screen.getByTestId('toggle-dark'));
      
      expect(screen.getByTestId('dark-mode')).toHaveTextContent('true');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('theme', 'dark');
    });

    it('should work with useFeatureFlags hook', () => {
      renderWithContext7(<FeatureFlagsTestComponent />);
      
      expect(screen.getByTestId('ai-analysis-enabled')).toHaveTextContent('true');
      
      fireEvent.click(screen.getByTestId('toggle-dark-mode'));
      
      expect(screen.getByTestId('dark-mode-enabled')).toHaveTextContent('true');
      
      fireEvent.click(screen.getByTestId('enable-experimental'));
      
      // Feature should be updated
      expect(screen.getByTestId('dark-mode-enabled')).toHaveTextContent('true');
    });
  });

  describe('Authentication', () => {
    it('should handle login success', () => {
      renderWithContext7(<AuthTestComponent />);
      
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated');
      
      fireEvent.click(screen.getByTestId('login'));
      
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('test@example.com');
      expect(screen.getByTestId('has-write-permission')).toHaveTextContent('true');
      expect(mockLocalStorage.setItem).toHaveBeenCalledWith('auth_token', 'test-token');
    });

    it('should handle logout', () => {
      renderWithContext7(<AuthTestComponent />);
      
      // Login first
      fireEvent.click(screen.getByTestId('login'));
      expect(screen.getByTestId('auth-status')).toHaveTextContent('authenticated');
      
      // Then logout
      fireEvent.click(screen.getByTestId('logout'));
      
      expect(screen.getByTestId('auth-status')).toHaveTextContent('not authenticated');
      expect(screen.getByTestId('user-email')).toHaveTextContent('No email');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
    });
  });

  describe('LLM Session Management', () => {
    it('should start LLM session', () => {
      renderWithContext7(<LLMSessionTestComponent />);
      
      expect(screen.getByTestId('current-session-id')).toHaveTextContent('No session');
      expect(screen.getByTestId('sessions-count')).toHaveTextContent('0');
      
      fireEvent.click(screen.getByTestId('start-session'));
      
      expect(screen.getByTestId('sessions-count')).toHaveTextContent('1');
      expect(screen.getByTestId('current-session-id')).not.toHaveTextContent('No session');
    });

    it('should end LLM session', () => {
      renderWithContext7(<LLMSessionTestComponent />);
      
      fireEvent.click(screen.getByTestId('start-session'));
      expect(screen.getByTestId('sessions-count')).toHaveTextContent('1');
      
      fireEvent.click(screen.getByTestId('end-session'));
      
      expect(screen.getByTestId('current-session-id')).toHaveTextContent('No session');
      expect(screen.getByTestId('sessions-count')).toHaveTextContent('1'); // Session still exists but not active
    });

    it('should add messages to LLM session', () => {
      renderWithContext7(<LLMSessionTestComponent />);
      
      fireEvent.click(screen.getByTestId('start-session'));
      expect(screen.getByTestId('messages-count')).toHaveTextContent('0');
      
      fireEvent.click(screen.getByTestId('add-message'));
      
      expect(screen.getByTestId('messages-count')).toHaveTextContent('1');
    });
  });

  describe('Error Handling', () => {
    it('should throw error when useContext7 is used outside provider', () => {
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      const TestComponentWithoutProvider = () => {
        try {
          useContext7();
          return <div>Should not render</div>;
        } catch (error) {
          return <div data-testid="error-caught">Error caught</div>;
        }
      };
      
      expect(() => render(<TestComponentWithoutProvider />)).toThrow();
      
      consoleSpy.mockRestore();
    });
  });

  describe('LocalStorage Integration', () => {
    it('should restore auth state from localStorage', () => {
      const mockUser = {
        id: 'test-user',
        name: 'Test User',
        email: 'test@example.com',
        roles: [],
      };
      
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'auth_token') return 'stored-token';
        if (key === 'user_data') return JSON.stringify(mockUser);
        return null;
      });
      
      renderWithContext7(<TestComponent />);
      
      expect(screen.getByTestId('authenticated')).toHaveTextContent('true');
      expect(screen.getByTestId('user-name')).toHaveTextContent('Test User');
    });

    it('should handle corrupted localStorage data', () => {
      mockLocalStorage.getItem.mockImplementation((key) => {
        if (key === 'auth_token') return 'stored-token';
        if (key === 'user_data') return 'invalid-json';
        return null;
      });
      
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});
      
      renderWithContext7(<TestComponent />);
      
      expect(screen.getByTestId('authenticated')).toHaveTextContent('false');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('auth_token');
      expect(mockLocalStorage.removeItem).toHaveBeenCalledWith('user_data');
      
      consoleSpy.mockRestore();
    });
  });

  describe('Performance', () => {
    it('should track performance metrics', async () => {
      const { rerender } = renderWithContext7(<TestComponent />);
      
      // Simulate performance monitoring
      act(() => {
        // Trigger performance update
        const event = new Event('load');
        window.dispatchEvent(event);
      });
      
      // Wait for useEffect to run
      await waitFor(() => {
        expect(performance.now).toHaveBeenCalled();
      });
    });
  });
});

describe('Context7 Specialized Hooks', () => {
  it('should provide auth-specific functionality', () => {
    const TestAuth = () => {
      const auth = useAuth();
      return (
        <div>
          <div data-testid="auth-authenticated">{auth.isAuthenticated ? 'true' : 'false'}</div>
          <div data-testid="auth-user">{auth.user?.name || 'No user'}</div>
        </div>
      );
    };
    
    renderWithContext7(<TestAuth />);
    
    expect(screen.getByTestId('auth-authenticated')).toHaveTextContent('false');
    expect(screen.getByTestId('auth-user')).toHaveTextContent('No user');
  });

  it('should provide LLM session-specific functionality', () => {
    const TestLLM = () => {
      const llm = useLLMSession();
      return (
        <div>
          <div data-testid="llm-current">{llm.currentSession?.id || 'No session'}</div>
          <div data-testid="llm-sessions">{llm.sessions.length}</div>
        </div>
      );
    };
    
    renderWithContext7(<TestLLM />);
    
    expect(screen.getByTestId('llm-current')).toHaveTextContent('No session');
    expect(screen.getByTestId('llm-sessions')).toHaveTextContent('0');
  });
});

describe('Context7 Integration', () => {
  it('should handle complex state interactions', () => {
    const ComplexTestComponent = () => {
      const { state, actions } = useContext7();
      
      const handleComplexAction = () => {
        actions.setLoading(true);
        actions.startLLMSession('gpt-4', 'openai');
        actions.toggleFeature('darkMode', true);
        actions.addNotification({
          type: 'success',
          title: 'Complex Action',
          message: 'Multiple state updates',
          persistent: false,
        });
      };
      
      return (
        <div>
          <div data-testid="complex-loading">{state.isLoading ? 'true' : 'false'}</div>
          <div data-testid="complex-dark">{state.features.darkMode ? 'true' : 'false'}</div>
          <div data-testid="complex-session">{state.currentLLMSession ? 'has-session' : 'no-session'}</div>
          <div data-testid="complex-notifications">{state.notifications.length}</div>
          <button onClick={handleComplexAction} data-testid="complex-action">
            Complex Action
          </button>
        </div>
      );
    };
    
    renderWithContext7(<ComplexTestComponent />);
    
    fireEvent.click(screen.getByTestId('complex-action'));
    
    expect(screen.getByTestId('complex-loading')).toHaveTextContent('true');
    expect(screen.getByTestId('complex-dark')).toHaveTextContent('true');
    expect(screen.getByTestId('complex-session')).toHaveTextContent('has-session');
    expect(screen.getByTestId('complex-notifications')).toHaveTextContent('1');
  });
}); 