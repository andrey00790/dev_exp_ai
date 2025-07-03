import apiClient from './client';

export interface ChatMessage {
  id: string;
  content: string;
  timestamp: string;
  type: 'user' | 'assistant';
  metadata?: {
    searchResults?: SearchResult[];
    rfcData?: RFCData;
    documentationData?: DocumentationData;
    error?: string;
    isStreaming?: boolean;
  };
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  score: number;
  metadata?: any;
}

export interface RFCData {
  session_id?: string;
  title: string;
  sections: Array<{
    title: string;
    content: string;
    order: number;
  }>;
  template: string;
  quality_score?: number;
  completeness?: number;
  questions?: AIQuestion[];
  is_ready_to_generate?: boolean;
  metadata?: any;
}

export interface AIQuestion {
  id: string;
  question: string;
  question_type: 'text' | 'choice' | 'multiple_choice' | 'boolean';
  options?: string[];
  is_required: boolean;
  context?: string;
  placeholder?: string;
}

export interface DocumentationData {
  title: string;
  content: string;
  sections: DocumentationSection[];
  file_tree?: string;
  summary?: string;
  language?: string;
  file_path?: string;
  documentation_type?: string;
  coverage?: number;
}

export interface DocumentationSection {
  title: string;
  content: string;
  type: 'overview' | 'api' | 'examples' | 'installation' | 'usage';
}

export interface SearchRequest {
  query: string;
  collections?: string[];
  limit?: number;
  filters?: Record<string, any>;
}

export interface GenerateRequest {
  task_type: 'new_feature' | 'modify_existing' | 'analyze_current';
  initial_request: string;
  user_id: string;
  context?: string;
  search_sources?: string[];
}

export interface AnswerRequest {
  session_id: string;
  answers: Array<{
    question_id: string;
    answer: string;
  }>;
}

export interface FinalizeRequest {
  session_id: string;
  additional_requirements?: string;
}

export interface DocumentationRequest {
  code_content?: string;
  file_path?: string;
  language?: string;
  doc_type?: string;
}

export interface ChatResponse {
  response: string;
  sources?: Array<{
    title: string;
    content: string;
    source: string;
    url?: string;
  }>;
  conversationId?: string;
  error?: string;
}

export interface ApiSearchResponse {
  id: string;
  timestamp: string;
  results: SearchResult[];
}

export interface ApiGenerateResponse {
  id: string;
  timestamp: string;
  session_id?: string;
  questions?: any[];
  is_ready_to_generate?: boolean;
  rfc_content?: string;
  content?: string;
  sections?: any[];
}

export interface ApiDocumentationResponse {
  id: string;
  timestamp: string;
  documentation?: string;
  language?: string;
  coverage?: number;
  sections?: any[];
}

export interface ApiResponse<T = any> {
  data: T;
  success: boolean;
  error?: string;
}

class ChatApi {
  // Semantic Search
  async search(query: string, _attachments?: File[]): Promise<ChatMessage> {
    try {
      const searchRequest: SearchRequest = {
        query,
        limit: 10,
      };

      const response = await apiClient.post('/api/v1/vector-search/search', searchRequest) as ApiSearchResponse;
      
      return {
        id: response.id,
        content: this.formatSearchResults(response.results || []),
        timestamp: response.timestamp,
        type: 'assistant',
        metadata: {
          searchResults: response.results || [],
        },
      };
    } catch (error) {
      console.error('Search API error:', error);
      return {
        id: '',
        content: 'Sorry, I encountered an error while searching. Please try again.',
        timestamp: '',
        type: 'assistant',
        metadata: {
          error: error instanceof Error ? error.message : 'Search failed',
        },
      };
    }
  }

  // RFC Generation - Start Session
  async generateRFC(description: string, taskType: 'new_feature' | 'modify_existing' | 'analyze_current' = 'new_feature'): Promise<ChatMessage> {
    try {
      // Get current user ID (in real app, this would come from auth context)
      const userId = 'admin_001'; // TODO: Get from auth context
      
      const generateRequest: GenerateRequest = {
        task_type: taskType,
        initial_request: description,
        user_id: userId,
        context: 'Generated from RFC Generator interface',
      };

      console.log('Sending RFC generation request:', generateRequest);
      const response = await apiClient.post('/api/v1/generate', generateRequest) as ApiGenerateResponse;
      console.log('RFC generation response:', response);
      
      // Format response for chat
      let content = `I've started generating an RFC for: "${description}"\n\n`;
      
      // Handle questions if they exist
      if (response.questions && Array.isArray(response.questions) && response.questions.length > 0) {
        // Normalize question types and structure
        const normalizedQuestions = response.questions.map((q: any, index: number) => ({
          id: q.id || `question_${index}`,
          question: q.question || q.text || 'Question',
          question_type: this.normalizeQuestionType(q.question_type || q.type || 'text'),
          options: q.options || q.choices || [],
          is_required: q.is_required !== false, // Default to true
          context: q.context || q.description || '',
          placeholder: q.placeholder || 'Enter your answer...',
        }));

        content += "To create a high-quality RFC, I need to ask you a few questions:\n\n";
        normalizedQuestions.forEach((q: AIQuestion, index: number) => {
          content += `**${index + 1}. ${q.question}**\n`;
          if (q.context) {
            content += `*${q.context}*\n`;
          }
          if (q.options && q.options.length > 0) {
            content += q.options.map(opt => `- ${opt}`).join('\n') + '\n';
          }
          content += '\n';
        });
        content += "Please answer these questions to continue with RFC generation.";

        return {
          id: response.id,
          content,
          timestamp: response.timestamp,
          type: 'assistant',
          metadata: {
            rfcData: {
              session_id: response.session_id || `session_${Date.now()}`,
              title: 'RFC Generation in Progress',
              sections: [],
              template: 'interactive',
              questions: normalizedQuestions,
              is_ready_to_generate: response.is_ready_to_generate || false,
            },
          },
        };
      } else {
        // No questions, direct RFC generation
        content += "Generating RFC directly from your description...";
        
        return {
          id: response.id,
          content: response.rfc_content || response.content || content,
          timestamp: response.timestamp,
          type: 'assistant',
          metadata: {
            rfcData: {
              session_id: response.session_id || `session_${Date.now()}`,
              title: 'Generated RFC',
              sections: response.sections || [],
              template: 'direct',
              is_ready_to_generate: true,
            },
          },
        };
      }
    } catch (error) {
      console.error('RFC Generation API error:', error);
      return {
        id: '',
        content: 'Sorry, I encountered an error while generating the RFC. Please try again.',
        timestamp: '',
        type: 'assistant',
        metadata: {
          error: error instanceof Error ? error.message : 'RFC generation failed',
        },
      };
    }
  }

  // Helper method to normalize question types
  private normalizeQuestionType(type: string): 'text' | 'choice' | 'multiple_choice' | 'boolean' {
    const normalizedType = type.toLowerCase();
    
    if (normalizedType.includes('choice') || normalizedType.includes('select')) {
      return normalizedType.includes('multiple') ? 'multiple_choice' : 'choice';
    }
    if (normalizedType.includes('bool') || normalizedType.includes('yes') || normalizedType.includes('no')) {
      return 'boolean';
    }
    return 'text';
  }

  // RFC Generation - Answer Questions
  async answerRFCQuestions(sessionId: string, answers: Array<{ question_id: string; answer: string }>): Promise<ChatMessage> {
    try {
      const answerRequest: AnswerRequest = {
        session_id: sessionId,
        answers,
      };

      const response = await apiClient.post('/api/v1/generate/answer', answerRequest) as ApiGenerateResponse;
      
      let content = "Thank you for your answers!\n\n";
      
      if (response.questions && response.questions.length > 0) {
        content += "I have a few more questions:\n\n";
        response.questions.forEach((q: AIQuestion, index: number) => {
          content += `**${index + 1}. ${q.question}**\n`;
          if (q.context) {
            content += `*${q.context}*\n`;
          }
          if (q.options) {
            content += q.options.map(opt => `- ${opt}`).join('\n') + '\n';
          }
          content += '\n';
        });
      } else if (response.is_ready_to_generate) {
        content += "Perfect! I have all the information needed to generate your RFC.";
      }
      
      return {
        id: response.id,
        content,
        timestamp: response.timestamp,
        type: 'assistant',
        metadata: {
          rfcData: {
            session_id: sessionId,
            title: 'RFC Generation in Progress',
            sections: [],
            template: 'interactive',
            questions: response.questions,
            is_ready_to_generate: response.is_ready_to_generate,
          },
        },
      };
    } catch (error) {
      console.error('Answer RFC Questions API error:', error);
      return {
        id: '',
        content: 'Sorry, I encountered an error while processing your answers. Please try again.',
        timestamp: '',
        type: 'assistant',
        metadata: {
          error: error instanceof Error ? error.message : 'Failed to process answers',
        },
      };
    }
  }

  // RFC Generation - Finalize
  async finalizeRFC(sessionId: string, additionalRequirements?: string): Promise<ChatMessage> {
    try {
      const finalizeRequest: FinalizeRequest = {
        session_id: sessionId,
        additional_requirements: additionalRequirements,
      };

      const response = await apiClient.post('/api/v1/generate/finalize', finalizeRequest) as ApiGenerateResponse & { rfc?: any };
      
      return {
        id: response.id,
        content: response.rfc?.content || 'RFC generated successfully!',
        timestamp: response.timestamp,
        type: 'assistant',
        metadata: {
          rfcData: {
            session_id: sessionId,
            title: response.rfc?.title || 'Generated RFC',
            sections: response.rfc?.sections || [],
            template: response.rfc?.template || 'interactive',
            quality_score: response.rfc?.quality_score,
            completeness: response.rfc?.completeness,
            is_ready_to_generate: true,
          },
        },
      };
    } catch (error) {
      console.error('Finalize RFC API error:', error);
      return {
        id: '',
        content: 'Sorry, I encountered an error while finalizing the RFC. Please try again.',
        timestamp: '',
        type: 'assistant',
        metadata: {
          error: error instanceof Error ? error.message : 'RFC finalization failed',
        },
      };
    }
  }

  // Get RFC Session
  async getRFCSession(sessionId: string): Promise<any> {
    try {
      return await apiClient.get(`/api/v1/generate/session/${sessionId}`);
    } catch (error) {
      console.error('Get RFC session error:', error);
      throw error;
    }
  }

  // Code Documentation
  async generateDocumentation(description: string, attachments?: File[]): Promise<ChatMessage> {
    try {
      if (attachments && attachments.length > 0) {
        // Upload file and generate documentation
        const file = attachments[0];
        const response = await apiClient.uploadFile('/api/v1/documentation/analyze', file, {
          doc_type: 'comprehensive',
        }) as ApiDocumentationResponse;

        return {
          id: response.id,
          content: response.documentation || 'Documentation generated successfully',
          timestamp: response.timestamp,
          type: 'assistant',
          metadata: {
            documentationData: {
              title: file.name,
              content: response.documentation || 'Documentation generated successfully',
              language: response.language || 'unknown',
              file_path: file.name,
              documentation_type: 'comprehensive',
              coverage: response.coverage || 0,
              sections: response.sections || [],
            },
          },
        };
      } else {
        // Generate documentation from description
        const docRequest: DocumentationRequest = {
          code_content: description,
          doc_type: 'comprehensive',
        };

        const response = await apiClient.post('/api/v1/documentation/generate', docRequest) as ApiDocumentationResponse;
        
        return {
          id: response.id,
          content: response.documentation || 'Documentation generated successfully',
          timestamp: response.timestamp,
          type: 'assistant',
          metadata: {
            documentationData: {
              title: 'inline',
              content: response.documentation || 'Documentation generated successfully',
              language: response.language || 'unknown',
              file_path: 'inline',
              documentation_type: 'comprehensive',
              coverage: response.coverage || 0,
              sections: response.sections || [],
            },
          },
        };
      }
    } catch (error) {
      console.error('Documentation API error:', error);
      return {
        id: '',
        content: 'Sorry, I encountered an error while generating documentation. Please try again.',
        timestamp: '',
        type: 'assistant',
        metadata: {
          error: error instanceof Error ? error.message : 'Documentation generation failed',
        },
      };
    }
  }

  // General chat (fallback to search)
  async general(message: string, attachments?: File[]): Promise<ChatMessage> {
    // For general messages, we can use search as a fallback
    // or implement a general chat endpoint if available
    return this.search(message, attachments);
  }

  // Get chat session (placeholder for future implementation)
  async getSession(sessionId: string): Promise<any> {
    try {
      return await apiClient.get(`/api/v1/chat/sessions/${sessionId}`);
    } catch (error) {
      console.error('Get session error:', error);
      throw error;
    }
  }

  // Health check for API
  async healthCheck(): Promise<{ status: string }> {
    try {
      return await apiClient.get('/health');
    } catch (error) {
      console.error('Health check error:', error);
      return { status: 'error' };
    }
  }

  // Helper method to format search results
  private formatSearchResults(results: SearchResult[]): string {
    if (!results || results.length === 0) {
      return 'No results found for your query. The knowledge base might be empty or your query might be too specific. Try using different keywords.';
    }

    let formatted = `I found ${results.length} relevant result${results.length > 1 ? 's' : ''}:\n\n`;
    
    results.forEach((result, index) => {
      formatted += `**${index + 1}. ${result.title}**\n`;
      formatted += `${result.content.substring(0, 200)}${result.content.length > 200 ? '...' : ''}\n`;
      formatted += `*Source: ${result.source}* | *Relevance: ${(result.score * 100).toFixed(1)}%*\n\n`;
    });

    return formatted;
  }

  // Authentication helper
  async login(email: string, password: string): Promise<{ access_token: string; user: any }> {
    try {
      const response = await apiClient.post('/auth/login', { email, password }) as { access_token: string; user: any };
      return response;
    } catch (error) {
      console.error('Login error:', error);
      throw error;
    }
  }

  // Get demo users for testing
  async getDemoUsers(): Promise<any> {
    try {
      return await apiClient.get('/auth/demo-users');
    } catch (error) {
      console.error('Get demo users error:', error);
      throw error;
    }
  }

  // These methods are now handled by the instance methods above
  // Removing duplicates to fix TypeScript issues
}

export const chatApi = new ChatApi();
export default chatApi; 