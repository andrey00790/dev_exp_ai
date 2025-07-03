import React, { useState, useEffect } from 'react';
import { 
  Bot, FileText, Code, MessageSquare, Zap, Settings, Download, 
  Clock, DollarSign, Cpu, BarChart3, RefreshCw 
} from 'lucide-react';

interface LLMResponse {
  content: string;
  provider: string;
  model: string;
  tokens_used: number;
  cost_usd: number;
  response_time: number;
  metadata: Record<string, any>;
}

interface LLMStats {
  status: string;
  service_metrics: {
    total_requests: number;
    total_cost_usd: number;
    avg_cost_per_request: number;
  };
  router_stats: {
    routing_strategy: string;
    providers: Record<string, any>;
  };
  providers_available: number;
}

type OperationType = 'text' | 'rfc' | 'documentation' | 'qa';

const LLMOperations: React.FC = () => {
  const [activeTab, setActiveTab] = useState<OperationType>('text');
  const [isGenerating, setIsGenerating] = useState(false);
  const [result, setResult] = useState<LLMResponse | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [stats, setStats] = useState<LLMStats | null>(null);

  // Text Generation State
  const [textPrompt, setTextPrompt] = useState('');
  const [systemPrompt, setSystemPrompt] = useState('');
  const [maxTokens, setMaxTokens] = useState(2000);
  const [temperature, setTemperature] = useState(0.7);

  // RFC Generation State
  const [taskDescription, setTaskDescription] = useState('');
  const [projectContext, setProjectContext] = useState('');
  const [technicalRequirements, setTechnicalRequirements] = useState('');

  // Documentation State
  const [code, setCode] = useState('');
  const [language, setLanguage] = useState('python');
  const [docType, setDocType] = useState('comprehensive');

  // Q&A State
  const [question, setQuestion] = useState('');
  const [context, setContext] = useState('');
  const [qaMaxTokens, setQaMaxTokens] = useState(1000);

  useEffect(() => {
    loadStats();
  }, []);

  const loadStats = async () => {
    try {
      const token = localStorage.getItem('token');
      const response = await fetch('/api/v1/llm/stats', {
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
      });

      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to load LLM stats:', err);
    }
  };

  const generateText = async () => {
    if (!textPrompt.trim()) return;

    setIsGenerating(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const requestData = {
        prompt: textPrompt,
        system_prompt: systemPrompt || undefined,
        max_tokens: maxTokens,
        temperature: temperature,
      };

      const response = await fetch('/api/v1/llm/generate', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data: LLMResponse = await response.json();
        setResult(data);
        loadStats(); // Refresh stats
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Generation failed');
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('Generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateRFC = async () => {
    if (!taskDescription.trim()) return;

    setIsGenerating(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const requestData = {
        task_description: taskDescription,
        project_context: projectContext || undefined,
        technical_requirements: technicalRequirements || undefined,
      };

      const response = await fetch('/api/v1/llm/generate/rfc', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data: LLMResponse = await response.json();
        setResult(data);
        loadStats();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'RFC generation failed');
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('RFC generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const generateDocumentation = async () => {
    if (!code.trim()) return;

    setIsGenerating(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const requestData = {
        code: code,
        language: language,
        doc_type: docType,
      };

      const response = await fetch('/api/v1/llm/generate/documentation', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data: LLMResponse = await response.json();
        setResult(data);
        loadStats();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Documentation generation failed');
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('Documentation generation error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const answerQuestion = async () => {
    if (!question.trim()) return;

    setIsGenerating(true);
    setError(null);

    try {
      const token = localStorage.getItem('token');
      const requestData = {
        question: question,
        context: context || undefined,
        max_tokens: qaMaxTokens,
      };

      const response = await fetch('/api/v1/llm/answer', {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData),
      });

      if (response.ok) {
        const data: LLMResponse = await response.json();
        setResult(data);
        loadStats();
      } else {
        const errorData = await response.json();
        setError(errorData.detail || 'Question answering failed');
      }
    } catch (err) {
      setError('Network error occurred');
      console.error('Q&A error:', err);
    } finally {
      setIsGenerating(false);
    }
  };

  const downloadResult = () => {
    if (!result) return;

    const content = `# Generated Content

**Type**: ${activeTab}
**Provider**: ${result.provider}
**Model**: ${result.model}
**Tokens Used**: ${result.tokens_used}
**Cost**: $${result.cost_usd.toFixed(4)}
**Response Time**: ${result.response_time.toFixed(2)}s

## Content

${result.content}

---
Generated by AI Assistant on ${new Date().toLocaleString()}
`;

    const blob = new Blob([content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `llm_${activeTab}_${Date.now()}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleGenerate = () => {
    switch (activeTab) {
      case 'text':
        generateText();
        break;
      case 'rfc':
        generateRFC();
        break;
      case 'documentation':
        generateDocumentation();
        break;
      case 'qa':
        answerQuestion();
        break;
    }
  };

  const canGenerate = () => {
    switch (activeTab) {
      case 'text':
        return textPrompt.trim().length > 0;
      case 'rfc':
        return taskDescription.trim().length > 0;
      case 'documentation':
        return code.trim().length > 0;
      case 'qa':
        return question.trim().length > 0;
      default:
        return false;
    }
  };

  const tabs = [
    { id: 'text' as OperationType, label: 'Text Generation', icon: Bot },
    { id: 'rfc' as OperationType, label: 'RFC Generation', icon: FileText },
    { id: 'documentation' as OperationType, label: 'Documentation', icon: Code },
    { id: 'qa' as OperationType, label: 'Q&A', icon: MessageSquare },
  ];

  return (
    <div className="max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="text-center">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          <Bot className="inline-block w-8 h-8 mr-2 text-purple-600" />
          LLM Operations
        </h1>
        <p className="text-gray-600">
          Generate text, documentation, RFCs, and get answers using advanced AI models
        </p>
      </div>

      {/* Stats Dashboard */}
      {stats && (
        <div className="bg-white rounded-lg shadow-md p-6 border">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold flex items-center">
              <BarChart3 className="w-5 h-5 mr-2" />
              Service Statistics
            </h3>
            <button
              onClick={loadStats}
              className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
            >
              <RefreshCw className="w-4 h-4" />
              Refresh
            </button>
          </div>
          
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {stats.service_metrics.total_requests}
              </div>
              <div className="text-sm text-gray-600">Total Requests</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                ${stats.service_metrics.total_cost_usd.toFixed(4)}
              </div>
              <div className="text-sm text-gray-600">Total Cost</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {stats.providers_available}
              </div>
              <div className="text-sm text-gray-600">Providers Available</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {stats.router_stats.routing_strategy}
              </div>
              <div className="text-sm text-gray-600">Routing Strategy</div>
            </div>
          </div>
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Input Panel */}
        <div className="lg:col-span-2 space-y-6">
          {/* Tab Navigation */}
          <div className="bg-white rounded-lg shadow-md border">
            <div className="border-b border-gray-200">
              <nav className="-mb-px flex space-x-8 px-6">
                {tabs.map(tab => {
                  const Icon = tab.icon;
                  return (
                    <button
                      key={tab.id}
                      onClick={() => setActiveTab(tab.id)}
                      className={`py-4 px-1 border-b-2 font-medium text-sm flex items-center gap-2 ${
                        activeTab === tab.id
                          ? 'border-purple-500 text-purple-600'
                          : 'border-transparent text-gray-500 hover:text-gray-700 hover:border-gray-300'
                      }`}
                    >
                      <Icon className="w-4 h-4" />
                      {tab.label}
                    </button>
                  );
                })}
              </nav>
            </div>

            <div className="p-6">
              {/* Text Generation */}
              {activeTab === 'text' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      System Prompt (Optional)
                    </label>
                    <textarea
                      value={systemPrompt}
                      onChange={(e) => setSystemPrompt(e.target.value)}
                      placeholder="You are a helpful assistant..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Prompt *
                    </label>
                    <textarea
                      value={textPrompt}
                      onChange={(e) => setTextPrompt(e.target.value)}
                      placeholder="Enter your prompt here..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={4}
                    />
                  </div>
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Max Tokens
                      </label>
                      <input
                        type="number"
                        value={maxTokens}
                        onChange={(e) => setMaxTokens(Number(e.target.value))}
                        min={1}
                        max={8000}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      />
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Temperature
                      </label>
                      <input
                        type="number"
                        value={temperature}
                        onChange={(e) => setTemperature(Number(e.target.value))}
                        min={0}
                        max={1}
                        step={0.1}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      />
                    </div>
                  </div>
                </div>
              )}

              {/* RFC Generation */}
              {activeTab === 'rfc' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Task Description *
                    </label>
                    <textarea
                      value={taskDescription}
                      onChange={(e) => setTaskDescription(e.target.value)}
                      placeholder="Describe the task or feature to be implemented..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Project Context
                    </label>
                    <textarea
                      value={projectContext}
                      onChange={(e) => setProjectContext(e.target.value)}
                      placeholder="Provide context about your project..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Technical Requirements
                    </label>
                    <textarea
                      value={technicalRequirements}
                      onChange={(e) => setTechnicalRequirements(e.target.value)}
                      placeholder="List technical requirements and constraints..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={2}
                    />
                  </div>
                </div>
              )}

              {/* Documentation Generation */}
              {activeTab === 'documentation' && (
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Language
                      </label>
                      <select
                        value={language}
                        onChange={(e) => setLanguage(e.target.value)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      >
                        <option value="python">Python</option>
                        <option value="javascript">JavaScript</option>
                        <option value="typescript">TypeScript</option>
                        <option value="java">Java</option>
                        <option value="go">Go</option>
                        <option value="rust">Rust</option>
                        <option value="cpp">C++</option>
                      </select>
                    </div>
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">
                        Documentation Type
                      </label>
                      <select
                        value={docType}
                        onChange={(e) => setDocType(e.target.value)}
                        className="w-full border border-gray-300 rounded-lg px-3 py-2"
                      >
                        <option value="brief">Brief</option>
                        <option value="comprehensive">Comprehensive</option>
                        <option value="api">API Reference</option>
                      </select>
                    </div>
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Code *
                    </label>
                    <textarea
                      value={code}
                      onChange={(e) => setCode(e.target.value)}
                      placeholder="Paste your code here..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 font-mono text-sm resize-none"
                      rows={8}
                    />
                  </div>
                </div>
              )}

              {/* Q&A */}
              {activeTab === 'qa' && (
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Question *
                    </label>
                    <textarea
                      value={question}
                      onChange={(e) => setQuestion(e.target.value)}
                      placeholder="Ask your question..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={2}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Context (Optional)
                    </label>
                    <textarea
                      value={context}
                      onChange={(e) => setContext(e.target.value)}
                      placeholder="Provide relevant context to help answer the question..."
                      className="w-full border border-gray-300 rounded-lg px-3 py-2 resize-none"
                      rows={3}
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">
                      Max Tokens
                    </label>
                    <input
                      type="number"
                      value={qaMaxTokens}
                      onChange={(e) => setQaMaxTokens(Number(e.target.value))}
                      min={50}
                      max={4000}
                      className="w-full border border-gray-300 rounded-lg px-3 py-2"
                    />
                  </div>
                </div>
              )}

              {/* Generate Button */}
              <div className="pt-4 border-t border-gray-200">
                <button
                  onClick={handleGenerate}
                  disabled={isGenerating || !canGenerate()}
                  className="w-full bg-purple-600 hover:bg-purple-700 disabled:bg-gray-400 text-white px-4 py-3 rounded-lg font-medium flex items-center justify-center gap-2"
                >
                  {isGenerating ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                      Generating...
                    </>
                  ) : (
                    <>
                      <Zap className="w-5 h-5" />
                      Generate
                    </>
                  )}
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Results Panel */}
        <div className="space-y-6">
          {/* Error Display */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-4">
              <div className="text-red-800">{error}</div>
            </div>
          )}

          {/* Result Display */}
          {result && (
            <div className="bg-white rounded-lg shadow-md border">
              <div className="p-4 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <h3 className="text-lg font-semibold">Generated Content</h3>
                  <button
                    onClick={downloadResult}
                    className="text-blue-600 hover:text-blue-800 flex items-center gap-1"
                  >
                    <Download className="w-4 h-4" />
                    Download
                  </button>
                </div>
                
                {/* Metrics */}
                <div className="grid grid-cols-2 gap-4 mt-4 text-sm">
                  <div className="flex items-center gap-2">
                    <Cpu className="w-4 h-4 text-gray-500" />
                    <span>{result.provider}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-gray-500" />
                    <span>{result.response_time.toFixed(2)}s</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Settings className="w-4 h-4 text-gray-500" />
                    <span>{result.tokens_used} tokens</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-gray-500" />
                    <span>${result.cost_usd.toFixed(4)}</span>
                  </div>
                </div>
              </div>
              
              <div className="p-4">
                <div className="prose prose-sm max-w-none">
                  <pre className="whitespace-pre-wrap text-sm text-gray-800 leading-relaxed">
                    {result.content}
                  </pre>
                </div>
              </div>
            </div>
          )}

          {/* Getting Started */}
          {!result && !isGenerating && (
            <div className="bg-gray-50 rounded-lg border p-6 text-center">
              <Bot className="w-12 h-12 text-gray-400 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Ready to Generate</h3>
              <p className="text-gray-600 text-sm">
                Fill in the form and click Generate to create content using AI.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default LLMOperations; 