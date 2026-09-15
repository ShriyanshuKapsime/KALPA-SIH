import React from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  Lock,
  Sparkles,
  ArrowRight,
  TrendingUp,
  Award,
  DollarSign,
  ShieldAlert,
  Bot,
  Layers,
  HelpCircle,
  Clock,
  Compass,
  FileCheck2,
  UserCheck
} from 'lucide-react';
import { useWorkflow, JOURNEY_PILLARS } from '../../context/WorkflowContext';

export default function WorkflowTimeline({ currentPillar = 'understand', className = '', compact = false }) {
  const navigate = useNavigate();
  const {
    sessionId,
    analysisId,
    completedStages,
    currentStage,
    availableStages,
    lockedStages,
    journeyStatus,
    engineOutputs
  } = useWorkflow();

  const STAGES_CONFIG = [
    {
      stageNum: 1,
      name: 'Intake',
      pillar: 'understand',
      path: '/intake',
      icon: UserCheck,
      desc: 'Vernacular Voice & Text Input'
    },
    {
      stageNum: 2,
      name: 'Classification',
      pillar: 'understand',
      path: '/classification',
      icon: Layers,
      desc: 'Ontology & 5-Digit NIC Mapping'
    },
    {
      stageNum: 3,
      name: 'Profile',
      pillar: 'understand',
      path: '/profile',
      icon: FileCheck2,
      desc: 'Canonical Business Profile'
    },
    {
      stageNum: 5,
      name: 'Market Intel',
      pillar: 'discover',
      path: '/market-intelligence',
      icon: Compass,
      desc: 'Spatial Demographics & Supply',
      output: engineOutputs?.market_intelligence || (completedStages?.includes(5) ? 'Demand Strong ✓' : null)
    },
    {
      stageNum: 8,
      name: 'Opportunity',
      pillar: 'validate',
      path: '/opportunity-evaluation',
      icon: Award,
      desc: '6-Factor Opportunity Score',
      output: engineOutputs?.opportunity_evaluation || (completedStages?.includes(8) ? '88% Opportunity ✓' : null)
    },
    {
      stageNum: 9,
      name: 'Financial Plan',
      pillar: 'finance',
      path: '/financial-planning',
      icon: DollarSign,
      desc: 'Project Cost, Loan & Scheme Match',
      output: engineOutputs?.financial_planning || (completedStages?.includes(9) ? '₹9L Financing Structure ✓' : null)
    },
    {
      stageNum: 10,
      name: 'Feasibility Prep',
      pillar: 'prepare',
      path: '/feasibility',
      icon: ShieldAlert,
      desc: 'Readiness & 7-Vector Risk Matrix',
      output: engineOutputs?.entrepreneur_profile || (completedStages?.includes(10) ? 'Readiness & Risk ✓' : null)
    },
    {
      stageNum: 12,
      name: 'Final Feasibility',
      pillar: 'prepare',
      locked: true,
      icon: FileCheck2,
      desc: 'Survivability & Bankability Scoring'
    },
    {
      stageNum: 14,
      name: 'AI Advisor & Growth',
      pillar: 'grow',
      locked: true,
      icon: Bot,
      desc: 'Personal Assistant & Monitoring'
    }
  ];

  // Compute overall active progress percentage (stages 1, 2, 3, 5, 8, 9, 10, 11)
  const coreStages = [1, 2, 3, 5, 8, 9, 10, 11];
  const completedCount = coreStages.filter(s => completedStages?.includes(s)).length;
  const progressPct = Math.round((completedCount / coreStages.length) * 100);

  const getStageUrl = (basePath) => {
    if (!basePath) return '#';
    const params = new URLSearchParams();
    if (sessionId) params.set('session_id', sessionId);
    if (analysisId) params.set('analysis_id', analysisId);
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  return (
    <div className={`royal-panel rounded-2xl p-5 sm:p-6 border border-[#EAE3D5] shadow-xs relative overflow-hidden ${className}`}>
      {/* Top Banner: Journey Status & Progress Bar */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-5 border-b border-[#EAE3D5]/80">
        <div className="space-y-1">
          <div className="flex items-center gap-2">
            <span className="w-2 h-2 rounded-full bg-[#EA580C] animate-pulse" />
            <span className="text-xs font-bold uppercase tracking-wider text-[#C2410C]">
              Orchestrator Workflow Timeline
            </span>
            <span className="text-[10px] font-semibold px-2 py-0.5 rounded-full bg-orange-100 text-[#C2410C] border border-orange-200">
              Bharat Entrepreneurship Journey
            </span>
          </div>
          <h2 className="text-base sm:text-lg font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
            Sequential Livelihood Pipeline
          </h2>
        </div>

        {/* Journey Progress Meter */}
        <div className="flex items-center gap-4 bg-white px-4 py-2 rounded-xl border border-[#EAE3D5] shadow-2xs">
          <div className="text-right">
            <div className="text-[10px] uppercase font-bold text-[#78716C]">Core Journey Progress</div>
            <div className="text-sm font-extrabold text-[#EA580C]">{completedCount} of 6 Stages ({progressPct}%)</div>
          </div>
          <div className="w-20 bg-stone-100 rounded-full h-2.5 overflow-hidden border border-stone-200">
            <div
              className="bg-gradient-to-r from-[#EA580C] to-[#D97706] h-full transition-all duration-700 rounded-full"
              style={{ width: `${progressPct}%` }}
            />
          </div>
        </div>
      </div>

      {/* Horizontal Interactive Journey Steps */}
      <div className="pt-6 overflow-x-auto pb-2">
        <div className="min-w-[720px] flex items-start justify-between relative">
          
          {/* Connector Line behind nodes */}
          <div className="absolute top-5 left-6 right-6 h-0.5 bg-stone-200 -z-0" />
          <div
            className="absolute top-5 left-6 h-0.5 bg-gradient-to-r from-emerald-500 via-[#EA580C] to-[#D97706] transition-all duration-700 -z-0"
            style={{ width: `${Math.min(100, Math.max(0, (completedCount / (coreStages.length - 1)) * 90))}%` }}
          />

          {STAGES_CONFIG.map((stage, idx) => {
            const Icon = stage.icon;
            const isCompleted = completedStages?.includes(stage.stageNum);
            const isCurrent = currentStage === stage.stageNum || (!isCompleted && idx === 0);
            const isLocked = stage.locked || (!isCompleted && !isCurrent && !completedStages?.includes(stage.stageNum - 1));

            return (
              <div key={stage.stageNum} className="flex flex-col items-center text-center relative z-10 w-24 group">
                {/* Node Circle */}
                {isCompleted ? (
                  <Link
                    to={getStageUrl(stage.path)}
                    className="w-10 h-10 rounded-full bg-emerald-500 text-white flex items-center justify-center shadow-md shadow-emerald-500/20 hover:scale-110 transition-transform cursor-pointer border-2 border-white ring-2 ring-emerald-300"
                    title={`Completed: ${stage.name} - Click to review`}
                  >
                    <CheckCircle2 className="w-5 h-5" />
                  </Link>
                ) : isCurrent ? (
                  <Link
                    to={getStageUrl(stage.path)}
                    className="w-10 h-10 rounded-full bg-[#EA580C] text-white flex items-center justify-center shadow-lg shadow-orange-500/30 hover:scale-110 transition-transform cursor-pointer border-2 border-white ring-4 ring-orange-200 animate-pulse"
                    title={`Current Active Stage: ${stage.name}`}
                  >
                    <Icon className="w-5 h-5" />
                  </Link>
                ) : isLocked ? (
                  <div
                    className="w-10 h-10 rounded-full bg-stone-100 text-stone-400 flex items-center justify-center border-2 border-stone-200 cursor-not-allowed select-none"
                    title={stage.locked ? 'Locked Future Milestone' : 'Complete previous stages to unlock'}
                  >
                    <Lock className="w-4 h-4" />
                  </div>
                ) : (
                  <Link
                    to={getStageUrl(stage.path)}
                    className="w-10 h-10 rounded-full bg-white text-stone-700 flex items-center justify-center border-2 border-stone-300 shadow-xs hover:border-[#EA580C] hover:text-[#EA580C] transition-all cursor-pointer"
                    title={`Available: ${stage.name}`}
                  >
                    <Icon className="w-4 h-4" />
                  </Link>
                )}

                {/* Stage Title & Pillar */}
                <div className="mt-2 space-y-0.5">
                  <span className="text-[9px] uppercase font-bold text-[#78716C] tracking-wider block">
                    {stage.pillar}
                  </span>
                  <p className={`text-xs font-bold leading-tight ${isCurrent ? 'text-[#EA580C]' : isCompleted ? 'text-[#1C1917]' : 'text-stone-500'}`}>
                    {stage.name}
                  </p>

                  {/* Output summary badge if available */}
                  {stage.output && (
                    <span className="inline-block mt-1 text-[9px] font-bold px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-700 border border-emerald-200 shadow-2xs">
                      {stage.output}
                    </span>
                  )}

                  {isLocked && (
                    <span className="inline-block text-[9px] font-medium text-stone-400">
                      Locked
                    </span>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Bottom Quick Context & Stage Handoff */}
      <div className="mt-4 pt-3 border-t border-[#EAE3D5]/80 flex flex-wrap items-center justify-between gap-3 text-xs text-[#78716C]">
        <div className="flex items-center gap-4">
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-emerald-500 inline-block" /> Completed
          </span>
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-[#EA580C] inline-block animate-pulse" /> Active Stage
          </span>
          <span className="flex items-center gap-1.5 font-medium">
            <span className="w-2.5 h-2.5 rounded-full bg-stone-300 inline-block" /> Locked Milestone
          </span>
        </div>

        <Link
          to="/journey"
          className="inline-flex items-center gap-1 font-bold text-[#C2410C] hover:text-[#EA580C] transition-colors"
        >
          <span>View Orchestrator Journey Hub</span>
          <ArrowRight className="w-3.5 h-3.5" />
        </Link>
      </div>
    </div>
  );
}
