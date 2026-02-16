import { authAPI, Session, SessionResponse, User } from '@/services/custom/auth';
import { createContext, ReactNode, useContext, useEffect, useState } from 'react';

interface AuthContextType {
  user?: User;
  session: Session | null;
  loading: boolean;
  signOut: () => Promise<void>;
  refreshAuth: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType>({
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
  const [session, setSession] = useState<Session | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const checkAuth = async () => {
      try {
        const responseData: SessionResponse = await authAPI.getSession();

        if (responseData.meta.is_authenticated) {
          setSession(responseData.data);
        } else {
          setSession(null);
        }
      } catch (error) {
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
      setSession(null);
      window.location.href = '/';
    } catch (error: any) {
      // If error message or response indicates 401, treat as successful logout
      if (
        error &&
        typeof error === 'object' &&
        (error.message?.includes('401') || error.message?.toLowerCase().includes('unauthorized'))
      ) {
        setSession(null);
        window.location.href = '/';
      } else {
        console.error('Logout failed:', error);
        // Still clear local state even if logout call fails
        setSession(null);
      }
    }
  };

  const refreshAuth = async () => {
    try {
      const responseData: SessionResponse = await authAPI.getSession();

      if (responseData.meta.is_authenticated) {
        setSession(responseData.data);
      } else {
        setSession(null);
      }
    } catch (error) {
      console.error('Auth refresh failed:', error);
      setSession(null);
    }
  };

  const value = {
    user: session?.user,
    session,
    loading,
    signOut,
    refreshAuth,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
