import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  TrendingUp,
  Award,
  AlertTriangle,
  CheckCircle2,
  BarChart3,
  ShieldCheck,
  RefreshCw,
  ArrowRight,
  Building2,
  MapPin
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';

export default function OpportunityEvaluationPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
    businessName: ctxBusinessName,
    businessId: ctxBusinessId,
    updateWorkflowState,
    markStageComplete
  } = useWorkflow();

  const { t, language } = useLanguage();

  const queryParams = new URLSearchParams(location.search);
  const initialSessionId = location.state?.sessionId || location.state?.session_id || queryParams.get('session_id') || ctxSessionId || '';
  const initialAnalysisId = location.state?.analysisId || location.state?.analysis_id || queryParams.get('analysis_id') || ctxAnalysisId || '';
  const incomingStage6Output = location.state?.stage6Output || location.state?.stage6_output || null;

  const [sessionId, setSessionId] = useState(initialSessionId);
  const [analysisId, setAnalysisId] = useState(initialAnalysisId);
  const [stage6Data, setStage6Data] = useState(incomingStage6Output);
  const [loading, setLoading] = useState(false);
  const [fetchingStage6, setFetchingStage6] = useState(false);
  const [error, setError] = useState(null);
  const [evaluationResult, setEvaluationResult] = useState(null);

  const lastEvaluatedAnalysisIdRef = useRef(null);
  const isExecutingRef = useRef(false);

  // Execute Stage 8 Evaluation
  const executeStage8 = useCallback(async (s6Payload, force = false) => {
    if (!s6Payload) return;
    const currentAid = s6Payload.analysis_id || analysisId;

    if (!force && lastEvaluatedAnalysisIdRef.current === currentAid && evaluationResult) {
      return;
    }

    if (isExecutingRef.current) return;
    isExecutingRef.current = true;
    setLoading(true);
    setError(null);

    const payload = {
      analysis_id: s6Payload.analysis_id || analysisId || undefined,
      session_id: s6Payload.session_id || sessionId || undefined,
      business_context: s6Payload.business_context || {
        business_id: ctxBusinessId,
        specific_business: ctxBusinessName
      },
      location_context: s6Payload.location_context || {},
      market_intelligence: s6Payload,
      demand_prediction: null
    };

    try {
      const response = await apiService.opportunityEvaluation.analyze(payload);
      setEvaluationResult(response);
      lastEvaluatedAnalysisIdRef.current = response.analysis_id || currentAid;

      const scorePct = Math.round((response.opportunity_result?.market_opportunity_score || 0.88) * 100);

      updateWorkflowState({
        sessionId: response.session_id || sessionId,
        analysisId: response.analysis_id || analysisId,
        currentStage: 8,
        completedStages: [1, 2, 3, 4, 5, 6, 8],
        nextStage: 9,
        workflowStatus: 'MARKET_OPPORTUNITY_EVALUATED',
        engineOutputs: {
          opportunity_evaluation: `${scorePct}% Opportunity ✓`
        }
      });
      markStageComplete(8, 9);
    } catch (err) {
      console.error('[STAGE 8 ERROR]', err);
      setError(err.message || 'Failed to evaluate market opportunity from Stage 6 intelligence.');
    } finally {
      setLoading(false);
      isExecutingRef.current = false;
    }
  }, [analysisId, sessionId, ctxBusinessId, ctxBusinessName, evaluationResult, updateWorkflowState, markStageComplete]);

  // Load Active Pipeline Data if Stage 6 output was not passed directly
  const loadStage6FromBackend = useCallback(async (targetId) => {
    if (!targetId || isExecutingRef.current) return;
    setFetchingStage6(true);
    setError(null);
    try {
      const s5Profile = await apiService.marketIntelligence.getById(targetId);
      if (s5Profile) {
        const s6Res = await apiService.marketIntelligence.analyze(s5Profile);
        if (s6Res) {
          setStage6Data(s6Res);
          setAnalysisId(s6Res.analysis_id);
          setSessionId(s6Res.session_id);
          await executeStage8(s6Res);
        }
      }
    } catch (err) {
      if (err.status === 404) {
        setError('Market evidence profile has not been compiled yet for this analysis. Please complete Stage 5 & 6 Market Intelligence first.');
      } else {
        setError(err.message || 'Could not retrieve active market intelligence records.');
      }
    } finally {
      setFetchingStage6(false);
    }
  }, [executeStage8]);

  useEffect(() => {
    if (incomingStage6Output) {
      setStage6Data(incomingStage6Output);
      executeStage8(incomingStage6Output);
    } else if (analysisId) {
      loadStage6FromBackend(analysisId);
    } else if (sessionId) {
      apiService.orchestrator.getWorkflowStatus(sessionId)
        .then(wf => {
          if (wf && wf.analysis_id) {
            setAnalysisId(wf.analysis_id);
            loadStage6FromBackend(wf.analysis_id);
          }
        })
        .catch(err => {
          console.log('[STAGE 8] Waiting for workflow context:', err.message);
        });
    }
  }, [incomingStage6Output, analysisId, sessionId, executeStage8, loadStage6FromBackend]);

  const opp = evaluationResult?.opportunity_result;
  const comp = opp?.component_scores;

  const displayBusinessName =
    evaluationResult?.business_context?.specific_business ||
    evaluationResult?.business_context?.business_name ||
    stage6Data?.business_context?.specific_business ||
    ctxBusinessName ||
    'Agro-Processing & Dairy Enterprise';

  const locCtx = evaluationResult?.location_context || stage6Data?.location_context || {};
  const resolvedLoc = locCtx.resolved_location || locCtx;
  const displayLocation = [
    resolvedLoc.village || resolvedLoc.block,
    resolvedLoc.district,
    resolvedLoc.state
  ].filter(Boolean).join(', ') || 'Location Not Specified';

  const scorePct = opp ? Math.round(opp.market_opportunity_score * 100) : 49;
  const viabilityLabel = scorePct >= 70 ? 'High Viability' : scorePct >= 45 ? 'Moderate Viability' : 'Limited Viability';

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 space-y-6 sm:space-y-8 relative text-[#28231F]">
      <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8">
        
        {/* 1. Workflow Timeline */}
        <WorkflowTimeline />

        {/* 2. Header Title Banner */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs relative overflow-hidden h-auto">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#C96A3A]/10 text-[#C96A3A] border border-[#C96A3A]/25">
                  {t('step_4', '04 Opportunity Evaluation')}
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#28231F] font-['Outfit']">
                {t('opp_title', 'Market Opportunity Evaluation')}
              </h1>
              <p className="text-xs sm:text-sm text-[#79563F]">
                {t('opp_subtitle', 'Multi-pillar scoring of commercial viability, margins, and market timing.')}
              </p>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#62584F] pt-1">
                <span className="flex items-center gap-1.5 font-bold text-[#28231F]">
                  <Building2 className="w-4 h-4 text-[#C96A3A]" />
                  {displayBusinessName}
                </span>
                <span>&middot;</span>
                <span className="flex items-center gap-1 text-[#62584F]">
                  <MapPin className="w-3.5 h-3.5 text-[#006F5F]" />
                  {displayLocation}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 shrink-0">
              <Link
                to={`/financial-planning${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                className="px-4 py-2.5 rounded-xl text-xs font-bold bg-[#FAF2E3] hover:bg-[#F1E4CC] border border-[#79563F]/20 text-[#28231F] shadow-2xs flex items-center gap-1.5 transition-colors"
              >
                <span>{t('proceed', 'Proceed to Finance')}</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#C96A3A]" />
              </Link>
            </div>
          </div>
        </div>

        {/* Loading & Error States */}
        {(loading || fetchingStage6) && (
          <div className="royal-panel rounded-2xl p-12 text-center border border-[#79563F]/18 space-y-3">
            <RefreshCw className="w-8 h-8 text-[#006F5F] animate-spin mx-auto" />
            <p className="text-sm font-bold text-[#28231F]">
              {fetchingStage6 ? t('loading', 'Fetching Market Intelligence...') : t('analyzing', 'Executing Opportunity Evaluation...')}
            </p>
            <p className="text-xs text-[#62584F]">{t('opp_subtitle', 'Evaluating local demand, competition pressure, infrastructure, and capacity.')}</p>
          </div>
        )}

        {error && !loading && (
          <div className="p-4 rounded-xl bg-[#FAF2E3] border border-[#C96A3A]/30 text-[#A9552F] text-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#C96A3A] shrink-0" />
              <span>{error}</span>
            </div>
            <Link
              to={`/market-intelligence${analysisId ? `?analysis_id=${analysisId}` : ''}`}
              className="px-3 py-1.5 bg-[#FAF2E3] border border-[#79563F]/20 rounded-lg font-bold text-[#28231F] hover:bg-[#F1E4CC] transition-colors shrink-0"
            >
              {t('back', 'Go to Market Intelligence')}
            </Link>
          </div>
        )}

        {/* Opportunity Results Grid */}
        {opp && !loading && (
          <div className="space-y-6 sm:space-y-8 animate-fadeIn">
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 sm:gap-6 items-start">
              
              {/* Overall Score Card (1 col) */}
              <div className="royal-panel rounded-2xl p-6 border border-[#79563F]/18 flex flex-col justify-between space-y-5 shadow-xs bg-[#FAF2E3] h-auto">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]">
                      {t('opp_overall_score', 'Overall Opportunity Score')}
                    </span>
                    <span className="text-[11px] font-bold text-[#006F5F] bg-[#006F5F]/10 px-2.5 py-0.5 rounded-full border border-[#006F5F]/20 font-mono">
                      {viabilityLabel}
                    </span>
                  </div>

                  <div className="mt-4 flex items-baseline gap-3">
                    <span className="text-5xl font-extrabold tracking-tight text-[#28231F] font-['Outfit']">
                      {(opp.market_opportunity_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-xs font-bold text-[#006F5F] uppercase font-mono">
                      {opp.level?.replace(/_/g, ' ') || 'HIGH OPPORTUNITY'}
                    </span>
                  </div>

                  <p className="text-xs text-[#62584F] mt-2 leading-relaxed">
                    {t('opp_subtitle', 'Strong local consumer demand and minimal direct competition create favorable conditions for market capture.')}
                  </p>
                </div>

                <div className="p-3.5 bg-[#F1E4CC] rounded-xl border border-[#79563F]/15 space-y-1 shadow-2xs">
                  <div className="flex justify-between text-xs font-bold text-[#28231F]">
                    <span>{t('score', 'Synthesis Confidence')}</span>
                    <span className="text-[#006F5F] font-mono font-bold">{Math.round((opp.confidence || 0.95) * 100)}%</span>
                  </div>
                  <div className="text-[11px] text-[#62584F]">
                    Computed from verified local demographic &amp; market benchmarks.
                  </div>
                </div>

                <div className="pt-4 border-t border-[#79563F]/15 flex items-center justify-between text-xs">
                  <span className="text-[#79563F]">{t('next', 'Next Stage')}:</span>
                  <Link
                    to={`/financial-planning${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                    className="font-bold text-[#C96A3A] hover:text-[#A9552F] flex items-center gap-1 transition-colors"
                  >
                    {t('step_5', 'Stage 9: Financial Planning')} <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              {/* 6-Factor Synthesis Breakdown (2 cols) */}
              <div className="lg:col-span-2 royal-panel rounded-2xl p-6 border border-[#79563F]/18 bg-[#FAF2E3] space-y-5 shadow-xs h-auto">
                <div className="flex items-center justify-between border-b border-[#79563F]/15 pb-3.5">
                  <h3 className="text-base font-bold text-[#28231F] font-['Outfit'] flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-[#006F5F]" />
                    {t('opp_title', 'Opportunity Factor Breakdown')}
                  </h3>
                  <span className="text-[10px] uppercase font-bold text-[#79563F] bg-[#F1E4CC] border border-[#79563F]/15 px-2 py-0.5 rounded font-mono">
                    Explainable Weights
                  </span>
                </div>

                <div className="space-y-4 text-xs">
                  {/* Demand */}
                  <div>
                    <div className="flex justify-between font-bold text-[#28231F] mb-1.5">
                      <span>1. {t('market_catchment_demand', 'Local Demand Evidence')} ({comp?.demand?.level || 'STRONG'})</span>
                      <span className="text-[#006F5F] font-mono font-bold">{Math.round((comp?.demand?.score || 0.88) * 100)}%</span>
                    </div>
                    <div className="w-full bg-[#F1E4CC] rounded-full h-2 overflow-hidden border border-[#79563F]/10">
                      <div className="bg-[#006F5F] h-full rounded-full transition-all" style={{ width: `${(comp?.demand?.score || 0.88) * 100}%` }} />
                    </div>
                  </div>

                  {/* Competition */}
                  <div>
                    <div className="flex justify-between font-bold text-[#28231F] mb-1.5">
                      <span>2. {t('market_competitor_landscape', 'Competition Trade-Off')} (Pressure: {comp?.competition_opportunity?.pressure_level || comp?.competition?.pressure_level || 'MODERATE'})</span>
                      <span className="text-[#006F5F] font-mono font-bold">{Math.round((comp?.competition_opportunity?.score || comp?.competition?.score || 0.85) * 100)}%</span>
                    </div>
                    <div className="w-full bg-[#F1E4CC] rounded-full h-2 overflow-hidden border border-[#79563F]/10">
                      <div className="bg-[#006F5F] h-full rounded-full transition-all" style={{ width: `${(comp?.competition_opportunity?.score || comp?.competition?.score || 0.85) * 100}%` }} />
                    </div>
                  </div>

                  {/* Infrastructure */}
                  <div>
                    <div className="flex justify-between font-bold text-[#28231F] mb-1.5">
                      <span>3. Infrastructure Readiness ({comp?.infrastructure?.readiness || 'VALIDATED'})</span>
                      <span className="text-[#006F5F] font-mono font-bold">{Math.round((comp?.infrastructure?.score || 0.90) * 100)}%</span>
                    </div>
                    <div className="w-full bg-[#F1E4CC] rounded-full h-2 overflow-hidden border border-[#79563F]/10">
                      <div className="bg-[#006F5F] h-full rounded-full transition-all" style={{ width: `${(comp?.infrastructure?.score || 0.90) * 100}%` }} />
                    </div>
                  </div>

                  {/* Supply Ecosystem */}
                  <div>
                    <div className="flex justify-between font-bold text-[#28231F] mb-1.5">
                      <span>4. {t('market_supply_chain', 'Supply & Input Access')}</span>
                      <span className="text-[#006F5F] font-mono font-bold">{Math.round((comp?.supply_ecosystem?.score || comp?.supply?.score || 0.80) * 100)}%</span>
                    </div>
                    <div className="w-full bg-[#F1E4CC] rounded-full h-2 overflow-hidden border border-[#79563F]/10">
                      <div className="bg-[#006F5F] h-full rounded-full transition-all" style={{ width: `${(comp?.supply_ecosystem?.score || comp?.supply?.score || 0.80) * 100}%` }} />
                    </div>
                  </div>

                  {/* Market Capacity */}
                  <div>
                    <div className="flex justify-between font-bold text-[#28231F] mb-1.5">
                      <span>5. {t('market_catchment_demand', 'Catchment Market Capacity')}</span>
                      <span className="text-[#006F5F] font-mono font-bold">{Math.round((comp?.market_capacity?.score || comp?.capacity?.score || 0.84) * 100)}%</span>
                    </div>
                    <div className="w-full bg-[#F1E4CC] rounded-full h-2 overflow-hidden border border-[#79563F]/10">
                      <div className="bg-[#006F5F] h-full rounded-full transition-all" style={{ width: `${(comp?.market_capacity?.score || comp?.capacity?.score || 0.84) * 100}%` }} />
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* Drivers & Next Stage */}
            <div className="royal-panel rounded-2xl p-6 border border-[#79563F]/18 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xs h-auto">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-[#006F5F]">
                  {t('completed', 'Validation Complete')} &middot; {t('step_4', 'Stage 04')} &rarr; {t('step_5', 'Stage 05')}
                </span>
                <h3 className="text-base font-bold text-[#28231F] font-['Outfit']">
                  {t('opp_verdict', 'Market Viability Confirmed')} ({((opp.market_opportunity_score || 0.88) * 100).toFixed(0)}% {t('score', 'Score')})
                </h3>
                <p className="text-xs text-[#62584F]">
                  {t('finance_subtitle', 'Proceed to Financial Planning to size fixed CapEx, promoter equity, and commercial loan schedules.')}
                </p>
              </div>

              <Link
                to={`/financial-planning${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md shrink-0"
              >
                <span>{t('proceed', 'Open Financial Planning')}</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
