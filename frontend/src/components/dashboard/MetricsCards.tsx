import React from 'react';
import { DashboardMetrics } from '../../types';
import { 
  CursorArrowRaysIcon,
  CurrencyDollarIcon,
  ClockIcon,
  ExclamationTriangleIcon
} from '@heroicons/react/24/outline';

interface MetricsCardsProps {
  metrics: DashboardMetrics | null;
}

const MetricsCards: React.FC<MetricsCardsProps> = ({ metrics }) => {
  if (!metrics) {
    return (
      <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
        {[...Array(4)].map((_, i) => (
          <div key={i} className="bg-white p-6 rounded-lg shadow animate-pulse">
            <div className="h-4 bg-gray-200 rounded w-24 mb-2"></div>
            <div className="h-8 bg-gray-200 rounded w-16 mb-2"></div>
            <div className="h-3 bg-gray-200 rounded w-20"></div>
          </div>
        ))}
      </div>
    );
  }

  const cards = [
    {
      title: 'Total Requests',
      value: metrics.total_requests_today.toLocaleString(),
      change: metrics.requests_growth,
      icon: CursorArrowRaysIcon,
      color: 'primary'
    },
    {
      title: 'Total Cost',
      value: `$${metrics.total_cost_today.toFixed(2)}`,
      change: metrics.cost_growth,
      icon: CurrencyDollarIcon,
      color: 'success'
    },
    {
      title: 'Avg Latency',
      value: `${Math.round(metrics.avg_latency_today)}ms`,
      change: metrics.latency_change,
      icon: ClockIcon,
      color: 'warning',
      inverse: true // For latency, lower is better
    },
    {
      title: 'Error Rate',
      value: `${metrics.error_rate_today.toFixed(1)}%`,
      change: 0, // Calculate error rate change if available
      icon: ExclamationTriangleIcon,
      color: 'danger',
      inverse: true
    }
  ];

  const getChangeColor = (change: number, inverse = false) => {
    if (change === 0) return 'text-gray-600';
    
    const isPositive = change > 0;
    if (inverse) {
      return isPositive ? 'text-red-600' : 'text-green-600';
    } else {
      return isPositive ? 'text-green-600' : 'text-red-600';
    }
  };

  const getChangeIcon = (change: number, inverse = false) => {
    if (change === 0) return '→';
    
    const isPositive = change > 0;
    if (inverse) {
      return isPositive ? '↑' : '↓';
    } else {
      return isPositive ? '↑' : '↓';
    }
  };

  return (
    <div className="grid grid-cols-1 gap-6 sm:grid-cols-2 lg:grid-cols-4">
      {cards.map((card, index) => (
        <div
          key={card.title}
          className="stat-card hover:shadow-md transition-shadow duration-200"
          style={{ animationDelay: `${index * 100}ms` }}
        >
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <div className={`w-8 h-8 bg-${card.color}-100 rounded-lg flex items-center justify-center`}>
                <card.icon className={`w-5 h-5 text-${card.color}-600`} />
              </div>
            </div>
            <div className="ml-5 w-0 flex-1">
              <dl>
                <dt className="stat-label">{card.title}</dt>
                <dd className="stat-value">{card.value}</dd>
                {card.change !== undefined && (
                  <dd className={`flex items-baseline ${getChangeColor(card.change, card.inverse)}`}>
                    <span className="stat-change text-sm font-medium">
                      {getChangeIcon(card.change, card.inverse)} {Math.abs(card.change).toFixed(1)}%
                    </span>
                    <span className="ml-2 text-xs font-normal text-gray-500">
                      vs yesterday
                    </span>
                  </dd>
                )}
              </dl>
            </div>
          </div>
        </div>
      ))}
    </div>
  );
};

export default MetricsCards;