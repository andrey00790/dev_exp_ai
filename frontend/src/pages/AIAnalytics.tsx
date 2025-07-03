import React, { useState, useEffect } from 'react';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement,
} from 'chart.js';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend,
  ArcElement
);

interface DashboardAnalytics {
  summary: {
    total_requests: number;
    active_models: number;
    active_users: number;
    data_points_collected: number;
  };
  performance_metrics: Record<string, {
    avg: number;
    min: number;
    max: number;
    std: number;
    count: number;
  }>;
  model_usage: Record<string, number>;
  user_activity_distribution: {
    heavy_users: number;
    regular_users: number;
    light_users: number;
  };
  top_insights: string[];
  last_updated: string;
}

interface TrendAnalysis {
  metric_type: string;
  trend_direction: string;
  trend_strength: number;
  change_percent: number;
  confidence: number;
  forecast_points: Array<{
    timestamp: string;
    value: number;
    confidence: number;
  }>;
  insights: string[];
  analysis_timestamp: string;
}

interface UsagePattern {
  pattern_id: string;
  pattern_type: string;
  frequency: number;
  peak_hours: number[];
  model_preferences: Record<string, number>;
  user_segments: Record<string, number>;
  seasonal_trends: Record<string, number>;
  recommendations: string[];
  analysis_timestamp: string;
}

interface CostInsight {
  insight_id: string;
  cost_driver: string;
  current_cost: number;
  potential_savings: number;
  savings_percent: number;
  optimization_actions: string[];
  impact_level: string;
  implementation_effort: string;
}

const AIAnalytics: React.FC = () => {
  const [dashboardData, setDashboardData] = useState<DashboardAnalytics | null>(null);
  const [trends, setTrends] = useState<TrendAnalysis[]>([]);
  const [usagePatterns, setUsagePatterns] = useState<UsagePattern[]>([]);
  const [costInsights, setCostInsights] = useState<CostInsight[]>([]);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [selectedMetric, setSelectedMetric] = useState('latency');
  const [selectedModel, setSelectedModel] = useState('');
  const [timeRange, setTimeRange] = useState(30);

  const metricTypes = [
    { value: 'latency', label: 'Latency' },
    { value: 'accuracy', label: 'Accuracy' },
    { value: 'cost', label: 'Cost' },
    { value: 'throughput', label: 'Throughput' },
    { value: 'quality_score', label: 'Quality Score' },
    { value: 'error_rate', label: 'Error Rate' }
  ];

  const modelTypes = [
    { value: '', label: 'All Models' },
    { value: 'code_review', label: 'Code Review' },
    { value: 'semantic_search', label: 'Semantic Search' },
    { value: 'rfc_generation', label: 'RFC Generation' },
    { value: 'multimodal_search', label: 'Multimodal Search' }
  ];

  // Load dashboard data
  const loadDashboardData = async () => {
    try {
      const response = await fetch('/api/v1/ai-analytics/dashboard', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDashboardData(data);
      }
    } catch (error) {
      console.error('Failed to load dashboard data:', error);
    }
  };

  // Analyze trends
  const analyzeTrends = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai-analytics/trends', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          metric_type: selectedMetric,
          model_type: selectedModel || undefined,
          time_range_days: timeRange
        })
      });

      if (response.ok) {
        const trendData = await response.json();
        setTrends([trendData]);
      }
    } catch (error) {
      console.error('Failed to analyze trends:', error);
    } finally {
      setLoading(false);
    }
  };

  // Load usage patterns
  const loadUsagePatterns = async () => {
    try {
      const response = await fetch(`/api/v1/ai-analytics/usage-patterns?time_range_days=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setUsagePatterns(data.patterns);
      }
    } catch (error) {
      console.error('Failed to load usage patterns:', error);
    }
  };

  // Load cost insights
  const loadCostInsights = async () => {
    try {
      const response = await fetch('/api/v1/ai-analytics/cost-insights', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setCostInsights(data.insights);
      }
    } catch (error) {
      console.error('Failed to load cost insights:', error);
    }
  };

  useEffect(() => {
    loadDashboardData();
    loadUsagePatterns();
    loadCostInsights();
  }, [timeRange]);

  // Chart configurations
  const createLineChartData = (trend: TrendAnalysis) => {
    return {
      labels: trend.forecast_points.map(point => 
        new Date(point.timestamp).toLocaleDateString()
      ),
      datasets: [
        {
          label: `${trend.metric_type} Forecast`,
          data: trend.forecast_points.map(point => point.value),
          borderColor: 'rgb(75, 192, 192)',
          backgroundColor: 'rgba(75, 192, 192, 0.2)',
          tension: 0.1
        }
      ]
    };
  };

  const createModelUsageChart = () => {
    if (!dashboardData) return null;

    return {
      labels: Object.keys(dashboardData.model_usage),
      datasets: [
        {
          data: Object.values(dashboardData.model_usage),
          backgroundColor: [
            '#FF6384',
            '#36A2EB',
            '#FFCE56',
            '#4BC0C0',
            '#9966FF',
            '#FF9F40'
          ]
        }
      ]
    };
  };

  const createUserActivityChart = () => {
    if (!dashboardData) return null;

    return {
      labels: ['Heavy Users', 'Regular Users', 'Light Users'],
      datasets: [
        {
          data: [
            dashboardData.user_activity_distribution.heavy_users,
            dashboardData.user_activity_distribution.regular_users,
            dashboardData.user_activity_distribution.light_users
          ],
          backgroundColor: ['#FF6384', '#36A2EB', '#FFCE56']
        }
      ]
    };
  };

  const getTrendIcon = (direction: string) => {
    switch (direction) {
      case 'increasing':
        return '📈';
      case 'decreasing':
        return '📉';
      case 'stable':
        return '➡️';
      default:
        return '❓';
    }
  };

  const getTrendColor = (direction: string, metricType: string) => {
    const isGoodMetric = ['accuracy', 'quality_score', 'throughput', 'user_satisfaction'].includes(metricType);
    
    if (direction === 'increasing') {
      return isGoodMetric ? 'text-green-600' : 'text-red-600';
    } else if (direction === 'decreasing') {
      return isGoodMetric ? 'text-red-600' : 'text-green-600';
    }
    return 'text-gray-600';
  };

  const getImpactColor = (level: string) => {
    switch (level) {
      case 'high':
        return 'bg-red-100 text-red-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getEffortColor = (effort: string) => {
    switch (effort) {
      case 'easy':
        return 'bg-green-100 text-green-800';
      case 'moderate':
        return 'bg-yellow-100 text-yellow-800';
      case 'complex':
        return 'bg-red-100 text-red-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  return (
    <div className="p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Analytics</h1>
        <p className="text-gray-600">Advanced analytics, predictive modeling, and performance insights</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['dashboard', 'trends', 'patterns', 'costs'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`py-2 px-1 border-b-2 font-medium text-sm ${
                activeTab === tab
                  ? 'border-blue-500 text-blue-600'
                  : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
              }`}
            >
              {tab.charAt(0).toUpperCase() + tab.slice(1)}
            </button>
          ))}
        </nav>
      </div>

      {/* Dashboard Tab */}
      {activeTab === 'dashboard' && (
        <div className="space-y-6">
          {/* Summary Cards */}
          {dashboardData && (
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Total Requests</h3>
                <p className="text-3xl font-bold text-blue-600">{dashboardData.summary.total_requests.toLocaleString()}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Active Models</h3>
                <p className="text-3xl font-bold text-green-600">{dashboardData.summary.active_models}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Active Users</h3>
                <p className="text-3xl font-bold text-purple-600">{dashboardData.summary.active_users}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Data Points</h3>
                <p className="text-3xl font-bold text-orange-600">{dashboardData.summary.data_points_collected.toLocaleString()}</p>
              </div>
            </div>
          )}

          {/* Charts */}
          <div className="grid grid-cols-2 gap-6">
            {/* Model Usage Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Model Usage Distribution</h3>
              {dashboardData && createModelUsageChart() && (
                <Pie data={createModelUsageChart()!} />
              )}
            </div>

            {/* User Activity Chart */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">User Activity Distribution</h3>
              {dashboardData && createUserActivityChart() && (
                <Doughnut data={createUserActivityChart()!} />
              )}
            </div>
          </div>

          {/* Performance Metrics */}
          {dashboardData && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Performance Metrics Overview</h3>
              <div className="grid grid-cols-3 gap-4">
                {Object.entries(dashboardData.performance_metrics).map(([metric, data]) => (
                  <div key={metric} className="p-4 bg-gray-50 rounded">
                    <h4 className="font-medium text-gray-700">{metric.replace('_', ' ').toUpperCase()}</h4>
                    <div className="mt-2 space-y-1">
                      <p className="text-sm text-gray-600">Avg: <span className="font-medium">{data.avg.toFixed(2)}</span></p>
                      <p className="text-sm text-gray-600">Min: <span className="font-medium">{data.min.toFixed(2)}</span></p>
                      <p className="text-sm text-gray-600">Max: <span className="font-medium">{data.max.toFixed(2)}</span></p>
                      <p className="text-sm text-gray-600">Count: <span className="font-medium">{data.count}</span></p>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Top Insights */}
          {dashboardData && dashboardData.top_insights.length > 0 && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Top Insights</h3>
              <ul className="space-y-2">
                {dashboardData.top_insights.map((insight, index) => (
                  <li key={index} className="flex items-start">
                    <span className="text-blue-500 mr-2">💡</span>
                    <span className="text-gray-700">{insight}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* Trends Tab */}
      {activeTab === 'trends' && (
        <div className="space-y-6">
          {/* Trend Analysis Controls */}
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Trend Analysis</h2>
            
            <div className="grid grid-cols-4 gap-4 mb-6">
              <div>
                <label className="block text-sm font-medium mb-2">Metric Type</label>
                <select
                  value={selectedMetric}
                  onChange={(e) => setSelectedMetric(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  {metricTypes.map((metric) => (
                    <option key={metric.value} value={metric.value}>
                      {metric.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Model Type</label>
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  {modelTypes.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium mb-2">Time Range (days)</label>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(Number(e.target.value))}
                  className="w-full p-2 border rounded-md"
                >
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                  <option value={60}>60 days</option>
                  <option value={90}>90 days</option>
                </select>
              </div>
              
              <div className="flex items-end">
                <button
                  onClick={analyzeTrends}
                  disabled={loading}
                  className="w-full px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
                >
                  {loading ? 'Analyzing...' : 'Analyze Trends'}
                </button>
              </div>
            </div>

            {/* Trend Results */}
            {trends.map((trend, index) => (
              <div key={index} className="space-y-4">
                {/* Trend Summary */}
                <div className="flex items-center justify-between p-4 bg-gray-50 rounded">
                  <div className="flex items-center space-x-4">
                    <span className="text-2xl">{getTrendIcon(trend.trend_direction)}</span>
                    <div>
                      <h3 className="font-medium">{trend.metric_type.replace('_', ' ').toUpperCase()} Trend</h3>
                      <p className={`text-sm ${getTrendColor(trend.trend_direction, trend.metric_type)}`}>
                        {trend.trend_direction.toUpperCase()} by {Math.abs(trend.change_percent).toFixed(1)}%
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="text-sm text-gray-600">Confidence</p>
                    <p className="font-medium">{(trend.confidence * 100).toFixed(1)}%</p>
                  </div>
                </div>

                {/* Forecast Chart */}
                {trend.forecast_points.length > 0 && (
                  <div className="p-4 bg-white border rounded">
                    <h4 className="font-medium mb-4">Forecast</h4>
                    <Line data={createLineChartData(trend)} />
                  </div>
                )}

                {/* Insights */}
                {trend.insights.length > 0 && (
                  <div className="p-4 bg-white border rounded">
                    <h4 className="font-medium mb-2">Insights</h4>
                    <ul className="space-y-1">
                      {trend.insights.map((insight, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          {insight}
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Usage Patterns Tab */}
      {activeTab === 'patterns' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Usage Patterns</h2>
              <div className="flex items-center space-x-2">
                <label className="text-sm font-medium">Time Range:</label>
                <select
                  value={timeRange}
                  onChange={(e) => setTimeRange(Number(e.target.value))}
                  className="p-2 border rounded-md"
                >
                  <option value={7}>7 days</option>
                  <option value={14}>14 days</option>
                  <option value={30}>30 days</option>
                  <option value={60}>60 days</option>
                </select>
              </div>
            </div>

            {usagePatterns.map((pattern, index) => (
              <div key={pattern.pattern_id} className="space-y-6 border-t pt-6 first:border-t-0 first:pt-0">
                {/* Pattern Overview */}
                <div className="grid grid-cols-3 gap-4">
                  <div className="p-4 bg-blue-50 rounded">
                    <h3 className="font-medium text-blue-900">Total Usage</h3>
                    <p className="text-2xl font-bold text-blue-600">{pattern.frequency.toLocaleString()}</p>
                    <p className="text-sm text-blue-700">requests</p>
                  </div>
                  <div className="p-4 bg-green-50 rounded">
                    <h3 className="font-medium text-green-900">Peak Hours</h3>
                    <p className="text-lg font-bold text-green-600">
                      {pattern.peak_hours.map(h => `${h}:00`).join(', ')}
                    </p>
                  </div>
                  <div className="p-4 bg-purple-50 rounded">
                    <h3 className="font-medium text-purple-900">Top Model</h3>
                    <p className="text-lg font-bold text-purple-600">
                      {Object.entries(pattern.model_preferences).sort((a, b) => b[1] - a[1])[0]?.[0] || 'N/A'}
                    </p>
                  </div>
                </div>

                {/* Model Preferences */}
                <div>
                  <h4 className="font-medium mb-3">Model Preferences</h4>
                  <div className="space-y-2">
                    {Object.entries(pattern.model_preferences)
                      .sort((a, b) => b[1] - a[1])
                      .map(([model, preference]) => (
                        <div key={model} className="flex items-center justify-between">
                          <span className="text-sm font-medium">{model.replace('_', ' ').toUpperCase()}</span>
                          <div className="flex items-center space-x-2">
                            <div className="w-32 bg-gray-200 rounded-full h-2">
                              <div
                                className="bg-blue-600 h-2 rounded-full"
                                style={{ width: `${preference * 100}%` }}
                              ></div>
                            </div>
                            <span className="text-sm text-gray-600">{(preference * 100).toFixed(1)}%</span>
                          </div>
                        </div>
                      ))}
                  </div>
                </div>

                {/* User Segments */}
                <div>
                  <h4 className="font-medium mb-3">User Segments</h4>
                  <div className="grid grid-cols-3 gap-4">
                    {Object.entries(pattern.user_segments).map(([segment, count]) => (
                      <div key={segment} className="p-3 bg-gray-50 rounded text-center">
                        <p className="text-sm font-medium text-gray-700">{segment.replace('_', ' ').toUpperCase()}</p>
                        <p className="text-xl font-bold text-gray-900">{count}</p>
                      </div>
                    ))}
                  </div>
                </div>

                {/* Recommendations */}
                {pattern.recommendations.length > 0 && (
                  <div>
                    <h4 className="font-medium mb-3">Recommendations</h4>
                    <ul className="space-y-2">
                      {pattern.recommendations.map((rec, idx) => (
                        <li key={idx} className="flex items-start">
                          <span className="text-green-500 mr-2">✓</span>
                          <span className="text-sm text-gray-700">{rec}</span>
                        </li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Cost Insights Tab */}
      {activeTab === 'costs' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-xl font-semibold">Cost Optimization Insights</h2>
              <button
                onClick={loadCostInsights}
                className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700"
              >
                Refresh Insights
              </button>
            </div>

            {/* Cost Summary */}
            {costInsights.length > 0 && (
              <div className="grid grid-cols-3 gap-4 mb-6">
                <div className="p-4 bg-red-50 rounded">
                  <h3 className="font-medium text-red-900">Total Potential Savings</h3>
                  <p className="text-2xl font-bold text-red-600">
                    ${costInsights.reduce((sum, insight) => sum + insight.potential_savings, 0).toFixed(3)}
                  </p>
                </div>
                <div className="p-4 bg-orange-50 rounded">
                  <h3 className="font-medium text-orange-900">High Impact Insights</h3>
                  <p className="text-2xl font-bold text-orange-600">
                    {costInsights.filter(i => i.impact_level === 'high').length}
                  </p>
                </div>
                <div className="p-4 bg-green-50 rounded">
                  <h3 className="font-medium text-green-900">Easy Wins</h3>
                  <p className="text-2xl font-bold text-green-600">
                    {costInsights.filter(i => i.implementation_effort === 'easy').length}
                  </p>
                </div>
              </div>
            )}

            {/* Cost Insights List */}
            <div className="space-y-4">
              {costInsights.map((insight) => (
                <div key={insight.insight_id} className="p-4 border rounded-lg">
                  <div className="flex justify-between items-start mb-3">
                    <div>
                      <h3 className="font-medium text-gray-900">{insight.cost_driver}</h3>
                      <p className="text-sm text-gray-600">Current cost: ${insight.current_cost.toFixed(3)} per request</p>
                    </div>
                    <div className="flex space-x-2">
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getImpactColor(insight.impact_level)}`}>
                        {insight.impact_level.toUpperCase()} IMPACT
                      </span>
                      <span className={`px-2 py-1 text-xs font-medium rounded ${getEffortColor(insight.implementation_effort)}`}>
                        {insight.implementation_effort.toUpperCase()}
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4 mb-4">
                    <div className="p-3 bg-green-50 rounded">
                      <p className="text-sm font-medium text-green-900">Potential Savings</p>
                      <p className="text-lg font-bold text-green-600">
                        ${insight.potential_savings.toFixed(3)} ({insight.savings_percent.toFixed(1)}%)
                      </p>
                    </div>
                    <div className="p-3 bg-blue-50 rounded">
                      <p className="text-sm font-medium text-blue-900">Implementation</p>
                      <p className="text-lg font-bold text-blue-600">{insight.implementation_effort}</p>
                    </div>
                  </div>

                  <div>
                    <h4 className="font-medium mb-2">Optimization Actions</h4>
                    <ul className="space-y-1">
                      {insight.optimization_actions.map((action, idx) => (
                        <li key={idx} className="text-sm text-gray-700 flex items-start">
                          <span className="text-blue-500 mr-2">•</span>
                          {action}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              ))}
            </div>

            {costInsights.length === 0 && (
              <div className="text-center py-8">
                <p className="text-gray-500">No cost insights available. Data is being analyzed...</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIAnalytics; 