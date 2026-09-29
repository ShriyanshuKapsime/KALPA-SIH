import React, { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

/**
 * Kalpa3DCard
 * Subtle 3D perspective mouse-follow tilt component for KALPA dashboard cards.
 * Designed with restrained ±4-5° tilt, smooth spring physics, and elevation on hover.
 */
export const Kalpa3DCard = ({ children, className = '', containerClassName = '' }) => {
  const cardRef = useRef(null);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth, subtle spring physics
  const springConfig = {
    damping: 20,
    stiffness: 180,
  };

  const springX = useSpring(mouseX, springConfig);
  const springY = useSpring(mouseY, springConfig);

  // Restrained maximum ±4.5 degrees rotation for clean financial dashboard cards
  const rotateX = useTransform(springY, [-0.5, 0.5], ['4.5deg', '-4.5deg']);
  const rotateY = useTransform(springX, [-0.5, 0.5], ['-4.5deg', '4.5deg']);

  const handleMouseMove = (e) => {
    if (!cardRef.current) return;
    const rect = cardRef.current.getBoundingClientRect();
    const width = rect.width;
    const height = rect.height;
    if (width === 0 || height === 0) return;

    const mousePosX = e.clientX - rect.left;
    const mousePosY = e.clientY - rect.top;

    mouseX.set(mousePosX / width - 0.5);
    mouseY.set(mousePosY / height - 0.5);
  };

  const handleMouseLeave = () => {
    mouseX.set(0);
    mouseY.set(0);
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      className={`[perspective:1000px] h-full w-full ${containerClassName}`}
    >
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: 'preserve-3d',
        }}
        whileHover={{
          y: -3,
          scale: 1.015,
        }}
        transition={{
          type: 'spring',
          stiffness: 320,
          damping: 24,
        }}
        className={`h-full w-full select-none ${className}`}
      >
        {children}
      </motion.div>
    </div>
  );
};

export default Kalpa3DCard;
