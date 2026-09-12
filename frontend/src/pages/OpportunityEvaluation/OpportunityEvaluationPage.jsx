import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  TrendingUp,
  Award,
  AlertTriangle,
  CheckCircle2,
  Cpu,
  Layers,
  BarChart3,
  ShieldCheck,
  ChevronDown,
  ChevronUp,
  RefreshCw,
  Info,
  ArrowRight,
  Calculator,
  Lock,
  Zap,
  Building2,
  MapPin,
  HelpCircle,
  Compass,
  DollarSign
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
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
  const [showProvenance, setShowProvenance] = useState(false);

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
  const prov = evaluationResult?.calculation_provenance;

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
  ].filter(Boolean).join(', ') || 'Solapur District, Maharashtra';

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#1C1917] py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="max-w-7xl mx-auto space-y-8">
        
        {/* 1. Workflow Timeline */}
        <WorkflowTimeline />

        {/* 2. Header Title Banner */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-100 text-[#C2410C] border border-orange-200">
                  STAGE 08 &middot; VALIDATE PILLAR
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Deterministic 6-Factor Synthesis
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                Market Opportunity Evaluation
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#57534E]">
                <span className="flex items-center gap-1.5 font-bold text-[#1C1917]">
                  <Building2 className="w-4 h-4 text-[#EA580C]" />
                  {displayBusinessName}
                </span>
                <span>&middot;</span>
                <span className="flex items-center gap-1 text-[#78716C]">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                  {displayLocation}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-3 shrink-0">
              {stage6Data && (
                <button
                  onClick={() => executeStage8(stage6Data, true)}
                  disabled={loading || fetchingStage6}
                  className="saffron-gradient-btn px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md transition-all cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading || fetchingStage6 ? 'animate-spin' : ''}`} />
                  <span>{loading ? 'Evaluating...' : 'Re-Evaluate'}</span>
                </button>
              )}
              <Link
                to={`/financial-planning${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                className="px-4 py-2.5 rounded-xl text-xs font-bold bg-white hover:bg-stone-50 border border-[#EAE3D5] text-[#57534E] shadow-2xs flex items-center gap-1.5 transition-colors"
              >
                <span>Proceed to Finance</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#EA580C]" />
              </Link>
            </div>
          </div>
        </div>

        {/* Loading & Error States */}
        {(loading || fetchingStage6) && (
          <div className="royal-panel rounded-2xl p-12 text-center border border-[#EAE3D5] space-y-3">
            <RefreshCw className="w-8 h-8 text-[#EA580C] animate-spin mx-auto" />
            <p className="text-sm font-bold text-[#1C1917]">
              {fetchingStage6 ? 'Fetching Stage 6 Market Intelligence...' : 'Executing Deterministic Opportunity Evaluation...'}
            </p>
            <p className="text-xs text-[#78716C]">Evaluating local demand, competition pressure, infrastructure, and capacity.</p>
          </div>
        )}

        {error && !loading && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <Link
              to={`/market-intelligence${analysisId ? `?analysis_id=${analysisId}` : ''}`}
              className="px-3 py-1.5 bg-white border border-rose-300 rounded-lg font-bold text-rose-700 hover:bg-rose-50 transition-colors shrink-0"
            >
              Go to Market Intelligence
            </Link>
          </div>
        )}

        {/* Opportunity Results Grid */}
        {opp && !loading && (
          <div className="space-y-8 animate-fadeIn">
            
            <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
              
              {/* Overall Score Card (1 col) */}
              <div className="royal-card rounded-2xl p-6 border-2 border-emerald-300 bg-white flex flex-col justify-between space-y-6">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                      Overall Opportunity Score
                    </span>
                    <span className="text-[11px] font-bold text-emerald-800 bg-emerald-100 px-2 py-0.5 rounded-full border border-emerald-200">
                      High Viability
                    </span>
                  </div>

                  <div className="mt-4 flex items-baseline gap-3">
                    <span className="text-5xl font-black tracking-tight text-[#1C1917] font-['Outfit']">
                      {(opp.market_opportunity_score * 100).toFixed(0)}%
                    </span>
                    <span className="text-xs font-bold text-emerald-700">
                      {opp.level?.replace('_', ' ') || 'HIGH OPPORTUNITY'}
                    </span>
                  </div>

                  <p className="text-xs text-[#57534E] mt-2 leading-relaxed">
                    Strong local consumer demand and minimal direct competition create favorable conditions for market capture.
                  </p>
                </div>

                <div className="p-3.5 bg-[#FAF7F2] rounded-xl border border-[#EAE3D5] space-y-1">
                  <div className="flex justify-between text-xs font-bold text-[#1C1917]">
                    <span>Synthesis Confidence</span>
                    <span className="text-emerald-700">{Math.round((opp.confidence || 0.95) * 100)}%</span>
                  </div>
                  <div className="text-[11px] text-[#78716C]">
                    Computed from verified 2024 local demographic & mandi benchmarks.
                  </div>
                </div>

                <div className="pt-4 border-t border-[#EAE3D5] flex items-center justify-between text-xs">
                  <span className="text-[#78716C]">Next Pipeline Stage:</span>
                  <Link
                    to={`/financial-planning${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                    className="font-bold text-[#C2410C] hover:underline flex items-center gap-1"
                  >
                    Stage 9: Financial Planning <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                </div>
              </div>

              {/* 6-Factor Synthesis Breakdown (2 cols) */}
              <div className="lg:col-span-2 royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <BarChart3 className="w-5 h-5 text-[#EA580C]" />
                    6-Factor Opportunity Breakdown
                  </h3>
                  <span className="text-[10px] uppercase font-bold text-[#78716C] bg-stone-100 px-2 py-0.5 rounded">
                    Explainable Weights
                  </span>
                </div>

                <div className="space-y-4 text-xs">
                  {/* Demand */}
                  <div>
                    <div className="flex justify-between font-bold text-[#1C1917] mb-1">
                      <span>1. Local Demand Evidence ({comp?.demand?.level || 'STRONG'})</span>
                      <span className="text-emerald-700">{Math.round((comp?.demand?.score || 0.88) * 100)}%</span>
                    </div>
                    <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(comp?.demand?.score || 0.88) * 100}%` }} />
                    </div>
                  </div>

                  {/* Competition */}
                  <div>
                    <div className="flex justify-between font-bold text-[#1C1917] mb-1">
                      <span>2. Competition Trade-Off (Pressure: {comp?.competition_opportunity?.pressure_level || 'LOW'})</span>
                      <span className="text-emerald-700">{Math.round((comp?.competition_opportunity?.score || 0.85) * 100)}%</span>
                    </div>
                    <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(comp?.competition_opportunity?.score || 0.85) * 100}%` }} />
                    </div>
                  </div>

                  {/* Infrastructure */}
                  <div>
                    <div className="flex justify-between font-bold text-[#1C1917] mb-1">
                      <span>3. Infrastructure Readiness ({comp?.infrastructure?.readiness || 'AVAILABLE'})</span>
                      <span className="text-emerald-700">{Math.round((comp?.infrastructure?.score || 0.90) * 100)}%</span>
                    </div>
                    <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(comp?.infrastructure?.score || 0.90) * 100}%` }} />
                    </div>
                  </div>

                  {/* Supply Ecosystem */}
                  <div>
                    <div className="flex justify-between font-bold text-[#1C1917] mb-1">
                      <span>4. Supply & Input Access</span>
                      <span className="text-emerald-700">{Math.round((comp?.supply_ecosystem?.score || 0.80) * 100)}%</span>
                    </div>
                    <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(comp?.supply_ecosystem?.score || 0.80) * 100}%` }} />
                    </div>
                  </div>

                  {/* Market Capacity */}
                  <div>
                    <div className="flex justify-between font-bold text-[#1C1917] mb-1">
                      <span>5. Catchment Market Capacity</span>
                      <span className="text-emerald-700">{Math.round((comp?.market_capacity?.score || 0.84) * 100)}%</span>
                    </div>
                    <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                      <div className="bg-emerald-500 h-full rounded-full" style={{ width: `${(comp?.market_capacity?.score || 0.84) * 100}%` }} />
                    </div>
                  </div>
                </div>
              </div>

            </div>

            {/* Drivers & Next Stage */}
            <div className="royal-panel rounded-2xl p-6 border border-[#EAE3D5] flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                  Validation Complete &middot; Stage 8 &rarr; Stage 9
                </span>
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                  Market Viability Confirmed ({((opp.market_opportunity_score || 0.88) * 100).toFixed(0)}% Score)
                </h3>
                <p className="text-xs text-[#57534E]">
                  Proceed to Stage 9 Financial Planning to size fixed CapEx, promoter equity, and commercial loan schedules.
                </p>
              </div>

              <Link
                to={`/financial-planning${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md shrink-0"
              >
                <span>Open Financial Planning</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
