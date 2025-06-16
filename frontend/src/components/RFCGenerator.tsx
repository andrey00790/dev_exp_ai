import React, { useState, useEffect } from 'react';
import { DocumentTextIcon, QuestionMarkCircleIcon, CheckCircleIcon, ArrowRightIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { chatApi, AIQuestion } from '../api/chatApi';

interface RFCGeneratorProps {
  initialRequest?: string;
  onRFCGenerated?: (rfc: any) => void;
}

interface GenerationSession {
  session_id: string;
  questions: AIQuestion[];
  answers: Record<string, string>;
  is_ready_to_generate: boolean;
  current_question_index: number;
}

export default function RFCGenerator({ initialRequest = '', onRFCGenerated }: RFCGeneratorProps) {
  const [step, setStep] = useState<'input' | 'questions' | 'generating' | 'preview'>('input');
  const [request, setRequest] = useState(initialRequest);
  const [session, setSession] = useState<GenerationSession | null>(null);
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [generatedRFC, setGeneratedRFC] = useState<string>('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const taskTypes = [
    { value: 'new_feature', label: 'New Feature', description: 'Design a completely new feature or system' },
    { value: 'modify_existing', label: 'Modify Existing', description: 'Improve or modify an existing system' },
    { value: 'analyze_current', label: 'Analyze Current', description: 'Analyze and optimize current solution' },
  ];

  const [selectedTaskType, setSelectedTaskType] = useState<'new_feature' | 'modify_existing' | 'analyze_current'>('new_feature');

  const startGeneration = async () => {
    if (!request.trim()) return;

    setIsLoading(true);
    setError(null);

    try {
      const response = await chatApi.generateRFC(request, selectedTaskType);
      
      if (response.metadata?.rfcData?.session_id && response.metadata.rfcData.questions) {
        setSession({
          session_id: response.metadata.rfcData.session_id,
          questions: response.metadata.rfcData.questions,
          answers: {},
          is_ready_to_generate: response.metadata.rfcData.is_ready_to_generate || false,
          current_question_index: 0,
        });
        setStep('questions');
      } else {
        // Direct RFC generation without questions
        setGeneratedRFC(response.content);
        setStep('preview');
      }
    } catch (error) {
      console.error('RFC Generation Error:', error);
      setError(error instanceof Error ? error.message : 'Failed to start RFC generation');
    } finally {
      setIsLoading(false);
    }
  };

  const answerQuestion = async () => {
    if (!session || !currentAnswer.trim()) return;

    const currentQuestion = session.questions[session.current_question_index];
    const updatedAnswers = {
      ...session.answers,
      [currentQuestion.id]: currentAnswer,
    };

    setSession({
      ...session,
      answers: updatedAnswers,
      current_question_index: session.current_question_index + 1,
    });

    setCurrentAnswer('');

    // Check if we've answered all questions
    if (session.current_question_index + 1 >= session.questions.length) {
      // All questions answered, generate RFC
      await generateFinalRFC(session.session_id, updatedAnswers);
    }
  };

  const generateFinalRFC = async (sessionId: string, answers: Record<string, string>) => {
    setIsLoading(true);
    setStep('generating');

    try {
      // In a real implementation, we would call the finalize endpoint
      // For now, we'll simulate RFC generation
      await new Promise(resolve => setTimeout(resolve, 3000)); // Simulate generation time

      const mockRFC = `# RFC: ${request}

## Summary

${request}

## Background

Based on your answers, this RFC addresses the following requirements:

${Object.entries(answers).map(([questionId, answer]) => 
  `- **${questionId}**: ${answer}`
).join('\n')}

## Proposed Solution

[Generated based on your requirements...]

## Implementation Plan

1. **Phase 1**: Initial setup and core functionality
2. **Phase 2**: Advanced features and optimization
3. **Phase 3**: Testing and deployment

## Considerations

- Security implications
- Performance requirements
- Scalability concerns
- Maintenance overhead

## Next Steps

- [ ] Technical review
- [ ] Architecture approval
- [ ] Implementation planning
- [ ] Resource allocation
`;

      setGeneratedRFC(mockRFC);
      setStep('preview');
      
      if (onRFCGenerated) {
        onRFCGenerated({ content: mockRFC, session_id: sessionId });
      }
    } catch (error) {
      setError(error instanceof Error ? error.message : 'Failed to generate RFC');
    } finally {
      setIsLoading(false);
    }
  };

  const resetGenerator = () => {
    setStep('input');
    setRequest('');
    setSession(null);
    setCurrentAnswer('');
    setGeneratedRFC('');
    setError(null);
  };

  const currentQuestion = session?.questions[session.current_question_index];
  const progress = session ? ((session.current_question_index) / session.questions.length) * 100 : 0;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg overflow-hidden">
        {/* Header */}
        <div className="bg-gradient-to-r from-blue-600 to-purple-600 px-6 py-4">
          <div className="flex items-center space-x-3">
            <DocumentTextIcon className="h-8 w-8 text-white" />
            <div>
              <h2 className="text-2xl font-bold text-white">RFC Generator</h2>
              <p className="text-blue-100">Create professional RFC documents with AI assistance</p>
            </div>
          </div>
        </div>

        {/* Progress Bar */}
        {step === 'questions' && session && (
          <div className="bg-gray-50 px-6 py-3">
            <div className="flex items-center justify-between mb-2">
              <span className="text-sm font-medium text-gray-700">
                Question {session.current_question_index + 1} of {session.questions.length}
              </span>
              <span className="text-sm text-gray-500">{Math.round(progress)}% complete</span>
            </div>
            <div className="w-full bg-gray-200 rounded-full h-2">
              <div 
                className="bg-blue-600 h-2 rounded-full transition-all duration-300"
                style={{ width: `${progress}%` }}
              />
            </div>
          </div>
        )}

        <div className="p-6">
          {error && (
            <div className="mb-6 p-4 bg-red-50 border border-red-200 rounded-lg">
              <p className="text-red-600">{error}</p>
            </div>
          )}

          {/* Step 1: Initial Input */}
          {step === 'input' && (
            <div className="space-y-6">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Task Type
                </label>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {taskTypes.map((type) => (
                    <button
                      key={type.value}
                      onClick={() => setSelectedTaskType(type.value as any)}
                      className={`p-4 border rounded-lg text-left transition-colors ${
                        selectedTaskType === type.value
                          ? 'border-blue-500 bg-blue-50'
                          : 'border-gray-200 hover:border-gray-300'
                      }`}
                    >
                      <h3 className="font-medium text-gray-900">{type.label}</h3>
                      <p className="text-sm text-gray-500 mt-1">{type.description}</p>
                    </button>
                  ))}
                </div>
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Describe what you want to create
                </label>
                <textarea
                  value={request}
                  onChange={(e) => setRequest(e.target.value)}
                  placeholder="e.g., Create a user authentication system with OAuth 2.0 support..."
                  className="w-full h-32 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
              </div>

              <button
                onClick={startGeneration}
                disabled={!request.trim() || isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-medium transition-colors flex items-center justify-center space-x-2"
              >
                {isLoading ? (
                  <>
                    <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white" />
                    <span>Starting generation...</span>
                  </>
                ) : (
                  <>
                    <ArrowRightIcon className="h-5 w-5" />
                    <span>Start RFC Generation</span>
                  </>
                )}
              </button>
            </div>
          )}

          {/* Step 2: Questions */}
          {step === 'questions' && session && currentQuestion && (
            <div className="space-y-6">
              <div className="bg-blue-50 p-4 rounded-lg">
                <div className="flex items-start space-x-3">
                  <QuestionMarkCircleIcon className="h-6 w-6 text-blue-600 mt-1" />
                  <div className="flex-1">
                    <h3 className="font-medium text-blue-900 mb-2">
                      {currentQuestion.question}
                    </h3>
                    {currentQuestion.context && (
                      <p className="text-sm text-blue-700">{currentQuestion.context}</p>
                    )}
                  </div>
                </div>
              </div>

              <div>
                {currentQuestion.question_type === 'choice' && currentQuestion.options ? (
                  <div className="space-y-2">
                    {currentQuestion.options.map((option, index) => (
                      <button
                        key={index}
                        onClick={() => setCurrentAnswer(option)}
                        className={`w-full p-3 text-left border rounded-lg transition-colors ${
                          currentAnswer === option
                            ? 'border-blue-500 bg-blue-50'
                            : 'border-gray-200 hover:border-gray-300'
                        }`}
                      >
                        {option}
                      </button>
                    ))}
                  </div>
                ) : currentQuestion.question_type === 'multiple_choice' && currentQuestion.options ? (
                  <div className="space-y-2">
                    {currentQuestion.options.map((option, index) => (
                      <label key={index} className="flex items-center space-x-3 p-3 border rounded-lg hover:bg-gray-50">
                        <input
                          type="checkbox"
                          checked={currentAnswer.split(',').includes(option)}
                          onChange={(e) => {
                            const selected = currentAnswer.split(',').filter(Boolean);
                            if (e.target.checked) {
                              setCurrentAnswer([...selected, option].join(','));
                            } else {
                              setCurrentAnswer(selected.filter(s => s !== option).join(','));
                            }
                          }}
                          className="rounded border-gray-300 text-blue-600 focus:ring-blue-500"
                        />
                        <span>{option}</span>
                      </label>
                    ))}
                  </div>
                ) : (
                  <textarea
                    value={currentAnswer}
                    onChange={(e) => setCurrentAnswer(e.target.value)}
                    placeholder={currentQuestion.placeholder || 'Enter your answer...'}
                    className="w-full h-24 px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                )}
              </div>

              <div className="flex space-x-4">
                <button
                  onClick={answerQuestion}
                  disabled={!currentAnswer.trim()}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg font-medium transition-colors"
                >
                  {session.current_question_index + 1 >= session.questions.length ? 'Generate RFC' : 'Next Question'}
                </button>
                
                <button
                  onClick={resetGenerator}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Start Over
                </button>
              </div>
            </div>
          )}

          {/* Step 3: Generating */}
          {step === 'generating' && (
            <div className="text-center py-12">
              <div className="animate-spin rounded-full h-16 w-16 border-b-2 border-blue-600 mx-auto mb-4" />
              <h3 className="text-lg font-medium text-gray-900 mb-2">Generating your RFC...</h3>
              <p className="text-gray-500">This may take a few moments while we create a professional RFC document.</p>
            </div>
          )}

          {/* Step 4: Preview */}
          {step === 'preview' && generatedRFC && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-2">
                  <CheckCircleIcon className="h-6 w-6 text-green-600" />
                  <h3 className="text-lg font-medium text-gray-900">RFC Generated Successfully!</h3>
                </div>
                <button
                  onClick={resetGenerator}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors"
                >
                  Generate Another
                </button>
              </div>

              <div className="border border-gray-200 rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b border-gray-200">
                  <h4 className="font-medium text-gray-900">RFC Preview</h4>
                </div>
                <div className="p-6 max-h-96 overflow-y-auto">
                  <ReactMarkdown className="prose prose-sm max-w-none">
                    {generatedRFC}
                  </ReactMarkdown>
                </div>
              </div>

              <div className="flex space-x-4">
                <button className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                  Download RFC
                </button>
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium transition-colors">
                  Share RFC
                </button>
                <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50 transition-colors">
                  Edit RFC
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 