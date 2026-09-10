import React from 'react';

export const Button = ({
  children,
  variant = 'primary',
  size = 'md',
  className = '',
  disabled = false,
  onClick,
  type = 'button',
  icon: Icon,
  ...props
}) => {
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-xl focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'saffron-gradient-btn focus:ring-orange-500 font-semibold',
    secondary: 'bg-[#1C1917] hover:bg-[#292524] text-[#FAF8F5] shadow-md shadow-stone-900/10 focus:ring-stone-700',
    outline: 'border border-[#D6CDBC] hover:border-[#D97706] text-[#292524] hover:text-[#C2410C] bg-white/80 hover:bg-[#FAF6F0] focus:ring-orange-400 shadow-sm',
    ghost: 'text-[#57534E] hover:text-[#1C1917] hover:bg-[#EFE8DE]/60 focus:ring-stone-400',
    gold: 'bg-gradient-to-r from-[#D97706] to-[#B45309] text-white shadow-md shadow-amber-600/20 hover:brightness-105',
    danger: 'bg-rose-600 hover:bg-rose-700 text-white focus:ring-rose-500 shadow-sm',
  };

  const sizes = {
    sm: 'text-xs px-3 py-1.5 gap-1.5',
    md: 'text-sm px-4 py-2.5 gap-2',
    lg: 'text-base px-6 py-3 gap-2.5',
  };

  return (
    <button
      type={type}
      disabled={disabled}
      onClick={onClick}
      className={`${baseStyles} ${variants[variant] || variants.primary} ${sizes[size] || sizes.md} ${className}`}
      {...props}
    >
      {Icon && <Icon className={size === 'sm' ? 'w-3.5 h-3.5' : size === 'lg' ? 'w-5 h-5' : 'w-4 h-4'} />}
      {children}
    </button>
  );
};

export default Button;
