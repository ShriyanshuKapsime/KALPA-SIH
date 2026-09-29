import React, { useState, useEffect, useCallback, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  Lightbulb,
  ShieldAlert,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  ArrowRight,
  ArrowLeft,
  Building2,
  MapPin,
  Lock,
  Sparkles,
  Info,
  Check,
  Target,
  FileText,
  AlertOctagon,
  Layers,
  Award,
  Clock,
  Compass,
  Cpu,
  Database
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';
import SwotQuadrantCard, { cleanEvidenceString } from '../../components/ui/SwotQuadrantCard';
import FloatingAssistantWidget from '../../components/assistant/FloatingAssistantWidget';

// Progressive 6-Stage Execution Definitions
export const SWOT_EXECUTION_STAGES = [
  {
    key: 'evidence-validation',
    index: 0,
    number: '01',
    title: 'Evidence validation',
    subtitle: 'Checking verified market, finance, readiness and risk evidence',
    defaultActivity: 'Validating upstream evidence across 5 analytical pillars…',
  },
  {
    key: 'strength-extraction',
    index: 1,
    number: '02',
    title: 'Strength extraction',
    subtitle: 'Identifying verified internal capabilities',
    defaultActivity: 'Analyzing promoter readiness, cash flow safety & competitive advantages…',
  },
  {
    key: 'weakness-analysis',
    index: 2,
    number: '03',
    title: 'Weakness analysis',
    subtitle: 'Evaluating capability and operating constraints',
    defaultActivity: 'Evaluating working capital buffer & operational dependencies…',
  },
  {
    key: 'opportunity-mapping',
    index: 3,
    number: '04',
    title: 'Opportunity mapping',
    subtitle: 'Mapping verified market and growth opportunities',
    defaultActivity: 'Mapping unmet catchment demand & institutional expansion linkages…',
  },
  {
    key: 'threat-assessment',
    index: 4,
    number: '05',
    title: 'Threat assessment',
    subtitle: 'Evaluating external risks and business constraints',
    defaultActivity: 'Assessing seasonal volatility, competitor pricing & compliance risks…',
  },
  {
    key: 'swot-synthesis',
    index: 5,
    number: '06',
    title: 'SWOT synthesis',
    subtitle: 'Combining verified findings into strategic actions',
    defaultActivity: 'Formulating executive strategic direction, priority action plan & phased roadmap…',
  },
];

// Helper to format evidence values
const formatVal = (v) => {
  if (v === null || v === undefined) return '—';
  if (typeof v === 'boolean') return v ? 'Yes' : 'No';
  if (typeof v === 'number') return Number.isInteger(v) ? v.toString() : v.toFixed(2);
  if (typeof v === 'string') return v;
  try {
    return JSON.stringify(v);
  } catch {
    return String(v);
  }
};

// Engine Name Formatter for Provenance (No stage numbers)
const formatStageName = (stageCode) => {
  if (!stageCode) return 'Feasibility';
  const code = String(stageCode).toUpperCase();
  if (code.includes('STAGE_6') || code.includes('STAGE6') || code.includes('MARKET')) return 'Market Intel';
  if (code.includes('STAGE_8') || code.includes('STAGE8') || code.includes('OPPORTUNITY')) return 'Opportunity';
  if (code.includes('STAGE_9') || code.includes('STAGE9') || code.includes('FINANCE') || code.includes('FINANCIAL')) return 'Finance';
  if (code.includes('STAGE_10') || code.includes('STAGE10') || code.includes('READINESS') || code.includes('ENTREPRENEUR')) return 'Readiness';
  if (code.includes('STAGE_11') || code.includes('STAGE11') || code.includes('RISK')) return 'Risk';
  if (code.includes('STAGE_12') || code.includes('STAGE12') || code.includes('FEASIBILITY')) return 'Feasibility';
  if (code.includes('STAGE_3') || code.includes('STAGE3') || code.includes('PROFILE')) return 'Profile';
  return String(stageCode).replace(/STAGE_?\d+/gi, '').replace(/^[•\s\-_]+/, '').trim() || 'Analytical Engine';
};

// Deterministic unique key helper for SWOT items ensuring zero cross-category collision
export const getDeterministicSwotKey = (category, item, idx, seenKeys = null) => {
  const catPrefix = (category || 'item').toLowerCase().replace(/s$/, '');
  const rawId = item?.id || item?.code;
  let key = rawId ? `${catPrefix}-${rawId}` : `${catPrefix}-${item?.title ? String(item.title).trim().slice(0, 20).replace(/[^a-zA-Z0-9]/g, '_').toLowerCase() : 'item'}-${idx}`;
  if (seenKeys && seenKeys.has(key)) {
    key = `${key}-${idx}`;
  }
  if (seenKeys) {
    seenKeys.add(key);
  }
  return key;
};

const MIN_STEP_TIME_MS = 750;
const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

export default function SWOTPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { t, language } = useLanguage();
  const {
    sessionId,
    analysisId,
    businessId,
    businessName,
    updateWorkflowState,
    completedStages,
  } = useWorkflow();

  const [loading, setLoading] = useState(true);
  const [currentStageIndex, setCurrentStageIndex] = useState(0);
  const [completedStagesSet, setCompletedStagesSet] = useState(new Set());
  const [stageActivities, setStageActivities] = useState({});
  const [stageSummaries, setStageSummaries] = useState({});
  const [failedStageIndex, setFailedStageIndex] = useState(null);
  const [isPreparingResult, setIsPreparingResult] = useState(false);
  const [swotData, setSwotData] = useState(null);
  const [error, setError] = useState(null);
  const [expandedItems, setExpandedItems] = useState({});
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'strengths', 'weaknesses', 'opportunities', 'threats'
  const [isAssistantOpen, setIsAssistantOpen] = useState(false);

  const effectiveAnalysisId = location.state?.analysisId || analysisId || sessionStorage.getItem('kalpa_analysis_id');
  const effectiveSessionId = location.state?.sessionId || sessionId || sessionStorage.getItem('kalpa_session_id');

  const hasFetchedRef = useRef(false);
  const isExecutingRef = useRef(false);

  const executeSWOTSequential = useCallback(async (isRetry = false) => {
    if (isExecutingRef.current) return;
    isExecutingRef.current = true;

    setLoading(true);
    setError(null);
    setFailedStageIndex(null);
    setIsPreparingResult(false);
    setCurrentStageIndex(0);
    setCompletedStagesSet(new Set());
    setStageActivities({});
    setStageSummaries({});
    setSwotData(null);

    let storedFinAnalysis = location.state?.financialAnalysis;
    if (!storedFinAnalysis) {
      try {
        const raw = sessionStorage.getItem('kalpa_financial_analysis');
        if (raw) storedFinAnalysis = JSON.parse(raw);
      } catch (e) {}
    }

    let storedFinContext = location.state?.financialContext;
    if (!storedFinContext) {
      try {
        const raw = sessionStorage.getItem('kalpa_financial_context');
        if (raw) storedFinContext = JSON.parse(raw);
      } catch (e) {}
    }
    if (!storedFinContext && storedFinAnalysis?.financial_context) {
      storedFinContext = storedFinAnalysis.financial_context;
    }

    const payload = {
      analysis_id: effectiveAnalysisId || undefined,
      session_id: effectiveSessionId || undefined,
      business_profile: location.state?.businessProfile || undefined,
      location_profile: location.state?.locationProfile || undefined,
      market_analysis: location.state?.marketAnalysis || undefined,
      opportunity_result: location.state?.opportunityResult || undefined,
      financial_analysis: storedFinAnalysis || undefined,
      financial_context: storedFinContext || undefined,
      entrepreneur_readiness: location.state?.entrepreneurReadiness || undefined,
      risk_analysis: location.state?.riskAnalysis || undefined,
      feasibility_result: location.state?.feasibilityResult || undefined,
      language: language || 'en',
      language_code: language || 'en',
      force_refresh: isRetry
    };

    const eventQueue = [];
    let streamFinished = false;
    let streamError = null;

    // Launch SSE Stream or fallback
    (async () => {
      try {
        console.log('[SWOT STREAM] Launching stage 13 agent stream:', payload);
        await apiService.swot.stream(payload, (evt) => {
          eventQueue.push(evt);
        });
      } catch (err) {
        console.warn('[SWOT STREAM] Direct stream encountered error, attempting fallback:', err);
        try {
          const syncResp = await apiService.swot.analyze(payload);
          SWOT_EXECUTION_STAGES.forEach((stg, i) => {
            eventQueue.push({ step: stg.key, step_index: i, status: 'running', activity: stg.defaultActivity });
            eventQueue.push({ step: stg.key, step_index: i, status: 'completed', summary: stg.subtitle });
          });
          eventQueue.push({ step: 'complete', step_index: 6, status: 'completed', result: syncResp });
        } catch (syncErr) {
          streamError = syncErr;
        }
      } finally {
        streamFinished = true;
      }
    })();

    // Sequentially process events with perceptible pacing
    try {
      let finalResultData = null;
      let lastCompletedIdx = -1;

      while (true) {
        if (eventQueue.length > 0) {
          const evt = eventQueue.shift();

          if (evt.status === 'blocked') {
            setSwotData({ status: 'BLOCKED_NOT_FEASIBLE', message: evt.message });
            setLoading(false);
            isExecutingRef.current = false;
            return;
          }

          if (evt.status === 'failed' || evt.step === 'error') {
            const failIdx = evt.step_index ?? currentStageIndex;
            setFailedStageIndex(failIdx);
            setError({
              errorCode: evt.error_code || 'SWOT_STAGE_FAILED',
              message: evt.message || 'Stage execution failed.',
              retryable: true
            });
            setLoading(false);
            isExecutingRef.current = false;
            return;
          }

          if (evt.step === 'complete' && evt.result) {
            finalResultData = evt.result;
          } else if (typeof evt.step_index === 'number') {
            const idx = evt.step_index;
            if (evt.status === 'running') {
              setCurrentStageIndex(idx);
              if (evt.activity) {
                setStageActivities(prev => ({ ...prev, [idx]: evt.activity }));
              }
              await sleep(MIN_STEP_TIME_MS);
            } else if (evt.status === 'completed') {
              setCompletedStagesSet(prev => new Set(prev).add(idx));
              if (evt.summary) {
                setStageSummaries(prev => ({ ...prev, [idx]: evt.summary }));
              }
              lastCompletedIdx = Math.max(lastCompletedIdx, idx);
            }
          }
        } else if (streamFinished) {
          if (streamError) {
            setError({
              errorCode: 'SWOT_API_ERROR',
              message: streamError.message || 'Failed to communicate with Dynamic SWOT Agent. Please retry.',
              retryable: true
            });
            setLoading(false);
            isExecutingRef.current = false;
            return;
          }

          if (finalResultData) {
            // Mark all 6 stages completed
            setCompletedStagesSet(new Set([0, 1, 2, 3, 4, 5]));
            setIsPreparingResult(true);
            setSwotData(finalResultData);

            // Auto-expand all items
            const initialExpanded = {};
            ['strengths', 'weaknesses', 'opportunities', 'threats'].forEach(cat => {
              const catPrefix = cat.replace(/s$/, '');
              const seen = new Set();
              (finalResultData.swot?.[cat] || []).forEach((item, idx) => {
                const key = getDeterministicSwotKey(catPrefix, item, idx, seen);
                initialExpanded[key] = true;
                if (item?.id) initialExpanded[item.id] = true;
              });
            });
            setExpandedItems(initialExpanded);

            // Mark SWOT completed in workflow context
            if (finalResultData.status === 'COMPLETED' || finalResultData.status === 'complete') {
              if (!completedStages?.includes(13)) {
                updateWorkflowState({
                  completedStages: Array.from(new Set([...(completedStages || []), 13])),
                  currentStage: 13,
                  availableStages: [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14],
                });
              }
            }

            await sleep(450); // Clean visual conclusion transition
            setLoading(false);
            isExecutingRef.current = false;
            return;
          }
          await sleep(60);
        } else {
          await sleep(60);
        }
      }
    } catch (loopErr) {
      console.error('[SWOT QUEUE ERROR]', loopErr);
      setError({
        errorCode: 'SWOT_PROCESSING_ERROR',
        message: loopErr.message || 'Execution error during SWOT analysis.',
        retryable: true
      });
      setLoading(false);
      isExecutingRef.current = false;
    }
  }, [effectiveAnalysisId, effectiveSessionId, location.state, language, completedStages, updateWorkflowState, currentStageIndex]);

  // Initial load once on mount
  useEffect(() => {
    if (!hasFetchedRef.current) {
      hasFetchedRef.current = true;
      executeSWOTSequential(false);
    }
  }, [executeSWOTSequential]);

  const toggleItem = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const getPriorityBadgeClass = (priority) => {
    switch ((priority || '').toUpperCase()) {
      case 'HIGH':
        return 'bg-[#FAF2E3] text-[#A05A35] border-[#A05A35]/30 font-bold';
      case 'MEDIUM':
        return 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25';
      case 'LOW':
        return 'bg-[#FAF7F2] text-[#79563F]/80 border-[#79563F]/20';
      default:
        return 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25';
    }
  };

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 space-y-8 relative text-[#28231F]">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* 1. Canonical KALPA Workflow Timeline Header */}
        <WorkflowTimeline />

        {/* 2. True Sequential SWOT Agent Loader */}
        {loading && (
          <div className="royal-card bg-[#FAF7F2] rounded-3xl p-8 sm:p-12 border border-[#79563F]/20 shadow-xs max-w-2xl mx-auto space-y-8 text-center animate-fadeIn">
            <div className="space-y-2">
              <div className="inline-flex items-center gap-1.5 px-3.5 py-1.5 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 shadow-2xs">
                <Compass className="w-3.5 h-3.5 text-[#79563F]" />
                <span>STAGE 13 · DYNAMIC SWOT AGENT</span>
              </div>
              <h3 className="text-2xl font-bold text-[#1C1917] font-['Outfit']">
                Strategic Synthesis Pipeline
              </h3>
              <p className="text-xs text-[#79563F] max-w-md mx-auto leading-relaxed">
                Autonomous sequential reasoning synthesizing verified upstream evidence across 5 analytical pillars.
              </p>
            </div>

            {/* Progressive 6-Stage Processing Timeline */}
            <div className="text-left space-y-4 max-w-xl mx-auto pt-2">
              {SWOT_EXECUTION_STAGES.map((stg, idx) => {
                const isCompleted = completedStagesSet.has(idx);
                const isActive = currentStageIndex === idx && !isCompleted;
                const isFailed = failedStageIndex === idx;

                return (
                  <div key={stg.key} className="relative flex items-start gap-4">
                    {/* Step Icon / Circle Badge */}
                    <div className="flex flex-col items-center flex-shrink-0 pt-0.5">
                      {isCompleted ? (
                        <div className="w-7 h-7 rounded-full bg-[#1B4D3E] text-white flex items-center justify-center shadow-xs transition-transform duration-300 scale-100">
                          <Check className="w-4 h-4 stroke-[3]" />
                        </div>
                      ) : isFailed ? (
                        <div className="w-7 h-7 rounded-full bg-[#9B2C2C] text-white flex items-center justify-center shadow-xs">
                          <AlertOctagon className="w-4 h-4" />
                        </div>
                      ) : isActive ? (
                        <div className="w-7 h-7 rounded-full bg-[#EAF5EE] border-2 border-[#1B4D3E] flex items-center justify-center relative shadow-xs">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#1B4D3E] animate-ping absolute opacity-75" />
                          <span className="w-2.5 h-2.5 rounded-full bg-[#1B4D3E] relative" />
                        </div>
                      ) : (
                        <div className="w-7 h-7 rounded-full border border-[#79563F]/25 bg-[#FAF2E3] flex items-center justify-center text-[11px] font-mono text-[#79563F]/50">
                          {stg.number}
                        </div>
                      )}

                      {/* Connecting Line */}
                      {idx < SWOT_EXECUTION_STAGES.length - 1 && (
                        <div
                          className={`w-0.5 h-8 mt-1 transition-colors duration-300 ${
                            isCompleted ? 'bg-[#1B4D3E]' : 'bg-[#79563F]/15'
                          }`}
                        />
                      )}
                    </div>

                    {/* Step Text Info */}
                    <div className="space-y-1 pb-2 flex-1">
                      <div className="flex items-center justify-between">
                        <h4
                          className={`text-xs font-bold leading-tight transition-colors duration-200 ${
                            isCompleted
                              ? 'text-[#1C1917]'
                              : isActive
                              ? 'text-[#1B4D3E]'
                              : 'text-[#79563F]/60'
                          }`}
                        >
                          <span className="font-mono text-[11px] mr-1.5 opacity-80">{stg.number} ·</span>
                          {stg.title}
                        </h4>

                        {isActive && (
                          <span className="inline-flex items-center gap-1 text-[10px] font-bold text-[#1B4D3E] uppercase tracking-wider bg-[#EAF5EE] px-2 py-0.5 rounded-full border border-[#1B4D3E]/30 animate-pulse">
                            <span className="w-1.5 h-1.5 rounded-full bg-[#1B4D3E]" />
                            RUNNING
                          </span>
                        )}
                        {isCompleted && (
                          <span className="text-[10px] font-bold text-[#1B4D3E] uppercase tracking-wider">
                            COMPLETED
                          </span>
                        )}
                      </div>

                      {isActive ? (
                        <p className="text-[11px] text-[#79563F] font-medium leading-relaxed animate-pulse">
                          {stageActivities[idx] || stg.defaultActivity}
                        </p>
                      ) : isCompleted ? (
                        <p className="text-[11px] text-[#79563F]/80 leading-relaxed">
                          {stageSummaries[idx] || stg.subtitle}
                        </p>
                      ) : (
                        <p className="text-[11px] text-[#79563F]/45 leading-relaxed">
                          {stg.subtitle}
                        </p>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Preparing Final Result Banner */}
            {isPreparingResult && (
              <div className="p-3.5 bg-[#EAF5EE] rounded-2xl border border-[#1B4D3E]/30 text-xs font-bold text-[#1B4D3E] flex items-center justify-center gap-2 animate-fadeIn shadow-2xs">
                <Check className="w-4 h-4 stroke-[3]" />
                <span>SWOT synthesis complete · Preparing your strategic analysis…</span>
              </div>
            )}
          </div>
        )}

        {/* 3. Error / LLM Unavailable State */}
        {!loading && error && (
          <div className="royal-card bg-[#FAF7F2] border border-[#A05A35]/30 rounded-3xl p-8 space-y-6 shadow-xs text-[#1C1917]">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-[#FAF2E3] rounded-2xl text-[#A05A35] border border-[#A05A35]/30 flex-shrink-0">
                <AlertOctagon className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF2E3] text-[#A05A35] border border-[#A05A35]/30">
                    {error.errorCode || 'SERVICE NOTICE'}
                  </span>
                  <span className="text-xs text-[#79563F] font-medium">Strategic SWOT Engine</span>
                </div>
                <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                  SWOT Analysis Notice
                </h3>
                <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
                  {error.message}
                </p>
                <div className="p-3.5 bg-[#FAF2E3] rounded-xl border border-[#79563F]/18 text-xs text-[#28231F] space-y-1">
                  <div className="font-semibold text-[#1C1917]">Deterministic Status:</div>
                  <div>✓ All upstream calculations remain intact and persisted.</div>
                  <div>✓ You can retry the SWOT analysis or proceed with existing findings.</div>
                </div>
              </div>
            </div>

            {error.retryable && (
              <div className="flex items-center space-x-3 pt-2">
                <button
                  type="button"
                  onClick={() => executeSWOTSequential(true)}
                  className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center space-x-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry SWOT Analysis</span>
                </button>
                <Link
                  to="/feasibility"
                  className="px-4 py-2.5 bg-[#FAF2E3] border border-[#79563F]/25 hover:bg-[#FAF7F2] text-[#79563F] rounded-xl text-xs font-bold transition"
                >
                  Return to Feasibility
                </Link>
              </div>
            )}
          </div>
        )}

        {/* 4. Blocked / Not Feasible State */}
        {!loading && swotData?.status === 'BLOCKED_NOT_FEASIBLE' && (
          <div className="royal-card bg-[#FAF7F2] border border-[#A05A35]/30 rounded-3xl p-8 space-y-6 shadow-xs text-[#1C1917]">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-[#FAF2E3] rounded-2xl text-[#A05A35] border border-[#A05A35]/30 flex-shrink-0">
                <AlertTriangle className="w-7 h-7" />
              </div>
              <div className="space-y-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF2E3] text-[#A05A35] border border-[#A05A35]/30">
                  FEASIBILITY GATE
                </span>
                <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                  SWOT Gated for Non-Viable Venture
                </h3>
                <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
                  {swotData.message || 'Dynamic SWOT is reserved for viable ventures. Please review recommended business pivots in Feasibility.'}
                </p>
              </div>
            </div>
            <Link
              to="/feasibility"
              className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center space-x-2 cursor-pointer shadow-xs transition-all hover:scale-[1.02]"
            >
              <span>View Feasibility & Pivot Advisor</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
        )}

        {/* 5. Completed Strategic SWOT Report */}
        {!loading && swotData && (swotData.status === 'COMPLETED' || swotData.status === 'complete') && (
          <div className="space-y-8 animate-fadeIn">
            
            {/* SWOT Hero Banner */}
            <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs relative overflow-hidden bg-[#FAF2E3]">
              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                <div className="space-y-1.5">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                      {t('swot_title', 'SWOT Analysis')}
                    </span>
                    {swotData.confidence > 0 && (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25">
                        {t('confidence', 'Confidence')} {(swotData.confidence * 100).toFixed(0)}%
                      </span>
                    )}
                  </div>

                  <h2 className="text-2xl font-bold text-[#1C1917] font-['Outfit']">
                    <TranslatedText text={swotData.business_name || businessName || 'Commercial Dairy Farm'} />
                  </h2>

                  <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
                    {t('swot_subtitle', 'Strategic view of internal capabilities and external business factors.')}
                  </p>

                  <div className="flex items-center space-x-4 text-xs text-[#79563F] pt-1">
                    <span className="flex items-center space-x-1">
                      <MapPin className="w-3.5 h-3.5 text-[#79563F]/70" />
                      <span><TranslatedText text={swotData.location || 'Local Cluster'} /></span>
                    </span>
                    <span className="text-[#79563F]/40">•</span>
                    <span className="flex items-center space-x-1">
                      <Layers className="w-3.5 h-3.5 text-[#79563F]/70" />
                      <span>{t('multi_pillar_evidence', 'Multi-Pillar Evidence Verified')}</span>
                    </span>
                  </div>
                </div>

                <div className="flex items-center space-x-3">
                  <Link
                    to={`/dpr?session_id=${effectiveSessionId || ''}&analysis_id=${effectiveAnalysisId || ''}&business_id=${businessId || effectiveSessionId || ''}`}
                    state={{ sessionId: effectiveSessionId, analysisId: effectiveAnalysisId, businessId }}
                    className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02] shrink-0 self-end sm:self-auto"
                  >
                    <span>{t('proceed_to_dpr', 'Proceed to DPR')}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>
            </div>

            {/* Strategic Summary & Executive Synthesis */}
            {(swotData.strategic_summary || swotData.swot?.executive_summary) && (
              <div className="royal-card bg-[#FAF2E3] rounded-3xl p-6 sm:p-8 border border-[#79563F]/20 shadow-xs space-y-6 text-[#1C1917]">
                <div className="space-y-1">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F] flex items-center space-x-1.5">
                    <Compass className="w-3.5 h-3.5 text-[#79563F]" />
                    <span>{t('swot_executive_direction', 'EXECUTIVE STRATEGIC DIRECTION')}</span>
                  </span>
                  <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
                    {t('swot_what_means', 'What This Means for Your Business')}
                  </h3>
                </div>

                <p className="text-sm text-[#28231F] leading-relaxed max-w-4xl">
                  <TranslatedText text={cleanEvidenceString(swotData.swot?.executive_summary || swotData.strategic_summary?.business_position)} />
                </p>

                {swotData.swot?.strategic_direction && swotData.swot.strategic_direction !== swotData.swot.executive_summary && (
                  <div className="p-3.5 bg-[#FAF7F2] rounded-xl border border-[#79563F]/18 text-xs text-[#28231F]">
                    <strong className="text-[#79563F]">{t('strategic_direction', 'Strategic Direction')}: </strong>
                    <TranslatedText text={cleanEvidenceString(swotData.swot.strategic_direction)} />
                  </div>
                )}

                {swotData.strategic_summary && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2 border-t border-[#79563F]/15">
                    <div className="bg-[#FAF7F2] rounded-2xl p-4 border border-[#79563F]/15 space-y-1.5">
                      <span className="text-[10px] font-bold text-[#1B4D3E] uppercase tracking-wide flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3 text-[#1B4D3E]" />
                        <span>{t('key_advantage', 'Key Advantage')}</span>
                      </span>
                      <p className="text-xs text-[#28231F] leading-snug">
                        <TranslatedText text={cleanEvidenceString(swotData.strategic_summary.key_advantage)} />
                      </p>
                    </div>

                    <div className="bg-[#FAF7F2] rounded-2xl p-4 border border-[#79563F]/15 space-y-1.5">
                      <span className="text-[10px] font-bold text-[#A05A35] uppercase tracking-wide flex items-center space-x-1">
                        <AlertTriangle className="w-3 h-3 text-[#A05A35]" />
                        <span>{t('main_constraint', 'Main Constraint')}</span>
                      </span>
                      <p className="text-xs text-[#28231F] leading-snug">
                        <TranslatedText text={cleanEvidenceString(swotData.strategic_summary.main_constraint)} />
                      </p>
                    </div>

                    <div className="bg-[#FAF7F2] rounded-2xl p-4 border border-[#79563F]/15 space-y-1.5">
                      <span className="text-[10px] font-bold text-[#2C5282] uppercase tracking-wide flex items-center space-x-1">
                        <Lightbulb className="w-3 h-3 text-[#2C5282]" />
                        <span>{t('top_growth_opportunity', 'Top Growth Opportunity')}</span>
                      </span>
                      <p className="text-xs text-[#28231F] leading-snug">
                        <TranslatedText text={cleanEvidenceString(swotData.strategic_summary.biggest_opportunity)} />
                      </p>
                    </div>

                    <div className="bg-[#FAF7F2] rounded-2xl p-4 border border-[#79563F]/15 space-y-1.5">
                      <span className="text-[10px] font-bold text-[#9B2C2C] uppercase tracking-wide flex items-center space-x-1">
                        <ShieldAlert className="w-3 h-3 text-[#9B2C2C]" />
                        <span>{t('critical_threat', 'Critical Threat')}</span>
                      </span>
                      <p className="text-xs text-[#28231F] leading-snug">
                        <TranslatedText text={cleanEvidenceString(swotData.strategic_summary.biggest_threat)} />
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SWOT 4-Quadrant Filter Navigation */}
            <div className="flex items-center space-x-2 pb-1 overflow-x-auto">
              {[
                { id: 'all', label: t('swot_all_quadrants', 'All 4 Quadrants'), count: null, dotColor: 'bg-[#79563F]' },
                { id: 'strengths', label: t('swot_strengths', 'Strengths'), count: swotData.swot?.strengths?.length || 0, dotColor: 'bg-[#1B4D3E]' },
                { id: 'weaknesses', label: t('swot_weaknesses', 'Weaknesses'), count: swotData.swot?.weaknesses?.length || 0, dotColor: 'bg-[#A05A35]' },
                { id: 'opportunities', label: t('swot_opportunities', 'Opportunities'), count: swotData.swot?.opportunities?.length || 0, dotColor: 'bg-[#2C5282]' },
                { id: 'threats', label: t('swot_threats', 'Threats'), count: swotData.swot?.threats?.length || 0, dotColor: 'bg-[#9B2C2C]' },
              ].map(tab => {
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    className={`px-3.5 py-1.5 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap ${
                      isActive
                        ? 'bg-[#79563F] text-white shadow-2xs'
                        : 'bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20 hover:bg-[#F2E8D5]'
                    }`}
                  >
                    <span className={`w-2 h-2 rounded-full ${tab.dotColor} ${isActive ? 'ring-1 ring-white' : ''}`} />
                    <span>{tab.label}</span>
                    {tab.count !== null && (
                      <span className={`text-[10px] px-1.5 py-0.2 rounded-md ${
                        isActive ? 'bg-white/20 text-white' : 'bg-[#FAF7F2] text-[#79563F]'
                      }`}>
                        {tab.count}
                      </span>
                    )}
                  </button>
                );
              })}
            </div>

            {/* SWOT Quadrants 2x2 Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* STRENGTHS */}
              {(activeTab === 'all' || activeTab === 'strengths') && (
                <SwotQuadrantCard
                  category="strengths"
                  title="STRENGTHS"
                  subtitle="What is already working in your favor (Internal Positive)"
                  items={swotData.swot?.strengths || []}
                  expandedItems={expandedItems}
                  onToggleItem={toggleItem}
                  formatStageName={formatStageName}
                  formatVal={formatVal}
                  getDeterministicKey={getDeterministicSwotKey}
                />
              )}

              {/* WEAKNESSES */}
              {(activeTab === 'all' || activeTab === 'weaknesses') && (
                <SwotQuadrantCard
                  category="weaknesses"
                  title="WEAKNESSES"
                  subtitle="What currently limits the business (Internal Negative)"
                  items={swotData.swot?.weaknesses || []}
                  expandedItems={expandedItems}
                  onToggleItem={toggleItem}
                  formatStageName={formatStageName}
                  formatVal={formatVal}
                  getDeterministicKey={getDeterministicSwotKey}
                />
              )}

              {/* OPPORTUNITIES */}
              {(activeTab === 'all' || activeTab === 'opportunities') && (
                <SwotQuadrantCard
                  category="opportunities"
                  title="OPPORTUNITIES"
                  subtitle="Where the entrepreneur can capture value (External Positive)"
                  items={swotData.swot?.opportunities || []}
                  expandedItems={expandedItems}
                  onToggleItem={toggleItem}
                  formatStageName={formatStageName}
                  formatVal={formatVal}
                  getDeterministicKey={getDeterministicSwotKey}
                />
              )}

              {/* THREATS */}
              {(activeTab === 'all' || activeTab === 'threats') && (
                <SwotQuadrantCard
                  category="threats"
                  title="THREATS"
                  subtitle="What could negatively affect the business (External Negative)"
                  items={swotData.swot?.threats || []}
                  expandedItems={expandedItems}
                  onToggleItem={toggleItem}
                  formatStageName={formatStageName}
                  formatVal={formatVal}
                  getDeterministicKey={getDeterministicSwotKey}
                />
              )}

            </div>

            {/* Priority Actions */}
            <div className="royal-card bg-[#FAF2E3] rounded-3xl p-6 sm:p-7 border border-[#79563F]/18 shadow-xs space-y-5 text-[#1C1917]">
              <div className="flex items-center justify-between pb-3 border-b border-[#79563F]/15">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                      PRIORITY ACTION PLAN
                    </span>
                    <span className="text-xs font-semibold text-[#79563F]">
                      Top Strategic Interventions
                    </span>
                  </div>
                  <h4 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                    What Should the Entrepreneur Do Next?
                  </h4>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/20">
                  {swotData.swot?.priority_actions?.length || swotData.immediate_actions?.length || swotData.recommendations?.length || 0} Priorities
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                {(swotData.swot?.priority_actions && swotData.swot.priority_actions.length > 0
                  ? swotData.swot.priority_actions
                  : (swotData.recommendations || []).map(r => ({
                      action: r.action,
                      reason: r.reason,
                      priority: r.priority,
                      source_stage: (r.source_stages && r.source_stages[0]) || 'READINESS'
                    }))
                ).map((act, aIdx) => (
                  <div
                    key={`rec-${act.id || act.action?.slice(0, 16) || aIdx}`}
                    className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#79563F]/18 space-y-3 hover:border-[#79563F]/40 transition flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-[#79563F] font-mono">
                          STEP {aIdx + 1}
                        </span>
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${getPriorityBadgeClass(act.priority)}`}>
                          {act.priority || 'HIGH'} PRIORITY
                        </span>
                      </div>

                      <h6 className="text-xs font-bold text-[#1C1917] leading-snug break-words">
                        {cleanEvidenceString(act.action)}
                      </h6>

                      <p className="text-[11px] text-[#79563F] leading-relaxed break-words">
                        <strong className="text-[#1C1917]">Why: </strong>
                        {cleanEvidenceString(act.reason)}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-[#79563F]/12 flex items-center justify-between text-[10px] text-[#79563F]">
                      <span className="font-bold">Source:</span>
                      <span className="font-mono px-1.5 py-0.5 bg-white border border-[#79563F]/20 rounded text-[#1C1917]">
                        {formatStageName(act.source_stage)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Phased Strategic Roadmap */}
            {swotData.swot?.roadmap && swotData.swot.roadmap.length > 0 && (
              <div className="royal-card bg-[#FAF2E3] rounded-3xl p-6 sm:p-7 border border-[#79563F]/18 shadow-xs space-y-5 text-[#1C1917]">
                <div className="flex items-center justify-between pb-3 border-b border-[#79563F]/15">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                        STRATEGIC ROADMAP
                      </span>
                      <span className="text-xs font-semibold text-[#79563F]">
                        Phased Implementation Timeline
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                      Execution Milestones & Action Steps
                    </h4>
                  </div>
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/20">
                    {swotData.swot.roadmap.length} Phases
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {swotData.swot.roadmap.map((phase, pIdx) => (
                    <div
                      key={`phase-${phase.phase || pIdx}`}
                      className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#79563F]/18 space-y-3"
                    >
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-[#79563F]" />
                        <span className="text-xs font-bold text-[#1C1917] uppercase tracking-wide">
                          {cleanEvidenceString(phase.phase)}
                        </span>
                      </div>
                      <ul className="space-y-2 text-xs text-[#28231F]">
                        {(phase.actions || []).map((act, actIdx) => (
                          <li key={`act-${phase.phase || pIdx}-${actIdx}`} className="flex items-start space-x-2">
                            <span className="text-[#79563F] font-bold text-xs mt-0.5">•</span>
                            <span className="text-[11px] leading-relaxed break-words">{cleanEvidenceString(act)}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Upstream Evidence Verification Strip (5 Pillars) */}
            {swotData.evidence_summary && (
              <div className="royal-card bg-[#FAF2E3] rounded-3xl p-6 border border-[#79563F]/18 shadow-2xs space-y-4 text-[#1C1917]">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-[#79563F]" />
                    <h4 className="text-xs font-bold text-[#1C1917] uppercase tracking-wider">
                      Upstream Evidence Verification Baseline
                    </h4>
                  </div>
                  <span className="text-[11px] text-[#79563F] font-medium">5 Pillars Grounded</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                  <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#79563F]/15 space-y-1">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wide">Market</span>
                    <p className="text-[11px] text-[#28231F] leading-snug">
                      {cleanEvidenceString(swotData.evidence_summary.market) || 'Verified demand signals'}
                    </p>
                  </div>
                  <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#79563F]/15 space-y-1">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wide">Finance</span>
                    <p className="text-[11px] text-[#28231F] leading-snug">
                      {cleanEvidenceString(swotData.evidence_summary.financial) || 'Verified DSCR & financing'}
                    </p>
                  </div>
                  <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#79563F]/15 space-y-1">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wide">Readiness</span>
                    <p className="text-[11px] text-[#28231F] leading-snug">
                      {cleanEvidenceString(swotData.evidence_summary.entrepreneur) || 'Promoter readiness confirmed'}
                    </p>
                  </div>
                  <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#79563F]/15 space-y-1">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wide">Risk</span>
                    <p className="text-[11px] text-[#28231F] leading-snug">
                      {cleanEvidenceString(swotData.evidence_summary.risk) || 'Multi-vector risks mapped'}
                    </p>
                  </div>
                  <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#79563F]/15 space-y-1">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wide">Feasibility</span>
                    <p className="text-[11px] text-[#28231F] leading-snug">
                      {cleanEvidenceString(swotData.evidence_summary.feasibility) || 'Viable venture approved'}
                    </p>
                  </div>
                </div>
              </div>
            )}

            {/* AI Business Advisor & DPR CTA Section */}
            <div className="royal-card bg-[#FAF2E3] text-[#1C1917] rounded-3xl p-6 sm:p-8 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6 border border-[#79563F]/20">
              <div className="space-y-1.5 text-center md:text-left">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                  AI Business Advisor
                </span>
                <h3 className="text-xl font-bold font-['Outfit'] text-[#1C1917]">
                  Need help with your next step?
                </h3>
                <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
                  Ask the AI Business Advisor about your SWOT findings, finance or actions.
                </p>
              </div>

              <div className="flex flex-wrap items-center gap-3">
                <button
                  type="button"
                  onClick={() => window.dispatchEvent(new CustomEvent('kalpa:open-ai-advisor'))}
                  className="px-5 py-2.5 bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/25 rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-2xs cursor-pointer whitespace-nowrap"
                >
                  <Sparkles className="w-4 h-4 text-[#79563F]" />
                  <span>Talk to AI Advisor →</span>
                </button>
                <Link
                  to={`/dpr?session_id=${effectiveSessionId || ''}&analysis_id=${effectiveAnalysisId || ''}&business_id=${businessId || effectiveSessionId || ''}`}
                  state={{ sessionId: effectiveSessionId, analysisId: effectiveAnalysisId, businessId }}
                  className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02] whitespace-nowrap"
                >
                  <span>Proceed to DPR →</span>
                </Link>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
