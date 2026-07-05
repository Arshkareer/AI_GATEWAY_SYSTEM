import { create } from 'zustand';
import { 
  DashboardMetrics, 
  LoadingState, 
  RealtimeMetrics,
  ModelInfo,
  AnalyticsFilters,
  DateRange 
} from '../types';
import apiService, { handleApiError } from '../services/api';

interface DashboardState {
  // Data
  metrics: DashboardMetrics | null;
  realtimeMetrics: RealtimeMetrics | null;
  availableModels: ModelInfo[];
  providerStatus: any;
  userQuota: any;
  
  // UI State
  loading: LoadingState;
  error: string | null;
  lastUpdated: Date | null;
  autoRefresh: boolean;
  refreshInterval: number; // seconds
  
  // Filters
  filters: AnalyticsFilters;
  
  // Actions
  fetchDashboardMetrics: () => Promise<void>;
  fetchAvailableModels: () => Promise<void>;
  fetchProviderStatus: () => Promise<void>;
  fetchUserQuota: () => Promise<void>;
  updateRealtimeMetrics: (metrics: RealtimeMetrics) => void;
  setAutoRefresh: (enabled: boolean) => void;
  setRefreshInterval: (interval: number) => void;
  updateFilters: (filters: Partial<AnalyticsFilters>) => void;
  clearError: () => void;
  startAutoRefresh: () => void;
  stopAutoRefresh: () => void;
}

export const useDashboardStore = create<DashboardState>((set, get) => ({
  // Initial State
  metrics: null,
  realtimeMetrics: null,
  availableModels: [],
  providerStatus: null,
  userQuota: null,
  loading: 'idle',
  error: null,
  lastUpdated: null,
  autoRefresh: false,
  refreshInterval: 30, // 30 seconds default
  
  filters: {
    dateRange: {
      start: new Date(Date.now() - 24 * 60 * 60 * 1000), // 24 hours ago
      end: new Date()
    }
  },

  // Actions
  fetchDashboardMetrics: async () => {
    try {
      set({ loading: 'loading', error: null });
      
      const metrics = await apiService.getDashboardMetrics();
      
      set({ 
        metrics,
        loading: 'success',
        error: null,
        lastUpdated: new Date()
      });
    } catch (error: any) {
      const errorMessage = handleApiError(error);
      set({ 
        loading: 'error',
        error: errorMessage
      });
    }
  },

  fetchAvailableModels: async () => {
    try {
      const models = await apiService.getAvailableModels();
      set({ availableModels: models });
    } catch (error: any) {
      console.error('Failed to fetch models:', error);
    }
  },

  fetchProviderStatus: async () => {
    try {
      const status = await apiService.getProviderStatus();
      set({ providerStatus: status });
    } catch (error: any) {
      console.error('Failed to fetch provider status:', error);
    }
  },

  fetchUserQuota: async () => {
    try {
      const quota = await apiService.getUserQuota();
      set({ userQuota: quota });
    } catch (error: any) {
      console.error('Failed to fetch user quota:', error);
    }
  },

  updateRealtimeMetrics: (realtimeMetrics: RealtimeMetrics) => {
    set({ realtimeMetrics });
  },

  setAutoRefresh: (autoRefresh: boolean) => {
    set({ autoRefresh });
    
    if (autoRefresh) {
      get().startAutoRefresh();
    } else {
      get().stopAutoRefresh();
    }
  },

  setRefreshInterval: (refreshInterval: number) => {
    set({ refreshInterval });
    
    // Restart auto refresh with new interval
    if (get().autoRefresh) {
      get().stopAutoRefresh();
      get().startAutoRefresh();
    }
  },

  updateFilters: (newFilters: Partial<AnalyticsFilters>) => {
    set(state => ({
      filters: { ...state.filters, ...newFilters }
    }));
    
    // Refresh data with new filters
    get().fetchDashboardMetrics();
  },

  clearError: () => {
    set({ error: null });
  },

  startAutoRefresh: () => {
    const intervalId = setInterval(() => {
      if (get().autoRefresh) {
        get().fetchDashboardMetrics();
        get().fetchProviderStatus();
        get().fetchUserQuota();
      }
    }, get().refreshInterval * 1000);
    
    // Store interval ID for cleanup (would need to be added to state)
    (window as any).dashboardRefreshInterval = intervalId;
  },

  stopAutoRefresh: () => {
    if ((window as any).dashboardRefreshInterval) {
      clearInterval((window as any).dashboardRefreshInterval);
      (window as any).dashboardRefreshInterval = null;
    }
  }
}));