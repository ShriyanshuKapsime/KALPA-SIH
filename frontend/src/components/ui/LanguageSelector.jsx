import React, { useState, useRef, useEffect } from 'react';
import { Languages, ChevronDown, Check } from 'lucide-react';
import { useLanguage } from '../../context/LanguageContext';

export const LanguageSelector = ({ className = '', compact = false }) => {
  const { language, setLanguage, availableLanguages, currentLanguageInfo } = useLanguage();
  const [isOpen, setIsOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Close dropdown on outside click
  useEffect(() => {
    const handleOutsideClick = (e) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    };
    const handleKeyDown = (e) => {
      if (e.key === 'Escape') setIsOpen(false);
    };

    if (isOpen) {
      document.addEventListener('mousedown', handleOutsideClick);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleOutsideClick);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleSelect = (code) => {
    setLanguage(code);
    setIsOpen(false);
  };

  return (
    <div className={`relative inline-block text-left ${className}`} ref={dropdownRef}>
      {/* Dropdown Trigger Button */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label={`Language selector: currently ${currentLanguageInfo.native}`}
        className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-[#FAF7F2] hover:bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 shadow-2xs text-xs font-bold transition-all cursor-pointer hover:border-[#79563F]/40 focus:outline-none focus:ring-2 focus:ring-[#79563F]/20"
      >
        <Languages className="w-3.5 h-3.5 text-[#79563F]" />
        <span className="font-semibold">{currentLanguageInfo.native}</span>
        {!compact && (
          <span className="text-[11px] text-[#79563F]/70 font-normal hidden sm:inline">
            ({currentLanguageInfo.label})
          </span>
        )}
        <ChevronDown
          className={`w-3.5 h-3.5 text-[#79563F]/70 transition-transform duration-200 ${
            isOpen ? 'rotate-180' : ''
          }`}
        />
      </button>

      {/* Dropdown Menu Modal / Popover */}
      {isOpen && (
        <div
          role="menu"
          aria-orientation="vertical"
          className="absolute right-0 mt-1.5 w-48 rounded-2xl bg-[#FAF7F2] border border-[#79563F]/25 shadow-lg py-1.5 z-50 animate-fadeIn focus:outline-none overflow-hidden"
        >
          <div className="px-3 py-1 border-b border-[#79563F]/15 mb-1">
            <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]/70">
              Select Language / भाषा
            </span>
          </div>

          <div className="max-h-64 overflow-y-auto divide-y divide-[#79563F]/10">
            {availableLanguages.map((lang) => {
              const isSelected = language === lang.code;
              return (
                <button
                  key={lang.code}
                  type="button"
                  role="menuitem"
                  onClick={() => handleSelect(lang.code)}
                  className={`w-full flex items-center justify-between px-3.5 py-2 text-left text-xs transition-colors cursor-pointer ${
                    isSelected
                      ? 'bg-[#EAF5EE] text-[#1B4D3E] font-bold'
                      : 'text-[#1C1917] hover:bg-[#FAF2E3]'
                  }`}
                >
                  <div className="flex flex-col">
                    <span className="font-bold text-xs">{lang.native}</span>
                    <span className="text-[10px] text-[#79563F]/70">{lang.label}</span>
                  </div>
                  {isSelected && <Check className="w-4 h-4 text-[#1B4D3E]" />}
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default LanguageSelector;
