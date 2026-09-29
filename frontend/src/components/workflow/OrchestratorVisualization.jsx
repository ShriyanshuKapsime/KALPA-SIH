import React, { useRef } from 'react';
import { Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'motion/react';
import {
  Compass,
  Award,
  DollarSign,
  ShieldCheck,
  TrendingUp,
  FileText,
  CheckCircle2,
  Clock,
  Lock,
  ChevronRight,
  Check
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

function PinnedVisualizationCard({ comp, idx, status, isEven, getStageUrl }) {
  const cardRef = useRef(null);
  const { scrollYProgress } = useScroll({
    target: cardRef,
    offset: ['start 0.95', 'center 0.5', 'end 0.05']
  });

  const baseRotation = isEven ? 2.5 : -2.5;
  const opacity = useTransform(scrollYProgress, [0, 0.45, 0.55, 1], [0.65, 1, 1, 0.85]);
  const scale = useTransform(scrollYProgress, [0, 0.45, 0.55, 1], [0.96, 1, 1, 0.98]);
  const rotate = useTransform(
    scrollYProgress,
    [0, 0.5, 1],
    [status === 'active' || status === 'running' ? 0 : baseRotation, 0, isEven ? 1 : -1]
  );
  const y = useTransform(scrollYProgress, [0, 0.45], [20, 0]);

  const Icon = comp.icon;
  const isCompleted = status === 'completed';
  const isActive = status === 'active';
  const isRunning = status === 'running';
  const isLocked = status === 'locked';

  return (
    <div
      ref={cardRef}
      className={`flex w-full ${isEven ? 'lg:justify-end' : 'lg:justify-start'} relative items-center`}
    >
      {/* Center Timeline Milestone Node (Desktop) */}
      <div className="hidden lg:flex absolute left-1/2 top-1/2 -translate-x-1/2 -translate-y-1/2 z-30 pointer-events-none">
        <div
          className={`w-7 h-7 rounded-full flex items-center justify-center text-[11px] font-bold transition-all duration-500 shadow-xs ${
            isCompleted
              ? 'bg-[#006F5F] text-white'
              : isRunning
              ? 'bg-[#79563F] text-white ring-4 ring-[#79563F]/25 animate-pulse'
              : isActive
              ? 'bg-[#79563F] text-white ring-4 ring-[#79563F]/20'
              : 'bg-[#FAF2E3] border border-[#79563F]/30 text-[#79563F]/60'
          }`}
        >
          {isCompleted ? <Check className="w-3.5 h-3.5 stroke-[2.5]" /> : comp.num}
        </div>
      </div>

      <motion.div
        style={{
          opacity: isLocked ? 0.6 : opacity,
          scale,
          rotate: isRunning || isActive ? 0 : rotate,
          y
        }}
        whileHover={!isLocked ? { scale: 1.015, y: -4, rotate: 0, transition: { duration: 0.25 } } : {}}
        className={`w-full lg:w-[46%] relative rounded-3xl p-6 sm:p-8 transition-all duration-300 ${
          isRunning || isActive
            ? 'bg-[#F1E4CC] border-2 border-[#79563F] shadow-[0_12px_32px_-8px_rgba(121,86,63,0.22)] ring-4 ring-[#79563F]/15 z-20'
            : isCompleted
            ? 'bg-[#FAF2E3] border border-[#79563F]/25 shadow-[0_4px_20px_-4px_rgba(40,35,31,0.08)] hover:shadow-md'
            : 'bg-[#FAF2E3]/70 border border-[#79563F]/15 shadow-none cursor-not-allowed'
        }`}
      >
        <div
          className={`absolute -top-3 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full shadow-xs border border-[#FAF2E3] flex items-center justify-center z-20 pointer-events-none ${
            isRunning || isActive
              ? 'bg-gradient-to-br from-[#A2724D] to-[#79563F]'
              : isCompleted
              ? 'bg-gradient-to-br from-[#006F5F] to-[#004D40]'
              : 'bg-gradient-to-br from-[#BFA47D] to-[#8C7E72]'
          }`}
        >
          <div className="w-1.5 h-1.5 rounded-full bg-[#FAF2E3]/90 shadow-inner" />
        </div>

        <div className="flex flex-col justify-between h-full space-y-4">
          <div>
            <div className="flex items-center justify-between gap-2 mb-3.5">
              <span className="text-[11px] font-bold uppercase tracking-widest text-[#79563F] font-mono">
                {comp.cardLabel}
              </span>

              {isCompleted ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#006F5F] bg-[#006F5F]/10 px-2.5 py-0.5 rounded-full border border-[#006F5F]/20">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#006F5F]" />
                  {comp.completedText || 'Completed'}
                </span>
              ) : isRunning ? (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#79563F] bg-[#79563F]/15 px-2.5 py-0.5 rounded-full border border-[#79563F]/30 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-[#79563F] animate-ping" />
                  Running
                </span>
              ) : isActive ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#79563F] bg-[#79563F]/10 px-2.5 py-0.5 rounded-full border border-[#79563F]/25">
                  <Clock className="w-3.5 h-3.5 text-[#79563F]" />
                  Current Step
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[#79563F]/60 bg-[#FAF2E3]/60 px-2.5 py-0.5 rounded-full border border-[#79563F]/15">
                  <Lock className="w-3 h-3 text-[#79563F]/50" />
                  Locked
                </span>
              )}
            </div>

            <div className="flex items-start gap-3.5 mb-2.5">
              <div
                className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border ${
                  isCompleted
                    ? 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/20'
                    : isRunning || isActive
                    ? 'bg-[#79563F]/15 text-[#79563F] border-[#79563F]/30'
                    : 'bg-[#FAF2E3] text-[#79563F]/60 border-[#79563F]/15'
                }`}
              >
                <Icon className="w-5 h-5" />
              </div>
              <div>
                <h3 className="text-xl sm:text-2xl font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif] leading-tight">
                  {comp.title}
                </h3>
              </div>
            </div>

            <p className="text-xs sm:text-sm text-[#62584F] leading-relaxed">
              {comp.desc}
            </p>

            {comp.subPills && (
              <div className="mt-3.5 pt-3 border-t border-[#79563F]/15 space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]">
                  Feasibility Components:
                </span>
                <div className="flex flex-wrap items-center gap-1.5">
                  {comp.subPills.map((sub, sIdx) => (
                    <span
                      key={sIdx}
                      className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border flex items-center gap-1 ${
                        sub.isDone
                          ? 'bg-[#006F5F]/10 text-[#006F5F] border-[#006F5F]/20'
                          : isRunning || isActive
                          ? 'bg-[#79563F]/10 text-[#79563F] border-[#79563F]/20'
                          : 'bg-[#FAF2E3] text-[#79563F]/60 border-[#79563F]/15'
                      }`}
                    >
                      {sub.isDone && <Check className="w-2.5 h-2.5" />}
                      {sub.label}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          <div className="pt-3.5 border-t border-[#79563F]/15 flex items-center justify-between">
            <span className="text-[11px] text-[#79563F]/70 font-medium">
              {isCompleted
                ? 'Outputs validated'
                : isRunning
                ? comp.runningText || 'Analyzing...'
                : isActive
                ? 'Input parameters ready'
                : 'Awaiting upstream stages'}
            </span>

            {isCompleted || isActive ? (
              <Link
                to={getStageUrl(comp.path)}
                className="inline-flex items-center gap-1 text-xs font-bold text-[#79563F] hover:text-[#28231F] transition-colors group"
              >
                <span>{isCompleted ? 'View Analysis' : 'Open Engine'}</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            ) : (
              <span className="text-[11px] text-[#79563F]/50 font-medium flex items-center gap-1">
                <Lock className="w-3 h-3" /> Locked
              </span>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default function OrchestratorVisualization({ className = '' }) {
  const {
    sessionId,
    analysisId,
    completedStages = [],
    engineOutputs = {},
    isOrchestrating
  } = useWorkflow();

  const getStageUrl = (basePath) => {
    const params = new URLSearchParams();
    if (sessionId) params.set('session_id', sessionId);
    if (analysisId) params.set('analysis_id', analysisId);
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  const isStage5RawDone = completedStages.includes(5) || Boolean(engineOutputs?.market_intelligence);
  const isStage8RawDone = completedStages.includes(8) || Boolean(engineOutputs?.opportunity_evaluation);
  const isStage9RawDone = completedStages.includes(9) || Boolean(engineOutputs?.financial_planning);
  const isStage10RawDone = completedStages.includes(10) || Boolean(engineOutputs?.entrepreneur_profile);
  const isStage11RawDone = completedStages.includes(11) || Boolean(engineOutputs?.risk_analysis);
  const isStage12RawDone = completedStages.includes(12) || Boolean(engineOutputs?.feasibility_assessment);
  const isStage13RawDone = completedStages.includes(13) || Boolean(engineOutputs?.swot_analysis);
  const isStage14RawDone = completedStages.includes(14) || Boolean(engineOutputs?.dpr);

  const isStage1Completed = Boolean(isStage5RawDone);
  const isStage2Completed = isStage1Completed && Boolean(isStage8RawDone);
  const isStage3Completed = isStage2Completed && Boolean(isStage9RawDone);
  const isStage4Completed = isStage3Completed && Boolean(isStage12RawDone);
  const isStage5Completed = isStage4Completed && Boolean(isStage13RawDone);
  const isStage6Completed = isStage5Completed && Boolean(isStage14RawDone);

  const isStage10Done = isStage3Completed && isStage10RawDone;
  const isStage11Done = isStage3Completed && isStage11RawDone;
  const isStage12Done = isStage4Completed;

  const completedFlags = [
    isStage1Completed,
    isStage2Completed,
    isStage3Completed,
    isStage4Completed,
    isStage5Completed,
    isStage6Completed
  ];

  const currentActiveIndex = completedFlags.findIndex((done) => !done);

  const getStageStatus = (idx) => {
    if (completedFlags[idx]) {
      return 'completed';
    }
    if (idx === currentActiveIndex) {
      return isOrchestrating ? 'running' : 'active';
    }
    return 'locked';
  };

  const STAGES_DEF = [
    {
      id: 'market_intelligence',
      num: '01',
      pipelineLabel: 'Market Intel',
      cardLabel: '01 · MARKET INTELLIGENCE',
      title: 'Market Intelligence',
      icon: Compass,
      desc: 'Retrieve and analyze local market evidence including demand, competition, infrastructure and market access.',
      runningText: 'Analyzing local market evidence...',
      path: '/market-intelligence',
      subPills: null
    },
    {
      id: 'opportunity',
      num: '02',
      pipelineLabel: 'Opportunity',
      cardLabel: '02 · OPPORTUNITY EVALUATION',
      title: 'Opportunity Evaluation',
      icon: Award,
      desc: 'Evaluate market attractiveness, demand conditions and business suitability.',
      runningText: 'Evaluating market attractiveness...',
      path: '/opportunity-evaluation',
      subPills: null
    },
    {
      id: 'financial',
      num: '03',
      pipelineLabel: 'Finance',
      cardLabel: '03 · FINANCIAL PLANNING',
      title: 'Financial Planning',
      icon: DollarSign,
      desc: 'Calculate project costs, working capital, loan requirements, cash flow and repayment structure.',
      runningText: 'Structuring project costs & loans...',
      path: '/financial-planning',
      subPills: null
    },
    {
      id: 'feasibility',
      num: '04',
      pipelineLabel: 'Feasibility',
      cardLabel: '04 · FEASIBILITY',
      title: 'Feasibility',
      icon: ShieldCheck,
      desc: 'Synthesize market, financial, entrepreneur and risk factors into an explainable feasibility assessment.',
      runningText: 'Synthesizing profile, risk & feasibility...',
      path: '/feasibility',
      subPills: [
        { label: 'Entrepreneur Profile', isDone: isStage10Done },
        { label: 'Risk', isDone: isStage11Done },
        { label: 'Feasibility Synthesis', isDone: isStage12Done }
      ]
    },
    {
      id: 'swot',
      num: '05',
      pipelineLabel: 'SWOT',
      cardLabel: '05 · SWOT',
      title: 'SWOT',
      icon: TrendingUp,
      desc: 'Translate validated market, financial, entrepreneur and risk evidence into strategic strengths, weaknesses, opportunities and threats.',
      runningText: 'Interpreting strategic SWOT factors...',
      completedText: 'SWOT Complete',
      path: '/swot',
      subPills: null
    },
    {
      id: 'dpr',
      num: '06',
      pipelineLabel: 'DPR',
      cardLabel: '06 · DPR',
      title: 'DPR',
      icon: FileText,
      desc: 'Bring validated business, market and financial findings into a structured project report.',
      runningText: 'Generating structured bank-ready report...',
      completedText: 'DPR Generated',
      path: '/dpr/drafting',
      subPills: null
    }
  ];

  return (
    <div className={`relative max-w-4xl mx-auto py-8 ${className}`}>
      <div className="hidden lg:block absolute left-1/2 top-12 bottom-16 w-0.5 -translate-x-1/2 bg-[#79563F]/20 pointer-events-none" />

      <div className="space-y-16 sm:space-y-20 lg:space-y-24">
        {STAGES_DEF.map((comp, idx) => {
          const isEven = idx % 2 === 1;
          const status = getStageStatus(idx);

          return (
            <PinnedVisualizationCard
              key={comp.num}
              comp={comp}
              idx={idx}
              status={status}
              isEven={isEven}
              getStageUrl={getStageUrl}
            />
          );
        })}
      </div>
    </div>
  );
}
