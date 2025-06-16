import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, StopIcon, MagnifyingGlassIcon, DocumentTextIcon, CodeBracketIcon } from '@heroicons/react/24/outline';
import ReactMarkdown from 'react-markdown';
import { chatApi } from '../api/chatApi';

interface Message {
  id: string;
  role: 'user' | 'assistant';
  content: string;
  timestamp: Date;
  mode?: 'search' | 'generate' | 'documentation' | 'general';
  metadata?: any;
}

type ChatMode = 'search' | 'generate' | 'documentation' | 'general';

export default function Chat() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [currentMode, setCurrentMode] = useState<ChatMode>('general');
  const [error, setError] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSendMessage = async () => {
    if (!input.trim() || isLoading) return;

    const userMessage: Message = {
      id: `msg-${Date.now()}-user`,
      role: 'user',
      content: input.trim(),
      timestamp: new Date(),
      mode: currentMode,
    };

    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);
    setError(null);

    try {
      let response;
      
      // Call appropriate API based on mode
      switch (currentMode) {
        case 'search':
          response = await chatApi.search(userMessage.content);
          break;
        case 'generate':
          response = await chatApi.generateRFC(userMessage.content);
          break;
        case 'documentation':
          response = await chatApi.generateDocumentation(userMessage.content);
          break;
        default:
          response = await chatApi.general(userMessage.content);
      }
      
      const assistantMessage: Message = {
        id: `msg-${Date.now()}-assistant`,
        role: 'assistant',
        content: response.content,
        timestamp: new Date(),
        mode: currentMode,
        metadata: response.metadata,
      };

      setMessages(prev => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);
      setError(error instanceof Error ? error.message : 'Failed to send message');
      
      // Add error message
      const errorMessage: Message = {
        id: `msg-${Date.now()}-error`,
        role: 'assistant',
        content: `Sorry, I encountered an error: ${error instanceof Error ? error.message : 'Unknown error'}. Please try again.`,
        timestamp: new Date(),
        mode: currentMode,
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const handleModeChange = (mode: ChatMode) => {
    setCurrentMode(mode);
    setError(null);
  };

  const getModeInfo = () => {
    switch (currentMode) {
      case 'search':
        return {
          title: 'Semantic Search',
          description: 'Search through your knowledge base',
          icon: MagnifyingGlassIcon,
          placeholder: 'Search for information...',
          color: 'blue'
        };
      case 'generate':
        return {
          title: 'RFC Generation',
          description: 'Generate professional RFC documents',
          icon: DocumentTextIcon,
          placeholder: 'Describe the system you want to create an RFC for...',
          color: 'green'
        };
      case 'documentation':
        return {
          title: 'Code Documentation',
          description: 'Generate code documentation',
          icon: CodeBracketIcon,
          placeholder: 'Describe what you want to document...',
          color: 'purple'
        };
      default:
        return {
          title: 'AI Assistant',
          description: 'Ask me anything about your project',
          icon: MagnifyingGlassIcon,
          placeholder: 'Ask me anything...',
          color: 'gray'
        };
    }
  };

  const modeInfo = getModeInfo();
  const ModeIcon = modeInfo.icon;

  return (
    <div className="flex flex-col h-full bg-white">
      {/* Chat Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className={`w-10 h-10 bg-${modeInfo.color}-100 rounded-lg flex items-center justify-center`}>
              <ModeIcon className={`h-6 w-6 text-${modeInfo.color}-600`} />
            </div>
            <div>
              <h2 className="text-lg font-semibold text-gray-900">{modeInfo.title}</h2>
              <p className="text-sm text-gray-500 mt-1">{modeInfo.description}</p>
            </div>
          </div>
          
          <div className="flex items-center space-x-2">
            {/* Mode Selector */}
            <div className="flex bg-gray-100 rounded-lg p-1">
              {(['search', 'generate', 'documentation', 'general'] as ChatMode[]).map((mode) => (
                <button
                  key={mode}
                  onClick={() => handleModeChange(mode)}
                  className={`px-3 py-1 text-sm font-medium rounded-md transition-colors ${
                    currentMode === mode
                      ? 'bg-white text-gray-900 shadow-sm'
                      : 'text-gray-600 hover:text-gray-900'
                  }`}
                >
                  {mode.charAt(0).toUpperCase() + mode.slice(1)}
                </button>
              ))}
            </div>
            
            {isLoading && (
              <button
                onClick={() => setIsLoading(false)}
                className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
              >
                <StopIcon className="h-4 w-4 mr-2" />
                Stop
              </button>
            )}
          </div>
        </div>
        
        {error && (
          <div className="mt-3 p-3 bg-red-50 border border-red-200 rounded-lg">
            <p className="text-sm text-red-600">{error}</p>
          </div>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md mx-auto px-6">
              <div className={`w-16 h-16 bg-${modeInfo.color}-100 rounded-full flex items-center justify-center mx-auto mb-4`}>
                <ModeIcon className={`w-8 h-8 text-${modeInfo.color}-600`} />
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Start a conversation
              </h3>
              <p className="text-gray-500 text-sm">
                {modeInfo.description}. Try asking something!
              </p>
              
              {/* Example prompts */}
              <div className="mt-6 space-y-2">
                <p className="text-xs font-medium text-gray-400 uppercase tracking-wider">Example prompts:</p>
                {currentMode === 'search' && (
                  <div className="space-y-1">
                    <button 
                      onClick={() => setInput('Search for API documentation')}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      "Search for API documentation"
                    </button>
                    <button 
                      onClick={() => setInput('Find information about authentication')}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      "Find information about authentication"
                    </button>
                  </div>
                )}
                {currentMode === 'generate' && (
                  <div className="space-y-1">
                    <button 
                      onClick={() => setInput('Create an RFC for user authentication system')}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      "Create an RFC for user authentication system"
                    </button>
                    <button 
                      onClick={() => setInput('Generate RFC for microservices architecture')}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      "Generate RFC for microservices architecture"
                    </button>
                  </div>
                )}
                {currentMode === 'documentation' && (
                  <div className="space-y-1">
                    <button 
                      onClick={() => setInput('Document my React components')}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      "Document my React components"
                    </button>
                    <button 
                      onClick={() => setInput('Create API documentation')}
                      className="block w-full text-left px-3 py-2 text-sm text-gray-600 hover:bg-gray-50 rounded-lg"
                    >
                      "Create API documentation"
                    </button>
                  </div>
                )}
              </div>
            </div>
          </div>
        ) : (
          <div className="py-6">
            {messages.map((message) => (
              <div key={message.id} className="px-6 py-4">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' 
                        ? 'bg-gray-600' 
                        : `bg-${modeInfo.color}-600`
                    }`}>
                      {message.role === 'user' ? (
                        <span className="text-white text-sm font-medium">U</span>
                      ) : (
                        <ModeIcon className="w-5 h-5 text-white" />
                      )}
                    </div>
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="text-sm text-gray-900">
                      {message.role === 'assistant' ? (
                        <ReactMarkdown className="prose prose-sm max-w-none">
                          {message.content}
                        </ReactMarkdown>
                      ) : (
                        <p className="whitespace-pre-wrap">{message.content}</p>
                      )}
                    </div>
                    
                    {/* Metadata display */}
                    {message.metadata && (
                      <div className="mt-3 p-3 bg-gray-50 rounded-lg">
                        {message.metadata.searchResults && (
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">
                              Found {message.metadata.searchResults.length} results
                            </p>
                          </div>
                        )}
                        {message.metadata.rfcData && (
                          <div>
                            <p className="text-xs font-medium text-gray-500 mb-2">
                              RFC Quality Score: {message.metadata.rfcData.quality_score || 'N/A'}
                            </p>
                          </div>
                        )}
                        {message.metadata.error && (
                          <div>
                            <p className="text-xs text-red-600">Error: {message.metadata.error}</p>
                          </div>
                        )}
                      </div>
                    )}
                    
                    <div className="text-xs text-gray-500 mt-2">
                      {message.timestamp.toLocaleTimeString()} • {message.mode || 'general'}
                    </div>
                  </div>
                </div>
              </div>
            ))}
            
            {/* Loading indicator */}
            {isLoading && (
              <div className="px-6 py-4">
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className={`w-8 h-8 bg-${modeInfo.color}-600 rounded-full flex items-center justify-center`}>
                      <ModeIcon className="w-5 h-5 text-white" />
                    </div>
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center space-x-2">
                      <div className="flex space-x-1">
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce"></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.1s' }}></div>
                        <div className="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                      </div>
                      <span className="text-sm text-gray-500">AI is thinking...</span>
                    </div>
                  </div>
                </div>
              </div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white p-4">
        <div className="flex items-end space-x-3">
          <div className="flex-1">
            <textarea
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder={modeInfo.placeholder}
              className="w-full resize-none border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              rows={1}
              style={{ minHeight: '40px', maxHeight: '120px' }}
              disabled={isLoading}
            />
          </div>
          <button
            onClick={handleSendMessage}
            disabled={!input.trim() || isLoading}
            className={`flex-shrink-0 bg-${modeInfo.color}-600 hover:bg-${modeInfo.color}-700 disabled:bg-gray-300 disabled:cursor-not-allowed text-white p-2 rounded-lg transition-colors`}
          >
            <PaperAirplaneIcon className="h-5 w-5" />
          </button>
        </div>
      </div>
    </div>
  );
} 