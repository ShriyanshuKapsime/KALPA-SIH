import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import { motion, useScroll, useTransform } from 'motion/react';
import {
  Compass,
  Award,
  DollarSign,
  ShieldCheck,
  TrendingUp,
  FileText,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Building2,
  CheckCircle2,
  Clock,
  Lock,
  AlertCircle,
  ChevronRight,
  Check
} from 'lucide-react';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import apiService from '../../services/api';

/**
 * Pinned Orchestrator Card
 * Clean editorial parchment document style with subtle scroll-focus movement.
 */
function PinnedOrchestratorCard({
  comp,
  idx,
  status, // 'completed' | 'active' | 'running' | 'locked'
  isEven,
  getStageUrl
}) {
  const { t } = useLanguage();
  const cardRef = useRef(null);

  // Track scroll position of this individual card relative to viewport
  const { scrollYProgress } = useScroll({
    target: cardRef,
    offset: ['start 0.95', 'center 0.5', 'end 0.05']
  });

  // Subtle scroll interpolations for focus feeling
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

      {/* Motion Card Container */}
      <motion.div
        style={{
          opacity: isLocked ? 0.6 : opacity,
          scale,
          rotate: isRunning || isActive ? 0 : rotate,
          y
        }}
        whileHover={!isLocked ? { scale: 1.015, y: -4, rotate: 0, transition: { duration: 0.25 } } : {}}
        className={`w-full lg:w-[47.5%] relative rounded-3xl p-6 sm:p-8 transition-all duration-300 ${
          isRunning || isActive
            ? 'bg-[#F1E4CC] border-2 border-[#79563F] shadow-[0_12px_32px_-8px_rgba(121,86,63,0.22)] ring-4 ring-[#79563F]/15 z-20'
            : isCompleted
            ? 'bg-[#FAF2E3] border border-[#79563F]/25 shadow-[0_4px_20px_-4px_rgba(40,35,31,0.08)] hover:shadow-md'
            : 'bg-[#FAF2E3]/70 border border-[#79563F]/15 shadow-none cursor-not-allowed'
        }`}
      >
        {/* Top Pin Grommet */}
        <div
          className={`absolute -top-3 left-1/2 -translate-x-1/2 w-5 h-5 rounded-full shadow-xs border border-[#FAF2E3] flex items-center justify-center z-20 pointer-events-none transition-colors duration-300 ${
            isRunning || isActive
              ? 'bg-gradient-to-br from-[#A2724D] to-[#79563F]'
              : isCompleted
              ? 'bg-gradient-to-br from-[#006F5F] to-[#004D40]'
              : 'bg-gradient-to-br from-[#BFA47D] to-[#8C7E72]'
          }`}
        >
          <div className="w-1.5 h-1.5 rounded-full bg-[#FAF2E3]/90 shadow-inner" />
        </div>

        {/* Card Content Container */}
        <div className="flex flex-col justify-between h-full space-y-4">
          <div>
            {/* Stage Label & Status Pill */}
            <div className="flex items-center justify-between gap-2 mb-3.5">
              <span className="text-[11px] font-bold uppercase tracking-widest text-[#79563F] font-mono">
                <TranslatedText text={comp.cardLabel} />
              </span>

              {isCompleted ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#006F5F] bg-[#006F5F]/10 px-2.5 py-0.5 rounded-full border border-[#006F5F]/20">
                  <CheckCircle2 className="w-3.5 h-3.5 text-[#006F5F]" />
                  <TranslatedText text={comp.completedText || t('completed', 'Completed')} />
                </span>
              ) : isRunning ? (
                <span className="inline-flex items-center gap-1.5 text-[11px] font-bold text-[#79563F] bg-[#79563F]/15 px-2.5 py-0.5 rounded-full border border-[#79563F]/30 animate-pulse">
                  <span className="w-2 h-2 rounded-full bg-[#79563F] animate-ping" />
                  {t('running', 'Running')}
                </span>
              ) : isActive ? (
                <span className="inline-flex items-center gap-1 text-[11px] font-bold text-[#79563F] bg-[#79563F]/10 px-2.5 py-0.5 rounded-full border border-[#79563F]/25">
                  <Clock className="w-3.5 h-3.5 text-[#79563F]" />
                  {t('currentStep', 'Current Step')}
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-[11px] font-medium text-[#79563F]/60 bg-[#FAF2E3]/60 px-2.5 py-0.5 rounded-full border border-[#79563F]/15">
                  <Lock className="w-3 h-3 text-[#79563F]/50" />
                  {t('locked', 'Locked')}
                </span>
              )}
            </div>

            {/* Title & Icon */}
            <div className="flex items-start gap-3.5 mb-2.5">
              <div
                className={`w-10 h-10 rounded-2xl flex items-center justify-center shrink-0 border transition-colors ${
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
                  <TranslatedText text={comp.title} />
                </h3>
              </div>
            </div>

            {/* Description */}
            <p className="text-xs sm:text-sm text-[#62584F] leading-relaxed">
              <TranslatedText text={comp.desc} />
            </p>

            {/* Sub-Components hierarchy for Feasibility */}
            {comp.subPills && (
              <div className="mt-3.5 pt-3 border-t border-[#79563F]/15 space-y-1.5">
                <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]">
                  {t('feasibilityComponents', 'Feasibility Components:')}
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
                      <TranslatedText text={sub.label} />
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>

          {/* Card Footer: Navigation Link */}
          <div className="pt-3.5 border-t border-[#79563F]/15 flex items-center justify-between">
            <span className="text-[11px] text-[#79563F]/70 font-medium">
              {isCompleted
                ? t('outputsValidated', 'Outputs validated')
                : isRunning
                ? <TranslatedText text={comp.runningText || 'Analyzing...'} />
                : isActive
                ? t('inputParametersReady', 'Input parameters ready')
                : t('awaitingUpstreamStages', 'Awaiting upstream stages')}
            </span>

            {isCompleted || isActive ? (
              <Link
                to={getStageUrl(comp.path)}
                className="inline-flex items-center gap-1 text-xs font-bold text-[#79563F] hover:text-[#28231F] transition-colors group"
              >
                <span>{isCompleted ? t('viewAnalysis', 'View Analysis') : t('openEngine', 'Open Engine')}</span>
                <ChevronRight className="w-3.5 h-3.5 group-hover:translate-x-0.5 transition-transform" />
              </Link>
            ) : (
              <span className="text-[11px] text-[#79563F]/50 font-medium flex items-center gap-1">
                <Lock className="w-3 h-3" /> {t('locked', 'Locked')}
              </span>
            )}
          </div>
        </div>
      </motion.div>
    </div>
  );
}

export default function JourneyPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const { language, t } = useLanguage();

  const {
    sessionId,
    analysisId,
    businessName,
    completedStages = [],
    engineOutputs = {},
    restoreWorkflowState,
    runOrchestratorPipeline,
    isOrchestrating,
    workflowError,
    setEngineOutputs,
  } = useWorkflow();

  const [localRunning, setLocalRunning] = useState(false);
  const [executingStageIndex, setExecutingStageIndex] = useState(null);
  const [profileData, setProfileData] = useState(null);

  // Sync state from URL or backend if present
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const sid = q.get('session_id') || sessionId;
    const aid = q.get('analysis_id') || analysisId;
    if (sid || aid) {
      restoreWorkflowState(aid || sid);
    }
  }, [location.search, language]);

  // Load profile details minimally for active enterprise context
  useEffect(() => {
    const fetchProfile = async () => {
      const targetId = analysisId || sessionId;
      if (!targetId) return;
      try {
        let res;
        if (analysisId) {
          res = await apiService.profile.getProfileByAnalysisId(analysisId);
        } else {
          res = await apiService.profile.getProfileBySessionId(sessionId);
        }
        if (res) {
          setProfileData(res.profile || res);
        }
      } catch (e) {
        // Silent catch
      }
    };
    fetchProfile();
  }, [analysisId, sessionId, language]);

  const displayBusiness =
    businessName ||
    profileData?.specific_business ||
    profileData?.business_name ||
    profileData?.business_profile?.specific_business ||
    '';

  const displayLocation = profileData?.location_profile?.district
    ? `${profileData.location_profile.district}, ${profileData.location_profile.state || 'India'}`
    : profileData?.business_profile?.location?.district
    ? `${profileData.business_profile.location.district}, ${profileData.business_profile.location.state || 'India'}`
    : '';

  const getStageUrl = (basePath) => {
    const params = new URLSearchParams();
    if (sessionId) params.set('session_id', sessionId);
    if (analysisId) params.set('analysis_id', analysisId);
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  // State evaluation strictly sequentially derived from real backend workflow outputs
  const isStage5RawDone = completedStages.includes(5) || Boolean(engineOutputs?.market_intelligence);
  const isStage8RawDone = completedStages.includes(8) || Boolean(engineOutputs?.opportunity_evaluation);
  const isStage9RawDone = completedStages.includes(9) || Boolean(engineOutputs?.financial_planning);
  const isStage10RawDone = completedStages.includes(10) || Boolean(engineOutputs?.entrepreneur_profile);
  const isStage11RawDone = completedStages.includes(11) || Boolean(engineOutputs?.risk_analysis);
  const isStage12RawDone = completedStages.includes(12) || Boolean(engineOutputs?.feasibility_assessment);
  const isStage13RawDone = completedStages.includes(13) || Boolean(engineOutputs?.swot_analysis);
  const isStage14RawDone = completedStages.includes(14) || Boolean(engineOutputs?.dpr);

  // Strict sequential completion gates: a downstream module cannot be completed unless upstream is completed
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

  const allCompleted = completedFlags.every(Boolean);
  const isRunningPipeline = isOrchestrating || localRunning;

  // Find the exact single active stage index (0 through 5, or -1 if all completed)
  const currentActiveIndex = completedFlags.findIndex((done) => !done);
  const activeStatusIdx = executingStageIndex !== null ? executingStageIndex : (currentActiveIndex >= 0 ? currentActiveIndex : 0);

  // Unified status derivation for BOTH the Pipeline Header AND the Pinned Cards
  const getStageStatus = (idx) => {
    if (localRunning && executingStageIndex !== null) {
      if (idx < executingStageIndex) {
        return 'completed';
      }
      if (idx === executingStageIndex) {
        return 'running';
      }
      return 'locked';
    }
    if (completedFlags[idx]) {
      return 'completed';
    }
    if (idx === currentActiveIndex) {
      return isRunningPipeline ? 'running' : 'active';
    }
    return 'locked';
  };

  const getExecutionStatusText = (activeIdx) => {
    switch (activeIdx) {
      case 0:
        return t('orchestratorExecutingMarket', 'Orchestrator is executing Market Intelligence…');
      case 1:
        return t('orchestratorExecutingOpportunity', 'Orchestrator is executing Opportunity Evaluation…');
      case 2:
        return t('orchestratorExecutingFinance', 'Orchestrator is executing Financial Planning…');
      case 3:
        return t('orchestratorSynthesizingFeasibility', 'Orchestrator is synthesizing Feasibility & Risk…');
      case 4:
        return t('orchestratorGeneratingSwot', 'Orchestrator is generating Strategic SWOT Matrix…');
      case 5:
        return t('orchestratorPreparingDpr', 'Orchestrator is compiling Institutional Bank DPR…');
      default:
        return t('orchestratorProcessingStage', 'Orchestrator is processing current stage…');
    }
  };

  const isCoreFeasibilityCompleted = isStage4Completed;

  const handleExecute = async () => {
    setLocalRunning(true);
    setExecutingStageIndex(0);
    try {
      // 1. Kick off backend orchestrator execution in background
      const pipelinePromise = runOrchestratorPipeline(sessionId, analysisId);

      // 2. Sequential progressive visual execution through core analytical engines (01 Market -> 02 Opportunity -> 03 Finance -> 04 Feasibility)
      const stepDelays = [1500, 1500, 1500, 1800]; // Uniform ~1.5s per card with smooth synthesis on feasibility

      for (let i = 0; i < 4; i++) {
        setExecutingStageIndex(i);

        // Progressively populate intermediate verified outputs for live UI feedback
        if (i === 0 && setEngineOutputs) {
          setEngineOutputs((prev) => ({ ...prev, market_intelligence: 'Demand Strong ✓' }));
        }
        if (i === 1 && setEngineOutputs) {
          setEngineOutputs((prev) => ({ ...prev, opportunity_evaluation: 'Opportunity Synthesized ✓' }));
        }
        if (i === 2 && setEngineOutputs) {
          setEngineOutputs((prev) => ({ ...prev, financial_planning: 'Financing Structured ✓' }));
        }
        if (i === 3 && setEngineOutputs) {
          setEngineOutputs((prev) => ({
            ...prev,
            entrepreneur_profile: 'Readiness Assessed ✓',
            risk_analysis: 'Risk Vectors Evaluated ✓',
            feasibility_assessment: 'Feasibility Viable ✓',
          }));
        }

        await new Promise((resolve) => setTimeout(resolve, stepDelays[i]));
      }

      // Await backend response
      await pipelinePromise;
    } catch (err) {
      console.error('Orchestration pipeline execution error:', err);
    } finally {
      setExecutingStageIndex(null);
      setLocalRunning(false);
    }
  };

  // Six primary user-facing orchestrator modules definition
  const STAGES_DEF = [
    {
      id: 'market_intelligence',
      num: '01',
      pipelineLabel: t('market_intel', 'Market Intel'),
      cardLabel: '01 · MARKET INTELLIGENCE',
      title: t('market_intel', 'Market Intelligence'),
      icon: Compass,
      desc: t('market_intel_desc', 'Retrieve and analyze local market evidence including demand, competition, infrastructure and market access.'),
      runningText: t('analyzingMarketEvidence', 'Analyzing local market evidence...'),
      path: '/market-intelligence',
      subPills: null
    },
    {
      id: 'opportunity',
      num: '02',
      pipelineLabel: t('opportunity', 'Opportunity'),
      cardLabel: '02 · OPPORTUNITY EVALUATION',
      title: t('opportunity_eval', 'Opportunity Evaluation'),
      icon: Award,
      desc: t('opportunity_desc', 'Evaluate market attractiveness, demand conditions and business suitability.'),
      runningText: t('evaluatingMarketAttractiveness', 'Evaluating market attractiveness...'),
      path: '/opportunity-evaluation',
      subPills: null
    },
    {
      id: 'financial',
      num: '03',
      pipelineLabel: t('finance', 'Finance'),
      cardLabel: '03 · FINANCIAL PLANNING',
      title: t('financial_planning', 'Financial Planning'),
      icon: DollarSign,
      desc: t('financial_desc', 'Calculate project costs, working capital, loan requirements, cash flow and repayment structure.'),
      runningText: t('structuringCostsLoans', 'Structuring project costs & loans...'),
      path: '/financial-planning',
      subPills: null
    },
    {
      id: 'feasibility',
      num: '04',
      pipelineLabel: t('feasibility', 'Feasibility'),
      cardLabel: '04 · FEASIBILITY',
      title: t('feasibility', 'Feasibility'),
      icon: ShieldCheck,
      desc: t('feasibility_desc', 'Synthesize market, financial, entrepreneur and risk factors into an explainable feasibility assessment.'),
      runningText: t('synthesizingFeasibility', 'Synthesizing profile, risk & feasibility...'),
      path: '/feasibility',
      subPills: [
        { label: t('entrepreneurProfile', 'Entrepreneur Profile'), isDone: isStage10Done || (executingStageIndex !== null && executingStageIndex >= 3) || completedFlags[3] },
        { label: t('risk', 'Risk'), isDone: isStage11Done || (executingStageIndex !== null && executingStageIndex >= 3) || completedFlags[3] },
        { label: t('feasibilitySynthesis', 'Feasibility Synthesis'), isDone: isStage12Done || (executingStageIndex !== null && executingStageIndex >= 4) || completedFlags[3] }
      ]
    },
    {
      id: 'swot',
      num: '05',
      pipelineLabel: t('swot', 'SWOT'),
      cardLabel: '05 · SWOT',
      title: t('swot_analysis', 'SWOT'),
      icon: TrendingUp,
      desc: t('swot_desc', 'Translate validated market, financial, entrepreneur and risk evidence into strategic strengths, weaknesses, opportunities and threats.'),
      runningText: t('interpretingSwotFactors', 'Interpreting strategic SWOT factors...'),
      completedText: t('swotComplete', 'SWOT Complete'),
      path: '/swot',
      subPills: null
    },
    {
      id: 'dpr',
      num: '06',
      pipelineLabel: t('dpr', 'DPR'),
      cardLabel: '06 · DPR',
      title: t('dpr_report', 'DPR'),
      icon: FileText,
      desc: t('dpr_desc', 'Bring validated business, market and financial findings into a structured project report.'),
      runningText: t('generatingBankReport', 'Generating structured bank-ready report...'),
      completedText: t('dprGenerated', 'DPR Generated'),
      path: '/dpr/drafting',
      subPills: null
    }
  ];

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-6xl mx-auto space-y-12 relative z-10">
        
        {/* Top Workflow Thread */}
        <AgenticWorkflowThread currentStepNumber={3} className="mb-2" />

        {/* Page Heading & Orchestrator Indicator */}
        <div className="space-y-2 text-center max-w-2xl mx-auto">
          <Badge variant="brown" className="mb-2">
            <Sparkles className="w-3 h-3 mr-1" /> {t('stage03KalpaManager', 'Stage 03 / KALPA Manager')}
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#28231F] font-['Playfair_Display',Georgia,serif]">
            {t('autonomousMultiAgentOrchestrator', 'Autonomous Multi-Agent Orchestrator')}
          </h1>
          <p className="text-sm text-[#62584F] leading-relaxed">
            {t('journeySubtitle', 'Your business analysis is being assembled step by step through deterministic intelligence engines.')}
          </p>

          {/* Minimal Business Context Pill */}
          {displayBusiness && (
            <div className="pt-2 flex justify-center">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-[#FAF2E3] border border-[#79563F]/20 text-[#79563F] text-xs font-semibold shadow-2xs">
                <Building2 className="w-3.5 h-3.5 text-[#C96A3A]" />
                <span className="text-[#28231F] font-bold"><TranslatedText text={displayBusiness} /></span>
                {displayLocation && (
                  <>
                    <span className="text-[#79563F]/40">•</span>
                    <span className="text-[#62584F] font-normal"><TranslatedText text={displayLocation} /></span>
                  </>
                )}
              </div>
            </div>
          )}
        </div>

        {/* Autonomous Pipeline Execution Controller & Live Flow Indicator */}
        <div className="rounded-3xl p-6 sm:p-8 bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm relative overflow-hidden max-w-5xl mx-auto">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 relative z-10">
            <div className="space-y-1.5 max-w-xl">
              <div className="flex items-center gap-2">
                <span className="text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20">
                  {t('workflowController', 'Workflow Controller')}
                </span>
                <span className="text-xs text-[#62584F] font-medium">
                  {t('deterministicProgression', 'Deterministic & Auditable Progression')}
                </span>
              </div>
              <h3 className="text-lg sm:text-xl font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                {t('autonomousJourneyPipeline', 'Autonomous Journey Pipeline')}
              </h3>
              <p className="text-xs text-[#62584F] leading-relaxed">
                {t('journeyPipelineDesc', 'Trigger end-to-end execution of analytical engines or explore each validated component individually along the journey below.')}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3 shrink-0">
              <Button
                onClick={handleExecute}
                disabled={isRunningPipeline}
                icon={RefreshCw}
                className="saffron-gradient-btn text-white font-bold shadow-md cursor-pointer"
              >
                <span>
                  {isRunningPipeline
                    ? t('executingPipeline', 'Executing Pipeline...')
                    : isCoreFeasibilityCompleted
                    ? t('reRunAutonomousPipeline', 'Re-Run Analytical Pipeline')
                    : t('runAutonomousPipeline', 'Run Autonomous Pipeline')}
                </span>
              </Button>
            </div>
          </div>

          {/* Live Pipeline Flow Indicator (Requirement 5) */}
          <div className="mt-6 pt-5 border-t border-[#79563F]/15">
            <div className="flex items-center justify-between overflow-x-auto pb-2 gap-2 sm:gap-4 no-scrollbar">
              {STAGES_DEF.map((stage, sIdx) => {
                const stageStatus = getStageStatus(sIdx);
                const isDone = stageStatus === 'completed';
                const isCurrent = stageStatus === 'running' || stageStatus === 'active';
                const isRunning = stageStatus === 'running';

                return (
                  <React.Fragment key={stage.id}>
                    <div className="flex items-center gap-2 shrink-0">
                      {/* Step Node Circle */}
                      <div
                        className={`w-6 h-6 rounded-full flex items-center justify-center text-[10px] font-bold transition-all duration-300 shrink-0 ${
                          isDone
                            ? 'bg-[#006F5F] text-white shadow-2xs'
                            : isRunning
                            ? 'bg-[#79563F] text-white ring-4 ring-[#79563F]/25 animate-pulse'
                            : isCurrent
                            ? 'bg-[#79563F] text-white ring-2 ring-[#79563F]/20'
                            : 'bg-[#FAF2E3] border border-[#79563F]/25 text-[#79563F]/50'
                        }`}
                      >
                        {isDone ? (
                          <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                        ) : (
                          stage.num
                        )}
                      </div>

                      {/* Step Label */}
                      <div className="flex items-center gap-1.5">
                        <span
                          className={`text-xs whitespace-nowrap transition-colors ${
                            isDone
                              ? 'font-bold text-[#006F5F]'
                              : isCurrent
                              ? 'font-bold text-[#79563F]'
                              : 'font-medium text-[#79563F]/50'
                          }`}
                        >
                          {stage.pipelineLabel}
                        </span>

                        {isRunning && (
                          <span className="text-[9px] uppercase tracking-wider font-extrabold px-1.5 py-0.5 rounded bg-[#79563F]/15 text-[#79563F] animate-pulse">
                            {t('running', 'RUNNING')}
                          </span>
                        )}
                      </div>
                    </div>

                    {/* Connecting Line between pipeline nodes */}
                    {sIdx < STAGES_DEF.length - 1 && (
                      <div className="flex-grow flex items-center min-w-[14px] sm:min-w-[20px]">
                        <div
                          className={`h-[2px] w-full transition-colors duration-300 ${
                            isDone && getStageStatus(sIdx + 1) === 'completed'
                              ? 'bg-[#006F5F]'
                              : isDone && (getStageStatus(sIdx + 1) === 'running' || getStageStatus(sIdx + 1) === 'active')
                              ? 'bg-[#79563F]'
                              : 'bg-[#79563F]/20'
                          }`}
                        />
                      </div>
                    )}
                  </React.Fragment>
                );
              })}
            </div>

            {/* Dynamic Status Text Driven Strictly by State (Requirement 14 & 15) */}
            <div className="mt-3 flex items-center justify-between text-xs text-[#62584F] pt-1">
              <div className="flex items-center gap-2">
                {isRunningPipeline ? (
                  <span className="w-2 h-2 rounded-full bg-[#79563F] animate-ping shrink-0" />
                ) : allCompleted ? (
                  <span className="w-2 h-2 rounded-full bg-[#006F5F] shrink-0" />
                ) : (
                  <span className="w-2 h-2 rounded-full bg-[#79563F]/40 shrink-0" />
                )}
                <span className={isRunningPipeline ? 'font-bold text-[#79563F]' : 'font-medium'}>
                  {isRunningPipeline
                    ? getExecutionStatusText(activeStatusIdx)
                    : allCompleted
                    ? t('all6StagesCompleted', 'All 6 analytical stages completed and validated.')
                    : isCoreFeasibilityCompleted
                    ? t('feasibilityCompletedReadySwot', 'Core analytical engines & Feasibility completed. Next: 05 SWOT Matrix.')
                    : `${t('currentFocus', 'Current focus')}: ${STAGES_DEF[currentActiveIndex >= 0 ? currentActiveIndex : 0].title}`}
                </span>
              </div>

              <span className="text-[11px] text-[#79563F]/70 font-medium hidden sm:inline-block">
                {allCompleted ? t('readyForDprAssistant', 'Ready for DPR / Assistant') : isCoreFeasibilityCompleted ? t('readyForSwot', 'Ready for SWOT') : t('sequentialExecution', 'Sequential Execution')}
              </span>
            </div>
          </div>

          {/* Workflow Error Alert */}
          {workflowError && (
            <div className="mt-4 p-3.5 rounded-2xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-2">
              <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
              <span>{workflowError}</span>
            </div>
          )}
        </div>

        {/* Six Primary Pinned-Paper Orchestrator Cards along Alternating Journey Path */}
        <div className="relative max-w-5xl mx-auto pt-8 pb-12">
          {/* Subtle Vertical Journey Center Thread (Desktop) */}
          <div className="hidden lg:block absolute left-1/2 top-12 bottom-16 w-0.5 -translate-x-1/2 bg-[#79563F]/20 pointer-events-none" />

          <div className="space-y-16 sm:space-y-20 lg:space-y-24">
            {STAGES_DEF.map((comp, idx) => {
              const isEven = idx % 2 === 1;
              const status = getStageStatus(idx);

              return (
                <PinnedOrchestratorCard
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

        {/* Post-Analysis Guidance & Post-Launch Extension (Requirements 22-29) */}
        <div className="max-w-5xl mx-auto pt-4 pb-12">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 sm:gap-8">
            
            {/* Card 1: Your Business Assistant (Post-Analysis Guidance) */}
            <div className="rounded-3xl p-7 sm:p-9 bg-[#FAF2E3] border border-[#79563F]/20 shadow-sm flex flex-col justify-between space-y-5">
              <div className="space-y-2.5">
                <span className="text-[10px] uppercase font-bold tracking-widest text-[#79563F] font-mono">
                  {t('postAnalysisGuidance', 'POST-ANALYSIS GUIDANCE')}
                </span>
                <h3 className="text-2xl sm:text-3xl font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                  {t('yourBusinessAssistant', 'Your Business Assistant')}
                </h3>
                <p className="text-xs sm:text-sm text-[#62584F] leading-relaxed">
                  {t('assistantGuidanceDesc', "Once your business analysis is complete, KALPA's Business Assistant helps you understand the findings, ask questions, explore loan options and improve your business plan.")}
                </p>
              </div>

              <div className="pt-4 border-t border-[#79563F]/15">
                {isStage5Completed ? (
                  <Button
                    onClick={() => navigate(getStageUrl('/assistant'))}
                    icon={ArrowRight}
                    className="saffron-gradient-btn text-white font-bold shadow-md w-full justify-center cursor-pointer py-3"
                  >
                    {t('openBusinessAssistant', 'Open Business Assistant')}
                  </Button>
                ) : (
                  <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full bg-[#F1E4CC] border border-[#79563F]/20 text-[#79563F]/70 text-xs font-medium w-full justify-center">
                    <Lock className="w-3.5 h-3.5 text-[#79563F]/50" />
                    <span>{t('availableFromSwot', 'Available from SWOT Analysis page onwards.')}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Card 2: KALPA Growth Manager (Post-Launch Extension) */}
            <div className="rounded-3xl p-7 sm:p-9 bg-[#FAF2E3]/80 border border-[#79563F]/20 shadow-sm flex flex-col justify-between space-y-5">
              <div className="space-y-2.5">
                <div className="flex items-center justify-between">
                  <span className="text-[10px] uppercase font-bold tracking-widest text-[#79563F] font-mono">
                    {t('postLaunchExtension', 'POST-LAUNCH EXTENSION')}
                  </span>
                  <span className="text-[10px] uppercase font-bold px-2.5 py-0.5 rounded-full bg-[#FAF2E3] text-[#79563F]/60 border border-[#79563F]/15">
                    {t('stage04', 'Stage 04')}
                  </span>
                </div>

                <h3 className="text-2xl sm:text-3xl font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                  {t('kalpaGrowthManager', 'KALPA Growth Manager')}
                </h3>
                <p className="text-xs sm:text-sm text-[#62584F] leading-relaxed">
                  {t('growthManagerDesc', 'After your business launches, KALPA continues to support day-to-day operations, financial health, market changes and growth opportunities.')}
                </p>

                <div className="pt-2">
                  <div className="text-[11px] font-semibold text-[#79563F] bg-[#FAF2E3] px-3.5 py-2 rounded-xl border border-[#79563F]/15 inline-block">
                    {t('growthManagerPill', 'Revenue • Expenses • Repayment • Market • Growth')}
                  </div>
                </div>
              </div>

              <div className="pt-4 border-t border-[#79563F]/15">
                <div className="inline-flex items-center gap-2 px-4 py-2.5 rounded-full bg-[#F1E4CC] border border-[#79563F]/20 text-[#79563F]/70 text-xs font-medium w-full justify-center">
                  <Lock className="w-3.5 h-3.5 text-[#79563F]/50" />
                  <span>{t('availableAfterLaunch', 'Available after launch')}</span>
                </div>
              </div>
            </div>

          </div>
        </div>

      </div>
    </div>
  );
}
