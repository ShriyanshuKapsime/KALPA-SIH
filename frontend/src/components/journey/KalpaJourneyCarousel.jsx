import React from 'react';
import CoverflowCarousel from '../ui/coverflow-carousel';

const JOURNEY_CARDS = [
  { id: '01', src: '/assets/01-feature.webp', alt: 'KALPA Journey Step 01: Understand - Start With Your Idea' },
  { id: '02', src: '/assets/02-feature.webp', alt: 'KALPA Journey Step 02: Discover - Know Your Local Market' },
  { id: '03', src: '/assets/03-feature.webp', alt: 'KALPA Journey Step 03: Validate - Find the Right Opportunity' },
  { id: '04', src: '/assets/04-feature.webp', alt: 'KALPA Journey Step 04: Plan - Plan Your Money' },
  { id: '05', src: '/assets/05-feature.webp', alt: 'KALPA Journey Step 05: Support - Find Schemes & Funding' },
  { id: '06', src: '/assets/06-feature.webp', alt: 'KALPA Journey Step 06: Review - Test Your Business Plan' },
  { id: '07', src: '/assets/07-feature.webp', alt: 'KALPA Journey Step 07: Prepare - Build Your Business Report' },
  { id: '08', src: '/assets/08-feature.webp', alt: 'KALPA Journey Step 08: Guidance - Get Practical Support' },
  { id: '09', src: '/assets/09-feature.webp', alt: 'KALPA Journey Step 09: Grow - Plan Your Next Step' },
];

export const KalpaJourneyCarousel = () => {
  return (
    <div className="kalpa-journey-stack-wrapper w-full max-w-6xl mx-auto px-2">
      <CoverflowCarousel
        items={JOURNEY_CARDS}
        rotate={38}
        depth={0.52}
        perspective={3.5}
        falloff={0.6}
        fade={0.08}
        gap={0.05}
        showCaption={false}
        showNavigation={true}
        autoplay={true}
        autoplayInterval={4500}
      />
    </div>
  );
};

export default KalpaJourneyCarousel;
