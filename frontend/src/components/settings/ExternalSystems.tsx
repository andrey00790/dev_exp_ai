import React, { useState } from 'react';
import { 
  LinkIcon, 
  CheckCircleIcon, 
  XCircleIcon,
  EyeIcon,
  EyeSlashIcon 
} from '@heroicons/react/24/outline';

interface ExternalSystem {
  id: string;
  name: string;
  type: 'confluence' | 'jira' | 'gitlab' | 'github';
  url: string;
  username: string;
  token: string;
  isConnected: boolean;
  lastSync?: Date;
}

export default function ExternalSystems() {
  const [systems, setSystems] = useState<ExternalSystem[]>([
    {
      id: '1',
      name: 'Company Confluence',
      type: 'confluence',
      url: 'https://company.atlassian.net',
      username: 'user@company.com',
      token: '***',
      isConnected: true,
      lastSync: new Date('2024-01-15T10:30:00'),
    },
    {
      id: '2',
      name: 'Company Jira',
      type: 'jira',
      url: 'https://company.atlassian.net',
      username: 'user@company.com',
      token: '***',
      isConnected: false,
    },
  ]);

  const [showTokens, setShowTokens] = useState<Record<string, boolean>>({});

  const toggleTokenVisibility = (systemId: string) => {
    setShowTokens(prev => ({
      ...prev,
      [systemId]: !prev[systemId]
    }));
  };

  const getSystemIcon = (type: string) => {
    switch (type) {
      case 'confluence':
        return '📚';
      case 'jira':
        return '🎫';
      case 'gitlab':
        return '🦊';
      case 'github':
        return '🐙';
      default:
        return '🔗';
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900 mb-2">External System Connections</h3>
        <p className="text-sm text-gray-600">
          Configure connections to external systems for data synchronization.
        </p>
      </div>

      <div className="grid gap-6">
        {systems.map((system) => (
          <div key={system.id} className="bg-white border border-gray-200 rounded-lg p-6">
            <div className="flex items-start justify-between">
              <div className="flex items-center space-x-3">
                <div className="text-2xl">{getSystemIcon(system.type)}</div>
                <div>
                  <h4 className="text-lg font-medium text-gray-900">{system.name}</h4>
                  <p className="text-sm text-gray-500 capitalize">{system.type}</p>
                </div>
              </div>
              <div className="flex items-center space-x-2">
                {system.isConnected ? (
                  <div className="flex items-center text-green-600">
                    <CheckCircleIcon className="h-5 w-5 mr-1" />
                    <span className="text-sm">Connected</span>
                  </div>
                ) : (
                  <div className="flex items-center text-red-600">
                    <XCircleIcon className="h-5 w-5 mr-1" />
                    <span className="text-sm">Disconnected</span>
                  </div>
                )}
              </div>
            </div>

            <div className="mt-4 grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  URL
                </label>
                <input
                  type="url"
                  value={system.url}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="https://your-instance.com"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Username/Email
                </label>
                <input
                  type="text"
                  value={system.username}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                  placeholder="user@company.com"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  API Token
                </label>
                <div className="relative">
                  <input
                    type={showTokens[system.id] ? 'text' : 'password'}
                    value={system.token}
                    className="w-full px-3 py-2 pr-10 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
                    placeholder="Enter your API token"
                  />
                  <button
                    type="button"
                    onClick={() => toggleTokenVisibility(system.id)}
                    className="absolute inset-y-0 right-0 pr-3 flex items-center"
                  >
                    {showTokens[system.id] ? (
                      <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                    ) : (
                      <EyeIcon className="h-5 w-5 text-gray-400" />
                    )}
                  </button>
                </div>
              </div>
            </div>

            {system.lastSync && (
              <div className="mt-4 text-sm text-gray-500">
                Last synchronized: {system.lastSync.toLocaleString()}
              </div>
            )}

            <div className="mt-4 flex space-x-3">
              <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
                Test Connection
              </button>
              <button className="px-4 py-2 bg-green-600 text-white rounded-md hover:bg-green-700 transition-colors">
                Save & Sync
              </button>
              <button className="px-4 py-2 border border-gray-300 text-gray-700 rounded-md hover:bg-gray-50 transition-colors">
                Remove
              </button>
            </div>
          </div>
        ))}

        {/* Add New System */}
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-6 text-center">
          <LinkIcon className="h-12 w-12 text-gray-400 mx-auto mb-4" />
          <h4 className="text-lg font-medium text-gray-900 mb-2">Add New System</h4>
          <p className="text-sm text-gray-600 mb-4">
            Connect to Confluence, Jira, GitLab, or GitHub
          </p>
          <button className="px-4 py-2 bg-blue-600 text-white rounded-md hover:bg-blue-700 transition-colors">
            Add Connection
          </button>
        </div>
      </div>
    </div>
  );
} 