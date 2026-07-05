import React, { useState } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement,
} from 'chart.js';
import { Line, Bar, Doughnut } from 'react-chartjs-2';
import { DashboardMetrics } from '../../types';

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  Title,
  Tooltip,
  Legend,
  BarElement,
  ArcElement
);

interface UsageChartsProps {
  metrics: DashboardMetrics | null;
}

const UsageCharts: React.FC<UsageChartsProps> = ({ metrics }) => {
  const [activeTab, setActiveTab] = useState<'requests' | 'cost' | 'latency' | 'providers'>('requests');

  if (!metrics) {
    return (
      <div className="bg-white p-6 rounded-lg shadow">
        <div className="animate-pulse">
          <div className="h-4 bg-gray-200 rounded w-32 mb-4"></div>
          <div className="h-64 bg-gray-200 rounded"></div>
        </div>
      </div>
    );
  }

  const tabs = [
    { key: 'requests' as const, label: 'Requests' },
    { key: 'cost' as const, label: 'Cost' },
    { key: 'latency' as const, label: 'Latency' },
    { key: 'providers' as const, label: 'Providers' },
  ];

  // Prepare chart data
  const getTimelineLabels = (timeline: any[]) => {
    return timeline.map(item => {
      const date = new Date(item.timestamp);
      return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    });
  };

  const requestsChartData = {
    labels: getTimelineLabels(metrics.requests_timeline || []),
    datasets: [
      {
        label: 'Requests per Hour',
        data: metrics.requests_timeline?.map(item => item.value) || [],
        borderColor: 'rgb(59, 130, 246)',
        backgroundColor: 'rgba(59, 130, 246, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const costChartData = {
    labels: getTimelineLabels(metrics.cost_timeline || []),
    datasets: [
      {
        label: 'Cost ($)',
        data: metrics.cost_timeline?.map(item => item.value) || [],
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const latencyChartData = {
    labels: getTimelineLabels(metrics.latency_timeline || []),
    datasets: [
      {
        label: 'Average Latency (ms)',
        data: metrics.latency_timeline?.map(item => item.value) || [],
        borderColor: 'rgb(245, 158, 11)',
        backgroundColor: 'rgba(245, 158, 11, 0.1)',
        tension: 0.4,
        fill: true,
      },
    ],
  };

  const providerChartData = {
    labels: metrics.provider_stats?.map(stat => stat.provider) || [],
    datasets: [
      {
        data: metrics.provider_stats?.map(stat => stat.market_share) || [],
        backgroundColor: [
          'rgba(59, 130, 246, 0.8)',
          'rgba(16, 185, 129, 0.8)',
          'rgba(245, 158, 11, 0.8)',
          'rgba(239, 68, 68, 0.8)',
        ],
        borderColor: [
          'rgba(59, 130, 246, 1)',
          'rgba(16, 185, 129, 1)',
          'rgba(245, 158, 11, 1)',
          'rgba(239, 68, 68, 1)',
        ],
        borderWidth: 2,
      },
    ],
  };

  const chartOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'top' as const,
      },
    },
    scales: {
      x: {
        grid: {
          display: false,
        },
      },
      y: {
        beginAtZero: true,
        grid: {
          color: 'rgba(0, 0, 0, 0.05)',
        },
      },
    },
  };

  const doughnutOptions = {
    responsive: true,
    maintainAspectRatio: false,
    plugins: {
      legend: {
        position: 'bottom' as const,
      },
    },
  };

  const renderChart = () => {
    switch (activeTab) {
      case 'requests':
        return <Line data={requestsChartData} options={chartOptions} />;
      case 'cost':
        return <Line data={costChartData} options={chartOptions} />;
      case 'latency':
        return <Line data={latencyChartData} options={chartOptions} />;
      case 'providers':
        return <Doughnut data={providerChartData} options={doughnutOptions} />;
      default:
        return null;
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <div className="flex items-center justify-between mb-6">
        <h3 className="text-lg font-medium text-gray-900">Usage Analytics</h3>
        <div className="flex space-x-1 bg-gray-100 p-1 rounded-lg">
          {tabs.map((tab) => (
            <button
              key={tab.key}
              onClick={() => setActiveTab(tab.key)}
              className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors duration-200 ${
                activeTab === tab.key
                  ? 'bg-white text-gray-900 shadow-sm'
                  : 'text-gray-600 hover:text-gray-900'
              }`}
            >
              {tab.label}
            </button>
          ))}
        </div>
      </div>

      <div className="h-64">
        {renderChart()}
      </div>

      {/* Chart Summary */}
      <div className="mt-4 grid grid-cols-2 gap-4 pt-4 border-t border-gray-200">
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">
            {activeTab === 'requests' && metrics.requests_last_hour}
            {activeTab === 'cost' && `$${metrics.current_cost_per_hour.toFixed(2)}`}
            {activeTab === 'latency' && `${Math.round(metrics.avg_latency_today)}ms`}
            {activeTab === 'providers' && metrics.provider_stats?.length || 0}
          </div>
          <div className="text-sm text-gray-500">
            {activeTab === 'requests' && 'Last Hour'}
            {activeTab === 'cost' && 'Current Hour'}
            {activeTab === 'latency' && 'Average Today'}
            {activeTab === 'providers' && 'Active Providers'}
          </div>
        </div>
        <div className="text-center">
          <div className="text-2xl font-bold text-gray-900">
            {activeTab === 'requests' && metrics.active_users_today}
            {activeTab === 'cost' && metrics.most_expensive_request_today.toFixed(2)}
            {activeTab === 'latency' && metrics.error_rate_today.toFixed(1)}
            {activeTab === 'providers' && metrics.top_model_today}
          </div>
          <div className="text-sm text-gray-500">
            {activeTab === 'requests' && 'Active Users'}
            {activeTab === 'cost' && 'Highest Request ($)'}
            {activeTab === 'latency' && 'Error Rate (%)'}
            {activeTab === 'providers' && 'Top Model'}
          </div>
        </div>
      </div>
    </div>
  );
};

export default UsageCharts;