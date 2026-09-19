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

// Stage Name Formatter for Provenance
const formatStageName = (stageCode) => {
  const code = (stageCode || '').toUpperCase();
  if (code.includes('STAGE_6') || code.includes('STAGE6')) return 'Stage 6 • Market Intelligence';
  if (code.includes('STAGE_8') || code.includes('STAGE8')) return 'Stage 8 • Opportunity Evaluation';
  if (code.includes('STAGE_9') || code.includes('STAGE9')) return 'Stage 9 • Financial Model';
  if (code.includes('STAGE_10') || code.includes('STAGE10')) return 'Stage 10 • Entrepreneur Readiness';
  if (code.includes('STAGE_11') || code.includes('STAGE11')) return 'Stage 11 • Multi-Vector Risk';
  if (code.includes('STAGE_12') || code.includes('STAGE12')) return 'Stage 12 • Feasibility Engine';
  if (code.includes('STAGE_3') || code.includes('STAGE3')) return 'Stage 3 • Business Profile';
  return stageCode || 'Stage 12 • Feasibility';
};

export default function SWOTPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const {
    sessionId,
    analysisId,
    businessId,
    businessName,
    updateWorkflowState,
    completedStages,
  } = useWorkflow();

  const [loading, setLoading] = useState(true);
  const [loadingStep, setLoadingStep] = useState('REQUESTING'); // REQUESTING -> ANALYZING -> GENERATING_SWOT -> COMPLETE
  const [swotData, setSwotData] = useState(null);
  const [error, setError] = useState(null);
  const [expandedItems, setExpandedItems] = useState({});
  const [activeTab, setActiveTab] = useState('all'); // 'all', 'strengths', 'weaknesses', 'opportunities', 'threats'

  const effectiveAnalysisId = location.state?.analysisId || analysisId || sessionStorage.getItem('kalpa_analysis_id');
  const effectiveSessionId = location.state?.sessionId || sessionId || sessionStorage.getItem('kalpa_session_id');

  const hasFetchedRef = useRef(false);

  const fetchSWOTAnalysis = useCallback(async (isRetry = false) => {
    setLoading(true);
    setError(null);
    setLoadingStep('REQUESTING');

    // Simulate progress steps for smooth UX
    const stepTimer1 = setTimeout(() => setLoadingStep('ANALYZING'), 600);
    const stepTimer2 = setTimeout(() => setLoadingStep('GENERATING_SWOT'), 1500);

    try {
      console.log('[STAGE 13 SWOT] Requesting analysis for:', {
        analysisId: effectiveAnalysisId,
        sessionId: effectiveSessionId,
        forceRefresh: isRetry
      });

      const payload = {
        analysis_id: effectiveAnalysisId || undefined,
        session_id: effectiveSessionId || undefined,
        business_profile: location.state?.businessProfile || undefined,
        location_profile: location.state?.locationProfile || undefined,
        market_analysis: location.state?.marketAnalysis || undefined,
        opportunity_result: location.state?.opportunityResult || undefined,
        financial_analysis: location.state?.financialAnalysis || undefined,
        entrepreneur_readiness: location.state?.entrepreneurReadiness || undefined,
        risk_analysis: location.state?.riskAnalysis || undefined,
        feasibility_result: location.state?.feasibilityResult || undefined,
        force_refresh: isRetry
      };

      const response = await apiService.swot.analyze(payload);
      console.log('[STAGE 13 SWOT] Analysis response received:', response);

      if (response.status === 'FAILED') {
        setError({
          errorCode: response.error_code || 'SWOT_LLM_UNAVAILABLE',
          message: response.message || 'Business analysis is ready, but the strategic SWOT could not be generated right now.',
          retryable: response.retryable ?? true
        });
      } else {
        setSwotData(response);

        // Auto-expand all items by default
        const initialExpanded = {};
        ['strengths', 'weaknesses', 'opportunities', 'threats'].forEach(cat => {
          (response.swot?.[cat] || []).forEach(item => {
            if (item && item.id) {
              initialExpanded[item.id] = true;
            }
          });
        });
        setExpandedItems(initialExpanded);

        // Mark Stage 13 completed in workflow context
        if (response.status === 'COMPLETED' || response.status === 'complete') {
          if (!completedStages?.includes(13)) {
            updateWorkflowState({
              completedStages: Array.from(new Set([...(completedStages || []), 13])),
              currentStage: 13,
              availableStages: [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13, 14],
            });
          }
        }
      }
    } catch (err) {
      console.error('[STAGE 13 SWOT] Error fetching SWOT:', err);
      setError({
        errorCode: 'SWOT_API_ERROR',
        message: err.message || 'Failed to communicate with Dynamic SWOT service. Please check connection and retry.',
        retryable: true
      });
    } finally {
      clearTimeout(stepTimer1);
      clearTimeout(stepTimer2);
      setLoading(false);
      setLoadingStep('COMPLETE');
    }
  }, [effectiveAnalysisId, effectiveSessionId, location.state]);

  // Initial load once on mount
  useEffect(() => {
    if (!hasFetchedRef.current) {
      hasFetchedRef.current = true;
      fetchSWOTAnalysis();
    }
  }, [fetchSWOTAnalysis]);

  const toggleItem = (id) => {
    setExpandedItems(prev => ({
      ...prev,
      [id]: !prev[id]
    }));
  };

  const getPriorityBadgeClass = (priority) => {
    switch ((priority || '').toUpperCase()) {
      case 'HIGH':
        return 'bg-rose-50 text-rose-700 border-rose-200';
      case 'MEDIUM':
        return 'bg-amber-50 text-amber-700 border-amber-200';
      case 'LOW':
        return 'bg-stone-50 text-stone-600 border-stone-200';
      default:
        return 'bg-orange-50 text-orange-700 border-orange-200';
    }
  };

  const getStatusBadgeClass = (status) => {
    switch ((status || '').toUpperCase()) {
      case 'KNOWN':
        return 'bg-emerald-50 text-emerald-700 border-emerald-200';
      case 'INFERRED':
        return 'bg-blue-50 text-blue-700 border-blue-200';
      case 'DATA_GAP':
        return 'bg-purple-50 text-purple-700 border-purple-200';
      default:
        return 'bg-stone-50 text-stone-700 border-stone-200';
    }
  };

  const isFallbackMode = swotData?.generation?.mode === 'DETERMINISTIC_FALLBACK';
  const isSarvamMode = swotData?.generation?.mode === 'SARVAM_LLM' || (!swotData?.generation && swotData?.model_metadata?.provider === 'sarvam');

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-stone-900 font-sans pb-24">
      {/* Top Breadcrumb & Workflow Stepper */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-30 shadow-xs">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5">
          <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
            <div className="flex items-center space-x-3">
              <Link
                to="/feasibility"
                className="p-1.5 rounded-lg border border-stone-200 hover:bg-stone-50 text-stone-600 transition flex items-center cursor-pointer"
                title="Back to Feasibility"
              >
                <ArrowLeft className="w-4 h-4" />
              </Link>
              <div>
                <div className="flex items-center space-x-2">
                  <span className="px-2 py-0.5 rounded text-[10px] font-bold tracking-wider uppercase bg-[#EA580C]/10 text-[#EA580C]">
                    STAGE 13
                  </span>
                  <span className="text-xs font-semibold text-stone-500">
                    Strategic Interpretation & Advisory
                  </span>
                </div>
                <h1 className="text-lg font-bold text-stone-900 font-['Outfit']">
                  Business SWOT & Strategic Roadmap
                </h1>
              </div>
            </div>

            {/* Workflow Stage Progress Indicator */}
            <div className="flex items-center space-x-1.5 overflow-x-auto py-1 text-xs">
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-medium">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Market (6/8)</span>
              </span>
              <span className="text-stone-300">›</span>
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-medium">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Finance (9)</span>
              </span>
              <span className="text-stone-300">›</span>
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-medium">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Entrepreneur (10)</span>
              </span>
              <span className="text-stone-300">›</span>
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-medium">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Risk (11)</span>
              </span>
              <span className="text-stone-300">›</span>
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-emerald-50 text-emerald-700 font-medium">
                <Check className="w-3.5 h-3.5 text-emerald-600" />
                <span>Feasibility (12)</span>
              </span>
              <span className="text-stone-300">›</span>
              <span className="flex items-center space-x-1 px-2.5 py-1 rounded-md bg-[#EA580C] text-white font-bold shadow-xs">
                <span>SWOT (13) ●</span>
              </span>
              <span className="text-stone-300">›</span>
              <Link to="/dpr" className="flex items-center space-x-1 px-2 py-1 rounded-md bg-stone-100 text-stone-600 hover:text-[#EA580C]">
                <FileText className="w-3 h-3" />
                <span>DPR (14)</span>
              </Link>
            </div>
          </div>
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-8">
        
        {/* Loading State with Stage Feedback */}
        {loading && (
          <div className="bg-white rounded-3xl p-12 border border-stone-200 shadow-sm text-center space-y-5">
            <div className="w-12 h-12 border-3 border-[#EA580C] border-t-transparent rounded-full animate-spin mx-auto" />
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-stone-900 font-['Outfit']">
                {loadingStep === 'REQUESTING' && 'Connecting to Stage 13 Dynamic SWOT Agent...'}
                {loadingStep === 'ANALYZING' && 'Ingesting Verified Facts from Stages 6, 8, 9, 10, 11 & 12...'}
                {loadingStep === 'GENERATING_SWOT' && 'Synthesizing Strategic SWOT & Cross-Engine Relationships...'}
                {loadingStep === 'COMPLETE' && 'Finalizing Strategic Roadmap...'}
              </h3>
              <p className="text-xs text-stone-500 max-w-md mx-auto leading-relaxed">
                Correlating market demand, financial DSCR, promoter skill readiness, and multi-vector risk mitigations without data fabrication.
              </p>
            </div>

            <div className="flex justify-center items-center space-x-2 text-[11px] text-stone-400 pt-2">
              <span className={`px-2 py-0.5 rounded ${loadingStep === 'REQUESTING' ? 'bg-orange-100 text-orange-800 font-bold' : 'bg-stone-100'}`}>1. Ingest</span>
              <span>→</span>
              <span className={`px-2 py-0.5 rounded ${loadingStep === 'ANALYZING' ? 'bg-orange-100 text-orange-800 font-bold' : 'bg-stone-100'}`}>2. Normalize</span>
              <span>→</span>
              <span className={`px-2 py-0.5 rounded ${loadingStep === 'GENERATING_SWOT' ? 'bg-orange-100 text-orange-800 font-bold' : 'bg-stone-100'}`}>3. Synthesize</span>
            </div>
          </div>
        )}

        {/* Error / LLM Unavailable State */}
        {!loading && error && (
          <div className="bg-amber-50/80 border-2 border-amber-300 rounded-3xl p-8 space-y-6 shadow-sm">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-amber-100 rounded-2xl text-amber-800 flex-shrink-0">
                <AlertOctagon className="w-8 h-8" />
              </div>
              <div className="space-y-2">
                <div className="flex items-center space-x-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-amber-200 text-amber-900">
                    {error.errorCode || 'SERVICE UNAVAILABLE'}
                  </span>
                  <span className="text-xs text-amber-800 font-medium">Stage 13 Strategic Agent</span>
                </div>
                <h3 className="text-xl font-bold text-amber-950 font-['Outfit']">
                  Dynamic SWOT Analysis Notice
                </h3>
                <p className="text-xs text-amber-900/90 max-w-2xl leading-relaxed">
                  {error.message}
                </p>
                <div className="p-3.5 bg-white/80 rounded-xl border border-amber-200 text-xs text-stone-700 space-y-1">
                  <div className="font-semibold text-stone-900">Deterministic Engine Status:</div>
                  <div>✓ All upstream calculations (Stages 6–12) remain intact and persisted in the database.</div>
                  <div>✓ You can retry SWOT analysis or trigger a deterministic fallback synthesis.</div>
                </div>
              </div>
            </div>

            {error.retryable && (
              <div className="flex items-center space-x-3 pt-2">
                <button
                  onClick={() => fetchSWOTAnalysis(true)}
                  className="px-5 py-2.5 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-sm cursor-pointer"
                >
                  <RefreshCw className="w-4 h-4" />
                  <span>Retry SWOT Analysis</span>
                </button>
                <Link
                  to="/feasibility"
                  className="px-4 py-2.5 bg-white border border-stone-300 hover:bg-stone-50 text-stone-700 rounded-xl text-xs font-bold transition"
                >
                  Return to Feasibility
                </Link>
              </div>
            )}
          </div>
        )}

        {/* Blocked / Not Feasible State */}
        {!loading && swotData?.status === 'BLOCKED_NOT_FEASIBLE' && (
          <div className="bg-red-50 border-2 border-red-200 rounded-3xl p-8 space-y-6 shadow-sm">
            <div className="flex items-start space-x-4">
              <div className="p-3 bg-red-100 rounded-2xl text-red-800 flex-shrink-0">
                <AlertTriangle className="w-8 h-8" />
              </div>
              <div className="space-y-2">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-red-200 text-red-900">
                  STAGE 12: YES-PATHWAY GATED
                </span>
                <h3 className="text-xl font-bold text-red-950 font-['Outfit']">
                  SWOT Gated for Non-Viable Venture
                </h3>
                <p className="text-xs text-red-800 max-w-2xl leading-relaxed">
                  {swotData.message || 'Stage 13 Dynamic SWOT is reserved for viable ventures. Since Stage 12 concluded as NOT_FEASIBLE, please review the recommended business pivots.'}
                </p>
              </div>
            </div>
            <Link to="/feasibility">
              <button className="px-5 py-2.5 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition flex items-center space-x-2 cursor-pointer">
                <span>View Feasibility & Pivot Advisor</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </Link>
          </div>
        )}

        {/* Completed Strategic SWOT Report */}
        {!loading && swotData && (swotData.status === 'COMPLETED' || swotData.status === 'complete') && (
          <div className="space-y-8 animate-fadeIn">
            
            {/* Top Enterprise Advisory Banner */}
            <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-sm flex flex-col md:flex-row md:items-center justify-between gap-6">
              <div className="space-y-2">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center space-x-1">
                    <CheckCircle2 className="w-3 h-3 text-emerald-600" />
                    <span>STAGE 12: VIABLE VENTURE</span>
                  </span>

                  {isSarvamMode && (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-[#EA580C]/10 text-[#EA580C] border border-[#EA580C]/20 flex items-center space-x-1">
                      <Cpu className="w-3 h-3 text-[#EA580C]" />
                      <span>SARVAM 105B AI SYNTHESIS</span>
                    </span>
                  )}

                  {isFallbackMode && (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-blue-50 text-blue-800 border border-blue-200 flex items-center space-x-1">
                      <Database className="w-3 h-3 text-blue-600" />
                      <span>DETERMINISTIC EVIDENCE SYNTHESIS</span>
                    </span>
                  )}

                  {swotData.confidence > 0 && (
                    <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-purple-50 text-purple-800 border border-purple-200">
                      SWOT Confidence: {(swotData.confidence * 100).toFixed(0)}%
                    </span>
                  )}
                </div>

                <h2 className="text-2xl font-bold text-stone-900 font-['Outfit']">
                  {swotData.business_name || businessName || 'Rural Micro-Enterprise'}
                </h2>

                <div className="flex items-center space-x-4 text-xs text-stone-600">
                  <span className="flex items-center space-x-1">
                    <MapPin className="w-3.5 h-3.5 text-stone-400" />
                    <span>{swotData.location || 'Local Cluster'}</span>
                  </span>
                  <span className="text-stone-300">•</span>
                  <span className="flex items-center space-x-1">
                    <Layers className="w-3.5 h-3.5 text-stone-400" />
                    <span>Grounded in Stages 6–12 Evidence</span>
                  </span>
                </div>
              </div>

              <div className="flex items-center space-x-3">
                <button
                  onClick={() => fetchSWOTAnalysis(true)}
                  className="px-4 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl text-xs font-bold transition flex items-center space-x-1.5 cursor-pointer"
                  title="Regenerate Strategic SWOT"
                >
                  <RefreshCw className="w-3.5 h-3.5" />
                  <span>Refresh SWOT</span>
                </button>
                <Link to="/dpr">
                  <button className="px-5 py-2.5 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-sm cursor-pointer">
                    <span>Generate Bank DPR (Stage 14)</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </Link>
              </div>
            </div>

            {/* Strategic Summary & Executive Synthesis */}
            {(swotData.strategic_summary || swotData.swot?.executive_summary) && (
              <div className="bg-gradient-to-br from-stone-900 via-stone-800 to-stone-900 text-white rounded-3xl p-6 sm:p-8 shadow-lg space-y-6">
                <div className="flex items-center justify-between">
                  <div className="space-y-1">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-orange-400 flex items-center space-x-1">
                      <Compass className="w-3.5 h-3.5" />
                      <span>EXECUTIVE STRATEGIC DIRECTION</span>
                    </span>
                    <h3 className="text-xl font-bold font-['Outfit']">
                      What This Means for Your Business
                    </h3>
                  </div>
                </div>

                <p className="text-sm text-stone-300 leading-relaxed max-w-4xl">
                  {swotData.swot?.executive_summary || swotData.strategic_summary?.business_position}
                </p>

                {swotData.swot?.strategic_direction && swotData.swot.strategic_direction !== swotData.swot.executive_summary && (
                  <div className="p-3.5 bg-white/5 rounded-xl border border-white/10 text-xs text-stone-300">
                    <strong className="text-orange-300">Strategic Direction: </strong>
                    {swotData.swot.strategic_direction}
                  </div>
                )}

                {swotData.strategic_summary && (
                  <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 pt-2 border-t border-stone-700/60">
                    <div className="bg-white/5 rounded-2xl p-4 border border-white/10 space-y-1.5">
                      <span className="text-[10px] font-bold text-emerald-400 uppercase tracking-wide flex items-center space-x-1">
                        <CheckCircle2 className="w-3 h-3" />
                        <span>Key Advantage</span>
                      </span>
                      <p className="text-xs text-stone-200 leading-snug">
                        {swotData.strategic_summary.key_advantage}
                      </p>
                    </div>

                    <div className="bg-white/5 rounded-2xl p-4 border border-white/10 space-y-1.5">
                      <span className="text-[10px] font-bold text-amber-400 uppercase tracking-wide flex items-center space-x-1">
                        <AlertTriangle className="w-3 h-3" />
                        <span>Main Constraint</span>
                      </span>
                      <p className="text-xs text-stone-200 leading-snug">
                        {swotData.strategic_summary.main_constraint}
                      </p>
                    </div>

                    <div className="bg-white/5 rounded-2xl p-4 border border-white/10 space-y-1.5">
                      <span className="text-[10px] font-bold text-blue-400 uppercase tracking-wide flex items-center space-x-1">
                        <Lightbulb className="w-3 h-3" />
                        <span>Top Growth Opportunity</span>
                      </span>
                      <p className="text-xs text-stone-200 leading-snug">
                        {swotData.strategic_summary.biggest_opportunity}
                      </p>
                    </div>

                    <div className="bg-white/5 rounded-2xl p-4 border border-white/10 space-y-1.5">
                      <span className="text-[10px] font-bold text-rose-400 uppercase tracking-wide flex items-center space-x-1">
                        <ShieldAlert className="w-3 h-3" />
                        <span>Critical Threat</span>
                      </span>
                      <p className="text-xs text-stone-200 leading-snug">
                        {swotData.strategic_summary.biggest_threat}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* SWOT 4-Quadrant Filter Navigation */}
            <div className="flex items-center space-x-2 border-b border-stone-200 pb-2 overflow-x-auto">
              {[
                { id: 'all', label: 'All 4 Quadrants' },
                { id: 'strengths', label: `Strengths (${swotData.swot?.strengths?.length || 0})`, color: 'text-emerald-700' },
                { id: 'weaknesses', label: `Weaknesses (${swotData.swot?.weaknesses?.length || 0})`, color: 'text-amber-700' },
                { id: 'opportunities', label: `Opportunities (${swotData.swot?.opportunities?.length || 0})`, color: 'text-blue-700' },
                { id: 'threats', label: `Threats (${swotData.swot?.threats?.length || 0})`, color: 'text-rose-700' },
              ].map(tab => (
                <button
                  key={tab.id}
                  onClick={() => setActiveTab(tab.id)}
                  className={`px-4 py-2 rounded-xl text-xs font-bold transition whitespace-nowrap cursor-pointer ${
                    activeTab === tab.id
                      ? 'bg-stone-900 text-white shadow-xs'
                      : 'bg-white border border-stone-200 text-stone-600 hover:bg-stone-50'
                  }`}
                >
                  <span className={tab.color}>{tab.label}</span>
                </button>
              ))}
            </div>

            {/* SWOT Quadrants Grid */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
              
              {/* STRENGTHS */}
              {(activeTab === 'all' || activeTab === 'strengths') && (
                <div className="bg-white rounded-3xl p-6 border-2 border-emerald-200 shadow-xs space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-emerald-100">
                    <div className="flex items-center space-x-3">
                      <div className="p-2.5 bg-emerald-100 rounded-2xl text-emerald-800">
                        <CheckCircle2 className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-emerald-950 font-['Outfit']">
                          STRENGTHS
                        </h4>
                        <p className="text-[11px] text-emerald-700">
                          What is already working in your favor (Internal Positive)
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800">
                      {swotData.swot?.strengths?.length || 0} Identified
                    </span>
                  </div>

                  <div className="space-y-4">
                    {swotData.swot?.strengths?.map((item, idx) => (
                      <div
                        key={item.id || idx}
                        className="bg-emerald-50/40 rounded-2xl p-4 border border-emerald-100 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-[10px] font-mono font-bold text-emerald-800">
                                {item.id || `ST-${String(idx + 1).padStart(3, '0')}`}
                              </span>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadgeClass(item.priority)}`}>
                                {item.priority || 'HIGH'} IMPACT
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-md border bg-emerald-100/80 text-emerald-900 border-emerald-200">
                                {formatStageName(item.source_stage)}
                              </span>
                            </div>
                            <h5 className="text-sm font-bold text-stone-900">
                              {item.title}
                            </h5>
                          </div>
                          <button
                            onClick={() => toggleItem(item.id || `ST-${idx}`)}
                            className="p-1 text-stone-400 hover:text-stone-600 rounded-lg hover:bg-emerald-100/60 transition cursor-pointer"
                            title="Toggle details"
                          >
                            {expandedItems[item.id || `ST-${idx}`] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>

                        <p className="text-xs text-stone-700 leading-relaxed">
                          {item.explanation || item.statement}
                        </p>

                        {expandedItems[item.id || `ST-${idx}`] && (
                          <div className="pt-2 border-t border-emerald-100 space-y-2 text-xs animate-fadeIn">
                            {item.why_it_matters && item.why_it_matters !== item.explanation && (
                              <div className="bg-white/80 rounded-xl p-3 border border-emerald-100 space-y-1">
                                <span className="text-[10px] font-bold text-emerald-900 uppercase">
                                  Why This Matters:
                                </span>
                                <p className="text-[11px] text-stone-600 leading-relaxed">
                                  {item.why_it_matters}
                                </p>
                              </div>
                            )}

                            {item.evidence && item.evidence.length > 0 && (
                              <div className="bg-emerald-100/40 rounded-xl p-3 border border-emerald-200/60 space-y-1.5">
                                <span className="text-[10px] font-bold text-emerald-950 uppercase flex items-center space-x-1">
                                  <Layers className="w-3 h-3" />
                                  <span>Upstream Grounded Evidence:</span>
                                </span>
                                {item.evidence.map((ev, eIdx) => (
                                  <div key={eIdx} className="text-[11px] text-emerald-900 flex flex-wrap items-center gap-1.5">
                                    {typeof ev === 'string' ? (
                                      <span className="font-semibold text-stone-800">
                                        • {ev}
                                      </span>
                                    ) : (
                                      <>
                                        <span className="font-bold px-1.5 py-0.5 rounded bg-white text-emerald-800 text-[10px]">
                                          {ev.source_stage}
                                        </span>
                                        <span className="text-stone-500">→</span>
                                        <span className="font-mono text-[10px] text-stone-700">
                                          {ev.source_field}
                                        </span>
                                        {ev.value !== undefined && ev.value !== null && (
                                          <span className="font-semibold text-stone-900">
                                            = {formatVal(ev.value)}
                                          </span>
                                        )}
                                      </>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* WEAKNESSES */}
              {(activeTab === 'all' || activeTab === 'weaknesses') && (
                <div className="bg-white rounded-3xl p-6 border-2 border-amber-200 shadow-xs space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-amber-100">
                    <div className="flex items-center space-x-3">
                      <div className="p-2.5 bg-amber-100 rounded-2xl text-amber-800">
                        <AlertTriangle className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-amber-950 font-['Outfit']">
                          WEAKNESSES
                        </h4>
                        <p className="text-[11px] text-amber-700">
                          What currently limits the business (Internal Negative)
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-amber-100 text-amber-800">
                      {swotData.swot?.weaknesses?.length || 0} Identified
                    </span>
                  </div>

                  <div className="space-y-4">
                    {swotData.swot?.weaknesses?.map((item, idx) => (
                      <div
                        key={item.id || idx}
                        className="bg-amber-50/40 rounded-2xl p-4 border border-amber-100 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-[10px] font-mono font-bold text-amber-800">
                                {item.id || `WK-${String(idx + 1).padStart(3, '0')}`}
                              </span>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadgeClass(item.priority)}`}>
                                {item.priority || 'HIGH'} IMPACT
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-md border bg-amber-100/80 text-amber-900 border-amber-200">
                                {formatStageName(item.source_stage)}
                              </span>
                            </div>
                            <h5 className="text-sm font-bold text-stone-900">
                              {item.title}
                            </h5>
                          </div>
                          <button
                            onClick={() => toggleItem(item.id || `WK-${idx}`)}
                            className="p-1 text-stone-400 hover:text-stone-600 rounded-lg hover:bg-amber-100/60 transition cursor-pointer"
                            title="Toggle details"
                          >
                            {expandedItems[item.id || `WK-${idx}`] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>

                        <p className="text-xs text-stone-700 leading-relaxed">
                          {item.explanation || item.statement}
                        </p>

                        {expandedItems[item.id || `WK-${idx}`] && (
                          <div className="pt-2 border-t border-amber-100 space-y-2 text-xs animate-fadeIn">
                            {item.why_it_matters && item.why_it_matters !== item.explanation && (
                              <div className="bg-white/80 rounded-xl p-3 border border-amber-100 space-y-1">
                                <span className="text-[10px] font-bold text-amber-900 uppercase">
                                  Why This Matters:
                                </span>
                                <p className="text-[11px] text-stone-600 leading-relaxed">
                                  {item.why_it_matters}
                                </p>
                              </div>
                            )}

                            {item.evidence && item.evidence.length > 0 && (
                              <div className="bg-amber-100/40 rounded-xl p-3 border border-amber-200/60 space-y-1.5">
                                <span className="text-[10px] font-bold text-amber-950 uppercase flex items-center space-x-1">
                                  <Layers className="w-3 h-3" />
                                  <span>Upstream Grounded Evidence:</span>
                                </span>
                                {item.evidence.map((ev, eIdx) => (
                                  <div key={eIdx} className="text-[11px] text-amber-900 flex flex-wrap items-center gap-1.5">
                                    {typeof ev === 'string' ? (
                                      <span className="font-semibold text-stone-800">
                                        • {ev}
                                      </span>
                                    ) : (
                                      <>
                                        <span className="font-bold px-1.5 py-0.5 rounded bg-white text-amber-800 text-[10px]">
                                          {ev.source_stage}
                                        </span>
                                        <span className="text-stone-500">→</span>
                                        <span className="font-mono text-[10px] text-stone-700">
                                          {ev.source_field}
                                        </span>
                                        {ev.value !== undefined && ev.value !== null && (
                                          <span className="font-semibold text-stone-900">
                                            = {formatVal(ev.value)}
                                          </span>
                                        )}
                                      </>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* OPPORTUNITIES */}
              {(activeTab === 'all' || activeTab === 'opportunities') && (
                <div className="bg-white rounded-3xl p-6 border-2 border-blue-200 shadow-xs space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-blue-100">
                    <div className="flex items-center space-x-3">
                      <div className="p-2.5 bg-blue-100 rounded-2xl text-blue-800">
                        <Lightbulb className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-blue-950 font-['Outfit']">
                          OPPORTUNITIES
                        </h4>
                        <p className="text-[11px] text-blue-700">
                          Where the entrepreneur can capture value (External Positive)
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">
                      {swotData.swot?.opportunities?.length || 0} Identified
                    </span>
                  </div>

                  <div className="space-y-4">
                    {swotData.swot?.opportunities?.map((item, idx) => (
                      <div
                        key={item.id || idx}
                        className="bg-blue-50/40 rounded-2xl p-4 border border-blue-100 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-[10px] font-mono font-bold text-blue-800">
                                {item.id || `OP-${String(idx + 1).padStart(3, '0')}`}
                              </span>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadgeClass(item.priority)}`}>
                                {item.priority || 'HIGH'} IMPACT
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-md border bg-blue-100/80 text-blue-900 border-blue-200">
                                {formatStageName(item.source_stage)}
                              </span>
                            </div>
                            <h5 className="text-sm font-bold text-stone-900">
                              {item.title}
                            </h5>
                          </div>
                          <button
                            onClick={() => toggleItem(item.id || `OP-${idx}`)}
                            className="p-1 text-stone-400 hover:text-stone-600 rounded-lg hover:bg-blue-100/60 transition cursor-pointer"
                            title="Toggle details"
                          >
                            {expandedItems[item.id || `OP-${idx}`] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>

                        <p className="text-xs text-stone-700 leading-relaxed">
                          {item.explanation || item.statement}
                        </p>

                        {expandedItems[item.id || `OP-${idx}`] && (
                          <div className="pt-2 border-t border-blue-100 space-y-2 text-xs animate-fadeIn">
                            {item.why_it_matters && item.why_it_matters !== item.explanation && (
                              <div className="bg-white/80 rounded-xl p-3 border border-blue-100 space-y-1">
                                <span className="text-[10px] font-bold text-blue-900 uppercase">
                                  Why This Matters:
                                </span>
                                <p className="text-[11px] text-stone-600 leading-relaxed">
                                  {item.why_it_matters}
                                </p>
                              </div>
                            )}

                            {item.evidence && item.evidence.length > 0 && (
                              <div className="bg-blue-100/40 rounded-xl p-3 border border-blue-200/60 space-y-1.5">
                                <span className="text-[10px] font-bold text-blue-950 uppercase flex items-center space-x-1">
                                  <Layers className="w-3 h-3" />
                                  <span>Upstream Grounded Evidence:</span>
                                </span>
                                {item.evidence.map((ev, eIdx) => (
                                  <div key={eIdx} className="text-[11px] text-blue-900 flex flex-wrap items-center gap-1.5">
                                    {typeof ev === 'string' ? (
                                      <span className="font-semibold text-stone-800">
                                        • {ev}
                                      </span>
                                    ) : (
                                      <>
                                        <span className="font-bold px-1.5 py-0.5 rounded bg-white text-blue-800 text-[10px]">
                                          {ev.source_stage}
                                        </span>
                                        <span className="text-stone-500">→</span>
                                        <span className="font-mono text-[10px] text-stone-700">
                                          {ev.source_field}
                                        </span>
                                        {ev.value !== undefined && ev.value !== null && (
                                          <span className="font-semibold text-stone-900">
                                            = {formatVal(ev.value)}
                                          </span>
                                        )}
                                      </>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* THREATS */}
              {(activeTab === 'all' || activeTab === 'threats') && (
                <div className="bg-white rounded-3xl p-6 border-2 border-rose-200 shadow-xs space-y-5">
                  <div className="flex items-center justify-between pb-3 border-b border-rose-100">
                    <div className="flex items-center space-x-3">
                      <div className="p-2.5 bg-rose-100 rounded-2xl text-rose-800">
                        <ShieldAlert className="w-5 h-5" />
                      </div>
                      <div>
                        <h4 className="text-base font-bold text-rose-950 font-['Outfit']">
                          THREATS
                        </h4>
                        <p className="text-[11px] text-rose-700">
                          What could negatively affect the business (External Negative)
                        </p>
                      </div>
                    </div>
                    <span className="text-xs font-bold px-2.5 py-0.5 rounded-full bg-rose-100 text-rose-800">
                      {swotData.swot?.threats?.length || 0} Identified
                    </span>
                  </div>

                  <div className="space-y-4">
                    {swotData.swot?.threats?.map((item, idx) => (
                      <div
                        key={item.id || idx}
                        className="bg-rose-50/40 rounded-2xl p-4 border border-rose-100 space-y-3"
                      >
                        <div className="flex items-start justify-between gap-3">
                          <div className="space-y-1">
                            <div className="flex flex-wrap items-center gap-1.5">
                              <span className="text-[10px] font-mono font-bold text-rose-800">
                                {item.id || `TH-${String(idx + 1).padStart(3, '0')}`}
                              </span>
                              <span className={`text-[10px] font-bold px-2 py-0.5 rounded-md border ${getPriorityBadgeClass(item.priority)}`}>
                                {item.priority || 'HIGH'} IMPACT
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded-md border bg-rose-100/80 text-rose-900 border-rose-200">
                                {formatStageName(item.source_stage)}
                              </span>
                            </div>
                            <h5 className="text-sm font-bold text-stone-900">
                              {item.title}
                            </h5>
                          </div>
                          <button
                            onClick={() => toggleItem(item.id || `TH-${idx}`)}
                            className="p-1 text-stone-400 hover:text-stone-600 rounded-lg hover:bg-rose-100/60 transition cursor-pointer"
                            title="Toggle details"
                          >
                            {expandedItems[item.id || `TH-${idx}`] ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                          </button>
                        </div>

                        <p className="text-xs text-stone-700 leading-relaxed">
                          {item.explanation || item.statement}
                        </p>

                        {expandedItems[item.id || `TH-${idx}`] && (
                          <div className="pt-2 border-t border-rose-100 space-y-2 text-xs animate-fadeIn">
                            {item.why_it_matters && item.why_it_matters !== item.explanation && (
                              <div className="bg-white/80 rounded-xl p-3 border border-rose-100 space-y-1">
                                <span className="text-[10px] font-bold text-rose-900 uppercase">
                                  Why This Matters:
                                </span>
                                <p className="text-[11px] text-stone-600 leading-relaxed">
                                  {item.why_it_matters}
                                </p>
                              </div>
                            )}

                            {item.evidence && item.evidence.length > 0 && (
                              <div className="bg-rose-100/40 rounded-xl p-3 border border-rose-200/60 space-y-1.5">
                                <span className="text-[10px] font-bold text-rose-950 uppercase flex items-center space-x-1">
                                  <Layers className="w-3 h-3" />
                                  <span>Upstream Grounded Evidence:</span>
                                </span>
                                {item.evidence.map((ev, eIdx) => (
                                  <div key={eIdx} className="text-[11px] text-rose-900 flex flex-wrap items-center gap-1.5">
                                    {typeof ev === 'string' ? (
                                      <span className="font-semibold text-stone-800">
                                        • {ev}
                                      </span>
                                    ) : (
                                      <>
                                        <span className="font-bold px-1.5 py-0.5 rounded bg-white text-rose-800 text-[10px]">
                                          {ev.source_stage}
                                        </span>
                                        <span className="text-stone-500">→</span>
                                        <span className="font-mono text-[10px] text-stone-700">
                                          {ev.source_field}
                                        </span>
                                        {ev.value !== undefined && ev.value !== null && (
                                          <span className="font-semibold text-stone-900">
                                            = {formatVal(ev.value)}
                                          </span>
                                        )}
                                      </>
                                    )}
                                  </div>
                                ))}
                              </div>
                            )}
                          </div>
                        )}
                      </div>
                    ))}
                  </div>
                </div>
              )}

            </div>

            {/* Priority Actions (3–5 Items) */}
            <div className="bg-white rounded-3xl p-6 sm:p-7 border border-stone-200 shadow-sm space-y-5">
              <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                <div className="space-y-1">
                  <div className="flex items-center space-x-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EA580C]/10 text-[#EA580C]">
                      PRIORITY ACTION PLAN
                    </span>
                    <span className="text-xs font-semibold text-stone-500">
                      Top 3–5 Strategic Interventions
                    </span>
                  </div>
                  <h4 className="text-base font-bold text-stone-900 font-['Outfit']">
                    What Should the Entrepreneur Do Next?
                  </h4>
                </div>
                <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-orange-50 text-orange-800">
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
                      source_stage: (r.source_stages && r.source_stages[0]) || 'STAGE_10'
                    }))
                ).map((act, aIdx) => (
                  <div
                    key={aIdx}
                    className="p-4 rounded-2xl bg-[#FDFBF7] border border-stone-200 space-y-3 hover:border-[#EA580C] transition flex flex-col justify-between"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[11px] font-bold text-[#EA580C] font-mono">
                          STEP {aIdx + 1}
                        </span>
                        <span className={`text-[9px] font-bold px-2 py-0.5 rounded ${getPriorityBadgeClass(act.priority)}`}>
                          {act.priority || 'HIGH'} PRIORITY
                        </span>
                      </div>

                      <h6 className="text-xs font-bold text-stone-900 leading-snug">
                        {act.action}
                      </h6>

                      <p className="text-[11px] text-stone-600 leading-relaxed">
                        <strong className="text-stone-700">Why: </strong>
                        {act.reason}
                      </p>
                    </div>

                    <div className="pt-2 border-t border-stone-100 flex items-center justify-between text-[10px] text-stone-500">
                      <span className="font-bold">Source:</span>
                      <span className="font-mono px-1.5 py-0.5 bg-white border border-stone-200 rounded text-stone-700">
                        {formatStageName(act.source_stage)}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Phased Strategic Roadmap */}
            {swotData.swot?.roadmap && swotData.swot.roadmap.length > 0 && (
              <div className="bg-white rounded-3xl p-6 sm:p-7 border border-stone-200 shadow-sm space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-stone-100">
                  <div className="space-y-1">
                    <div className="flex items-center space-x-2">
                      <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EA580C]/10 text-[#EA580C]">
                        STRATEGIC ROADMAP
                      </span>
                      <span className="text-xs font-semibold text-stone-500">
                        Phased Implementation Timeline
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-stone-900 font-['Outfit']">
                      Execution Milestones & Action Steps
                    </h4>
                  </div>
                  <span className="text-xs font-bold px-2.5 py-1 rounded-lg bg-orange-50 text-orange-800">
                    {swotData.swot.roadmap.length} Phases
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  {swotData.swot.roadmap.map((phase, pIdx) => (
                    <div
                      key={pIdx}
                      className="p-4 rounded-2xl bg-[#FDFBF7] border border-stone-200 space-y-3"
                    >
                      <div className="flex items-center space-x-2">
                        <Clock className="w-4 h-4 text-[#EA580C]" />
                        <span className="text-xs font-bold text-stone-900 uppercase tracking-wide">
                          {phase.phase}
                        </span>
                      </div>
                      <ul className="space-y-2 text-xs text-stone-700">
                        {(phase.actions || []).map((act, actIdx) => (
                          <li key={actIdx} className="flex items-start space-x-2">
                            <span className="text-[#EA580C] font-bold text-xs mt-0.5">•</span>
                            <span className="text-[11px] leading-relaxed">{act}</span>
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
              <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-xs space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-2">
                    <Layers className="w-4 h-4 text-stone-500" />
                    <h4 className="text-xs font-bold text-stone-800 uppercase tracking-wider">
                      Upstream Evidence Verification Baseline
                    </h4>
                  </div>
                  <span className="text-[11px] text-stone-500 font-medium">5 Pillars Grounded</span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-5 gap-3 text-xs">
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">Stage 6/8 • Market</span>
                    <p className="text-[11px] text-stone-700">{swotData.evidence_summary.market || 'Verified demand signals'}</p>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">Stage 9 • Finance</span>
                    <p className="text-[11px] text-stone-700">{swotData.evidence_summary.financial || 'Verified DSCR & financing'}</p>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">Stage 10 • Readiness</span>
                    <p className="text-[11px] text-stone-700">{swotData.evidence_summary.entrepreneur || 'Promoter readiness confirmed'}</p>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">Stage 11 • Risk</span>
                    <p className="text-[11px] text-stone-700">{swotData.evidence_summary.risk || 'Multi-vector risks mapped'}</p>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200/60 space-y-1">
                    <span className="text-[10px] font-bold text-stone-500 uppercase">Stage 12 • Feasibility</span>
                    <p className="text-[11px] text-stone-700">{swotData.evidence_summary.feasibility || 'Viable venture approved'}</p>
                  </div>
                </div>
              </div>
            )}

            {/* Bottom Next Step Call-To-Action -> DPR Stage 14 */}
            <div className="bg-[#EA580C] text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-center justify-between gap-6">
              <div className="space-y-1.5 text-center md:text-left">
                <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold bg-white/20 text-white">
                  NEXT STAGE UNLOCKED
                </span>
                <h3 className="text-xl font-bold font-['Outfit']">
                  Ready to Generate Bank Detailed Project Report (DPR)?
                </h3>
                <p className="text-xs text-orange-100 max-w-2xl">
                  Your SWOT matrix and strategic priorities are now finalized. Proceed to compile a bank-ready DPR for PMEGP, Mudra, or CGTMSE institutional financing.
                </p>
              </div>

              <div className="flex items-center space-x-3">
                <Link to="/dpr">
                  <button className="px-6 py-3 bg-white hover:bg-orange-50 text-[#EA580C] rounded-xl text-xs font-bold transition flex items-center space-x-2 shadow-sm cursor-pointer whitespace-nowrap">
                    <span>Proceed to Stage 14 DPR</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </Link>
              </div>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
