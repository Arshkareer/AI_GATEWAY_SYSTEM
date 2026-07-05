import React from 'react';
import { Link } from 'react-router-dom';
import { 
  CpuChipIcon, 
  ChartBarIcon, 
  DocumentTextIcon,
  ArrowPathIcon 
} from '@heroicons/react/24/outline';
import { useDashboardStore } from '../../stores/dashboardStore';

const QuickActions: React.FC = () => {
  const { fetchDashboardMetrics, loading } = useDashboardStore();

  const handleRefresh = () => {
    fetchDashboardMetrics();
  };

  return (
    <div className="flex space-x-3">
      {/* Refresh Button */}
      <button
        onClick={handleRefresh}
        disabled={loading === 'loading'}
        className="btn btn-secondary btn-sm"
        title="Refresh Dashboard"
      >
        <ArrowPathIcon className={`h-4 w-4 ${loading === 'loading' ? 'animate-spin' : ''}`} />
        <span className="ml-1 hidden sm:inline">Refresh</span>
      </button>

      {/* Quick Action Buttons */}
      <Link to="/gateway" className="btn btn-primary btn-sm">
        <CpuChipIcon className="h-4 w-4" />
        <span className="ml-1 hidden sm:inline">AI Gateway</span>
      </Link>

      <Link to="/analytics" className="btn btn-secondary btn-sm">
        <ChartBarIcon className="h-4 w-4" />
        <span className="ml-1 hidden sm:inline">Analytics</span>
      </Link>

      <Link to="/logs" className="btn btn-secondary btn-sm">
        <DocumentTextIcon className="h-4 w-4" />
        <span className="ml-1 hidden sm:inline">Logs</span>
      </Link>
    </div>
  );
};

export default QuickActions;