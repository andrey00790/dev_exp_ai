import axios from 'axios';

// Context7 pattern: named export for explicit imports
const apiClient = axios.create({
  baseURL: '/api/v1',
  headers: {
    'Content-Type': 'application/json',
  },
});

// Add interceptors for token handling and error processing
apiClient.interceptors.response.use(
  (response) => response,
  (error) => {
    // Global error handling
    console.error('API Error:', error.response?.data || error.message);
    return Promise.reject(error);
  }
);

// Named export for Context7 best practices
export { apiClient };

// Default export for backward compatibility  
export default apiClient; 