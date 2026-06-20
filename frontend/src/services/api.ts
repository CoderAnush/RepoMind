import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || 'https://repomind-api-z6x5.onrender.com/api/v1';

export const apiClient = axios.create({
  baseURL: API_BASE,
  headers: { 'Content-Type': 'application/json' },
  timeout: 90000, // Increased to 90s to accommodate Render free-tier cold-starts
});

// Attach token from localStorage on every request
apiClient.interceptors.request.use((config) => {
  const token = localStorage.getItem('repomind_token');
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
  }
  return config;
});

// Handle 401 responses — clear token and redirect to login
apiClient.interceptors.response.use(
  (res) => res,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('repomind_token');
      localStorage.removeItem('repomind_user');
      window.location.href = '/login';
    }
    return Promise.reject(error);
  }
);

export default apiClient;
