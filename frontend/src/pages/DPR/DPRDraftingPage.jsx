import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  CheckCircle,
  AlertCircle,
  AlertTriangle,
  Clock,
  RefreshCw,
  Download,
  Eye,
  ArrowLeft,
  ArrowRight,
  ShieldCheck,
  Building,
  User,
  MapPin,
  TrendingUp,
  FileCheck,
} from 'lucide-react';
import apiService from '../../services/api';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';
import GrowthManagerLaunchCard from '../../components/growth/GrowthManagerLaunchCard';
import GrowthManagerTransitionOverlay from '../../components/growth/GrowthManagerTransitionOverlay';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';

const PIPELINE_STAGES = [
  { id: 1, name: 'Data Validation', desc: 'Validating identity isolation and canonical schema' },
  { id: 2, name: 'Narrative Planning', desc: 'Planning section narrative structure' },
  { id: 3, name: 'Narrative Drafting', desc: 'Drafting institutional appraisal prose' },
  { id: 4, name: 'Narrative Validation', desc: 'Scanning for zero hallucinated facts/numbers' },
  { id: 5, name: 'Document Assembly', desc: 'Compiling 40 canonical sections & annexures' },
  { id: 6, name: 'Financial Validation', desc: 'Reconciling financial sources, uses & DSCR' },
  { id: 7, name: 'PDF Rendering', desc: 'Typesetting ReportLab portrait & landscape pages' },
  { id: 8, name: 'Quality Check', desc: 'Scanning PDF text and visual regression tokens' },
  { id: 9, name: 'Generation Complete', desc: 'Institutional DPR ready for banking review' },
];

export const DPRDraftingPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { businessName: ctxBusinessName, businessId: ctxBusinessId, sessionId: ctxSessionId } = useWorkflow();
  const { language, t } = useLanguage();

  const businessId = (searchParams.get('business_id') || ctxBusinessId || sessionStorage.getItem('kalpa_business_id') || '').trim();
  const activeSessionId = (searchParams.get('session_id') || ctxSessionId || sessionStorage.getItem('kalpa_session_id') || '').trim();
  const dprKey = businessId && activeSessionId ? `kalpa_dpr_scenario_${businessId}_${activeSessionId}` : (businessId ? `kalpa_dpr_scenario_${businessId}` : 'kalpa_dpr_scenario_active');
  const scenarioId = (searchParams.get('scenario_id') || sessionStorage.getItem(dprKey) || (businessId ? `DPR-${businessId.slice(0, 8)}` : 'default')).trim();

  const [currentStep, setCurrentStep] = useState(1);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [contextPackage, setContextPackage] = useState(null);
  const [errorState, setErrorState] = useState(null);
  const [previewOpen, setPreviewOpen] = useState(false);
  const [previewBlobUrl, setPreviewBlobUrl] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState(false);

  // Business Name resolution for Growth Manager launch context
  const [confirmedBusinessName, setConfirmedBusinessName] = useState(() => {
    return ctxBusinessName || sessionStorage.getItem('kalpa_business_name') || '';
  });

  // Product-State Transition Orchestration for Growth Manager
  const [isTransitioning, setIsTransitioning] = useState(false);
  const [targetGrowthUrl, setTargetGrowthUrl] = useState('');

  const handleContinueTransition = ({ businessId: bId, sessionId: sId, scenarioId: scId, businessName: bName }) => {
    if (isTransitioning) return;

    if (bName) {
      setConfirmedBusinessName(bName);
    }

    const params = new URLSearchParams();
    if (bId) params.set('business_id', bId);
    if (sId) params.set('session_id', sId);
    if (scId) params.set('scenario_id', scId);
    const destination = `/growth-manager?${params.toString()}`;
    setTargetGrowthUrl(destination);

    const prefersReducedMotion =
      typeof window !== 'undefined' &&
      window.matchMedia &&
      window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    if (prefersReducedMotion) {
      navigate(destination);
      return;
    }

    setIsTransitioning(true);
  };

  const handleTransitionComplete = () => {
    if (targetGrowthUrl) {
      navigate(targetGrowthUrl);
    } else {
      const params = new URLSearchParams();
      if (businessId) params.set('business_id', businessId);
      if (activeSessionId) params.set('session_id', activeSessionId);
      if (scenarioId) params.set('scenario_id', scenarioId);
      navigate(`/growth-manager?${params.toString()}`);
    }
  };

  // Pre-load canonical context for consistent snapshot display
  useEffect(() => {
    if (businessId) {
      apiService.dpr
        .getContext(businessId, { scenario_id: scenarioId })
        .then((res) => {
          const data = res?.data || res;
          if (data) {
            setContextPackage(data);
            if (!confirmedBusinessName) {
              const bName = data.business_profile?.enterprise_name || data.business_profile?.business_name || data.fields?.enterprise_name?.value || '';
              if (bName) setConfirmedBusinessName(bName);
            }
          }
        })
        .catch((err) => {
          console.warn('[DPRDraftingPage] Context pre-fetch warning:', err);
        });
    }
  }, [businessId, scenarioId]);

  useEffect(() => {
    if (result?.metadata?.business_name && !confirmedBusinessName) {
      setConfirmedBusinessName(result.metadata.business_name);
    }
  }, [result, confirmedBusinessName]);

  // Clean up Object URL on unmount or when URL changes
  useEffect(() => {
    return () => {
      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
      }
    };
  }, [previewBlobUrl]);

  const triggerGeneration = async (forceRegenerate = false) => {
    setLoading(true);
    setErrorState(null);
    setResult(null);

    setCurrentStep(1);
    const stepInterval = setInterval(() => {
      setCurrentStep((prev) => (prev < 7 ? prev + 1 : prev));
    }, 700);

    try {
      const resp = await apiService.dpr.generate14_3DPR(businessId, {
        scenario_id: scenarioId,
        format: 'pdf',
        language: language || 'en',
        regenerate_narrative: forceRegenerate,
      });

      clearInterval(stepInterval);
      setCurrentStep(9);
      setResult(resp?.data || resp);
    } catch (err) {
      clearInterval(stepInterval);
      console.error('[DPRDraftingPage] Generation failed:', err);

      let errTitle = 'Generation Failed';
      let errType = 'PDF Generation Failed';
      const rawDetail = err.response?.data?.detail;
      const detailStr =
        typeof rawDetail === 'object' ? JSON.stringify(rawDetail) : String(rawDetail || err.message || '');

      if (detailStr.includes('DPR_STATE_ISOLATION_ERROR') || err.response?.status === 409) {
        errType = 'Scenario Identity Conflict';
        errTitle = 'Business / Scenario Identity Mismatch';
      } else if (
        err.response?.status === 422 ||
        detailStr.includes('DPR_FINANCIAL_RECONCILIATION_FAILED') ||
        detailStr.includes('financial reconciliation') ||
        detailStr.includes('Sources = Uses')
      ) {
        errType = 'Financial Reconciliation Failed';
        errTitle = 'DPR generation blocked: financial reconciliation requires correction.';
      } else if (detailStr.includes('Narrative') || detailStr.includes('hallucinated')) {
        errType = 'Narrative Validation Failed';
        errTitle = 'LLM Narrative Validation Failed';
      } else if (detailStr.includes('Validation')) {
        errType = 'Validation Failed';
        errTitle = 'Data Completeness Validation Failed';
      }

      setErrorState({
        title: errTitle,
        type: errType,
        detail: detailStr,
      });
      setCurrentStep(0);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (businessId) {
      triggerGeneration();
    }
  }, [businessId, scenarioId]);

  const openPreviewModal = async () => {
    const docId = result?.document_id;
    if (!docId) return;
    setPreviewOpen(true);
    setPreviewLoading(true);
    setPreviewError(false);

    try {
      const previewUrl = apiService.dpr.preview14_3Url(docId);
      const res = await fetch(previewUrl);
      if (!res.ok) {
        throw new Error(`Preview failed with status ${res.status}`);
      }
      const blob = await res.blob();
      const pdfBlob = new Blob([blob], { type: 'application/pdf' });
      const objectUrl = URL.createObjectURL(pdfBlob);
      if (previewBlobUrl) {
        URL.revokeObjectURL(previewBlobUrl);
      }
      setPreviewBlobUrl(objectUrl);
    } catch (err) {
      console.error('[DPRDraftingPage] Preview Blob Error:', err);
      setPreviewError(true);
    } finally {
      setPreviewLoading(false);
    }
  };

  const closePreviewModal = () => {
    setPreviewOpen(false);
    if (previewBlobUrl) {
      URL.revokeObjectURL(previewBlobUrl);
      setPreviewBlobUrl(null);
    }
  };

  const getDprStatusBadge = (status) => {
    if (status === 'READY_FOR_SUBMISSION') {
      return {
        bg: 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]',
        label: 'READY FOR SUBMISSION',
        desc: 'All documentary evidence verified and financial schedules balanced.',
      };
    }
    if (status === 'BANK_REVIEW_READY') {
      return {
        bg: 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]',
        label: 'BANK-REVIEW-READY',
        desc: 'Core financials reconciled. Ready for institutional review.',
      };
    }
    return {
      bg: 'bg-[#FAF2E3] border-[#79563F]/25 text-[#79563F]',
      label: 'DRAFT DPR',
      desc: 'Institutional DPR generated from validated business context.',
    };
  };

  const formatBusinessName = (name) => {
    if (!name) return 'Detailed Project Report';
    const cleaned = String(name).trim();
    if (cleaned.includes('_')) {
      return cleaned.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    }
    return cleaned;
  };

  const statusInfo = getDprStatusBadge(result?.status || 'BANK_REVIEW_READY');

  return (
    <div className="max-w-6xl mx-auto px-3 sm:px-6 py-5 sm:py-6 space-y-5 sm:space-y-6 animate-fadeIn relative">
      {/* Top Standard KALPA Workflow */}
      <div className={`transition-opacity duration-300 ${isTransitioning ? 'opacity-0 pointer-events-none' : 'opacity-100'}`}>
        <AgenticWorkflowThread currentStepNumber={3} />
      </div>

      {/* Main DPR Content Area (Softly blurs, scales down, and recedes during workflow transformation) */}
      <div
        className={`space-y-5 sm:space-y-6 transition-all duration-700 ease-out ${
          isTransitioning
            ? 'scale-[0.98] brightness-95 opacity-30 blur-[6px] pointer-events-none'
            : 'scale-100 opacity-100 blur-0'
        }`}
      >
        {/* Clean DPR Step 3 Header */}
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                  {t('dpr_step_3_title', 'DPR · STEP 3')}
                </span>
                <span className="text-xs text-[#79563F]/80 font-medium">
                  {t('dpr_step_3_subtitle', 'Detailed Project Report Generation')}
                </span>
              </div>
              <h1 className="text-xl sm:text-2xl font-extrabold text-[#1C1917] font-['Outfit']">
                {formatBusinessName(ctxBusinessName || result?.metadata?.business_name || sessionStorage.getItem('kalpa_business_name') || businessId || 'Bank-Ready Project Report')}
              </h1>
              <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
                {t('dpr_step_3_desc', 'Institutional-grade bank-review-ready DPR synthesis across 40 canonical sections and financial tables.')}
              </p>
            </div>

            <div className="flex items-center gap-2.5 self-start sm:self-center">
              <Link
                to={`/dpr/enrichment?business_id=${businessId}&scenario_id=${scenarioId}`}
                className="px-3.5 py-2 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/20 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs cursor-pointer"
              >
                <ArrowLeft className="w-3.5 h-3.5" />
                <span>{t('dpr_back_step_2', 'Back to Step 2')}</span>
              </Link>

              {result && (
                <button
                  type="button"
                  onClick={() => triggerGeneration(true)}
                  disabled={loading}
                  className="px-3.5 py-2 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/20 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs cursor-pointer"
                >
                  <RefreshCw className={`w-3.5 h-3.5 ${loading ? 'animate-spin text-[#79563F]' : ''}`} />
                  <span>{t('regenerate', 'Regenerate')}</span>
                </button>
              )}
            </div>
          </div>
        </div>

        {/* Synthesis Pipeline Execution Tracker */}
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4">
          <h2 className="text-xs font-bold uppercase tracking-wider text-[#79563F] flex items-center gap-2">
            <Clock className="w-4 h-4 text-[#79563F]" />
            <span>{t('dpr_pipeline_execution', 'DPR Synthesis Pipeline Execution')}</span>
          </h2>

          <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-9 gap-2">
            {PIPELINE_STAGES.map((s) => {
              const isCompleteState = Boolean(result) && !loading;
              const isPast = isCompleteState ? true : currentStep > s.id;
              const isCurrent = !isCompleteState && currentStep === s.id;
              return (
                <div
                  key={s.id}
                  className={`p-2.5 rounded-xl border text-center transition-all ${
                    isPast
                      ? 'bg-[#EAF5EE] border-[#1B4D3E]/30 text-[#1B4D3E]'
                      : isCurrent
                      ? `bg-[#FAF7F2] border-[#79563F] text-[#79563F] ring-2 ring-[#79563F]/20 ${loading ? 'animate-pulse' : ''}`
                      : 'bg-[#FAF7F2]/60 border-[#79563F]/15 text-[#79563F]/60'
                  }`}
                >
                  <div className="text-[10px] font-bold">Step {s.id}</div>
                  <div className="text-[11px] font-semibold truncate mt-0.5">{s.name}</div>
                </div>
              );
            })}
          </div>
        </div>

        {/* Generation Result View */}
        {result && (
          <div className="space-y-5 animate-fadeIn">
            {/* Main Success Banner */}
            <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-6 shadow-2xs space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="flex items-center gap-3.5">
                  <div className="w-12 h-12 rounded-2xl bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 flex items-center justify-center shrink-0 shadow-2xs">
                    <FileCheck className="w-6 h-6 text-[#1B4D3E]" />
                  </div>
                  <div>
                    <div className="flex items-center gap-2">
                      <span className={`text-[10px] font-bold px-2.5 py-0.5 rounded-md border ${statusInfo.bg}`}>
                        {statusInfo.label}
                      </span>
                      <span className="text-xs text-[#1B4D3E] font-bold px-2.5 py-0.5 rounded-md bg-[#EAF5EE] border border-[#1B4D3E]/30">
                        Bank-Ready Project Report
                      </span>
                    </div>
                    <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit'] mt-1">
                      {formatBusinessName(result.metadata?.business_name || ctxBusinessName || sessionStorage.getItem('kalpa_business_name') || businessId || 'Institutional Detailed Project Report')}
                    </h3>
                    <p className="text-xs text-[#79563F]">{statusInfo.desc}</p>
                  </div>
                </div>

                {/* Action Buttons: Preview and Download */}
                <div className="flex items-center gap-3">
                  <button
                    type="button"
                    onClick={openPreviewModal}
                    className="px-4 py-2.5 rounded-xl bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/30 text-xs font-bold transition flex items-center gap-2 shadow-2xs cursor-pointer"
                  >
                    <Eye className="w-4 h-4 text-[#79563F]" />
                    <span>{t('dpr_preview_pdf', 'Preview PDF')}</span>
                  </button>

                  <a
                    href={apiService.dpr.download14_3Url(result.document_id)}
                    download
                    className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
                  >
                    <Download className="w-4 h-4" />
                    <span>{t('dpr_download_pdf', 'Download Bank DPR (PDF)')}</span>
                  </a>
                </div>
              </div>
            </div>

            {/* Key Metrics Snapshot - Pristine 4-Column Responsive Grid */}
            {(() => {
              const fields = contextPackage?.fields || {};
              const bp = contextPackage?.business_profile || {};
              const ep = contextPackage?.entrepreneur_profile || {};
              const finPkg = contextPackage?.financial_package || {};
              const bm = finPkg.banking_metrics || {};

              const promoterDisplay =
                result.metadata?.promoter_name ||
                fields.promoter_name?.value ||
                ep.promoter_name ||
                bp.promoter_name ||
                'Venture Promoter';

              const locationDisplay =
                result.metadata?.location ||
                (fields.location_district?.value && fields.location_state?.value
                  ? `${fields.location_district.value}, ${fields.location_state.value}`
                  : bp.district && bp.state
                  ? `${bp.district}, ${bp.state}`
                  : 'Operational Site');

              const totalCostNum =
                result.metadata?.total_project_cost ??
                fields.total_project_cost?.value ??
                fields.glance_total_project_cost?.value ??
                finPkg.total_project_cost ??
                null;

              const termLoanNum =
                result.metadata?.bank_term_loan ??
                fields.bank_term_loan_amount?.value ??
                fields.glance_term_loan?.value ??
                finPkg.term_loan ??
                null;

              const dscrNum =
                result.metadata?.average_dscr ??
                fields.glance_average_dscr?.value ??
                bm.average_dscr ??
                finPkg.average_dscr ??
                null;

              return (
                <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
                  <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                    <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Promoter</div>
                    <div className="text-sm font-bold text-[#1C1917] mt-1">{promoterDisplay}</div>
                    <div className="text-[11px] text-[#79563F] mt-0.5">{locationDisplay}</div>
                  </div>

                  <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                    <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Total Project Cost</div>
                    <div className="text-lg font-black text-[#1C1917] font-['Outfit'] mt-1">
                      {totalCostNum !== null && totalCostNum !== undefined
                        ? `₹${Number(totalCostNum).toLocaleString('en-IN')}`
                        : 'Evaluated'}
                    </div>
                    <div className="text-[11px] text-[#1B4D3E] mt-0.5 font-medium">Reconciled in financial tables</div>
                  </div>

                  <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                    <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Bank Term Loan</div>
                    <div className="text-lg font-black text-[#1C1917] font-['Outfit'] mt-1">
                      {termLoanNum !== null && termLoanNum !== undefined
                        ? `₹${Number(termLoanNum).toLocaleString('en-IN')}`
                        : 'Eligible'}
                    </div>
                    <div className="text-[11px] text-[#79563F] mt-0.5">Aligned with PMEGP/MUDRA parameters</div>
                  </div>

                  <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                    <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Average DSCR</div>
                    <div className="text-lg font-black text-[#1B4D3E] font-['Outfit'] mt-1">
                      {dscrNum !== null && dscrNum !== undefined ? `${Number(dscrNum).toFixed(2)}x` : '—'}
                    </div>
                    <div className="text-[11px] text-[#1B4D3E] mt-0.5 font-medium">Viable for bank sanction (&gt;= 1.5x)</div>
                  </div>
                </div>
              );
            })()}

            {/* Growth Manager Launch Section — Additive Block Strictly BELOW Summary Cards */}
            <GrowthManagerLaunchCard
              businessId={businessId}
              sessionId={activeSessionId}
              scenarioId={scenarioId}
              initialBusinessName={
                confirmedBusinessName ||
                result.metadata?.business_name ||
                ctxBusinessName ||
                sessionStorage.getItem('kalpa_business_name') ||
                ''
              }
              onContinueTransition={handleContinueTransition}
              isTransitioning={isTransitioning}
            />
          </div>
        )}

        {/* Error Card */}
        {errorState && (
          <div className="bg-rose-50 border border-rose-200 rounded-3xl p-6 text-rose-900 space-y-3 shadow-2xs">
            <div className="flex items-center gap-2 font-bold text-base text-rose-900">
              <AlertTriangle className="w-5 h-5 text-rose-700" />
              <span>{errorState.title}</span>
            </div>
            <p className="text-xs text-rose-800 leading-relaxed">{errorState.detail}</p>
            <div className="pt-2 flex gap-3">
              <button
                type="button"
                onClick={() => triggerGeneration(true)}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold shadow-xs cursor-pointer"
              >
                Retry Generation
              </button>
            </div>
          </div>
        )}
      </div>

      {/* PDF Preview Modal */}
      {previewOpen && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-xs z-50 flex items-center justify-center p-3 sm:p-6 animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl w-full max-w-5xl h-[85vh] flex flex-col shadow-2xl overflow-hidden">
            <div className="px-6 py-4 bg-[#FAF2E3] border-b border-[#79563F]/20 flex items-center justify-between">
              <div className="flex items-center gap-2">
                <FileText className="w-5 h-5 text-[#79563F]" />
                <h3 className="font-bold text-base text-[#1C1917] font-['Outfit']">
                  DPR Document Preview
                </h3>
              </div>
              <button
                type="button"
                onClick={closePreviewModal}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-lg cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="flex-1 min-h-0 bg-[#FAF7F2]">
              {previewLoading ? (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-[#79563F]">
                  <RefreshCw className="w-8 h-8 animate-spin text-[#79563F]" />
                  <span className="text-xs font-semibold">Rendering PDF Document...</span>
                </div>
              ) : previewError ? (
                <div className="h-full flex flex-col items-center justify-center gap-3 text-rose-800 p-6 text-center">
                  <AlertCircle className="w-8 h-8 text-rose-700" />
                  <span className="text-sm font-bold">Unable to render PDF preview directly.</span>
                  <a
                    href={apiService.dpr.download14_3Url(result.document_id)}
                    download
                    className="saffron-gradient-btn px-4 py-2 rounded-xl text-xs font-bold"
                  >
                    Download PDF Document
                  </a>
                </div>
              ) : previewBlobUrl ? (
                <iframe
                  src={previewBlobUrl}
                  title="DPR Document Preview"
                  className="w-full h-full border-0"
                />
              ) : null}
            </div>
          </div>
        </div>
      )}
      {/* Cinematic Restrained KALPA Growth Manager Mode Transition Overlay */}
      <GrowthManagerTransitionOverlay
        isOpen={isTransitioning}
        businessName={
          confirmedBusinessName ||
          result?.metadata?.business_name ||
          ctxBusinessName ||
          sessionStorage.getItem('kalpa_business_name') ||
          'Commercial Enterprise'
        }
        onComplete={handleTransitionComplete}
      />
    </div>
  );
};

export default DPRDraftingPage;
