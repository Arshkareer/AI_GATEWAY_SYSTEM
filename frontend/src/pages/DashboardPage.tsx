import React, { useEffect } from 'react';
import { useDashboardStore } from '../stores/dashboardStore';
import LoadingSpinner from '../components/common/LoadingSpinner';
import MetricsCards from '../components/dashboard/MetricsCards';
import UsageCharts from '../components/dashboard/UsageCharts';
import RecentActivity from '../components/dashboard/RecentActivity';
import ProviderStatus from '../components/dashboard/ProviderStatus';
import QuickActions from '../components/dashboard/QuickActions';

const DashboardPage: React.FC = () => {
  const { 
    metrics, 
    loading, 
    error, 
    lastUpdated,
    fetchDashboardMetrics,
    fetchProviderStatus,
    fetchUserQuota,
    setAutoRefresh 
  } = useDashboardStore();

  useEffect(() => {
    // Initial data fetch
    fetchDashboardMetrics();
    fetchProviderStatus();
    fetchUserQuota();

    // Enable auto-refresh
    setAutoRefresh(true);

    // Cleanup on unmount
    return () => {
      setAutoRefresh(false);
    };
  }, [fetchDashboardMetrics, fetchProviderStatus, fetchUserQuota, setAutoRefresh]);

  if (loading === 'loading' && !metrics) {
    return (
      <div className="flex items-center justify-center min-h-96">
        <LoadingSpinner size="lg" />
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md">
        <div className="flex">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium">Error Loading Dashboard</h3>
            <p className="mt-1 text-sm">{error}</p>
            <div className="mt-3">
              <button 
                onClick={fetchDashboardMetrics}
                className="btn btn-sm btn-secondary"
              >
                Try Again
              </button>
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Dashboard
          </h1>
          <div className="mt-1 flex flex-col sm:mt-0 sm:flex-row sm:flex-wrap sm:space-x-6">
            <div className="mt-2 flex items-center text-sm text-gray-500">
              <svg
                className="mr-1.5 h-5 w-5 flex-shrink-0 text-gray-400"
                viewBox="0 0 20 20"
                fill="currentColor"
              >
                <path
                  fillRule="evenodd"
                  d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z"
                  clipRule="evenodd"
                />
              </svg>
              Last updated: {lastUpdated ? lastUpdated.toLocaleTimeString() : 'Never'}
            </div>
            {loading === 'loading' && (
              <div className="mt-2 flex items-center text-sm text-gray-500">
                <LoadingSpinner size="sm" className="mr-1.5" />
                Updating...
              </div>
            )}
          </div>
        </div>
        <div className="mt-4 flex md:mt-0 md:ml-4">
          <QuickActions />
        </div>
      </div>

      {/* Main Metrics Cards */}
      <MetricsCards metrics={metrics} />

      {/* Charts and Provider Status */}
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
        <div className="lg:col-span-2">
          <UsageCharts metrics={metrics} />
        </div>
        <div>
          <ProviderStatus />
        </div>
      </div>

      {/* Recent Activity */}
      <RecentActivity />
    </div>
  );
};

export default DashboardPage;