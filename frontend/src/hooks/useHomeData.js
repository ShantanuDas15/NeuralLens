import { useCallback, useEffect, useRef, useState } from 'react';
import api from '../api';

const RECENT_COUNT = 6;

const fetchHome = async () => {
  const [history, profile] = await Promise.all([
    api.get(`/history?page=1&page_size=${RECENT_COUNT}`),
    // Stats are a nice-to-have: never let them break the home screen.
    api.get('/profile').catch(() => null),
  ]);
  return {
    status: 'ready',
    total: history.data.total,
    items: history.data.items,
    stats: profile?.data?.stats ?? null,
  };
};

/**
 * Loads what the home screen needs to decide which layout to show:
 * the user's most recent completed jobs (and how many exist) plus usage stats.
 *
 * status: 'loading' | 'ready' | 'error'
 */
const useHomeData = () => {
  const [state, setState] = useState({ status: 'loading', total: 0, items: [], stats: null });
  const mounted = useRef(true);

  const load = useCallback(() => {
    return fetchHome()
      .then((next) => {
        if (mounted.current) setState(next);
      })
      .catch((err) => {
        if (import.meta.env.DEV) console.error('Home data failed:', err);
        if (mounted.current) setState((prev) => ({ ...prev, status: 'error' }));
      });
  }, []);

  useEffect(() => {
    mounted.current = true;
    load();
    return () => {
      mounted.current = false;
    };
  }, [load]);

  return { ...state, refresh: load };
};

export default useHomeData;
