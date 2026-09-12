import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { 
  Sparkles, 
  Mic, 
  ArrowRight, 
  CheckCircle2, 
  Lock, 
  Layers, 
  Compass, 
  TrendingUp, 
  FileText,
  ShieldCheck,
  Award,
  DollarSign,
  Bot,
  UserCheck
} from 'lucide-react';
import Card, { CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import apiService from '../../services/api';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';

export const HomePage = () => {
  const [gatewayHealth, setGatewayHealth] = useState({ status: 'checking' });
  const [aiHealth, setAiHealth] = useState({ status: 'checking' });

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const gw = await apiService.checkGatewayHealth();
        setGatewayHealth(gw);
      } catch (e) {
        setGatewayHealth({ status: 'offline' });
      }

      try {
        const ai = await apiService.checkAIHealth();
        setAiHealth(ai);
      } catch (e) {
        setAiHealth({ status: 'offline' });
      }
    };

    fetchStatus();
  }, []);

  const journeyPillars = [
    {
      step: '01',
      pillar: 'Understand',
      title: 'Intake, Classification & Profile',
      desc: 'Multilingual vernacular voice & text intake, 5-digit NIC ontology classification, and canonical MSME profile.',
      active: true,
      badge: 'Active — Stages 1-3',
      link: '/intake',
      icon: UserCheck,
    },
    {
      step: '02',
      pillar: 'Discover',
      title: 'Spatial Market Intelligence',
      desc: 'Hyper-local radius demographics, competitor mapping, supply chain accessibility, and demand benchmarking.',
      active: true,
      badge: 'Orchestrator Stage 5',
      link: '/market-intelligence',
      icon: Compass,
    },
    {
      step: '03',
      pillar: 'Validate',
      title: 'Opportunity Evaluation Engine',
      desc: 'Deterministic 6-factor opportunity score synthesizing demand, competition pressure, infrastructure, and local capacity.',
      active: true,
      badge: 'Orchestrator Stage 8',
      link: '/opportunity-evaluation',
      icon: Award,
    },
    {
      step: '04',
      pillar: 'Finance',
      title: 'Financial Planning & Scheme Match',
      desc: 'Fixed CapEx/OpEx structuring, 90% debt sizing, annuity repayment amortization, and institutional PMMY/PMEGP matching.',
      active: true,
      badge: 'Orchestrator Stage 9',
      link: '/financial-planning',
      icon: DollarSign,
    },
    {
      step: '05',
      pillar: 'Prepare',
      title: 'Risk Assessment & DPR Generator',
      desc: 'Automated climatic & supply risk modeling, SWOT analysis, and institutional bankable Detailed Project Reports.',
      active: false,
      badge: 'Future Stage (Locked)',
      locked: true,
      icon: ShieldCheck,
    },
    {
      step: '06',
      pillar: 'Grow',
      title: 'Personal AI Advisor & Growth Manager',
      desc: 'Conversational vernacular advisor for day-to-day operations, working capital monitoring, and market expansion.',
      active: false,
      badge: 'Future Stage (Locked)',
      locked: true,
      icon: Bot,
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16 py-6">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-4 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-100 border border-orange-200 text-[#C2410C] text-xs font-bold shadow-2xs">
          <Sparkles className="w-3.5 h-3.5 text-[#EA580C]" />
          <span>Smart India Hackathon 2026 &middot; Rural Enterprise Advisory</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-black tracking-tight text-[#1C1917] font-['Outfit'] leading-tight">
          AI-Powered Hyper-Local <br />
          <span className="text-[#EA580C]">Livelihood & Business Advisory</span> <br />
          for <span className="text-[#292524]">Rural Bharat</span>
        </h1>

        <p className="text-base sm:text-lg text-[#57534E] max-w-2xl mx-auto leading-relaxed font-normal">
          A workflow-first journey guided by the KALPA Orchestrator Agent. From an entrepreneurial idea in native vernacular to validated market feasibility and bankable financing.
        </p>

        {/* Primary CTAs */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/intake">
            <button className="saffron-gradient-btn px-8 py-3.5 rounded-xl font-bold text-sm shadow-md hover:scale-105 transition-all flex items-center gap-2 cursor-pointer">
              <Mic className="w-4 h-4" />
              <span>START YOUR BUSINESS JOURNEY</span>
            </button>
          </Link>
          <Link to="/journey">
            <button className="px-6 py-3.5 rounded-xl font-bold text-sm bg-white hover:bg-stone-50 border border-[#EAE3D5] text-[#57534E] shadow-2xs transition-all flex items-center gap-2 cursor-pointer">
              <Compass className="w-4 h-4 text-[#EA580C]" />
              <span>Explore Orchestrator Journey</span>
            </button>
          </Link>
        </div>

        {/* Indic Language Pills */}
        <div className="pt-2 flex flex-wrap items-center justify-center gap-2 text-xs text-[#78716C]">
          <span className="font-semibold">Supports Vernacular Voice:</span>
          <span className="px-2.5 py-0.5 rounded-md bg-stone-100 border border-stone-200 text-stone-700 font-medium">हिन्दी (Hindi)</span>
          <span className="px-2.5 py-0.5 rounded-md bg-stone-100 border border-stone-200 text-stone-700 font-medium">मराठी (Marathi)</span>
          <span className="px-2.5 py-0.5 rounded-md bg-stone-100 border border-stone-200 text-stone-700 font-medium">தமிழ் (Tamil)</span>
          <span className="px-2.5 py-0.5 rounded-md bg-stone-100 border border-stone-200 text-stone-700 font-medium">తెలుగు (Telugu)</span>
          <span className="px-2.5 py-0.5 rounded-md bg-stone-100 border border-stone-200 text-stone-700 font-medium">English</span>
        </div>
      </section>

      {/* Embedded Live Workflow Timeline */}
      <section>
        <WorkflowTimeline />
      </section>

      {/* 6 Journey Pillars Roadmap */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <Badge variant="saffron">Sequential Architecture</Badge>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1C1917] font-['Outfit']">
            The 6 KALPA Journey Pillars
          </h2>
          <p className="text-xs sm:text-sm text-[#57534E]">
            A structured entrepreneurship progression controlled by the KALPA Orchestrator Agent.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-2">
          {journeyPillars.map((item, idx) => {
            const Icon = item.icon;
            if (item.active) {
              return (
                <div
                  key={idx}
                  className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white shadow-sm flex flex-col justify-between hover:border-[#EA580C] transition-all"
                >
                  <div>
                    <div className="flex items-center justify-between mb-3">
                      <span className="text-2xl font-black text-[#EA580C] font-['Outfit']">
                        {item.step}
                      </span>
                      <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-orange-100 text-[#C2410C] border border-orange-200">
                        {item.pillar}
                      </span>
                    </div>

                    <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] mb-1.5">
                      {item.title}
                    </h3>
                    <p className="text-xs text-[#57534E] leading-relaxed">
                      {item.desc}
                    </p>
                  </div>

                  <div className="mt-6 pt-4 border-t border-[#EAE3D5] flex items-center justify-between">
                    <span className="text-xs font-semibold text-emerald-700 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5" />
                      Active Stage
                    </span>
                    <Link to={item.link}>
                      <button className="px-3.5 py-1.5 rounded-lg text-xs font-bold text-[#C2410C] bg-orange-50 hover:bg-orange-100 border border-orange-200 transition-colors flex items-center gap-1">
                        <span>Launch</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </Link>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={idx}
                className="rounded-2xl p-6 border border-[#EAE3D5]/80 bg-white/70 opacity-80 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xl font-bold text-stone-400 font-['Outfit']">
                      {item.step}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-stone-200/60 text-stone-600 font-medium">
                      <Lock className="w-3 h-3" />
                      Locked Milestone
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-stone-700 mb-1.5 font-['Outfit']">
                    {item.title}
                  </h3>
                  <p className="text-xs text-stone-500 leading-relaxed">
                    {item.desc}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-stone-200/60 flex items-center justify-between text-[11px] text-stone-400">
                  <span>Unlocks in Phase 2</span>
                  <span className="font-semibold">{item.pillar}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* System Infrastructure Banner */}
      <section className="royal-panel rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4 border border-[#EAE3D5]">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#EA580C]" />
            Pipeline Infrastructure Status
          </h3>
          <p className="text-xs text-[#78716C] mt-0.5">
            Stage 1-9 Deterministic Multi-Agent & Scheme Calculation Engine
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#EAE3D5] text-xs">
            <span className="text-[#78716C]">Gateway:</span>
            <Badge variant={gatewayHealth.status === 'online' || gatewayHealth.status === 'healthy' ? 'emerald' : 'amber'}>
              {gatewayHealth.status || 'Checking'}
            </Badge>
          </div>

          <div className="flex items-center gap-2 px-3 py-1.5 rounded-xl bg-white border border-[#EAE3D5] text-xs">
            <span className="text-[#78716C]">AI Engine:</span>
            <Badge variant={aiHealth.status === 'healthy' ? 'emerald' : 'amber'}>
              {aiHealth.status || 'Active'}
            </Badge>
          </div>
        </div>
      </section>
    </div>
  );
};

export default HomePage;
