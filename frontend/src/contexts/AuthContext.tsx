import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

interface User {
  user_id: string;
  email: string;
  name: string;
  budget_limit: number;
  current_usage: number;
  scopes: string[];
  is_active: boolean;
}

interface AuthContextType {
  isAuthenticated: boolean;
  user: User | null;
  token: string | null;
  login: (token: string, user: User) => void;
  logout: () => void;
  loading: boolean;
}

// Context7 pattern: explicit export of context
export const AuthContext = createContext<AuthContextType | undefined>(undefined);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

interface AuthProviderProps {
  children: ReactNode;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({ children }) => {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    // Check for existing token and user info on app start
    const savedToken = localStorage.getItem('auth_token');
    const savedUser = localStorage.getItem('user_info');

    if (savedToken && savedUser) {
      try {
        const userInfo = JSON.parse(savedUser);
        setToken(savedToken);
        setUser(userInfo);
        setIsAuthenticated(true);
        
        // Verify token is still valid
        verifyToken(savedToken);
      } catch (error) {
        console.error('Error parsing saved user info:', error);
        logout();
      }
    }
    
    setLoading(false);
  }, []);

  const verifyToken = async (tokenToVerify: string) => {
    try {
      const response = await fetch('/auth/verify', {
        headers: {
          'Authorization': `Bearer ${tokenToVerify}`,
        },
      });

      if (!response.ok) {
        // Token is invalid, logout user
        logout();
      }
    } catch (error) {
      console.error('Token verification failed:', error);
      logout();
    }
  };

  const login = (newToken: string, newUser: User) => {
    setToken(newToken);
    setUser(newUser);
    setIsAuthenticated(true);
    
    // Save to localStorage
    localStorage.setItem('auth_token', newToken);
    localStorage.setItem('user_info', JSON.stringify(newUser));
  };

  const logout = () => {
    setToken(null);
    setUser(null);
    setIsAuthenticated(false);
    
    // Clear localStorage
    localStorage.removeItem('auth_token');
    localStorage.removeItem('user_info');
  };

  const value: AuthContextType = {
    isAuthenticated,
    user,
    token,
    login,
    logout,
    loading,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};
