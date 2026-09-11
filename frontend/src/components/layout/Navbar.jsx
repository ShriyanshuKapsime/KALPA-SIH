import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Sparkles, Lock, Menu, X, Activity } from 'lucide-react';
import apiService from '../../services/api';

export const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [gatewayStatus, setGatewayStatus] = useState('checking');
  const location = useLocation();

  useEffect(() => {
    const handleScroll = () => {
      setIsScrolled(window.scrollY > 20);
    };
    window.addEventListener('scroll', handleScroll);
    return () => window.removeEventListener('scroll', handleScroll);
  }, []);

  useEffect(() => {
    const checkStatus = async () => {
      try {
        await apiService.checkGatewayHealth();
        setGatewayStatus('online');
      } catch (e) {
        setGatewayStatus('offline');
      }
    };
    checkStatus();
  }, []);

  const navLinks = [
    { name: 'Home', path: '/', activeStage: true },
    { name: '01 Intake & NLP', path: '/intake', activeStage: true, badge: 'Stage 1' },
    { name: '02 Classification', path: '/classification', activeStage: true, badge: 'Stage 2' },
    { name: '03 Business Profile', path: '/profile', activeStage: true, badge: 'Stage 3' },
    { name: '04 Market Intel', path: '/market', activeStage: false, locked: true },
    { name: '05 Feasibility', path: '/feasibility', activeStage: false, locked: true },
    { name: '06 DPR Generator', path: '/dpr', activeStage: false, locked: true },
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'bg-[#FAF7F2]/90 backdrop-blur-md shadow-sm border-b border-[#EAE3D5] py-3' : 'bg-transparent py-4'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#EA580C] to-[#C2410C] flex items-center justify-center shadow-md shadow-orange-600/20 group-hover:scale-105 transition-transform duration-200">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-bold tracking-tight text-[#1C1917] font-['Outfit']">KALPA</span>
                <span className="text-[10px] uppercase tracking-wider font-bold px-2 py-0.5 rounded-full bg-orange-100 text-[#C2410C] border border-orange-200">
                  SIH 2026
                </span>
              </div>
              <p className="text-[11px] text-[#78716C] font-medium hidden sm:block">
                Livelihood & Business Advisory for Rural Bharat
              </p>
            </div>
          </Link>

          {/* Desktop Navigation */}
          <nav className="hidden md:flex items-center gap-1.5 bg-white/90 p-1.5 rounded-2xl border border-[#EAE3D5] shadow-sm backdrop-blur-md">
            {navLinks.map((link) => {
              const isActive = location.pathname === link.path && link.activeStage;
              if (link.locked) {
                return (
                  <div
                    key={link.name}
                    className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-xs font-medium text-[#A8A29E] cursor-not-allowed select-none"
                    title="Available in sequential stage progression"
                  >
                    <Lock className="w-3 h-3 text-[#A8A29E]" />
                    <span>{link.name}</span>
                  </div>
                );
              }
              return (
                <Link
                  key={link.path}
                  to={link.path}
                  className={`flex items-center gap-1.5 px-3.5 py-1.5 rounded-xl text-xs font-semibold transition-all duration-200 ${
                    isActive
                      ? 'bg-[#EA580C] text-white shadow-sm'
                      : 'text-[#57534E] hover:text-[#1C1917] hover:bg-[#FAF7F2]'
                  }`}
                >
                  <span>{link.name}</span>
                  {link.badge && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded bg-white/20 text-white font-bold">
                      {link.badge}
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* System Status & Mobile toggle */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#EAE3D5] text-xs shadow-sm">
              <div
                className={`w-2 h-2 rounded-full ${
                  gatewayStatus === 'online'
                    ? 'bg-emerald-500 animate-pulse'
                    : gatewayStatus === 'checking'
                    ? 'bg-amber-400'
                    : 'bg-rose-500'
                }`}
              />
              <span className="text-[#78716C] text-[11px]">
                Gateway: <strong className="text-[#1C1917] uppercase">{gatewayStatus}</strong>
              </span>
            </div>

            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              className="p-2 rounded-xl text-[#57534E] hover:text-[#1C1917] hover:bg-white md:hidden"
            >
              {mobileMenuOpen ? <X className="w-6 h-6" /> : <Menu className="w-6 h-6 text-[#1C1917]" />}
            </button>
          </div>
        </div>

        {/* Mobile menu dropdown */}
        {mobileMenuOpen && (
          <div className="md:hidden mt-3 p-4 bg-white rounded-2xl border border-[#EAE3D5] shadow-lg space-y-2 animate-fadeIn">
            {navLinks.map((link) => {
              if (link.locked) {
                return (
                  <div
                    key={link.name}
                    className="flex items-center justify-between px-4 py-2 rounded-xl text-sm font-medium text-[#A8A29E]"
                  >
                    <span>{link.name}</span>
                    <span className="text-[10px] bg-stone-100 text-stone-500 px-2 py-0.5 rounded">Locked</span>
                  </div>
                );
              }
              return (
                <Link
                  key={link.name}
                  to={link.path}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`block px-4 py-2 rounded-xl text-sm font-medium ${
                    location.pathname === link.path
                      ? 'bg-[#EA580C] text-white font-semibold'
                      : 'text-[#44403C] hover:bg-[#FAF7F2]'
                  }`}
                >
                  {link.name}
                </Link>
              );
            })}
          </div>
        )}
      </div>
    </header>
  );
};

export default Navbar;
