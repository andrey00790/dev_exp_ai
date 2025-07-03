import React, { useState, useRef } from 'react';
import { useDropzone } from 'react-dropzone';

interface CodeFile {
  name: string;
  content: string;
  language: string;
}

interface DocumentationResult {
  title: string;
  content: string;
  type: string;
  generationTime: number;
}

const LANGUAGE_OPTIONS = [
  { value: 'python', label: 'Python' },
  { value: 'javascript', label: 'JavaScript' },
  { value: 'typescript', label: 'TypeScript' },
  { value: 'java', label: 'Java' },
  { value: 'cpp', label: 'C++' },
  { value: 'csharp', label: 'C#' },
  { value: 'go', label: 'Go' },
  { value: 'rust', label: 'Rust' },
  { value: 'php', label: 'PHP' },
  { value: 'other', label: 'Other' }
];

const DOC_TYPES = [
  { value: 'readme', label: '📄 README', description: 'Project overview and setup guide' },
  { value: 'api_docs', label: '📚 API Documentation', description: 'Comprehensive API reference' },
  { value: 'technical_spec', label: '⚙️ Technical Specification', description: 'Detailed technical design' },
  { value: 'code_comments', label: '💬 Code Comments', description: 'Inline code documentation' },
  { value: 'user_guide', label: '👥 User Guide', description: 'End-user documentation' }
];

const TARGET_AUDIENCES = [
  { value: 'developers', label: 'Developers' },
  { value: 'users', label: 'End Users' },
  { value: 'stakeholders', label: 'Stakeholders' },
  { value: 'technical_writers', label: 'Technical Writers' },
  { value: 'management', label: 'Management' }
];

export default function CodeDocumentation() {
  const [codeInput, setCodeInput] = useState('');
  const [selectedLanguage, setSelectedLanguage] = useState('python');
  const [docType, setDocType] = useState('readme');
  const [targetAudience, setTargetAudience] = useState('developers');
  const [detailLevel, setDetailLevel] = useState('detailed');
  const [generating, setGenerating] = useState(false);
  const [result, setResult] = useState<DocumentationResult | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<CodeFile[]>([]);
  const [activeTab, setActiveTab] = useState<'paste' | 'upload'>('paste');

  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // File upload handling
  const onDrop = async (acceptedFiles: File[]) => {
    const newFiles: CodeFile[] = [];
    
    for (const file of acceptedFiles) {
      if (file.size > 1024 * 1024) { // 1MB limit
        alert(`File ${file.name} is too large (max 1MB)`);
        continue;
      }
      
      const content = await file.text();
      const language = detectLanguageFromFilename(file.name);
      
      newFiles.push({
        name: file.name,
        content,
        language
      });
    }
    
    setUploadedFiles(prev => [...prev, ...newFiles]);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'text/*': ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.cs', '.go', '.rs', '.php', '.rb', '.swift', '.kt']
    },
    multiple: true
  });

  const detectLanguageFromFilename = (filename: string): string => {
    const ext = filename.split('.').pop()?.toLowerCase();
    const langMap: Record<string, string> = {
      'py': 'python',
      'js': 'javascript',
      'ts': 'typescript',
      'java': 'java',
      'cpp': 'cpp',
      'c': 'cpp',
      'h': 'cpp',
      'cs': 'csharp',
      'go': 'go',
      'rs': 'rust',
      'php': 'php',
      'rb': 'ruby',
      'swift': 'swift',
      'kt': 'kotlin'
    };
    return langMap[ext || ''] || 'other';
  };

  const handleGenerate = async () => {
    if (!codeInput.trim() && uploadedFiles.length === 0) {
      alert('Please provide code input or upload files');
      return;
    }

    setGenerating(true);

    try {
      // Prepare request based on input type
      let requestData;
      
      if (activeTab === 'paste' && codeInput.trim()) {
        requestData = {
          documentation_type: docType,
          code_input: codeInput,
          target_audience: targetAudience,
          detail_level: detailLevel,
          language: selectedLanguage
        };
      } else if (uploadedFiles.length > 0) {
        // For multiple files, create a repository-like structure
        requestData = {
          documentation_type: docType,
          code_input: {
            type: 'repository',
            files: uploadedFiles.map(file => ({
              filename: file.name,
              content: file.content,
              language: file.language
            }))
          },
          target_audience: targetAudience,
          detail_level: detailLevel
        };
      }

      // Call API
      const response = await fetch('/api/v1/documentation/generate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestData)
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const data = await response.json();

      setResult({
        title: data.documentation.title,
        content: data.documentation.full_content,
        type: docType,
        generationTime: data.generation_time_seconds || 0
      });

    } catch (error) {
      console.error('Documentation generation failed:', error);
      alert('Failed to generate documentation. Please try again.');
    } finally {
      setGenerating(false);
    }
  };

  const copyToClipboard = () => {
    if (result) {
      navigator.clipboard.writeText(result.content);
      alert('Documentation copied to clipboard!');
    }
  };

  const downloadAsFile = () => {
    if (result) {
      const blob = new Blob([result.content], { type: 'text/markdown' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `${result.title.replace(/\s+/g, '_')}.md`;
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
      URL.revokeObjectURL(url);
    }
  };

  const removeFile = (index: number) => {
    setUploadedFiles(prev => prev.filter((_, i) => i !== index));
  };

  return (
    <div className="p-6 max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-3xl font-bold text-gray-900 mb-2">
          📝 Code Documentation Generator
        </h1>
        <p className="text-gray-600">
          Generate comprehensive documentation for your code automatically using AI
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Input Section */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <h2 className="text-xl font-semibold mb-4">Code Input</h2>
          
          {/* Tab Selector */}
          <div className="flex mb-4 border-b">
            <button
              onClick={() => setActiveTab('paste')}
              className={`px-4 py-2 font-medium ${
                activeTab === 'paste'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📝 Paste Code
            </button>
            <button
              onClick={() => setActiveTab('upload')}
              className={`px-4 py-2 font-medium ${
                activeTab === 'upload'
                  ? 'border-b-2 border-blue-500 text-blue-600'
                  : 'text-gray-500 hover:text-gray-700'
              }`}
            >
              📁 Upload Files
            </button>
          </div>

          {/* Code Input Area */}
          {activeTab === 'paste' ? (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Programming Language
                </label>
                <select
                  value={selectedLanguage}
                  onChange={(e) => setSelectedLanguage(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                >
                  {LANGUAGE_OPTIONS.map(lang => (
                    <option key={lang.value} value={lang.value}>
                      {lang.label}
                    </option>
                  ))}
                </select>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Source Code
                </label>
                <textarea
                  ref={textareaRef}
                  value={codeInput}
                  onChange={(e) => setCodeInput(e.target.value)}
                  placeholder="Paste your source code here..."
                  className="w-full h-64 p-4 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent font-mono text-sm"
                />
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              {/* File Upload Zone */}
              <div
                {...getRootProps()}
                className={`border-2 border-dashed rounded-lg p-8 text-center cursor-pointer transition-colors ${
                  isDragActive
                    ? 'border-blue-400 bg-blue-50'
                    : 'border-gray-300 hover:border-gray-400'
                }`}
              >
                <input {...getInputProps()} />
                <div className="text-4xl mb-4">📁</div>
                {isDragActive ? (
                  <p className="text-blue-600">Drop files here...</p>
                ) : (
                  <div>
                    <p className="text-gray-600 mb-2">
                      Drag & drop code files here, or click to select
                    </p>
                    <p className="text-sm text-gray-500">
                      Supports: .py, .js, .ts, .java, .cpp, .cs, .go, .rs, .php and more
                    </p>
                  </div>
                )}
              </div>

              {/* Uploaded Files List */}
              {uploadedFiles.length > 0 && (
                <div className="space-y-2">
                  <h3 className="font-medium text-gray-700">Uploaded Files:</h3>
                  {uploadedFiles.map((file, index) => (
                    <div key={index} className="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                      <div className="flex items-center space-x-3">
                        <span className="text-blue-600 font-mono text-sm">
                          {file.language}
                        </span>
                        <span className="font-medium">{file.name}</span>
                        <span className="text-sm text-gray-500">
                          ({file.content.length} chars)
                        </span>
                      </div>
                      <button
                        onClick={() => removeFile(index)}
                        className="text-red-500 hover:text-red-700"
                      >
                        ✕
                      </button>
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}

          {/* Documentation Options */}
          <div className="mt-6 space-y-4">
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Documentation Type
              </label>
              <div className="grid grid-cols-1 gap-2">
                {DOC_TYPES.map(type => (
                  <label key={type.value} className="flex items-center p-3 border rounded-lg cursor-pointer hover:bg-gray-50">
                    <input
                      type="radio"
                      name="docType"
                      value={type.value}
                      checked={docType === type.value}
                      onChange={(e) => setDocType(e.target.value)}
                      className="mr-3"
                    />
                    <div>
                      <div className="font-medium">{type.label}</div>
                      <div className="text-sm text-gray-500">{type.description}</div>
                    </div>
                  </label>
                ))}
              </div>
            </div>

            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Target Audience
                </label>
                <select
                  value={targetAudience}
                  onChange={(e) => setTargetAudience(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  {TARGET_AUDIENCES.map(audience => (
                    <option key={audience.value} value={audience.value}>
                      {audience.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Detail Level
                </label>
                <select
                  value={detailLevel}
                  onChange={(e) => setDetailLevel(e.target.value)}
                  className="w-full p-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                >
                  <option value="brief">Brief</option>
                  <option value="detailed">Detailed</option>
                  <option value="comprehensive">Comprehensive</option>
                </select>
              </div>
            </div>
          </div>

          {/* Generate Button */}
          <button
            onClick={handleGenerate}
            disabled={generating || (!codeInput.trim() && uploadedFiles.length === 0)}
            className="w-full mt-6 px-6 py-3 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {generating ? '🔄 Generating Documentation...' : '🚀 Generate Documentation'}
          </button>
        </div>

        {/* Output Section */}
        <div className="bg-white rounded-lg shadow-sm border p-6">
          <div className="flex items-center justify-between mb-4">
            <h2 className="text-xl font-semibold">Generated Documentation</h2>
            {result && (
              <div className="flex space-x-2">
                <button
                  onClick={copyToClipboard}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
                >
                  📋 Copy
                </button>
                <button
                  onClick={downloadAsFile}
                  className="px-3 py-1 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
                >
                  💾 Download
                </button>
              </div>
            )}
          </div>

          {!result ? (
            <div className="h-96 flex items-center justify-center text-gray-500 border-2 border-dashed border-gray-200 rounded-lg">
              <div className="text-center">
                <div className="text-4xl mb-4">📄</div>
                <p>Generated documentation will appear here</p>
                <p className="text-sm mt-2">Select code input and documentation type to get started</p>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                <div className="flex items-center space-x-2">
                  <span className="text-green-600">✅</span>
                  <span className="font-medium text-green-800">{result.title}</span>
                </div>
                <span className="text-sm text-green-600">
                  Generated in {result.generationTime}s
                </span>
              </div>
              
              <div className="border rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b">
                  <span className="text-sm font-medium text-gray-700">
                    {DOC_TYPES.find(t => t.value === result.type)?.label} - Markdown
                  </span>
                </div>
                <div className="p-4 max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm font-mono text-gray-800">
                    {result.content}
                  </pre>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 