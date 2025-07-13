/**
 * Main App Component - Enhanced with Context7 Central Provider
 * 
 * Entry point with unified Context7 state management.
 * Follows modern React patterns with TypeScript and TailwindCSS.
 */

import React, { Suspense, lazy, useEffect } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';

// Context7 Central Provider
import { Context7Provider, useContext7 } from './contexts/Context7Provider';

// Legacy context providers for gradual migration
import { PerformanceProvider } from './contexts/performance/PerformanceContext';
import { VKTeamsProvider } from './infrastructure/vkTeams/application/VKTeamsContext';

// Layout Components
import Layout from './components/Layout/Layout';
import LoadingSpinner from './components/UI/LoadingSpinner';
import ErrorBoundary from './components/ErrorBoundary/ErrorBoundary';

// Lazy loaded pages for performance
const Dashboard = lazy(() => import('./pages/Dashboard'));
const AIAnalysis = lazy(() => import('./pages/AIAnalysis'));
const Profile = lazy(() => import('./pages/Profile'));
const Settings = lazy(() => import('./pages/Settings'));
const Login = lazy(() => import('./pages/Login'));
const Register = lazy(() => import('./pages/Register'));
const NotFound = lazy(() => import('./pages/NotFound'));

// New enhanced pages
const CodeAnalysis = lazy(() => import('./pages/CodeAnalysis'));
const TemplateLibrary = lazy(() => import('./pages/TemplateLibrary'));
const UserStats = lazy(() => import('./pages/UserStats'));

// ============================================================================
// App Loading Component
// ============================================================================

const AppLoading: React.FC = () => {
  const { state } = useContext7();
  
  return (
    <div className={`min-h-screen ${state.features.darkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 flex items-center justify-center">
        <div className="text-center">
          <LoadingSpinner size="lg" />
          <p className="mt-4 text-gray-600 dark:text-gray-400">
            Loading AI Assistant...
          </p>
          {state.isLoading && (
            <p className="mt-2 text-sm text-gray-500 dark:text-gray-500">
              {state.error ? `Error: ${state.error}` : 'Initializing Context7...'}
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

// ============================================================================
// App Content Component (inside Context7)
// ============================================================================

const AppContent: React.FC = () => {
  const { state, actions } = useContext7();

  // Initialize app performance metrics
  useEffect(() => {
    const startTime = performance.now();
    
    const handleLoad = () => {
      const loadTime = performance.now() - startTime;
      actions.updatePerformance({ loadTime });
    };

    if (document.readyState === 'complete') {
      handleLoad();
    } else {
      window.addEventListener('load', handleLoad);
      return () => window.removeEventListener('load', handleLoad);
    }
  }, [actions]);

  // Load available LLM models on app start
  useEffect(() => {
    const loadModels = async () => {
      try {
        actions.setLoading(true);
        const response = await fetch('/api/v1/llm/models');
        if (response.ok) {
          const models = await response.json();
          actions.loadModels(models);
        }
      } catch (error) {
        console.error('Failed to load LLM models:', error);
        actions.setError('Failed to load LLM models');
      } finally {
        actions.setLoading(false);
      }
    };

    if (state.isAuthenticated) {
      loadModels();
    }
  }, [state.isAuthenticated, actions]);

  // Apply theme to document
  useEffect(() => {
    if (state.currentTheme === 'dark' || 
        (state.currentTheme === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [state.currentTheme]);

  // Update document language
  useEffect(() => {
    document.documentElement.lang = state.currentLanguage;
  }, [state.currentLanguage]);

  return (
    <div className={`min-h-screen ${state.features.darkMode ? 'dark' : ''}`}>
      <div className="min-h-screen bg-gray-50 dark:bg-gray-900 transition-colors duration-200">
        <Suspense fallback={<AppLoading />}>
          <Routes>
            {/* Auth Routes */}
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />
            
            {/* Protected Routes */}
            <Route path="/" element={<Layout />}>
              <Route index element={<Dashboard />} />
              <Route path="ai-analysis" element={<AIAnalysis />} />
              <Route path="code-analysis" element={<CodeAnalysis />} />
              <Route path="templates" element={<TemplateLibrary />} />
              <Route path="user-stats" element={<UserStats />} />
              <Route path="profile" element={<Profile />} />
              <Route path="settings" element={<Settings />} />
            </Route>
            
            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </Suspense>
        
        {/* Global UI Elements */}
        {state.error && (
          <div className="fixed top-4 right-4 z-50">
            <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded-lg shadow-lg">
              <div className="flex items-center justify-between">
                <span>{state.error}</span>
                <button
                  onClick={() => actions.setError(null)}
                  className="ml-2 text-red-500 hover:text-red-700"
                >
                  ×
                </button>
              </div>
            </div>
          </div>
        )}
        
        {/* Connection Status Indicator */}
        {state.metrics.connectionStatus !== 'connected' && (
          <div className="fixed bottom-4 left-4 z-50">
            <div className={`px-3 py-2 rounded-full text-sm font-medium ${
              state.metrics.connectionStatus === 'disconnected' 
                ? 'bg-red-100 text-red-800' 
                : 'bg-yellow-100 text-yellow-800'
            }`}>
              {state.metrics.connectionStatus === 'disconnected' ? '📶❌ Offline' : '📶⚠️ Reconnecting...'}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

// ============================================================================
// Main App Component
// ============================================================================

const App: React.FC = () => {
  return (
    <ErrorBoundary>
      <Context7Provider>
        <PerformanceProvider>
          <VKTeamsProvider apiUrl={process.env.REACT_APP_API_URL || 'http://localhost:8000'}>
            <Router>
              <AppContent />
            </Router>
          </VKTeamsProvider>
        </PerformanceProvider>
      </Context7Provider>
    </ErrorBoundary>
  );
};

export default App;
