import { useState, useEffect, useCallback } from 'react';
import { User, Token } from '@/types';
import { authApi } from '@/services/api';
import { useRouter } from 'next/router';

interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    token: null,
    isAuthenticated: false,
    isLoading: true,
    error: null,
  });

  const router = useRouter();

  // Initialize auth state from localStorage
  useEffect(() => {
    const initializeAuth = async () => {
      try {
        const token = localStorage.getItem('access_token');
        const userData = localStorage.getItem('user');

        if (token && userData) {
          const user: User = JSON.parse(userData);
          
          // Verify token by calling /me endpoint
          try {
            const response = await authApi.me();
            setAuthState({
              user: response.data,
              token,
              isAuthenticated: true,
              isLoading: false,
              error: null,
            });
          } catch (error) {
            // Token invalid, clear and redirect
            localStorage.removeItem('access_token');
            localStorage.removeItem('user');
            setAuthState({
              user: null,
              token: null,
              isAuthenticated: false,
              isLoading: false,
              error: 'Invalid token',
            });
          }
        } else {
          setAuthState({
            user: null,
            token: null,
            isAuthenticated: false,
            isLoading: false,
            error: null,
          });
        }
      } catch (error) {
        setAuthState({
          user: null,
          token: null,
          isAuthenticated: false,
          isLoading: false,
          error: 'Failed to initialize auth',
        });
      }
    };

    initializeAuth();
  }, [router]);

  // Login function
  const login = useCallback(async (provider: 'google' | 'facebook', token: string) => {
    try {
      setAuthState(prev => ({ ...prev, isLoading: true, error: null }));
      
      const response = provider === 'google' 
        ? await authApi.google(token) 
        : await authApi.facebook(token);

      const { access_token, user } = response.data;

      // Store token and user in localStorage
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      setAuthState({
        user,
        token: access_token,
        isAuthenticated: true,
        isLoading: false,
        error: null,
      });

      return user;
    } catch (error: any) {
      const errorMessage = error.response?.data?.detail || error.message || 'Login failed';
      setAuthState(prev => ({
        ...prev,
        isLoading: false,
        error: errorMessage,
        isAuthenticated: false,
      }));
      throw error;
    }
  }, []);

  // Logout function
  const logout = useCallback(() => {
    localStorage.removeItem('access_token');
    localStorage.removeItem('user');
    
    setAuthState({
      user: null,
      token: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    });

    // Redirect to login page
    router.push('/login');
  }, [router]);

  // Refresh token function
  const refreshToken = useCallback(async () => {
    try {
      const response = await authApi.refresh();
      const { access_token, user } = response.data;

      // Store new token and user
      localStorage.setItem('access_token', access_token);
      localStorage.setItem('user', JSON.stringify(user));

      setAuthState(prev => ({
        ...prev,
        user,
        token: access_token,
        isAuthenticated: true,
      }));

      return access_token;
    } catch (error) {
      // If refresh fails, logout
      logout();
      throw error;
    }
  }, [logout]);

  // Get current user
  const getCurrentUser = useCallback(async () => {
    try {
      const response = await authApi.me();
      const user = response.data;
      
      // Update localStorage and state
      localStorage.setItem('user', JSON.stringify(user));
      setAuthState(prev => ({ ...prev, user }));
      
      return user;
    } catch (error) {
      throw error;
    }
  }, []);

  return {
    ...authState,
    login,
    logout,
    refreshToken,
    getCurrentUser,
  };
}

export default useAuth;
