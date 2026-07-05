import React from 'react';

const UsersPage: React.FC = () => {
  return (
    <div className="space-y-6">
      <div className="md:flex md:items-center md:justify-between">
        <div className="min-w-0 flex-1">
          <h1 className="text-2xl font-bold leading-7 text-gray-900 sm:truncate sm:text-3xl sm:tracking-tight">
            Users
          </h1>
          <p className="mt-2 text-sm text-gray-600">
            Manage users, permissions, and usage limits
          </p>
        </div>
      </div>

      <div className="bg-white p-12 rounded-lg shadow text-center">
        <div className="w-12 h-12 mx-auto bg-indigo-100 rounded-lg flex items-center justify-center mb-4">
          <svg className="w-6 h-6 text-indigo-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197m13.5-9a2.5 2.5 0 11-5 0 2.5 2.5 0 015 0z" />
          </svg>
        </div>
        <h2 className="text-xl font-semibold text-gray-900 mb-2">User Management Coming Soon</h2>
        <p className="text-gray-600 mb-6">
          This page will contain user management, role assignment, and usage monitoring.
        </p>
        <div className="flex justify-center space-x-4">
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-indigo-100 text-indigo-800">
            User CRUD
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-yellow-100 text-yellow-800">
            Role Management
          </span>
          <span className="inline-flex items-center px-3 py-1.5 rounded-full text-xs font-medium bg-red-100 text-red-800">
            Usage Limits
          </span>
        </div>
      </div>
    </div>
  );
};

export default UsersPage;