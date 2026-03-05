import { useState, useEffect } from 'react';

/**
 * Returns true when the viewport is a landscape mobile screen (height < 500px).
 * Desktop monitors and tablets (height >= 500px) always return false,
 * guaranteeing zero impact on the existing desktop experience.
 */
export function useIsMobile(): boolean {
  const [isMobile, setIsMobile] = useState(() => window.innerHeight < 500);

  useEffect(() => {
    const handler = () => setIsMobile(window.innerHeight < 500);
    window.addEventListener('resize', handler);
    return () => window.removeEventListener('resize', handler);
  }, []);

  return isMobile;
}
