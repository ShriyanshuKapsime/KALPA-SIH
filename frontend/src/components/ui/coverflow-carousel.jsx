import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';
import { cn } from '../../lib/utils';

export const CoverflowCarousel = ({
  items = [],
  rotate = 38,
  depth = 0.52,
  perspective = 3.5,
  falloff = 0.6,
  fade = 0.08,
  gap = 0.05,
  showNavigation = true,
  showCaption = false,
  autoplay = true,
  autoplayInterval = 4500,
  className = '',
  onActiveChange,
}) => {
  const containerRef = useRef(null);
  const [currentIndex, setCurrentIndex] = useState(0);
  const [containerWidth, setContainerWidth] = useState(1200);
  const [isHovered, setIsHovered] = useState(false);
  const [isInteracting, setIsInteracting] = useState(false);

  // Animation refs
  const currentPosRef = useRef(0);
  const targetPosRef = useRef(0);
  const isDraggingRef = useRef(false);
  const dragStartXRef = useRef(0);
  const dragStartPosRef = useRef(0);
  const lastDragTimeRef = useRef(0);
  const lastDragXRef = useRef(0);
  const velocityRef = useRef(0);
  const rafIdRef = useRef(null);
  const resumeTimerRef = useRef(null);
  const isPointerDownRef = useRef(false);

  const total = items.length;

  // Responsive card dimensions (clean, comfortable size)
  const cardWidth =
    containerWidth < 640
      ? Math.min(200, containerWidth * 0.55)
      : containerWidth < 1024
      ? 240
      : 280;

  const cardHeight = cardWidth * 1.55;

  // Update container width on resize
  useEffect(() => {
    const handleResize = () => {
      if (containerRef.current) {
        setContainerWidth(containerRef.current.offsetWidth || window.innerWidth);
      }
    };
    handleResize();
    window.addEventListener('resize', handleResize, { passive: true });
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  // Wrap index to [0, total - 1]
  const wrapIndex = useCallback(
    (idx) => {
      if (total === 0) return 0;
      return ((Math.round(idx) % total) + total) % total;
    },
    [total]
  );

  // Pause autoplay on user action, resume after delay
  const markInteraction = useCallback(() => {
    setIsInteracting(true);
    if (resumeTimerRef.current) clearTimeout(resumeTimerRef.current);
    resumeTimerRef.current = setTimeout(() => {
      setIsInteracting(false);
    }, 2800);
  }, []);

  // Programmatic navigation
  const goTo = useCallback(
    (idx) => {
      markInteraction();
      targetPosRef.current = idx;
    },
    [markInteraction]
  );

  const goToNext = useCallback(() => {
    markInteraction();
    targetPosRef.current = Math.round(targetPosRef.current) + 1;
  }, [markInteraction]);

  const goToPrev = useCallback(() => {
    markInteraction();
    targetPosRef.current = Math.round(targetPosRef.current) - 1;
  }, [markInteraction]);

  // Autoplay ticker
  useEffect(() => {
    if (!autoplay || isHovered || isInteracting || isDraggingRef.current || total <= 1) return;

    const timer = setInterval(() => {
      targetPosRef.current = Math.round(targetPosRef.current) + 1;
    }, autoplayInterval);

    return () => clearInterval(timer);
  }, [autoplay, autoplayInterval, isHovered, isInteracting, total]);

  // Main animation loop using requestAnimationFrame
  const [, setRerender] = useState(0);

  useEffect(() => {
    let lastActive = -1;

    const animate = () => {
      if (!isDraggingRef.current) {
        // Lerp towards target position with spring-like smoothness
        const diff = targetPosRef.current - currentPosRef.current;
        if (Math.abs(diff) > 0.0005) {
          currentPosRef.current += diff * 0.11;
          setRerender((r) => (r + 1) % 100000);
        } else {
          currentPosRef.current = targetPosRef.current;
        }
      }

      // Check active card index change
      const active = wrapIndex(currentPosRef.current);
      if (active !== lastActive) {
        lastActive = active;
        setCurrentIndex(active);
        if (onActiveChange) onActiveChange(active);
      }

      rafIdRef.current = requestAnimationFrame(animate);
    };

    rafIdRef.current = requestAnimationFrame(animate);
    return () => {
      if (rafIdRef.current) cancelAnimationFrame(rafIdRef.current);
    };
  }, [wrapIndex, onActiveChange]);

  // Pointer & Drag Handlers
  const handlePointerDown = (e) => {
    if (e.button !== 0 && e.pointerType === 'mouse') return;
    markInteraction();
    isPointerDownRef.current = true;
    isDraggingRef.current = true;
    dragStartXRef.current = e.clientX;
    dragStartPosRef.current = currentPosRef.current;
    lastDragTimeRef.current = Date.now();
    lastDragXRef.current = e.clientX;
    velocityRef.current = 0;
  };

  const handlePointerMove = (e) => {
    if (!isPointerDownRef.current) return;

    const deltaX = e.clientX - dragStartXRef.current;
    const dragSensitivity = cardWidth * 1.15;
    currentPosRef.current = dragStartPosRef.current - deltaX / dragSensitivity;

    // Track velocity for momentum flick
    const now = Date.now();
    const dt = now - lastDragTimeRef.current;
    if (dt > 10) {
      const dx = e.clientX - lastDragXRef.current;
      velocityRef.current = dx / dt;
      lastDragXRef.current = e.clientX;
      lastDragTimeRef.current = now;
    }

    setRerender((r) => (r + 1) % 100000);
  };

  const handlePointerUp = () => {
    if (!isPointerDownRef.current) return;
    isPointerDownRef.current = false;
    isDraggingRef.current = false;

    // Apply flick momentum
    const momentum = Math.max(-2, Math.min(2, -velocityRef.current * 1.8));
    targetPosRef.current = Math.round(currentPosRef.current + momentum);
    markInteraction();
  };

  // Keyboard navigation
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowLeft') {
      e.preventDefault();
      goToPrev();
    } else if (e.key === 'ArrowRight') {
      e.preventDefault();
      goToNext();
    }
  };

  // Touch handlers for mobile
  const handleTouchStart = (e) => {
    markInteraction();
    isPointerDownRef.current = true;
    isDraggingRef.current = true;
    const touch = e.touches[0];
    dragStartXRef.current = touch.clientX;
    dragStartPosRef.current = currentPosRef.current;
    lastDragTimeRef.now = Date.now();
    lastDragXRef.current = touch.clientX;
    velocityRef.current = 0;
  };

  const handleTouchMove = (e) => {
    if (!isPointerDownRef.current) return;
    const touch = e.touches[0];
    const deltaX = touch.clientX - dragStartXRef.current;
    const dragSensitivity = cardWidth * 1.1;
    currentPosRef.current = dragStartPosRef.current - deltaX / dragSensitivity;

    const now = Date.now();
    const dt = now - lastDragTimeRef.current;
    if (dt > 10) {
      const dx = touch.clientX - lastDragXRef.current;
      velocityRef.current = dx / dt;
      lastDragXRef.current = touch.clientX;
      lastDragTimeRef.current = now;
    }

    setRerender((r) => (r + 1) % 100000);
  };

  const handleTouchEnd = () => {
    handlePointerUp();
  };

  // Classic Coverflow 3D transformation
  const getCardTransformStyle = (index) => {
    if (total === 0) return {};

    const pos = currentPosRef.current;
    // Circular wrapped offset relative to current fractional position
    let offset = ((index - (pos % total) + total) % total);
    if (offset > total / 2) offset -= total;
    if (offset < -total / 2) offset += total;

    const absOffset = Math.abs(offset);
    const sign = Math.sign(offset);

    // Spacing between cards along the 3D plane
    const spacing = cardWidth * (0.68 + gap);
    const x = sign * (Math.pow(absOffset, 0.9) * spacing);

    // 3D Depth (Z) and Rotation (Y)
    const z = absOffset < 0.15 ? 40 : -Math.pow(absOffset, depth) * cardWidth * 0.9;
    const rotY =
      absOffset < 0.05
        ? 0
        : -sign * Math.min(rotate, rotate * Math.pow(Math.min(absOffset, 1.6), falloff));

    // Scale and Opacity falloff
    const scale = Math.max(0.58, 1 - absOffset * 0.12);
    const opacity = Math.max(0, 1 - Math.pow(absOffset * fade * 3.4, 1.15));
    const zIndex = Math.round(100 - absOffset * 15);

    const isCenter = absOffset < 0.5;

    return {
      transform: `translate3d(${x}px, 0px, ${z}px) rotateY(${rotY}deg) scale(${scale})`,
      opacity: opacity < 0.02 ? 0 : opacity,
      zIndex,
      visibility: opacity < 0.02 ? 'hidden' : 'visible',
      cursor: isCenter ? 'default' : 'pointer',
    };
  };

  const perspectivePx = Math.round(containerWidth * (perspective / 3.2));

  return (
    <div
      ref={containerRef}
      className={cn('kalpa-coverflow-container relative w-full select-none outline-none', className)}
      tabIndex={0}
      role="region"
      aria-label="KALPA Journey Coverflow Carousel"
      onKeyDown={handleKeyDown}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      onPointerDown={handlePointerDown}
      onPointerMove={handlePointerMove}
      onPointerUp={handlePointerUp}
      onPointerCancel={handlePointerUp}
      onTouchStart={handleTouchStart}
      onTouchMove={handleTouchMove}
      onTouchEnd={handleTouchEnd}
    >
      {/* 3D Viewport Stage — Pure Picture Only, Zero Shadows, Zero Borders */}
      <div
        className="kalpa-coverflow-stage relative w-full flex items-center justify-center overflow-hidden py-6"
        style={{
          perspective: `${perspectivePx}px`,
          perspectiveOrigin: 'center 50%',
          height: `${cardHeight + 40}px`,
        }}
      >
        <div
          className="kalpa-coverflow-plane relative w-full h-full flex items-center justify-center"
          style={{ transformStyle: 'preserve-3d' }}
        >
          {items.map((item, idx) => {
            const style = getCardTransformStyle(idx);
            const isCenter = idx === currentIndex;

            return (
              <div
                key={item.id || idx}
                className={cn(
                  'kalpa-coverflow-card absolute top-1/2 left-1/2 flex items-center justify-center bg-transparent border-0 outline-none shadow-none',
                  isCenter && 'kalpa-coverflow-card--active'
                )}
                style={{
                  width: `${cardWidth}px`,
                  height: `${cardHeight}px`,
                  marginTop: `-${cardHeight / 2}px`,
                  marginLeft: `-${cardWidth / 2}px`,
                  transformStyle: 'preserve-3d',
                  willChange: 'transform, opacity',
                  backfaceVisibility: 'hidden',
                  ...style,
                }}
                onClick={() => {
                  if (!isCenter) {
                    goTo(idx);
                  }
                }}
                role="button"
                tabIndex={isCenter ? -1 : 0}
                aria-label={item.alt || `Step ${idx + 1}`}
                aria-current={isCenter ? 'true' : 'false'}
              >
                {/* Pure Picture Only — Zero shadows, frames, borders, or backgrounds */}
                <img
                  src={item.src || item.image}
                  alt={item.alt || `KALPA Journey Step ${item.id || idx + 1}`}
                  className="w-full h-full object-contain pointer-events-none select-none"
                  loading="eager"
                  draggable={false}
                />
              </div>
            );
          })}
        </div>
      </div>

      {/* Caption Area (hidden when showCaption is false) */}
      {showCaption && items[currentIndex] && (
        <div className="kalpa-coverflow-caption text-center mt-3">
          <p className="text-sm font-semibold text-[#006B59]">{items[currentIndex].title}</p>
        </div>
      )}

      {/* Editorial Minimal Navigation Arrows */}
      {showNavigation && (
        <div className="kalpa-coverflow-controls flex items-center justify-center gap-6 mt-3 text-[#795548]">
          <button
            type="button"
            onClick={goToPrev}
            className="kalpa-coverflow-arrow p-2 text-[#006B59] hover:text-[#F15A24] transition-colors duration-200 cursor-pointer"
            aria-label="Previous step"
            title="Previous step"
          >
            <ArrowLeft className="w-5 h-5" aria-hidden="true" />
          </button>

          <span className="kalpa-coverflow-step-hint text-xs font-medium text-[#795548]/80 tracking-wide">
            {String(currentIndex + 1).padStart(2, '0')} / {String(total).padStart(2, '0')}
          </span>

          <button
            type="button"
            onClick={goToNext}
            className="kalpa-coverflow-arrow p-2 text-[#006B59] hover:text-[#F15A24] transition-colors duration-200 cursor-pointer"
            aria-label="Next step"
            title="Next step"
          >
            <ArrowRight className="w-5 h-5" aria-hidden="true" />
          </button>
        </div>
      )}
    </div>
  );
};

export default CoverflowCarousel;
