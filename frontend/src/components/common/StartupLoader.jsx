import React, { useState, useEffect, useRef } from 'react';
import startupVideoAsset from '../../assets/Man_scratching_hair_animation_1080p_20260929040613.mp4';

/**
 * KALPA multilingual translations across exactly 9 Indian languages.
 * Sequence:
 * 1. English: KALPA
 * 2. Hindi: कल्प
 * 3. Marathi: कल्प
 * 4. Bengali: কল্প
 * 5. Gujarati: કલ્પ
 * 6. Punjabi: ਕਲਪ
 * 7. Tamil: கல்ப
 * 8. Telugu: కల్ప
 * 9. Kannada: ಕಲ್ಪ
 */
export const KALPA_WORDS = [
  'KALPA',      // 1. English
  'कल्प',       // 2. Hindi
  'கல்ப',       // 7. Tamil
  'कल्प',       // 3. Marathi
  'ಕಲ್ಪ',       // 9. Kannada
  'কল্প',       // 4. Bengali
  'કલ્પ',       // 5. Gujarati
  'കൽപ',       // Malayalam
  'ਕਲਪ',       // 6. Punjabi
  'కల్ప',       // 8. Telugu
];

export const LOADER_STATE = {
  LOADING: 'LOADING',
  READY_TO_EXIT: 'READY_TO_EXIT',
  EXITING: 'EXITING',
  EXITED: 'EXITED',
};

const MINIMUM_DISPLAY_MS = 3000;
const EXIT_ANIMATION_MS = 700; // 700ms smooth cinematic zoom & fade
// Exact median sampled background color from the MP4 video asset (RGB 246, 229, 205)
const VIDEO_BG_COLOR = '#F6E5CD';

export const StartupLoader = () => {
  const [loaderState, setLoaderState] = useState(LOADER_STATE.LOADING);
  const [wordIndex, setWordIndex] = useState(0);
  const [videoLoaded, setVideoLoaded] = useState(false);
  const [videoFailed, setVideoFailed] = useState(false);

  const loaderStateRef = useRef(LOADER_STATE.LOADING);
  const animTimerRef = useRef(null);
  const videoRef = useRef(null);

  // Keep ref synchronized with state for synchronous lifecycle guards
  useEffect(() => {
    loaderStateRef.current = loaderState;
  }, [loaderState]);

  // ---------------------------------------------------------------------------
  // 9-Language Multilingual Animation Loop:
  // Cycles strictly through all 9 languages in deterministic order at constant speed.
  // 1000ms pause on English (initial brand word), then steady 220ms per language.
  // Immediately cancelled & frozen when transitioning out of LOADING.
  // ---------------------------------------------------------------------------
  useEffect(() => {
    let isCancelled = false;
    let timerId = null;

    const stepWord = () => {
      if (isCancelled || loaderStateRef.current !== LOADER_STATE.LOADING) return;

      setWordIndex((prevIndex) => {
        const nextIndex = (prevIndex + 1) % KALPA_WORDS.length;
        // Hold 1000ms when looping back to English (index 0), steady 220ms for subsequent languages
        const nextDelay = nextIndex === 0 ? 1000 : 220;
        timerId = setTimeout(stepWord, nextDelay);
        animTimerRef.current = timerId;
        return nextIndex;
      });
    };

    // Initial hold on English before stepping through the other 8 languages
    timerId = setTimeout(stepWord, 1000);
    animTimerRef.current = timerId;

    return () => {
      isCancelled = true;
      if (timerId) clearTimeout(timerId);
      if (animTimerRef.current) clearTimeout(animTimerRef.current);
    };
  }, []);

  // ---------------------------------------------------------------------------
  // Application Readiness & Minimum 3-Second Display Gate
  // ---------------------------------------------------------------------------
  useEffect(() => {
    const loaderStartedAt = performance.now();
    let isCancelled = false;
    let gateTimer = null;
    let exitTimer = null;
    let unmountTimer = null;

    const initializeApp = async () => {
      try {
        // 1. Wait for document ready
        if (typeof document !== 'undefined' && document.readyState !== 'complete') {
          await new Promise((resolve) => {
            const onReady = () => {
              window.removeEventListener('load', onReady);
              resolve();
            };
            window.addEventListener('load', onReady);
            setTimeout(resolve, 800);
          });
        }

        // 2. Wait for fonts if available
        if (typeof document !== 'undefined' && document.fonts && document.fonts.ready) {
          try {
            await document.fonts.ready;
          } catch (e) {
            // Non-critical font error ignored
          }
        }
      } catch (e) {
        console.warn('[STARTUP_LOADER] Initialization notice:', e);
      }

      if (isCancelled) return;

      // 3. Ensure minimum 3000ms display duration
      const elapsed = performance.now() - loaderStartedAt;
      const remainingTime = Math.max(0, MINIMUM_DISPLAY_MS - elapsed);

      gateTimer = setTimeout(() => {
        if (isCancelled || loaderStateRef.current !== LOADER_STATE.LOADING) return;

        // Step 1: READY_TO_EXIT — Stop KALPA language animation immediately
        loaderStateRef.current = LOADER_STATE.READY_TO_EXIT;
        if (animTimerRef.current) {
          clearTimeout(animTimerRef.current);
          animTimerRef.current = null;
        }
        setLoaderState(LOADER_STATE.READY_TO_EXIT);

        // Step 2: EXITING — Trigger smooth zoom + fade transition
        exitTimer = setTimeout(() => {
          if (isCancelled) return;
          loaderStateRef.current = LOADER_STATE.EXITING;
          setLoaderState(LOADER_STATE.EXITING);

          // Step 3: EXITED — Unmount after exit animation completes
          unmountTimer = setTimeout(() => {
            if (isCancelled) return;
            loaderStateRef.current = LOADER_STATE.EXITED;
            setLoaderState(LOADER_STATE.EXITED);
          }, EXIT_ANIMATION_MS);
        }, 20);
      }, remainingTime);
    };

    initializeApp();

    return () => {
      isCancelled = true;
      if (gateTimer) clearTimeout(gateTimer);
      if (exitTimer) clearTimeout(exitTimer);
      if (unmountTimer) clearTimeout(unmountTimer);
      if (animTimerRef.current) clearTimeout(animTimerRef.current);
    };
  }, []);

  const handleVideoLoaded = () => {
    setVideoLoaded(true);
    if (videoRef.current) {
      videoRef.current.play().catch(() => { });
    }
  };

  const handleVideoError = () => {
    setVideoFailed(true);
  };

  if (loaderState === LOADER_STATE.EXITED) return null;

  const currentWord = KALPA_WORDS[wordIndex];
  const isExiting = loaderState === LOADER_STATE.EXITING;

  return (
    <aside
      aria-label="Loading KALPA"
      aria-busy={loaderState === LOADER_STATE.LOADING}
      role="status"
      className="fixed inset-0 z-[99999] flex flex-col items-center justify-center select-none overflow-hidden"
      style={{
        backgroundColor: VIDEO_BG_COLOR,
        transform: isExiting ? 'scale(1.05)' : 'scale(1)',
        opacity: isExiting ? 0 : 1,
        transition: `transform ${EXIT_ANIMATION_MS}ms cubic-bezier(0.16, 1, 0.3, 1), opacity ${EXIT_ANIMATION_MS}ms cubic-bezier(0.4, 0, 0.2, 1)`,
        pointerEvents: loaderState === LOADER_STATE.LOADING ? 'auto' : 'none',
        willChange: 'transform, opacity',
        border: 'none',
        outline: 'none',
      }}
    >
      {/* Centered Composition: Video + KALPA Text */}
      <div className="relative z-10 flex flex-col items-center justify-center text-center px-4 w-full">
        {/* Video Wrapper: Full aspect-ratio reserved so KALPA is static, object-contain so full body is visible */}
        <div
          className="flex items-center justify-center overflow-hidden"
          style={{
            width: 'clamp(240px, 30vw, 320px)',
            maxWidth: 'min(82vw, 320px)',
            aspectRatio: '1080 / 1920',
            maxHeight: 'min(58vh, 480px)',
            border: 'none',
            outline: 'none',
            boxShadow: 'none',
            background: 'transparent',
          }}
        >
          {!videoFailed && (
            <video
              ref={videoRef}
              src={startupVideoAsset}
              autoPlay
              muted
              loop
              playsInline
              controls={false}
              preload="auto"
              onLoadedData={handleVideoLoaded}
              onError={handleVideoError}
              className={`w-full h-full object-contain transition-opacity duration-300 ${videoLoaded ? 'opacity-100' : 'opacity-0'
                }`}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                outline: 'none',
                boxShadow: 'none',
                display: 'block',
              }}
            />
          )}

          {/* Graceful Fallback if video fails to load */}
          {videoFailed && (
            <div className="w-20 h-20 rounded-full bg-[#E8D6B7]/60 flex items-center justify-center mb-2">
              <span className="text-2xl text-[#79563F] font-serif font-bold">K</span>
            </div>
          )}
        </div>

        {/* Animated Multilingual KALPA Wordmark - Spaced 24px directly below Video */}
        <div
          className="mt-6 flex items-center justify-center min-h-[3.5rem]"
          style={{
            border: 'none',
            outline: 'none',
            boxShadow: 'none',
          }}
        >
          <h1
            className="font-extrabold tracking-wider uppercase text-[#28231F] m-0 p-0 select-none"
            style={{
              fontFamily: "'Manrope', 'Outfit', 'Inter', system-ui, sans-serif",
              fontSize: 'clamp(1.85rem, 3vw, 2.5rem)',
              letterSpacing: '0.1em',
              lineHeight: 1.1,
              border: 'none',
              outline: 'none',
            }}
          >
            {currentWord}
          </h1>
        </div>
      </div>
    </aside>
  );
};

export default StartupLoader;
