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
  const baseStyles = 'inline-flex items-center justify-center font-medium transition-all duration-200 rounded-lg focus:outline-none focus:ring-2 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed';
  
  const variants = {
    primary: 'saffron-gradient-btn focus:ring-[#C96A3A] font-semibold',
    secondary: 'bg-[#006F5F] hover:bg-[#075648] text-white shadow-md shadow-stone-900/10 focus:ring-[#006F5F]',
    outline: 'border border-[#79563F]/30 hover:border-[#79563F] text-[#28231F] hover:text-[#4A3427] bg-[#FAF2E3] hover:bg-[#F1E4CC] focus:ring-[#79563F] shadow-sm',
    ghost: 'text-[#62584F] hover:text-[#28231F] hover:bg-[#FAF2E3] focus:ring-[#79563F]',
    gold: 'bg-[#79563F] hover:bg-[#4A3427] text-white shadow-md shadow-stone-900/10',
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
