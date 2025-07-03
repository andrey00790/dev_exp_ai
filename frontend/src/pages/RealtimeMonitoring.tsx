import React, { useState, useEffect, useCallback } from 'react';
import { Line, Bar, Doughnut } from 'react-chartjs-2';

interface LiveMetrics {
  timestamp: string;
  metrics: Record<string, {
    value: number;
    timestamp: string;
    metric: string;
    source: string;
  }>;
  alerts_summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
    low: number;
  };
  anomalies_summary: {
    total: number;
    critical: number;
    high: number;
    medium: number;
  };
}

interface Alert {
  alert_id: string;
  severity: string;
  status: string;
  title: string;
  description: string;
  metric: string;
  current_value: number;
  threshold_value: number;
  source: string;
  created_at: string;
  updated_at: string;
  resolved_at?: string;
  acknowledged_by?: string;
  metadata?: Record<string, any>;
}

interface Anomaly {
  anomaly_id: string;
  anomaly_type: string;
  metric: string;
  source: string;
  confidence: number;
  severity: string;
  description: string;
  detected_at: string;
  start_time: string;
  end_time?: string;
  baseline_value: number;
  anomalous_value: number;
  metadata?: Record<string, any>;
}

interface SLAStatus {
  sla_id: string;
  name: string;
  description: string;
  is_active: boolean;
  current_compliance: number;
  violations_24h: number;
  thresholds: Array<{
    metric: string;
    threshold_value: number;
    comparison: string;
    violations_24h: number;
    compliant: boolean;
  }>;
}

const RealtimeMonitoring: React.FC = () => {
  const [liveMetrics, setLiveMetrics] = useState<LiveMetrics | null>(null);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [anomalies, setAnomalies] = useState<Anomaly[]>([]);
  const [slaStatus, setSlaStatus] = useState<SLAStatus[]>([]);
  const [dashboardStats, setDashboardStats] = useState<any>(null);
  const [activeTab, setActiveTab] = useState('dashboard');
  const [autoRefresh, setAutoRefresh] = useState(true);
  const [websocket, setWebsocket] = useState<WebSocket | null>(null);
  const [connectionStatus, setConnectionStatus] = useState('disconnected');

  // WebSocket connection
  const connectWebSocket = useCallback(() => {
    const token = localStorage.getItem('auth_token');
    const wsUrl = `ws://localhost:8000/api/v1/realtime-monitoring/live-feed`;
    
    try {
      const ws = new WebSocket(wsUrl);
      
      ws.onopen = () => {
        setConnectionStatus('connected');
        console.log('WebSocket connected');
      };
      
      ws.onmessage = (event) => {
        const data = JSON.parse(event.data);
        
        if (data.type === 'alert') {
          setAlerts(prev => [data.data, ...prev.slice(0, 49)]); // Keep last 50
        } else if (data.type === 'anomaly') {
          setAnomalies(prev => [data.data, ...prev.slice(0, 49)]); // Keep last 50
        } else if (data.type === 'live_update') {
          // Update dashboard stats
          setDashboardStats(prev => prev ? { ...prev, ...data.data } : data.data);
        }
      };
      
      ws.onclose = () => {
        setConnectionStatus('disconnected');
        console.log('WebSocket disconnected');
        
        // Attempt to reconnect after 5 seconds
        setTimeout(() => {
          if (autoRefresh) {
            connectWebSocket();
          }
        }, 5000);
      };
      
      ws.onerror = (error) => {
        setConnectionStatus('error');
        console.error('WebSocket error:', error);
      };
      
      setWebsocket(ws);
    } catch (error) {
      console.error('Failed to connect WebSocket:', error);
      setConnectionStatus('error');
    }
  }, [autoRefresh]);

  // Load live metrics
  const loadLiveMetrics = async () => {
    try {
      const response = await fetch('/api/v1/realtime-monitoring/live-metrics', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setLiveMetrics(data);
      }
    } catch (error) {
      console.error('Failed to load live metrics:', error);
    }
  };

  // Load alerts
  const loadAlerts = async () => {
    try {
      const response = await fetch('/api/v1/realtime-monitoring/alerts?limit=50', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAlerts(data.alerts);
      }
    } catch (error) {
      console.error('Failed to load alerts:', error);
    }
  };

  // Load anomalies
  const loadAnomalies = async () => {
    try {
      const response = await fetch('/api/v1/realtime-monitoring/anomalies?hours=24', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setAnomalies(data.anomalies);
      }
    } catch (error) {
      console.error('Failed to load anomalies:', error);
    }
  };

  // Load SLA status
  const loadSLAStatus = async () => {
    try {
      const response = await fetch('/api/v1/realtime-monitoring/sla-status', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setSlaStatus(data.slas);
      }
    } catch (error) {
      console.error('Failed to load SLA status:', error);
    }
  };

  // Load dashboard stats
  const loadDashboardStats = async () => {
    try {
      const response = await fetch('/api/v1/realtime-monitoring/dashboard-stats', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const data = await response.json();
        setDashboardStats(data.dashboard_stats);
      }
    } catch (error) {
      console.error('Failed to load dashboard stats:', error);
    }
  };

  // Acknowledge alert
  const acknowledgeAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/realtime-monitoring/alerts/${alertId}/acknowledge`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ action: 'acknowledge' })
      });

      if (response.ok) {
        // Update local alert status
        setAlerts(prev => prev.map(alert => 
          alert.alert_id === alertId 
            ? { ...alert, status: 'acknowledged' }
            : alert
        ));
      }
    } catch (error) {
      console.error('Failed to acknowledge alert:', error);
    }
  };

  // Resolve alert
  const resolveAlert = async (alertId: string) => {
    try {
      const response = await fetch(`/api/v1/realtime-monitoring/alerts/${alertId}/resolve`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({ action: 'resolve' })
      });

      if (response.ok) {
        // Update local alert status
        setAlerts(prev => prev.map(alert => 
          alert.alert_id === alertId 
            ? { ...alert, status: 'resolved', resolved_at: new Date().toISOString() }
            : alert
        ));
      }
    } catch (error) {
      console.error('Failed to resolve alert:', error);
    }
  };

  useEffect(() => {
    // Initial data load
    loadLiveMetrics();
    loadAlerts();
    loadAnomalies();
    loadSLAStatus();
    loadDashboardStats();

    // Connect WebSocket
    if (autoRefresh) {
      connectWebSocket();
    }

    // Auto-refresh data every 30 seconds (backup to WebSocket)
    const interval = setInterval(() => {
      if (autoRefresh) {
        loadLiveMetrics();
        loadDashboardStats();
      }
    }, 30000);

    return () => {
      clearInterval(interval);
      if (websocket) {
        websocket.close();
      }
    };
  }, [autoRefresh, connectWebSocket]);

  // Helper functions
  const getSeverityColor = (severity: string) => {
    switch (severity) {
      case 'critical':
        return 'bg-red-100 text-red-800';
      case 'high':
        return 'bg-orange-100 text-orange-800';
      case 'medium':
        return 'bg-yellow-100 text-yellow-800';
      case 'low':
        return 'bg-blue-100 text-blue-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
        return 'bg-red-100 text-red-800';
      case 'acknowledged':
        return 'bg-yellow-100 text-yellow-800';
      case 'resolved':
        return 'bg-green-100 text-green-800';
      default:
        return 'bg-gray-100 text-gray-800';
    }
  };

  const getConnectionStatusColor = () => {
    switch (connectionStatus) {
      case 'connected':
        return 'text-green-600';
      case 'error':
        return 'text-red-600';
      default:
        return 'text-yellow-600';
    }
  };

  const createAlertsChart = () => {
    if (!liveMetrics) return null;

    return {
      labels: ['Critical', 'High', 'Medium', 'Low'],
      datasets: [
        {
          data: [
            liveMetrics.alerts_summary.critical,
            liveMetrics.alerts_summary.high,
            liveMetrics.alerts_summary.medium,
            liveMetrics.alerts_summary.low
          ],
          backgroundColor: ['#EF4444', '#F97316', '#EAB308', '#3B82F6']
        }
      ]
    };
  };

  const formatTimestamp = (timestamp: string) => {
    return new Date(timestamp).toLocaleString();
  };

  const formatValue = (value: number, metric: string) => {
    switch (metric) {
      case 'response_time':
        return `${value.toFixed(0)}ms`;
      case 'error_rate':
        return `${value.toFixed(2)}%`;
      case 'cpu_usage':
      case 'memory_usage':
        return `${value.toFixed(1)}%`;
      case 'accuracy':
        return `${(value * 100).toFixed(1)}%`;
      default:
        return value.toFixed(2);
    }
  };

  return (
    <div className="p-6 space-y-8">
      {/* Header */}
      <div className="flex justify-between items-center">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">Real-time Monitoring</h1>
          <p className="text-gray-600">Live AI system monitoring, alerts, and anomaly detection</p>
        </div>
        <div className="flex items-center space-x-4">
          <div className="flex items-center space-x-2">
            <div className={`w-3 h-3 rounded-full ${connectionStatus === 'connected' ? 'bg-green-500' : connectionStatus === 'error' ? 'bg-red-500' : 'bg-yellow-500'}`}></div>
            <span className={`text-sm font-medium ${getConnectionStatusColor()}`}>
              {connectionStatus.charAt(0).toUpperCase() + connectionStatus.slice(1)}
            </span>
          </div>
          <button
            onClick={() => setAutoRefresh(!autoRefresh)}
            className={`px-4 py-2 rounded-md text-sm font-medium ${
              autoRefresh 
                ? 'bg-green-100 text-green-800' 
                : 'bg-gray-100 text-gray-800'
            }`}
          >
            Auto-refresh: {autoRefresh ? 'ON' : 'OFF'}
          </button>
        </div>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['dashboard', 'alerts', 'anomalies', 'sla'].map((tab) => (
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
          {/* Status Cards */}
          {dashboardStats && (
            <div className="grid grid-cols-4 gap-4">
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">System Health</h3>
                <p className={`text-3xl font-bold ${dashboardStats.system_health === 'healthy' ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboardStats.system_health?.toUpperCase()}
                </p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Active Alerts</h3>
                <p className="text-3xl font-bold text-orange-600">{dashboardStats.active_alerts}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Critical Alerts</h3>
                <p className="text-3xl font-bold text-red-600">{dashboardStats.critical_alerts}</p>
              </div>
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold text-gray-700">Monitoring Active</h3>
                <p className={`text-3xl font-bold ${dashboardStats.monitoring_active ? 'text-green-600' : 'text-red-600'}`}>
                  {dashboardStats.monitoring_active ? 'YES' : 'NO'}
                </p>
              </div>
            </div>
          )}

          {/* Live Metrics */}
          {liveMetrics && (
            <div className="grid grid-cols-2 gap-6">
              {/* Alerts Summary Chart */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">Active Alerts by Severity</h3>
                {createAlertsChart() && <Doughnut data={createAlertsChart()!} />}
              </div>

              {/* Current Metrics */}
              <div className="bg-white p-6 rounded-lg shadow">
                <h3 className="text-lg font-semibold mb-4">Current Metrics</h3>
                <div className="space-y-3">
                  {Object.entries(liveMetrics.metrics).slice(0, 6).map(([key, metric]) => (
                    <div key={key} className="flex justify-between items-center">
                      <span className="text-sm font-medium text-gray-700">
                        {metric.metric.replace('_', ' ').toUpperCase()}
                      </span>
                      <div className="text-right">
                        <span className="text-sm font-bold text-gray-900">
                          {formatValue(metric.value, metric.metric)}
                        </span>
                        <p className="text-xs text-gray-500">{metric.source}</p>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          )}

          {/* Recent Alerts & Anomalies */}
          <div className="grid grid-cols-2 gap-6">
            {/* Recent Alerts */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Recent Alerts</h3>
              <div className="space-y-3">
                {alerts.slice(0, 5).map((alert) => (
                  <div key={alert.alert_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{alert.title}</p>
                      <p className="text-xs text-gray-500">{formatTimestamp(alert.created_at)}</p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                      {alert.severity.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Recent Anomalies */}
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Recent Anomalies</h3>
              <div className="space-y-3">
                {anomalies.slice(0, 5).map((anomaly) => (
                  <div key={anomaly.anomaly_id} className="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-gray-900 truncate">{anomaly.description}</p>
                      <p className="text-xs text-gray-500">
                        Confidence: {(anomaly.confidence * 100).toFixed(1)}%
                      </p>
                    </div>
                    <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(anomaly.severity)}`}>
                      {anomaly.anomaly_type.toUpperCase()}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Alerts Tab */}
      {activeTab === 'alerts' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Alert Management</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Alert
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Severity
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Status
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Created
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Actions
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {alerts.map((alert) => (
                    <tr key={alert.alert_id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{alert.title}</div>
                          <div className="text-sm text-gray-500">{alert.description}</div>
                          <div className="text-xs text-gray-400">
                            {alert.metric} | {alert.source}
                          </div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(alert.severity)}`}>
                          {alert.severity.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getStatusColor(alert.status)}`}>
                          {alert.status.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatTimestamp(alert.created_at)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {alert.status === 'active' && (
                          <div className="space-x-2">
                            <button
                              onClick={() => acknowledgeAlert(alert.alert_id)}
                              className="text-yellow-600 hover:text-yellow-900"
                            >
                              Acknowledge
                            </button>
                            <button
                              onClick={() => resolveAlert(alert.alert_id)}
                              className="text-green-600 hover:text-green-900"
                            >
                              Resolve
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* Anomalies Tab */}
      {activeTab === 'anomalies' && (
        <div className="space-y-6">
          <div className="bg-white rounded-lg shadow overflow-hidden">
            <div className="px-6 py-4 border-b border-gray-200">
              <h2 className="text-xl font-semibold">Anomaly Detection</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Anomaly
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Type
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Confidence
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Values
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Detected
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {anomalies.map((anomaly) => (
                    <tr key={anomaly.anomaly_id}>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <div>
                          <div className="text-sm font-medium text-gray-900">{anomaly.description}</div>
                          <div className="text-sm text-gray-500">{anomaly.metric} | {anomaly.source}</div>
                        </div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        <span className={`px-2 py-1 text-xs font-medium rounded ${getSeverityColor(anomaly.severity)}`}>
                          {anomaly.anomaly_type.toUpperCase()}
                        </span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                        {(anomaly.confidence * 100).toFixed(1)}%
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        <div>Baseline: {anomaly.baseline_value.toFixed(2)}</div>
                        <div>Anomalous: {anomaly.anomalous_value.toFixed(2)}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                        {formatTimestamp(anomaly.detected_at)}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>
      )}

      {/* SLA Tab */}
      {activeTab === 'sla' && (
        <div className="space-y-6">
          <div className="grid gap-6">
            {slaStatus.map((sla) => (
              <div key={sla.sla_id} className="bg-white p-6 rounded-lg shadow">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900">{sla.name}</h3>
                    <p className="text-sm text-gray-600">{sla.description}</p>
                  </div>
                  <div className="text-right">
                    <div className={`text-2xl font-bold ${sla.current_compliance >= 99 ? 'text-green-600' : sla.current_compliance >= 95 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {sla.current_compliance.toFixed(1)}%
                    </div>
                    <p className="text-sm text-gray-500">Compliance</p>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4">
                  <div className="p-3 bg-gray-50 rounded">
                    <p className="text-sm font-medium text-gray-700">Status</p>
                    <p className={`text-lg font-bold ${sla.is_active ? 'text-green-600' : 'text-gray-600'}`}>
                      {sla.is_active ? 'Active' : 'Inactive'}
                    </p>
                  </div>
                  <div className="p-3 bg-gray-50 rounded">
                    <p className="text-sm font-medium text-gray-700">Violations (24h)</p>
                    <p className={`text-lg font-bold ${sla.violations_24h === 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {sla.violations_24h}
                    </p>
                  </div>
                </div>

                <div className="mt-4">
                  <h4 className="text-sm font-medium text-gray-700 mb-2">Thresholds</h4>
                  <div className="space-y-2">
                    {sla.thresholds.map((threshold, index) => (
                      <div key={index} className="flex justify-between items-center p-2 bg-gray-50 rounded">
                        <span className="text-sm text-gray-600">
                          {threshold.metric} {threshold.comparison} {threshold.threshold_value}
                        </span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm text-gray-500">
                            {threshold.violations_24h} violations
                          </span>
                          <span className={`w-3 h-3 rounded-full ${threshold.compliant ? 'bg-green-500' : 'bg-red-500'}`}></span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default RealtimeMonitoring; 