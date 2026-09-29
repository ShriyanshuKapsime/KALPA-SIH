import React from 'react';

export const Badge = ({ children, variant = 'default', className = '' }) => {
  const variants = {
    default: 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25 font-semibold',
    brown: 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25 font-semibold',
    orange: 'bg-[#FAF2E3] text-[#C96A3A] border-[#C96A3A]/30 font-semibold',
    saffron: 'bg-[#FAF2E3] text-[#C96A3A] border-[#C96A3A]/30 font-semibold',
    gold: 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25 font-semibold',
    charcoal: 'bg-[#4A3427] text-white border-[#4A3427]',
    emerald: 'bg-[#FAF2E3] text-[#006F5F] border-[#006F5F]/30 font-semibold',
    amber: 'bg-[#FAF2E3] text-[#92745A] border-[#92745A]/25 font-semibold',
    rose: 'bg-rose-50 text-rose-800 border-rose-200',
    locked: 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/20',
  };

  return (
    <span
      className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium border ${variants[variant] || variants.default} ${className}`}
    >
      {children}
    </span>
  );
};

export default Badge;
