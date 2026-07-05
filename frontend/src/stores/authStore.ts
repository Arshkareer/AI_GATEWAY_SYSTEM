import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { User, LoginCredentials, LoadingState } from '../types';
import apiService, { handleApiError } from '../services/api';

interface AuthState {
  // State
  user: User | null;
  isAuthenticated: boolean;
  loading: LoadingState;
  error: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  refreshUser: () => Promise<void>;
  clearError: () => void;
  setLoading: (loading: LoadingState) => void;
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set, get) => ({
      // Initial State
      user: null,
      isAuthenticated: false,
      loading: 'idle',
      error: null,

      // Actions
      login: async (credentials: LoginCredentials) => {
        try {
          set({ loading: 'loading', error: null });
          
          const authResponse = await apiService.login(credentials);
          
          set({ 
            user: authResponse.user,
            isAuthenticated: true,
            loading: 'success',
            error: null 
          });
        } catch (error: any) {
          const errorMessage = handleApiError(error);
          set({ 
            loading: 'error',
            error: errorMessage,
            user: null,
            isAuthenticated: false 
          });
          throw error;
        }
      },

      logout: async () => {
        try {
          set({ loading: 'loading' });
          
          await apiService.logout();
          
          set({
            user: null,
            isAuthenticated: false,
            loading: 'idle',
            error: null
          });
        } catch (error: any) {
          // Even if logout fails on server, clear local state
          set({
            user: null,
            isAuthenticated: false,
            loading: 'idle',
            error: null
          });
        }
      },

      refreshUser: async () => {
        try {
          if (!apiService.isAuthenticated()) {
            set({
              user: null,
              isAuthenticated: false,
              loading: 'idle',
              error: null
            });
            return;
          }

          set({ loading: 'loading', error: null });
          
          const user = await apiService.getCurrentUser();
          
          set({
            user,
            isAuthenticated: true,
            loading: 'success',
            error: null
          });
        } catch (error: any) {
          const errorMessage = handleApiError(error);
          set({
            loading: 'error',
            error: errorMessage,
            user: null,
            isAuthenticated: false
          });
        }
      },

      clearError: () => {
        set({ error: null });
      },

      setLoading: (loading: LoadingState) => {
        set({ loading });
      }
    }),
    {
      name: 'auth-store',
      partialize: (state) => ({ 
        user: state.user,
        isAuthenticated: state.isAuthenticated 
      }),
    }
  )
);