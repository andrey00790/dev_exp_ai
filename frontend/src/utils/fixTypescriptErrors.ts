// Context7 pattern: Utility for fixing common TypeScript errors

// Fix 1: Import meta environment access
declare global {
  interface ImportMeta {
    env: {
      VITE_API_URL?: string;
      [key: string]: any;
    }
  }
}

// Fix 2: Speech Recognition API types
interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
  resultIndex: number;
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
  message: string;
}

interface SpeechRecognition extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  onresult: (event: SpeechRecognitionEvent) => void;
  onerror: (event: SpeechRecognitionErrorEvent) => void;
  onstart: () => void;
  onend: () => void;
  start(): void;
  stop(): void;
  abort(): void;
}

interface SpeechRecognitionResultList {
  readonly length: number;
  item(index: number): SpeechRecognitionResult;
  [index: number]: SpeechRecognitionResult;
}

interface SpeechRecognitionResult {
  readonly length: number;
  item(index: number): SpeechRecognitionAlternative;
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

declare global {
  interface Window {
    SpeechRecognition: {
      new(): SpeechRecognition;
    };
    webkitSpeechRecognition: {
      new(): SpeechRecognition;
    };
  }
}

// Fix 3: Service Worker types
declare global {
  interface ServiceWorkerGlobalScope {
    skipWaiting(): Promise<void>;
    clients: Clients;
    registration: ServiceWorkerRegistration;
  }
}

// Fix 4: API Response types
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: number;
}

// Fix 5: User types consistency
export interface User {
  user_id: string;
  email: string;
  name: string;
  budget_limit: number;
  current_usage: number;
  scopes: string[];
  is_active: boolean;
  is_admin?: boolean;
}

export default {}; 