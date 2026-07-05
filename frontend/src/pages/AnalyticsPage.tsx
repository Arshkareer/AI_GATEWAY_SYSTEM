import React from 'react';

const AnalyticsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Analytics
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Comprehensive analytics and insights for your AI usage
          </p>
        </div>
      </div>

      <div className="bg-white p-12 rounded-lg shadow text-center">
        <div className="w-12 h-12 mx-auto bg-blue-100 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Advanced Analytics Coming Soon</h2>
        <p className="text-gray-600 mb-6">
          This page will contain detailed analytics, cost breakdowns, usage trends, and AI-powered insights.
        </p>
        <div className="flex justify-center space-x-4">
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Cost Analysis
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Usage Trends
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            AI Insights
          </span>
        </div>
      </div>
    </div>
  );
};

export default AnalyticsPage;