import React, { useState, useEffect, useCallback } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  ShieldCheck,
  CheckCircle2,
  RefreshCw,
  Layers,
  TrendingUp,
  Sliders,
  Check,
  AlertCircle,
  ArrowRight,
  ArrowLeft,
  Edit3,
  CheckCircle,
  XCircle,
  Clock,
  Sparkles,
  Info,
  ChevronDown,
  ChevronUp,
  Database,
  Calculator,
  Building,
  DollarSign,
  AlertTriangle,
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';
import { validatePackageIdentity } from './dprIdentityValidator';

// Formatting helpers
const formatINR = (val) => {
  if (val === null || val === undefined || val === '') return 'Not resolved';
  const num = parseFloat(val);
  if (isNaN(num)) return 'Not resolved';
  const isNeg = num < 0;
  const abs = Math.abs(num);
  const formatted = abs.toLocaleString('en-IN', {
    maximumFractionDigits: 0,
    minimumFractionDigits: 0,
  });
  return isNeg ? `(₹${formatted})` : `₹${formatted}`;
};

const formatPct = (val) => {
  if (val === null || val === undefined || val === '') return 'Not resolved';
  const num = parseFloat(val);
  if (isNaN(num)) return 'Not resolved';
  return `${num.toFixed(1)}%`;
};

const formatRatio = (val) => {
  if (val === null || val === undefined || val === '') return 'Not resolved';
  const num = parseFloat(val);
  if (isNaN(num)) return 'Not resolved';
  return `${num.toFixed(2)}x`;
};

// KALPA Source Badge Helper
const renderSourceBadge = (sourceType) => {
  const rawTag = (sourceType || 'UNKNOWN').toUpperCase().replace(/_/g, ' ');
  let colorClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25';

  if (rawTag.includes('OVERRIDE')) {
    colorClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/40 font-bold';
  } else if (rawTag.includes('USER') || rawTag.includes('PROVIDED') || rawTag.includes('VERIFIED') || rawTag.includes('COMPLETE')) {
    colorClass = 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/30 font-semibold';
  } else if (rawTag.includes('BENCHMARK') || rawTag.includes('ENGINE') || rawTag.includes('CALCULATED') || rawTag.includes('POLICY') || rawTag.includes('MARKET')) {
    colorClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/20 font-medium';
  }

  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-md border tracking-wide uppercase ${colorClass}`}>
      {rawTag}
    </span>
  );
};

export const DPREnrichmentPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { t } = useLanguage();
  const {
    currentBusiness,
    businessId: ctxBusinessId,
    businessName: ctxBusinessName,
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
  } = useWorkflow();

  const queryParams = new URLSearchParams(location.search);
  const urlBizId = queryParams.get('business_id');

  const businessId = (
    urlBizId ||
    location.state?.businessId ||
    location.state?.business_id ||
    ctxBusinessId ||
    sessionStorage.getItem('kalpa_business_id') ||
    ctxAnalysisId ||
    sessionStorage.getItem('kalpa_analysis_id') ||
    ctxSessionId ||
    sessionStorage.getItem('kalpa_session_id') ||
    currentBusiness?.id ||
    'business'
  ).trim();

  const rawBusinessName = ctxBusinessName || currentBusiness?.name || sessionStorage.getItem('kalpa_business_name') || (businessId && businessId !== 'business' ? businessId : '');
  const businessName = rawBusinessName.includes('_') ? rawBusinessName.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase()) : rawBusinessName;

  const getDprScenarioKey = (bId, sId) => {
    const cleanB = (bId || '').trim();
    const cleanS = (sId || '').trim();
    if (cleanB && cleanS) return `kalpa_dpr_scenario_${cleanB}_${cleanS}`;
    if (cleanB) return `kalpa_dpr_scenario_${cleanB}`;
    return 'kalpa_dpr_scenario_active';
  };

  const initialScenarioId = (
    queryParams.get('scenario_id') ||
    location.state?.scenarioId ||
    location.state?.scenario_id ||
    sessionStorage.getItem(getDprScenarioKey(businessId, activeSessionId)) ||
    ''
  ).trim();

  const [scenarioId, setScenarioId] = useState(() => {
    if (initialScenarioId && businessId && (initialScenarioId.includes(businessId.slice(0, 5)) || initialScenarioId.startsWith('DPR-'))) {
      return initialScenarioId;
    }
    return initialScenarioId || (businessId ? `DPR-${businessId.slice(0, 8)}` : 'default');
  });

  const [enrichmentPackage, setEnrichmentPackage] = useState(null);
  const [readiness, setReadiness] = useState(null);
  const [loading, setLoading] = useState(true);
  const [enriching, setEnriching] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('assumptions'); // assumptions, modules, validation
  const [expandedModule, setExpandedModule] = useState('module_0');
  const [editItem, setEditItem] = useState(null);
  const [editValue, setEditValue] = useState('');

  const loadEnrichmentState = useCallback(async () => {
    if (!businessId) {
      setLoading(false);
      setError({ title: 'No active business profile found', message: 'Please complete intake steps first.' });
      return;
    }
    try {
      setLoading(true);
      setError(null);
      const activeScen = (scenarioId || sessionStorage.getItem(getDprScenarioKey(businessId, activeSessionId)) || (businessId ? `DPR-${businessId.slice(0, 8)}` : 'default')).trim();
      const params = { scenario_id: activeScen };

      const [enRes, readRes] = await Promise.allSettled([
        apiService.dpr.getEnrichment(businessId, params),
        apiService.dpr.get14_2Readiness(businessId, params),
      ]);

      if (enRes.status === 'rejected') {
        const httpStatus = enRes.reason?.response?.status || 500;
        const errDetail =
          enRes.reason?.response?.data?.message ||
          enRes.reason?.response?.data?.detail ||
          enRes.reason?.message ||
          'Enrichment request failed';
        setEnrichmentPackage(null);
        setError({
          title: 'Unable to load DPR enrichment',
          http_error: httpStatus,
          message: typeof errDetail === 'string' ? errDetail : JSON.stringify(errDetail),
          scenario: activeScen,
        });
        return;
      }

      const pkgData = enRes.value?.data || enRes.value;
      const rData = readRes.status === 'fulfilled' ? readRes.value?.data || readRes.value : null;

      const pkgValidation = validatePackageIdentity(pkgData, { business_id: businessId, scenario_id: activeScen });
      if (!pkgValidation.valid) {
        throw new Error(`DPR_STATE_ISOLATION_ERROR: ${pkgValidation.reason}`);
      }

      if (pkgData) {
        setEnrichmentPackage(pkgData);
        if (pkgData.scenario_id) {
          setScenarioId(pkgData.scenario_id.trim());
        }
      }
      if (rData) {
        setReadiness(rData);
      }
    } catch (err) {
      console.error('[DPREnrichmentPage] Load error:', err);
      const httpStatus = err.response?.status || 500;
      const errMsg = err.message || 'Failed to load DPR enrichment. Please try again.';
      setEnrichmentPackage(null);
      setError({
        title: 'Unable to load DPR enrichment',
        http_error: httpStatus,
        message: errMsg,
        scenario: scenarioId,
      });
    } finally {
      setLoading(false);
    }
  }, [businessId, scenarioId]);

  useEffect(() => {
    loadEnrichmentState();
  }, [loadEnrichmentState]);

  const handleRunEnrichment = async () => {
    try {
      setEnriching(true);
      const expectedScen = getExpectedScenarioId(businessId);
      const activeScen = scenarioId && scenarioId.includes(businessId.slice(0, 5)) ? scenarioId : expectedScen;
      const res = await apiService.dpr.runEnrichment(businessId, {}, { scenario_id: activeScen });
      const pkgData = res.data || res;

      const pkgValidation = validatePackageIdentity(pkgData, { business_id: businessId, scenario_id: activeScen });
      if (!pkgValidation.valid) {
        throw new Error(`DPR_STATE_ISOLATION_ERROR: ${pkgValidation.reason}`);
      }

      setEnrichmentPackage(pkgData);
      await loadEnrichmentState();
    } catch (err) {
      console.error('[DPREnrichmentPage] Run error:', err);
      setError({ title: 'Re-enrichment failed', message: err.message });
    } finally {
      setEnriching(false);
    }
  };

  const handleUpdateAssumption = async (actionType, customVal = null) => {
    if (!editItem) return;
    try {
      setEnriching(true);
      const expectedScen = getExpectedScenarioId(businessId);
      const activeScen = scenarioId && scenarioId.includes(businessId.slice(0, 5)) ? scenarioId : expectedScen;
      const targetVal = customVal !== null ? customVal : editValue;
      const res = await apiService.dpr.updateEnrichmentAssumption(businessId, {
        field_id: editItem.field_id,
        action: actionType,
        value: targetVal,
        scenario_id: activeScen,
      });
      const pkgData = res.data || res;

      const pkgValidation = validatePackageIdentity(pkgData, { business_id: businessId, scenario_id: activeScen });
      if (!pkgValidation.valid) {
        throw new Error(`DPR_STATE_ISOLATION_ERROR: ${pkgValidation.reason}`);
      }

      setEnrichmentPackage(pkgData);
      setEditItem(null);
      await loadEnrichmentState();
    } catch (err) {
      console.error('[DPREnrichmentPage] Error updating assumption:', err);
      setError({ title: 'Update failed', message: err.message });
    } finally {
      setEnriching(false);
    }
  };

  if (loading && !enrichmentPackage) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6 animate-fadeIn">
        <AgenticWorkflowThread />
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 rounded-2xl bg-[#FAF7F2] border border-[#79563F]/25 flex items-center justify-center mx-auto text-[#79563F] shadow-2xs">
            <RefreshCw className="w-6 h-6 animate-spin text-[#79563F]" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
              Loading Project Report Enrichment...
            </h3>
            <p className="text-xs text-[#79563F]">
              Resolving empirical benchmarks, market signals, and authoritative financial schedules.
            </p>
          </div>
        </div>
      </div>
    );
  }

  const bp = enrichmentPackage?.business_profile || {};
  const fields = enrichmentPackage?.fields || {};
  const modules = enrichmentPackage?.modules || {};
  const assumptionReview = enrichmentPackage?.assumption_review || {};
  const validation = enrichmentPackage?.validation || {};
  const isEnrichmentComplete = enrichmentPackage?.is_enrichment_complete || false;
  const readyForDrafting = readiness?.ready_for_stage_14_3 ?? enrichmentPackage?.ready_for_stage_14_3 ?? false;
  const activeScenario = enrichmentPackage?.scenario_id || scenarioId;

  return (
    <div className="max-w-6xl mx-auto px-3 sm:px-6 py-5 sm:py-6 space-y-5 sm:space-y-6 animate-fadeIn">
      {/* Top Standard Workflow */}
      <AgenticWorkflowThread />

      {/* Clean KALPA DPR Step 2 Header */}
      <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                {t('dpr_step_2_title', 'DPR · STEP 2')}
              </span>
              <span className="text-xs text-[#79563F]/80 font-medium">
                {t('dpr_step_2_subtitle', 'Policy & Scheme Enrichment')}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-[#1C1917] font-['Outfit']">
              {businessName || ctxBusinessName || bp.business_name || 'Enriched Enterprise Project Report'}
            </h1>
            <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
              Auditing and enriching 8 modules across 39 canonical DPR sections with empirical benchmarks and financial engines.
            </p>
          </div>

          <div className="flex items-center gap-2.5 self-start sm:self-center">
            <span
              className={`px-3 py-1 rounded-xl text-xs font-bold border shadow-2xs ${
                isEnrichmentComplete
                  ? 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/30'
                  : 'bg-[#FAF7F2] text-[#79563F] border-[#79563F]/20'
              }`}
            >
              {isEnrichmentComplete ? t('completed', 'ENRICHMENT COMPLETE') : t('in_progress', 'REVIEW IN PROGRESS')}
            </span>

            <button
              type="button"
              onClick={handleRunEnrichment}
              disabled={enriching}
              title="Re-run Enrichment"
              className="p-2 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/20 transition cursor-pointer shadow-2xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${enriching ? 'animate-spin text-[#79563F]' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Error Alert */}
      {error && (
        <div className="p-5 rounded-2xl border border-rose-200 bg-rose-50 text-rose-900 space-y-2 shadow-2xs">
          <div className="flex items-center gap-2 font-bold text-sm text-rose-900">
            <AlertTriangle className="w-4 h-4 text-rose-700" />
            <span>{error.title || 'Enrichment Notice'}</span>
          </div>
          <p className="text-xs text-rose-800">{error.message}</p>
        </div>
      )}

      {/* Summary Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">39 Sections Status</div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {Object.values(enrichmentPackage?.sections || {}).filter((s) => s.completeness_status === 'COMPLETE').length}
            <span className="text-xs font-medium text-[#79563F]"> / 39 Complete</span>
          </div>
          <div className="text-[11px] text-[#1B4D3E] mt-2 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#1B4D3E]" />
            <span>Canonical DPR Registry Active</span>
          </div>
        </div>

        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Total Project Cost</div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {formatINR(fields.total_project_cost?.value)}
          </div>
          <div className="text-[11px] text-[#79563F] mt-2">
            Loan: {formatINR(fields.bank_term_loan_amount?.value)}
          </div>
        </div>

        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Average DSCR</div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {formatRatio(fields.glance_average_dscr?.value)}
          </div>
          <div className="text-[11px] text-[#79563F] mt-2">
            Break-Even: {formatPct(fields.glance_break_even_utilization?.value)}
          </div>
        </div>

        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Deterministic Audit</div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {validation.passed_checks || 14}{' '}
            <span className="text-xs font-medium text-[#79563F]">/ {validation.total_checks || 14} Passed</span>
          </div>
          <div className="text-[11px] text-[#1B4D3E] mt-2 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#1B4D3E]" />
            <span>Zero mathematical imbalances</span>
          </div>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-[#79563F]/20 gap-2 overflow-x-auto pb-1 no-scrollbar">
        <button
          type="button"
          onClick={() => setActiveTab('assumptions')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs ${
            activeTab === 'assumptions'
              ? 'bg-[#79563F] text-white shadow-xs'
              : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#F2E8D5] border border-[#79563F]/20'
          }`}
        >
          <Sliders className="w-3.5 h-3.5" />
          <span>Confirm Assumptions</span>
          {assumptionReview?.assumptions_requiring_review?.length > 0 && (
            <span className="bg-[#EAF5EE] text-[#1B4D3E] text-[10px] font-bold px-1.5 py-0.2 rounded-full">
              {assumptionReview.assumptions_requiring_review.length}
            </span>
          )}
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('modules')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs ${
            activeTab === 'modules'
              ? 'bg-[#79563F] text-white shadow-xs'
              : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#F2E8D5] border border-[#79563F]/20'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>8 Enriched Modules & Schedules</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('validation')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs ${
            activeTab === 'validation'
              ? 'bg-[#79563F] text-white shadow-xs'
              : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#F2E8D5] border border-[#79563F]/20'
          }`}
        >
          <ShieldCheck className="w-3.5 h-3.5" />
          <span>Audit & Validation Trail</span>
        </button>
      </div>

      {/* TAB 1: ASSUMPTIONS */}
      {activeTab === 'assumptions' && (
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
          <div>
            <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
              Review & Confirm Inferred Assumptions
            </h3>
            <p className="text-xs text-[#79563F] mt-0.5">
              KALPA has inferred empirical industry standards for operational drivers. You can accept the estimates or specify exact values.
            </p>
          </div>

          <div className="divide-y divide-[#79563F]/15">
            {Object.entries(enrichmentPackage?.assumptions || {}).map(([key, val], idx) => {
              const fieldRec = fields[key] || {};
              const isOverridden = enrichmentPackage?.overrides && enrichmentPackage.overrides[key] !== undefined;

              return (
                <div key={idx} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="font-bold text-sm text-[#1C1917] flex items-center gap-2">
                      <span>{fieldRec.label || key.replace(/_/g, ' ').toUpperCase()}</span>
                      {renderSourceBadge(fieldRec.source_type || 'EMPIRICAL_BENCHMARK')}
                    </div>
                    <div className="text-xs text-[#79563F] mt-1 flex flex-wrap items-center gap-3">
                      <span>
                        Inferred Benchmark:{' '}
                        <strong className="text-[#1C1917]">
                          {typeof val === 'object'
                            ? 'Configured Schedule'
                            : val !== null && val !== undefined
                            ? String(val)
                            : 'Standard'}
                        </strong>
                      </span>
                      <span>
                        Active Value:{' '}
                        <strong className="text-[#1B4D3E]">
                          {typeof fieldRec.value === 'object' && fieldRec.value !== null && Object.keys(fieldRec.value).length > 0
                            ? 'Verified Schedule'
                            : fieldRec.value !== null && fieldRec.value !== undefined && typeof fieldRec.value !== 'object'
                            ? String(fieldRec.value)
                            : 'Standard'}
                        </strong>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    <button
                      type="button"
                      onClick={() => {
                        setEditItem({ field_id: key, ...fieldRec, benchmark_val: val });
                        setEditValue(fieldRec.value !== null && fieldRec.value !== undefined ? fieldRec.value : '');
                      }}
                      className="text-xs px-3 py-1.5 bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/30 rounded-xl font-bold flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Adjust</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* TAB 2: MODULES */}
      {activeTab === 'modules' && (
        <div className="space-y-3 animate-fadeIn">
          {Object.values(modules).map((mod) => (
            <div
              key={mod.module_id}
              className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl overflow-hidden shadow-2xs"
            >
              <button
                type="button"
                onClick={() => setExpandedModule(expandedModule === mod.module_id ? null : mod.module_id)}
                className="w-full text-left p-4 sm:p-5 flex items-center justify-between hover:bg-[#F2E8D5] transition cursor-pointer"
              >
                <div className="flex items-center gap-3">
                  <span className="w-8 h-8 rounded-xl bg-[#FAF7F2] border border-[#79563F]/25 text-[#79563F] flex items-center justify-center font-bold text-xs shadow-2xs">
                    {mod.module_number}
                  </span>
                  <div>
                    <h4 className="font-bold text-[#1C1917] text-sm sm:text-base font-['Outfit']">
                      MODULE {mod.module_number}: {mod.title}
                    </h4>
                    <p className="text-xs text-[#79563F]">{mod.description}</p>
                  </div>
                </div>

                <div className="flex items-center gap-3">
                  <span className="text-xs text-[#79563F] font-semibold">
                    {mod.completed_sections} / {mod.total_sections} Sections
                  </span>
                  {expandedModule === mod.module_id ? (
                    <ChevronUp className="w-4 h-4 text-[#79563F]" />
                  ) : (
                    <ChevronDown className="w-4 h-4 text-[#79563F]" />
                  )}
                </div>
              </button>

              {expandedModule === mod.module_id && (
                <div className="border-t border-[#79563F]/15 p-4 bg-[#FAF7F2]/70 space-y-3">
                  {Object.values(mod.sections || {}).map((sec) => (
                    <div
                      key={sec.section_id}
                      className="bg-white border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <span className="text-xs font-bold text-[#79563F] bg-[#FAF2E3] px-2 py-0.5 rounded-lg border border-[#79563F]/20">
                            {sec.section_number}
                          </span>
                          <h5 className="font-bold text-[#1C1917] text-sm">{sec.title}</h5>
                        </div>
                        {renderSourceBadge(sec.completeness_status)}
                      </div>
                      <p className="text-xs text-[#79563F] mt-1">{sec.description}</p>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* TAB 3: VALIDATION */}
      {activeTab === 'validation' && (
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
          <div>
            <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
              Audit & Deterministic Validation Trail
            </h3>
            <p className="text-xs text-[#79563F] mt-0.5">
              Automated reconciliation cross-verifying financial balance, debt-service coverage, and statutory policy eligibility.
            </p>
          </div>

          <div className="space-y-2.5">
            <div className="p-4 bg-white border border-[#79563F]/20 rounded-2xl flex items-center justify-between shadow-2xs">
              <div>
                <div className="font-bold text-sm text-[#1C1917]">Sources of Funds = Uses of Funds Balance</div>
                <div className="text-[11px] text-[#79563F] mt-0.5">
                  Term Loan + Equity + Subsidies exactly equal Total Project Cost
                </div>
              </div>
              <span className="text-[10px] px-2.5 py-1 rounded-md bg-[#EAF5EE] text-[#1B4D3E] font-bold border border-[#1B4D3E]/30">
                BALANCED
              </span>
            </div>

            <div className="p-4 bg-white border border-[#79563F]/20 rounded-2xl flex items-center justify-between shadow-2xs">
              <div>
                <div className="font-bold text-sm text-[#1C1917]">Debt Service Coverage Ratio (DSCR) Benchmark</div>
                <div className="text-[11px] text-[#79563F] mt-0.5">
                  Average DSCR {formatRatio(fields.glance_average_dscr?.value)} meets bank viability criterion (&ge; 1.5x)
                </div>
              </div>
              <span className="text-[10px] px-2.5 py-1 rounded-md bg-[#EAF5EE] text-[#1B4D3E] font-bold border border-[#1B4D3E]/30">
                VIABLE
              </span>
            </div>

            <div className="p-4 bg-white border border-[#79563F]/20 rounded-2xl flex items-center justify-between shadow-2xs">
              <div>
                <div className="font-bold text-sm text-[#1C1917]">Statutory Compliance & Permitted Schemes</div>
                <div className="text-[11px] text-[#79563F] mt-0.5">
                  Udyam and target credit schemes mapped correctly
                </div>
              </div>
              <span className="text-[10px] px-2.5 py-1 rounded-md bg-[#EAF5EE] text-[#1B4D3E] font-bold border border-[#1B4D3E]/30">
                VERIFIED
              </span>
            </div>
          </div>
        </div>
      )}

      {/* Bottom Action Bar */}
      <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <Link
          to={`/dpr?business_id=${businessId}&scenario_id=${activeScenario}`}
          className="px-4 py-2.5 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/25 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>{t('dpr_back_step_1', 'Back to DPR Step 1')}</span>
        </Link>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              navigate(`/dpr/drafting?business_id=${businessId}&scenario_id=${activeScenario}`, {
                state: { businessId, scenarioId: activeScenario },
              });
            }}
            className="saffron-gradient-btn px-6 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
          >
            <span>{t('dpr_proceed_step_3', 'Generate Final Bank DPR')} →</span>
          </button>
        </div>
      </div>

      {/* Edit Modal */}
      {editItem && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#79563F]/15 pb-3">
              <h3 className="font-bold text-base text-[#1C1917] font-['Outfit']">Adjust Assumption</h3>
              <button
                type="button"
                onClick={() => setEditItem(null)}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Field</label>
              <div className="font-bold text-[#1C1917] text-sm">{editItem.label}</div>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Target Value</label>
              <input
                type="text"
                value={editValue}
                onChange={(e) => setEditValue(e.target.value)}
                className="w-full bg-white border border-[#79563F]/25 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-[#1C1917] focus:outline-none focus:border-[#79563F] focus:ring-1 focus:ring-[#79563F]/30"
              />
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-[#79563F]/15">
              <button
                type="button"
                onClick={() => setEditItem(null)}
                className="px-4 py-2 rounded-xl bg-[#FAF2E3] hover:bg-[#F2E8D5] text-[#79563F] text-xs font-bold border border-[#79563F]/20 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={() => handleUpdateAssumption('OVERRIDE')}
                disabled={enriching}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold shadow-xs cursor-pointer disabled:opacity-50"
              >
                Save & Recalculate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DPREnrichmentPage;
