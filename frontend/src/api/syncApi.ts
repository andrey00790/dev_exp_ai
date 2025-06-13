import apiClient from './apiClient';

interface RunSyncPayload {
  source_type: string;
  source_name: string;
}

export const runSync = async (payload: RunSyncPayload): Promise<any> => {
  const response = await apiClient.post('/sync/run', payload);
  return response.data;
};

export const rescheduleSync = async (): Promise<any> => {
    const response = await apiClient.post('/sync/reschedule');
    return response.data;
} 