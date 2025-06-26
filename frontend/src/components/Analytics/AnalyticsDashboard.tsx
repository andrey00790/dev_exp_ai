import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Tabs,
  Tab,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Button,
  Alert,
  CircularProgress,
  Chip,
  Stack
} from '@mui/material';
import {
  TrendingUp,
  AttachMoney,
  Speed,
  People,
  Timeline,
  Assessment,
  Warning,
  CheckCircle
} from '@mui/icons-material';
import { Line, Bar, Pie } from 'react-chartjs-2';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
} from 'chart.js';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

interface MetricCard {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'positive' | 'negative' | 'neutral';
  icon: React.ReactNode;
  color: string;
}

interface DashboardData {
  usage_data?: any[];
  cost_data?: any[];
  performance_data?: any[];
  top_features?: any[];
  usage_trends?: any[];
  cost_trends?: any[];
  optimization_opportunities?: any[];
  insights?: any[];
  generated_at?: string;
}

interface AnalyticsDashboardProps {
  userId?: number;
  isAdmin?: boolean;
}

const AnalyticsDashboard: React.FC<AnalyticsDashboardProps> = ({ userId, isAdmin = false }) => {
  const [activeTab, setActiveTab] = useState(0);
  const [timeRange, setTimeRange] = useState('last_7_days');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [dashboardData, setDashboardData] = useState<DashboardData>({});

  // Chart theme colors
  const chartColors = {
    primary: '#1976d2',
    secondary: '#dc004e',
    success: '#2e7d32',
    warning: '#ed6c02',
    info: '#0288d1',
    gradients: {
      blue: ['rgba(25, 118, 210, 0.8)', 'rgba(25, 118, 210, 0.1)'],
      green: ['rgba(46, 125, 50, 0.8)', 'rgba(46, 125, 50, 0.1)'],
      orange: ['rgba(237, 108, 2, 0.8)', 'rgba(237, 108, 2, 0.1)']
    }
  };

  useEffect(() => {
    loadDashboardData();
  }, [activeTab, timeRange, userId]);

  const loadDashboardData = async () => {
    setLoading(true);
    setError(null);

    try {
      const endpoints = [
        { tab: 0, endpoint: '/api/v1/analytics/dashboard/usage' },
        { tab: 1, endpoint: '/api/v1/analytics/dashboard/cost' },
        { tab: 2, endpoint: '/api/v1/analytics/dashboard/performance' }
      ];

      const currentEndpoint = endpoints.find(e => e.tab === activeTab);
      if (!currentEndpoint) return;

      const response = await fetch(currentEndpoint.endpoint, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        },
        body: JSON.stringify({
          time_range: timeRange,
          user_id: userId,
          aggregation: 'daily'
        })
      });

      if (!response.ok) {
        throw new Error(`Failed to load dashboard data: ${response.statusText}`);
      }

      const data = await response.json();
      setDashboardData(data.data || {});

      // Load insights if admin
      if (isAdmin && activeTab <= 2) {
        await loadInsights();
      }

    } catch (err) {
      console.error('Failed to load dashboard data:', err);
      setError(err instanceof Error ? err.message : 'Failed to load dashboard data');
    } finally {
      setLoading(false);
    }
  };

  const loadInsights = async () => {
    try {
      const insightType = activeTab === 1 ? 'cost' : 'performance';
      const response = await fetch(`/api/v1/analytics/insights/${insightType}?time_range=${timeRange}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('token')}`
        }
      });

      if (response.ok) {
        const insights = await response.json();
        setDashboardData(prev => ({ ...prev, insights: insights.insights }));
      }
    } catch (err) {
      console.error('Failed to load insights:', err);
    }
  };

  const getMetricCards = (): MetricCard[] => {
    switch (activeTab) {
      case 0: // Usage
        return [
          {
            title: 'Total Requests',
            value: dashboardData.usage_data?.reduce((sum: number, item: any) => sum + (item.count || 0), 0) || 0,
            icon: <Timeline />,
            color: chartColors.primary
          },
          {
            title: 'Unique Users',
            value: dashboardData.top_features?.length || 0,
            icon: <People />,
            color: chartColors.success
          },
          {
            title: 'Total Tokens',
            value: dashboardData.usage_data?.reduce((sum: number, item: any) => sum + (item.sum_value || 0), 0)?.toLocaleString() || '0',
            icon: <TrendingUp />,
            color: chartColors.info
          },
          {
            title: 'Avg Response Time',
            value: `${dashboardData.usage_trends?.reduce((sum: number, item: any) => sum + (item.average || 0), 0) / Math.max(dashboardData.usage_trends?.length || 1, 1) || 0}ms`,
            icon: <Speed />,
            color: chartColors.warning
          }
        ];

      case 1: // Cost
        return [
          {
            title: 'Total Cost',
            value: `$${dashboardData.total_cost?.total_cost?.toFixed(2) || '0.00'}`,
            icon: <AttachMoney />,
            color: chartColors.secondary
          },
          {
            title: 'Avg per Request',
            value: `$${dashboardData.total_cost?.average_per_transaction?.toFixed(4) || '0.0000'}`,
            icon: <Assessment />,
            color: chartColors.warning
          },
          {
            title: 'Total Transactions',
            value: dashboardData.total_cost?.total_transactions || 0,
            icon: <Timeline />,
            color: chartColors.primary
          },
          {
            title: 'Optimization Opportunities',
            value: dashboardData.optimization_opportunities?.length || 0,
            icon: <Warning />,
            color: chartColors.warning
          }
        ];

      case 2: // Performance
        return [
          {
            title: 'Avg Response Time',
            value: `${dashboardData.response_time_trends?.reduce((sum: number, item: any) => sum + (item.average || 0), 0) / Math.max(dashboardData.response_time_trends?.length || 1, 1) || 0}ms`,
            icon: <Speed />,
            color: chartColors.primary
          },
          {
            title: 'Error Rate',
            value: `${dashboardData.error_rates?.error_rate_percent || 0}%`,
            icon: <Warning />,
            color: dashboardData.error_rates?.error_rate_percent > 5 ? chartColors.secondary : chartColors.success
          },
          {
            title: 'Total Requests',
            value: dashboardData.error_rates?.total_requests || 0,
            icon: <Timeline />,
            color: chartColors.info
          },
          {
            title: 'Slowest Endpoints',
            value: dashboardData.slowest_endpoints?.length || 0,
            icon: <Assessment />,
            color: chartColors.warning
          }
        ];

      default:
        return [];
    }
  };

  const renderUsageDashboard = () => {
    const usageTrendData = {
      labels: dashboardData.usage_trends?.map((item: any) => 
        new Date(item.timestamp).toLocaleDateString()
      ) || [],
      datasets: [
        {
          label: 'Usage Count',
          data: dashboardData.usage_trends?.map((item: any) => item.value) || [],
          borderColor: chartColors.primary,
          backgroundColor: chartColors.gradients.blue[1],
          fill: true,
          tension: 0.4
        }
      ]
    };

    const topFeaturesData = {
      labels: dashboardData.top_features?.map((item: any) => item.feature) || [],
      datasets: [
        {
          label: 'Usage Count',
          data: dashboardData.top_features?.map((item: any) => item.usage_count) || [],
          backgroundColor: [
            chartColors.primary,
            chartColors.success,
            chartColors.warning,
            chartColors.info,
            chartColors.secondary
          ]
        }
      ]
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Usage Trends
              </Typography>
              <Box height={300}>
                <Line 
                  data={usageTrendData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'top' as const,
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Features
              </Typography>
              <Box height={300}>
                <Pie 
                  data={topFeaturesData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'bottom' as const,
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {dashboardData.error_analytics && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Error Analytics
                </Typography>
                <Stack direction="row" spacing={2} sx={{ mb: 2 }}>
                  <Chip 
                    label={`Error Rate: ${dashboardData.error_analytics.error_rate_percent}%`}
                    color={dashboardData.error_analytics.error_rate_percent > 5 ? 'error' : 'success'}
                    icon={dashboardData.error_analytics.error_rate_percent > 5 ? <Warning /> : <CheckCircle />}
                  />
                  <Chip 
                    label={`Total Errors: ${dashboardData.error_analytics.total_errors}`}
                    variant="outlined"
                  />
                </Stack>
                
                {dashboardData.error_analytics.top_errors?.map((error: any, index: number) => (
                  <Box key={index} sx={{ mb: 1 }}>
                    <Typography variant="body2">
                      {error.error_code}: {error.count} occurrences ({error.percentage}%)
                    </Typography>
                  </Box>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    );
  };

  const renderCostDashboard = () => {
    const costTrendData = {
      labels: dashboardData.cost_trends?.map((item: any) => 
        new Date(item.timestamp).toLocaleDateString()
      ) || [],
      datasets: [
        {
          label: 'Daily Cost ($)',
          data: dashboardData.cost_trends?.map((item: any) => item.value) || [],
          borderColor: chartColors.secondary,
          backgroundColor: chartColors.gradients.orange[1],
          fill: true,
          tension: 0.4
        }
      ]
    };

    const costByServiceData = {
      labels: dashboardData.cost_by_service?.map((item: any) => item.service) || [],
      datasets: [
        {
          label: 'Cost ($)',
          data: dashboardData.cost_by_service?.map((item: any) => item.total_cost) || [],
          backgroundColor: [
            chartColors.primary,
            chartColors.success,
            chartColors.warning,
            chartColors.info,
            chartColors.secondary
          ]
        }
      ]
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cost Trends
              </Typography>
              <Box height={300}>
                <Line 
                  data={costTrendData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'top' as const,
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: function(value) {
                            return '$' + value;
                          }
                        }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Cost by Service
              </Typography>
              <Box height={300}>
                <Bar 
                  data={costByServiceData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        display: false
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: function(value) {
                            return '$' + value;
                          }
                        }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {dashboardData.optimization_opportunities && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Cost Optimization Opportunities
                </Typography>
                {dashboardData.optimization_opportunities.map((opportunity: any, index: number) => (
                  <Alert 
                    key={index}
                    severity={opportunity.impact_score > 70 ? 'error' : opportunity.impact_score > 40 ? 'warning' : 'info'}
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="subtitle2">
                      {opportunity.title} (Impact: {opportunity.impact_score}/100)
                    </Typography>
                    <Typography variant="body2">
                      {opportunity.description}
                    </Typography>
                    {opportunity.recommendation && (
                      <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                        Recommendation: {opportunity.recommendation}
                      </Typography>
                    )}
                  </Alert>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    );
  };

  const renderPerformanceDashboard = () => {
    const performanceTrendData = {
      labels: dashboardData.response_time_trends?.map((item: any) => 
        new Date(item.timestamp).toLocaleDateString()
      ) || [],
      datasets: [
        {
          label: 'Avg Response Time (ms)',
          data: dashboardData.response_time_trends?.map((item: any) => item.average) || [],
          borderColor: chartColors.success,
          backgroundColor: chartColors.gradients.green[1],
          fill: true,
          tension: 0.4
        }
      ]
    };

    return (
      <Grid container spacing={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Response Time Trends
              </Typography>
              <Box height={300}>
                <Line 
                  data={performanceTrendData}
                  options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                      legend: {
                        position: 'top' as const,
                      }
                    },
                    scales: {
                      y: {
                        beginAtZero: true,
                        ticks: {
                          callback: function(value) {
                            return value + 'ms';
                          }
                        }
                      }
                    }
                  }}
                />
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Slowest Endpoints
              </Typography>
              {dashboardData.slowest_endpoints?.map((endpoint: any, index: number) => (
                <Box key={index} sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1 }}>
                  <Typography variant="body2" fontWeight="bold">
                    {endpoint.endpoint}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Avg: {endpoint.avg_response_time_ms}ms | Max: {endpoint.max_response_time_ms}ms
                  </Typography>
                  <Typography variant="caption" display="block">
                    {endpoint.request_count} requests
                  </Typography>
                </Box>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {dashboardData.performance_insights && (
          <Grid item xs={12}>
            <Card>
              <CardContent>
                <Typography variant="h6" gutterBottom>
                  Performance Insights
                </Typography>
                {dashboardData.performance_insights.map((insight: any, index: number) => (
                  <Alert 
                    key={index}
                    severity={insight.impact_score > 70 ? 'error' : insight.impact_score > 40 ? 'warning' : 'info'}
                    sx={{ mb: 2 }}
                  >
                    <Typography variant="subtitle2">
                      {insight.title} (Impact: {insight.impact_score}/100)
                    </Typography>
                    <Typography variant="body2">
                      {insight.description}
                    </Typography>
                    {insight.recommendation && (
                      <Typography variant="body2" sx={{ mt: 1, fontStyle: 'italic' }}>
                        Recommendation: {insight.recommendation}
                      </Typography>
                    )}
                  </Alert>
                ))}
              </CardContent>
            </Card>
          </Grid>
        )}
      </Grid>
    );
  };

  const renderTabContent = () => {
    switch (activeTab) {
      case 0:
        return renderUsageDashboard();
      case 1:
        return isAdmin ? renderCostDashboard() : (
          <Alert severity="warning">
            Cost analytics are only available to administrators.
          </Alert>
        );
      case 2:
        return isAdmin ? renderPerformanceDashboard() : (
          <Alert severity="warning">
            Performance analytics are only available to administrators.
          </Alert>
        );
      default:
        return null;
    }
  };

  return (
    <Box>
      {/* Header Controls */}
      <Box sx={{ mb: 3, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h4" component="h1">
          Analytics Dashboard
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 150 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              label="Time Range"
            >
              <MenuItem value="last_hour">Last Hour</MenuItem>
              <MenuItem value="last_24_hours">Last 24 Hours</MenuItem>
              <MenuItem value="last_7_days">Last 7 Days</MenuItem>
              <MenuItem value="last_30_days">Last 30 Days</MenuItem>
              <MenuItem value="last_90_days">Last 90 Days</MenuItem>
            </Select>
          </FormControl>
          
          <Button 
            variant="outlined" 
            onClick={loadDashboardData}
            disabled={loading}
            startIcon={loading ? <CircularProgress size={16} /> : null}
          >
            Refresh
          </Button>
        </Box>
      </Box>

      {/* Error Display */}
      {error && (
        <Alert severity="error" sx={{ mb: 3 }}>
          {error}
        </Alert>
      )}

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={activeTab} onChange={(_, newValue) => setActiveTab(newValue)}>
          <Tab label="Usage Analytics" />
          <Tab label="Cost Analytics" disabled={!isAdmin} />
          <Tab label="Performance Analytics" disabled={!isAdmin} />
        </Tabs>
      </Box>

      {/* Metric Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {getMetricCards().map((metric, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card>
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
                  <Box>
                    <Typography color="textSecondary" gutterBottom variant="body2">
                      {metric.title}
                    </Typography>
                    <Typography variant="h5" component="div">
                      {metric.value}
                    </Typography>
                    {metric.change && (
                      <Typography 
                        variant="caption" 
                        color={
                          metric.changeType === 'positive' ? 'success.main' : 
                          metric.changeType === 'negative' ? 'error.main' : 
                          'text.secondary'
                        }
                      >
                        {metric.change}
                      </Typography>
                    )}
                  </Box>
                  <Box sx={{ color: metric.color }}>
                    {metric.icon}
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Tab Content */}
      {loading ? (
        <Box sx={{ display: 'flex', justifyContent: 'center', py: 4 }}>
          <CircularProgress />
        </Box>
      ) : (
        renderTabContent()
      )}
    </Box>
  );
};

export default AnalyticsDashboard; 