import React, { useState } from 'react';
import { SparklesIcon, DocumentTextIcon, CloudArrowUpIcon } from '@heroicons/react/24/outline';
import RFCTemplates from './RFCTemplates';
import FileUpload from './FileUpload';
import RFCExport from './RFCExport';
import RFCGenerator from './RFCGenerator';

type GenerationMode = 'interactive' | 'template' | 'file-analysis';

interface RFCTemplate {
  id: string;
  name: string;
  description: string;
  category: string;
  template: string;
}

export default function EnhancedRFCGenerator() {
  const [mode, setMode] = useState<GenerationMode>('interactive');
  const [selectedTemplate, setSelectedTemplate] = useState<RFCTemplate | null>(null);
  const [uploadedFiles, setUploadedFiles] = useState<File[]>([]);
  const [generatedRFC, setGeneratedRFC] = useState<string>('');
  const [rfcTitle, setRfcTitle] = useState<string>('Generated RFC');
  const [showExport, setShowExport] = useState(false);

  const modes = [
    {
      id: 'interactive' as GenerationMode,
      name: 'Interactive Generation',
      description: 'AI asks smart questions to create a comprehensive RFC',
      icon: SparklesIcon,
      recommended: true,
    },
    {
      id: 'template' as GenerationMode,
      name: 'Template-based',
      description: 'Start with a pre-built template and customize',
      icon: DocumentTextIcon,
      recommended: false,
    },
    {
      id: 'file-analysis' as GenerationMode,
      name: 'Code Analysis',
      description: 'Upload code files for AI analysis and RFC generation',
      icon: CloudArrowUpIcon,
      recommended: false,
    },
  ];

  const handleTemplateSelect = (template: RFCTemplate) => {
    setSelectedTemplate(template);
    setRfcTitle(`RFC: ${template.name}`);
  };

  const handleFilesSelected = (files: File[]) => {
    setUploadedFiles(files);
  };

  const handleRFCGenerated = (rfc: any) => {
    setGeneratedRFC(rfc.content || rfc);
    setRfcTitle(rfc.title || 'Generated RFC');
    setShowExport(true);
  };

  const generateFromTemplate = () => {
    if (!selectedTemplate) return;
    
    const customizedRFC = selectedTemplate.template.replace(
      /\[.*?\]/g, 
      (match) => `${match} - Please customize this section`
    );
    
    setGeneratedRFC(customizedRFC);
    setRfcTitle(`RFC: ${selectedTemplate.name}`);
    setShowExport(true);
  };

  const generateFromFiles = async () => {
    if (uploadedFiles.length === 0) return;
    
    // Simulate file analysis and RFC generation
    const fileNames = uploadedFiles.map(f => f.name).join(', ');
    const analysisRFC = `# RFC: Code Analysis Results

## Summary
Analysis of uploaded files: ${fileNames}

## Files Analyzed
${uploadedFiles.map(file => `- ${file.name} (${Math.round(file.size / 1024)}KB)`).join('\n')}

## Code Structure Analysis
Based on the uploaded files, the following structure was identified:

### Key Components
- File analysis would be performed here
- Architecture patterns would be identified
- Dependencies would be mapped

### Recommendations
- Code quality improvements
- Architecture suggestions
- Best practices implementation

## Implementation Plan
1. **Phase 1**: Code review and analysis
2. **Phase 2**: Architecture improvements
3. **Phase 3**: Implementation of recommendations

## Next Steps
- Detailed code review
- Architecture documentation
- Implementation planning
`;

    setGeneratedRFC(analysisRFC);
    setRfcTitle('RFC: Code Analysis Results');
    setShowExport(true);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <div className="bg-gradient-to-r from-blue-600 to-purple-600 text-white">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
          <div className="text-center">
            <h1 className="text-4xl font-bold mb-4">Enhanced RFC Generator</h1>
            <p className="text-xl text-blue-100 mb-8 max-w-3xl mx-auto">
              Create professional RFC documents with AI assistance, templates, and code analysis.
            </p>
            
            {/* Mode Selection */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 max-w-4xl mx-auto">
              {modes.map((modeOption) => {
                const Icon = modeOption.icon;
                return (
                  <button
                    key={modeOption.id}
                    onClick={() => setMode(modeOption.id)}
                    className={`relative p-6 rounded-lg border-2 transition-all ${
                      mode === modeOption.id
                        ? 'border-white bg-white/10'
                        : 'border-white/30 hover:border-white/50'
                    }`}
                  >
                    {modeOption.recommended && (
                      <div className="absolute -top-2 -right-2 bg-yellow-400 text-yellow-900 text-xs font-bold px-2 py-1 rounded-full">
                        Recommended
                      </div>
                    )}
                    <Icon className="h-8 w-8 mx-auto mb-3" />
                    <h3 className="font-semibold mb-2">{modeOption.name}</h3>
                    <p className="text-sm text-blue-100">{modeOption.description}</p>
                  </button>
                );
              })}
            </div>
          </div>
        </div>
      </div>

      {/* Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Interactive Mode */}
        {mode === 'interactive' && (
          <div>
            <div className="text-center mb-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Interactive RFC Generation</h2>
              <p className="text-gray-600">
                Our AI will ask you smart questions to create a comprehensive RFC document.
              </p>
            </div>
            <RFCGenerator onRFCGenerated={handleRFCGenerated} />
          </div>
        )}

        {/* Template Mode */}
        {mode === 'template' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Template-based RFC Generation</h2>
              <p className="text-gray-600">
                Choose from professional templates and customize them for your needs.
              </p>
            </div>

            {!selectedTemplate ? (
              <RFCTemplates 
                onTemplateSelect={handleTemplateSelect}
                selectedTemplateId={selectedTemplate?.id}
              />
            ) : (
              <div className="space-y-6">
                {/* Selected Template Info */}
                <div className="bg-white rounded-lg shadow-lg p-6">
                  <div className="flex items-center justify-between mb-4">
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900">
                        Selected Template: {selectedTemplate.name}
                      </h3>
                      <p className="text-gray-600">{selectedTemplate.description}</p>
                    </div>
                    <button
                      onClick={() => setSelectedTemplate(null)}
                      className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                    >
                      Change Template
                    </button>
                  </div>
                  
                  <div className="border-t pt-4">
                    <h4 className="font-medium text-gray-900 mb-2">Template Preview:</h4>
                    <div className="bg-gray-50 p-4 rounded-lg max-h-64 overflow-y-auto">
                      <pre className="text-sm text-gray-700 whitespace-pre-wrap">
                        {selectedTemplate.template.substring(0, 500)}...
                      </pre>
                    </div>
                  </div>

                  <div className="mt-6">
                    <button
                      onClick={generateFromTemplate}
                      className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium transition-colors"
                    >
                      Generate RFC from Template
                    </button>
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* File Analysis Mode */}
        {mode === 'file-analysis' && (
          <div className="space-y-8">
            <div className="text-center">
              <h2 className="text-2xl font-bold text-gray-900 mb-4">Code Analysis RFC Generation</h2>
              <p className="text-gray-600">
                Upload your code files and let AI analyze them to generate comprehensive RFC documents.
              </p>
            </div>

            <div className="bg-white rounded-lg shadow-lg p-6">
              <FileUpload 
                onFilesSelected={handleFilesSelected}
                acceptedTypes={['.js', '.ts', '.jsx', '.tsx', '.py', '.java', '.cpp', '.c', '.cs', '.php', '.rb', '.go', '.rs', '.md', '.txt']}
                maxFiles={10}
                maxSizeBytes={50 * 1024 * 1024} // 50MB
              />

              {uploadedFiles.length > 0 && (
                <div className="mt-6">
                  <button
                    onClick={generateFromFiles}
                    className="w-full bg-blue-600 hover:bg-blue-700 text-white py-3 px-4 rounded-lg font-medium transition-colors"
                  >
                    Analyze Files and Generate RFC
                  </button>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Export Section */}
        {showExport && generatedRFC && (
          <div className="mt-12">
            <RFCExport 
              rfcContent={generatedRFC}
              rfcTitle={rfcTitle}
              onExport={(format) => {
                console.log(`RFC exported as ${format}`);
              }}
            />
          </div>
        )}
      </div>
    </div>
  );
} 