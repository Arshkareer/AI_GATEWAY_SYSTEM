import React from 'react';

const DepartmentsPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Departments
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage departments, budgets, and team analytics
          </p>
        </div>
      </div>

      <div className="bg-white p-12 rounded-lg shadow text-center">
        <div className="w-12 h-12 mx-auto bg-cyan-100 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-cyan-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">Department Management Coming Soon</h2>
        <p className="text-gray-600 mb-6">
          This page will contain department management, budget tracking, and team analytics.
        </p>
        <div className="flex justify-center space-x-4">
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-cyan-100 text-cyan-800">
            Department CRUD
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-green-100 text-green-800">
            Budget Tracking
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-blue-100 text-blue-800">
            Team Analytics
          </span>
        </div>
      </div>
    </div>
  );
};

export default DepartmentsPage;