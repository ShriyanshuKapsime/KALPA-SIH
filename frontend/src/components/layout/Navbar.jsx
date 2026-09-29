import React from 'react';
import { Link } from 'react-router-dom';
import LanguageSelector from '../ui/LanguageSelector';

/**
 * Minimal Header
 * Wordmark directly over the warm beige botanical background.
 * Language Selector on the top-right for universal whole-website translation.
 * Clicking KALPA navigates to home/landing page.
 */
export const Navbar = () => {
  return (
    <header className="w-full pt-5 sm:pt-6 pb-2 px-4 sm:px-8 transition-all">
      <div className="max-w-7xl mx-auto flex items-center justify-between gap-4">
        {/* Brand Left - Editorial serif typography matching landing page branding */}
        <Link
          to="/"
          className="text-2xl sm:text-3xl font-bold tracking-tight text-[#006B59] font-['Playfair_Display',Georgia,serif] hover:opacity-85 transition-opacity shrink-0"
          aria-label="KALPA - Return to Home"
        >
          KALPA
        </Link>

        {/* Top-Right Universal Language Option */}
        <div className="flex items-center gap-3">
          <LanguageSelector />
        </div>
      </div>
    </header>
  );
};

export default Navbar;
