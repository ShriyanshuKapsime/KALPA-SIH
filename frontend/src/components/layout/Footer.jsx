import React from 'react';
import { Sparkles, Award } from 'lucide-react';

export const Footer = () => {
  return (
    <footer className="border-t border-[#EAE3D5] bg-white/60 backdrop-blur-md mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col md:flex-row items-center justify-between gap-6">
          <div>
            <div className="flex items-center gap-2 mb-2">
              <div className="w-7 h-7 rounded-lg bg-[#EA580C] flex items-center justify-center shadow-sm">
                <Sparkles className="w-3.5 h-3.5 text-white" />
              </div>
              <span className="text-lg font-bold tracking-tight text-[#1C1917] font-['Outfit']">KALPA</span>
              <span className="text-xs text-[#78716C]">• Smart India Hackathon 2026</span>
            </div>
            <p className="text-xs text-[#78716C] max-w-md">
              AI-Powered Hyper-Local Livelihood & Business Advisory for Rural Bharat.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-6 text-xs text-[#78716C]">
            <span className="font-medium text-[#1C1917]">Phase 1: Multilingual Intake Engine</span>
            <span>•</span>
            <span>Sarvam Saaras STT</span>
            <span>•</span>
            <span>Indic NLP Pipeline</span>
          </div>
        </div>

        <div className="border-t border-[#EAE3D5]/80 mt-6 pt-6 flex flex-col sm:flex-row items-center justify-between gap-4 text-xs text-[#A8A29E]">
          <p>© 2026 KALPA Platform. Rural Entrepreneurship & Micro-Enterprise Advisory.</p>
          <p>Deterministic NLP Pipeline Architecture</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
