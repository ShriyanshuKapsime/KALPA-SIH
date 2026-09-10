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
  ShieldCheck
} from 'lucide-react';
import Card, { CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import Button from '../../components/ui/Button';
import Badge from '../../components/ui/Badge';
import apiService from '../../services/api';

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

  const sequentialWorkflow = [
    {
      step: '01',
      title: 'Business Idea & Vernacular Intake',
      desc: 'Capture entrepreneurial ideas in Hindi, Tamil, Telugu, Marathi, and English via voice or text with Sarvam STT and deterministic NLP.',
      active: true,
      badge: 'Active — Phase 1',
      link: '/intake',
      icon: Mic,
    },
    {
      step: '02',
      title: 'Entrepreneur Profile & Experience',
      desc: 'Extract investment capital, location boundaries, technical skills, and past commercial experience.',
      active: false,
      badge: 'Stage 2 Ready',
      locked: true,
    },
    {
      step: '03',
      title: 'Business Classification & NIC Mapping',
      desc: 'Deterministic mapping into 5-digit National Industrial Classification (NIC) and domain ontology taxonomy.',
      active: false,
      badge: 'Upcoming Stage 2',
      locked: true,
    },
    {
      step: '04',
      title: 'Spatial Market Intelligence',
      desc: 'PostGIS hyper-local radius competition mapping, infrastructure accessibility, and demand benchmarking.',
      active: false,
      badge: 'Future Stage',
      locked: true,
    },
    {
      step: '05',
      title: 'ML Feasibility & Risk Modeling',
      desc: 'Multivariate enterprise survivability assessment combining financial viability, local demand, and risk index.',
      active: false,
      badge: 'Future Stage',
      locked: true,
    },
    {
      step: '06',
      title: 'Bankable DPR Generator',
      desc: 'Institutional-grade Detailed Project Report generation aligned with PMMY / PMEGP credit parameters.',
      active: false,
      badge: 'Future Stage',
      locked: true,
    },
  ];

  return (
    <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 space-y-16 py-6">
      {/* Hero Section */}
      <section className="text-center space-y-6 pt-4 max-w-4xl mx-auto">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full bg-orange-100/80 border border-orange-200/80 text-[#C2410C] text-xs font-semibold shadow-sm">
          <Sparkles className="w-3.5 h-3.5 text-[#EA580C]" />
          <span>Smart India Hackathon 2026 • Bharat Rural Advisory</span>
        </div>

        <h1 className="text-4xl sm:text-6xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit'] leading-tight">
          AI-Powered Hyper-Local <br />
          <span className="text-[#EA580C]">Livelihood & Business Advisory</span> <br />
          for <span className="text-[#292524]">Rural Bharat</span>
        </h1>

        <p className="text-base sm:text-lg text-[#57534E] max-w-2xl mx-auto leading-relaxed">
          From an entrepreneurial idea to an informed, sustainable business decision.
        </p>

        {/* Primary CTA */}
        <div className="pt-4 flex flex-col sm:flex-row items-center justify-center gap-4">
          <Link to="/intake">
            <Button size="lg" icon={Mic} className="px-8 py-3.5 text-base shadow-lg shadow-orange-500/20">
              START YOUR BUSINESS JOURNEY
            </Button>
          </Link>
        </div>

        {/* Indic Language Pills */}
        <div className="pt-2 flex flex-wrap items-center justify-center gap-2 text-xs text-[#78716C]">
          <span>Supports:</span>
          <span className="px-2 py-0.5 rounded bg-stone-100 border border-stone-200 text-stone-700">हिन्दी (Hindi)</span>
          <span className="px-2 py-0.5 rounded bg-stone-100 border border-stone-200 text-stone-700">मराठी (Marathi)</span>
          <span className="px-2 py-0.5 rounded bg-stone-100 border border-stone-200 text-stone-700">தமிழ் (Tamil)</span>
          <span className="px-2 py-0.5 rounded bg-stone-100 border border-stone-200 text-stone-700">తెలుగు (Telugu)</span>
          <span className="px-2 py-0.5 rounded bg-stone-100 border border-stone-200 text-stone-700">English</span>
        </div>
      </section>

      {/* Sequential Journey Roadmap */}
      <section className="space-y-6">
        <div className="text-center max-w-2xl mx-auto space-y-2">
          <Badge variant="saffron">Sequential Workflow</Badge>
          <h2 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1C1917] font-['Outfit']">
            The KALPA Entrepreneurship Journey
          </h2>
          <p className="text-xs sm:text-sm text-[#57534E]">
            A step-by-step advisory pipeline. Only active stages are accessible to ensure structured data integrity.
          </p>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 pt-4">
          {sequentialWorkflow.map((stepItem, idx) => {
            if (stepItem.active) {
              return (
                <div
                  key={idx}
                  className="royal-card rounded-2xl p-6 border-2 border-orange-400/80 bg-white shadow-md relative overflow-hidden flex flex-col justify-between"
                >
                  <div className="absolute top-0 right-0 bg-orange-500 text-white text-[10px] font-bold px-3 py-1 rounded-bl-xl uppercase tracking-wider">
                    Current Stage
                  </div>

                  <div>
                    <div className="flex items-center gap-3 mb-3">
                      <span className="text-2xl font-black text-[#EA580C] font-['Outfit']">
                        {stepItem.step}
                      </span>
                      <Badge variant="saffron">{stepItem.badge}</Badge>
                    </div>

                    <CardTitle className="text-base text-[#1C1917] mb-2">
                      {stepItem.title}
                    </CardTitle>
                    <CardDescription className="text-xs text-[#57534E]">
                      {stepItem.desc}
                    </CardDescription>
                  </div>

                  <div className="mt-6 pt-4 border-t border-[#EAE3D5] flex items-center justify-between">
                    <span className="text-xs font-semibold text-[#EA580C]">Ready for Input</span>
                    <Link to={stepItem.link}>
                      <Button size="sm" icon={ArrowRight}>
                        Launch Step 1
                      </Button>
                    </Link>
                  </div>
                </div>
              );
            }

            return (
              <div
                key={idx}
                className="rounded-2xl p-6 border border-stone-200/80 bg-stone-50/70 opacity-80 flex flex-col justify-between"
              >
                <div>
                  <div className="flex items-center justify-between mb-3">
                    <span className="text-xl font-bold text-stone-400 font-['Outfit']">
                      {stepItem.step}
                    </span>
                    <span className="inline-flex items-center gap-1 text-[11px] px-2.5 py-0.5 rounded-full bg-stone-200/60 text-stone-600 font-medium">
                      <Lock className="w-3 h-3" />
                      Locked
                    </span>
                  </div>

                  <h3 className="text-sm font-semibold text-stone-700 mb-1.5">
                    {stepItem.title}
                  </h3>
                  <p className="text-xs text-stone-500 leading-relaxed">
                    {stepItem.desc}
                  </p>
                </div>

                <div className="mt-6 pt-3 border-t border-stone-200/60 flex items-center justify-between text-[11px] text-stone-400">
                  <span>Sequentially unlocked after Stage {parseInt(stepItem.step) - 1}</span>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* System Infrastructure Banner */}
      <section className="royal-panel rounded-2xl p-6 flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h3 className="text-xs font-bold uppercase tracking-wider text-[#1C1917] flex items-center gap-2">
            <ShieldCheck className="w-4 h-4 text-[#EA580C]" />
            Pipeline Architecture Status
          </h3>
          <p className="text-xs text-[#78716C] mt-0.5">
            Stage 1 Multilingual NLP & Sarvam Saaras STT Engine
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
