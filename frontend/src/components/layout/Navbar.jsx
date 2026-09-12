import React, { useState, useEffect } from 'react';
import { Link, useLocation } from 'react-router-dom';
import {
  Sparkles,
  Lock,
  Menu,
  X,
  CheckCircle2,
  Activity,
  Compass,
  Award,
  DollarSign,
  Layers,
  ChevronDown,
  ShieldCheck,
  Bot
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';

export const Navbar = () => {
  const [isScrolled, setIsScrolled] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [gatewayStatus, setGatewayStatus] = useState('checking');
  const [understandMenuOpen, setUnderstandMenuOpen] = useState(false);
  const location = useLocation();

  const {
    sessionId,
    analysisId,
    completedStages,
    currentStage,
    businessName,
    engineOutputs
  } = useWorkflow();

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

  const getStageUrl = (basePath) => {
    if (basePath === '/') return basePath;
    const [path, existingQs] = basePath.split('?');
    const params = new URLSearchParams(existingQs || '');
    if (sessionId) params.set('session_id', sessionId);
    if (analysisId) params.set('analysis_id', analysisId);
    const qs = params.toString();
    return qs ? `${path}?${qs}` : path;
  };

  // 6 Journey Pillars
  const journeyNav = [
    {
      id: 'understand',
      name: 'Understand',
      path: '/intake',
      stageNums: [1, 2, 3],
      unlocked: true,
      isDone: completedStages?.includes(1) && completedStages?.includes(2) && completedStages?.includes(3),
      subItems: [
        { name: 'Stage 1: Intake', path: '/intake', done: completedStages?.includes(1) },
        { name: 'Stage 2: Classification', path: '/classification', done: completedStages?.includes(2) },
        { name: 'Stage 3: Profile', path: '/profile', done: completedStages?.includes(3) }
      ]
    },
    {
      id: 'discover',
      name: 'Discover',
      path: '/market-intelligence',
      stageNums: [5],
      unlocked: Boolean(sessionId || analysisId || completedStages?.includes(3) || completedStages?.includes(5)),
      isDone: completedStages?.includes(5),
      badge: engineOutputs?.market_intelligence || (completedStages?.includes(5) ? 'Demand Strong ✓' : null)
    },
    {
      id: 'validate',
      name: 'Validate',
      path: '/opportunity-evaluation',
      stageNums: [8],
      unlocked: Boolean(sessionId || analysisId || completedStages?.includes(5) || completedStages?.includes(8)),
      isDone: completedStages?.includes(8),
      badge: engineOutputs?.opportunity_evaluation || (completedStages?.includes(8) ? '88% Opportunity ✓' : null)
    },
    {
      id: 'finance',
      name: 'Finance',
      path: '/financial-planning',
      stageNums: [9],
      unlocked: Boolean(sessionId || analysisId || completedStages?.includes(8) || completedStages?.includes(9)),
      isDone: completedStages?.includes(9),
      badge: engineOutputs?.financial_planning || (completedStages?.includes(9) ? '₹9L Loan ✓' : null)
    },
    {
      id: 'prepare',
      name: 'Prepare',
      path: '#locked',
      locked: true,
      stageNums: [10, 11, 12, 13],
      badge: 'Locked'
    },
    {
      id: 'grow',
      name: 'Grow',
      path: '#locked',
      locked: true,
      stageNums: [14, 15],
      badge: 'Locked'
    }
  ];

  return (
    <header
      className={`fixed top-0 left-0 right-0 z-50 transition-all duration-300 ${
        isScrolled ? 'bg-[#FAF7F2]/95 backdrop-blur-md shadow-sm border-b border-[#EAE3D5] py-2.5' : 'bg-[#FAF7F2]/80 backdrop-blur-sm py-3.5 border-b border-[#EAE3D5]/50'
      }`}
    >
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between">
          
          {/* Logo & Brand */}
          <Link to="/" className="flex items-center gap-3 group">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-[#EA580C] via-[#D97706] to-[#C2410C] flex items-center justify-center shadow-md shadow-orange-600/20 group-hover:scale-105 transition-transform duration-200">
              <Sparkles className="w-5 h-5 text-white" />
            </div>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xl font-black tracking-tight text-[#1C1917] font-['Outfit']">KALPA</span>
                <span className="text-[10px] uppercase tracking-wider font-extrabold px-2 py-0.5 rounded-full bg-orange-100 text-[#C2410C] border border-orange-200">
                  SIH 2026
                </span>
              </div>
              <p className="text-[11px] text-[#78716C] font-medium hidden sm:block">
                Livelihood & Business Advisory for Rural Bharat
              </p>
            </div>
          </Link>

          {/* 6 Journey Pillars Navigation (Desktop) */}
          <nav className="hidden md:flex items-center gap-1.5 bg-white/95 p-1.5 rounded-2xl border border-[#EAE3D5] shadow-2xs backdrop-blur-md">
            
            {/* Journey Hub Quick Tab */}
            <Link
              to={getStageUrl('/journey')}
              className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                location.pathname === '/journey'
                  ? 'bg-[#EA580C] text-white shadow-sm'
                  : 'text-[#57534E] hover:text-[#1C1917] hover:bg-stone-50'
              }`}
            >
              <Compass className="w-3.5 h-3.5" />
              <span>Journey Hub</span>
            </Link>

            <div className="w-px h-5 bg-stone-200 mx-1" />

            {/* Journey Pillars */}
            {journeyNav.map((pillar) => {
              if (pillar.locked) {
                return (
                  <div
                    key={pillar.id}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium text-stone-400 cursor-not-allowed select-none opacity-80"
                    title={`${pillar.name} unlocks in Phase 2`}
                  >
                    <Lock className="w-3 h-3 text-stone-400" />
                    <span>{pillar.name}</span>
                  </div>
                );
              }

              if (!pillar.unlocked) {
                return (
                  <div
                    key={pillar.id}
                    className="flex items-center gap-1 px-2.5 py-1.5 rounded-xl text-xs font-medium text-stone-400 cursor-not-allowed select-none"
                    title="Complete previous stages to unlock"
                  >
                    <Lock className="w-3 h-3 text-stone-400" />
                    <span>{pillar.name}</span>
                  </div>
                );
              }

              const isActive = location.pathname.startsWith(pillar.path) || (pillar.id === 'understand' && ['/intake', '/classification', '/profile'].includes(location.pathname));

              return (
                <Link
                  key={pillar.id}
                  to={getStageUrl(pillar.path)}
                  className={`flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-xs font-bold transition-all duration-200 ${
                    isActive
                      ? 'bg-[#EA580C] text-white shadow-sm'
                      : pillar.isDone
                      ? 'text-[#1C1917] hover:bg-stone-50'
                      : 'text-[#57534E] hover:text-[#1C1917] hover:bg-stone-50'
                  }`}
                >
                  {pillar.isDone && !isActive && (
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 inline shrink-0" />
                  )}
                  <span>{pillar.name}</span>
                  {pillar.badge && !isActive && (
                    <span className="text-[9px] px-1.5 py-0.2 rounded font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
                      ✓
                    </span>
                  )}
                </Link>
              );
            })}
          </nav>

          {/* System Status & Mobile Toggle */}
          <div className="flex items-center gap-3">
            <div className="hidden lg:flex items-center gap-2 px-3 py-1 rounded-full bg-white border border-[#EAE3D5] text-xs shadow-2xs">
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
            <Link
              to={getStageUrl('/journey')}
              onClick={() => setMobileMenuOpen(false)}
              className="block px-4 py-2.5 rounded-xl text-sm font-bold bg-orange-50 text-[#C2410C] border border-orange-200"
            >
              🧭 Orchestrator Journey Hub
            </Link>

            {journeyNav.map((pillar) => {
              if (pillar.locked) {
                return (
                  <div
                    key={pillar.id}
                    className="flex items-center justify-between px-4 py-2 rounded-xl text-sm font-medium text-stone-400"
                  >
                    <span>{pillar.name}</span>
                    <span className="text-[10px] bg-stone-100 text-stone-500 px-2 py-0.5 rounded">Locked Milestone</span>
                  </div>
                );
              }

              return (
                <Link
                  key={pillar.id}
                  to={getStageUrl(pillar.path)}
                  onClick={() => setMobileMenuOpen(false)}
                  className={`flex items-center justify-between px-4 py-2 rounded-xl text-sm font-semibold ${
                    location.pathname.startsWith(pillar.path)
                      ? 'bg-[#EA580C] text-white'
                      : 'text-[#44403C] hover:bg-[#FAF7F2]'
                  }`}
                >
                  <span>{pillar.name}</span>
                  {pillar.isDone && <CheckCircle2 className="w-4 h-4 text-emerald-500" />}
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
