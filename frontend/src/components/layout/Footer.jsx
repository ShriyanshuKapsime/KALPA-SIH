import React from 'react';
import { useLanguage } from '../../context/LanguageContext';

export const Footer = () => {
  const { t } = useLanguage();

  return (
    <footer className="border-t border-[#79563F]/18 bg-[#F8F0E2] mt-20">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
        <div className="flex flex-col md:flex-row items-start md:items-center justify-between gap-6">
          <div>
            <div className="flex flex-wrap items-baseline gap-2.5 mb-2">
              <span className="text-2xl font-bold tracking-tight text-[#006F5F] font-['Playfair_Display',Georgia,serif]">
                KALPA
              </span>
              <span className="text-xs font-semibold text-[#79563F] tracking-wide">
                · Smart India Hackathon 2026
              </span>
            </div>
            <p className="text-xs sm:text-sm text-[#62584F] max-w-lg leading-relaxed">
              {t('footer_tagline', 'AI-Powered Hyper-Local Livelihood & Business Advisory for Rural Bharat.')}
            </p>
          </div>

          <div className="text-left md:text-right">
            <p className="text-xs sm:text-sm font-medium text-[#79563F] italic font-['Playfair_Display',Georgia,serif] max-w-sm">
              {t('footer_quote', '“Built for rural entrepreneurs, with local context at the centre.”')}
            </p>
          </div>
        </div>

        <div className="border-t border-[#79563F]/15 mt-8 pt-6 flex flex-col sm:flex-row items-center justify-between gap-3 text-xs text-[#92745A]">
          <p>{t('footer_copyright', '© 2026 KALPA Platform. Rural Entrepreneurship & Micro-Enterprise Advisory.')}</p>
        </div>
      </div>
    </footer>
  );
};

export default Footer;
