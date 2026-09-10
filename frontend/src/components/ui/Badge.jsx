import React from 'react';

export const Badge = ({ children, variant = 'default', className = '' }) => {
  const variants = {
    default: 'bg-[#EFE8DE] text-[#44403C] border-[#D6CDBC]',
    saffron: 'bg-orange-50 text-[#C2410C] border-orange-200 font-semibold',
    gold: 'bg-amber-50 text-[#B45309] border-amber-200 font-semibold',
    charcoal: 'bg-[#292524] text-[#FAF8F5] border-[#1C1917]',
    emerald: 'bg-emerald-50 text-emerald-800 border-emerald-200',
    amber: 'bg-amber-50 text-amber-800 border-amber-200',
    rose: 'bg-rose-50 text-rose-800 border-rose-200',
    locked: 'bg-stone-100 text-stone-500 border-stone-200',
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
