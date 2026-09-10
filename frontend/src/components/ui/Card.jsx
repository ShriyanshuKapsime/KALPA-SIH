import React from 'react';

export const Card = ({ children, className = '', hover = false, onClick, ...props }) => {
  return (
    <div
      onClick={onClick}
      className={`royal-card rounded-2xl p-6 ${
        hover ? 'hover:-translate-y-0.5 cursor-pointer' : ''
      } ${className}`}
      {...props}
    >
      {children}
    </div>
  );
};

export const CardHeader = ({ children, className = '' }) => (
  <div className={`mb-4 ${className}`}>{children}</div>
);

export const CardTitle = ({ children, className = '' }) => (
  <h3 className={`text-lg font-bold text-[#1C1917] font-['Outfit'] ${className}`}>{children}</h3>
);

export const CardDescription = ({ children, className = '' }) => (
  <p className={`text-sm text-[#57534E] mt-1 leading-relaxed ${className}`}>{children}</p>
);

export const CardContent = ({ children, className = '' }) => (
  <div className={`${className}`}>{children}</div>
);

export default Card;
