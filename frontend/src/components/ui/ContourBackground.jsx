import React from 'react';

export const ContourBackground = () => {
  return (
    <div className="fixed inset-0 pointer-events-none overflow-hidden z-0 select-none">
      {/* Soft warm ambient gradients */}
      <div className="absolute top-0 right-1/4 w-[600px] h-[500px] bg-orange-200/20 rounded-full blur-3xl" />
      <div className="absolute bottom-10 left-10 w-[500px] h-[500px] bg-amber-100/30 rounded-full blur-3xl" />
      
      {/* Subtle animated SVG topographic contour lines */}
      <svg
        className="absolute inset-0 w-full h-full opacity-35 animate-topo"
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 1440 900"
        fill="none"
        stroke="currentColor"
      >
        {/* Layer 1: Outer Terrain Outlines */}
        <path
          d="M-50,200 C300,120 450,280 800,220 C1150,160 1250,300 1500,240"
          stroke="#D4A373"
          strokeWidth="1.2"
          strokeDasharray="4 6"
          opacity="0.5"
        />
        <path
          d="M-100,320 C250,260 500,400 900,340 C1300,280 1350,450 1550,380"
          stroke="#C89666"
          strokeWidth="1.0"
          opacity="0.4"
        />
        <path
          d="M-50,480 C320,400 550,560 950,480 C1350,400 1400,600 1550,520"
          stroke="#B07D62"
          strokeWidth="1.2"
          strokeDasharray="8 6"
          opacity="0.4"
        />

        {/* Layer 2: Micro-Elevation Rings / Watershed Contours */}
        <path
          d="M150,680 C350,620 520,740 750,690 C980,640 1200,760 1450,710"
          stroke="#D4A373"
          strokeWidth="1.0"
          opacity="0.5"
        />
        <path
          d="M400,180 C500,100 650,120 720,200 C790,280 650,340 520,300 C390,260 300,260 400,180 Z"
          stroke="#E07A5F"
          strokeWidth="0.8"
          strokeDasharray="2 4"
          opacity="0.35"
        />
        <path
          d="M900,420 C1020,360 1150,390 1200,480 C1250,570 1120,640 980,600 C840,560 780,480 900,420 Z"
          stroke="#D4A373"
          strokeWidth="0.9"
          opacity="0.35"
        />
        <path
          d="M950,460 C1030,420 1100,440 1140,500 C1180,560 1090,600 1010,580 C930,560 870,500 950,460 Z"
          stroke="#C89666"
          strokeWidth="0.7"
          strokeDasharray="3 5"
          opacity="0.3"
        />

        {/* Subtle grid coordinates marker representing rural geographic mapping */}
        <circle cx="720" cy="200" r="3" fill="#D9531E" opacity="0.6" />
        <circle cx="1140" cy="500" r="3" fill="#D9531E" opacity="0.6" />
        <circle cx="350" cy="620" r="3" fill="#D9531E" opacity="0.6" />
      </svg>
    </div>
  );
};

export default ContourBackground;
