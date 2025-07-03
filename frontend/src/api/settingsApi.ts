import apiClient from './apiClient';
import { UserSettings } from '../types';

export const fetchSettings = async (): Promise<UserSettings> => {
  const response = await apiClient.get('/users/current/settings');
  return response.data;
};

export const updateSettings = async (settings: UserSettings): Promise<UserSettings> => {
  const response = await apiClient.put('/users/current/settings', settings);
  return response.data;
}; 