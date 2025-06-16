import React, { useState, useRef, useEffect } from 'react';
import { PaperAirplaneIcon, StopIcon } from '@heroicons/react/24/outline';
import { motion, AnimatePresence } from 'framer-motion';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { useChatStore } from '../../stores/chatStore';
import { ChatMessage as ChatMessageType, ChatMode } from '../../types/chat';

interface ChatInterfaceProps {
  mode?: ChatMode;
  className?: string;
}

export default function ChatInterface({ mode = 'general', className = '' }: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { 
    messages, 
    isLoading, 
    currentMode,
    sendMessage, 
    stopGeneration,
    setMode 
  } = useChatStore();

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Set mode when component mounts
  useEffect(() => {
    setMode(mode);
  }, [mode, setMode]);

  const handleSendMessage = async (content: string, attachments?: File[]) => {
    await sendMessage(content, attachments);
  };

  const handleStopGeneration = () => {
    stopGeneration();
  };

  return (
    <div className={`flex flex-col h-full bg-white ${className}`}>
      {/* Chat Header */}
      <div className="flex-shrink-0 border-b border-gray-200 bg-white px-6 py-4">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-lg font-semibold text-gray-900">
              {currentMode === 'search' && 'Semantic Search'}
              {currentMode === 'generate' && 'RFC Generation'}
              {currentMode === 'documentation' && 'Code Documentation'}
              {currentMode === 'general' && 'AI Assistant'}
            </h2>
            <p className="text-sm text-gray-500 mt-1">
              {currentMode === 'search' && 'Search through your knowledge base'}
              {currentMode === 'generate' && 'Generate professional RFC documents'}
              {currentMode === 'documentation' && 'Generate code documentation'}
              {currentMode === 'general' && 'Ask me anything about your project'}
            </p>
          </div>
          {isLoading && (
            <button
              onClick={handleStopGeneration}
              className="flex items-center px-3 py-2 text-sm font-medium text-red-600 hover:text-red-700 hover:bg-red-50 rounded-lg transition-colors"
            >
              <StopIcon className="h-4 w-4 mr-2" />
              Stop
            </button>
          )}
        </div>
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <div className="flex items-center justify-center h-full">
            <div className="text-center max-w-md mx-auto px-6">
              <div className="w-16 h-16 bg-blue-100 rounded-full flex items-center justify-center mx-auto mb-4">
                <svg className="w-8 h-8 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
              <h3 className="text-lg font-medium text-gray-900 mb-2">
                Start a conversation
              </h3>
              <p className="text-gray-500 text-sm">
                {currentMode === 'search' && 'Ask me to search for specific information in your knowledge base.'}
                {currentMode === 'generate' && 'Describe the system or feature you want to create an RFC for.'}
                {currentMode === 'documentation' && 'Upload code files or describe what you want to document.'}
                {currentMode === 'general' && 'Ask me anything about your project, code, or documentation.'}
              </p>
            </div>
          </div>
        ) : (
          <div className="py-6">
            <AnimatePresence>
              {messages.map((message, index) => (
                <motion.div
                  key={message.id}
                  initial={{ opacity: 0, y: 20 }}
                  animate={{ opacity: 1, y: 0 }}
                  exit={{ opacity: 0, y: -20 }}
                  transition={{ duration: 0.3, delay: index * 0.1 }}
                >
                  <ChatMessage message={message} />
                </motion.div>
              ))}
            </AnimatePresence>
            
            {/* Loading indicator */}
            {isLoading && (
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                className="px-6 py-4"
              >
                <div className="flex items-start space-x-4">
                  <div className="flex-shrink-0">
                    <div className="w-8 h-8 bg-blue-600 rounded-full flex items-center justify-center">
                      <svg className="w-5 h-5 text-white" fill="currentColor" viewBox="0 0 20 20">
                        <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-8.293l-3-3a1 1 0 00-1.414 0l-3 3a1 1 0 001.414 1.414L9 9.414V13a1 1 0 102 0V9.414l1.293 1.293a1 1 0 001.414-1.414z" clipRule="evenodd" />
                      </svg>
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
              </motion.div>
            )}
            
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Chat Input */}
      <div className="flex-shrink-0 border-t border-gray-200 bg-white">
        <ChatInput
          onSendMessage={handleSendMessage}
          disabled={isLoading}
          mode={currentMode}
          placeholder={
            currentMode === 'search' ? 'Search for information...' :
            currentMode === 'generate' ? 'Describe the system you want to create an RFC for...' :
            currentMode === 'documentation' ? 'Describe what you want to document...' :
            'Ask me anything...'
          }
        />
      </div>
    </div>
  );
} 