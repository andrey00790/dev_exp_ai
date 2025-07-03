import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';

interface LoginProps {
  onLogin: (token: string, user: any) => void;
}

interface LoginFormData {
  email: string;
  password: string;
}

const Login: React.FC<LoginProps> = ({ onLogin }) => {
  const [formData, setFormData] = useState<LoginFormData>({
    email: '',
    password: ''
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [showDemo, setShowDemo] = useState(false);
  const navigate = useNavigate();

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
    setError(null);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(formData),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Login failed');
      }

      const data = await response.json();
      
      // Store token in localStorage
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      
      // Call parent component's onLogin
      onLogin(data.access_token, data.user);
      
      navigate('/');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleDemoLogin = async (email: string, password: string) => {
    setFormData({ email, password });
    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch('/auth/login', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ email, password }),
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || 'Demo login failed');
      }

      const data = await response.json();
      
      localStorage.setItem('auth_token', data.access_token);
      localStorage.setItem('user_info', JSON.stringify(data.user));
      
      onLogin(data.access_token, data.user);
      navigate('/');
      
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Demo login failed');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
            AI Assistant Login
          </h2>
          <p className="mt-2 text-center text-sm text-gray-600">
            Secure access to your AI-powered development assistant
          </p>
        </div>
        
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email" className="sr-only">
                Email address
              </label>
              <input
                id="email"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={formData.email}
                onChange={handleInputChange}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-t-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Email address"
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                value={formData.password}
                onChange={handleInputChange}
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-gray-300 placeholder-gray-500 text-gray-900 rounded-b-md focus:outline-none focus:ring-indigo-500 focus:border-indigo-500 focus:z-10 sm:text-sm"
                placeholder="Password"
              />
            </div>
          </div>

          {error && (
            <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded">
              {error}
            </div>
          )}

          <div>
            <button
              type="submit"
              disabled={isLoading}
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isLoading ? (
                <svg className="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4"></circle>
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                </svg>
              ) : null}
              Sign in
            </button>
          </div>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setShowDemo(!showDemo)}
              className="text-indigo-600 hover:text-indigo-500 text-sm"
            >
              {showDemo ? 'Hide' : 'Show'} Demo Accounts
            </button>
          </div>

          {showDemo && (
            <div className="bg-blue-50 border border-blue-300 rounded p-4">
              <h4 className="text-sm font-medium text-blue-800 mb-2">Demo Accounts:</h4>
              <div className="space-y-2">
                <button
                  type="button"
                  onClick={() => handleDemoLogin('admin@example.com', 'admin123')}
                  disabled={isLoading}
                  className="w-full text-left text-sm text-blue-700 hover:text-blue-900 bg-blue-100 hover:bg-blue-200 px-3 py-2 rounded disabled:opacity-50"
                >
                  🔒 Admin User (admin@example.com / admin123)
                  <br />
                  <span className="text-xs text-blue-600">Full access including admin functions</span>
                </button>
                <button
                  type="button"
                  onClick={() => handleDemoLogin('user@example.com', 'user123')}
                  disabled={isLoading}
                  className="w-full text-left text-sm text-blue-700 hover:text-blue-900 bg-blue-100 hover:bg-blue-200 px-3 py-2 rounded disabled:opacity-50"
                >
                  👤 Regular User (user@example.com / user123)
                  <br />
                  <span className="text-xs text-blue-600">Standard search and generation access</span>
                </button>
              </div>
            </div>
          )}
        </form>

        <div className="text-center text-xs text-gray-500">
          <p>🔐 Secure JWT Authentication</p>
          <p>⚡ Rate Limited: 5 attempts per minute</p>
          <p>💰 Budget Control: Cost tracking enabled</p>
        </div>
      </div>
    </div>
  );
};

export default Login;
