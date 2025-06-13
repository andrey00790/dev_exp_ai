import axios from 'axios';

const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Можно добавить interceptors для обработки токенов или ошибок
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Глобальная обработка ошибок
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

export default apiClient; 