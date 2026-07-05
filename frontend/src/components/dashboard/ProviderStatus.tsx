import React from 'react';
import { useDashboardStore } from '../../stores/dashboardStore';
import { 
  CheckCircleIcon, 
  ExclamationCircleIcon, 
  XCircleIcon,
  CpuChipIcon 
} from '@heroicons/react/24/outline';

const ProviderStatus: React.FC = () => {
  const { providerStatus, loading } = useDashboardStore();

  if (loading === 'loading' && !providerStatus) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-5 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="space-y-3">
            {[...Array(3)].map((_, i) => (
              <div key={i} className="flex items-center space-x-3">
                <div className="h-4 w-4 bg-gray-200 rounded-full"></div>
                <div className="h-4 bg-gray-200 rounded w-24"></div>
                <div className="h-3 bg-gray-200 rounded w-16 ml-auto"></div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  const getStatusIcon = (healthy: boolean) => {
    if (healthy) {
      return <CheckCircleIcon className="h-5 w-5 text-green-500" />;
    } else {
      return <XCircleIcon className="h-5 w-5 text-red-500" />;
    }
  };

  const getStatusText = (healthy: boolean) => {
    return healthy ? 'Healthy' : 'Unavailable';
  };

  const getStatusColor = (healthy: boolean) => {
    return healthy ? 'text-green-700 bg-green-50' : 'text-red-700 bg-red-50';
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-4">
        <h3 className="text-lg font-medium text-gray-900">Provider Status</h3>
        <CpuChipIcon className="h-5 w-5 text-gray-400" />
      </div>

      {!providerStatus?.providers ? (
        <div className="text-center py-8">
          <ExclamationCircleIcon className="h-12 w-12 text-gray-400 mx-auto mb-2" />
          <p className="text-gray-500">No provider data available</p>
        </div>
      ) : (
        <div className="space-y-4">
          {Object.entries(providerStatus.providers).map(([provider, info]: [string, any]) => (
            <div key={provider} className="flex items-center justify-between">
              <div className="flex items-center space-x-3">
                {getStatusIcon(info.healthy)}
                <div>
                  <div className="font-medium text-gray-900 capitalize">
                    {provider}
                  </div>
                  <div className="text-sm text-gray-500">
                    {info.supported_models?.length || 0} models
                  </div>
                </div>
              </div>
              <span className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${getStatusColor(info.healthy)}`}>
                {getStatusText(info.healthy)}
              </span>
            </div>
          ))}

          {/* Summary Stats */}
          <div className="pt-4 border-t border-gray-200">
            <div className="grid grid-cols-2 gap-4 text-center">
              <div>
                <div className="text-2xl font-bold text-green-600">
                  {providerStatus.healthy_providers || 0}
                </div>
                <div className="text-sm text-gray-500">Healthy</div>
              </div>
              <div>
                <div className="text-2xl font-bold text-gray-900">
                  {providerStatus.total_providers || 0}
                </div>
                <div className="text-sm text-gray-500">Total</div>
              </div>
            </div>
          </div>

          {/* Last Updated */}
          {providerStatus.timestamp && (
            <div className="pt-2 text-center">
              <p className="text-xs text-gray-500">
                Updated: {new Date(providerStatus.timestamp).toLocaleTimeString()}
              </p>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

export default ProviderStatus;