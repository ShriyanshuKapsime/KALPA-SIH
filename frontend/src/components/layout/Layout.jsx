import React from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Navbar from './Navbar';
import Footer from './Footer';
import ScrollToTop from './ScrollToTop';
import GlobalBackground from '../ui/GlobalBackground';
import GlobalPageTranslator from './GlobalPageTranslator';
import FloatingAssistantWidget from '../assistant/FloatingAssistantWidget';

export const Layout = () => {
  const location = useLocation();
  const isLandingPage = location.pathname === '/';
  const isAssistantPage = location.pathname.startsWith('/assistant');
  const isSwotOrDownstream =
    location.pathname.startsWith('/swot') ||
    location.pathname.startsWith('/dpr') ||
    location.pathname.startsWith('/growth-manager');

  return (
    <div className="kalpa-app-shell flex flex-col min-h-screen relative">
      <ScrollToTop />
      <GlobalBackground />
      <GlobalPageTranslator />
      <div className="kalpa-content relative z-10 flex flex-col flex-grow">
        {!isLandingPage && !isAssistantPage && <Navbar />}
        <main className={`flex-grow ${isAssistantPage ? 'flex flex-col h-[100dvh]' : 'pb-12'}`}>
          <Outlet />
        </main>
        {!isAssistantPage && <Footer />}
      </div>
      {/* Global AI Advisor floating trigger & window only from SWOT analysis page onwards */}
      {!isLandingPage && !isAssistantPage && isSwotOrDownstream && <FloatingAssistantWidget />}
    </div>
  );
};

export default Layout;
