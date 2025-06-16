import React, { useState } from 'react';
import { chatApi } from '../api/chatApi';

interface Question {
  id: string;
  question: string;
  question_type: string;
  options?: string[];
  is_required: boolean;
  context?: string;
  placeholder?: string;
}

export default function RFCDemo() {
  const [step, setStep] = useState<'input' | 'questions' | 'generating' | 'result'>('input');
  const [request, setRequest] = useState('');
  const [sessionId, setSessionId] = useState('');
  const [questions, setQuestions] = useState<Question[]>([]);
  const [currentQuestionIndex, setCurrentQuestionIndex] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({});
  const [currentAnswer, setCurrentAnswer] = useState('');
  const [result, setResult] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const startGeneration = async () => {
    if (!request.trim()) return;
    
    setIsLoading(true);
    setError('');
    
    try {
      const response = await chatApi.generateRFC(request, 'new_feature');
      console.log('RFC Response:', response);
      
      if (response.metadata?.rfcData?.questions && response.metadata.rfcData.questions.length > 0) {
        setSessionId(response.metadata.rfcData.session_id || '');
        setQuestions(response.metadata.rfcData.questions);
        setCurrentQuestionIndex(0);
        setStep('questions');
      } else {
        setResult(response.content);
        setStep('result');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate RFC');
    } finally {
      setIsLoading(false);
    }
  };

  const answerQuestion = () => {
    if (!currentAnswer.trim()) return;
    
    const currentQuestion = questions[currentQuestionIndex];
    const newAnswers = { ...answers, [currentQuestion.id]: currentAnswer };
    setAnswers(newAnswers);
    setCurrentAnswer('');
    
    if (currentQuestionIndex + 1 < questions.length) {
      setCurrentQuestionIndex(currentQuestionIndex + 1);
    } else {
      // All questions answered, generate final RFC
      generateFinalRFC(newAnswers);
    }
  };

  const generateFinalRFC = async (finalAnswers: Record<string, string>) => {
    setStep('generating');
    setIsLoading(true);
    
    try {
      // Simulate RFC generation (in real app, call finalize endpoint)
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const mockRFC = `# RFC: ${request}

## Summary
${request}

## Requirements Analysis
Based on your answers:

${Object.entries(finalAnswers).map(([questionId, answer]) => {
  const question = questions.find(q => q.id === questionId);
  return `**${question?.question}**: ${answer}`;
}).join('\n\n')}

## Proposed Solution
[Generated based on requirements...]

## Implementation Plan
1. Phase 1: Core authentication
2. Phase 2: OAuth 2.0 integration
3. Phase 3: Security hardening

## Next Steps
- Technical review
- Implementation planning
`;

      setResult(mockRFC);
      setStep('result');
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to generate final RFC');
    } finally {
      setIsLoading(false);
    }
  };

  const reset = () => {
    setStep('input');
    setRequest('');
    setSessionId('');
    setQuestions([]);
    setCurrentQuestionIndex(0);
    setAnswers({});
    setCurrentAnswer('');
    setResult('');
    setError('');
  };

  const currentQuestion = questions[currentQuestionIndex];
  const progress = questions.length > 0 ? ((currentQuestionIndex) / questions.length) * 100 : 0;

  return (
    <div className="max-w-4xl mx-auto p-6">
      <div className="bg-white rounded-lg shadow-lg">
        <div className="px-6 py-4 border-b">
          <h2 className="text-2xl font-bold">RFC Generation Demo</h2>
          <p className="text-gray-600">Test the interactive RFC generation process</p>
        </div>

        <div className="p-6">
          {error && (
            <div className="mb-4 p-4 bg-red-50 border border-red-200 rounded text-red-600">
              {error}
            </div>
          )}

          {/* Step 1: Input */}
          {step === 'input' && (
            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium mb-2">
                  Describe what you want to create:
                </label>
                <textarea
                  value={request}
                  onChange={(e) => setRequest(e.target.value)}
                  placeholder="e.g., Create a user authentication system with OAuth 2.0 support"
                  className="w-full h-32 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                />
              </div>
              <button
                onClick={startGeneration}
                disabled={!request.trim() || isLoading}
                className="w-full bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-3 px-4 rounded-lg font-medium"
              >
                {isLoading ? 'Starting...' : 'Start RFC Generation'}
              </button>
            </div>
          )}

          {/* Step 2: Questions */}
          {step === 'questions' && currentQuestion && (
            <div className="space-y-6">
              {/* Progress */}
              <div>
                <div className="flex justify-between text-sm text-gray-600 mb-2">
                  <span>Question {currentQuestionIndex + 1} of {questions.length}</span>
                  <span>{Math.round(progress)}% complete</span>
                </div>
                <div className="w-full bg-gray-200 rounded-full h-2">
                  <div 
                    className="bg-blue-600 h-2 rounded-full transition-all"
                    style={{ width: `${progress}%` }}
                  />
                </div>
              </div>

              {/* Question */}
              <div className="bg-blue-50 p-4 rounded-lg">
                <h3 className="font-medium text-blue-900 mb-2">
                  {currentQuestion.question}
                </h3>
                {currentQuestion.context && (
                  <p className="text-sm text-blue-700">{currentQuestion.context}</p>
                )}
              </div>

              {/* Answer Input */}
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
                    className="w-full h-24 p-3 border rounded-lg focus:ring-2 focus:ring-blue-500"
                  />
                )}
              </div>

              {/* Actions */}
              <div className="flex space-x-4">
                <button
                  onClick={answerQuestion}
                  disabled={!currentAnswer.trim()}
                  className="flex-1 bg-blue-600 hover:bg-blue-700 disabled:bg-gray-400 text-white py-2 px-4 rounded-lg font-medium"
                >
                  {currentQuestionIndex + 1 >= questions.length ? 'Generate RFC' : 'Next Question'}
                </button>
                <button
                  onClick={reset}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
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
              <h3 className="text-lg font-medium mb-2">Generating your RFC...</h3>
              <p className="text-gray-500">This may take a few moments.</p>
            </div>
          )}

          {/* Step 4: Result */}
          {step === 'result' && (
            <div className="space-y-6">
              <div className="flex items-center justify-between">
                <h3 className="text-lg font-medium text-green-600">✅ RFC Generated Successfully!</h3>
                <button
                  onClick={reset}
                  className="px-4 py-2 border border-gray-300 text-gray-700 rounded-lg hover:bg-gray-50"
                >
                  Generate Another
                </button>
              </div>

              <div className="border rounded-lg overflow-hidden">
                <div className="bg-gray-50 px-4 py-2 border-b">
                  <h4 className="font-medium">RFC Preview</h4>
                </div>
                <div className="p-6 max-h-96 overflow-y-auto">
                  <pre className="whitespace-pre-wrap text-sm">{result}</pre>
                </div>
              </div>

              <div className="flex space-x-4">
                <button className="flex-1 bg-green-600 hover:bg-green-700 text-white py-2 px-4 rounded-lg font-medium">
                  Download RFC
                </button>
                <button className="flex-1 bg-blue-600 hover:bg-blue-700 text-white py-2 px-4 rounded-lg font-medium">
                  Share RFC
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
} 