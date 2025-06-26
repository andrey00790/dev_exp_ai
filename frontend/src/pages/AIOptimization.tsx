import React, { useState, useEffect } from 'react';

interface OptimizationResult {
  optimization_id: string;
  model_type: string;
  optimization_type: string;
  status: string;
  improvement_percent: Record<string, number>;
  optimization_time: number;
  recommendations: string[];
  before_metrics: Record<string, number>;
  after_metrics: Record<string, number>;
}

interface BenchmarkResult {
  benchmark_id: string;
  models: Record<string, Record<string, number>>;
  benchmark_time: number;
  timestamp: string;
}

interface ModelConfig {
  model_type: string;
  config: Record<string, any>;
  last_updated: string;
}

const AIOptimization: React.FC = () => {
  const [selectedModel, setSelectedModel] = useState('code_review');
  const [selectedOptimization, setSelectedOptimization] = useState('performance');
  const [optimizationResult, setOptimizationResult] = useState<OptimizationResult | null>(null);
  const [benchmarkResult, setBenchmarkResult] = useState<BenchmarkResult | null>(null);
  const [recommendations, setRecommendations] = useState<Record<string, string[]>>({});
  const [modelConfig, setModelConfig] = useState<ModelConfig | null>(null);
  const [loading, setLoading] = useState(false);
  const [activeTab, setActiveTab] = useState('optimize');

  const modelTypes = [
    { value: 'code_review', label: 'Code Review' },
    { value: 'semantic_search', label: 'Semantic Search' },
    { value: 'rfc_generation', label: 'RFC Generation' },
    { value: 'multimodal_search', label: 'Multimodal Search' }
  ];

  const optimizationTypes = [
    { value: 'model_tuning', label: 'Model Fine-tuning' },
    { value: 'performance', label: 'Performance Optimization' },
    { value: 'cost_reduction', label: 'Cost Reduction' },
    { value: 'quality_improvement', label: 'Quality Improvement' }
  ];

  // Optimize model
  const handleOptimize = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai-optimization/optimize', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          model_type: selectedModel,
          optimization_type: selectedOptimization
        })
      });

      if (response.ok) {
        const result = await response.json();
        setOptimizationResult(result);
      }
    } catch (error) {
      console.error('Optimization failed:', error);
    } finally {
      setLoading(false);
    }
  };

  // Benchmark models
  const handleBenchmark = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/v1/ai-optimization/benchmark', {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        setBenchmarkResult(result);
      }
    } catch (error) {
      console.error('Benchmarking failed:', error);
    } finally {
      setLoading(false);
    }
  };

  // Get recommendations
  const getRecommendations = async () => {
    try {
      const response = await fetch('/api/v1/ai-optimization/recommendations', {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        setRecommendations(result.recommendations);
      }
    } catch (error) {
      console.error('Failed to get recommendations:', error);
    }
  };

  // Get model config
  const getModelConfig = async (modelType: string) => {
    try {
      const response = await fetch(`/api/v1/ai-optimization/config/${modelType}`, {
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        const result = await response.json();
        setModelConfig(result);
      }
    } catch (error) {
      console.error('Failed to get model config:', error);
    }
  };

  // Reset model config
  const resetModelConfig = async (modelType: string) => {
    try {
      const response = await fetch(`/api/v1/ai-optimization/config/${modelType}/reset`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        }
      });

      if (response.ok) {
        await getModelConfig(modelType);
      }
    } catch (error) {
      console.error('Failed to reset model config:', error);
    }
  };

  useEffect(() => {
    getRecommendations();
    getModelConfig(selectedModel);
  }, [selectedModel]);

  const formatMetric = (key: string, value: number) => {
    switch (key) {
      case 'accuracy':
        return `${(value * 100).toFixed(1)}%`;
      case 'latency_ms':
        return `${value.toFixed(0)}ms`;
      case 'cost_per_request':
        return `$${value.toFixed(4)}`;
      case 'throughput_rps':
        return `${value.toFixed(1)} RPS`;
      case 'memory_usage_mb':
        return `${value.toFixed(0)}MB`;
      case 'cpu_usage_percent':
        return `${value.toFixed(1)}%`;
      case 'quality_score':
        return `${value.toFixed(1)}/10`;
      default:
        return value.toFixed(2);
    }
  };

  const getImprovementColor = (improvement: number) => {
    if (improvement > 10) return 'text-green-600 font-semibold';
    if (improvement > 0) return 'text-green-500';
    if (improvement < -10) return 'text-red-600 font-semibold';
    if (improvement < 0) return 'text-red-500';
    return 'text-gray-600';
  };

  return (
    <div className="p-6 space-y-8">
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">AI Optimization</h1>
        <p className="text-gray-600">Model fine-tuning, performance optimization, and cost reduction</p>
      </div>

      {/* Tab Navigation */}
      <div className="border-b border-gray-200">
        <nav className="-mb-px flex space-x-8">
          {['optimize', 'benchmark', 'config', 'recommendations'].map((tab) => (
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

      {/* Optimize Tab */}
      {activeTab === 'optimize' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Model Optimization</h2>
            
            <div className="grid grid-cols-2 gap-4 mb-6">
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
                <label className="block text-sm font-medium mb-2">Optimization Type</label>
                <select
                  value={selectedOptimization}
                  onChange={(e) => setSelectedOptimization(e.target.value)}
                  className="w-full p-2 border rounded-md"
                >
                  {optimizationTypes.map((opt) => (
                    <option key={opt.value} value={opt.value}>
                      {opt.label}
                    </option>
                  ))}
                </select>
              </div>
            </div>

            <button
              onClick={handleOptimize}
              disabled={loading}
              className="px-6 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 disabled:opacity-50"
            >
              {loading ? 'Optimizing...' : 'Start Optimization'}
            </button>
          </div>

          {/* Optimization Results */}
          {optimizationResult && (
            <div className="bg-white p-6 rounded-lg shadow">
              <h3 className="text-lg font-semibold mb-4">Optimization Results</h3>
              
              <div className="grid grid-cols-2 gap-6">
                {/* Before Metrics */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">Before Optimization</h4>
                  <div className="space-y-2">
                    {Object.entries(optimizationResult.before_metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm text-gray-600">{key.replace('_', ' ').toUpperCase()}:</span>
                        <span className="text-sm font-medium">{formatMetric(key, value)}</span>
                      </div>
                    ))}
                  </div>
                </div>

                {/* After Metrics */}
                <div>
                  <h4 className="font-medium text-gray-700 mb-3">After Optimization</h4>
                  <div className="space-y-2">
                    {Object.entries(optimizationResult.after_metrics).map(([key, value]) => (
                      <div key={key} className="flex justify-between">
                        <span className="text-sm text-gray-600">{key.replace('_', ' ').toUpperCase()}:</span>
                        <div className="flex items-center space-x-2">
                          <span className="text-sm font-medium">{formatMetric(key, value)}</span>
                          <span className={`text-xs ${getImprovementColor(optimizationResult.improvement_percent[key])}`}>
                            ({optimizationResult.improvement_percent[key] > 0 ? '+' : ''}{optimizationResult.improvement_percent[key].toFixed(1)}%)
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

              {/* Recommendations */}
              {optimizationResult.recommendations.length > 0 && (
                <div className="mt-6">
                  <h4 className="font-medium text-gray-700 mb-3">Recommendations</h4>
                  <ul className="space-y-2">
                    {optimizationResult.recommendations.map((rec, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-start">
                        <span className="text-blue-500 mr-2">•</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Benchmark Tab */}
      {activeTab === 'benchmark' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Model Benchmarking</h2>
              <button
                onClick={handleBenchmark}
                disabled={loading}
                className="px-4 py-2 bg-purple-600 text-white rounded-md hover:bg-purple-700 disabled:opacity-50"
              >
                {loading ? 'Benchmarking...' : 'Run Benchmark'}
              </button>
            </div>

            {benchmarkResult && (
              <div className="overflow-x-auto">
                <table className="min-w-full divide-y divide-gray-200">
                  <thead className="bg-gray-50">
                    <tr>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Model
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Accuracy
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Latency
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Cost
                      </th>
                      <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                        Quality Score
                      </th>
                    </tr>
                  </thead>
                  <tbody className="bg-white divide-y divide-gray-200">
                    {Object.entries(benchmarkResult.models).map(([modelType, metrics]) => (
                      <tr key={modelType}>
                        <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                          {modelType.replace('_', ' ').toUpperCase()}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatMetric('accuracy', metrics.accuracy)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatMetric('latency_ms', metrics.latency_ms)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatMetric('cost_per_request', metrics.cost_per_request)}
                        </td>
                        <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                          {formatMetric('quality_score', metrics.quality_score)}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Config Tab */}
      {activeTab === 'config' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-xl font-semibold">Model Configuration</h2>
              <div className="space-x-2">
                <select
                  value={selectedModel}
                  onChange={(e) => setSelectedModel(e.target.value)}
                  className="p-2 border rounded-md"
                >
                  {modelTypes.map((model) => (
                    <option key={model.value} value={model.value}>
                      {model.label}
                    </option>
                  ))}
                </select>
                <button
                  onClick={() => resetModelConfig(selectedModel)}
                  className="px-4 py-2 bg-gray-600 text-white rounded-md hover:bg-gray-700"
                >
                  Reset to Defaults
                </button>
              </div>
            </div>

            {modelConfig && (
              <div className="space-y-4">
                <h3 className="font-medium text-gray-700">
                  {selectedModel.replace('_', ' ').toUpperCase()} Configuration
                </h3>
                <div className="grid grid-cols-2 gap-4">
                  {Object.entries(modelConfig.config).map(([key, value]) => (
                    <div key={key} className="flex justify-between items-center p-3 bg-gray-50 rounded">
                      <span className="text-sm font-medium text-gray-700">
                        {key.replace('_', ' ').toUpperCase()}:
                      </span>
                      <span className="text-sm text-gray-900">
                        {typeof value === 'boolean' ? (value ? 'Enabled' : 'Disabled') : String(value)}
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Recommendations Tab */}
      {activeTab === 'recommendations' && (
        <div className="space-y-6">
          <div className="bg-white p-6 rounded-lg shadow">
            <h2 className="text-xl font-semibold mb-4">Optimization Recommendations</h2>
            
            {Object.entries(recommendations).map(([modelType, recs]) => (
              <div key={modelType} className="mb-6">
                <h3 className="font-medium text-gray-700 mb-3">
                  {modelType.replace('_', ' ').toUpperCase()}
                </h3>
                {recs.length > 0 ? (
                  <ul className="space-y-2">
                    {recs.map((rec, index) => (
                      <li key={index} className="text-sm text-gray-600 flex items-start">
                        <span className="text-yellow-500 mr-2">⚠</span>
                        {rec}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="text-sm text-green-600">✓ No optimization recommendations - model is performing well</p>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AIOptimization; 