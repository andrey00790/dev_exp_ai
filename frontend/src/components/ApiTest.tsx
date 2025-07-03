import React, { useState } from 'react';
import { chatApi } from '../api/chatApi';

interface TestResult {
  endpoint: string;
  status: 'pending' | 'success' | 'error';
  response?: any;
  error?: string;
  duration?: number;
}

export default function ApiTest() {
  const [results, setResults] = useState<TestResult[]>([]);
  const [isRunning, setIsRunning] = useState(false);

  const updateResult = (endpoint: string, update: Partial<TestResult>) => {
    setResults(prev => prev.map(r => 
      r.endpoint === endpoint ? { ...r, ...update } : r
    ));
  };

  const runTest = async (endpoint: string, testFn: () => Promise<any>) => {
    const startTime = Date.now();
    updateResult(endpoint, { status: 'pending' });
    
    try {
      const response = await testFn();
      const duration = Date.now() - startTime;
      updateResult(endpoint, { 
        status: 'success', 
        response, 
        duration 
      });
    } catch (error) {
      const duration = Date.now() - startTime;
      updateResult(endpoint, { 
        status: 'error', 
        error: error instanceof Error ? error.message : 'Unknown error',
        duration 
      });
    }
  };

  const runAllTests = async () => {
    setIsRunning(true);
    setResults([
      { endpoint: 'Health Check', status: 'pending' },
      { endpoint: 'Demo Users', status: 'pending' },
      { endpoint: 'Authentication', status: 'pending' },
      { endpoint: 'Vector Search', status: 'pending' },
      { endpoint: 'RFC Generation', status: 'pending' },
    ]);

    // Health Check
    await runTest('Health Check', () => chatApi.healthCheck());

    // Demo Users
    await runTest('Demo Users', () => chatApi.getDemoUsers());

    // Authentication
    await runTest('Authentication', async () => {
      const response = await chatApi.login('admin@example.com', 'admin123');
      // Store token for subsequent requests
      if (response.access_token) {
        localStorage.setItem('token', response.access_token);
      }
      return response;
    });

    // Vector Search
    await runTest('Vector Search', () => chatApi.search('test query'));

    // RFC Generation
    await runTest('RFC Generation', () => 
      chatApi.generateRFC('Create a user authentication system with OAuth 2.0 support', 'new_feature')
    );

    setIsRunning(false);
  };

  const getStatusColor = (status: TestResult['status']) => {
    switch (status) {
      case 'pending': return 'text-yellow-600 bg-yellow-50';
      case 'success': return 'text-green-600 bg-green-50';
      case 'error': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  const getStatusIcon = (status: TestResult['status']) => {
    switch (status) {
      case 'pending': return '⏳';
      case 'success': return '✅';
      case 'error': return '❌';
      default: return '⚪';
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="px-6 py-4 border-b border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900">API Integration Tests</h2>
          <p className="text-gray-600 mt-1">Test all API endpoints to ensure proper integration</p>
        </div>

        <div className="p-6">
          <button
            onClick={runAllTests}
            disabled={isRunning}
            className="mb-6 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white px-6 py-2 rounded-lg font-medium transition-colors"
          >
            {isRunning ? 'Running Tests...' : 'Run All Tests'}
          </button>

          <div className="space-y-4">
            {results.map((result, index) => (
              <div key={index} className="border border-gray-200 rounded-lg p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center space-x-3">
                    <span className="text-xl">{getStatusIcon(result.status)}</span>
                    <h3 className="font-medium text-gray-900">{result.endpoint}</h3>
                  </div>
                  <div className="flex items-center space-x-2">
                    {result.duration && (
                      <span className="text-sm text-gray-500">{result.duration}ms</span>
                    )}
                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${getStatusColor(result.status)}`}>
                      {result.status.toUpperCase()}
                    </span>
                  </div>
                </div>

                {result.error && (
                  <div className="mt-2 p-3 bg-red-50 border border-red-200 rounded">
                    <p className="text-sm text-red-600 font-medium">Error:</p>
                    <p className="text-sm text-red-600">{result.error}</p>
                  </div>
                )}

                {result.response && (
                  <div className="mt-2">
                    <details className="cursor-pointer">
                      <summary className="text-sm font-medium text-gray-700 hover:text-gray-900">
                        View Response
                      </summary>
                      <pre className="mt-2 p-3 bg-gray-50 border border-gray-200 rounded text-xs overflow-x-auto">
                        {JSON.stringify(result.response, null, 2)}
                      </pre>
                    </details>
                  </div>
                )}
              </div>
            ))}
          </div>

          {results.length > 0 && (
            <div className="mt-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
              <h4 className="font-medium text-blue-900 mb-2">Test Summary</h4>
              <div className="grid grid-cols-3 gap-4 text-sm">
                <div>
                  <span className="text-green-600 font-medium">
                    ✅ Passed: {results.filter(r => r.status === 'success').length}
                  </span>
                </div>
                <div>
                  <span className="text-red-600 font-medium">
                    ❌ Failed: {results.filter(r => r.status === 'error').length}
                  </span>
                </div>
                <div>
                  <span className="text-yellow-600 font-medium">
                    ⏳ Pending: {results.filter(r => r.status === 'pending').length}
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 