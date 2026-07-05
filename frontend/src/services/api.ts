import axios, { AxiosInstance, AxiosResponse, AxiosError } from 'axios';
import { 
  LoginCredentials, 
  AuthResponse, 
  User, 
  DashboardMetrics,
  GatewayRequest,
  GatewayResponse,
  ModelInfo,
  RequestLog,
  Department,
  ApiResponse 
} from '../types';

class ApiService {
  private api: AxiosInstance;
  private baseURL: string;

  constructor() {
    this.baseURL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';
    
    this.api = axios.create({
      baseURL: this.baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors() {
    // Request interceptor to add auth token
    this.api.interceptors.request.use(
      (config) => {
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }
        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // Response interceptor to handle errors and token refresh
    this.api.interceptors.response.use(
      (response: AxiosResponse) => response,
      async (error: AxiosError) => {
        const originalRequest = error.config as any;

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true;
          
          try {
            await this.refreshToken();
            const token = localStorage.getItem('access_token');
            if (token && originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            return this.api(originalRequest);
          } catch (refreshError) {
            this.logout();
            window.location.href = '/login';
            return Promise.reject(refreshError);
          }
        }

        return Promise.reject(error);
      }
    );
  }

  // Authentication Methods
  async login(credentials: LoginCredentials): Promise<AuthResponse> {
    const response = await this.api.post<AuthResponse>('/auth/login', credentials);
    const { access_token, refresh_token } = response.data;
    
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', refresh_token);
    
    return response.data;
  }

  async logout(): Promise<void> {
    try {
      const refreshToken = localStorage.getItem('refresh_token');
      if (refreshToken) {
        await this.api.post('/auth/logout', { refresh_token: refreshToken });
      }
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      localStorage.removeItem('refresh_token');
    }
  }

  async refreshToken(): Promise<void> {
    const refreshToken = localStorage.getItem('refresh_token');
    if (!refreshToken) {
      throw new Error('No refresh token available');
    }

    const response = await this.api.post<AuthResponse>('/auth/refresh', {
      refresh_token: refreshToken
    });

    const { access_token, refresh_token: newRefreshToken } = response.data;
    localStorage.setItem('access_token', access_token);
    localStorage.setItem('refresh_token', newRefreshToken);
  }

  async getCurrentUser(): Promise<User> {
    const response = await this.api.get<User>('/auth/me');
    return response.data;
  }

  // Dashboard and Analytics Methods
  async getDashboardMetrics(): Promise<DashboardMetrics> {
    const response = await this.api.get<DashboardMetrics>('/analytics/dashboard');
    return response.data;
  }

  async getUserAnalytics(userId?: number, startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const url = userId ? `/analytics/users/${userId}` : '/analytics/users/me';
    const response = await this.api.get(`${url}?${params.toString()}`);
    return response.data;
  }

  async getDepartmentAnalytics(departmentId: number, startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await this.api.get(`/analytics/departments/${departmentId}?${params.toString()}`);
    return response.data;
  }

  async getCostAnalysis(startDate?: string, endDate?: string) {
    const params = new URLSearchParams();
    if (startDate) params.append('start_date', startDate);
    if (endDate) params.append('end_date', endDate);
    
    const response = await this.api.get(`/analytics/cost?${params.toString()}`);
    return response.data;
  }

  async getPerformanceMetrics(provider?: string, model?: string) {
    const params = new URLSearchParams();
    if (provider) params.append('provider', provider);
    if (model) params.append('model', model);
    
    const response = await this.api.get(`/analytics/performance?${params.toString()}`);
    return response.data;
  }

  // Gateway Methods
  async sendChatRequest(request: GatewayRequest): Promise<GatewayResponse> {
    const response = await this.api.post<GatewayResponse>('/gateway/chat', request);
    return response.data;
  }

  async getAvailableModels(): Promise<ModelInfo[]> {
    const response = await this.api.get<ModelInfo[]>('/gateway/models');
    return response.data;
  }

  async getProviderStatus() {
    const response = await this.api.get('/gateway/providers');
    return response.data;
  }

  async getUserQuota() {
    const response = await this.api.get('/gateway/usage/quota');
    return response.data;
  }

  async getGatewayStats() {
    const response = await this.api.get('/gateway/stats');
    return response.data;
  }

  // User Management Methods
  async getUsers(skip = 0, limit = 50, search?: string) {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (search) params.append('search', search);
    
    const response = await this.api.get<User[]>(`/users?${params.toString()}`);
    return response.data;
  }

  async getUser(userId: number): Promise<User> {
    const response = await this.api.get<User>(`/users/${userId}`);
    return response.data;
  }

  async updateUser(userId: number, updates: Partial<User>): Promise<User> {
    const response = await this.api.put<User>(`/users/${userId}`, updates);
    return response.data;
  }

  async deleteUser(userId: number): Promise<void> {
    await this.api.delete(`/users/${userId}`);
  }

  // Department Management Methods  
  async getDepartments(skip = 0, limit = 50, search?: string): Promise<Department[]> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (search) params.append('search', search);
    
    const response = await this.api.get<Department[]>(`/departments?${params.toString()}`);
    return response.data;
  }

  async getDepartment(departmentId: number): Promise<Department> {
    const response = await this.api.get<Department>(`/departments/${departmentId}`);
    return response.data;
  }

  async createDepartment(department: Partial<Department>): Promise<Department> {
    const response = await this.api.post<Department>('/departments', department);
    return response.data;
  }

  async updateDepartment(departmentId: number, updates: Partial<Department>): Promise<Department> {
    const response = await this.api.put<Department>(`/departments/${departmentId}`, updates);
    return response.data;
  }

  async deleteDepartment(departmentId: number): Promise<void> {
    await this.api.delete(`/departments/${departmentId}`);
  }

  // Request Logs Methods
  async getRequestLogs(
    skip = 0, 
    limit = 50, 
    userId?: number, 
    provider?: string, 
    status?: string
  ): Promise<RequestLog[]> {
    const params = new URLSearchParams();
    params.append('skip', skip.toString());
    params.append('limit', limit.toString());
    if (userId) params.append('user_id', userId.toString());
    if (provider) params.append('provider', provider);
    if (status) params.append('status', status);
    
    const response = await this.api.get<RequestLog[]>(`/logs?${params.toString()}`);
    return response.data;
  }

  // Health Check
  async healthCheck() {
    const response = await this.api.get('/health');
    return response.data;
  }

  // Utility Methods
  isAuthenticated(): boolean {
    return !!localStorage.getItem('access_token');
  }

  getAuthToken(): string | null {
    return localStorage.getItem('access_token');
  }

  // WebSocket connection helper
  getWebSocketUrl(): string {
    const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsHost = process.env.REACT_APP_WS_URL || `${window.location.host}`;
    return `${wsProtocol}//${wsHost}/ws`;
  }
}

// Error handling helper
export const handleApiError = (error: any): string => {
  if (error.response?.data?.detail) {
    return error.response.data.detail;
  }
  if (error.response?.data?.message) {
    return error.response.data.message;
  }
  if (error.message) {
    return error.message;
  }
  return 'An unexpected error occurred';
};

export const apiService = new ApiService();
export default apiService;