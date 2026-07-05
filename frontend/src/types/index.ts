// User Types
export interface User {
  id: number;
  email: string;
  username: string;
  full_name: string;
  role: 'admin' | 'employee' | 'viewer';
  department_id?: number;
  monthly_budget: number;
  total_requests: number;
  total_cost: number;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

// Authentication Types
export interface LoginCredentials {
  email: string;
  password: string;
  remember_me?: boolean;
}

export interface AuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

// Department Types
export interface Department {
  id: number;
  name: string;
  description?: string;
  monthly_budget: number;
  budget_utilization: number;
  remaining_budget: number;
  is_over_budget: boolean;
  user_count: number;
  total_requests: number;
  total_cost: number;
  current_month_cost: number;
  is_active: boolean;
}

// Gateway Types
export interface GatewayRequest {
  messages: Array<{
    role: 'system' | 'user' | 'assistant';
    content: string;
  }>;
  model?: string;
  provider?: 'openai' | 'anthropic' | 'google';
  temperature?: number;
  max_tokens?: number;
  top_p?: number;
  frequency_penalty?: number;
  presence_penalty?: number;
  session_id?: string;
  request_id?: string;
  user_metadata?: Record<string, any>;
  store_prompt?: boolean;
  store_response?: boolean;
  prefer_speed?: boolean;
  prefer_cost?: boolean;
  prefer_quality?: boolean;
}

export interface GatewayResponse {
  request_id: string;
  session_id?: string;
  provider: string;
  model: string;
  content: string;
  finish_reason: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  latency_ms: number;
  cost: number;
  currency: string;
  created_at: string;
  response_metadata?: Record<string, any>;
}

// Analytics Types
export interface DashboardMetrics {
  total_requests_today: number;
  total_cost_today: number;
  avg_latency_today: number;
  error_rate_today: number;
  requests_growth: number;
  cost_growth: number;
  latency_change: number;
  active_users_today: number;
  requests_last_hour: number;
  current_cost_per_hour: number;
  top_user_today?: {
    user_id: number;
    username: string;
    requests: number;
    cost: number;
  };
  top_department_today?: {
    department_id: number;
    name: string;
    requests: number;
    cost: number;
  };
  top_model_today: string;
  most_expensive_request_today: number;
  provider_stats: ProviderStats[];
  requests_timeline: TimeSeriesData[];
  cost_timeline: TimeSeriesData[];
  latency_timeline: TimeSeriesData[];
  error_timeline: TimeSeriesData[];
}

export interface ProviderStats {
  provider: string;
  stats: UsageStats;
  top_models: Array<{ model: string; requests: number; cost: number }>;
  market_share: number;
}

export interface UsageStats {
  total_requests: number;
  successful_requests: number;
  failed_requests: number;
  total_tokens: number;
  prompt_tokens: number;
  completion_tokens: number;
  total_cost: number;
  avg_latency_ms: number;
  success_rate: number;
  avg_cost_per_request: number;
  avg_tokens_per_request: number;
  cost_per_1k_tokens: number;
}

export interface TimeSeriesData {
  timestamp: string;
  value: number;
  label?: string;
}

// Model Types
export interface ModelInfo {
  name: string;
  provider: string;
  description: string;
  max_tokens: number;
  supports_streaming: boolean;
  supports_functions: boolean;
  supports_vision: boolean;
  input_cost_per_1k: number;
  output_cost_per_1k: number;
  avg_latency_ms: number;
  quality_rating: number;
  is_available: boolean;
  rate_limit_per_minute: number;
}

// Request Log Types
export interface RequestLog {
  id: number;
  request_id: string;
  session_id?: string;
  user_id: number;
  department_id?: number;
  provider: string;
  model_name: string;
  prompt_tokens: number;
  response_tokens: number;
  total_tokens: number;
  latency_ms: number;
  status: 'success' | 'error' | 'timeout' | 'rate_limited';
  total_cost: number;
  currency: string;
  created_at: string;
  error_message?: string;
}

// API Response Types
export interface ApiResponse<T> {
  data?: T;
  error?: string;
  message?: string;
  status?: number;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

// Chart Types
export interface ChartData {
  labels: string[];
  datasets: Array<{
    label: string;
    data: number[];
    backgroundColor?: string | string[];
    borderColor?: string;
    borderWidth?: number;
    fill?: boolean;
  }>;
}

// Notification Types
export interface Notification {
  id: string;
  type: 'success' | 'error' | 'warning' | 'info';
  title: string;
  message: string;
  timestamp: Date;
  read: boolean;
  actions?: Array<{
    label: string;
    action: () => void;
  }>;
}

// Filter Types
export interface DateRange {
  start: Date;
  end: Date;
}

export interface AnalyticsFilters {
  dateRange: DateRange;
  providers?: string[];
  models?: string[];
  users?: number[];
  departments?: number[];
  status?: string[];
}

// WebSocket Types
export interface WebSocketMessage {
  type: string;
  data: any;
  timestamp: string;
}

export interface RealtimeMetrics {
  requests_per_second: number;
  active_requests: number;
  avg_response_time: number;
  error_rate: number;
  cost_per_minute: number;
}

// Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    browser: boolean;
    budget_alerts: boolean;
    error_alerts: boolean;
  };
  dashboard: {
    auto_refresh: boolean;
    refresh_interval: number; // seconds
    default_date_range: string;
  };
}

// Export utility types
export type LoadingState = 'idle' | 'loading' | 'success' | 'error';
export type SortDirection = 'asc' | 'desc';
export type TableColumn<T> = {
  key: keyof T;
  label: string;
  sortable?: boolean;
  width?: string;
  render?: (value: any, item: T) => React.ReactNode;
};