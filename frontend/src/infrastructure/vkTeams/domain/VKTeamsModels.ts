/**
 * VK Teams Domain Models
 * 
 * Context7 pattern: Pure business logic types and interfaces
 * No external dependencies, only domain concepts
 */

// ============================================================================
// Core Domain Types
// ============================================================================

export interface VKTeamsUser {
  id: string;
  name: string;
  email?: string;
  avatar?: string;
  isAdmin?: boolean;
}

export interface VKTeamsChat {
  id: string;
  type: 'private' | 'group' | 'channel';
  title: string;
  description?: string;
  memberCount?: number;
}

export interface VKTeamsMessage {
  id: string;
  chatId: string;
  userId: string;
  text: string;
  timestamp: Date;
  messageType: 'text' | 'command' | 'callback';
  replyToMessage?: string;
  isEdited?: boolean;
}

export interface VKTeamsCommand {
  command: string;
  description: string;
  usage: string;
  adminOnly?: boolean;
}

// ============================================================================
// Bot Configuration
// ============================================================================

export interface VKTeamsBotConfig {
  botId?: string;
  botName?: string;
  botToken: string;
  apiUrl: string;
  webhookUrl?: string;
  isActive: boolean;
  allowedUsers: string[];
  allowedChats: string[];
  autoStart: boolean;
  created: Date;
  updated: Date;
}

// ============================================================================
// Bot Statistics
// ============================================================================

export interface VKTeamsBotStats {
  totalMessages: number;
  totalUsers: number;
  totalChats: number;
  averageResponseTime: number;
  successRate: number;
  errors: number;
  lastActivity?: Date;
  popularCommands: Record<string, number>;
  hourlyActivity: Record<string, number>;
}

// ============================================================================
// Integration State
// ============================================================================

export interface VKTeamsIntegrationState {
  isConnected: boolean;
  isConfigured: boolean;
  config?: VKTeamsBotConfig;
  stats?: VKTeamsBotStats;
  lastError?: string;
  lastSync?: Date;
}

// ============================================================================
// API Response Types
// ============================================================================

export interface VKTeamsApiResponse<T = any> {
  success: boolean;
  data?: T;
  error?: string;
  timestamp: string;
}

export interface VKTeamsBotStatusResponse {
  is_active: boolean;
  bot_id?: string;
  bot_name?: string;
  webhook_url?: string;
  last_activity?: string;
  stats: Record<string, any>;
}

export interface VKTeamsBotConfigResponse {
  success: boolean;
  message: string;
  config: Record<string, any>;
}

// ============================================================================
// Events
// ============================================================================

export interface VKTeamsEvent {
  eventType: string;
  eventId: string;
  timestamp: number;
  payload: Record<string, any>;
}

export interface VKTeamsNewMessageEvent extends VKTeamsEvent {
  eventType: 'newMessage';
  payload: {
    chat: VKTeamsChat;
    from: VKTeamsUser;
    text: string;
    msgId: string;
  };
}

export interface VKTeamsCallbackEvent extends VKTeamsEvent {
  eventType: 'callbackQuery';
  payload: {
    queryId: string;
    chat: VKTeamsChat;
    from: VKTeamsUser;
    callbackData: string;
  };
}

// ============================================================================
// Validation & Utility Types
// ============================================================================

export type VKTeamsEventType = 'newMessage' | 'callbackQuery' | 'editedMessage';

export interface VKTeamsValidationResult {
  isValid: boolean;
  errors: string[];
  warnings: string[];
}

export interface VKTeamsConnectionTest {
  success: boolean;
  responseTime: number;
  error?: string;
  botInfo?: {
    id: string;
    name: string;
    username: string;
  };
}

// ============================================================================
// Command System
// ============================================================================

export interface VKTeamsCommandHandler {
  command: string;
  description: string;
  usage: string;
  adminOnly: boolean;
  handler: (message: VKTeamsMessage, args: string[]) => Promise<string>;
}

export interface VKTeamsCommandRegistry {
  commands: Map<string, VKTeamsCommandHandler>;
  registerCommand: (handler: VKTeamsCommandHandler) => void;
  getCommand: (command: string) => VKTeamsCommandHandler | undefined;
  listCommands: (isAdmin?: boolean) => VKTeamsCommandHandler[];
}

// ============================================================================
// Error Types
// ============================================================================

export class VKTeamsError extends Error {
  constructor(
    message: string,
    public code?: string,
    public details?: Record<string, any>
  ) {
    super(message);
    this.name = 'VKTeamsError';
  }
}

export class VKTeamsConnectionError extends VKTeamsError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'CONNECTION_ERROR', details);
    this.name = 'VKTeamsConnectionError';
  }
}

export class VKTeamsAuthError extends VKTeamsError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'AUTH_ERROR', details);
    this.name = 'VKTeamsAuthError';
  }
}

export class VKTeamsConfigError extends VKTeamsError {
  constructor(message: string, details?: Record<string, any>) {
    super(message, 'CONFIG_ERROR', details);
    this.name = 'VKTeamsConfigError';
  }
} 