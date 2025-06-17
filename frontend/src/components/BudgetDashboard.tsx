import React, { useState, useEffect } from 'react';
import { useAuth } from '../contexts/AuthContext';
import ApiClient from '../utils/api';

interface BudgetStatus {
  user_id: string;
  email: string;
  current_usage: number;
  budget_limit: number;
  remaining_budget: number;
  usage_percentage: number;
  budget_status: string;
}

const BudgetDashboard: React.FC = () => {
  const { user } = useAuth();
  const [budgetStatus, setBudgetStatus] = useState<BudgetStatus | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchBudgetStatus();
  }, []);

  const fetchBudgetStatus = async () => {
    try {
      setLoading(true);
      const response = await ApiClient.get('/api/v1/budget/status');
      
      if (response.ok) {
        const data = await response.json();
        setBudgetStatus(data);
      } else {
        throw new Error('Failed to fetch budget status');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Unknown error');
    } finally {
      setLoading(false);
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'EXCEEDED':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'CRITICAL':
        return 'text-red-500 bg-red-50 border-red-200';
      case 'WARNING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      default:
        return 'text-green-600 bg-green-50 border-green-200';
    }
  };

  const getProgressBarColor = (percentage: number) => {
    if (percentage >= 100) return 'bg-red-500';
    if (percentage >= 95) return 'bg-red-400';
    if (percentage >= 80) return 'bg-yellow-400';
    return 'bg-green-500';
  };

  if (loading) {
    return (
      <div className="animate-pulse">
        <div className="h-4 bg-gray-200 rounded w-1/4 mb-4"></div>
        <div className="space-y-3">
          <div className="h-4 bg-gray-200 rounded"></div>
          <div className="h-4 bg-gray-200 rounded w-5/6"></div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-red-50 border border-red-200 rounded-lg p-4">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-red-800">Error Loading Budget</h3>
            <p className="text-sm text-red-700 mt-1">{error}</p>
            <button
              onClick={fetchBudgetStatus}
              className="mt-2 text-sm text-red-800 underline hover:text-red-900"
            >
              Try again
            </button>
          </div>
        </div>
      </div>
    );
  }

  if (!budgetStatus) {
    return (
      <div className="text-center py-4">
        <p className="text-gray-500">No budget information available</p>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Budget Overview Card */}
      <div className="bg-white shadow rounded-lg p-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-medium text-gray-900">Budget Overview</h3>
          <span className={`px-3 py-1 rounded-full text-sm font-medium border ${getStatusColor(budgetStatus.budget_status)}`}>
            {budgetStatus.budget_status}
          </span>
        </div>

        {/* Progress Bar */}
        <div className="mb-4">
          <div className="flex justify-between text-sm text-gray-600 mb-2">
            <span>Usage Progress</span>
            <span>{budgetStatus.usage_percentage.toFixed(1)}%</span>
          </div>
          <div className="w-full bg-gray-200 rounded-full h-2">
            <div
              className={`h-2 rounded-full transition-all duration-300 ${getProgressBarColor(budgetStatus.usage_percentage)}`}
              style={{ width: `${Math.min(budgetStatus.usage_percentage, 100)}%` }}
            ></div>
          </div>
        </div>

        {/* Budget Stats Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${budgetStatus.current_usage.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">Used</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-gray-900">
              ${budgetStatus.budget_limit.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">Total Budget</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-green-600">
              ${budgetStatus.remaining_budget.toFixed(2)}
            </div>
            <div className="text-sm text-gray-500">Remaining</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {budgetStatus.usage_percentage.toFixed(1)}%
            </div>
            <div className="text-sm text-gray-500">Used</div>
          </div>
        </div>
      </div>

      {/* Budget Alerts */}
      {budgetStatus.usage_percentage >= 80 && (
        <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-4">
          <div className="flex">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-yellow-800">
                Budget Alert
              </h3>
              <p className="text-sm text-yellow-700 mt-1">
                {budgetStatus.usage_percentage >= 100
                  ? 'Your budget has been exceeded. Future AI operations may be blocked.'
                  : budgetStatus.usage_percentage >= 95
                  ? 'You are approaching your budget limit. Consider monitoring your usage closely.'
                  : 'You have used over 80% of your budget. Consider reviewing your usage patterns.'}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Budget Tools */}
      <div className="bg-white shadow rounded-lg p-6">
        <h3 className="text-lg font-medium text-gray-900 mb-4">Budget Tools</h3>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          <button
            onClick={fetchBudgetStatus}
            className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
          >
            Refresh Status
          </button>
          
          <button
            className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            disabled
          >
            Usage History
          </button>
          
          <button
            className="flex items-center justify-center px-4 py-2 border border-gray-300 rounded-md shadow-sm text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
            disabled
          >
            Set Alerts
          </button>
        </div>
      </div>

      {/* User Info */}
      <div className="text-sm text-gray-500 text-center">
        Budget information for {budgetStatus.email} • Last updated: {new Date().toLocaleTimeString()}
      </div>
    </div>
  );
};

export default BudgetDashboard; 