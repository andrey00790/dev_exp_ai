import { create } from 'zustand';
import { devtools } from 'zustand/middleware';
import { ChatMessage, ChatMode, ChatSession } from '../types/chat';
import { chatApi } from '../api/chatApi';

interface ChatState {
  // Current chat state
  messages: ChatMessage[];
  currentSession: ChatSession | null;
  currentMode: ChatMode;
  isLoading: boolean;
  error: string | null;
  
  // Chat sessions
  sessions: ChatSession[];
  
  // Actions
  sendMessage: (content: string, attachments?: File[]) => Promise<void>;
  stopGeneration: () => void;
  setMode: (mode: ChatMode) => void;
  clearMessages: () => void;
  loadSession: (sessionId: string) => Promise<void>;
  createNewSession: (mode: ChatMode) => void;
  deleteSession: (sessionId: string) => void;
  updateSessionTitle: (sessionId: string, title: string) => void;
  
  // Utility actions
  setError: (error: string | null) => void;
  setLoading: (loading: boolean) => void;
}

export const useChatStore = create<ChatState>()(
  devtools(
    (set, get) => ({
      // Initial state
      messages: [],
      currentSession: null,
      currentMode: 'general',
      isLoading: false,
      error: null,
      sessions: [],

      // Send message action
      sendMessage: async (content: string, attachments?: File[]) => {
        const { currentMode, messages } = get();
        
        // Create user message
        const userMessage: ChatMessage = {
          id: `msg-${Date.now()}-user`,
          role: 'user',
          content,
          timestamp: new Date(),
          mode: currentMode,
          attachments: attachments?.map(file => ({
            id: `att-${Date.now()}-${file.name}`,
            name: file.name,
            type: file.type,
            size: file.size,
          })),
        };

        // Add user message and set loading
        set({ 
          messages: [...messages, userMessage], 
          isLoading: true, 
          error: null 
        });

        try {
          // Send to API based on mode
          let response;
          switch (currentMode) {
            case 'search':
              response = await chatApi.search(content, attachments);
              break;
            case 'generate':
              response = await chatApi.generateRFC(content, attachments);
              break;
            case 'documentation':
              response = await chatApi.generateDocumentation(content, attachments);
              break;
            default:
              response = await chatApi.general(content, attachments);
          }

          // Create assistant message
          const assistantMessage: ChatMessage = {
            id: `msg-${Date.now()}-assistant`,
            role: 'assistant',
            content: response.content,
            timestamp: new Date(),
            mode: currentMode,
            metadata: response.metadata,
          };

          // Add assistant message and stop loading
          set(state => ({
            messages: [...state.messages, assistantMessage],
            isLoading: false,
          }));

          // Auto-generate session title if this is the first message
          const updatedMessages = get().messages;
          if (updatedMessages.length === 2) { // user + assistant
            const title = content.slice(0, 50) + (content.length > 50 ? '...' : '');
            // Update current session or create new one
            // This would be implemented based on session management needs
          }

        } catch (error) {
          console.error('Error sending message:', error);
          set({ 
            error: error instanceof Error ? error.message : 'Failed to send message',
            isLoading: false 
          });
        }
      },

      // Stop generation
      stopGeneration: () => {
        // This would cancel any ongoing API requests
        set({ isLoading: false });
      },

      // Set chat mode
      setMode: (mode: ChatMode) => {
        set({ currentMode: mode });
      },

      // Clear messages
      clearMessages: () => {
        set({ messages: [], currentSession: null });
      },

      // Load session
      loadSession: async (sessionId: string) => {
        try {
          const session = await chatApi.getSession(sessionId);
          set({ 
            currentSession: session,
            messages: session.messages,
            currentMode: session.mode,
          });
        } catch (error) {
          console.error('Error loading session:', error);
          set({ error: 'Failed to load session' });
        }
      },

      // Create new session
      createNewSession: (mode: ChatMode) => {
        const newSession: ChatSession = {
          id: `session-${Date.now()}`,
          title: 'New Chat',
          mode,
          messages: [],
          created_at: new Date(),
          updated_at: new Date(),
        };

        set(state => ({
          currentSession: newSession,
          sessions: [newSession, ...state.sessions],
          messages: [],
          currentMode: mode,
        }));
      },

      // Delete session
      deleteSession: (sessionId: string) => {
        set(state => ({
          sessions: state.sessions.filter(s => s.id !== sessionId),
          ...(state.currentSession?.id === sessionId ? {
            currentSession: null,
            messages: [],
          } : {}),
        }));
      },

      // Update session title
      updateSessionTitle: (sessionId: string, title: string) => {
        set(state => ({
          sessions: state.sessions.map(s => 
            s.id === sessionId ? { ...s, title, updated_at: new Date() } : s
          ),
          ...(state.currentSession?.id === sessionId ? {
            currentSession: { ...state.currentSession, title, updated_at: new Date() }
          } : {}),
        }));
      },

      // Utility actions
      setError: (error: string | null) => {
        set({ error });
      },

      setLoading: (loading: boolean) => {
        set({ isLoading: loading });
      },
    }),
    {
      name: 'chat-store',
    }
  )
); 