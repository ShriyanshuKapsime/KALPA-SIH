import React from 'react';

export const Stage6StatusBadge = ({ status, type = 'status', className = '' }) => {
  if (!status) return null;

  const normalized = String(status).toUpperCase();

  // Status mapping
  const styles = {
    // Data status
    ACTUAL: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    LIVE_RETRIEVED: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    OFFICIAL_STATIC_DATA: 'bg-blue-500/10 text-blue-400 border-blue-500/30',
    PROXY: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    ESTIMATED: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    PARTIAL: 'bg-amber-500/10 text-amber-300 border-amber-500/20',
    MISSING: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    UNAVAILABLE: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    UNKNOWN: 'bg-slate-800 text-slate-300 border-slate-700',
    UNKNOWN_DATA_GAP: 'bg-amber-500/15 text-amber-300 border-amber-500/40 font-semibold',

    // Readiness & Capacity
    AVAILABLE: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    LIMITED: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    SATURATED: 'bg-rose-500/10 text-rose-400 border-rose-500/30',
    EXPANSION_OPPORTUNITY: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 font-bold',
    HEALTHY_MARKET: 'bg-teal-500/15 text-teal-300 border-teal-500/40 font-bold',
    HIGH_SATURATION: 'bg-rose-500/15 text-rose-300 border-rose-500/40 font-bold',

    // Risk / Pressure
    LOW: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    MODERATE: 'bg-amber-500/10 text-amber-400 border-amber-500/30',
    HIGH: 'bg-orange-500/10 text-orange-400 border-orange-500/30',
    SEVERE: 'bg-rose-500/15 text-rose-300 border-rose-500/40 font-bold',
    CRITICAL: 'bg-rose-500/20 text-rose-200 border-rose-500/50 font-bold',
    WARNING: 'bg-amber-500/15 text-amber-300 border-amber-500/40',
    INFO: 'bg-blue-500/10 text-blue-300 border-blue-500/30',

    // Strength
    STRONG: 'bg-emerald-500/15 text-emerald-300 border-emerald-500/40 font-bold',
    EMERGING: 'bg-cyan-500/10 text-cyan-300 border-cyan-500/30',
    WEAK: 'bg-rose-500/10 text-rose-400 border-rose-500/30',

    // Precision / Catchment
    PRIMARY: 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30',
    SECONDARY: 'bg-cyan-500/10 text-cyan-400 border-cyan-500/30',
    EXTENDED: 'bg-indigo-500/10 text-indigo-400 border-indigo-500/30',
    OUTSIDE: 'bg-slate-800 text-slate-400 border-slate-700',
  };

  const style = styles[normalized] || 'bg-slate-800 text-slate-300 border-slate-700';

  const formatText = (txt) => {
    if (txt === 'UNKNOWN_DATA_GAP') return 'UNKNOWN (DATA GAP)';
    return txt.replace(/_/g, ' ');
  };

  return (
    <span
      className={`inline-flex items-center text-[10px] font-mono uppercase px-2 py-0.5 rounded border tracking-wider select-none ${style} ${className}`}
    >
      {formatText(normalized)}
    </span>
  );
};

export default Stage6StatusBadge;
