import axios from 'axios';
import { auth } from './firebase';

const api = axios.create({
  baseURL: `${import.meta.env.VITE_API_URL ?? ''}/api`,
});

// Interceptor to inject Firebase ID token into every request
api.interceptors.request.use(
  async (config) => {
    if (auth.currentUser) {
      const token = await auth.currentUser.getIdToken();
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Fetch a backend image (e.g. "/api/results/<id>.png") as a Blob.
 *
 * These endpoints require the Firebase Bearer token, which a plain <img src>
 * or fetch() cannot send, so images are loaded through the authenticated
 * client (which also honours VITE_API_URL).
 */
export const fetchImageBlob = async (url) => {
  const { data } = await api.get(url.replace(/^\/api/, ''), { responseType: 'blob' });
  return data;
};

export default api;
