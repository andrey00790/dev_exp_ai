import React, { useState, useRef } from 'react';
import { 
  MagnifyingGlassIcon, 
  CodeBracketIcon, 
  CpuChipIcon,
  ChartBarIcon,
  DocumentTextIcon,
  ShieldCheckIcon,
  BoltIcon,
  ClipboardDocumentIcon,
  ArrowDownTrayIcon,
  ExclamationTriangleIcon,
  CheckCircleIcon,
  XCircleIcon,
  InformationCircleIcon
} from '@heroicons/react/24/outline';

interface AnalysisResult {
  content_type: string;
  language: string;
  size: number;
  readability_score: number;
  complexity: string;
  structure_score: number;
  suggestions: string[];
  key_topics: string[];
  security_issues: SecurityIssue[];
  performance_issues: PerformanceIssue[];
  quality_metrics: QualityMetrics;
}

interface SecurityIssue {
  severity: 'critical' | 'high' | 'medium' | 'low';
  description: string;
  line: number;
  suggestion: string;
}

interface PerformanceIssue {
  type: string;
  description: string;
  impact: 'high' | 'medium' | 'low';
  suggestion: string;
}

interface QualityMetrics {
  maintainability: number;
  reliability: number;
  security: number;
  performance: number;
  overall_score: number;
}

export default function CodeAnalysis() {
  const [code, setCode] = useState('');
  const [analysisType, setAnalysisType] = useState<'comprehensive' | 'security' | 'performance' | 'quality'>('comprehensive');
  const [language, setLanguage] = useState('auto');
  const [result, setResult] = useState<AnalysisResult | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');
  const [history, setHistory] = useState<AnalysisResult[]>([]);
  
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  const languages = [
    { value: 'auto', label: 'Auto-detect' },
    { value: 'python', label: 'Python' },
    { value: 'javascript', label: 'JavaScript' },
    { value: 'typescript', label: 'TypeScript' },
    { value: 'java', label: 'Java' },
    { value: 'cpp', label: 'C++' },
    { value: 'csharp', label: 'C#' },
    { value: 'go', label: 'Go' },
    { value: 'rust', label: 'Rust' },
    { value: 'php', label: 'PHP' },
    { value: 'ruby', label: 'Ruby' }
  ];

  const analysisTypes = [
    { value: 'comprehensive', label: 'Comprehensive', icon: MagnifyingGlassIcon, description: 'Full analysis with all checks' },
    { value: 'security', label: 'Security Focus', icon: ShieldCheckIcon, description: 'Security vulnerabilities and risks' },
    { value: 'performance', label: 'Performance', icon: BoltIcon, description: 'Performance bottlenecks and optimization' },
    { value: 'quality', label: 'Code Quality', icon: ChartBarIcon, description: 'Code quality and maintainability' }
  ];

  const handleAnalyze = async () => {
    if (!code.trim()) {
      alert('Please enter code to analyze');
      return;
    }

    setIsAnalyzing(true);
    
    try {
      const response = await fetch('/api/v1/ai/analyze', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          text: code,
          analysis_type: analysisType,
          language: language === 'auto' ? undefined : language,
          include_suggestions: true,
          include_security: true,
          include_performance: true
        })
      });

      if (!response.ok) {
        throw new Error('Analysis failed');
      }

      const analysisResult = await response.json();
      setResult(analysisResult);
      setHistory(prev => [analysisResult, ...prev.slice(0, 9)]); // Keep last 10
      setActiveTab('overview');
    } catch (error) {
      console.error('Analysis error:', error);
      alert('Analysis failed. Please try again.');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handleExport = async (format: 'pdf' | 'markdown' | 'json') => {
    if (!result) return;

    try {
      const response = await fetch('/api/v1/ai/analyze/export', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('auth_token')}`
        },
        body: JSON.stringify({
          analysis_result: result,
          format: format
        })
      });

      if (response.ok) {
        const blob = await response.blob();
        const url = window.URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `code-analysis.${format}`;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);
      }
    } catch (error) {
      console.error('Export error:', error);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 8) return 'text-green-600 bg-green-100';
    if (score >= 6) return 'text-yellow-600 bg-yellow-100';
    return 'text-red-600 bg-red-100';
  };

  const getSeverityIcon = (severity: string) => {
    switch (severity) {
      case 'critical':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'high':
        return <ExclamationTriangleIcon className="h-5 w-5 text-red-500" />;
      case 'medium':
        return <ExclamationTriangleIcon className="h-5 w-5 text-yellow-500" />;
      case 'low':
        return <InformationCircleIcon className="h-5 w-5 text-blue-500" />;
      default:
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    }
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      {/* Header */}
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">🔧 Code Analysis</h1>
        <p className="text-gray-600">
          Comprehensive code analysis with security, performance, and quality insights
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="space-y-6">
          {/* Analysis Configuration */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">Analysis Configuration</h2>
            
            {/* Analysis Type Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Analysis Type
              </label>
              <div className="grid grid-cols-2 gap-2">
                {analysisTypes.map((type) => {
                  const Icon = type.icon;
                  return (
                    <button
                      key={type.value}
                      onClick={() => setAnalysisType(type.value as any)}
                      className={`p-3 rounded-lg border text-left transition-colors ${
                        analysisType === type.value
                          ? 'border-blue-500 bg-blue-50 text-blue-700'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <div className="flex items-center space-x-2 mb-1">
                        <Icon className="h-4 w-4" />
                        <span className="font-medium text-sm">{type.label}</span>
                      </div>
                      <p className="text-xs text-gray-500">{type.description}</p>
                    </button>
                  );
                })}
              </div>
            </div>

            {/* Language Selection */}
            <div className="mb-4">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Programming Language
              </label>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                {languages.map((lang) => (
                  <option key={lang.value} value={lang.value}>
                    {lang.label}
                  </option>
                ))}
              </select>
            </div>
          </div>

          {/* Code Input */}
          <div className="bg-white rounded-lg shadow-sm border p-6">
            <h2 className="text-xl font-semibold mb-4">Code Input</h2>
            
            <textarea
              ref={textareaRef}
              value={code}
              onChange={(e) => setCode(e.target.value)}
              placeholder="Paste your code here for analysis..."
              className="w-full h-64 px-4 py-3 border border-gray-300 rounded-lg font-mono text-sm focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
            />

            <div className="mt-4 flex items-center justify-between">
              <div className="text-sm text-gray-500">
                {code.length} characters • {code.split('\n').length} lines
              </div>
              
              <div className="flex space-x-2">
                <button
                  onClick={() => setCode('')}
                  className="px-4 py-2 text-gray-600 hover:text-gray-800 transition-colors"
                >
                  Clear
                </button>
                <button
                  onClick={handleAnalyze}
                  disabled={isAnalyzing || !code.trim()}
                  className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed flex items-center space-x-2"
                >
                  {isAnalyzing ? (
                    <>
                      <div className="animate-spin h-4 w-4 border-2 border-white border-t-transparent rounded-full"></div>
                      <span>Analyzing...</span>
                    </>
                  ) : (
                    <>
                      <MagnifyingGlassIcon className="h-4 w-4" />
                      <span>Analyze Code</span>
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Results Section */}
        <div className="space-y-6">
          {result ? (
            <>
              {/* Quick Stats */}
              <div className="bg-white rounded-lg shadow-sm border p-6">
                <div className="flex items-center justify-between mb-4">
                  <h2 className="text-xl font-semibold">Analysis Results</h2>
                  <div className="flex space-x-2">
                    <button
                      onClick={() => handleExport('markdown')}
                      className="p-2 text-gray-500 hover:text-gray-700"
                      title="Export as Markdown"
                    >
                      <DocumentTextIcon className="h-5 w-5" />
                    </button>
                    <button
                      onClick={() => handleExport('pdf')}
                      className="p-2 text-gray-500 hover:text-gray-700"
                      title="Export as PDF"
                    >
                      <ArrowDownTrayIcon className="h-5 w-5" />
                    </button>
                  </div>
                </div>

                <div className="grid grid-cols-2 gap-4 mb-6">
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{result.language}</div>
                    <div className="text-sm text-gray-500">Language</div>
                  </div>
                  <div className="text-center p-3 bg-gray-50 rounded-lg">
                    <div className="text-2xl font-bold text-gray-900">{result.size}</div>
                    <div className="text-sm text-gray-500">Characters</div>
                  </div>
                </div>

                {/* Quality Metrics */}
                {result.quality_metrics && (
                  <div className="space-y-3">
                    <h3 className="font-medium text-gray-900">Quality Metrics</h3>
                    {Object.entries(result.quality_metrics).map(([metric, score]) => (
                      <div key={metric} className="flex items-center justify-between">
                        <span className="text-sm text-gray-600 capitalize">
                          {metric.replace('_', ' ')}
                        </span>
                        <div className="flex items-center space-x-2">
                          <div className="w-20 bg-gray-200 rounded-full h-2">
                            <div
                              className={`h-2 rounded-full ${
                                score >= 8 ? 'bg-green-500' : score >= 6 ? 'bg-yellow-500' : 'bg-red-500'
                              }`}
                              style={{ width: `${score * 10}%` }}
                            ></div>
                          </div>
                          <span className={`text-sm font-medium px-2 py-1 rounded ${getScoreColor(score)}`}>
                            {score.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* Detailed Results Tabs */}
              <div className="bg-white rounded-lg shadow-sm border">
                {/* Tab Navigation */}
                <div className="border-b border-gray-200">
                  <nav className="-mb-px flex space-x-8 px-6">
                    {['overview', 'security', 'performance', 'suggestions'].map((tab) => (
                      <button
                        key={tab}
                        onClick={() => setActiveTab(tab)}
                        className={`py-4 px-1 border-b-2 font-medium text-sm capitalize ${
                          activeTab === tab
                            ? 'border-blue-500 text-blue-600'
                            : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                        }`}
                      >
                        {tab}
                      </button>
                    ))}
                  </nav>
                </div>

                {/* Tab Content */}
                <div className="p-6">
                  {activeTab === 'overview' && (
                    <div className="space-y-4">
                      <div>
                        <h3 className="font-medium text-gray-900 mb-2">Content Analysis</h3>
                        <div className="grid grid-cols-2 gap-4 text-sm">
                          <div>
                            <span className="text-gray-500">Readability Score:</span>
                            <span className="ml-2 font-medium">{result.readability_score}/10</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Complexity:</span>
                            <span className="ml-2 font-medium">{result.complexity}</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Structure Score:</span>
                            <span className="ml-2 font-medium">{result.structure_score}/10</span>
                          </div>
                          <div>
                            <span className="text-gray-500">Content Type:</span>
                            <span className="ml-2 font-medium">{result.content_type}</span>
                          </div>
                        </div>
                      </div>

                      {result.key_topics.length > 0 && (
                        <div>
                          <h3 className="font-medium text-gray-900 mb-2">Key Topics</h3>
                          <div className="flex flex-wrap gap-2">
                            {result.key_topics.map((topic, index) => (
                              <span
                                key={index}
                                className="px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm"
                              >
                                {topic}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'security' && (
                    <div className="space-y-4">
                      <h3 className="font-medium text-gray-900">Security Issues</h3>
                      {result.security_issues && result.security_issues.length > 0 ? (
                        <div className="space-y-3">
                          {result.security_issues.map((issue, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-4">
                              <div className="flex items-start space-x-3">
                                {getSeverityIcon(issue.severity)}
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className="font-medium text-gray-900">{issue.description}</span>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                      issue.severity === 'critical' ? 'bg-red-100 text-red-800' :
                                      issue.severity === 'high' ? 'bg-red-100 text-red-800' :
                                      issue.severity === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                      'bg-blue-100 text-blue-800'
                                    }`}>
                                      {issue.severity}
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600 mb-2">{issue.suggestion}</p>
                                  <p className="text-xs text-gray-500">Line {issue.line}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <CheckCircleIcon className="h-12 w-12 mx-auto mb-2 text-green-500" />
                          <p>No security issues found</p>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'performance' && (
                    <div className="space-y-4">
                      <h3 className="font-medium text-gray-900">Performance Issues</h3>
                      {result.performance_issues && result.performance_issues.length > 0 ? (
                        <div className="space-y-3">
                          {result.performance_issues.map((issue, index) => (
                            <div key={index} className="border border-gray-200 rounded-lg p-4">
                              <div className="flex items-start space-x-3">
                                <BoltIcon className={`h-5 w-5 mt-0.5 ${
                                  issue.impact === 'high' ? 'text-red-500' :
                                  issue.impact === 'medium' ? 'text-yellow-500' :
                                  'text-blue-500'
                                }`} />
                                <div className="flex-1">
                                  <div className="flex items-center space-x-2 mb-1">
                                    <span className="font-medium text-gray-900">{issue.type}</span>
                                    <span className={`px-2 py-1 rounded-full text-xs font-medium ${
                                      issue.impact === 'high' ? 'bg-red-100 text-red-800' :
                                      issue.impact === 'medium' ? 'bg-yellow-100 text-yellow-800' :
                                      'bg-blue-100 text-blue-800'
                                    }`}>
                                      {issue.impact} impact
                                    </span>
                                  </div>
                                  <p className="text-sm text-gray-600 mb-2">{issue.description}</p>
                                  <p className="text-sm text-blue-600">{issue.suggestion}</p>
                                </div>
                              </div>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <BoltIcon className="h-12 w-12 mx-auto mb-2 text-green-500" />
                          <p>No performance issues found</p>
                        </div>
                      )}
                    </div>
                  )}

                  {activeTab === 'suggestions' && (
                    <div className="space-y-4">
                      <h3 className="font-medium text-gray-900">Improvement Suggestions</h3>
                      {result.suggestions && result.suggestions.length > 0 ? (
                        <div className="space-y-3">
                          {result.suggestions.map((suggestion, index) => (
                            <div key={index} className="flex items-start space-x-3 p-4 bg-blue-50 rounded-lg">
                              <InformationCircleIcon className="h-5 w-5 text-blue-500 mt-0.5" />
                              <p className="text-sm text-gray-700">{suggestion}</p>
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div className="text-center py-8 text-gray-500">
                          <CheckCircleIcon className="h-12 w-12 mx-auto mb-2 text-green-500" />
                          <p>Code looks good! No suggestions at this time.</p>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </>
          ) : (
            <div className="bg-white rounded-lg shadow-sm border p-12 text-center">
              <CodeBracketIcon className="h-16 w-16 mx-auto mb-4 text-gray-300" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Analyze</h3>
              <p className="text-gray-500">
                Paste your code in the input area and click "Analyze Code" to get comprehensive insights.
              </p>
            </div>
          )}
        </div>
      </div>

      {/* Analysis History */}
      {history.length > 0 && (
        <div className="mt-8">
          <h2 className="text-xl font-semibold mb-4">Recent Analyses</h2>
          <div className="bg-white rounded-lg shadow-sm border">
            <div className="p-4 border-b border-gray-200">
              <h3 className="font-medium text-gray-900">Analysis History</h3>
            </div>
            <div className="divide-y divide-gray-200">
              {history.slice(0, 5).map((analysis, index) => (
                <div key={index} className="p-4 hover:bg-gray-50 cursor-pointer" onClick={() => setResult(analysis)}>
                  <div className="flex items-center justify-between">
                    <div>
                      <div className="font-medium text-gray-900">{analysis.language} Analysis</div>
                      <div className="text-sm text-gray-500">
                        {analysis.size} characters • Score: {analysis.quality_metrics?.overall_score?.toFixed(1) || 'N/A'}
                      </div>
                    </div>
                    <div className="text-xs text-gray-400">
                      {/* You could add timestamp here */}
                      Recent
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
} 