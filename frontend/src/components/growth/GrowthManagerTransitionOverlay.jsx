import React, { useState, useEffect } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { Check } from 'lucide-react';
import shopLineArt from '../../assets/kalpa-shop-entrepreneur.png';

const STATUS_MESSAGES = [
  'Understanding your business',
  'Preparing operating workspace',
  'Activating Growth Manager',
];

const MODES = [
  { id: 'plan', label: 'PLAN' },
  { id: 'analyze', label: 'ANALYZE' },
  { id: 'operate', label: 'OPERATE' },
  { id: 'grow', label: 'GROW' },
];

export const GrowthManagerTransitionOverlay = ({
  isOpen,
  businessName = 'Commercial Enterprise',
  onComplete,
}) => {
  const shouldReduceMotion = useReducedMotion();
  const [statusIndex, setStatusIndex] = useState(0);
  const [activeModeIndex, setActiveModeIndex] = useState(2); // 2 = OPERATE -> 3 = GROW

  useEffect(() => {
    if (!isOpen) {
      document.body.classList.remove('kalpa-growth-transitioning');
      setStatusIndex(0);
      setActiveModeIndex(2);
      return;
    }

    // Add global class to hide Ask KALPA and other floating elements during transition
    document.body.classList.add('kalpa-growth-transitioning');

    if (shouldReduceMotion) {
      const timer = setTimeout(() => {
        document.body.classList.remove('kalpa-growth-transitioning');
        if (onComplete) onComplete();
      }, 400);
      return () => {
        clearTimeout(timer);
        document.body.classList.remove('kalpa-growth-transitioning');
      };
    }

    // Phase 1: Mode progression to GROW + status to "Preparing operating workspace" at 600ms
    const modeTimer = setTimeout(() => {
      setActiveModeIndex(3);
      setStatusIndex(1);
    }, 600);

    // Phase 2: Status to "Activating Growth Manager" at 1300ms
    const statusTimer = setTimeout(() => {
      setStatusIndex(2);
    }, 1300);

    // Phase 3: Complete transition and enter Growth Manager at 1950ms
    const completeTimer = setTimeout(() => {
      document.body.classList.remove('kalpa-growth-transitioning');
      if (onComplete) onComplete();
    }, 1950);

    return () => {
      clearTimeout(modeTimer);
      clearTimeout(statusTimer);
      clearTimeout(completeTimer);
      document.body.classList.remove('kalpa-growth-transitioning');
    };
  }, [isOpen, shouldReduceMotion, onComplete]);

  if (!isOpen) return null;

  return (
    <AnimatePresence>
      <motion.div
        key="kalpa-growth-transition-overlay"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        transition={{ duration: 0.35, ease: 'easeOut' }}
        className="fixed inset-0 z-[99999] w-screen h-screen min-h-screen flex items-center justify-center p-4 sm:p-6 md:p-8 bg-[#FAF2E3]/60 backdrop-blur-lg overflow-hidden pointer-events-auto select-none"
        style={{
          backdropFilter: 'blur(10px)',
          WebkitBackdropFilter: 'blur(10px)',
        }}
      >
        {/* Perfectly Centered Transition Content */}
        <div className="w-full max-w-xl mx-auto flex flex-col items-center justify-center text-center space-y-4 sm:space-y-5 my-auto">
          {/* Subtitle & Title Reveal */}
          <motion.div
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ duration: 0.5, delay: 0.15, ease: 'easeOut' }}
            className="space-y-1"
          >
            <p className="text-[10px] sm:text-xs font-bold uppercase tracking-[0.25em] text-[#79563F]">
              Post-Launch Business Operating Portal
            </p>
            <h2 className="text-3xl sm:text-4xl md:text-5xl font-extrabold text-[#1B4D3E] font-['Playfair_Display',Georgia,serif] tracking-tight leading-tight">
              KALPA GROWTH MANAGER
            </h2>
            <p className="text-sm sm:text-base font-bold text-[#1C1917] font-['Outfit']">
              {businessName || 'Commercial Enterprise'}
            </p>
          </motion.div>

          {/* Shop + Rural Entrepreneur Warm Brown Line Illustration */}
          <motion.div
            className="relative w-full max-w-[320px] sm:max-w-[380px] px-2 py-1 flex items-center justify-center"
            initial={{ opacity: 0, scale: 0.96 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5, delay: 0.2, ease: 'easeOut' }}
          >
            {/* Smooth Progressive Drawing / Reveal Effect */}
            <motion.div
              initial={
                shouldReduceMotion
                  ? { opacity: 0 }
                  : { clipPath: 'inset(0 100% 0 0)', opacity: 0.15 }
              }
              animate={
                shouldReduceMotion
                  ? { opacity: 1 }
                  : { clipPath: 'inset(0 0% 0 0)', opacity: 1 }
              }
              transition={{
                duration: 1.1,
                delay: 0.2,
                ease: [0.22, 1, 0.36, 1],
              }}
              className="w-full flex items-center justify-center"
            >
              <img
                src={shopLineArt}
                alt="KALPA Business & Storefront Line Art"
                className="w-full h-auto object-contain pointer-events-none drop-shadow-xs"
                style={{
                  maxHeight: '260px',
                  mixBlendMode: 'multiply',
                  filter: 'contrast(1.1)',
                }}
              />
            </motion.div>
          </motion.div>

          {/* Horizontal Journey Sequence: PLAN -> ANALYZE -> OPERATE -> GROW */}
          <motion.div
            initial={{ opacity: 0, y: 8 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, delay: 0.4, ease: 'easeOut' }}
            className="flex items-center justify-center gap-2 sm:gap-3.5 py-1"
          >
            {MODES.map((mode, index) => {
              const isCurrent = index === activeModeIndex;
              const isPast = index < activeModeIndex;

              return (
                <div key={mode.id} className="flex items-center gap-2 sm:gap-3.5">
                  <div
                    className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-[10px] sm:text-[11px] font-extrabold tracking-wider transition-all duration-500 ${
                      isCurrent
                        ? 'bg-[#1B4D3E] text-white shadow-sm scale-105'
                        : isPast
                        ? 'bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/30'
                        : 'bg-[#FAF2E3]/60 text-[#79563F]/60 border border-[#79563F]/15'
                    }`}
                  >
                    {isPast && <Check className="w-3 h-3 text-[#1B4D3E]" />}
                    {isCurrent && (
                      <span className="w-1.5 h-1.5 rounded-full bg-[#FAF2E3] animate-pulse" />
                    )}
                    <span>{mode.label}</span>
                  </div>

                  {index < MODES.length - 1 && (
                    <span className="text-[#79563F]/40 text-xs font-bold">→</span>
                  )}
                </div>
              );
            })}
          </motion.div>

          {/* Business Mode Status Message (Sequential Smooth Cross-Fade with High Contrast) */}
          <div className="h-6 flex items-center justify-center">
            <AnimatePresence mode="wait">
              <motion.p
                key={statusIndex}
                initial={{ opacity: 0, y: 4 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: -4 }}
                transition={{ duration: 0.3, ease: 'easeInOut' }}
                className="text-xs sm:text-sm font-bold text-[#4A3427] tracking-wide"
              >
                {STATUS_MESSAGES[statusIndex]}
              </motion.p>
            </AnimatePresence>
          </div>

          {/* Loading Bar: Smooth Brown to Green Transition with Clear Track */}
          <div className="w-56 sm:w-72 h-2.5 bg-[#79563F]/20 border border-[#79563F]/35 rounded-full p-0.5 overflow-hidden shadow-inner mx-auto">
            <motion.div
              className="h-full bg-gradient-to-r from-[#79563F] via-[#C86D3B] to-[#1B4D3E] rounded-full shadow-xs"
              initial={{ width: '0%' }}
              animate={{ width: '100%' }}
              transition={{ duration: 1.85, ease: 'easeInOut' }}
            />
          </div>

          {/* Bottom subtle brand baseline */}
          <div className="text-[11px] font-semibold text-[#79563F]/80 tracking-wide text-center pt-1">
            KALPA Autonomous Enterprise Operations
          </div>
        </div>
      </motion.div>
    </AnimatePresence>
  );
};

export default GrowthManagerTransitionOverlay;
