import React, { useState, useEffect, useRef, useCallback } from 'react';
import { ArrowLeft, ArrowRight } from 'lucide-react';

const BENEFITS_DATA = [
  {
    id: '01',
    label: 'FOR THE ENTREPRENEUR',
    shortLabel: 'Entrepreneur',
    text: 'Instead of discovering after taking a loan that the market is too small or competition is too high, the entrepreneur gets a data-driven feasibility assessment based on local market demand before committing capital.',
  },
  {
    id: '02',
    label: 'FOR THE FAMILY',
    shortLabel: 'Family',
    text: 'Better project costing and clear understanding of loan structuring, margin requirements, and repayment schedules helps reduce financial confusion and the risk of unsustainable debt.',
  },
  {
    id: '03',
    label: 'FOR THE VILLAGE',
    shortLabel: 'Village',
    text: 'A viable dairy, retail, poultry or other micro-enterprise can create local income and employment instead of forcing economic activity to move elsewhere.',
  },
  {
    id: '04',
    label: 'FOR THE LONG TERM',
    shortLabel: 'Long Term',
    text: 'KALPA continuously monitors newly funded micro-enterprises and uses real business outcomes to improve future recommendations and reduce business failure.',
  },
];

export const KalpaArchitecturalBenefits = () => {
  const [activeIndex, setActiveIndex] = useState(0);
  const [prefersReducedMotion, setPrefersReducedMotion] = useState(false);
  const sectionRef = useRef(null);
  const isAutoScrollingRef = useRef(false);

  // Check prefers-reduced-motion
  useEffect(() => {
    const mediaQuery = window.matchMedia('(prefers-reduced-motion: reduce)');
    setPrefersReducedMotion(mediaQuery.matches);
    const handler = (e) => setPrefersReducedMotion(e.matches);
    mediaQuery.addEventListener('change', handler);
    return () => mediaQuery.removeEventListener('change', handler);
  }, []);

  // Scroll listener for sticky progress
  useEffect(() => {
    let rafId = null;

    const handleScroll = () => {
      if (isAutoScrollingRef.current) return;
      if (!sectionRef.current) return;

      const rect = sectionRef.current.getBoundingClientRect();
      const sectionHeight = sectionRef.current.offsetHeight;
      const viewportHeight = window.innerHeight;
      const totalScrollable = sectionHeight - viewportHeight;

      if (totalScrollable <= 0) return;

      const scrolled = -rect.top;
      const progress = Math.max(0, Math.min(1, scrolled / totalScrollable));

      let index = 0;
      if (progress < 0.25) {
        index = 0;
      } else if (progress < 0.5) {
        index = 1;
      } else if (progress < 0.75) {
        index = 2;
      } else {
        index = 3;
      }

      setActiveIndex((prev) => (prev !== index ? index : prev));
    };

    const onScroll = () => {
      if (rafId) cancelAnimationFrame(rafId);
      rafId = requestAnimationFrame(handleScroll);
    };

    window.addEventListener('scroll', onScroll, { passive: true });
    handleScroll();

    return () => {
      window.removeEventListener('scroll', onScroll);
      if (rafId) cancelAnimationFrame(rafId);
    };
  }, []);

  // Smooth scroll to target benefit
  const scrollToBenefit = useCallback((index) => {
    if (!sectionRef.current) return;
    setActiveIndex(index);

    const rect = sectionRef.current.getBoundingClientRect();
    const currentScrollY = window.scrollY;
    const sectionTop = currentScrollY + rect.top;
    const sectionHeight = sectionRef.current.offsetHeight;
    const viewportHeight = window.innerHeight;
    const totalScrollable = sectionHeight - viewportHeight;

    const targetScroll = sectionTop + (index / 3.2) * totalScrollable;

    isAutoScrollingRef.current = true;
    window.scrollTo({
      top: targetScroll,
      behavior: 'smooth',
    });

    setTimeout(() => {
      isAutoScrollingRef.current = false;
    }, 750);
  }, []);

  const goToNext = useCallback(() => {
    const next = (activeIndex + 1) % BENEFITS_DATA.length;
    scrollToBenefit(next);
  }, [activeIndex, scrollToBenefit]);

  const goToPrev = useCallback(() => {
    const prev = (activeIndex - 1 + BENEFITS_DATA.length) % BENEFITS_DATA.length;
    scrollToBenefit(prev);
  }, [activeIndex, scrollToBenefit]);

  const activeBenefit = BENEFITS_DATA[activeIndex];

  return (
    <section
      ref={sectionRef}
      className="kalpa-minimal-benefits-track relative min-h-[280vh] mt-16 sm:mt-24"
      aria-labelledby="benefits-heading"
    >
      {/* Sticky Centered Viewport Stage */}
      <div className="sticky top-0 h-screen flex flex-col items-center justify-center px-4 overflow-hidden z-10">
        {/* Section Heading */}
        <div className="kalpa-section-heading mb-6 sm:mb-8 text-center">
          <p className="kalpa-eyebrow">KALPA BENEFITS</p>
          <h2 id="benefits-heading" className="kalpa-editorial-title text-2xl sm:text-3xl md:text-4xl">
            Benefits
          </h2>
        </div>

        {/* Minimal Architectural Arched Window */}
        <div className="relative w-full max-w-[520px] mx-auto">
          <article
            className="kalpa-minimal-window relative w-full rounded-t-[140px] sm:rounded-t-[170px] rounded-b-xl border-[2.5px] border-[#7A563E] bg-[#F3E5CA] shadow-[0_16px_36px_rgba(80,60,40,0.08)] overflow-hidden transition-all duration-500"
            style={{
              background: 'linear-gradient(180deg, #FAF4E8 0%, #F3E5CA 100%)',
            }}
          >
            {/* Subtle Minimal Arched Upper Panes Divider */}
            <div className="w-full h-16 sm:h-20 border-b border-[#7A563E]/20 flex items-center justify-center relative overflow-hidden" aria-hidden="true">
              {/* Minimal Arch Line */}
              <div className="absolute top-2 w-28 sm:w-36 h-28 sm:h-36 rounded-full border border-[#7A563E]/20 pointer-events-none" />
              {/* Subtle Central Divider */}
              <div className="absolute top-0 bottom-0 left-1/2 w-[1px] bg-[#7A563E]/20 pointer-events-none" />
            </div>

            {/* Content Body Area (Spacious, Generously Padded, 100% Contained) */}
            <div className="px-6 py-8 sm:px-10 sm:py-10 text-center relative z-10 min-h-[260px] sm:min-h-[280px] flex flex-col justify-center">
              {BENEFITS_DATA.map((benefit, idx) => {
                const isActive = idx === activeIndex;

                return (
                  <div
                    key={benefit.id}
                    className={`transition-all duration-600 ease-[cubic-bezier(0.22,1,0.36,1)] ${
                      isActive
                        ? 'opacity-100 transform translate-y-0 relative'
                        : 'opacity-0 transform translate-y-3 absolute inset-x-6 sm:inset-x-10 pointer-events-none hidden'
                    }`}
                    style={isActive ? { display: 'block' } : { display: 'none' }}
                    aria-hidden={!isActive}
                  >
                    {/* Small Label: 01 · KALPA BENEFIT */}
                    <p className="text-[11px] sm:text-xs font-bold tracking-[0.16em] text-[#7A563E] uppercase mb-2 sm:mb-3">
                      {benefit.id} · KALPA BENEFIT
                    </p>

                    {/* Primary Heading */}
                    <h3 className="text-lg sm:text-xl md:text-2xl font-bold text-[#006B59] font-['Playfair_Display',Georgia,serif] tracking-tight mb-3 sm:mb-4">
                      {benefit.label}
                    </h3>

                    {/* Exact Paragraph Body */}
                    <p className="text-[14.5px] sm:text-[16px] md:text-[16.5px] leading-[1.68] text-[#382A22] font-medium max-w-lg mx-auto">
                      {benefit.text}
                    </p>
                  </div>
                );
              })}
            </div>
          </article>
        </div>

        {/* Minimal Editorial Index Navigation (Directly Below Window) */}
        <nav
          className="flex flex-wrap items-center justify-center gap-2 sm:gap-4 mt-6 sm:mt-8 text-sm"
          aria-label="Benefits editorial index navigation"
        >
          {/* Previous Arrow */}
          <button
            type="button"
            onClick={goToPrev}
            className="p-1.5 text-[#006B59] hover:text-[#7A563E] transition-colors cursor-pointer"
            aria-label="Previous benefit"
            title="Previous benefit"
          >
            <ArrowLeft className="w-4 h-4 sm:w-5 sm:h-5" aria-hidden="true" />
          </button>

          {/* Plain Text Links / Active Brown Pill */}
          <div className="flex flex-wrap items-center gap-1 sm:gap-2">
            {BENEFITS_DATA.map((benefit, idx) => {
              const isActive = idx === activeIndex;

              return (
                <button
                  key={benefit.id}
                  type="button"
                  onClick={() => scrollToBenefit(idx)}
                  className={`text-xs sm:text-sm font-semibold transition-all duration-200 cursor-pointer ${
                    isActive
                      ? 'bg-[#7A563E] text-[#FAF4E8] rounded-full px-3.5 py-1.5 shadow-sm'
                      : 'text-[#6F746E] hover:text-[#26332F] px-2.5 py-1.5 bg-transparent border-0'
                  }`}
                  aria-current={isActive ? 'true' : 'false'}
                  aria-label={`Jump to ${benefit.label}`}
                >
                  <span className="opacity-90 mr-1">{benefit.id}</span>
                  <span>{benefit.shortLabel}</span>
                </button>
              );
            })}
          </div>

          {/* Next Arrow */}
          <button
            type="button"
            onClick={goToNext}
            className="p-1.5 text-[#006B59] hover:text-[#7A563E] transition-colors cursor-pointer"
            aria-label="Next benefit"
            title="Next benefit"
          >
            <ArrowRight className="w-4 h-4 sm:w-5 sm:h-5" aria-hidden="true" />
          </button>
        </nav>
      </div>
    </section>
  );
};

export default KalpaArchitecturalBenefits;
