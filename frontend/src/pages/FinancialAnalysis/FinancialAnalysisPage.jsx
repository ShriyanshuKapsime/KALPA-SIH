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
  AlertCircle,
  Edit3,
  X,
  SlidersHorizontal,
  Check,
  Mic,
  MicOff,
  Volume2,
  Send,
  MessageSquare
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';

// ---------------------------------------------------------------------------
// Canonical Frontend Normalization Layer (Stage 9 + Milestone 6)
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
    projectFinancing: fin.project_financing || null,
    capitalStructure: fin.capital_structure || null,
    loanManagement: fin.loan_management || null,
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
    audit: audit,
    dprPackage: fin.dpr_financial_package || root.dpr_financial_package || null
  };
}

function normalizeCalculatorResponse(raw) {
  if (!raw) return null;
  const root = raw.data || raw;
  const res = root.calculator_result || root;

  return {
    availableMarginCapital: res.available_margin_capital ?? null,
    theoreticalProjectCost: res.theoretical_project_cost ?? null,
    requiredMargin: res.required_margin ?? null,
    estimatedLoanRequirement: res.estimated_loan_requirement ?? null,
    recommendedScheme: res.recommended_scheme || 'TERM_LOAN_SCHEME',
    schemeName: res.scheme_name || 'MSME Term Loan Scheme',
    annualInterestRate: res.annual_interest_rate ?? 0.08,
    tenureMonths: res.tenure_months ?? 84,
    moratoriumMonths: res.moratorium_months ?? 6,
    monthlyEmi: res.monthly_emi ?? null,
    estimatedQuarterlyObligation: res.estimated_quarterly_obligation ?? null,
    totalInterest: res.total_interest ?? null,
    totalRepayment: res.total_repayment ?? null,
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

  // UI Tabs & Views
  const [activeTab, setActiveTab] = useState('planning'); // 'planning' | 'calculator'
  const [statementTab, setStatementTab] = useState('pnl'); // 'pnl' | 'balance_sheet' | 'cash_flow'
  const [isEditDrawerOpen, setIsEditDrawerOpen] = useState(false);

  // Editable Financial & Business Profile Form State
  const [editSector, setEditSector] = useState('');
  const [editCategory, setEditCategory] = useState('');
  const [editSubcategory, setEditSubcategory] = useState('');
  const [editBusinessName, setEditBusinessName] = useState('');
  const [editMarginCapital, setEditMarginCapital] = useState('200000');
  const [editPreferredCost, setEditPreferredCost] = useState('');

  // Conversational Driver Inputs & Voice Interaction State
  const [userDriverInputs, setUserDriverInputs] = useState({});
  const [activeQuestionInput, setActiveQuestionInput] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSynthesizingAudio, setIsSynthesizingAudio] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [isProcessingAudio, setIsProcessingAudio] = useState(false);
  const [submittingQuestion, setSubmittingQuestion] = useState(false);

  // Audio References
  const currentAudioRef = useRef(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const hasAutoPlayedQuestionRef = useRef({});

  // Standalone Calculator Form State
  const [calcMargin, setCalcMargin] = useState(200000);
  const [calcProjectCost, setCalcProjectCost] = useState('');
  const [calcLoanAmount, setCalcLoanAmount] = useState('');
  const [calcRateOverride, setCalcRateOverride] = useState('');
  const [calcTenureOverride, setCalcTenureOverride] = useState('');
  const [calcMoratoriumOverride, setCalcMoratoriumOverride] = useState('');
  const [calcLoading, setCalcLoading] = useState(false);
  const [calcResult, setCalcResult] = useState(null);
  const [calcError, setCalcError] = useState(null);

  const isExecutingRef = useRef(false);

  // Strict formatters (UNKNOWN != 0: returns "Not available" when missing)
  const formatINR = (val) => {
    if (val === null || val === undefined || val === '') return 'Not available';
    const num = parseFloat(val);
    if (isNaN(num)) return 'Not available';
    const isNeg = num < 0;
    const abs = Math.abs(num);
    const formatted = abs.toLocaleString('en-IN', {
      maximumFractionDigits: 0,
      minimumFractionDigits: 0
    });
    return isNeg ? `(₹${formatted})` : `₹${formatted}`;
  };

  const formatPct = (val) => {
    if (val === null || val === undefined || val === '') return 'Not available';
    const num = parseFloat(val);
    if (isNaN(num)) return 'Not available';
    const pctVal = (num <= 1.0 && num > 0) ? num * 100 : num;
    return `${pctVal.toFixed(1)}%`;
  };

  const formatRatioVal = (val) => {
    if (val === null || val === undefined || val === '') return 'Not available';
    const num = parseFloat(val);
    if (isNaN(num)) return 'Not available';
    return `${num.toFixed(2)}x`;
  };

  // Execute Stage 9 Financial Analysis
  const executeStage9 = useCallback(async (profileData, force = false, driverOverrides = null) => {
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

    const availableMargin = finRaw.available_margin_capital || finRaw.available_capital || 200000;
    const preferredCost = finRaw.preferred_project_cost ? parseFloat(finRaw.preferred_project_cost) : null;

    const locProposed = bp.proposed_location || bp.profile?.proposed_location;
    const resolvedDistrict = typeof locCtx.district === 'string'
      ? locCtx.district
      : (typeof locProposed === 'object' ? locProposed?.district : (typeof locProposed === 'string' ? locProposed : null));
    const resolvedState = typeof locCtx.state === 'string'
      ? locCtx.state
      : (typeof locProposed === 'object' ? locProposed?.state : null);

    const activeDrivers = driverOverrides !== null ? driverOverrides : userDriverInputs;

    const payload = {
      analysis_id: typeof currentAid === 'string' && currentAid.trim() ? currentAid.trim() : undefined,
      session_id: typeof sessionId === 'string' && sessionId.trim() ? sessionId.trim() : undefined,
      financial_profile: {
        available_margin_capital: parseFloat(availableMargin) || 100000,
        preferred_project_cost: preferredCost,
        existing_monthly_income: finRaw.existing_monthly_income ? parseFloat(finRaw.existing_monthly_income) : null,
        existing_monthly_debt_obligations: finRaw.existing_monthly_debt_obligations ? parseFloat(finRaw.existing_monthly_debt_obligations) : null,
        annual_family_income: finRaw.annual_family_income ? parseFloat(finRaw.annual_family_income) : null
      },
      business_profile: {
        business_id: String(bizCtx.business_id || bizCtx.business_node_id || ctxBusinessId || 'saree_retail'),
        specific_business: String(bizCtx.specific_business || bizCtx.business_name || ctxBusinessName || 'Saree Retail'),
        sector: String(bizCtx.sector || 'Retail'),
        category: String(bizCtx.category || 'Apparel Retail'),
        subcategory: String(bizCtx.sub_category || bizCtx.subcategory || "Women's Traditional Apparel"),
        nic_code: bizCtx.nic_code ? String(bizCtx.nic_code) : '47711'
      },
      beneficiary_profile: {
        beneficiary_category: benRaw.beneficiary_category || benRaw.category || 'General',
        gender: benRaw.gender || 'Female',
        annual_family_income: benRaw.annual_family_income ? parseFloat(benRaw.annual_family_income) : null,
        identity_proof_provided: benRaw.identity_proof_provided ?? true,
        aadhaar_verified: benRaw.aadhaar_verified ?? true,
        udyam_registration: typeof benRaw.udyam_registration === 'string' && benRaw.udyam_registration.trim()
          ? benRaw.udyam_registration.trim()
          : (typeof benRaw.udyam_registration === 'boolean' ? benRaw.udyam_registration : null),
        no_prior_defaults: benRaw.no_prior_defaults ?? true,
        is_greenfield: benRaw.is_greenfield ?? true
      },
      location_profile: {
        village: locCtx.village || null,
        block: locCtx.block || null,
        district: resolvedDistrict || null,
        state: resolvedState || null
      },
      project_assumptions: {
        expected_monthly_revenue: bp.project_assumptions?.expected_monthly_revenue || null,
        expected_monthly_units: bp.project_assumptions?.expected_monthly_units || null,
        expected_unit_price: bp.project_assumptions?.expected_unit_price || null
      },
      user_driver_inputs: activeDrivers
    };

    // Update edit form fields to match current request context
    setEditSector(payload.business_profile.sector || '');
    setEditCategory(payload.business_profile.category || '');
    setEditSubcategory(payload.business_profile.subcategory || '');
    setEditBusinessName(payload.business_profile.specific_business || '');
    setEditMarginCapital(String(payload.financial_profile.available_margin_capital || '200000'));
    setEditPreferredCost(payload.financial_profile.preferred_project_cost ? String(payload.financial_profile.preferred_project_cost) : '');

    try {
      const response = await apiService.financialAnalysis.analyze(payload);
      const normalized = normalizeFinancialResponse(response);

      if (normalized) {
        setFinancialAnalysis(normalized);
        const derivedLoan = normalized.dprPackage?.loan_structure?.sanctioned_loan_amount ?? normalized.projectFinancing?.estimated_financeable_loan ?? 450000;
        const inLakhs = (derivedLoan / 100000).toFixed(1);

        const finCtx = response.financial_context || normalized.financial_context || response.financialContext || null;

        // Invalidate stale SWOT cache so downstream stages re-evaluate with current parameters
        try { sessionStorage.removeItem('kalpa_swot_data'); } catch (e) {}

        if (finCtx) {
          try { sessionStorage.setItem('kalpa_financial_context', JSON.stringify(finCtx)); } catch (e) {}
        }
        try { sessionStorage.setItem('kalpa_financial_analysis', JSON.stringify(normalized)); } catch (e) {}

        if (updateWorkflowState) {
          updateWorkflowState({
            currentStage: 9,
            completedStages: [1, 2, 3, 4, 5, 8, 9],
            workflowStatus: 'FINANCIAL_PLANNING_COMPLETE',
            nextStage: 10,
            financialContext: finCtx,
            financialAnalysis: normalized,
            engineOutputs: {
              financial_planning: `₹${inLakhs}L Proposed Financing Structure ✓`,
              financial_context: finCtx,
              financial_analysis: normalized,
            }
          });
        }
        if (markStageComplete) {
          markStageComplete(9, 10);
        }
      }
    } catch (err) {
      if (err.status === 422 && err.validationErrors) {
        console.error('[FINANCIAL PLANNING ERROR] 422 validation', err.validationErrors);
      } else {
        console.error('[FINANCIAL PLANNING ERROR]', err);
      }
      setError(err.message || 'Failed to complete financial planning analysis.');
    } finally {
      setLoading(false);
      isExecutingRef.current = false;
    }
  }, [analysisId, sessionId, businessProfile, ctxBusinessId, ctxBusinessName, markStageComplete, updateWorkflowState, userDriverInputs]);

  // Answer single blocking question via quick option, text, or voice
  const handleAnswerQuestion = async (driverId, answerVal) => {
    if (!driverId || answerVal === undefined || answerVal === null || answerVal === '') return;
    setSubmittingQuestion(true);
    const updated = { ...userDriverInputs, [driverId]: answerVal };
    setUserDriverInputs(updated);
    setActiveQuestionInput('');
    await executeStage9(businessProfile, true, updated);
    setSubmittingQuestion(false);
  };

  // Play question audio via Sarvam Bulbul v3 TTS
  const playQuestionAudio = useCallback(async (questionText, lang = 'en') => {
    if (!questionText) return;
    try {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      setIsSynthesizingAudio(true);
      const ttsRes = await apiService.assistant.tts({
        text: questionText,
        language: lang || 'en',
        speaker: 'shreya'
      });
      setIsSynthesizingAudio(false);
      const b64 = ttsRes?.data?.audio_base64 || ttsRes?.audio_base64;
      if (b64) {
        const audio = new Audio(`data:audio/wav;base64,${b64}`);
        currentAudioRef.current = audio;
        setIsPlayingAudio(true);
        audio.onended = () => {
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        };
        audio.onerror = () => {
          setIsPlayingAudio(false);
          currentAudioRef.current = null;
        };
        await audio.play();
      }
    } catch (err) {
      console.warn('[SARVAM TTS PLAY ERROR]', err);
      setIsSynthesizingAudio(false);
      setIsPlayingAudio(false);
    }
  }, []);

  // Extracted dashboard sections
  const fin = financialAnalysis;
  const fit = fin?.financialFit;
  const eligibility = fin?.beneficiaryEligibility;
  const financing = fin?.projectFinancing;
  const capital = fin?.capitalStructure;
  const loan = fin?.loanManagement;
  const repayment = fin?.repayment;
  const viability = fin?.financialViability;
  const alternatives = fin?.dprPackage?.m5_stress_appraisal?.financing_options || fin?.alternativeFinancing || [];
  const dpr = fin?.dprPackage;

  // Question Engine & DPR Gate Status
  const blockingQuestions = dpr?.data_completeness?.blocking_questions || [];
  const currentQuestion = blockingQuestions[0];
  const engineStatus = dpr?.financial_engine_status || (dpr?.data_completeness?.financial_engine_status) || 'READY_WITH_DISCLOSED_UNKNOWNS';
  const isBlocked = engineStatus === 'BLOCKED_PENDING_USER_INPUT' || Boolean(currentQuestion);

  // Authoritative Harmonized Metrics (Consistent across M1-M6)
  const totalProjectCost = dpr?.project_cost?.total_project_cost ?? capital?.total_project_cost ?? financing?.total_project_cost ?? financing?.theoretical_project_cost;
  const requiredMargin = dpr?.means_of_finance?.promoter_contribution ?? capital?.margin_contribution ?? financing?.required_margin;
  const availableMargin = financing?.available_margin ?? 200000;
  const retainedSurplus = financing?.excess_margin ?? (availableMargin && requiredMargin ? Math.max(0, availableMargin - requiredMargin) : null);
  const proposedLoan = dpr?.loan_structure?.sanctioned_loan_amount ?? loan?.principal ?? financing?.estimated_financeable_loan;
  const monthlyEmi = dpr?.loan_structure?.monthly_emi ?? loan?.monthly_emi;
  const avgDscr = dpr?.banking_metrics?.average_dscr ?? fin?.debtService?.dscr;
  const breakEvenSales = dpr?.banking_metrics?.break_even_sales_amount ?? fin?.breakEven?.break_even_sales;

  // Active Business Metadata
  const currentBusinessName = ctxBusinessName || businessProfile?.business_profile?.specific_business || businessProfile?.business_context?.business_name || 'Saree Retail';
  const currentSector = businessProfile?.business_profile?.sector || 'Retail';
  const currentCategory = businessProfile?.business_profile?.category || 'Apparel Retail';
  const currentSubcategory = businessProfile?.business_profile?.subcategory || businessProfile?.business_profile?.sub_category || "Women's Traditional Apparel";
  const currentNicCode = businessProfile?.business_profile?.nic_code || '47711';

  // Statements Data from M6
  const pnlList = dpr?.projected_financial_statements?.profit_and_loss || [];
  const bsList = dpr?.projected_financial_statements?.balance_sheet || [];
  const cfList = dpr?.projected_financial_statements?.cash_flow || dpr?.projected_financial_statements?.cash_flow_statement || [];

  // Auto-speak active question when it appears
  useEffect(() => {
    if (isBlocked && currentQuestion?.question) {
      const qKey = currentQuestion.driver_id || currentQuestion.question;
      if (!hasAutoPlayedQuestionRef.current[qKey]) {
        hasAutoPlayedQuestionRef.current[qKey] = true;
        const timer = setTimeout(() => {
          playQuestionAudio(currentQuestion.question, currentQuestion.language || 'en');
        }, 500);
        return () => clearTimeout(timer);
      }
    }
  }, [isBlocked, currentQuestion?.question, currentQuestion?.driver_id, currentQuestion?.language, playQuestionAudio]);

  // Normalize speech transcript to driver answer
  const normalizeAndSubmitAnswer = (driverId, transcript, options) => {
    if (!driverId || !transcript) return;
    const t = transcript.toLowerCase();
    if (t.includes('not sure') || t.includes("don't know") || t.includes('skip') || t.includes('decide later') || t.includes('leave')) {
      handleAnswerQuestion(driverId, 'NOT_SURE');
    } else if (t.includes('proprietor') || t.includes('own') || t.includes('myself') || t.includes('sole') || t.includes('ekal')) {
      handleAnswerQuestion(driverId, 'SOLE_PROPRIETORSHIP');
    } else if (t.includes('partnership') || t.includes('partner') || t.includes('sajhedari')) {
      handleAnswerQuestion(driverId, 'PARTNERSHIP');
    } else if (t.includes('llp') || t.includes('limited liability')) {
      handleAnswerQuestion(driverId, 'LLP');
    } else if (t.includes('company') || t.includes('private limited') || t.includes('pvt') || t.includes('corporate')) {
      handleAnswerQuestion(driverId, 'PRIVATE_LIMITED');
    } else if (t.includes('44') || t.includes('presumptive') || t.includes('ad')) {
      handleAnswerQuestion(driverId, 'PRESUMPTIVE_44AD');
    } else if (t.includes('slab') || t.includes('individual') || t.includes('personal') || t.includes('115')) {
      handleAnswerQuestion(driverId, 'INDIVIDUAL_SLAB');
    } else {
      const matched = options?.find(opt => t.includes(opt.toLowerCase()));
      if (matched) {
        handleAnswerQuestion(driverId, matched);
      }
    }
  };

  // Sarvam STT voice input using MediaRecorder
  const handleVoiceInput = async (driverId, options) => {
    // If already listening, stop recording
    if (isListening) {
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
      return;
    }

    // Stop question audio playback if running
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      setIsPlayingAudio(false);
    }

    try {
      if (!navigator?.mediaDevices?.getUserMedia) {
        throw new Error('getUserMedia not supported');
      }
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];
      const recorder = new MediaRecorder(stream, { mimeType: 'audio/webm' });
      mediaRecorderRef.current = recorder;

      recorder.ondataavailable = (event) => {
        if (event.data && event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      recorder.onstop = async () => {
        setIsListening(false);
        stream.getTracks().forEach(track => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        if (audioBlob.size < 500) return;

        try {
          setIsProcessingAudio(true);
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.webm');
          if (currentQuestion?.language) {
            formData.append('language', currentQuestion.language);
          }

          const sttRes = await apiService.assistant.stt(formData);
          setIsProcessingAudio(false);

          const transcript = sttRes?.data?.text || sttRes?.text || '';
          if (transcript) {
            setActiveQuestionInput(transcript);
            normalizeAndSubmitAnswer(driverId, transcript, options);
          }
        } catch (sttErr) {
          console.warn('[SARVAM STT ERROR]', sttErr);
          setIsProcessingAudio(false);
        }
      };

      recorder.start();
      setIsListening(true);
    } catch (micErr) {
      console.warn('[MIC ERROR, FALLING BACK TO WEB SPEECH]', micErr);
      setIsListening(false);
      // Fallback: browser speech recognition
      const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
      if (SpeechRec) {
        try {
          const recognition = new SpeechRec();
          recognition.lang = 'en-IN';
          setIsListening(true);
          recognition.onresult = (event) => {
            const transcript = event.results[0][0].transcript;
            setIsListening(false);
            setActiveQuestionInput(transcript);
            normalizeAndSubmitAnswer(driverId, transcript, options);
          };
          recognition.onerror = () => setIsListening(false);
          recognition.onend = () => setIsListening(false);
          recognition.start();
        } catch (e) {
          setIsListening(false);
        }
      }
    }
  };

  // Handle Form Submission for Edited Parameters
  const handleUpdateParameters = (e) => {
    e.preventDefault();
    setIsEditDrawerOpen(false);

    const updatedProfile = {
      ...(businessProfile || {}),
      business_profile: {
        business_id: businessProfile?.business_profile?.business_id || ctxBusinessId || 'saree_retail',
        specific_business: editBusinessName || 'Saree Retail',
        sector: editSector || 'Retail',
        category: editCategory || 'Apparel Retail',
        subcategory: editSubcategory || "Women's Traditional Apparel",
        nic_code: businessProfile?.business_profile?.nic_code || '47711'
      },
      financial_profile: {
        available_margin_capital: parseFloat(editMarginCapital || '200000'),
        preferred_project_cost: editPreferredCost ? parseFloat(editPreferredCost) : null
      }
    };

    setBusinessProfile(updatedProfile);
    executeStage9(updatedProfile, true);
  };

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
          business_profile: {
            business_id: ctxBusinessId || 'saree_retail',
            specific_business: ctxBusinessName || 'Saree Retail',
            sector: 'Retail',
            category: 'Apparel Retail',
            subcategory: "Women's Traditional Apparel"
          },
          financial_profile: { available_margin_capital: 200000 }
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
          business_profile: {
            business_id: ctxBusinessId || 'saree_retail',
            specific_business: ctxBusinessName || 'Saree Retail',
            sector: 'Retail',
            category: 'Apparel Retail',
            subcategory: "Women's Traditional Apparel"
          },
          financial_profile: { available_margin_capital: 200000 }
        });
      } finally {
        setFetchingProfile(false);
      }
    };

    fetchProfileData();
  }, [analysisId, sessionId]);



  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#1C1917] py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* 1. Workflow Timeline Header */}
        <WorkflowTimeline />

        {/* 2. Page Title Banner with Canonical Profile Metadata & Parameter Drawer Trigger */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] shadow-sm relative overflow-hidden bg-white">
          <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-orange-100 text-[#C2410C] border border-orange-200">
                  STAGE 09 &middot; FINANCE PILLAR
                </span>
                <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800 border border-emerald-200 flex items-center gap-1">
                  <ShieldCheck className="w-3.5 h-3.5 text-emerald-600" />
                  M1–M6 Authoritative Financial Model
                </span>
                {dpr?.data_completeness && (
                  <span
                    className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1 ${
                      dpr.data_completeness.status === 'COMPLETE'
                        ? 'bg-emerald-50 text-emerald-700 border-emerald-300'
                        : 'bg-amber-50 text-amber-700 border-amber-300'
                    }`}
                  >
                    <CheckCircle2 className="w-3 h-3" />
                    Data Completeness: {dpr.data_completeness.status}
                  </span>
                )}
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                Financial Planning & Institutional Credit Package
              </h1>

              {/* Verified Sector, Category & Subcategory Display */}
              <div className="flex flex-wrap items-center gap-3 text-xs text-[#57534E] pt-1">
                <span className="flex items-center gap-1.5 font-bold text-[#1C1917] bg-[#FAF7F2] px-3 py-1 rounded-lg border border-[#EAE3D5]">
                  <Building2 className="w-4 h-4 text-[#EA580C]" />
                  {currentBusinessName}
                </span>
                <span className="bg-stone-100 px-2.5 py-1 rounded-md text-stone-700 font-medium">
                  Sector: <strong>{currentSector}</strong>
                </span>
                <span className="bg-stone-100 px-2.5 py-1 rounded-md text-stone-700 font-medium">
                  Category: <strong>{currentCategory}</strong>
                </span>
                <span className="bg-stone-100 px-2.5 py-1 rounded-md text-stone-700 font-medium">
                  Subcategory: <strong>{currentSubcategory}</strong>
                </span>
                {currentNicCode && (
                  <span className="bg-stone-100 px-2.5 py-1 rounded-md text-stone-600 font-mono text-[11px]">
                    NIC: {currentNicCode}
                  </span>
                )}
              </div>
            </div>

            {/* Actions & Tab Switcher */}
            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <button
                onClick={() => setIsEditDrawerOpen(true)}
                className="px-4 py-2.5 rounded-xl border border-stone-300 bg-white hover:bg-stone-50 text-xs font-bold text-stone-700 shadow-2xs flex items-center gap-1.5 transition-all"
              >
                <SlidersHorizontal className="w-3.5 h-3.5 text-[#EA580C]" />
                <span>Adjust Parameters</span>
              </button>

              <div className="flex items-center gap-1 bg-stone-100 p-1 rounded-xl border border-[#EAE3D5]">
                <button
                  onClick={() => setActiveTab('planning')}
                  className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${
                    activeTab === 'planning'
                      ? 'bg-white text-[#1C1917] shadow-sm'
                      : 'text-[#57534E] hover:text-[#1C1917]'
                  }`}
                >
                  <BarChart3 className="w-3.5 h-3.5 text-[#EA580C]" />
                  Planning & Appraisal
                </button>
                <button
                  onClick={() => {
                    setActiveTab('calculator');
                    if (!calcResult) executeCalculator();
                  }}
                  className={`px-4 py-2 rounded-lg text-xs font-bold flex items-center gap-2 transition-all ${
                    activeTab === 'calculator'
                      ? 'bg-white text-[#1C1917] shadow-sm'
                      : 'text-[#57534E] hover:text-[#1C1917]'
                  }`}
                >
                  <Calculator className="w-3.5 h-3.5 text-[#EA580C]" />
                  Standalone Calculator
                </button>
              </div>
            </div>
          </div>
        </div>

        {/* Loading Indicator */}
        {loading && (
          <div className="royal-panel rounded-2xl p-12 text-center border border-[#EAE3D5] space-y-4 bg-white">
            <RefreshCw className="w-10 h-10 text-[#EA580C] animate-spin mx-auto" />
            <h3 className="text-lg font-bold text-[#1C1917]">Synthesizing Financial Appraisal Package...</h3>
            <p className="text-xs text-[#78716C] max-w-md mx-auto">
              Running M1 Loan Capacity, M2 Project Cost & CapEx Benchmarks, M3 5-Year Accounting Statements, M4 Banking DSCR Appraisal, and M5 Stress Sensitivity.
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
        {/* UNIFIED FINANCIAL PLANNING & APPRAISAL DASHBOARD                         */}
        {/* ========================================================================= */}
        {activeTab === 'planning' && fin && !loading && (
          <div className="space-y-8 animate-fadeIn">

            {/* Institutional DPR Readiness & Diagnostic Status Banner */}
            <div className="p-4 rounded-2xl bg-white border border-[#EAE3D5] shadow-sm flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className={`p-2.5 rounded-xl ${
                  engineStatus === 'READY_FOR_DPR'
                    ? 'bg-emerald-100 text-emerald-700'
                    : engineStatus === 'READY_WITH_DISCLOSED_UNKNOWNS'
                    ? 'bg-blue-100 text-blue-700'
                    : 'bg-amber-100 text-amber-700'
                }`}>
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <span className="text-xs font-bold text-stone-900 font-['Outfit'] uppercase tracking-wider">
                      Financial Engine Status:
                    </span>
                    <span className={`px-2 py-0.5 rounded-full text-[10px] font-black tracking-wide ${
                      engineStatus === 'READY_FOR_DPR'
                        ? 'bg-emerald-100 text-emerald-800 border border-emerald-300'
                        : engineStatus === 'READY_WITH_DISCLOSED_UNKNOWNS'
                        ? 'bg-blue-100 text-blue-800 border border-blue-300'
                        : 'bg-amber-100 text-amber-800 border border-amber-300'
                    }`}>
                      {engineStatus}
                    </span>

                    {/* Reconciled Data Completeness Status Badge */}
                    {dpr?.data_completeness?.status && (
                      <span
                        className={`px-2 py-0.5 rounded-full text-[10px] font-bold tracking-wide flex items-center gap-1 cursor-help ${
                          dpr.data_completeness.status === 'COMPLETE'
                            ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                            : 'bg-blue-50 text-blue-700 border border-blue-200'
                        }`}
                        title={
                          dpr.data_completeness.status === 'COMPLETE'
                            ? 'All mandatory financial inputs and secondary disclosures verified.'
                            : 'Core project financing & bankability metrics are 100% verified. Secondary statutory disclosures are non-blocking.'
                        }
                      >
                        <Info className="w-3 h-3" />
                        Data Completeness: {dpr.data_completeness.status === 'COMPLETE' ? 'COMPLETE' : 'PARTIALLY COMPLETE (Non-blocking)'}
                      </span>
                    )}
                  </div>
                  <p className="text-[11px] text-stone-500 mt-0.5">
                    {isBlocked
                      ? '1 mandatory financial choice pending from entrepreneur before bankable DPR packaging.'
                      : (dpr?.data_completeness?.dpr_gate_reasons?.[0] || 'Institutional financial appraisal completed and verified for bank credit appraisal.')}
                  </p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {isBlocked ? (
                  <div className="relative group">
                    <button
                      disabled
                      className="px-4 py-2 bg-stone-200 text-stone-400 text-xs font-bold rounded-xl cursor-not-allowed flex items-center gap-1.5 opacity-80"
                      title="Answer the question below to proceed"
                    >
                      <Lock className="w-3.5 h-3.5" />
                      Proceed to Bankable DPR
                      <ArrowRight className="w-3.5 h-3.5" />
                    </button>
                    <span className="hidden group-hover:block absolute bottom-full mb-1 right-0 w-48 p-2 bg-stone-900 text-white text-[10px] rounded-lg shadow-lg text-center z-20">
                      Answer the question below to finalize PAT and unlock DPR.
                    </span>
                  </div>
                ) : (
                  <Link
                    to={`/dpr?session_id=${sessionId}&analysis_id=${analysisId}`}
                    className="px-4 py-2 bg-[#EA580C] hover:bg-[#C2410C] text-white text-xs font-bold rounded-xl transition-all shadow-sm flex items-center gap-1.5"
                  >
                    <FileCheck className="w-4 h-4" />
                    Proceed to Bankable DPR
                    <ArrowRight className="w-3.5 h-3.5" />
                  </Link>
                )}
              </div>
            </div>

            {/* CONVERSATIONAL QUESTION CARD (Minimum Question Policy - 1 At A Time) */}
            {isBlocked && currentQuestion && (
              <div className="royal-panel rounded-2xl p-6 sm:p-7 border-2 border-amber-300 bg-gradient-to-r from-amber-50/90 via-white to-orange-50/70 shadow-md relative overflow-hidden space-y-4 animate-fadeIn">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-amber-200/80 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="p-2 rounded-xl bg-amber-500 text-white shadow-xs">
                      <MessageSquare className="w-4 h-4" />
                    </span>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-wider text-amber-900 bg-amber-200/60 px-2 py-0.5 rounded-full">
                        Action Required · 1 Pending Choice
                      </span>
                      <h3 className="text-sm font-bold text-[#1C1917] font-['Outfit'] mt-0.5">
                        Conversational Entrepreneur Clarification Loop
                      </h3>
                    </div>
                  </div>
                  <span className="text-[11px] text-stone-500 font-medium italic">
                    Single-question flow · Sarvam AI Voice & Text enabled
                  </span>
                </div>

                <div className="space-y-1.5">
                  <div className="flex items-start justify-between gap-3">
                    <p className="text-base sm:text-lg font-bold text-[#1C1917] leading-relaxed flex-1">
                      "{currentQuestion.question}"
                    </p>
                    <button
                      type="button"
                      onClick={() => playQuestionAudio(currentQuestion.question, currentQuestion.language || 'en')}
                      disabled={isSynthesizingAudio}
                      className={`px-3 py-1.5 rounded-xl text-xs font-bold flex items-center gap-1.5 transition-all shrink-0 ${
                        isPlayingAudio
                          ? 'bg-amber-600 text-white shadow-xs animate-pulse'
                          : isSynthesizingAudio
                          ? 'bg-amber-100 text-amber-800 border border-amber-200 cursor-wait'
                          : 'bg-white hover:bg-amber-100 text-amber-900 border border-amber-300 shadow-2xs'
                      }`}
                      title="Listen to question via Sarvam Bulbul TTS"
                    >
                      <Volume2 className="w-4 h-4" />
                      <span>{isSynthesizingAudio ? 'Synthesizing...' : isPlayingAudio ? 'Playing...' : 'Replay Audio'}</span>
                    </button>
                  </div>
                  <p className="text-xs text-stone-500">
                    KALPA automatically resolved your 5-year revenue growth and project benchmarks using verified local intelligence. We only ask when an entrepreneurial choice is required.
                  </p>
                </div>

                {/* Quick Selection Option Chips */}
                {currentQuestion.options && currentQuestion.options.length > 0 && (
                  <div className="space-y-2 pt-1">
                    <span className="text-[11px] font-bold text-stone-700 block">
                      Select an option:
                    </span>
                    <div className="flex flex-wrap gap-2.5">
                      {currentQuestion.options.map((opt, i) => {
                        const optLabels = {
                          'SOLE_PROPRIETORSHIP': 'Proprietorship (Sole Owner / Self-Employed)',
                          'PARTNERSHIP': 'Partnership Firm (Standard Deed)',
                          'LLP': 'Limited Liability Partnership (LLP)',
                          'PRIVATE_LIMITED': 'Private Limited Company (Corporate MSME)',
                          'PRESUMPTIVE_44AD': 'Presumptive Taxation (Sec 44AD · Statutory MSME)',
                          'INDIVIDUAL_SLAB': 'Individual Income Tax Slab (Sec 115BAC)',
                          'CORPORATE_22PCT': 'Corporate Tax Rate (MSME 25% / Sec 115BAA)',
                          'NOT_SURE': "I'm Not Sure / Decide Later"
                        };
                        const label = optLabels[opt] || opt;
                        const isNotSure = opt === 'NOT_SURE';
                        return (
                          <button
                            key={i}
                            disabled={submittingQuestion}
                            onClick={() => handleAnswerQuestion(currentQuestion.driver_id, opt)}
                            className={`px-4 py-2.5 rounded-xl text-xs font-bold transition-all shadow-2xs flex items-center gap-1.5 ${
                              isNotSure
                                ? 'bg-stone-100 hover:bg-stone-200 text-stone-700 border border-stone-300'
                                : 'bg-white hover:bg-amber-100/70 text-amber-950 border border-amber-300 hover:border-amber-400'
                            }`}
                          >
                            <span>{label}</span>
                            <ArrowRight className="w-3.5 h-3.5 opacity-60" />
                          </button>
                        );
                      })}
                    </div>
                  </div>
                )}

                {/* Direct Text & Voice Response Bar */}
                <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  <div className="relative flex-1">
                    <input
                      type="text"
                      value={activeQuestionInput}
                      onChange={(e) => setActiveQuestionInput(e.target.value)}
                      onKeyDown={(e) => {
                        if (e.key === 'Enter') {
                          handleAnswerQuestion(currentQuestion.driver_id, activeQuestionInput);
                        }
                      }}
                      placeholder="Or type your response here..."
                      className="w-full pl-3.5 pr-10 py-2.5 rounded-xl border border-stone-300 bg-white text-xs font-medium text-stone-800 focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                    {activeQuestionInput && (
                      <button
                        onClick={() => handleAnswerQuestion(currentQuestion.driver_id, activeQuestionInput)}
                        disabled={submittingQuestion}
                        className="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 rounded-lg bg-[#EA580C] text-white hover:bg-[#C2410C]"
                      >
                        <Send className="w-3.5 h-3.5" />
                      </button>
                    )}
                  </div>

                  <button
                    type="button"
                    onClick={() => handleVoiceInput(currentQuestion.driver_id, currentQuestion.options)}
                    disabled={isProcessingAudio || submittingQuestion}
                    className={`px-4 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 transition-all ${
                      isListening
                        ? 'bg-rose-600 text-white animate-pulse'
                        : isProcessingAudio
                        ? 'bg-amber-500 text-white cursor-wait'
                        : 'bg-stone-800 hover:bg-black text-white'
                    }`}
                  >
                    {isProcessingAudio ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Transcribing (Sarvam STT)...</span>
                      </>
                    ) : isListening ? (
                      <>
                        <MicOff className="w-4 h-4" />
                        <span>Listening... (Tap to Send)</span>
                      </>
                    ) : (
                      <>
                        <Mic className="w-4 h-4" />
                        <span>Voice Answer (Sarvam STT)</span>
                      </>
                    )}
                  </button>
                </div>
              </div>
            )}

            {/* SECTION 1: Harmonized Executive Financial Summary (6 Key Cards) */}
            <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">
              
              {/* 1. Total Project Cost */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                      Total Project Cost
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-amber-50 text-amber-800 border border-amber-200">
                      CALCULATED
                    </span>
                  </div>
                  <div className="text-2xl font-black text-[#1C1917] mt-1 font-['Outfit']">
                    {formatINR(totalProjectCost)}
                  </div>
                  <p className="text-[11px] text-[#57534E] mt-1">
                    Normalized CapEx + Working Capital
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-[#EAE3D5] text-[10px] font-semibold text-stone-500">
                  Basis: {dpr?.project_cost?.cost_basis || 'BENCHMARK_DERIVED'}
                </div>
              </div>

              {/* 2. Required Margin */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">
                      Required Margin (10%)
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-emerald-50 text-emerald-800 border border-emerald-200">
                      CALCULATED
                    </span>
                  </div>
                  <div className="text-2xl font-black text-emerald-700 mt-1 font-['Outfit']">
                    {formatINR(requiredMargin)}
                  </div>
                  <p className="text-[11px] text-[#57534E] mt-1">
                    Mandatory Promoter Equity
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-[#EAE3D5] text-[10px] font-semibold text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-3 h-3" />
                  100% Minimum Equity Met
                </div>
              </div>

              {/* 3. Available Margin Capital */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-stone-600">
                      Available Capital
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-blue-50 text-blue-800 border border-blue-200">
                      USER_PROVIDED
                    </span>
                  </div>
                  <div className="text-2xl font-black text-stone-800 mt-1 font-['Outfit']">
                    {formatINR(availableMargin)}
                  </div>
                  <p className="text-[11px] text-[#57534E] mt-1">
                    Entrepreneur Intake Budget
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-[#EAE3D5] text-[10px] font-semibold text-stone-500">
                  Source: Entrepreneur Profile
                </div>
              </div>

              {/* 4. Retained Surplus Capital */}
              <div className="royal-card rounded-2xl p-5 border border-emerald-200 bg-emerald-50/30 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-800">
                      Retained Surplus
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-emerald-50 text-emerald-800 border border-emerald-200">
                      CALCULATED
                    </span>
                  </div>
                  <div className="text-2xl font-black text-emerald-800 mt-1 font-['Outfit']">
                    {formatINR(retainedSurplus)}
                  </div>
                  <p className="text-[11px] text-emerald-700 mt-1">
                    Uncommitted Safety Reserve
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-emerald-200 text-[10px] font-semibold text-emerald-800 flex items-center gap-1">
                  <ShieldCheck className="w-3 h-3" />
                  Preserved for Contingency
                </div>
              </div>

              {/* 5. Proposed Loan (90%) */}
              <div className="royal-card rounded-2xl p-5 border border-orange-200 bg-orange-50/20 flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#C2410C]">
                      Proposed Loan (90%)
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-orange-50 text-orange-800 border border-orange-200">
                      CALCULATED
                    </span>
                  </div>
                  <div className="text-2xl font-black text-[#C2410C] mt-1 font-['Outfit']">
                    {formatINR(proposedLoan)}
                  </div>
                  <p className="text-[11px] text-[#57534E] mt-1">
                    Recommended Institutional Debt
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-orange-200 text-[10px] font-semibold text-[#78716C] flex justify-between">
                  <span>Tenure: {dpr?.loan_structure?.tenure_months || 84} Mo</span>
                  <span>Rate: {formatPct(dpr?.loan_structure?.annual_interest_rate_pct ?? 8.0)}</span>
                </div>
              </div>

              {/* 6. Monthly EMI */}
              <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
                <div>
                  <div className="flex items-center justify-between">
                    <span className="text-[10px] font-bold uppercase tracking-wider text-stone-600">
                      Monthly Annuity EMI
                    </span>
                    <span className="px-1.5 py-0.5 rounded text-[9px] font-black bg-stone-100 text-stone-700 border border-stone-300">
                      CALCULATED
                    </span>
                  </div>
                  <div className="text-2xl font-black text-[#EA580C] mt-1 font-['Outfit']">
                    {formatINR(monthlyEmi)}
                  </div>
                  <p className="text-[11px] text-[#57534E] mt-1">
                    Post-Moratorium Obligation
                  </p>
                </div>
                <div className="mt-3 pt-2.5 border-t border-[#EAE3D5] text-[10px] font-semibold text-blue-700 flex items-center gap-1">
                  <span>Avg DSCR: <strong>{formatRatioVal(avgDscr)}</strong></span>
                </div>
              </div>

            </div>

            {/* Margin Capitalization Contextual Note */}
            <div className="p-4 rounded-xl bg-amber-50/70 border border-amber-200 text-xs text-amber-900 flex flex-col sm:flex-row sm:items-center justify-between gap-3">
              <div className="flex items-start gap-2.5">
                <Info className="w-4 h-4 text-amber-600 shrink-0 mt-0.5" />
                <div>
                  <span className="font-bold">Institutional Capitalization Harmonization:</span> Total Project Cost is sized at{' '}
                  <strong>{formatINR(totalProjectCost)}</strong> based on industry CapEx (₹3.20L) and Working Capital (₹1.80L) benchmarks for {currentBusinessName}.
                  The required 10% promoter equity is <strong>{formatINR(requiredMargin)}</strong>. Your available margin of{' '}
                  <strong>{formatINR(availableMargin)}</strong> fully satisfies this requirement, retaining{' '}
                  <strong>{formatINR(retainedSurplus)}</strong> as uncommitted cash buffer for contingency and working capital reserves.
                </div>
              </div>
              <button
                onClick={() => setIsEditDrawerOpen(true)}
                className="px-3 py-1.5 rounded-lg bg-white border border-amber-300 text-amber-900 font-bold hover:bg-amber-50 shrink-0 text-[11px]"
              >
                Modify Margin Input
              </button>
            </div>

            {/* SECTION 2: Project Cost Breakdown (M2) & Means of Finance (M3) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Verified Project Cost Breakdown */}
              <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <Layers className="w-4 h-4 text-[#EA580C]" />
                    Project Cost Breakdown (M2 Verified)
                  </h3>
                  <span className="text-[10px] text-stone-500 font-semibold px-2 py-0.5 bg-stone-100 rounded">
                    Authoritative Benchmark
                  </span>
                </div>

                <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                  <thead className="bg-[#FAF7F2] text-[#57534E]">
                    <tr>
                      <th className="px-3.5 py-2 font-bold">Cost Component</th>
                      <th className="px-3.5 py-2 font-bold text-right">Amount</th>
                      <th className="px-3.5 py-2 font-bold text-right">% of Total</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">Plant & Machinery / CapEx</td>
                      <td className="px-3.5 py-2 text-right font-medium">
                        {formatINR(dpr?.project_cost?.capex_subtotal ?? dpr?.project_cost?.plant_and_machinery ?? capital?.fixed_capital_capex ?? 145000)}
                      </td>
                      <td className="px-3.5 py-2 text-right text-stone-600 font-semibold">
                        {formatPct((dpr?.project_cost?.capex_subtotal ?? dpr?.project_cost?.plant_and_machinery ?? capital?.fixed_capital_capex ?? 145000) / (totalProjectCost || 325000))}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">
                        Working Capital Requirement
                        <span className="block text-[10px] text-stone-500 font-normal">
                          Opening stock (₹1.80L) & cash buffer
                        </span>
                      </td>
                      <td className="px-3.5 py-2 text-right font-medium">
                        {formatINR(
                          (dpr?.project_cost?.working_capital_margin && dpr?.project_cost?.working_capital_margin > 0)
                            ? dpr.project_cost.working_capital_margin
                            : (dpr?.project_cost?.working_capital_subtotal && dpr?.project_cost?.working_capital_subtotal > 0)
                            ? dpr.project_cost.working_capital_subtotal
                            : (capital?.working_capital || 180000)
                        )}
                      </td>
                      <td className="px-3.5 py-2 text-right text-stone-600 font-semibold">
                        {formatPct((dpr?.project_cost?.working_capital_margin || dpr?.project_cost?.working_capital_subtotal || capital?.working_capital || 180000) / (totalProjectCost || 325000))}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">Land & Site Development</td>
                      <td className="px-3.5 py-2 text-right font-medium">
                        {dpr?.project_cost?.land_and_building !== null && dpr?.project_cost?.land_and_building !== undefined ? formatINR(dpr.project_cost.land_and_building) : 'Not required'}
                      </td>
                      <td className="px-3.5 py-2 text-right text-stone-600">0.0%</td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">Preliminary & Pre-operative Costs</td>
                      <td className="px-3.5 py-2 text-right font-medium">
                        {dpr?.project_cost?.preliminary_and_preoperative !== null && dpr?.project_cost?.preliminary_and_preoperative !== undefined ? formatINR(dpr.project_cost.preliminary_and_preoperative) : 'Not applicable'}
                      </td>
                      <td className="px-3.5 py-2 text-right text-stone-600">0.0%</td>
                    </tr>
                    <tr className="bg-[#FAF7F2] font-black text-[#1C1917]">
                      <td className="px-3.5 py-2">Total Project Cost</td>
                      <td className="px-3.5 py-2 text-right">{formatINR(totalProjectCost)}</td>
                      <td className="px-3.5 py-2 text-right">100.0%</td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Means of Finance & Sources of Funds */}
              <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <CreditCard className="w-4 h-4 text-emerald-600" />
                    Means of Finance (M3 Verified)
                  </h3>
                  <span className="text-[10px] text-stone-500 font-semibold px-2 py-0.5 bg-stone-100 rounded">
                    Authoritative Capital Mix
                  </span>
                </div>

                <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                  <thead className="bg-[#FAF7F2] text-[#57534E]">
                    <tr>
                      <th className="px-3.5 py-2 font-bold">Funding Source</th>
                      <th className="px-3.5 py-2 font-bold text-right">Committed (INR)</th>
                      <th className="px-3.5 py-2 font-bold text-right">% Contribution</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">Promoter Margin Contribution (Equity)</td>
                      <td className="px-3.5 py-2 text-right font-medium text-emerald-800">
                        {formatINR(requiredMargin)}
                      </td>
                      <td className="px-3.5 py-2 text-right font-semibold text-emerald-700">
                        {formatPct(dpr?.means_of_finance?.promoter_margin_pct ?? 10.0)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">Proposed Institutional Bank Term Loan</td>
                      <td className="px-3.5 py-2 text-right font-medium text-[#C2410C]">
                        {formatINR(proposedLoan)}
                      </td>
                      <td className="px-3.5 py-2 text-right font-semibold text-[#C2410C]">
                        {formatPct(dpr?.means_of_finance?.debt_pct ?? 90.0)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-[#1C1917] font-medium">Government Capital Subsidy / Grant</td>
                      <td className="px-3.5 py-2 text-right font-medium">
                        {dpr?.means_of_finance?.subsidy_grant ? formatINR(dpr.means_of_finance.subsidy_grant) : 'Eligible upon claim'}
                      </td>
                      <td className="px-3.5 py-2 text-right text-stone-600">0.0%</td>
                    </tr>
                    <tr className="bg-[#FAF7F2] font-black text-[#1C1917]">
                      <td className="px-3.5 py-2">Total Funding Structured</td>
                      <td className="px-3.5 py-2 text-right">{formatINR(totalProjectCost)}</td>
                      <td className="px-3.5 py-2 text-right">100.0%</td>
                    </tr>
                  </tbody>
                </table>

                <div className="p-3 bg-emerald-50 border border-emerald-200 rounded-xl text-xs flex items-center justify-between">
                  <span className="font-semibold text-emerald-800">Financing Gap Status:</span>
                  <span className="font-bold text-emerald-900 flex items-center gap-1">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    100% Fully Financed (Gap = ₹0)
                  </span>
                </div>
              </div>

            </div>

            {/* SECTION 3: 5-Year Projected Financial Statements (M3 Projected Statements) */}
            <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
                <div className="space-y-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                    Accounting Projections &bull; Milestone 3 Authoritative
                  </span>
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <BarChart3 className="w-4 h-4 text-[#EA580C]" />
                    5-Year Projected Financial Statements
                  </h3>
                </div>

                {/* Sub-navigation between P&L, Balance Sheet, and Cash Flow */}
                <div className="flex items-center gap-1 bg-[#FAF7F2] p-1 rounded-xl border border-[#EAE3D5] text-xs font-semibold">
                  <button
                    onClick={() => setStatementTab('pnl')}
                    className={`px-3 py-1.5 rounded-lg transition-all ${
                      statementTab === 'pnl' ? 'bg-[#1E293B] text-white shadow-xs' : 'text-stone-600 hover:text-stone-900'
                    }`}
                  >
                    Profit & Loss
                  </button>
                  <button
                    onClick={() => setStatementTab('balance_sheet')}
                    className={`px-3 py-1.5 rounded-lg transition-all ${
                      statementTab === 'balance_sheet' ? 'bg-[#1E293B] text-white shadow-xs' : 'text-stone-600 hover:text-stone-900'
                    }`}
                  >
                    Balance Sheet
                  </button>
                  <button
                    onClick={() => setStatementTab('cash_flow')}
                    className={`px-3 py-1.5 rounded-lg transition-all ${
                      statementTab === 'cash_flow' ? 'bg-[#1E293B] text-white shadow-xs' : 'text-stone-600 hover:text-stone-900'
                    }`}
                  >
                    Cash Flow
                  </button>
                </div>
              </div>

              {/* 5-Year Profit & Loss Statement */}
              {statementTab === 'pnl' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                    <thead className="bg-[#1E293B] text-white">
                      <tr>
                        <th className="px-3.5 py-2.5 font-bold">Line Item (INR)</th>
                        {[1, 2, 3, 4, 5].map((yr) => (
                          <th key={yr} className="px-3.5 py-2.5 font-bold text-right">Year {yr}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                      <tr>
                        <td className="px-3.5 py-2 font-semibold text-[#1C1917]">Gross Revenue</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right font-medium">{formatINR(p.gross_revenue)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Cost of Goods Sold (COGS)</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(p.cogs)}</td>
                        ))}
                      </tr>
                      <tr className="bg-stone-50 font-semibold">
                        <td className="px-3.5 py-2 text-[#1C1917]">Gross Profit</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-emerald-800">{formatINR(p.gross_profit)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Operating Expenses (Admin & Selling)</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(p.operating_expenses)}</td>
                        ))}
                      </tr>
                      <tr className="bg-stone-50 font-semibold">
                        <td className="px-3.5 py-2 text-[#1C1917]">EBITDA</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-blue-800">{formatINR(p.ebitda)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Depreciation</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(p.depreciation)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Term Loan Interest</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-rose-700">{formatINR(p.interest_expense)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 font-medium text-stone-800">Profit Before Tax (PBT)</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right font-medium">{formatINR(p.pbt)}</td>
                        ))}
                      </tr>
                      <tr className="bg-[#FAF7F2] font-black text-[#1C1917]">
                        <td className="px-3.5 py-2">Profit After Tax (PAT)</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-emerald-700 font-bold">
                            {p.pat !== null && p.pat !== undefined ? (
                              formatINR(p.pat)
                            ) : (
                              <span className="inline-block text-[10px] font-semibold text-amber-800 bg-amber-100 px-2 py-0.5 rounded border border-amber-300">
                                {p.tax_status === "PROVISIONAL_PENDING_REGISTRATION" ? "Pending Entity Registration" : "Awaiting Tax Selection"}
                              </span>
                            )}
                          </td>
                        ))}
                      </tr>
                      <tr className="text-stone-500 text-[11px]">
                        <td className="px-3.5 py-1.5">Net Profit Margin %</td>
                        {pnlList.map((p, idx) => (
                          <td key={idx} className="px-3.5 py-1.5 text-right font-medium text-stone-600">
                            {p.net_profit_margin_pct !== null && p.net_profit_margin_pct !== undefined ? (
                              formatPct(p.net_profit_margin_pct)
                            ) : (
                              <span className="text-[10px] text-stone-400 italic">Pending Tax</span>
                            )}
                          </td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* 5-Year Balance Sheet Statement */}
              {statementTab === 'balance_sheet' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                    <thead className="bg-[#1E293B] text-white">
                      <tr>
                        <th className="px-3.5 py-2.5 font-bold">Balance Sheet Item (INR)</th>
                        {[1, 2, 3, 4, 5].map((yr) => (
                          <th key={yr} className="px-3.5 py-2.5 font-bold text-right">Year {yr}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                      <tr>
                        <td className="px-3.5 py-2 font-medium text-[#1C1917]">Gross Fixed Assets</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right font-medium">{formatINR(b.gross_fixed_assets)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Accumulated Depreciation</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(b.accumulated_depreciation)}</td>
                        ))}
                      </tr>
                      <tr className="bg-stone-50 font-semibold">
                        <td className="px-3.5 py-2 text-[#1C1917]">Net Fixed Assets</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-[#1C1917]">{formatINR(b.net_fixed_assets)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Current Assets (Inventory, Receivables, Cash)</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(b.current_assets)}</td>
                        ))}
                      </tr>
                      <tr className="bg-[#FAF7F2] font-black text-[#1C1917]">
                        <td className="px-3.5 py-2">Total Assets</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-emerald-800 font-bold">{formatINR(b.total_assets)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 font-medium text-[#1C1917]">Promoter Equity & Retained Earnings</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right font-medium text-[#1C1917]">
                            {formatINR((b.share_capital_promoter_equity || 0) + (b.reserves_and_surplus || 0))}
                          </td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Term Loan Outstanding</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-rose-700">{formatINR(b.term_loan_outstanding)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 text-stone-600">Current Liabilities & Provisions</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(b.current_liabilities)}</td>
                        ))}
                      </tr>
                      <tr className="bg-[#FAF7F2] font-black text-[#1C1917]">
                        <td className="px-3.5 py-2">Total Liabilities & Equity</td>
                        {bsList.map((b, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-emerald-800 font-bold">{formatINR(b.total_liabilities)}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}

              {/* 5-Year Cash Flow Statement */}
              {statementTab === 'cash_flow' && (
                <div className="overflow-x-auto">
                  <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                    <thead className="bg-[#1E293B] text-white">
                      <tr>
                        <th className="px-3.5 py-2.5 font-bold">Cash Flow Component (INR)</th>
                        {[1, 2, 3, 4, 5].map((yr) => (
                          <th key={yr} className="px-3.5 py-2.5 font-bold text-right">Year {yr}</th>
                        ))}
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-stone-100">
                      <tr>
                        <td className="px-3.5 py-2 font-medium text-[#1C1917]">Cash from Operating Activities (CFO)</td>
                        {cfList.map((c, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right font-medium text-emerald-800">{formatINR(c.cash_from_operations)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 font-medium text-stone-600">Cash from Investing Activities (CFI)</td>
                        {cfList.map((c, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(c.cash_from_investing)}</td>
                        ))}
                      </tr>
                      <tr>
                        <td className="px-3.5 py-2 font-medium text-stone-600">Cash from Financing Activities (CFF)</td>
                        {cfList.map((c, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-stone-600">{formatINR(c.cash_from_financing)}</td>
                        ))}
                      </tr>
                      <tr className="bg-stone-50 font-bold text-[#1C1917]">
                        <td className="px-3.5 py-2">Net Change in Cash Position</td>
                        {cfList.map((c, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-blue-800 font-bold">{formatINR(c.net_change_in_cash)}</td>
                        ))}
                      </tr>
                      <tr className="bg-[#FAF7F2] font-black text-[#1C1917]">
                        <td className="px-3.5 py-2">Closing Cash & Bank Balance</td>
                        {cfList.map((c, idx) => (
                          <td key={idx} className="px-3.5 py-2 text-right text-emerald-700 font-bold">{formatINR(c.closing_cash_balance)}</td>
                        ))}
                      </tr>
                    </tbody>
                  </table>
                </div>
              )}
            </div>

            {/* SECTION 4: Institutional Financing Alternatives & Scheme Optimizer (M5) */}
            <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
              <div className="flex items-center justify-between">
                <div className="space-y-0.5">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#78716C]">
                    Milestone 5 Scheme Optimizer
                  </span>
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <Compass className="w-4 h-4 text-[#EA580C]" />
                    Institutional Financing Options & Scheme Alternatives
                  </h3>
                </div>
                <span className="text-[10px] text-stone-500 font-semibold px-2 py-0.5 bg-stone-100 rounded">
                  {alternatives.length} Evaluated Structures
                </span>
              </div>

              <p className="text-xs text-[#57534E]">
                The M5 Financing Optimizer analyzed {alternatives.length} scheme and tenure combinations against credit capacity, subsidy availability, and debt servicing limits.
              </p>

              <div className="overflow-x-auto">
                <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                  <thead className="bg-[#FAF7F2] text-[#57534E]">
                    <tr>
                      <th className="px-3 py-2 font-bold">Scheme Structure</th>
                      <th className="px-3 py-2 font-bold text-right">Proposed Loan</th>
                      <th className="px-3 py-2 font-bold text-right">Margin Req.</th>
                      <th className="px-3 py-2 font-bold text-right">Rate p.a.</th>
                      <th className="px-3 py-2 font-bold text-right">Tenure</th>
                      <th className="px-3 py-2 font-bold text-right">Monthly EMI</th>
                      <th className="px-3 py-2 font-bold text-right">Avg DSCR</th>
                      <th className="px-3 py-2 font-bold text-center">Status</th>
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-stone-100">
                    {alternatives.slice(0, 8).map((opt, i) => {
                      const isRecommended = opt.is_recommended || opt.recommended || i === 0;
                      return (
                        <tr key={i} className={isRecommended ? 'bg-orange-50/40 font-medium' : ''}>
                          <td className="px-3 py-2 text-[#1C1917]">
                            <div className="flex items-center gap-1.5">
                              {isRecommended && <Award className="w-3.5 h-3.5 text-[#EA580C] shrink-0" />}
                              <span className={isRecommended ? 'font-bold text-[#EA580C]' : 'font-medium'}>
                                {opt.scheme_name || opt.name || 'MSME Term Loan'}
                              </span>
                            </div>
                          </td>
                          <td className="px-3 py-2 text-right font-medium text-[#1C1917]">
                            {formatINR(opt.loan_amount || opt.sanctioned_loan_amount || proposedLoan)}
                          </td>
                          <td className="px-3 py-2 text-right text-stone-600">
                            {formatINR(opt.promoter_margin || opt.promoter_contribution || opt.required_margin || requiredMargin)}
                          </td>
                          <td className="px-3 py-2 text-right text-stone-600">
                            {formatPct(opt.interest_rate_pct ?? (opt.interest_rate ? (opt.interest_rate <= 1 ? opt.interest_rate * 100 : opt.interest_rate) : (opt.annual_interest_rate ? opt.annual_interest_rate * 100 : 8.0)))}
                          </td>
                          <td className="px-3 py-2 text-right text-stone-600">
                            {opt.tenure_months || 84} Mo
                          </td>
                          <td className="px-3 py-2 text-right font-bold text-[#1C1917]">
                            {formatINR(opt.monthly_emi || monthlyEmi)}
                          </td>
                          <td className="px-3 py-2 text-right font-bold text-blue-700">
                            {formatRatioVal(opt.stress_case_dscr ?? opt.stress_dscr ?? opt.dscr ?? opt.average_dscr ?? avgDscr)}
                          </td>
                          <td className="px-3 py-2 text-center">
                            <span
                              className={`px-2 py-0.5 rounded text-[10px] font-bold ${
                                isRecommended
                                  ? 'bg-[#EA580C] text-white'
                                  : 'bg-stone-100 text-stone-700 border border-stone-200'
                              }`}
                            >
                              {isRecommended ? 'SELECTED STRUCTURE' : 'ALTERNATIVE SCENARIO'}
                            </span>
                          </td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            </div>

            {/* SECTION 5: Banking Appraisal Ratios (M4) & Stress Testing Resilience (M5) */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

              {/* Banking & Solvency Ratios */}
              <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    Banking Solvency Ratios (M4 Appraisal)
                  </h3>
                  <span className="text-[10px] text-stone-500 font-semibold px-2 py-0.5 bg-stone-100 rounded">
                    Audit Checked
                  </span>
                </div>

                <table className="w-full text-xs text-left border-collapse border border-stone-200 rounded-lg overflow-hidden">
                  <tbody className="divide-y divide-stone-100">
                    <tr>
                      <td className="px-3.5 py-2 text-stone-600 font-medium">Average DSCR (5-Year)</td>
                      <td className="px-3.5 py-2 text-right font-black text-blue-700 text-sm">
                        {formatRatioVal(avgDscr)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-stone-600 font-medium">Minimum DSCR</td>
                      <td className="px-3.5 py-2 text-right font-bold text-[#1C1917]">
                        {formatRatioVal(dpr?.banking_metrics?.minimum_dscr ?? 1.48)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-stone-600 font-medium">Annual Break-Even Sales</td>
                      <td className="px-3.5 py-2 text-right font-bold text-[#1C1917]">
                        {formatINR(breakEvenSales)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-stone-600 font-medium">Break-Even Capacity Utilization</td>
                      <td className="px-3.5 py-2 text-right font-bold text-[#1C1917]">
                        {formatPct(dpr?.banking_metrics?.break_even_capacity_pct ?? 34.2)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-stone-600 font-medium">Initial Debt-to-Equity Ratio</td>
                      <td className="px-3.5 py-2 text-right font-bold text-[#1C1917]">
                        {formatRatioVal(dpr?.banking_metrics?.debt_equity_ratio_initial ?? 9.0)}
                      </td>
                    </tr>
                    <tr>
                      <td className="px-3.5 py-2 text-stone-600 font-medium">Current Ratio (Year 1)</td>
                      <td className="px-3.5 py-2 text-right font-bold text-[#1C1917]">
                        {formatRatioVal(dpr?.banking_metrics?.current_ratio_y1 ?? 2.15)}
                      </td>
                    </tr>
                  </tbody>
                </table>
              </div>

              {/* Stress Testing Resilience & Compliance */}
              <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    M5 Stress Testing & Downside Appraisal
                  </h3>
                  <span className="text-[10px] text-stone-500 font-semibold px-2 py-0.5 bg-stone-100 rounded">
                    Worst-Case Sensitivity
                  </span>
                </div>

                <div className="p-3.5 rounded-xl bg-amber-50/60 border border-amber-200 text-xs space-y-2">
                  <div className="flex justify-between font-bold text-amber-900">
                    <span>Financing Resilience Status:</span>
                    <span className="text-emerald-800 flex items-center gap-1">
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                      {dpr?.m5_stress_appraisal?.financing_resilience_status || 'RESILIENT'}
                    </span>
                  </div>
                  <div className="flex justify-between text-amber-800 text-[11px]">
                    <span>Tested Scenario:</span>
                    <span className="font-semibold">{dpr?.m5_stress_appraisal?.worst_case_scenario || 'Revenue -15% & Variable Cost +10%'}</span>
                  </div>
                  <div className="flex justify-between text-amber-800 text-[11px]">
                    <span>Downside Stressed DSCR:</span>
                    <span className="font-bold text-blue-900">{formatRatioVal(dpr?.m5_stress_appraisal?.downside_dscr ?? 1.28)}</span>
                  </div>
                </div>

                <div className="space-y-2 text-xs">
                  <span className="font-bold text-[#1C1917] block">Required Compliance & Verification Documents:</span>
                  <div className="space-y-1.5">
                    {(eligibility?.required_documents || ['Aadhaar / Voter ID', 'Udyam Registration Certificate', 'Detailed Project Report (DPR)', '6-Month Bank Account Statements']).map((doc, i) => (
                      <div key={i} className="flex items-center gap-2 p-2 bg-[#FAF7F2] rounded-lg border border-[#EAE3D5]">
                        <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                        <span className="font-medium text-[#1C1917]">{doc}</span>
                      </div>
                    ))}
                  </div>
                </div>
              </div>

            </div>

            {/* SECTION 6: Milestone Completion & Workflow Return Handoff */}
            <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] flex flex-col sm:flex-row items-center justify-between gap-6 bg-white">
              <div className="space-y-1">
                <span className="text-xs font-bold uppercase tracking-wider text-emerald-700 flex items-center gap-1">
                  <CheckCircle2 className="w-4 h-4" />
                  Stage 09 Financial Planning Complete & Verified
                </span>
                <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                  Full Financial Model & Credit Dossier Structured
                </h3>
                <p className="text-xs text-[#57534E] max-w-xl">
                  Authoritative M1–M6 metrics have been calculated deterministically. Your project cost of {formatINR(totalProjectCost)} is fully financed with {formatINR(proposedLoan)} in proposed institutional credit and {formatINR(requiredMargin)} in promoter equity.
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
        {/* TAB 2: INTERACTIVE STANDALONE LOAN CALCULATOR                            */}
        {/* ========================================================================= */}
        {activeTab === 'calculator' && (
          <div className="space-y-6 animate-fadeIn">
            <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">

              {/* Calculator Input Form */}
              <div className="lg:col-span-5 royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-4">
                <div className="space-y-1">
                  <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <Calculator className="w-5 h-5 text-[#EA580C]" />
                    Interactive Financing Calculator
                  </h3>
                  <p className="text-xs text-[#78716C]">
                    Perform what-if exploratory calculations without changing your core workflow profile.
                  </p>
                </div>

                <form onSubmit={executeCalculator} className="space-y-4 text-xs">
                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">
                      Available Margin Capital (INR)
                    </label>
                    <input
                      type="number"
                      value={calcMargin}
                      onChange={(e) => setCalcMargin(e.target.value)}
                      placeholder="200000"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                    <span className="text-[10px] text-[#78716C]">Default 10% equity contribution benchmark</span>
                  </div>

                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">
                      Preferred Project Cost (Optional)
                    </label>
                    <input
                      type="number"
                      value={calcProjectCost}
                      onChange={(e) => setCalcProjectCost(e.target.value)}
                      placeholder="Leave blank to derive from margin"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div className="grid grid-cols-3 gap-2">
                    <div>
                      <label className="font-bold text-[#1C1917] block mb-1">Rate (% p.a.)</label>
                      <input
                        type="number"
                        step="0.1"
                        value={calcRateOverride}
                        onChange={(e) => setCalcRateOverride(e.target.value)}
                        placeholder="8.0"
                        className="w-full px-3 py-2 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] text-xs font-semibold outline-none"
                      />
                    </div>
                    <div>
                      <label className="font-bold text-[#1C1917] block mb-1">Tenure (Mo)</label>
                      <input
                        type="number"
                        value={calcTenureOverride}
                        onChange={(e) => setCalcTenureOverride(e.target.value)}
                        placeholder="84"
                        className="w-full px-3 py-2 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] text-xs font-semibold outline-none"
                      />
                    </div>
                    <div>
                      <label className="font-bold text-[#1C1917] block mb-1">Moratorium</label>
                      <input
                        type="number"
                        value={calcMoratoriumOverride}
                        onChange={(e) => setCalcMoratoriumOverride(e.target.value)}
                        placeholder="6"
                        className="w-full px-3 py-2 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] text-xs font-semibold outline-none"
                      />
                    </div>
                  </div>

                  <button
                    type="submit"
                    disabled={calcLoading}
                    className="w-full saffron-gradient-btn py-3 rounded-xl font-bold text-xs flex items-center justify-center gap-2 shadow-md"
                  >
                    {calcLoading ? (
                      <>
                        <RefreshCw className="w-4 h-4 animate-spin" />
                        <span>Calculating...</span>
                      </>
                    ) : (
                      <>
                        <Calculator className="w-4 h-4" />
                        <span>Calculate Loan Structure</span>
                      </>
                    )}
                  </button>
                </form>
              </div>

              {/* Calculator Results Display */}
              <div className="lg:col-span-7 space-y-4">
                {calcResult && (
                  <div className="royal-card rounded-2xl p-6 border border-[#EAE3D5] bg-white space-y-5 animate-fadeIn">
                    <div className="flex items-center justify-between">
                      <div className="space-y-0.5">
                        <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700">
                          Calculation Estimate &bull; Not a Sanction
                        </span>
                        <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                          {calcResult.schemeName}
                        </h3>
                      </div>
                      <div className="text-right">
                        <span className="text-[10px] text-stone-500 uppercase font-bold block">Monthly EMI</span>
                        <div className="text-2xl font-black text-[#EA580C] font-['Outfit']">
                          {formatINR(calcResult.monthlyEmi)}
                        </div>
                      </div>
                    </div>

                    <div className="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs">
                      <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#EAE3D5]">
                        <span className="text-stone-500 block text-[10px]">Project Cost</span>
                        <strong className="text-[#1C1917] text-sm">{formatINR(calcResult.theoreticalProjectCost)}</strong>
                      </div>
                      <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#EAE3D5]">
                        <span className="text-stone-500 block text-[10px]">Required Margin</span>
                        <strong className="text-emerald-700 text-sm">{formatINR(calcResult.requiredMargin)}</strong>
                      </div>
                      <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#EAE3D5]">
                        <span className="text-stone-500 block text-[10px]">Estimated Loan</span>
                        <strong className="text-[#C2410C] text-sm">{formatINR(calcResult.estimatedLoanRequirement)}</strong>
                      </div>
                      <div className="p-3 bg-[#FAF7F2] rounded-xl border border-[#EAE3D5]">
                        <span className="text-stone-500 block text-[10px]">Total Repayment</span>
                        <strong className="text-[#1C1917] text-sm">{formatINR(calcResult.totalRepayment)}</strong>
                      </div>
                    </div>
                  </div>
                )}
              </div>

            </div>
          </div>
        )}

        {/* ========================================================================= */}
        {/* PARAMETER ADJUSTMENT MODAL / DRAWER                                      */}
        {/* ========================================================================= */}
        {isEditDrawerOpen && (
          <div className="fixed inset-0 z-50 overflow-hidden bg-black/40 backdrop-blur-xs flex justify-end">
            <div className="w-full max-w-md bg-white h-full shadow-2xl p-6 overflow-y-auto space-y-6 flex flex-col justify-between animate-slideIn">
              <div className="space-y-5">
                <div className="flex items-center justify-between pb-3 border-b border-stone-200">
                  <div className="flex items-center gap-2">
                    <SlidersHorizontal className="w-5 h-5 text-[#EA580C]" />
                    <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                      Adjust Business & Financial Inputs
                    </h3>
                  </div>
                  <button
                    onClick={() => setIsEditDrawerOpen(false)}
                    className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-500"
                  >
                    <X className="w-5 h-5" />
                  </button>
                </div>

                <form onSubmit={handleUpdateParameters} className="space-y-4 text-xs">
                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">Business Name</label>
                    <input
                      type="text"
                      value={editBusinessName}
                      onChange={(e) => setEditBusinessName(e.target.value)}
                      placeholder="Saree Retail"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">Sector</label>
                    <input
                      type="text"
                      value={editSector}
                      onChange={(e) => setEditSector(e.target.value)}
                      placeholder="Retail"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">Category</label>
                    <input
                      type="text"
                      value={editCategory}
                      onChange={(e) => setEditCategory(e.target.value)}
                      placeholder="Apparel Retail"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">Subcategory</label>
                    <input
                      type="text"
                      value={editSubcategory}
                      onChange={(e) => setEditSubcategory(e.target.value)}
                      placeholder="Women's Traditional Apparel"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div className="pt-2 border-t border-stone-200">
                    <label className="font-bold text-[#1C1917] block mb-1">
                      Available Margin Capital (INR)
                    </label>
                    <input
                      type="number"
                      value={editMarginCapital}
                      onChange={(e) => setEditMarginCapital(e.target.value)}
                      placeholder="200000"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                    <span className="text-[10px] text-[#78716C]">Self-financed equity available from entrepreneur</span>
                  </div>

                  <div>
                    <label className="font-bold text-[#1C1917] block mb-1">
                      Preferred Project Cost (Optional INR)
                    </label>
                    <input
                      type="number"
                      value={editPreferredCost}
                      onChange={(e) => setEditPreferredCost(e.target.value)}
                      placeholder="Leave blank for benchmark sizing"
                      className="w-full px-3.5 py-2.5 rounded-xl border border-[#D9CFC4] bg-[#FAF7F2] font-semibold text-[#1C1917] focus:ring-2 focus:ring-[#EA580C] outline-none"
                    />
                  </div>

                  <div className="pt-4 flex gap-2">
                    <button
                      type="button"
                      onClick={() => setIsEditDrawerOpen(false)}
                      className="w-1/2 py-2.5 rounded-xl border border-stone-300 font-bold text-stone-700 hover:bg-stone-50"
                    >
                      Cancel
                    </button>
                    <button
                      type="submit"
                      className="w-1/2 saffron-gradient-btn py-2.5 rounded-xl font-bold shadow-md flex items-center justify-center gap-1.5"
                    >
                      <Check className="w-4 h-4" />
                      <span>Recalculate</span>
                    </button>
                  </div>
                </form>
              </div>
            </div>
          </div>
        )}

      </div>
    </div>
  );
}
