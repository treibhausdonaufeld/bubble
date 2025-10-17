import { authAPI, SessionResponse } from '@/services/custom/auth';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

// Custom types for Django session auth
interface User {
  id: string | number;
  uuid: string;
  email: string;
  username: string;
  display: string;
  has_usable_password: boolean;
}

interface Session {
  user: User;
  methods: Array<{
    method: 'password' | 'socialaccount' | 'mfa';
    at: number;
    email?: string;
    username?: string;
    reauthenticated?: boolean;
    provider?: string;
    uid?: string;
    type?: 'recovery_codes' | 'totp';
  }>;
}

interface AuthContextType {
  user: User | null;
  session: Session | null;
  loading: boolean;
  signOut: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
  user: null,
  session: null,
  loading: true,
  signOut: async () => {},
  refreshAuth: async () => {},
});

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
};

export const AuthProvider = ({ children }: { children: ReactNode }) => {
  const [user, setUser] = useState<User | null>(null);
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const responseData: SessionResponse = await authAPI.getSession();

        if (responseData.meta.is_authenticated) {
          const userData: User = {
            id: responseData.data.user.id,
            uuid: responseData.data.user.uuid,
            email: responseData.data.user.email,
            username: responseData.data.user.username,
            display: responseData.data.user.display,
            has_usable_password: responseData.data.user.has_usable_password,
          };

          const sessionData: Session = {
            user: userData,
            methods: responseData.data.methods,
          };

          setUser(userData);
          setSession(sessionData);
        } else {
          setUser(null);
          setSession(null);
        }
      } catch (error) {
        setUser(null);
        setSession(null);
      } finally {
        setLoading(false);
      }
    };

    checkAuth();
  }, []);

  const signOut = async () => {
    try {
      await authAPI.logout();
      // Clear local state and refresh
      setUser(null);
      setSession(null);
      window.location.href = '/';
    } catch (error: any) {
      // If error message or response indicates 401, treat as successful logout
      if (
        error &&
        typeof error === 'object' &&
        (error.message?.includes('401') || error.message?.toLowerCase().includes('unauthorized'))
      ) {
        setUser(null);
        setSession(null);
        window.location.href = '/';
      } else {
        console.error('Logout failed:', error);
        // Still clear local state even if logout call fails
        setUser(null);
        setSession(null);
      }
    }
  };

  const refreshAuth = async () => {
    try {
      const responseData: SessionResponse = await authAPI.getSession();

      if (responseData.meta.is_authenticated) {
        const userData: User = {
          id: responseData.data.user.id,
          email: responseData.data.user.email,
          username: responseData.data.user.username,
          display: responseData.data.user.display,
          has_usable_password: responseData.data.user.has_usable_password,
        };

        const sessionData: Session = {
          user: userData,
          methods: responseData.data.methods,
        };

        setUser(userData);
        setSession(sessionData);
      } else {
        setUser(null);
        setSession(null);
      }
    } catch (error) {
      console.error('Auth refresh failed:', error);
      setUser(null);
      setSession(null);
    }
  };

  const value = {
    user,
    session,
    loading,
    signOut,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
