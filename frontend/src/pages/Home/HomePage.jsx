import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Mic } from 'lucide-react';
import apiService from '../../services/api';
import KalpaJourneyCarousel from '../../components/journey/KalpaJourneyCarousel';
import KalpaArchitecturalBenefits from '../../components/benefits/KalpaArchitecturalBenefits';
import LanguageSelector from '../../components/ui/LanguageSelector';
import { useLanguage } from '../../context/LanguageContext';

export const HomePage = () => {
  const { t, setLanguage, language } = useLanguage();
  const [gatewayHealth, setGatewayHealth] = useState({ status: 'checking' });
  const [aiHealth, setAiHealth] = useState({ status: 'checking' });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const gateway = await apiService.checkGatewayHealth();
        setGatewayHealth(gateway);
      } catch (error) {
        setGatewayHealth({ status: 'offline' });
      }

      try {
        const ai = await apiService.checkAIHealth();
        setAiHealth(ai);
      } catch (error) {
        setAiHealth({ status: 'offline' });
      }
    };

    fetchStatus();
  }, []);

  const languagePills = [
    { code: 'hi', label: 'हिन्दी (Hindi)' },
    { code: 'mr', label: 'मराठी (Marathi)' },
    { code: 'kn', label: 'ಕನ್ನಡ (Kannada)' },
    { code: 'ta', label: 'தமிழ் (Tamil)' },
    { code: 'te', label: 'తెలుగు (Telugu)' },
    { code: 'gu', label: 'ગુજરાતી (Gujarati)' },
    { code: 'en', label: 'English' },
  ];

  return (
    <div className="kalpa-landing max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 relative">
      {/* Top-Right Language Option on Landing Page */}
      <div className="w-full flex justify-end pt-5 sm:pt-6 pb-2">
        <LanguageSelector />
      </div>

      <section className="kalpa-hero text-center">
        <img
          className="kalpa-hero-logo"
          src="/assets/kalpa-rupee-wordmark.png"
          alt="KALPA"
          width="969"
          height="281"
        />
        <h1 className="kalpa-editorial-title kalpa-hero-caption">
          <span className="kalpa-hero-caption-lead">{t('tagline_lead', 'AI-Powered Hyper-Local')}</span>
          <span className="kalpa-hero-caption-accent">{t('tagline_accent', 'Livelihood & Business Advisory')}</span>
          <span className="kalpa-hero-caption-end">{t('tagline_end', 'for Rural Bharat')}</span>
        </h1>
        <Link to="/intake" className="inline-flex">
          <button className="saffron-gradient-btn kalpa-hero-cta cursor-pointer" type="button">
            <Mic className="w-4 h-4" />
            <span>{t('start_journey', 'START YOUR BUSINESS JOURNEY')}</span>
          </button>
        </Link>
        <div className="kalpa-language-row" aria-label="Supported vernacular voice languages">
          <span className="kalpa-language-label">{t('supports_vernacular', 'Supports Vernacular Voice:')}</span>
          {languagePills.map((langItem) => {
            const isSelected = language === langItem.code;
            return (
              <button
                type="button"
                key={langItem.code}
                onClick={() => setLanguage(langItem.code)}
                className={`kalpa-language-pill transition-all cursor-pointer ${
                  isSelected ? 'bg-[#1B4D3E] text-white font-bold ring-2 ring-[#1B4D3E]/30' : 'hover:bg-[#FAF2E3]'
                }`}
              >
                {langItem.label}
              </button>
            );
          })}
        </div>
      </section>

      <section className="kalpa-journey-section" aria-labelledby="journey-heading">
        <div className="kalpa-section-heading">
          <p className="kalpa-eyebrow">KALPA JOURNEY</p>
          <h2 id="journey-heading" className="kalpa-editorial-title">From Idea to Your Next Step</h2>
        </div>
        <KalpaJourneyCarousel />
      </section>

      <KalpaArchitecturalBenefits />
    </div>
  );
};

export default HomePage;
