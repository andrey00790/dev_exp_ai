import React from 'react';
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { Toaster } from 'react-hot-toast';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './components/Auth/Login';
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import Search from './pages/Search';
import Generate from './pages/Generate';
import CodeDocumentation from './pages/CodeDocumentation';
import Settings from './pages/Settings';
import Monitoring from './pages/Monitoring';
import Analytics from './pages/Analytics';
import Chat from './pages/Chat';
import VectorSearchPage from './pages/VectorSearch';
import LLMOperationsPage from './pages/LLMOperations';
import AdvancedAI from './pages/AdvancedAI';
import AIOptimization from './pages/AIOptimization';
import AIAnalytics from './pages/AIAnalytics';
import RealtimeMonitoring from './pages/RealtimeMonitoring';
import DataSourcesManagement from './pages/DataSourcesManagement';
import ApiTest from './components/ApiTest';
import RFCDemo from './components/RFCDemo';
import EnhancedRFCGenerator from './components/EnhancedRFCGenerator';

// Create a client
const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      retry: 1,
      refetchOnWindowFocus: false,
    },
  },
});

// Protected Route Component
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// App Routes Component
const AppRoutes: React.FC = () => {
  const { isAuthenticated, loading, login } = useAuth();

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-indigo-600"></div>
      </div>
    );
  }

  return (
    <Routes>
      <Route 
        path="/login" 
        element={
          isAuthenticated ? (
            <Navigate to="/" replace />
          ) : (
            <Login onLogin={login} />
          )
        } 
      />
      <Route
        path="/*"
        element={
          <ProtectedRoute>
            <Layout>
              <Routes>
                <Route path="/" element={<Dashboard />} />
                <Route path="/vector-search" element={<VectorSearchPage />} />
                <Route path="/llm-operations" element={<LLMOperationsPage />} />
                <Route path="/advanced-ai" element={<AdvancedAI />} />
                <Route path="/ai-optimization" element={<AIOptimization />} />
                <Route path="/ai-analytics" element={<AIAnalytics />} />
                <Route path="/realtime-monitoring" element={<RealtimeMonitoring />} />
                <Route path="/data-sources" element={<DataSourcesManagement />} />
                <Route path="/search" element={<Search />} />
                <Route path="/generate" element={<Generate />} />
                <Route path="/enhanced-rfc" element={<EnhancedRFCGenerator />} />
                <Route path="/chat" element={<Chat />} />
                <Route path="/code-docs" element={<CodeDocumentation />} />
                <Route path="/analytics" element={<Analytics />} />
                <Route path="/settings" element={<Settings />} />
                <Route path="/monitoring" element={<Monitoring />} />
                <Route path="/api-test" element={<ApiTest />} />
                <Route path="/rfc-demo" element={<RFCDemo />} />
              </Routes>
            </Layout>
          </ProtectedRoute>
        }
      />
    </Routes>
  );
};

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Router>
          <AppRoutes />
          <Toaster position="top-right" />
        </Router>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default App;
