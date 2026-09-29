import React, { useRef } from 'react';
import { motion, useMotionValue, useSpring, useTransform } from 'framer-motion';

export const Kalpa3DCard = ({ children, className = '' }) => {
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

  // Maximum ±5 degrees tilt as specified for subtle editorial feel
  const rotateX = useTransform(springY, [-0.5, 0.5], ['5deg', '-5deg']);
  const rotateY = useTransform(springX, [-0.5, 0.5], ['-5deg', '5deg']);

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
      className="[perspective:1000px] h-full w-full"
    >
      <motion.div
        style={{
          rotateX,
          rotateY,
          transformStyle: 'preserve-3d',
        }}
        whileHover={{
          y: -3,
          scale: 1.01,
        }}
        transition={{
          type: 'spring',
          stiffness: 300,
          damping: 25,
        }}
        className={`bg-[#FAF2E3] p-4 rounded-xl border border-[#79563F]/18 hover:border-[#79563F]/35 transition-colors flex flex-col justify-between shadow-2xs hover:shadow-md h-full select-none ${className}`}
      >
        {children}
      </motion.div>
    </div>
  );
};

export default Kalpa3DCard;
