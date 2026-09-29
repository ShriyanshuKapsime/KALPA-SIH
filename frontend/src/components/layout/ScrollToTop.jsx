import { useEffect } from 'react';
import { useLocation } from 'react-router-dom';

/**
 * ScrollToTop Component
 * Ensures every navigation, route change, and search parameter change across
 * the entire KALPA website immediately and reliably resets scroll position to (0, 0).
 * Prevents browser history scroll restoration from overriding the top position.
 */
export const ScrollToTop = () => {
  const { pathname, search, key } = useLocation();

  useEffect(() => {
    // Disable browser automatic scroll restoration so user always lands at the top of the next page
    if ('scrollRestoration' in window.history) {
      window.history.scrollRestoration = 'manual';
    }

    const resetScroll = () => {
      // 1. Immediately reset window & document element scroll
      window.scrollTo({
        top: 0,
        left: 0,
        behavior: 'instant',
      });

      if (document.documentElement) {
        document.documentElement.scrollTop = 0;
        document.documentElement.scrollLeft = 0;
      }

      if (document.body) {
        document.body.scrollTop = 0;
        document.body.scrollLeft = 0;
      }

      // 2. Reset any internal scroll containers
      const scrollContainers = document.querySelectorAll(
        '.kalpa-app-shell, .kalpa-content, main, [data-scroll-container], .overflow-y-auto, .overflow-y-scroll, .overflow-auto'
      );

      scrollContainers.forEach((container) => {
        if (container && container.scrollTop > 0) {
          container.scrollTop = 0;
        }
      });
    };

    // Immediate synchronous reset
    resetScroll();

    // Frame-level reset after React reconciliation & layout mount
    const rafId = requestAnimationFrame(resetScroll);

    // Multi-phase timeouts to handle dynamic component hydration
    const timerId1 = setTimeout(resetScroll, 20);
    const timerId2 = setTimeout(resetScroll, 80);

    return () => {
      cancelAnimationFrame(rafId);
      clearTimeout(timerId1);
      clearTimeout(timerId2);
    };
  }, [pathname, search, key]);

  return null;
};

export default ScrollToTop;
