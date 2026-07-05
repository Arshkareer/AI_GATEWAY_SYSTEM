import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { RequestLog } from '../../types';
import apiService from '../../services/api';
import { 
  CheckCircleIcon, 
  XCircleIcon, 
  ClockIcon,
  ExclamationTriangleIcon 
} from '@heroicons/react/24/outline';

const RecentActivity: React.FC = () => {
  const [recentLogs, setRecentLogs] = useState<RequestLog[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const fetchRecentLogs = async () => {
      try {
        setLoading(true);
        // Mock data for now - replace with real API call
        const mockLogs: RequestLog[] = [
          {
            id: 1,
            request_id: 'req_123456',
            user_id: 1,
            provider: 'openai',
            model_name: 'gpt-4',
            prompt_tokens: 150,
            response_tokens: 200,
            total_tokens: 350,
            latency_ms: 1250,
            status: 'success',
            total_cost: 0.021,
            currency: 'USD',
            created_at: new Date(Date.now() - 5 * 60000).toISOString(), // 5 minutes ago
          },
          {
            id: 2,
            request_id: 'req_123457',
            user_id: 2,
            provider: 'anthropic',
            model_name: 'claude-3-haiku',
            prompt_tokens: 75,
            response_tokens: 100,
            total_tokens: 175,
            latency_ms: 800,
            status: 'success',
            total_cost: 0.0044,
            currency: 'USD',
            created_at: new Date(Date.now() - 10 * 60000).toISOString(), // 10 minutes ago
          },
          {
            id: 3,
            request_id: 'req_123458',
            user_id: 1,
            provider: 'openai',
            model_name: 'gpt-3.5-turbo',
            prompt_tokens: 200,
            response_tokens: 0,
            total_tokens: 200,
            latency_ms: 0,
            status: 'error',
            total_cost: 0,
            currency: 'USD',
            error_message: 'Rate limit exceeded',
            created_at: new Date(Date.now() - 15 * 60000).toISOString(), // 15 minutes ago
          },
        ];
        
        setRecentLogs(mockLogs);
      } catch (error) {
        console.error('Failed to fetch recent logs:', error);
      } finally {
        setLoading(false);
      }
    };

    fetchRecentLogs();
  }, []);

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
      case 'error':
        return <XCircleIcon className="h-5 w-5 text-red-500" />;
      case 'timeout':
        return <ClockIcon className="h-5 w-5 text-yellow-500" />;
      case 'rate_limited':
        return <ExclamationTriangleIcon className="h-5 w-5 text-orange-500" />;
      default:
        return <div className="h-5 w-5 bg-gray-300 rounded-full" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'success':
        return 'text-green-700 bg-green-50';
      case 'error':
        return 'text-red-700 bg-red-50';
      case 'timeout':
        return 'text-yellow-700 bg-yellow-50';
      case 'rate_limited':
        return 'text-orange-700 bg-orange-50';
      default:
        return 'text-gray-700 bg-gray-50';
    }
  };

  const formatTimeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    
    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  if (loading) {
    return (
      <div className="bg-white rounded-lg shadow">
        <div className="px-6 py-4 border-b border-gray-200">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
        </div>
        <div className="p-6">
          <div className="animate-pulse space-y-4">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-4">
                <div className="h-5 w-5 bg-gray-200 rounded-full"></div>
                <div className="flex-1 space-y-2">
                  <div className="h-4 bg-gray-200 rounded w-3/4"></div>
                  <div className="h-3 bg-gray-200 rounded w-1/2"></div>
                </div>
                <div className="h-6 bg-gray-200 rounded w-16"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg shadow">
      <div className="px-6 py-4 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <h3 className="text-lg font-medium text-gray-900">Recent Activity</h3>
          <Link 
            to="/logs" 
            className="text-sm text-primary-600 hover:text-primary-500 font-medium"
          >
            View all
          </Link>
        </div>
      </div>
      
      <div className="divide-y divide-gray-200">
        {recentLogs.length === 0 ? (
          <div className="p-6 text-center text-gray-500">
            No recent activity
          </div>
        ) : (
          recentLogs.map((log) => (
            <div key={log.id} className="p-6 hover:bg-gray-50">
              <div className="flex items-center space-x-4">
                {getStatusIcon(log.status)}
                <div className="flex-1 min-w-0">
                  <div className="flex items-center space-x-3">
                    <p className="text-sm font-medium text-gray-900 truncate">
                      {log.provider} • {log.model_name}
                    </p>
                    <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(log.status)}`}>
                      {log.status}
                    </span>
                  </div>
                  <div className="mt-1 flex items-center space-x-4 text-sm text-gray-500">
                    <span>ID: {log.request_id}</span>
                    <span>{log.total_tokens} tokens</span>
                    {log.status === 'success' && (
                      <>
                        <span>${log.total_cost.toFixed(4)}</span>
                        <span>{log.latency_ms}ms</span>
                      </>
                    )}
                    {log.error_message && (
                      <span className="text-red-600">{log.error_message}</span>
                    )}
                  </div>
                </div>
                <div className="text-sm text-gray-500">
                  {formatTimeAgo(log.created_at)}
                </div>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
};

export default RecentActivity;