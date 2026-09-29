import React, { useRef, useState } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

/**
 * Kalpa3DCard
 * Rich 3D perspective mouse-follow tilt component for KALPA dashboard cards.
 * Designed with dynamic ±8.5° 3D tilt, specular glare lighting, and tangible 3D elevation.
 */
export const Kalpa3DCard = ({ children, className = '', containerClassName = '' }) => {
  const cardRef = useRef(null);
  const [isHovered, setIsHovered] = useState(false);
  const mouseX = useMotionValue(0);
  const mouseY = useMotionValue(0);

  // Smooth, snappy spring physics
  const springConfig = {
    damping: 18,
    stiffness: 220,
  };

  const springX = useSpring(mouseX, springConfig);
  const springY = useSpring(mouseY, springConfig);

  // 3D rotation angles up to ±8.5 degrees
  const rotateX = useTransform(springY, [-0.5, 0.5], ['8.5deg', '-8.5deg']);
  const rotateY = useTransform(springX, [-0.5, 0.5], ['-8.5deg', '8.5deg']);
  const glareX = useTransform(springX, [-0.5, 0.5], ['0%', '100%']);
  const glareY = useTransform(springY, [-0.5, 0.5], ['0%', '100%']);

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

  const handleMouseEnter = () => {
    setIsHovered(true);
  };

  const handleMouseLeave = () => {
    setIsHovered(false);
    mouseX.set(0);
    mouseY.set(0);
  };

  return (
    <div
      ref={cardRef}
      onMouseMove={handleMouseMove}
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      className={`[perspective:1200px] h-full w-full ${containerClassName}`}
    >
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: 'preserve-3d',
        }}
        whileHover={{
          y: -6,
          scale: 1.025,
        }}
        transition={{
          type: 'spring',
          stiffness: 340,
          damping: 22,
        }}
        className={`relative h-full w-full select-none transition-shadow duration-300 rounded-xl ${className}`}
      >
        {children}

        {/* 3D Dynamic Specular Light Glare on Hover */}
        {isHovered && (
          <motion.div
            className="absolute inset-0 pointer-events-none rounded-xl overflow-hidden mix-blend-overlay opacity-30"
            style={{
              background: `radial-gradient(circle at ${glareX} ${glareY}, rgba(255,255,255,0.8) 0%, transparent 60%)`,
            }}
          />
        )}
      </motion.div>
    </div>
  );
};

export default Kalpa3DCard;
