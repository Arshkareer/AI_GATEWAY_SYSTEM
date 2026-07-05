import React from 'react';

const GatewayPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            AI Gateway
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Interactive AI chat interface with model selection and monitoring
          </p>
        </div>
      </div>

      <div className="bg-white p-12 rounded-lg shadow text-center">
        <div className="w-12 h-12 mx-auto bg-purple-100 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">AI Gateway Interface Coming Soon</h2>
        <p className="text-gray-600 mb-6">
          This page will contain an interactive chat interface, model selection, and real-time monitoring.
        </p>
        <div className="flex justify-center space-x-4">
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-purple-100 text-purple-800">
            Multi-Provider Chat
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Model Selection
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Real-time Monitoring
          </span>
        </div>
      </div>
    </div>
  );
};

export default GatewayPage;