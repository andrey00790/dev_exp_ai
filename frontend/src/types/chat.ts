export type ChatMode = 'general' | 'search' | 'generate' | 'documentation';

export type MessageRole = 'user' | 'assistant' | 'system';

export interface ChatMessage {
  id: string;
  role: MessageRole;
  content: string;
  timestamp: Date;
  mode: ChatMode;
  attachments?: ChatAttachment[];
  metadata?: {
    searchResults?: SearchResult[];
    rfcData?: RFCData;
    documentationData?: DocumentationData;
    error?: string;
    isStreaming?: boolean;
  };
}

export interface ChatAttachment {
  id: string;
  name: string;
  type: string;
  size: number;
  url?: string;
  content?: string;
}

export interface SearchResult {
  id: string;
  title: string;
  content: string;
  source: string;
  score: number;
  url?: string;
}

export interface RFCData {
  title: string;
  sections: RFCSection[];
  template: string;
  quality_score?: number;
  completeness?: number;
}

export interface RFCSection {
  title: string;
  content: string;
  order: number;
}

export interface DocumentationData {
  language: string;
  file_path: string;
  documentation_type: string;
  coverage: number;
  sections: DocumentationSection[];
}

export interface DocumentationSection {
  title: string;
  content: string;
  type: 'overview' | 'api' | 'examples' | 'installation' | 'usage';
}

export interface ChatSession {
  id: string;
  title: string;
  mode: ChatMode;
  messages: ChatMessage[];
  created_at: Date;
  updated_at: Date;
} 