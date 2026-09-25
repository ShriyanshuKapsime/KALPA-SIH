import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  Download,
  ShieldCheck,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  Building2,
  Calendar,
  Layers,
  BarChart3,
  TrendingUp,
  DollarSign,
  PieChart,
  HelpCircle,
  ExternalLink,
  ChevronDown,
  ChevronUp,
  FileCheck,
  Sliders,
  Check,
  AlertCircle,
  ArrowRight
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';

// Formatting helpers ensuring UNKNOWN != 0
const formatINR = (val) => {
  if (val === null || val === undefined || val === '') return 'Not available';
  const num = parseFloat(val);
  if (isNaN(num)) return 'Not available';
  const isNeg = num < 0;
  const abs = Math.abs(num);
  const formatted = abs.toLocaleString('en-IN', {
    maximumFractionDigits: 2,
    minimumFractionDigits: 2,
  });
  return isNeg ? `(₹${formatted})` : `₹${formatted}`;
};

const formatPct = (val) => {
  if (val === null || val === undefined || val === '') return 'Not available';
  const num = parseFloat(val);
  if (isNaN(num)) return 'Not available';
  return `${num.toFixed(1)}%`;
};

const formatRatio = (val) => {
  if (val === null || val === undefined || val === '') return 'Not available';
  const num = parseFloat(val);
  if (isNaN(num)) return 'Not available';
  return `${num.toFixed(2)}x`;
};

export const DPRPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    currentBusiness,
    currentSession,
    businessId: ctxBusinessId,
    businessName: ctxBusinessName,
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId
  } = useWorkflow();

  const queryParams = new URLSearchParams(location.search);
  const activeSessionId = location.state?.sessionId || location.state?.session_id || queryParams.get('session_id') || ctxSessionId || '';
  const activeAnalysisId = location.state?.analysisId || location.state?.analysis_id || queryParams.get('analysis_id') || ctxAnalysisId || '';

  const businessId =
    location.state?.businessId ||
    currentBusiness?.id ||
    currentSession?.id ||
    ctxBusinessId ||
    null;

  const [loading, setLoading] = useState(false);
  const [generating, setGenerating] = useState(false);
  const [dprMetadata, setDprMetadata] = useState(null);
  const [dprPackage, setDprPackage] = useState(null);
  const [error, setError] = useState(null);
  const [expandedSection, setExpandedSection] = useState(1); // Section 1 open by default

  useEffect(() => {
    if (businessId || activeSessionId || activeAnalysisId) {
      fetchDprPackage();
    }
  }, [businessId, activeSessionId, activeAnalysisId]);

  const fetchDprPackage = async () => {
    if (!businessId && !activeSessionId && !activeAnalysisId) {
      return;
    }
    setLoading(true);
    setError(null);
    try {
      // Load canonical DPR package directly using active session / business context
      const payload = {
        analysis_id: activeAnalysisId || undefined,
        session_id: activeSessionId || undefined,
        business_profile: {
          business_id: businessId || undefined,
          specific_business: ctxBusinessName || currentBusiness?.name || undefined,
        }
      };
      const res = await apiService.financialAnalysis.getDprPackage(payload);
      const pkg = res.data || res;
      setDprPackage(pkg);
    } catch (err) {
      console.warn('Could not load existing DPR package:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleGenerateDpr = async () => {
    setGenerating(true);
    setError(null);
    try {
      const res = await apiService.dpr.generateReport(businessId, {
        target_scheme: 'PMEGP',
        financial_package: dprPackage || undefined,
      });
      const meta = res.data || res;
      setDprMetadata(meta);
      if (meta.dpr_package) {
        setDprPackage(meta.dpr_package);
      }
    } catch (err) {
      console.error('Failed to generate DPR report:', err);
      setError('DPR generation failed. Please ensure upstream Stage 9 financials are verified.');
    } finally {
      setGenerating(false);
    }
  };

  const handleDownloadPdf = () => {
    const docId = dprMetadata?.document_id || `dpr-${businessId}`;
    const url = apiService.dpr.downloadPdfUrl(docId);
    window.open(url, '_blank');
  };

  const completeness = dprPackage?.data_completeness;
  const isEligible = completeness?.is_dpr_eligible ?? true;
  const sections = dprPackage?.sections || [];

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#1C1917] py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="max-w-7xl mx-auto space-y-8">
        {/* 1. Workflow Header */}
        <WorkflowTimeline />

        {/* 2. Top Header Banner */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-100 text-[#C2410C] border border-orange-200">
                  STAGE 14 &middot; CREDIT DOSSIER
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Bankable Detailed Project Report (DPR)
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                Institutional DPR & CMA Dossier
              </h1>

              <p className="text-xs sm:text-sm text-[#57534E] max-w-2xl leading-relaxed">
                Automated synthesis of verified project costs, means of finance, 5-year statement projections,
                repayment schedules, DSCR coverage, and downside stress tests formatted for institutional bank appraisal.
              </p>
            </div>

            {/* Action Buttons */}
            <div className="flex flex-wrap items-center gap-3">
              <button
                onClick={handleGenerateDpr}
                disabled={generating}
                className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold shadow-md cursor-pointer flex items-center gap-2 transition-all"
              >
                <RefreshCw className={`w-4 h-4 ${generating ? 'animate-spin' : ''}`} />
                <span>{generating ? 'Compiling Dossier...' : 'Generate Bankable DPR'}</span>
              </button>

              <button
                onClick={handleDownloadPdf}
                className="px-4 py-2.5 rounded-xl text-xs font-bold border border-stone-300 bg-white text-[#1C1917] hover:bg-stone-50 shadow-2xs flex items-center gap-2 transition-all cursor-pointer"
              >
                <Download className="w-4 h-4 text-[#EA580C]" />
                <span>Download Official PDF</span>
              </button>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-red-50 border border-red-200 text-xs text-red-800 flex items-center gap-2">
            <AlertCircle className="w-4 h-4 text-red-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* 3. Data Completeness & Bank Eligibility Banner */}
        {completeness && (
          <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white shadow-2xs space-y-4">
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div
                  className={`w-10 h-10 rounded-xl flex items-center justify-center ${
                    isEligible ? 'bg-emerald-100 text-emerald-700' : 'bg-amber-100 text-amber-700'
                  }`}
                >
                  {isEligible ? <CheckCircle2 className="w-5 h-5" /> : <AlertTriangle className="w-5 h-5" />}
                </div>
                <div>
                  <h3 className="text-sm font-bold text-[#1C1917] font-['Outfit']">
                    Data Completeness & Institutional Gate
                  </h3>
                  <p className="text-xs text-[#57534E]">
                    {completeness.resolved_fields} of {completeness.required_fields_total} financial fields verified
                    &middot; Status: <span className="font-bold">{completeness.status}</span>
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                {dprPackage?.financial_engine_status && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border ${
                      dprPackage.financial_engine_status === 'READY_FOR_DPR'
                        ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                        : dprPackage.financial_engine_status === 'READY_WITH_DISCLOSED_UNKNOWNS'
                        ? 'bg-blue-50 text-blue-800 border-blue-200'
                        : 'bg-amber-50 text-amber-800 border-amber-200'
                    }`}
                  >
                    {dprPackage.financial_engine_status}
                  </span>
                )}
                <span
                  className={`px-3 py-1 rounded-full text-xs font-bold border ${
                    isEligible
                      ? 'bg-emerald-50 text-emerald-800 border-emerald-200'
                      : 'bg-amber-50 text-amber-800 border-amber-200'
                  }`}
                >
                  {isEligible ? 'ELIGIBLE FOR BANK SUBMISSION' : 'INCOMPLETE DRAFT'}
                </span>
              </div>
            </div>

            {/* Unresolved fields notice if any */}
            {completeness.unresolved_fields && completeness.unresolved_fields.length > 0 && (
              <div className="pt-2 border-t border-stone-100 space-y-2">
                <span className="text-[11px] font-bold text-amber-900 block">
                  Pending Verification Inputs:
                </span>
                <div className="flex flex-wrap gap-1.5">
                  {completeness.unresolved_fields.map((f, i) => (
                    <span
                      key={i}
                      className="px-2.5 py-0.5 rounded-md text-[10px] font-medium bg-amber-50 text-amber-800 border border-amber-200"
                    >
                      {f}
                    </span>
                  ))}
                </div>
              </div>
            )}

            {/* Metric Diagnostics / Disclosed Analytical Parameters */}
            {dprPackage?.metric_diagnostics?.some((d) => d.status === 'NOT_AVAILABLE') && (
              <div className="pt-2 border-t border-stone-100 space-y-1.5">
                <span className="text-[11px] font-bold text-blue-900 block">
                  Disclosed Analytical Parameters:
                </span>
                <div className="space-y-1">
                  {dprPackage.metric_diagnostics
                    .filter((d) => d.status === 'NOT_AVAILABLE')
                    .map((diag, i) => (
                      <div
                        key={i}
                        className="text-[11px] text-blue-800 bg-blue-50/70 px-3 py-1.5 rounded-lg border border-blue-200 flex flex-col sm:flex-row sm:items-center justify-between gap-1"
                      >
                        <span className="font-semibold">{diag.metric_name}: {diag.reason_code}</span>
                        <span className="text-[10px] text-blue-600">{diag.diagnostic_note}</span>
                      </div>
                    ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 4. Core Highlights Grid */}
        {dprPackage && (
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-4">
            <div className="royal-card p-4 rounded-xl border border-[#EAE3D5] bg-white text-center">
              <span className="text-[10px] uppercase font-bold text-[#78716C] block">Total Project Cost</span>
              <div className="text-lg font-black text-[#1C1917] font-['Outfit'] mt-1">
                {formatINR(dprPackage.project_cost?.total_project_cost)}
              </div>
            </div>

            <div className="royal-card p-4 rounded-xl border border-[#EAE3D5] bg-white text-center">
              <span className="text-[10px] uppercase font-bold text-[#78716C] block">Term Loan</span>
              <div className="text-lg font-black text-[#C2410C] font-['Outfit'] mt-1">
                {formatINR(dprPackage.loan_structure?.sanctioned_loan_amount)}
              </div>
            </div>

            <div className="royal-card p-4 rounded-xl border border-[#EAE3D5] bg-white text-center">
              <span className="text-[10px] uppercase font-bold text-[#78716C] block">Promoter Margin</span>
              <div className="text-lg font-black text-emerald-700 font-['Outfit'] mt-1">
                {formatINR(dprPackage.means_of_finance?.promoter_contribution)}
              </div>
            </div>

            <div className="royal-card p-4 rounded-xl border border-[#EAE3D5] bg-white text-center">
              <span className="text-[10px] uppercase font-bold text-[#78716C] block">Monthly EMI</span>
              <div className="text-lg font-black text-[#1C1917] font-['Outfit'] mt-1">
                {formatINR(dprPackage.loan_structure?.monthly_emi)}
              </div>
            </div>

            <div className="royal-card p-4 rounded-xl border border-[#EAE3D5] bg-white text-center">
              <span className="text-[10px] uppercase font-bold text-[#78716C] block">Average DSCR</span>
              <div className="text-lg font-black text-blue-700 font-['Outfit'] mt-1">
                {formatRatio(dprPackage.banking_metrics?.average_dscr)}
              </div>
            </div>

            <div className="royal-card p-4 rounded-xl border border-[#EAE3D5] bg-white text-center">
              <span className="text-[10px] uppercase font-bold text-[#78716C] block">Break-Even Sales</span>
              <div className="text-lg font-black text-amber-700 font-['Outfit'] mt-1">
                {formatINR(dprPackage.banking_metrics?.break_even_sales_amount)}
              </div>
            </div>
          </div>
        )}

        {/* 5. 18 Standardized DPR Report Sections */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-xl font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
              <Layers className="w-5 h-5 text-[#EA580C]" />
              Detailed 18-Section Credit Dossier (Institutional Model)
            </h2>
            <span className="text-xs text-[#78716C]">
              {sections.length} Standardized Sections Available
            </span>
          </div>

          <div className="space-y-3">
            {sections.map((sec) => {
              const isOpen = expandedSection === sec.section_number;
              return (
                <div
                  key={sec.section_code}
                  className="royal-card rounded-2xl border border-[#EAE3D5] bg-white overflow-hidden shadow-2xs transition-all"
                >
                  <button
                    onClick={() => setExpandedSection(isOpen ? null : sec.section_number)}
                    className="w-full px-6 py-4 flex items-center justify-between text-left hover:bg-stone-50 transition-colors cursor-pointer"
                  >
                    <div className="flex items-center gap-3">
                      <span className="w-7 h-7 rounded-lg bg-orange-100 text-[#C2410C] font-bold text-xs flex items-center justify-center">
                        {sec.section_number}
                      </span>
                      <div>
                        <h4 className="text-sm font-bold text-[#1C1917]">{sec.title}</h4>
                        <span className="text-[11px] text-[#78716C]">{sec.provenance_tag}</span>
                      </div>
                    </div>
                    {isOpen ? (
                      <ChevronUp className="w-4 h-4 text-[#78716C]" />
                    ) : (
                      <ChevronDown className="w-4 h-4 text-[#78716C]" />
                    )}
                  </button>

                  {isOpen && (
                    <div className="px-6 pb-6 pt-2 border-t border-stone-100 space-y-4 animate-fadeIn">
                      <p className="text-xs text-[#57534E] leading-relaxed bg-[#FAF7F2] p-3.5 rounded-xl border border-[#EAE3D5]">
                        {sec.summary_text}
                      </p>

                      {/* Section Tables */}
                      {sec.tables &&
                        sec.tables.map((t, tIdx) => (
                          <div key={tIdx} className="space-y-2 overflow-x-auto">
                            {t.title && (
                              <h5 className="text-xs font-bold text-[#1C1917] font-['Outfit']">{t.title}</h5>
                            )}
                            <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                              <thead className="bg-[#1E293B] text-white">
                                <tr>
                                  {t.headers.map((h, hIdx) => (
                                    <th key={hIdx} className="px-3.5 py-2 font-bold text-[11px]">
                                      {h}
                                    </th>
                                  ))}
                                </tr>
                              </thead>
                              <tbody className="divide-y divide-stone-100">
                                {t.rows.map((row, rIdx) => (
                                  <tr
                                    key={rIdx}
                                    className={rIdx % 2 === 0 ? 'bg-white' : 'bg-[#FAF7F2]'}
                                  >
                                    {row.map((cell, cIdx) => (
                                      <td
                                        key={cIdx}
                                        className={`px-3.5 py-2 ${
                                          cIdx === 0
                                            ? 'font-semibold text-[#1C1917]'
                                            : cell === 'Not available' || cell === 'Pending verification'
                                            ? 'text-[#A8A29E] italic'
                                            : 'text-[#44403C]'
                                        }`}
                                      >
                                        {cell}
                                      </td>
                                    ))}
                                  </tr>
                                ))}
                              </tbody>
                            </table>
                          </div>
                        ))}

                      {/* Notes and Disclosures */}
                      {sec.notes_and_disclosures && sec.notes_and_disclosures.length > 0 && (
                        <div className="text-[11px] text-[#78716C] space-y-1 bg-stone-50 p-3 rounded-lg border border-stone-200">
                          <span className="font-bold text-[#1C1917] block">Appraisal Disclosures & Notes:</span>
                          {sec.notes_and_disclosures.map((n, nIdx) => (
                            <div key={nIdx} className="flex items-start gap-1.5">
                              <span className="text-[#EA580C]">&bull;</span>
                              <span>{n}</span>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </div>

        {/* 6. Bottom Navigation Call To Action */}
        <div className="royal-panel rounded-2xl p-6 border border-[#EAE3D5] flex flex-col sm:flex-row items-center justify-between gap-4">
          <div>
            <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
              Stage 14 Complete — Loan Dossier Bank-Ready
            </h3>
            <p className="text-xs text-[#57534E]">
              Proceed to Personal AI Assistant for interview prep and scheme application submission.
            </p>
          </div>
          <Link to="/assistant">
            <Button size="md" icon={ArrowRight}>
              Proceed to AI Assistant (Stage 15)
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
};

export default DPRPage;
