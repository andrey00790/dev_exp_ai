import React from 'react';
import { Switch } from '@headlessui/react';
import { ArrowPathIcon } from '@heroicons/react/24/solid';
import { DataSource } from '../../types';
import { formatDistanceToNow } from 'date-fns';

type DataSourceCardProps = {
  source: DataSource;
  onUpdate: (source: DataSource) => void;
  onSync: (sourceType: string) => void;
  isSyncing: boolean;
};

function classNames(...classes) {
  return classes.filter(Boolean).join(' ');
}

const getStatusChip = (status: string) => {
  switch (status) {
    case 'success':
      return <span className="px-2 py-1 text-xs font-medium text-green-700 bg-green-100 rounded-full">Success</span>;
    case 'running':
      return <span className="px-2 py-1 text-xs font-medium text-blue-700 bg-blue-100 rounded-full">Running</span>;
    case 'error':
      return <span className="px-2 py-1 text-xs font-medium text-red-700 bg-red-100 rounded-full">Error</span>;
    default:
      return <span className="px-2 py-1 text-xs font-medium text-gray-700 bg-gray-100 rounded-full">Pending</span>;
  }
};

export default function DataSourceCard({ source, onUpdate, onSync, isSyncing }: DataSourceCardProps) {
  const handleFieldChange = (field: keyof DataSource, value: any) => {
    onUpdate({ ...source, [field]: value });
  };

  return (
    <div className="bg-white border border-gray-200 rounded-lg shadow-sm p-6">
      <div className="flex items-start justify-between">
        <div>
          <h4 className="text-lg font-bold capitalize">{source.source_type}</h4>
          <div className="flex items-center space-x-2 mt-1 text-sm text-gray-500">
            {getStatusChip(source.sync_status)}
            {source.last_sync_at && (
              <span>Last sync: {formatDistanceToNow(new Date(source.last_sync_at), { addSuffix: true })}</span>
            )}
          </div>
        </div>
        <button
          onClick={() => onSync(source.source_type)}
          disabled={isSyncing}
          className="flex items-center space-x-2 px-4 py-2 text-sm font-medium text-white bg-blue-600 rounded-lg hover:bg-blue-700 disabled:opacity-50"
        >
          <ArrowPathIcon className={classNames("h-5 w-5", isSyncing && "animate-spin")} />
          <span>{isSyncing ? 'Syncing...' : 'Sync Now'}</span>
        </button>
      </div>

      <div className="mt-6 space-y-4">
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Enable for Semantic Search</span>
          <Switch
            checked={source.is_enabled_semantic_search}
            onChange={(checked) => handleFieldChange('is_enabled_semantic_search', checked)}
            className={classNames(
              source.is_enabled_semantic_search ? 'bg-blue-600' : 'bg-gray-200',
              'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
            )}
          >
            <span
              className={classNames(
                source.is_enabled_semantic_search ? 'translate-x-5' : 'translate-x-0',
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
              )}
            />
          </Switch>
        </div>
        
        <div className="flex items-center justify-between">
          <span className="text-sm font-medium text-gray-700">Auto-sync on startup</span>
          <Switch
            checked={source.auto_sync_on_startup}
            onChange={(checked) => handleFieldChange('auto_sync_on_startup', checked)}
            className={classNames(
                source.auto_sync_on_startup ? 'bg-blue-600' : 'bg-gray-200',
                'relative inline-flex h-6 w-11 flex-shrink-0 cursor-pointer rounded-full border-2 border-transparent transition-colors duration-200 ease-in-out focus:outline-none focus:ring-2 focus:ring-blue-500 focus:ring-offset-2'
              )}
          >
             <span
              className={classNames(
                source.auto_sync_on_startup ? 'translate-x-5' : 'translate-x-0',
                'pointer-events-none inline-block h-5 w-5 transform rounded-full bg-white shadow ring-0 transition duration-200 ease-in-out'
              )}
            />
          </Switch>
        </div>

        <div>
          <label htmlFor={`cron-${source.source_type}`} className="block text-sm font-medium text-gray-700">
            Sync Schedule (Cron)
          </label>
          <input
            type="text"
            id={`cron-${source.source_type}`}
            value={source.sync_schedule || ''}
            onChange={(e) => handleFieldChange('sync_schedule', e.target.value)}
            placeholder="e.g., 0 2 * * *"
            className="mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm"
          />
        </div>
      </div>
    </div>
  );
} 