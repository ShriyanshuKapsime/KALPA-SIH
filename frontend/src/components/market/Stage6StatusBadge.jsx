import React from 'react';

export const Stage6StatusBadge = ({ status, type = 'status', className = '' }) => {
  if (!status) return null;

  const normalized = String(status).toUpperCase();

  // Status mapping matching KALPA palette
  const styles = {
    // Data status / Positive
    ACTUAL: 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/30',
    LIVE_RETRIEVED: 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/30',
    OFFICIAL_STATIC_DATA: 'bg-[#4A3427]/10 text-[#4A3427] border-[#4A3427]/30',
    PROXY: 'bg-[#C96A3A]/10 text-[#C96A3A] border-[#C96A3A]/30',
    ESTIMATED: 'bg-[#79563F]/10 text-[#79563F] border-[#79563F]/30',
    PARTIAL: 'bg-[#C96A3A]/10 text-[#C96A3A] border-[#C96A3A]/25',
    MISSING: 'bg-[#9E2A2B]/10 text-[#9E2A2B] border-[#9E2A2B]/30',
    UNAVAILABLE: 'bg-[#9E2A2B]/10 text-[#9E2A2B] border-[#9E2A2B]/30',
    UNKNOWN: 'bg-[#79563F]/10 text-[#62584F] border-[#79563F]/20',
    UNKNOWN_DATA_GAP: 'bg-[#C96A3A]/10 text-[#A9552F] border-[#C96A3A]/30 font-medium',

    // Readiness & Capacity
    AVAILABLE: 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/30 font-semibold',
    LIMITED: 'bg-[#C96A3A]/10 text-[#C96A3A] border-[#C96A3A]/30 font-semibold',
    SATURATED: 'bg-[#9E2A2B]/10 text-[#9E2A2B] border-[#9E2A2B]/30 font-semibold',
    EXPANSION_OPPORTUNITY: 'bg-[#006F5F]/15 text-[#006F5F] border-[#006F5F]/40 font-bold',
    HEALTHY_MARKET: 'bg-[#006F5F]/15 text-[#006F5F] border-[#006F5F]/40 font-bold',
    HIGH_SATURATION: 'bg-[#9E2A2B]/15 text-[#9E2A2B] border-[#9E2A2B]/40 font-bold',

    // Risk / Pressure
    LOW: 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/30 font-semibold',
    MODERATE: 'bg-[#C96A3A]/10 text-[#A9552F] border-[#C96A3A]/30 font-semibold',
    HIGH: 'bg-[#C96A3A]/15 text-[#C96A3A] border-[#C96A3A]/40 font-bold',
    SEVERE: 'bg-[#9E2A2B]/15 text-[#9E2A2B] border-[#9E2A2B]/40 font-bold',
    CRITICAL: 'bg-[#9E2A2B]/20 text-[#9E2A2B] border-[#9E2A2B]/50 font-bold',
    WARNING: 'bg-[#C96A3A]/15 text-[#A9552F] border-[#C96A3A]/40',
    INFO: 'bg-[#79563F]/10 text-[#4A3427] border-[#79563F]/30',

    // Strength
    STRONG: 'bg-[#006F5F]/15 text-[#006F5F] border-[#006F5F]/40 font-bold',
    EMERGING: 'bg-[#006F5F]/10 text-[#075648] border-[#006F5F]/30',
    WEAK: 'bg-[#9E2A2B]/10 text-[#9E2A2B] border-[#9E2A2B]/30',

    // Precision / Catchment
    PRIMARY: 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/30',
    SECONDARY: 'bg-[#79563F]/10 text-[#79563F] border-[#79563F]/30',
    EXTENDED: 'bg-[#79563F]/10 text-[#62584F] border-[#79563F]/25',
    OUTSIDE: 'bg-[#79563F]/10 text-[#62584F] border-[#79563F]/20',
  };

  const style = styles[normalized] || 'bg-[#79563F]/10 text-[#4A3427] border-[#79563F]/20';

  const formatText = (txt) => {
    if (txt === 'UNKNOWN_DATA_GAP') return 'DATA GAP';
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
