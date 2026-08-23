import { useState, useCallback } from 'react';

const useApi = (apiFunc) => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const result = await apiFunc(...args);
      setData(result.data);
      return result.data;
    } catch (err) {
      console.error("API Error:", err);
      // Extract error message safely from Axios error response or default to err.message
      const message = err.response?.data?.detail || err.response?.data?.message || err.message || 'An unexpected error occurred';
      setError(message);
      throw new Error(message);
    } finally {
      setLoading(false);
    }
  }, [apiFunc]);

  return { data, loading, error, execute };
};

export default useApi;
