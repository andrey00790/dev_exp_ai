import React, { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { toast } from 'react-hot-toast';
import { fetchSettings, updateSettings } from '../../api/settingsApi';
import { runSync } from '../../api/syncApi';
import DataSourceCard from './DataSourceCard';
import { DataSource } from '../../types';

export default function DataSourcesSettings() {
  const queryClient = useQueryClient();

  const { data: settings, isLoading, isError } = useQuery({
    queryKey: ['settings'],
    queryFn: fetchSettings,
  });

  const updateMutation = useMutation({
    mutationFn: updateSettings,
    onSuccess: () => {
      toast.success('Settings updated successfully!');
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to update settings: ${error.message}`);
    },
  });

  const syncMutation = useMutation({
    mutationFn: runSync,
    onSuccess: (data, variables) => {
      toast.success(`Sync started for ${variables.source_type}!`);
      // Optionally, trigger a refetch or update status locally
      queryClient.invalidateQueries({ queryKey: ['settings'] });
    },
    onError: (error: Error) => {
      toast.error(`Failed to start sync: ${error.message}`);
    },
  });

  const handleUpdateDataSource = (source: DataSource) => {
    if (!settings) return;
    const updatedSources = settings.data_sources.map(ds =>
      ds.source_type === source.source_type ? source : ds
    );
    updateMutation.mutate({ ...settings, data_sources: updatedSources });
  };

  const handleRunSync = (source_type: string) => {
    syncMutation.mutate({ source_type, source_name: 'default' });
  };

  if (isLoading) {
    return <div>Loading data sources...</div>;
  }

  if (isError) {
    return <div className="text-red-500">Error loading data sources.</div>;
  }

  return (
    <div className="space-y-6">
      <div>
        <h3 className="text-lg font-medium text-gray-900">
          Manage Data Sources
        </h3>
        <p className="mt-1 text-sm text-gray-600">
          Enable, disable, and configure synchronization for your data sources.
        </p>
      </div>
      <div className="space-y-4">
        {settings?.data_sources.map(source => (
          <DataSourceCard
            key={source.source_type}
            source={source}
            onUpdate={handleUpdateDataSource}
            onSync={handleRunSync}
            isSyncing={syncMutation.isLoading && syncMutation.variables?.source_type === source.source_type}
          />
        ))}
      </div>
    </div>
  );
} 