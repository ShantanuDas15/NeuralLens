import { useEffect, useState } from 'react';
import { fetchImageBlob } from '../api';

/**
 * Load a protected backend image and return an object URL usable as <img src>.
 * Returns null until loaded (or if loading fails). The object URL is revoked
 * automatically when the url changes or the component unmounts.
 */
const useAuthedImage = (url) => {
  const [src, setSrc] = useState(null);

  useEffect(() => {
    if (!url) return undefined;

    let cancelled = false;
    let objectUrl = null;

    fetchImageBlob(url)
      .then((blob) => {
        if (cancelled) return;
        objectUrl = URL.createObjectURL(blob);
        setSrc(objectUrl);
      })
      .catch((err) => {
        if (import.meta.env.DEV) console.error('Image load failed:', err);
      });

    return () => {
      cancelled = true;
      if (objectUrl) URL.revokeObjectURL(objectUrl);
    };
  }, [url]);

  return src;
};

export default useAuthedImage;
