/**
 * Local Storage Adapter
 * 
 * Adapter for local storage operations.
 * Handles session persistence and user preferences.
 */

import { AuthSession } from '../../contexts/AuthContext';
import { UserPreferences } from '../../domain/auth/entities';

// ============================================================================
// Storage Keys
// ============================================================================

const STORAGE_KEYS = {
  AUTH_SESSION: 'auth_session',
  USER_PREFERENCES: 'user_preferences',
  THEME: 'theme',
  LANGUAGE: 'language',
  RECENT_SEARCHES: 'recent_searches',
  UI_STATE: 'ui_state',
} as const;

// ============================================================================
// Types
// ============================================================================

interface StoredSession {
  id: string;
  token: string;
  refreshToken: string;
  expiresAt: string;
  isActive: boolean;
  userId?: string;
}

interface UIState {
  sidebarCollapsed: boolean;
  selectedWorkspace?: string;
  recentFiles: string[];
  bookmarks: string[];
}

// ============================================================================
// Local Storage Adapter
// ============================================================================

export class LocalStorageAdapter {
  private isAvailable: boolean;

  constructor() {
    this.isAvailable = this.checkStorageAvailability();
  }

  // ============================================================================
  // Private Methods
  // ============================================================================

  private checkStorageAvailability(): boolean {
    try {
      const test = 'localStorage_test';
      localStorage.setItem(test, test);
      localStorage.removeItem(test);
      return true;
    } catch {
      return false;
    }
  }

  private safeGetItem(key: string): string | null {
    if (!this.isAvailable) return null;
    
    try {
      return localStorage.getItem(key);
    } catch (error) {
      console.warn(`Failed to get item from localStorage: ${key}`, error);
      return null;
    }
  }

  private safeSetItem(key: string, value: string): boolean {
    if (!this.isAvailable) return false;
    
    try {
      localStorage.setItem(key, value);
      return true;
    } catch (error) {
      console.warn(`Failed to set item in localStorage: ${key}`, error);
      return false;
    }
  }

  private safeRemoveItem(key: string): boolean {
    if (!this.isAvailable) return false;
    
    try {
      localStorage.removeItem(key);
      return true;
    } catch (error) {
      console.warn(`Failed to remove item from localStorage: ${key}`, error);
      return false;
    }
  }

  private parseJSON<T>(value: string | null, fallback: T): T {
    if (!value) return fallback;
    
    try {
      return JSON.parse(value) as T;
    } catch {
      return fallback;
    }
  }

  // ============================================================================
  // Session Management
  // ============================================================================

  getSession(): AuthSession | null {
    const sessionData = this.safeGetItem(STORAGE_KEYS.AUTH_SESSION);
    if (!sessionData) return null;

    try {
      const stored: StoredSession = JSON.parse(sessionData);
      
      // Check if session is expired
      const expiresAt = new Date(stored.expiresAt);
      if (expiresAt <= new Date()) {
        this.removeSession();
        return null;
      }

      return {
        id: stored.id,
        token: stored.token,
        refreshToken: stored.refreshToken,
        expiresAt,
        isActive: stored.isActive,
      };
    } catch (error) {
      console.warn('Failed to parse stored session', error);
      this.removeSession();
      return null;
    }
  }

  setSession(session: AuthSession): boolean {
    const stored: StoredSession = {
      id: session.id,
      token: session.token,
      refreshToken: session.refreshToken,
      expiresAt: session.expiresAt.toISOString(),
      isActive: session.isActive,
    };

    return this.safeSetItem(STORAGE_KEYS.AUTH_SESSION, JSON.stringify(stored));
  }

  removeSession(): boolean {
    return this.safeRemoveItem(STORAGE_KEYS.AUTH_SESSION);
  }

  isSessionValid(): boolean {
    const session = this.getSession();
    return session !== null && session.isActive && session.expiresAt > new Date();
  }

  // ============================================================================
  // User Preferences
  // ============================================================================

  getPreferences(): Partial<UserPreferences> {
    const prefsData = this.safeGetItem(STORAGE_KEYS.USER_PREFERENCES);
    return this.parseJSON(prefsData, {});
  }

  setPreferences(preferences: Partial<UserPreferences>): boolean {
    const currentPrefs = this.getPreferences();
    const updatedPrefs = { ...currentPrefs, ...preferences };
    
    return this.safeSetItem(
      STORAGE_KEYS.USER_PREFERENCES, 
      JSON.stringify(updatedPrefs)
    );
  }

  getTheme(): 'light' | 'dark' {
    const theme = this.safeGetItem(STORAGE_KEYS.THEME);
    return theme === 'dark' ? 'dark' : 'light';
  }

  setTheme(theme: 'light' | 'dark'): boolean {
    return this.safeSetItem(STORAGE_KEYS.THEME, theme);
  }

  getLanguage(): 'en' | 'ru' {
    const language = this.safeGetItem(STORAGE_KEYS.LANGUAGE);
    return language === 'ru' ? 'ru' : 'en';
  }

  setLanguage(language: 'en' | 'ru'): boolean {
    return this.safeSetItem(STORAGE_KEYS.LANGUAGE, language);
  }

  // ============================================================================
  // Search History
  // ============================================================================

  getRecentSearches(): string[] {
    const searches = this.safeGetItem(STORAGE_KEYS.RECENT_SEARCHES);
    return this.parseJSON(searches, []);
  }

  addRecentSearch(query: string): boolean {
    const current = this.getRecentSearches();
    
    // Remove if already exists
    const filtered = current.filter(search => search !== query);
    
    // Add to beginning
    const updated = [query, ...filtered].slice(0, 10); // Keep last 10
    
    return this.safeSetItem(STORAGE_KEYS.RECENT_SEARCHES, JSON.stringify(updated));
  }

  clearRecentSearches(): boolean {
    return this.safeRemoveItem(STORAGE_KEYS.RECENT_SEARCHES);
  }

  // ============================================================================
  // UI State
  // ============================================================================

  getUIState(): Partial<UIState> {
    const uiState = this.safeGetItem(STORAGE_KEYS.UI_STATE);
    return this.parseJSON(uiState, {});
  }

  setUIState(state: Partial<UIState>): boolean {
    const currentState = this.getUIState();
    const updatedState = { ...currentState, ...state };
    
    return this.safeSetItem(STORAGE_KEYS.UI_STATE, JSON.stringify(updatedState));
  }

  setSidebarCollapsed(collapsed: boolean): boolean {
    return this.setUIState({ sidebarCollapsed: collapsed });
  }

  isSidebarCollapsed(): boolean {
    const uiState = this.getUIState();
    return uiState.sidebarCollapsed ?? false;
  }

  addRecentFile(filePath: string): boolean {
    const uiState = this.getUIState();
    const recentFiles = uiState.recentFiles || [];
    
    // Remove if already exists
    const filtered = recentFiles.filter(file => file !== filePath);
    
    // Add to beginning
    const updated = [filePath, ...filtered].slice(0, 20); // Keep last 20
    
    return this.setUIState({ recentFiles: updated });
  }

  getRecentFiles(): string[] {
    const uiState = this.getUIState();
    return uiState.recentFiles || [];
  }

  addBookmark(path: string): boolean {
    const uiState = this.getUIState();
    const bookmarks = uiState.bookmarks || [];
    
    if (!bookmarks.includes(path)) {
      const updated = [...bookmarks, path];
      return this.setUIState({ bookmarks: updated });
    }
    
    return true;
  }

  removeBookmark(path: string): boolean {
    const uiState = this.getUIState();
    const bookmarks = uiState.bookmarks || [];
    
    const updated = bookmarks.filter(bookmark => bookmark !== path);
    return this.setUIState({ bookmarks: updated });
  }

  getBookmarks(): string[] {
    const uiState = this.getUIState();
    return uiState.bookmarks || [];
  }

  // ============================================================================
  // Utility Methods
  // ============================================================================

  clear(): boolean {
    if (!this.isAvailable) return false;
    
    try {
      // Clear all app-related storage
      Object.values(STORAGE_KEYS).forEach(key => {
        localStorage.removeItem(key);
      });
      return true;
    } catch (error) {
      console.warn('Failed to clear localStorage', error);
      return false;
    }
  }

  getStorageSize(): number {
    if (!this.isAvailable) return 0;
    
    try {
      let total = 0;
      Object.values(STORAGE_KEYS).forEach(key => {
        const value = localStorage.getItem(key);
        if (value) {
          total += new Blob([value]).size;
        }
      });
      return total;
    } catch {
      return 0;
    }
  }

  isStorageAvailable(): boolean {
    return this.isAvailable;
  }

  // ============================================================================
  // Migration and Cleanup
  // ============================================================================

  migrateOldData(): void {
    // Handle migration from old storage format if needed
    try {
      // Example: migrate old auth_token to new session format
      const oldToken = localStorage.getItem('auth_token');
      const oldUser = localStorage.getItem('user_info');
      
      if (oldToken && oldUser && !this.getSession()) {
        // Convert old format to new format
        // This is just an example - implement based on your old format
        localStorage.removeItem('auth_token');
        localStorage.removeItem('user_info');
      }
    } catch (error) {
      console.warn('Failed to migrate old storage data', error);
    }
  }

  cleanupExpiredData(): void {
    // Remove expired sessions and old data
    try {
      const session = this.getSession();
      if (session && session.expiresAt <= new Date()) {
        this.removeSession();
      }
      
      // Could add more cleanup logic here
    } catch (error) {
      console.warn('Failed to cleanup expired data', error);
    }
  }
}

// ============================================================================
// Default Instance
// ============================================================================

export const localStorageAdapter = new LocalStorageAdapter();

// Initialize cleanup on load
localStorageAdapter.migrateOldData();
localStorageAdapter.cleanupExpiredData(); 