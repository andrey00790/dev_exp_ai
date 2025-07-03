import React, { useState } from 'react';
import { useChatStore } from '../stores/chatStore';
import Chat from '../components/Chat';
import api from '../services/api';
import toast from 'react-hot-toast';

export default function Dashboard() {
  const { currentSession, addMessage, setLoading, isLoading } = useChatStore();
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSendMessage = async (message: string) => {
    try {
      // Add user message
      addMessage(message, 'user');
      setLoading(true);
      setIsProcessing(true);

      // Determine the type of request based on message content
      const lowerMessage = message.toLowerCase();
      let response = '';

      if (lowerMessage.includes('search') || lowerMessage.includes('find')) {
        // Handle search request
        try {
          const searchResponse = await api.search({
            query: message,
            limit: 5,
          });
          
          response = `I found ${searchResponse.results.length} results for your search:\n\n`;
          searchResponse.results.forEach((result, index) => {
            response += `**${index + 1}. ${result.title}**\n`;
            response += `${result.content.substring(0, 200)}...\n`;
            response += `Source: ${result.source}\n`;
            if (result.url) {
              response += `URL: ${result.url}\n`;
            }
            response += `Score: ${result.score.toFixed(2)}\n\n`;
          });
        } catch (error) {
          response = 'I encountered an error while searching. Please try again or check your connection.';
        }
      } else if (lowerMessage.includes('generate') || lowerMessage.includes('rfc') || lowerMessage.includes('document')) {
        // Handle RFC generation request
        try {
          const rfcResponse = await api.generateRFC({
            title: message,
            description: message,
          });
          
          if (rfcResponse.questions && rfcResponse.questions.length > 0) {
            response = `I'll help you generate an RFC. First, let me ask you some questions:\n\n`;
            rfcResponse.questions.forEach((question, index) => {
              response += `${index + 1}. ${question}\n`;
            });
            response += `\nPlease provide answers to these questions so I can create a comprehensive RFC for you.`;
          } else if (rfcResponse.rfc_content) {
            response = `Here's your generated RFC:\n\n${rfcResponse.rfc_content}`;
          } else {
            response = 'RFC generation has been started. Please provide more details about what you want to document.';
          }
        } catch (error) {
          response = 'I encountered an error while generating the RFC. Please try again or provide more specific details.';
        }
      } else if (lowerMessage.includes('code') || lowerMessage.includes('documentation')) {
        // Handle code documentation request
        response = `I can help you generate code documentation! To get started, please:

1. Go to the **Code Docs** section in the sidebar
2. Upload your code files (drag & drop or click to select)
3. Choose the type of documentation you need:
   - README files
   - API documentation
   - Technical specifications

I support 13+ programming languages including Python, JavaScript, TypeScript, Java, Go, and more.

Would you like me to guide you through the process?`;
      } else {
        // General AI assistant response
        response = `Hello! I'm your AI Assistant. I can help you with:

🔍 **Semantic Search** - Search through your corporate data sources (Confluence, Jira, GitLab, etc.)
📝 **RFC Generation** - Create technical documents and specifications
📋 **Code Documentation** - Generate documentation for your code projects

Here are some example commands you can try:
- "Search for API authentication methods"
- "Generate an RFC for user authentication system"
- "Help me document my React components"

What would you like to do today?`;
      }

      // Add assistant response
      addMessage(response, 'assistant');
    } catch (error) {
      console.error('Error processing message:', error);
      addMessage('I apologize, but I encountered an error processing your request. Please try again.', 'assistant');
      toast.error('Failed to process your message');
    } finally {
      setLoading(false);
      setIsProcessing(false);
    }
  };

  return (
    <div className="h-full flex flex-col">
      <Chat
        messages={currentSession?.messages || []}
        onSendMessage={handleSendMessage}
        isLoading={isProcessing}
        placeholder="Ask me anything about search, RFC generation, or code documentation..."
      />
    </div>
  );
}
