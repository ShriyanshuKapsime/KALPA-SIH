import React, { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  Cpu,
  Sparkles,
  ArrowRight,
  CheckCircle2,
  Clock,
  Compass,
  Award,
  DollarSign,
  Layers,
  RefreshCw,
  ShieldCheck,
  TrendingUp,
  BarChart3,
  ExternalLink,
  ChevronRight,
  AlertCircle
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';

export default function OrchestratorVisualization({ onRunSuccess, className = '' }) {
  const navigate = useNavigate();
  const {
    sessionId,
    analysisId,
    businessName,
    businessId,
    completedStages,
    currentStage,
    engineOutputs,
    isOrchestrating,
    orchestrationProgress,
    workflowError,
    runOrchestratorPipeline
  } = useWorkflow();

  const [localRunning, setLocalRunning] = useState(false);
  const [activeStepIndex, setActiveStepIndex] = useState(null);

  const isStage5Done = completedStages?.includes(5) || Boolean(engineOutputs?.market_intelligence);
  const isStage8Done = completedStages?.includes(8) || Boolean(engineOutputs?.opportunity_evaluation);
  const isStage9Done = completedStages?.includes(9) || Boolean(engineOutputs?.financial_planning);
  const isStage10Done = completedStages?.includes(10) || Boolean(engineOutputs?.entrepreneur_profile);
  const isStage11Done = completedStages?.includes(11) || Boolean(engineOutputs?.risk_analysis);
  const isStage12Done = completedStages?.includes(12) || Boolean(engineOutputs?.feasibility_assessment);

  const engines = [
    {
      id: 'stage5',
      stageNum: 5,
      pillar: 'Discover',
      title: 'Market Intelligence Engine',
      icon: Compass,
      status: isStage5Done ? 'COMPLETED' : isOrchestrating ? 'EXECUTING' : 'PENDING',
      output: engineOutputs?.market_intelligence || (isStage5Done ? 'Demand Strong ✓' : null),
      metricLabel: 'Local Demand & Supply',
      path: '/market-intelligence',
      desc: 'Spatial Demographics, Catchment Density & MSME Benchmark Synthesis',
      highlightColor: 'from-amber-500/10 to-orange-500/5',
      borderColor: 'border-orange-200'
    },
    {
      id: 'stage8',
      stageNum: 8,
      pillar: 'Validate',
      title: 'Opportunity Evaluation Engine',
      icon: Award,
      status: isStage8Done ? 'COMPLETED' : isOrchestrating && isStage5Done ? 'EXECUTING' : 'PENDING',
      output: engineOutputs?.opportunity_evaluation || (isStage8Done ? '88% Opportunity ✓' : null),
      metricLabel: '6-Factor Synthesis Score',
      path: '/opportunity-evaluation',
      desc: 'Auditable Multi-Factor Opportunity Scoring & Constraint Validation',
      highlightColor: 'from-blue-500/10 to-indigo-500/5',
      borderColor: 'border-indigo-200'
    },
    {
      id: 'stage9',
      stageNum: 9,
      pillar: 'Finance',
      title: 'Financial Planning Engine',
      icon: DollarSign,
      status: isStage9Done ? 'COMPLETED' : isOrchestrating && isStage8Done ? 'EXECUTING' : 'PENDING',
      output: engineOutputs?.financial_planning || (isStage9Done ? '₹9L Financing Structure ✓' : null),
      metricLabel: 'Capital & Scheme Structuring',
      path: '/financial-planning',
      desc: 'CapEx/OpEx, 90% Loan Structuring, Annuity EMI & Scheme Eligibility Match',
      highlightColor: 'from-emerald-500/10 to-teal-500/5',
      borderColor: 'border-emerald-200'
    },
    {
      id: 'stage10',
      stageNum: 10,
      pillar: 'Founder',
      title: 'Entrepreneur Profile Engine',
      icon: BarChart3,
      status: isStage10Done ? 'COMPLETED' : isOrchestrating && isStage9Done ? 'EXECUTING' : 'PENDING',
      output: engineOutputs?.entrepreneur_profile || (isStage10Done ? 'Readiness Assessed ✓' : null),
      metricLabel: 'Skills & Readiness Audit',
      path: '/entrepreneur-profile',
      desc: 'Multi-Factor Capability Scoring, Experience Verification & Statutory Training Gaps',
      highlightColor: 'from-purple-500/10 to-violet-500/5',
      borderColor: 'border-purple-200'
    },
    {
      id: 'stage11',
      stageNum: 11,
      pillar: 'Resilience',
      title: 'Enterprise Risk Engine',
      icon: TrendingUp,
      status: isStage11Done ? 'COMPLETED' : isOrchestrating && isStage10Done ? 'EXECUTING' : 'PENDING',
      output: engineOutputs?.risk_analysis || (isStage11Done ? 'Risk Vectors Evaluated ✓' : null),
      metricLabel: '7-Vector Severity Assessment',
      path: '/risk-analysis',
      desc: 'Market, Climate, Regulatory, Financial, Liquidity & Execution Risk Synthesis',
      highlightColor: 'from-rose-500/10 to-pink-500/5',
      borderColor: 'border-rose-200'
    },
    {
      id: 'stage12',
      stageNum: 12,
      pillar: 'Viability',
      title: 'Feasibility Synthesis Engine',
      icon: ShieldCheck,
      status: isStage12Done ? 'COMPLETED' : isOrchestrating && isStage11Done ? 'EXECUTING' : 'PENDING',
      output: engineOutputs?.feasibility_assessment || (isStage12Done ? 'Feasibility Synthesized ✓' : null),
      metricLabel: 'Master Feasibility Matrix',
      path: '/feasibility',
      desc: '4-Pillar Mathematical Synthesis, Critical Go/No-Go Gates & Bankable Viability Decision',
      highlightColor: 'from-amber-500/15 to-emerald-500/10',
      borderColor: 'border-amber-300'
    }
  ];

  const handleExecute = async () => {
    setLocalRunning(true);
    try {
      await runOrchestratorPipeline(sessionId, analysisId);
      if (onRunSuccess) onRunSuccess();
    } catch (err) {
      console.error('Orchestration run failed:', err);
    } finally {
      setLocalRunning(false);
    }
  };

  const getStageUrl = (basePath) => {
    const params = new URLSearchParams();
    if (sessionId) params.set('session_id', sessionId);
    if (analysisId) params.set('analysis_id', analysisId);
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  return (
    <div className={`space-y-6 ${className}`}>
      {/* Main Orchestrator Control Card */}
      <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] shadow-sm relative overflow-hidden">
        <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
          <div className="space-y-2 max-w-2xl">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-orange-100 border border-orange-200 text-[#C2410C] text-xs font-bold shadow-2xs">
              <Cpu className="w-3.5 h-3.5 text-[#EA580C]" />
              <span>KALPA Orchestrator Agent Controller</span>
            </div>
            
            <h2 className="text-2xl sm:text-3xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
              Sequential Multi-Engine Execution
            </h2>
            
            <p className="text-xs sm:text-sm text-[#57534E] leading-relaxed">
              The Orchestrator Agent autonomously guides the entrepreneur journey. After Intake & Profile, it sequentially runs <strong className="text-[#1C1917]">Market Intelligence</strong>, <strong className="text-[#1C1917]">Opportunity Evaluation</strong>, and <strong className="text-[#1C1917]">Financial Planning</strong> to establish full enterprise viability.
            </p>
          </div>

          {/* Trigger Action */}
          <div className="flex flex-col items-start lg:items-end gap-3 shrink-0">
            <button
              onClick={handleExecute}
              disabled={isOrchestrating || localRunning}
              className="saffron-gradient-btn px-6 py-3.5 rounded-xl text-sm font-bold flex items-center gap-2.5 shadow-md hover:scale-[1.02] active:scale-[0.98] transition-all disabled:opacity-60 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${(isOrchestrating || localRunning) ? 'animate-spin' : ''}`} />
              <span>
                {isOrchestrating || localRunning
                  ? `Executing Engine Pipeline (${orchestrationProgress}%)...`
                  : isStage9Done
                  ? 'Re-Run Orchestrator Pipeline'
                  : 'Run Orchestrator Pipeline'}
              </span>
            </button>

            <span className="text-[11px] text-[#78716C] font-medium flex items-center gap-1.5">
              <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
              Deterministic Zero-LLM Math + Auditable Verification
            </span>
          </div>
        </div>

        {/* Live Progress Bar when running */}
        {(isOrchestrating || localRunning) && (
          <div className="mt-6 pt-5 border-t border-[#EAE3D5] space-y-2 animate-fadeIn">
            <div className="flex justify-between text-xs font-bold text-[#1C1917]">
              <span>Orchestrating Sequential Journey Pipeline...</span>
              <span className="text-[#EA580C]">{orchestrationProgress}%</span>
            </div>
            <div className="w-full bg-stone-100 rounded-full h-2.5 overflow-hidden border border-stone-200">
              <div
                className="bg-gradient-to-r from-[#EA580C] to-[#D97706] h-full transition-all duration-500 rounded-full"
                style={{ width: `${orchestrationProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Workflow Error Alert */}
        {workflowError && (
          <div className="mt-4 p-3.5 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
            <span>{workflowError}</span>
          </div>
        )}
      </div>

      {/* 6-Engine Output Visualizer Cards */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {engines.map((engine, idx) => {
          const Icon = engine.icon;
          const isDone = engine.status === 'COMPLETED';
          const isRunning = engine.status === 'EXECUTING';

          return (
            <div
              key={engine.id}
              className={`royal-card rounded-2xl p-6 flex flex-col justify-between relative overflow-hidden transition-all duration-300 border-2 ${
                isDone
                  ? 'border-emerald-400/80 bg-white shadow-sm'
                  : isRunning
                  ? 'border-[#EA580C] bg-orange-50/30 shadow-md ring-2 ring-orange-200'
                  : 'border-[#EAE3D5] bg-[#FAF7F2]/50 opacity-90'
              }`}
            >
              <div>
                {/* Header: Pillar Badge & Status */}
                <div className="flex items-center justify-between gap-2 mb-4">
                  <span className="text-[10px] font-bold uppercase tracking-wider px-2.5 py-0.5 rounded-full bg-stone-100 text-[#57534E] border border-stone-200">
                    Stage 0{engine.stageNum} &middot; {engine.pillar}
                  </span>

                  {isDone ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-emerald-700 bg-emerald-100 px-2.5 py-0.5 rounded-full border border-emerald-200">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      Executed
                    </span>
                  ) : isRunning ? (
                    <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#C2410C] bg-orange-100 px-2.5 py-0.5 rounded-full border border-orange-200 animate-pulse">
                      <RefreshCw className="w-3.5 h-3.5 text-[#EA580C] animate-spin" />
                      Running...
                    </span>
                  ) : (
                    <span className="inline-flex items-center gap-1 text-[11px] font-medium text-stone-500 bg-stone-100 px-2.5 py-0.5 rounded-full">
                      <Clock className="w-3 h-3" />
                      Ready to Run
                    </span>
                  )}
                </div>

                {/* Engine Title & Icon */}
                <div className="flex items-start gap-3 mb-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center shrink-0 ${
                    isDone
                      ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                      : isRunning
                      ? 'bg-orange-100 text-[#EA580C] border border-orange-200'
                      : 'bg-stone-100 text-stone-600'
                  }`}>
                    <Icon className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-[#1C1917] leading-tight font-['Outfit']">
                      {engine.title}
                    </h3>
                    <p className="text-xs text-[#78716C] mt-0.5">{engine.desc}</p>
                  </div>
                </div>

                {/* Output Highlight Badge (Prominently displays the required format) */}
                <div className="mt-4 p-3.5 rounded-xl bg-[#FAF7F2] border border-[#EAE3D5] space-y-1">
                  <div className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                    Engine Output Result
                  </div>
                  {engine.output ? (
                    <div className="text-sm font-extrabold text-[#1C1917] flex items-center gap-1.5">
                      <span className="text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded-md border border-emerald-200">
                        {engine.output}
                      </span>
                    </div>
                  ) : (
                    <div className="text-xs text-stone-400 italic">
                      Awaiting orchestrator trigger...
                    </div>
                  )}
                </div>
              </div>

              {/* Card Footer: Drilldown Link */}
              <div className="mt-6 pt-4 border-t border-[#EAE3D5] flex items-center justify-between">
                <span className="text-[11px] text-[#78716C] font-medium">
                  {isDone ? 'Full analytics available' : 'Input profiles ready'}
                </span>
                <Link
                  to={getStageUrl(engine.path)}
                  className="inline-flex items-center gap-1 text-xs font-bold text-[#C2410C] hover:text-[#EA580C] transition-colors"
                >
                  <span>Inspect Details</span>
                  <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}
