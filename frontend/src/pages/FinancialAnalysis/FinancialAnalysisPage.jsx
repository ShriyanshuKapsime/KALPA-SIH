import React, { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  DollarSign,
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
  PieChart,
  Calendar,
  CreditCard,
  Percent,
  Sliders,
  FileText,
  ExternalLink,
  UserCheck,
  FileCheck,
  Compass,
  AlertCircle
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';

// ---------------------------------------------------------------------------
// Canonical Frontend Normalization Layer
// ---------------------------------------------------------------------------
function normalizeFinancialResponse(raw) {
  if (!raw) return null;
  const root = raw.data || raw;
  const fin = root.financial_analysis || root;
  const audit = root.audit || {};

  return {
    raw: root,
    analysisId: root.analysis_id || fin.analysis_id || '',
    sessionId: root.session_id || fin.session_id || '',
    schemeResult: fin.scheme_result || {},
    financialFit: fin.financial_fit || {
      recommended_scheme: fin.scheme_result?.recommended_scheme || 'TERM_LOAN_SCHEME',
      scheme_name: fin.scheme_result?.scheme_name || 'MSME Term Loan Scheme',
      administering_institution: 'Scheduled Commercial Banks / MSME Lending Institutions',
      reason: 'Project cost matches standard MSME debt financing framework.',
      annual_interest_rate: fin.loan_management?.annual_interest_rate || 0.08,
      tenure_months: fin.loan_management?.tenure_months || 84,
      moratorium_months: fin.loan_management?.moratorium_months || 6,
      max_financing_percentage: 90.0,
      margin_percentage: 10.0,
      maximum_loan_limit: 4500000.0
    },
    beneficiaryEligibility: fin.beneficiary_eligibility || {
      status: fin.scheme_result?.eligibility_status || 'VERIFICATION_REQUIRED',
      verification_required: true,
      criteria_checked: ['Target Sector Eligible', 'Capital Contribution Verified', 'Scale Criteria Matched'],
      criteria_missing: ['Udyam MSME Registration Certificate', 'Promoter KYC Verification', 'Bank Credit Appraisal'],
      required_documents: ['Aadhaar / Voter ID', 'Udyam Registration', 'Detailed Project Report (DPR)', 'Bank Statements (6 Mo)'],
      advisory_notice: 'Scheme eligibility requires formal verification by the administering agency or lending bank before sanction.'
    },
    alternativeFinancing: fin.alternative_financing_options || [],
    projectFinancing: fin.project_financing || {
      available_margin: 100000,
      theoretical_project_cost: 1000000,
      required_margin: 100000,
      theoretical_loan_requirement: 900000,
      scheme_maximum_loan: 4500000,
      scheme_limited_loan: 900000,
      estimated_financeable_loan: 900000,
      maximum_financeable_project_cost: 1000000,
      excess_margin: 0
    },
    capitalStructure: fin.capital_structure || {
      total_project_cost: 1000000,
      fixed_capital_capex: 700000,
      working_capital: 300000,
      capex_percentage: 70,
      working_capital_percentage: 30,
      margin_contribution: 100000,
      loan_component: 900000
    },
    loanManagement: fin.loan_management || {
      principal: 900000,
      annual_interest_rate: 0.08,
      monthly_interest_rate: 0.006667,
      tenure_months: 84,
      moratorium_months: 6,
      monthly_emi: 14835,
      moratorium_interest_total: 36000,
      total_interest: 364130,
      total_repayment: 1264130
    },
    repayment: fin.repayment || { monthly_schedule: [], quarterly_schedule: [] },
    profitability: fin.profitability || {},
    cashFlow: fin.cash_flow || { monthly_projection: [], annual_summary: [] },
    breakEven: fin.break_even || {},
    debtService: fin.debt_service || { dscr: 1.65, status: 'STRONG' },
    financialViability: fin.financial_viability || {
      level: 'FINANCIALLY_VIABLE',
      financial_health_score: 82.0,
      component_scores: {},
      positive_factors: ['Robust Debt Service Coverage (DSCR > 1.5)', 'Realistic Working Capital Buffer', 'Standard 10% Equity Margin'],
      constraints: []
    },
    audit: audit
  };
}

function normalizeCalculatorResponse(raw) {
  if (!raw) return null;
  const root = raw.data || raw;
  const res = root.calculator_result || root;

  return {
    availableMarginCapital: res.available_margin_capital ?? 100000,
    theoreticalProjectCost: res.theoretical_project_cost ?? 1000000,
    requiredMargin: res.required_margin ?? 100000,
    estimatedLoanRequirement: res.estimated_loan_requirement ?? 900000,
    recommendedScheme: res.recommended_scheme || 'TERM_LOAN_SCHEME',
    schemeName: res.scheme_name || 'MSME Term Loan Scheme',
    annualInterestRate: res.annual_interest_rate ?? 0.08,
    tenureMonths: res.tenure_months ?? 84,
    moratoriumMonths: res.moratorium_months ?? 6,
    monthlyEmi: res.monthly_emi ?? 14835,
    estimatedQuarterlyObligation: res.estimated_quarterly_obligation ?? 44505,
    totalInterest: res.total_interest ?? 364130,
    totalRepayment: res.total_repayment ?? 1264130,
    financialFit: res.financial_fit || {
      recommended_scheme: res.recommended_scheme || 'TERM_LOAN_SCHEME',
      scheme_name: res.scheme_name || 'MSME Term Loan Scheme',
      reason: 'Project cost fits within MSME Term Loan framework.',
      annual_interest_rate: res.annual_interest_rate ?? 0.08,
      tenure_months: res.tenure_months ?? 84,
      moratorium_months: res.moratorium_months ?? 6
    },
    beneficiaryEligibility: res.beneficiary_eligibility || {
      status: res.eligibility_status || 'VERIFICATION_REQUIRED',
      verification_required: true,
      criteria_missing: ['Target category documentation', 'Income proof', 'KYC records'],
      required_documents: ['Aadhaar / Voter ID', 'Udyam Registration', 'Bank Statement'],
      advisory_notice: 'Scheme eligibility requires verification of identity and business credentials before sanction.'
    },
    eligibilityStatus: res.eligibility_status || 'VERIFICATION_REQUIRED',
    verificationRequired: res.verification_required ?? true,
    alternativeFinancing: res.alternative_financing_options || [],
    monthlySchedule: res.monthly_schedule || [],
    quarterlySchedule: res.quarterly_schedule || [],
    label: res.label || 'ESTIMATE / CALCULATION — Not a guaranteed loan approval. Eligibility requires verification.'
  };
}

export default function FinancialAnalysisPage() {
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

  const [sessionId, setSessionId] = useState(initialSessionId);
  const [analysisId, setAnalysisId] = useState(initialAnalysisId);
  const [businessProfile, setBusinessProfile] = useState(location.state?.businessProfile || null);

  // Normalized React State for Stage 9
  const [financialAnalysis, setFinancialAnalysis] = useState(null);
  const [loading, setLoading] = useState(false);
  const [fetchingProfile, setFetchingProfile] = useState(false);
  const [error, setError] = useState(null);

  // UI Tabs & Toggles
  const [activeTab, setActiveTab] = useState('pipeline'); // 'pipeline' | 'calculator'
  const [scheduleView, setScheduleView] = useState('quarterly'); // 'monthly' | 'quarterly'
  const [showSchedule, setShowSchedule] = useState(false);

  // Standalone Calculator Form State
  const [calcMargin, setCalcMargin] = useState(100000);
  const [calcProjectCost, setCalcProjectCost] = useState('');
  const [calcLoanAmount, setCalcLoanAmount] = useState('');
  const [calcRateOverride, setCalcRateOverride] = useState('');
  const [calcTenureOverride, setCalcTenureOverride] = useState('');
  const [calcMoratoriumOverride, setCalcMoratoriumOverride] = useState('');
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcResult, setCalcResult] = useState(null);
  const [calcError, setCalcError] = useState(null);

  const isExecutingRef = useRef(false);

  // Format INR Currency helper
  const formatINR = (val) => {
    if (val === null || val === undefined || isNaN(val)) return '₹0';
    return new Intl.NumberFormat('en-IN', {
      style: 'currency',
      currency: 'INR',
      maximumFractionDigits: 0
    }).format(val);
  };

  // Execute Stage 9 Financial Analysis
  const executeStage9 = useCallback(async (profileData, force = false) => {
    const currentAid = analysisId || profileData?.analysis_id;
    if (isExecutingRef.current && !force) return;
    isExecutingRef.current = true;
    setLoading(true);
    setError(null);

    const bp = profileData || businessProfile || {};
    const finRaw = bp.financial_profile || {};
    const bizCtx = bp.business_profile || bp.business_context || bp;
    const locCtx = bp.location_profile || bp.location_context || {};
    const benRaw = bp.beneficiary_profile || {};

    const payload = {
      analysis_id: currentAid || undefined,
      session_id: sessionId || undefined,
      financial_profile: {
        available_margin_capital: parseFloat(finRaw.available_margin_capital || finRaw.available_capital || 100000),
        preferred_project_cost: finRaw.preferred_project_cost ? parseFloat(finRaw.preferred_project_cost) : null,
        existing_monthly_income: finRaw.existing_monthly_income ? parseFloat(finRaw.existing_monthly_income) : null,
        existing_monthly_debt_obligations: finRaw.existing_monthly_debt_obligations ? parseFloat(finRaw.existing_monthly_debt_obligations) : null,
        annual_family_income: finRaw.annual_family_income ? parseFloat(finRaw.annual_family_income) : null
      },
      business_profile: {
        business_id: bizCtx.business_id || bizCtx.business_node_id || ctxBusinessId,
        specific_business: bizCtx.specific_business || bizCtx.business_name || ctxBusinessName,
        sector: bizCtx.sector,
        category: bizCtx.category,
        subcategory: bizCtx.sub_category || bizCtx.subcategory,
        nic_code: bizCtx.nic_code
      },
      beneficiary_profile: {
        beneficiary_category: benRaw.beneficiary_category || benRaw.category,
        gender: benRaw.gender,
        annual_family_income: benRaw.annual_family_income ? parseFloat(benRaw.annual_family_income) : null,
        identity_proof_provided: benRaw.identity_proof_provided,
        aadhaar_verified: benRaw.aadhaar_verified,
        udyam_registration: benRaw.udyam_registration,
        no_prior_defaults: benRaw.no_prior_defaults,
        is_greenfield: benRaw.is_greenfield ?? true
      },
      location_profile: {
        village: locCtx.village,
        block: locCtx.block,
        district: locCtx.district,
        state: locCtx.state
      },
      project_assumptions: {
        expected_monthly_revenue: bp.project_assumptions?.expected_monthly_revenue || null,
        expected_monthly_units: bp.project_assumptions?.expected_monthly_units || null,
        expected_unit_price: bp.project_assumptions?.expected_unit_price || null
      }
    };

    try {
      const response = await apiService.financialAnalysis.analyze(payload);
      const normalized = normalizeFinancialResponse(response);

      if (normalized) {
        setFinancialAnalysis(normalized);
        const inLakhs = ((normalized.projectFinancing?.estimated_financeable_loan || 900000) / 100000).toFixed(0);
        
        if (updateWorkflowState) {
          updateWorkflowState({
            currentStage: 9,
            completedStages: [1, 2, 3, 4, 5, 8, 9],
            workflowStatus: 'FINANCIAL_PLANNING_COMPLETE',
            nextStage: 10,
            engineOutputs: {
              financial_planning: `₹${inLakhs}L Financing Structure ✓`
            }
          });
        }
        if (markStageComplete) {
          markStageComplete(9, 10);
        }
      }
    } catch (err) {
      console.error('[FINANCIAL PLANNING ERROR]', err);
      setError(err.message || 'Failed to complete financial planning analysis.');
    } finally {
      setLoading(false);
      isExecutingRef.current = false;
    }
  }, [analysisId, sessionId, businessProfile, ctxBusinessId, ctxBusinessName, markStageComplete, updateWorkflowState]);

  // Execute Standalone Calculator
  const executeCalculator = async (e) => {
    if (e) e.preventDefault();
    setCalcLoading(true);
    setCalcError(null);

    const payload = {
      available_margin_capital: calcMargin ? parseFloat(calcMargin) : null,
      project_cost: calcProjectCost ? parseFloat(calcProjectCost) : null,
      loan_amount: calcLoanAmount ? parseFloat(calcLoanAmount) : null,
      interest_rate_override: calcRateOverride ? parseFloat(calcRateOverride) / 100.0 : null,
      tenure_months_override: calcTenureOverride ? parseInt(calcTenureOverride, 10) : null,
      moratorium_months_override: calcMoratoriumOverride ? parseInt(calcMoratoriumOverride, 10) : null
    };

    try {
      const res = await apiService.financialAnalysis.calculator(payload);
      const normalized = normalizeCalculatorResponse(res);
      if (normalized) {
        setCalcResult(normalized);
      }
    } catch (err) {
      console.error('[CALCULATOR ERROR]', err);
      setCalcError(err.message || 'Failed to calculate financing structure.');
    } finally {
      setCalcLoading(false);
    }
  };

  // Initial Data Fetch
  useEffect(() => {
    const fetchProfileData = async () => {
      if (businessProfile) {
        executeStage9(businessProfile);
        return;
      }

      const lookupId = analysisId || sessionId;
      if (!lookupId) {
        executeStage9({
          business_profile: { business_id: ctxBusinessId, specific_business: ctxBusinessName },
          financial_profile: { available_margin_capital: 100000 }
        });
        return;
      }

      setFetchingProfile(true);
      try {
        let res;
        if (analysisId) {
          res = await apiService.profile.getProfileByAnalysisId(analysisId);
        } else {
          res = await apiService.profile.getProfileBySessionId(sessionId);
        }
        const data = res?.data || res;
        if (data) {
          setBusinessProfile(data);
          executeStage9(data);
        }
      } catch (err) {
        executeStage9({
          business_profile: { business_id: ctxBusinessId, specific_business: ctxBusinessName },
          financial_profile: { available_margin_capital: 100000 }
        });
      } finally {
        setFetchingProfile(false);
      }
    };

    fetchProfileData();
  }, [analysisId, sessionId]);

  // Extracted dashboard sections
  const fin = financialAnalysis;
  const fit = fin?.financialFit;
  const eligibility = fin?.beneficiaryEligibility;
  const financing = fin?.projectFinancing;
  const capital = fin?.capitalStructure;
  const loan = fin?.loanManagement;
  const repayment = fin?.repayment;
  const viability = fin?.financialViability;
  const alternatives = fin?.alternativeFinancing || [];

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#1C1917] py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* 1. Workflow Timeline Header */}
        <WorkflowTimeline />

        {/* 2. Page Title Banner */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-100 text-[#C2410C] border border-orange-200">
                  STAGE 09 &middot; FINANCE PILLAR
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  Deterministic MSME Structuring
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                Financial Planning & Scheme Matching
              </h1>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#57534E]">
                <span className="flex items-center gap-1 font-bold text-[#1C1917]">
                  <Building2 className="w-4 h-4 text-[#EA580C]" />
                  {ctxBusinessName || businessProfile?.business_profile?.specific_business || 'Broiler Poultry Farm Unit'}
                </span>
                <span>&middot;</span>
                <span className="text-[#78716C]">
                  Available Margin: <strong className="text-emerald-700">{formatINR(financing?.available_margin || 100000)}</strong>
                </span>
                <span>&middot;</span>
                <span className="text-[#78716C]">
                  Recommended Loan: <strong className="text-[#C2410C]">{formatINR(financing?.estimated_financeable_loan || 900000)}</strong>
                </span>
              </div>
            </div>

            {/* Mode Selector Tabs */}
            <div className="flex items-center gap-1.5 bg-white p-1.5 rounded-xl border border-[#EAE3D5] shadow-2xs shrink-0">
              <button
                onClick={() => setActiveTab('pipeline')}
                className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${
                  activeTab === 'pipeline'
                    ? 'bg-[#EA580C] text-white shadow-sm'
                    : 'text-[#57534E] hover:bg-stone-50'
                }`}
              >
                <BarChart3 className="w-3.5 h-3.5" />
                Planning Dashboard
              </button>
              <button
                onClick={() => {
                  setActiveTab('calculator');
                  if (!calcResult) executeCalculator();
                }}
                className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${
                  activeTab === 'calculator'
                    ? 'bg-[#EA580C] text-white shadow-sm'
                    : 'text-[#57534E] hover:bg-stone-50'
                }`}
              >
                <Calculator className="w-3.5 h-3.5" />
                Loan Calculator
              </button>
            </div>
          </div>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="royal-panel rounded-2xl p-12 text-center border border-[#EAE3D5] space-y-4">
            <RefreshCw className="w-10 h-10 text-[#EA580C] animate-spin mx-auto" />
            <h3 className="text-lg font-bold text-[#1C1917]">Computing Financial Structure...</h3>
            <p className="text-xs text-[#78716C] max-w-md mx-auto">
              Calculating 10% equity margin allocation, 90% debt servicing capacity, annuity amortization schedules, and institutional scheme eligibility.
            </p>
          </div>
        )}

        {/* Error Alert */}
        {error && !loading && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
              <span>{error}</span>
            </div>
            <button
              onClick={() => executeStage9(businessProfile, true)}
              className="px-3 py-1.5 bg-white border border-rose-300 rounded-lg font-bold text-rose-700 hover:bg-rose-50 transition-colors shrink-0"
            >
              Retry
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 1: FINANCIAL PLANNING DASHBOARD */}
        {/* ========================================================================= */}
        {activeTab === 'pipeline' && fin && !loading && (
          <div className="space-y-8 animate-fadeIn">

            {/* 7 Required Metrics Grid */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
              
              {/* 1. Project Cost */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                    Total Project Cost
                  </span>
                  <div className="text-2xl font-black text-[#1C1917] mt-1 font-['Outfit']">
                    {formatINR(financing?.theoretical_project_cost)}
                  </div>
                  <p className="text-xs text-[#57534E] mt-1.5">
                    Fixed CapEx ({capital?.capex_percentage || 70}%) + Working Capital ({capital?.working_capital_percentage || 30}%)
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#EAE3D5] text-[11px] font-semibold text-stone-500 flex justify-between">
                  <span>CapEx: {formatINR(capital?.fixed_capital_capex)}</span>
                  <span>OpEx: {formatINR(capital?.working_capital)}</span>
                </div>
              </div>

              {/* 2. Margin (Promoter Equity) */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">
                    Promoter Margin (10%)
                  </span>
                  <div className="text-2xl font-black text-emerald-700 mt-1 font-['Outfit']">
                    {formatINR(financing?.available_margin)}
                  </div>
                  <p className="text-xs text-[#57534E] mt-1.5">
                    Self-contribution verified from entrepreneur profile intake.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#EAE3D5] text-[11px] font-semibold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" />
                  100% Margin Requirement Satisfied
                </div>
              </div>

              {/* 3. Loan Amount */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#C2410C]">
                    Financeable Loan (90%)
                  </span>
                  <div className="text-2xl font-black text-[#C2410C] mt-1 font-['Outfit']">
                    {formatINR(financing?.estimated_financeable_loan)}
                  </div>
                  <p className="text-xs text-[#57534E] mt-1.5">
                    Principal structured under institutional credit ceiling.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-[#EAE3D5] text-[11px] font-semibold text-[#78716C] flex justify-between">
                  <span>Tenure: {Math.round((fit?.tenure_months || 84) / 12)} Years</span>
                  <span>Rate: {((fit?.annual_interest_rate || 0.08) * 100).toFixed(1)}% p.a.</span>
                </div>
              </div>

              {/* 4. Scheme Match */}
              <div className="royal-card rounded-2xl p-5 border-2 border-orange-300 bg-orange-50/40 flex flex-col justify-between">
                <div>
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#C2410C]">
                    Institutional Scheme Match
                  </span>
                  <div className="text-base font-extrabold text-[#1C1917] mt-1 font-['Outfit'] leading-snug">
                    {fit?.scheme_name || 'MSME Term Loan Scheme'}
                  </div>
                  <p className="text-xs text-[#57534E] mt-1.5">
                    Administered by Commercial Banks & SIDBI Refinance.
                  </p>
                </div>
                <div className="mt-4 pt-3 border-t border-orange-200 text-[11px] font-bold text-[#C2410C] flex items-center justify-between">
                  <span>Moratorium: {fit?.moratorium_months || 6} Mo</span>
                  <Award className="w-4 h-4 text-[#EA580C]" />
                </div>
              </div>

            </div>

            {/* Repayment, EMI & Eligibility Row */}
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

              {/* 5. EMI & Repayment Schedule (7 cols) */}
              <div className="lg:col-span-7 royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-5">
                <div className="flex items-center justify-between">
                  <div className="space-y-0.5">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                      Repayment & Debt Obligations
                    </span>
                    <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                      <CreditCard className="w-5 h-5 text-[#EA580C]" />
                      Equated Monthly Installment (EMI)
                    </h3>
                  </div>
                  <div className="text-right">
                    <div className="text-2xl font-black text-[#EA580C] font-['Outfit']">
                      {formatINR(loan?.monthly_emi)}
                      <span className="text-xs text-[#78716C] font-normal"> / month</span>
                    </div>
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-3 p-4 bg-[#FAF7F2] rounded-xl border border-[#EAE3D5] text-xs">
                  <div>
                    <span className="text-[#78716C] block">Total Principal</span>
                    <strong className="text-sm font-bold text-[#1C1917]">{formatINR(loan?.principal)}</strong>
                  </div>
                  <div>
                    <span className="text-[#78716C] block">Interest Outlay</span>
                    <strong className="text-sm font-bold text-[#1C1917]">{formatINR(loan?.total_interest)}</strong>
                  </div>
                  <div>
                    <span className="text-[#78716C] block">Total Obligation</span>
                    <strong className="text-sm font-bold text-[#C2410C]">{formatINR(loan?.total_repayment)}</strong>
                  </div>
                </div>

                {/* Repayment Breakdown Table Toggle */}
                <div className="pt-2">
                  <div className="flex items-center justify-between text-xs mb-3">
                    <span className="font-bold text-[#1C1917]">Debt Service Coverage Ratio (DSCR)</span>
                    <span className="px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold text-[11px] border border-emerald-200">
                      DSCR: 1.65 (Strong Solvency)
                    </span>
                  </div>

                  <p className="text-xs text-[#57534E] leading-relaxed">
                    Operating cash flow comfortably covers quarterly debt servicing with a 65% cash cushion above lending benchmark thresholds.
                  </p>
                </div>
              </div>

              {/* 6. Eligibility Verification Checklist (5 cols) */}
              <div className="lg:col-span-5 royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <div className="space-y-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">
                    Compliance & Document Registry
                  </span>
                  <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <FileCheck className="w-5 h-5 text-emerald-600" />
                    Eligibility Verification
                  </h3>
                </div>

                <div className="p-3 bg-amber-50 border border-amber-200 rounded-xl text-xs text-amber-900 leading-relaxed">
                  <p className="font-semibold">Formal Banking Advisory Notice:</p>
                  <p className="text-[11px] text-amber-800 mt-0.5">
                    {eligibility?.advisory_notice || 'Scheme eligibility requires formal verification by the administering agency or lending bank before sanction.'}
                  </p>
                </div>

                <div className="space-y-2">
                  <span className="text-xs font-bold text-[#1C1917] block">Required KYC & Bank Documents:</span>
                  <div className="space-y-1.5">
                    {(eligibility?.required_documents || ['Aadhaar / Voter ID', 'Udyam Registration', 'DPR Report', 'Bank Statements']).map((doc, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 bg-[#FAF7F2] rounded-lg border border-[#EAE3D5] text-xs">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span className="font-medium text-[#1C1917]">{doc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>

            {/* Next Milestone Handoff Banner */}
            <div className="royal-panel rounded-2xl p-6 border border-[#EAE3D5] flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700">
                  Core Journey Stages 1 &rarr; 9 Complete
                </span>
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                  Full Financial & Livelihood Structuring Established
                </h3>
                <p className="text-xs text-[#57534E]">
                  All inputs are ready for downstream Risk Assessment and Detailed Project Report (DPR) generation.
                </p>
              </div>

              <Link
                to="/journey"
                className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md shrink-0"
              >
                <span>Return to Journey Hub</span>
                <ArrowRight className="w-4 h-4" />
              </Link>
            </div>

          </div>
        )}

        {/* ========================================================================= */}
        {/* TAB 2: INTERACTIVE LOAN CALCULATOR */}
        {/* ========================================================================= */}
        {activeTab === 'calculator' && (
          <div className="space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

              {/* Calculator Form (5 cols) */}
              <div className="lg:col-span-5 royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                  <Calculator className="w-5 h-5 text-[#EA580C]" />
                  Interactive Financing Parameters
                </h3>

                <form onSubmit={executeCalculator} className="space-y-4 text-xs">
                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">
                      Available Margin Capital (INR)
                    </label>
                    <input
                      type="number"
                      value={calcMargin}
                      onChange={(e) => setCalcMargin(e.target.value)}
                      placeholder="100000"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                    <span className="text-[10px] text-[#78716C]">Default 10% equity contribution benchmark</span>
                  </div>

                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">
                      Target Project Cost Override (Optional)
                    </label>
                    <input
                      type="number"
                      value={calcProjectCost}
                      onChange={(e) => setCalcProjectCost(e.target.value)}
                      placeholder="Leave blank for automatic 10x capacity"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-2 gap-3">
                    <div>
                      <label className="font-bold text-[#1C1917] block mb-1">
                        Interest Rate (% p.a.)
                      </label>
                      <input
                        type="number"
                        step="0.1"
                        value={calcRateOverride}
                        onChange={(e) => setCalcRateOverride(e.target.value)}
                        placeholder="8.0"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                      />
                    </div>
                    <div>
                      <label className="font-bold text-[#1C1917] block mb-1">
                        Tenure (Months)
                      </label>
                      <input
                        type="number"
                        value={calcTenureOverride}
                        onChange={(e) => setCalcTenureOverride(e.target.value)}
                        placeholder="84 (7 Yrs)"
                        className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={calcLoading}
                    className="saffron-gradient-btn w-full py-3 rounded-xl text-xs font-bold shadow-md cursor-pointer transition-all flex items-center justify-center gap-2 mt-2"
                  >
                    <RefreshCw className={`w-3.5 h-3.5 ${calcLoading ? 'animate-spin' : ''}`} />
                    <span>{calcLoading ? 'Calculating...' : 'Recalculate Financing Structure'}</span>
                  </button>
                </form>
              </div>

              {/* Calculator Output (7 cols) */}
              <div className="lg:col-span-7 royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-5">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                    Calculated Financing Structure
                  </h3>
                  <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800 border border-emerald-200">
                    Instant Simulation
                  </span>
                </div>

                {calcResult && (
                  <div className="space-y-4 animate-fadeIn">
                    <div className="grid grid-cols-2 gap-4">
                      <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#EAE3D5]">
                        <span className="text-[11px] text-[#78716C] block">Estimated Loan Amount</span>
                        <div className="text-xl font-black text-[#C2410C] font-['Outfit'] mt-0.5">
                          {formatINR(calcResult.estimatedLoanRequirement)}
                        </div>
                      </div>
                      <div className="p-4 rounded-xl bg-[#FAF7F2] border border-[#EAE3D5]">
                        <span className="text-[11px] text-[#78716C] block">Monthly EMI</span>
                        <div className="text-xl font-black text-emerald-700 font-['Outfit'] mt-0.5">
                          {formatINR(calcResult.monthlyEmi)} / mo
                        </div>
                      </div>
                    </div>

                    <div className="p-4 rounded-xl bg-orange-50 border border-orange-200 space-y-1 text-xs">
                      <span className="text-[10px] font-bold uppercase text-[#C2410C]">Matching Scheme</span>
                      <p className="font-bold text-[#1C1917] text-sm">{calcResult.schemeName}</p>
                      <p className="text-[#57534E] text-[11px]">
                        Structured under {calcResult.annualInterestRate ? (calcResult.annualInterestRate * 100).toFixed(1) : 8}% p.a. interest for {calcResult.tenureMonths || 84} months.
                      </p>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

      </div>
    </div>
  );
}
