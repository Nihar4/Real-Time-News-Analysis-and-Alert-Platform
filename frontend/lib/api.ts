import axios from 'axios';
import Cookies from 'js-cookie';

const api = axios.create({
  baseURL: process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8001',
});

api.interceptors.request.use((config) => {
  const token = Cookies.get('token');
  console.log(Cookies);
  console.log('[API] Token from cookie:', token);
  if (token) {
    config.headers.Authorization = `Bearer ${token}`;
    console.log(`[API] Attaching token to ${config.url}: ${token.substring(0, 10)}...`);
  } else {
    console.warn(`[API] No token found for ${config.url}`);
  }
  return config;
});

api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response) {
      console.error(`[API] Error ${error.response.status} for ${error.config.url}`, error.response.data);
      if (error.response.status === 401) {
        console.warn('[API] 401 Unauthorized - Clearing token and redirecting');
        Cookies.remove('token');
        if (typeof window !== 'undefined' && !window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/signup')) {
          window.location.href = '/login';
        }
      }
    }
    return Promise.reject(error);
  }
);

export default api;
