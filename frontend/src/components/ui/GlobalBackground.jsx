import React, { useEffect, useRef } from 'react';

export const GlobalBackground = () => {
  const frameRef = useRef();

  useEffect(() => {
    const updatePointer = (event) => {
      if (frameRef.current) return;

      frameRef.current = requestAnimationFrame(() => {
        document.documentElement.style.setProperty('--kalpa-pointer-x', `${event.clientX}px`);
        document.documentElement.style.setProperty('--kalpa-pointer-y', `${event.clientY}px`);
        frameRef.current = undefined;
      });
    };

    window.addEventListener('pointermove', updatePointer, { passive: true });
    return () => {
      window.removeEventListener('pointermove', updatePointer);
      if (frameRef.current) cancelAnimationFrame(frameRef.current);
    };
  }, []);

  return (
    <div className="kalpa-background" aria-hidden="true">
      <div className="kalpa-background-art" />
      <div className="kalpa-background-ink" />
      <div className="kalpa-background-shine" />
    </div>
  );
};

export default GlobalBackground;
