import React, { useRef, useState, useEffect } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';
import { ChevronDown, ChevronUp } from 'lucide-react';
import { formatEnumLabel, renderIntegrityBadge } from '../../pages/Feasibility/FeasibilityPage';

/**
 * FeasibilityScoreCard
 * Reusable 3D analytical score card with half-circle gauge visualization,
 * restrained mouse-follow perspective tilt, and expandable calculation trigger.
 * Built for KALPA Feasibility Synthesis 4-pillar evaluation.
 */
export const FeasibilityScoreCard = ({
  title,
  score,
  weight,
  contribution,
  status = 'ADEQUATE',
  sourceStage = 'CALCULATED',
  confidence = 1.0,
  isExpanded = false,
  onToggleExpand,
  className = '',
}) => {
  const cardRef = useRef(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);
  const [canHover, setCanHover] = useState(false);

  useEffect(() => {
    if (typeof window !== 'undefined') {
      setCanHover(window.matchMedia('(hover: hover)').matches);
    }
  }, []);

  // Smooth, restrained spring physics (±4.5° maximum tilt)
  const springConfig = { damping: 22, stiffness: 220 };
  const rawRotateX = useTransform(mouseY, [-0.5, 0.5], [4.5, -4.5]);
  const rawRotateY = useTransform(mouseX, [-0.5, 0.5], [-4.5, 4.5]);
  const rotateX = useSpring(rawRotateX, springConfig);
  const rotateY = useSpring(rawRotateY, springConfig);

  const handleMouseMove = (e) => {
    if (!canHover || !cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    if (rect.width === 0 || rect.height === 0) return;
    const x = e.clientX - rect.left;
    const y = e.clientY - rect.top;
    mouseX.set(x / rect.width - 0.5);
    mouseY.set(y / rect.height - 0.5);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  const numScore = typeof score === 'number' ? Math.round(score) : Number(score) || 0;
  const clampedScore = Math.max(0, Math.min(100, numScore));
  const normStatus = String(status || '').toUpperCase();

  // Semantic color mapping in strict KALPA palette (zero cyan/bright neon)
  let arcStrokeColor = '#79563F'; // Default warm neutral brown
  let statusBadgeClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25';

  if (normStatus === 'STRONG' || normStatus === 'PASS' || clampedScore >= 80) {
    arcStrokeColor = '#1B4D3E'; // Muted KALPA Green
    statusBadgeClass = 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/25';
  } else if (normStatus === 'CAUTION' || normStatus === 'DEVELOPING' || clampedScore < 55) {
    arcStrokeColor = '#A05A35'; // Muted Terracotta
    statusBadgeClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/30';
  }

  // Semicircle arc math: radius = 46, circumference = pi * 46 ≈ 144.513
  const arcLength = 144.513;
  const strokeDashoffset = arcLength * (1 - clampedScore / 100);

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`[perspective:1000px] h-full w-full ${className}`}
    >
      <motion.div
        style={{
          rotateX: canHover ? rotateX : 0,
          rotateY: canHover ? rotateY : 0,
          transformStyle: 'preserve-3d',
        }}
        whileHover={canHover ? { y: -3, scale: 1.012 } : {}}
        transition={{ type: 'spring', stiffness: 320, damping: 24 }}
        className={`royal-card bg-[#FAF7F2] rounded-2xl border transition-all h-full flex flex-col justify-between p-5 shadow-2xs hover:shadow-md select-none ${
          isExpanded ? 'border-[#79563F] ring-1 ring-[#79563F]/20' : 'border-[#79563F]/18'
        }`}
      >
        {/* Card Content Container with 3D Depth */}
        <div className="space-y-3" style={{ transform: 'translateZ(10px)' }}>
          {/* Top Row: Weight Badge & Status Badge */}
          <div className="flex items-center justify-between gap-2" style={{ transform: 'translateZ(14px)' }}>
            <span className="text-[10px] font-black tracking-wider text-[#79563F]/80 uppercase font-mono bg-[#FAF2E3] px-2 py-0.5 rounded border border-[#79563F]/15">
              {weight}% WEIGHT
            </span>
            <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${statusBadgeClass}`}>
              {formatEnumLabel(status)}
            </span>
          </div>

          {/* Pillar Title (Controlled 2-line max height for equal card heights) */}
          <div className="min-h-[2.5rem] flex items-center" style={{ transform: 'translateZ(12px)' }}>
            <h4 className="text-sm font-bold text-[#1C1917] font-['Outfit'] line-clamp-2 leading-tight">
              {title}
            </h4>
          </div>

          {/* Half-Circle / Arc Score Visualization */}
          <div className="flex flex-col items-center justify-center pt-1" style={{ transform: 'translateZ(20px)' }}>
            <div className="relative w-36 h-20 flex items-end justify-center">
              <svg
                viewBox="0 0 120 70"
                className="w-full h-full overflow-visible"
                aria-hidden="true"
              >
                {/* Background Track Arc */}
                <path
                  d="M 14 58 A 46 46 0 0 1 106 58"
                  fill="none"
                  stroke="#EFE5D3"
                  strokeWidth="8"
                  strokeLinecap="round"
                />
                {/* Active Semantic Score Arc */}
                <motion.path
                  d="M 14 58 A 46 46 0 0 1 106 58"
                  fill="none"
                  stroke={arcStrokeColor}
                  strokeWidth="8"
                  strokeLinecap="round"
                  strokeDasharray={arcLength}
                  initial={{ strokeDashoffset: arcLength }}
                  animate={{ strokeDashoffset }}
                  transition={{ duration: 0.9, ease: [0.16, 1, 0.3, 1] }}
                />
              </svg>

              {/* Centered Numeric Score */}
              <div className="absolute inset-0 flex flex-col items-center justify-end pb-0.5">
                <div className="flex items-baseline gap-0.5">
                  <span className="text-3xl font-extrabold text-[#1C1917] font-['Outfit'] tracking-tight">
                    {numScore}
                  </span>
                  <span className="text-xs text-stone-500 font-semibold font-mono">
                    /100
                  </span>
                </div>
              </div>
            </div>
          </div>

          {/* Contribution & Source Row */}
          <div className="pt-2 flex items-center justify-between border-t border-[#79563F]/10 text-xs" style={{ transform: 'translateZ(10px)' }}>
            <div>
              {renderIntegrityBadge(sourceStage)}
            </div>
            <div className="text-right">
              <span className="text-[10px] text-stone-500 font-medium block">Contribution</span>
              <span className="text-xs font-bold text-[#1B4D3E] font-mono">
                +{typeof contribution === 'number' ? contribution.toFixed(1) : contribution} pts
              </span>
            </div>
          </div>
        </div>

        {/* Footer: Expandable Trigger ("How calculated?") */}
        <div className="pt-3 mt-3 border-t border-[#79563F]/10" style={{ transform: 'translateZ(8px)' }}>
          <button
            type="button"
            onClick={onToggleExpand}
            className="w-full text-left text-[11px] font-bold text-[#79563F] hover:text-[#5C3F2D] flex items-center justify-between py-1 transition cursor-pointer"
          >
            <span>How calculated?</span>
            {isExpanded ? (
              <ChevronUp className="w-3.5 h-3.5 text-[#79563F]" />
            ) : (
              <ChevronDown className="w-3.5 h-3.5 text-[#79563F]" />
            )}
          </button>
        </div>
      </motion.div>
    </div>
  );
};

export default FeasibilityScoreCard;
