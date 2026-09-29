import React, { useState, useEffect, useRef, useCallback, Component } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  ShieldCheck,
  Award,
  AlertTriangle,
  CheckCircle2,
  Lock,
  Zap,
  RefreshCw,
  Info,
  ArrowRight,
  TrendingUp,
  UserCheck,
  Building2,
  MapPin,
  Mic,
  MicOff,
  Send,
  HelpCircle,
  Sparkles,
  ChevronDown,
  ChevronUp,
  Briefcase,
  GraduationCap,
  Hammer,
  Clock,
  ExternalLink,
  Sliders,
  DollarSign,
  Activity,
  Layers,
  AlertOctagon,
  ArrowLeft,
  Check,
  BookOpen,
  Compass,
  FileText,
  Calculator,
  Database,
  X,
  Eye,
  CheckCircle,
  BarChart3,
  Scale,
  RefreshCcw,
  Target,
  ArrowUpRight,
  CheckCheck,
  MessageSquare
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';
import Button from '../../components/ui/Button';
import CalculationBreakdown from '../../components/common/CalculationBreakdown';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';
import Kalpa3DCard from '../../components/ui/Kalpa3DCard';
import FeasibilityScoreCard from '../../components/ui/FeasibilityScoreCard';
import { extractCanonicalBusinessContext } from '../../services/canonicalBusinessContext';

// ---------------------------------------------------------------------------
// Reusable Safe Data Formatter (Prevents "Objects are not valid as a React child")
// ---------------------------------------------------------------------------
export const formatDisplayValue = (val) => {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (typeof val === 'number') {
    return Number.isInteger(val) ? val.toString() : val.toFixed(2);
  }
  if (typeof val === 'string') return val;
  if (Array.isArray(val)) {
    return val.map((v) => (typeof v === 'object' ? JSON.stringify(v) : String(v))).join(', ');
  }
  if (typeof val === 'object') {
    if (val.title || val.name || val.description || val.text || val.message) {
      return val.title || val.name || val.description || val.text || val.message;
    }
    try {
      return JSON.stringify(val);
    } catch {
      return String(val);
    }
  }
  return String(val);
};

// ---------------------------------------------------------------------------
// Human-Friendly Enum Label Formatter (No Raw Machine Tokens)
// ---------------------------------------------------------------------------
export const formatEnumLabel = (val) => {
  if (val === null || val === undefined) return '—';
  if (typeof val !== 'string') return formatDisplayValue(val);
  const v = val.trim();
  const map = {
    'USER_INPUT': 'User Input',
    'USER_VOICE': 'Voice Input',
    'USER_CLARIFICATION': 'Clarification Input',
    'ACTUAL': 'Verified Actual',
    'VERIFIED': 'Verified',
    'CALCULATED': 'Calculated',
    'BENCHMARK': 'Benchmark',
    'KNOWLEDGE_DATABASE': 'Knowledge Base',
    'BENCHMARK_DATABASE': 'Benchmark Database',
    'BUSINESS_ONTOLOGY': 'Business Ontology',
    'STAGE_KNOWLEDGE_BENCHMARKS': 'Stage Benchmark',
    'STAGE_6_MARKET_INTELLIGENCE': 'Market Intel',
    'STAGE_8_OPPORTUNITY': 'Opportunity Signal',
    'STAGE_9_FINANCIAL': 'Financial Plan',
    'STAGE_10_ENTREPRENEUR_PROFILE': 'Profile Engine',
    'STAGE_11_RISK': 'Risk Engine',
    'STAGE_12_FEASIBILITY': 'Feasibility Engine',
    'PROXY': 'Proxy Estimate',
    'PROXY_DATA': 'Proxy Estimate',
    'DATA_GAP': 'Data Gap',
    'UNKNOWN_DATA_GAP': 'Data Gap',
    'BENCHMARK_DATA_UNAVAILABLE': 'Data Gap',
    'STRONG': 'Strong',
    'ADEQUATE': 'Adequate',
    'DEVELOPING': 'Developing',
    'DEFICIENT': 'Deficient',
    'HIGH': 'High',
    'MODERATE': 'Moderate',
    'MEDIUM': 'Medium',
    'LOW': 'Low',
    'CRITICAL': 'Critical',
    'PASS': 'Pass',
    'CAUTION': 'Caution',
    'RESTRICT': 'Restrict',
    'VIABLE': 'Viable',
    'CONDITIONALLY_VIABLE': 'Conditionally Viable',
    'VIABLE_WITH_CAUTION': 'Viable with Caution',
    'NOT_FEASIBLE': 'Not Feasible',
    'COMPLETE': 'Complete',
    'INCOMPLETE': 'Incomplete',
    'READY': 'Ready',
    'PROFILE_INCOMPLETE': 'Clarification Needed',
    'CLARIFICATION_REQUIRED': 'Clarification Needed'
  };
  if (map[v.toUpperCase()]) return map[v.toUpperCase()];
  return v
    .toLowerCase()
    .split('_')
    .map((w) => w.charAt(0).toUpperCase() + w.slice(1))
    .join(' ');
};

// ---------------------------------------------------------------------------
// Clarification Item Normalizer (Standardizes Backend Contract)
// ---------------------------------------------------------------------------
export const normalizeClarification = (item) => {
  if (!item || typeof item !== 'object') return null;

  const field = item.field || item.question_id || item.target_field || '';
  const question =
    item.question ??
    item.question_text ??
    item.question_en ??
    item.prompt ??
    item.display_question ??
    item.label ??
    item.message ??
    null;

  const priority =
    item.priority ??
    item.importance ??
    'HIGH';

  const reason =
    item.reason ??
    item.why_it_matters ??
    item.description ??
    'Required for deterministic entrepreneur readiness evaluation.';

  const benchmark =
    item.benchmark ??
    item.benchmark_requirement ??
    item.benchmark_min ??
    null;

  const current_value =
    item.current_value ??
    item.value ??
    null;

  const input_type = item.input_type || 'text';
  const suggested_options = Array.isArray(item.suggested_options)
    ? item.suggested_options
    : (typeof item.suggested_options === 'string' ? [item.suggested_options] : []);

  if (!question) {
    console.warn('[STAGE 10] Missing clarification question text in item:', item);
  }

  return {
    field,
    question: question || `Please provide details for ${field}`,
    raw_question: question,
    priority,
    importance: priority,
    reason,
    benchmark,
    current_value,
    input_type,
    suggested_options,
    raw: item,
  };
};

// ---------------------------------------------------------------------------
// Authoritative Stage Completion Checkers
// ---------------------------------------------------------------------------
export const isValidStageResult = (result) => {
  return Boolean(
    result &&
    typeof result === 'object' &&
    result.status !== 'error' &&
    result.status !== 'DATA_GAP'
  );
};

export const isStage10Complete = (data) => {
  if (!data || typeof data !== 'object') return false;
  if (
    data.status === 'CLARIFICATION_REQUIRED' ||
    data.readiness_status === 'CLARIFICATION_REQUIRED' ||
    data.status === 'PROFILE_INCOMPLETE' ||
    data.status === 'INCOMPLETE' ||
    data.status === 'error' ||
    data.status === 'DATA_GAP'
  ) {
    return false;
  }
  const questions = data.questions || [];
  const missing = data.missing_fields || data.pending_fields || [];
  if (questions.length > 0 || missing.length > 0) {
    return false;
  }
  if (
    data.status === 'COMPLETE' ||
    data.status === 'READY' ||
    data.readiness_status === 'COMPLETE' ||
    data.readiness_status === 'READY'
  ) {
    return true;
  }
  return data.readiness_score !== undefined && data.readiness_score !== null;
};

export const isStage11Complete = (data) => {
  if (!data || typeof data !== 'object') return false;
  if (data.status === 'error' || data.status === 'DATA_GAP') return false;
  if (data.overall_risk_severity === 'DATA_GAP' || data.overall_risk_severity === 'UNKNOWN') return false;
  return (data.overall_risk_score !== undefined && data.overall_risk_score !== null) || Boolean(data.overall_risk_severity);
};

// ---------------------------------------------------------------------------
// Reusable Safe Data Integrity Badge (KALPA Warm Palette - Strict Zero Cyan)
// ---------------------------------------------------------------------------
export const renderIntegrityBadge = (sourceType) => {
  const norm = (sourceType || '').toUpperCase();
  if (norm.includes('USER') || norm === 'USER_INPUT' || norm === 'USER_VOICE' || norm === 'USER_CLARIFICATION') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25">
        User Input
      </span>
    );
  }
  if (norm === 'ACTUAL' || norm === 'VERIFIED') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/25">
        Verified
      </span>
    );
  }
  if (norm === 'CALCULATED') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25">
        Calculated
      </span>
    );
  }
  if (
    norm === 'BENCHMARK' ||
    norm === 'KNOWLEDGE_DATABASE' ||
    norm === 'BUSINESS_ONTOLOGY' ||
    norm === 'STAGE_KNOWLEDGE_BENCHMARKS' ||
    norm === 'BENCHMARK_DATABASE'
  ) {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20">
        Benchmark
      </span>
    );
  }
  if (norm === 'UNKNOWN' || norm === 'UNKNOWN_DATA_GAP' || norm === 'DATA_GAP' || norm === 'BENCHMARK_DATA_UNAVAILABLE') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/30 animate-pulse">
        Data Gap
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/15">
      {formatEnumLabel(sourceType) || 'Provenance'}
    </span>
  );
};

// ---------------------------------------------------------------------------
// Severity & Level Helpers (KALPA Warm Palette - Strict Zero Cyan)
// ---------------------------------------------------------------------------
export const getSeverityBadge = (sev) => {
  const s = String(sev || '').toUpperCase();
  switch (s) {
    case 'CRITICAL':
    case 'RESTRICT':
    case 'HIGH':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/30">
          <AlertTriangle className="w-3 h-3 mr-1 text-[#79563F]" /> {formatEnumLabel(s)}
        </span>
      );
    case 'MEDIUM':
    case 'CAUTION':
    case 'DEVELOPING':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20">
          <Activity className="w-3 h-3 mr-1 text-[#79563F]" /> {formatEnumLabel(s)}
        </span>
      );
    case 'LOW':
    case 'PASS':
    case 'STRONG':
    case 'ADEQUATE':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/25">
          <CheckCircle2 className="w-3 h-3 mr-1 text-[#1B4D3E]" /> {formatEnumLabel(s)}
        </span>
      );
    case 'UNKNOWN':
    case 'DATA_GAP':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25">
          Data Gap
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/15">
          {formatEnumLabel(sev) || 'Evaluated'}
        </span>
      );
  }
};

export const getFeasibilityDecisionBadge = (decision) => {
  const d = String(decision || '').toUpperCase();
  switch (d) {
    case 'VIABLE':
      return (
        <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-bold bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/25 shadow-2xs">
          <CheckCircle className="w-3.5 h-3.5 mr-1.5 text-[#1B4D3E]" /> Viable for Venture Launch
        </span>
      );
    case 'VIABLE_WITH_CAUTION':
      return (
        <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/30 shadow-2xs">
          <AlertTriangle className="w-3.5 h-3.5 mr-1.5 text-[#79563F]" /> Viable with Operational Caution
        </span>
      );
    case 'CONDITIONALLY_VIABLE':
      return (
        <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-bold bg-amber-50 text-amber-800 border border-amber-300 shadow-2xs">
          <Activity className="w-3.5 h-3.5 mr-1.5 text-amber-700" /> Conditionally Viable
        </span>
      );
    case 'NOT_FEASIBLE':
      return (
        <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/35 shadow-2xs">
          <AlertOctagon className="w-3.5 h-3.5 mr-1.5 text-[#79563F]" /> Not Feasible in Current Configuration
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-3.5 py-1 rounded-full text-xs font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/20 shadow-2xs">
          {formatEnumLabel(decision) || 'Pending Evaluation'}
        </span>
      );
  }
};

// ---------------------------------------------------------------------------
// Slide-Over Full Calculation Drawer Component (KALPA Dark Stone / Bronze)
// ---------------------------------------------------------------------------
export const CalculationDrawer = ({ isOpen, onClose, title, subtitle, provenanceData, type = 'stage10' }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div className="w-full max-w-2xl bg-stone-900 text-stone-100 h-full shadow-2xl flex flex-col justify-between border-l border-stone-800 animate-slideLeft">
        {/* Drawer Header */}
        <div className="p-6 border-b border-stone-800 flex items-center justify-between bg-stone-950">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#79563F] text-white uppercase tracking-wider font-mono">
                {type === 'stage10' ? 'Readiness Audit' : (type === 'stage11' ? 'Risk Audit' : 'Feasibility Audit')}
              </span>
              <span className="text-xs text-stone-400 font-mono">100% Deterministic Engine</span>
            </div>
            <h3 className="text-lg font-bold text-white font-['Outfit']">{title}</h3>
            {subtitle && <p className="text-xs text-stone-400">{subtitle}</p>}
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-stone-800 hover:bg-stone-700 text-stone-400 hover:text-white transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* Drawer Content */}
        <div className="p-6 overflow-y-auto space-y-6 flex-1">
          <div className="space-y-3">
            <h4 className="text-xs font-bold text-stone-400 uppercase tracking-wider flex items-center gap-1.5 font-mono">
              <Calculator className="w-4 h-4 text-[#A05A35]" />
              Full Mathematical Synthesis & Provenance Audit
            </h4>
            <CalculationBreakdown
              items={provenanceData}
              title={title}
              stage={type}
            />
          </div>
        </div>

        {/* Drawer Footer */}
        <div className="p-4 border-t border-stone-800 bg-stone-950 flex items-center justify-between text-xs text-stone-400">
          <span>Source: KALPA Deterministic Synthesis Engine</span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-lg text-xs font-bold transition cursor-pointer"
          >
            Close Audit Trail
          </button>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Dynamic SWOT Modal Viewer Component (KALPA Warm Beige Theme)
// ---------------------------------------------------------------------------
export const DynamicSWOTModal = ({ isOpen, onClose, swot, businessTitle }) => {
  if (!isOpen || !swot) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-xs animate-fadeIn">
      <div className="bg-[#FAF7F2] rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-[#79563F]/25 p-6 space-y-6 animate-scaleUp">
        <div className="flex items-center justify-between border-b border-[#79563F]/15 pb-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2.5 py-0.5 rounded text-[10px] font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 uppercase font-mono">
                Evidence-Grounded SWOT
              </span>
              <span className="text-xs text-stone-500">Strategic Synthesis</span>
            </div>
            <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
              Dynamic Strategic SWOT: {businessTitle}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-[#FAF2E3] hover:bg-[#F3E8D4] text-[#79563F] transition cursor-pointer border border-[#79563F]/20"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 2x2 SWOT Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strengths */}
          <div className="p-5 bg-[#EAF5EE] border border-[#1B4D3E]/25 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-[#1B4D3E] font-bold text-sm uppercase tracking-wider font-['Outfit']">
              <CheckCircle className="w-4 h-4 text-[#1B4D3E]" />
              <span>Strengths (Internal Advantages)</span>
            </div>
            <ul className="space-y-2">
              {swot.strengths?.map((s, idx) => (
                <li key={idx} className="text-xs text-[#1C1917] bg-white p-3 rounded-xl border border-[#1B4D3E]/15 space-y-1">
                  <div className="font-bold text-[#1B4D3E]">{formatDisplayValue(s.title || s)}</div>
                  {s.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(s.description)}</div>}
                  {s.evidence && (
                    <div className="text-[10px] text-[#1B4D3E] italic font-mono pt-1">
                      Evidence: {formatDisplayValue(s.evidence)} ({formatDisplayValue(s.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="p-5 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm uppercase tracking-wider font-['Outfit']">
              <AlertTriangle className="w-4 h-4 text-amber-600" />
              <span>Weaknesses (Internal Gaps)</span>
            </div>
            <ul className="space-y-2">
              {swot.weaknesses?.map((w, idx) => (
                <li key={idx} className="text-xs text-amber-950 bg-white p-3 rounded-xl border border-amber-100 space-y-1">
                  <div className="font-bold">{formatDisplayValue(w.title || w)}</div>
                  {w.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(w.description)}</div>}
                  {w.evidence && (
                    <div className="text-[10px] text-amber-700 italic font-mono pt-1">
                      Evidence: {formatDisplayValue(w.evidence)} ({formatDisplayValue(w.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Opportunities */}
          <div className="p-5 bg-[#FAF2E3]/80 border border-[#79563F]/25 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-[#79563F] font-bold text-sm uppercase tracking-wider font-['Outfit']">
              <Compass className="w-4 h-4 text-[#79563F]" />
              <span>Opportunities (External Growth Vectors)</span>
            </div>
            <ul className="space-y-2">
              {swot.opportunities?.map((o, idx) => (
                <li key={idx} className="text-xs text-[#28231F] bg-white p-3 rounded-xl border border-[#79563F]/15 space-y-1">
                  <div className="font-bold">{formatDisplayValue(o.title || o)}</div>
                  {o.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(o.description)}</div>}
                  {o.evidence && (
                    <div className="text-[10px] text-[#79563F] italic font-mono pt-1">
                      Evidence: {formatDisplayValue(o.evidence)} ({formatDisplayValue(o.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Threats */}
          <div className="p-5 bg-stone-100 border border-stone-300 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-stone-800 font-bold text-sm uppercase tracking-wider font-['Outfit']">
              <ShieldCheck className="w-4 h-4 text-stone-600" />
              <span>Threats (External Risks & Stress)</span>
            </div>
            <ul className="space-y-2">
              {swot.threats?.map((t, idx) => (
                <li key={idx} className="text-xs text-stone-900 bg-white p-3 rounded-xl border border-stone-200 space-y-1">
                  <div className="font-bold">{formatDisplayValue(t.title || t)}</div>
                  {t.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(t.description)}</div>}
                  {t.evidence && (
                    <div className="text-[10px] text-stone-600 italic font-mono pt-1">
                      Evidence: {formatDisplayValue(t.evidence)} ({formatDisplayValue(t.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <button
            onClick={onClose}
            className="px-4 py-2 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition cursor-pointer"
          >
            Close Strategic SWOT
          </button>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Informative Stage Locked Notice Component (KALPA Warm Palette)
// ---------------------------------------------------------------------------
export const StageLockedNotice = ({ stepNum, stepName, reason, unlockAction, onUnlockClick }) => {
  return (
    <div className="royal-panel bg-[#FAF2E3] rounded-2xl p-8 border border-[#79563F]/25 text-center space-y-4 max-w-xl mx-auto my-8 animate-fadeIn shadow-xs">
      <div className="w-14 h-14 bg-[#FAF7F2] rounded-2xl flex items-center justify-center mx-auto text-[#79563F] border border-[#79563F]/20 shadow-2xs">
        <Lock className="w-7 h-7" />
      </div>
      <div className="space-y-1.5">
        <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-widest font-mono">
          Feasibility · Step {stepNum} Prerequisite Guard Active
        </span>
        <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
          {stepName} is Locked
        </h3>
        <p className="text-xs text-[#57534E] leading-relaxed max-w-md mx-auto">
          {reason}
        </p>
      </div>

      <div className="pt-2">
        <button
          onClick={onUnlockClick}
          className="inline-flex items-center px-5 py-2.5 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition shadow-xs cursor-pointer space-x-1.5"
        >
          <span>{unlockAction || 'Complete Required Upstream Step'}</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </button>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Error Boundary Component
// ---------------------------------------------------------------------------
export class FeasibilityErrorBoundary extends Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }

  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }

  componentDidCatch(error, errorInfo) {
    console.error('[FEASIBILITY BOUNDARY CAUGHT ERROR]', error, errorInfo);
  }

  render() {
    if (this.state.hasError) {
      return (
        <div className="min-h-screen flex items-center justify-center p-6 relative">
          <div className="bg-[#FAF2E3] rounded-3xl p-8 border border-[#79563F]/25 shadow-xl max-w-lg w-full text-center space-y-4">
            <div className="w-14 h-14 bg-[#FAF7F2] rounded-2xl flex items-center justify-center mx-auto text-[#79563F] border border-[#79563F]/20">
              <AlertOctagon className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
                Feasibility Display Render Error
              </h2>
              <p className="text-xs text-stone-600 leading-relaxed">
                An unexpected error occurred while rendering the assessment. Your session and inputs are safe.
              </p>
            </div>
            <div className="p-3 bg-white rounded-xl text-xs text-stone-600 font-mono text-left max-h-32 overflow-y-auto border border-[#79563F]/15">
              {String(this.state.error?.message || this.state.error)}
            </div>
            <div className="pt-2 flex justify-center space-x-3">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition shadow-sm cursor-pointer"
              >
                Reload Assessment
              </button>
              <Link
                to="/journey"
                className="px-4 py-2 bg-[#FAF7F2] hover:bg-[#F3E8D4] text-[#28231F] rounded-xl text-xs font-bold transition inline-flex items-center border border-[#79563F]/20"
              >
                Return to Journey
              </Link>
            </div>
          </div>
        </div>
      );
    }
    return this.props.children;
  }
}

// ---------------------------------------------------------------------------
// Canonical 5 Readiness Dimensions List Definition
// ---------------------------------------------------------------------------
const READINESS_DIMENSIONS = [
  {
    key: 'skills',
    title: 'Skills',
    icon: Hammer,
    defaultWeight: 0.25,
    description: 'Technical, vocational, and trade competencies verified against sector benchmarks'
  },
  {
    key: 'experience',
    title: 'Experience',
    icon: Briefcase,
    defaultWeight: 0.25,
    description: 'Years of direct domain experience, previous venture ownership, and operational background'
  },
  {
    key: 'training',
    title: 'Training',
    icon: GraduationCap,
    defaultWeight: 0.15,
    description: 'Formal vocational certifications, compliance training, and statutory accreditations'
  },
  {
    key: 'resources',
    title: 'Resources',
    icon: Building2,
    defaultWeight: 0.20,
    description: 'Available land area, commercial premises, utility connections, and existing equipment'
  },
  {
    key: 'operational_readiness',
    altKey: 'operational',
    title: 'Operational Readiness',
    icon: Clock,
    defaultWeight: 0.15,
    description: 'Full-time commitment, daily operating hours, helper availability, and labor management'
  }
];

// ---------------------------------------------------------------------------
// Canonical 4 Analytical Pillars List Definition (Step 3)
// ---------------------------------------------------------------------------
const FEASIBILITY_PILLARS = [
  {
    key: 'market_opportunity',
    title: 'Market Opportunity & Demand Potential',
    defaultScore: 49,
    defaultWeight: 25,
    defaultContribution: 12.3,
    defaultStatus: 'Caution',
    sourceStage: 'STAGE_8_OPPORTUNITY'
  },
  {
    key: 'financial_viability',
    title: 'Financial Viability & Repayment Buffer',
    defaultScore: 92,
    defaultWeight: 35,
    defaultContribution: 32.2,
    defaultStatus: 'Strong',
    sourceStage: 'STAGE_9_FINANCIAL'
  },
  {
    key: 'entrepreneur_readiness',
    title: 'Entrepreneur Competency & Operational Readiness',
    defaultScore: 72,
    defaultWeight: 20,
    defaultContribution: 14.5,
    defaultStatus: 'Adequate',
    sourceStage: 'STAGE_10_ENTREPRENEUR_PROFILE'
  },
  {
    key: 'risk_resilience',
    title: 'Multi-Vector Risk Resilience',
    defaultScore: 57,
    defaultWeight: 20,
    defaultContribution: 11.4,
    defaultStatus: 'Adequate',
    sourceStage: 'STAGE_11_RISK'
  }
];

// ---------------------------------------------------------------------------
// Main Feasibility Page (Multi-Step: Step 1 Readiness -> Step 2 Risk -> Step 3 Synthesis)
// ---------------------------------------------------------------------------
export const FeasibilityPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const { t, language } = useLanguage();

  const {
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
    businessName: ctxBusinessName,
    businessProfile: ctxBusinessProfile,
    businessId: ctxBusinessId,
    markStageComplete,
    startNewAnalysis
  } = useWorkflow();

  const queryParams = new URLSearchParams(location.search);
  const effectiveSessionId =
    location.state?.sessionId ||
    queryParams.get('session_id') ||
    ctxSessionId ||
    sessionStorage.getItem('kalpa_session_id') ||
    '';

  const effectiveAnalysisId =
    location.state?.analysisId ||
    queryParams.get('analysis_id') ||
    ctxAnalysisId ||
    sessionStorage.getItem('kalpa_analysis_id') ||
    effectiveSessionId;

  const sessionId = effectiveSessionId;
  const analysisId = effectiveAnalysisId;

  useEffect(() => {
    if (effectiveSessionId) sessionStorage.setItem('kalpa_session_id', effectiveSessionId);
    if (effectiveAnalysisId) sessionStorage.setItem('kalpa_analysis_id', effectiveAnalysisId);
  }, [effectiveSessionId, effectiveAnalysisId]);

  // Step state: 'step1' (Readiness) | 'step2' (Risk) | 'step3' (Synthesis)
  const initialStepParam = queryParams.get('step') || location.state?.step || 'step1';
  const canonicalStep = (initialStepParam === '2' || initialStepParam === 'step2' || initialStepParam === 'risk')
    ? 'step2'
    : (initialStepParam === '3' || initialStepParam === 'step3' || initialStepParam === 'synthesis')
    ? 'step3'
    : 'step1';

  const [currentStep, setCurrentStep] = useState(canonicalStep);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Ensure switching between Step 1, Step 2, and Step 3 always scrolls instantly to the top
  useEffect(() => {
    window.scrollTo({ top: 0, left: 0, behavior: 'instant' });
    if (document.documentElement) document.documentElement.scrollTop = 0;
    if (document.body) document.body.scrollTop = 0;
  }, [currentStep]);

  // Stage 10 Data (Step 1)
  const [stage10Data, setStage10Data] = useState(null);
  const [expandedComponent, setExpandedComponent] = useState(null);
  const [clarificationAnswers, setClarificationAnswers] = useState({});
  const [submittingClarificationField, setSubmittingClarificationField] = useState(null);

  // Stage 11 Data (Step 2)
  const [stage11Data, setStage11Data] = useState(null);
  const [expandedRisk, setExpandedRisk] = useState('FINANCIAL');

  // Stage 12 Data (Step 3)
  const [feasibilityData, setFeasibilityData] = useState(null);
  const [expandedPillar, setExpandedPillar] = useState(null);

  // Modals & Drawers
  const [isStage10DrawerOpen, setIsStage10DrawerOpen] = useState(false);
  const [isStage11DrawerOpen, setIsStage11DrawerOpen] = useState(false);
  const [isStage12DrawerOpen, setIsStage12DrawerOpen] = useState(false);
  const [isSWOTModalOpen, setIsSWOTModalOpen] = useState(false);

  // Voice recording state
  const [isRecording, setIsRecording] = useState(false);
  const [activeVoiceField, setActiveVoiceField] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const browserSpeechRef = useRef(null);
  const browserTranscriptRef = useRef('');

  const isInitialFetchDone = useRef(false);

  // Canonical Business Context
  const canonicalContext = extractCanonicalBusinessContext(
    ctxBusinessProfile || location.state?.businessProfile,
    {
      businessId: ctxBusinessId || location.state?.businessId,
      sessionId: effectiveSessionId,
      businessName: ctxBusinessName || location.state?.businessName
    }
  );

  const businessTitle =
    stage10Data?.business_title ||
    canonicalContext?.businessName ||
    ctxBusinessName ||
    location.state?.businessName ||
    'Target Micro-Enterprise';

  const currentSector = canonicalContext?.sector || 'General Micro-Enterprise';
  const currentCategory = canonicalContext?.category || 'Manufacturing & Services';
  const currentSubcategory = canonicalContext?.subcategory || null;

  // Canonical Step Completion Statuses
  const s10Ready = isStage10Complete(stage10Data);
  const s11Ready = isStage11Complete(stage11Data);
  const s12Ready = Boolean(
    feasibilityData &&
    feasibilityData.overall_feasibility_score !== undefined &&
    feasibilityData.overall_feasibility_score !== null
  );
  const pendingQuestions = stage10Data?.questions || [];

  // Fetch full pipeline hydration with strict Step 1 -> Step 2 -> Step 3 gating
  const fetchData = useCallback(async () => {
    if (!analysisId && !sessionId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Fetch Stage 10 Entrepreneur Readiness (Step 1)
      const epRes = await apiService.entrepreneurProfile.analyze({
        analysis_id: analysisId,
        session_id: sessionId,
        language: language || 'en',
      });
      setStage10Data(epRes);

      const isS10CompleteNow = isStage10Complete(epRes);

      // If Step 1 is incomplete, keep user at step 1
      if (!isS10CompleteNow) {
        setStage11Data(null);
        setFeasibilityData(null);
        setCurrentStep('step1');
        setLoading(false);
        return;
      }

      // 2. Fetch Stage 11 Risk Analysis (Step 2)
      let riskRes = null;
      try {
        riskRes = await apiService.riskAnalysis.analyze({
          analysis_id: analysisId,
          session_id: sessionId,
          entrepreneur_readiness: epRes,
          language: language || 'en',
        });
        setStage11Data(riskRes);
      } catch (riskErr) {
        if (riskErr.response?.status === 409 || riskErr.status === 409) {
          console.warn('[STAGE 11 BLOCKED BY HARD GATE]', riskErr);
          setCurrentStep('step1');
          setLoading(false);
          return;
        }
        throw riskErr;
      }

      const isS11CompleteNow = isStage11Complete(riskRes);
      if (!isS11CompleteNow) {
        setFeasibilityData(null);
        setLoading(false);
        return;
      }

      // 3. Fetch Stage 12 Final Feasibility Synthesis (Step 3)
      try {
        const feasRes = await apiService.feasibility.analyze({
          analysis_id: analysisId,
          session_id: sessionId,
          entrepreneur_readiness: epRes,
          risk_analysis: riskRes,
          language: language || 'en',
        });
        setFeasibilityData(feasRes);

        if (markStageComplete) {
          markStageComplete(10, 11);
          markStageComplete(11, 12);
          markStageComplete(12, 13);
        }
      } catch (feasErr) {
        if (feasErr.response?.status === 409 || feasErr.status === 409) {
          console.warn('[STAGE 12 BLOCKED BY HARD GATE]', feasErr);
        } else {
          throw feasErr;
        }
      }
    } catch (err) {
      console.error('[FEASIBILITY READINESS ERROR]', err);
      setError(err.message || 'Failed to evaluate Feasibility model.');
    } finally {
      setLoading(false);
    }
  }, [analysisId, sessionId, markStageComplete]);

  useEffect(() => {
    if (!isInitialFetchDone.current) {
      isInitialFetchDone.current = true;
      fetchData();
    }
  }, [fetchData]);

  // Handle Clarification Submission (Voice and Text)
  const handleAnswerSubmit = async (field, explicitText = null) => {
    const rawAnswer = (explicitText !== null && explicitText !== undefined)
      ? explicitText
      : clarificationAnswers[field];
    const textAnswer = (typeof rawAnswer === 'string') ? rawAnswer.trim() : '';
    if (!textAnswer) return;

    setSubmittingClarificationField(field);
    setError(null);

    try {
      const clarifyRes = await apiService.entrepreneurProfile.clarify({
        text: textAnswer,
        field: field,
        analysis_id: analysisId,
        session_id: sessionId,
      });

      const updatedStage10 = clarifyRes.readiness_response || clarifyRes;
      setStage10Data(updatedStage10);
      setClarificationAnswers((prev) => ({ ...prev, [field]: '' }));

      const isCompleteNow = isStage10Complete(updatedStage10);

      // If Step 1 is now completely answered, evaluate Step 2 & Step 3
      if (isCompleteNow) {
        const updatedRisk = await apiService.riskAnalysis.analyze({
          analysis_id: analysisId,
          session_id: sessionId,
          entrepreneur_readiness: updatedStage10,
        });
        setStage11Data(updatedRisk);

        const updatedFeas = await apiService.feasibility.analyze({
          analysis_id: analysisId,
          session_id: sessionId,
          entrepreneur_readiness: updatedStage10,
          risk_analysis: updatedRisk,
        });
        setFeasibilityData(updatedFeas);

        if (markStageComplete) {
          markStageComplete(10, 11);
          markStageComplete(11, 12);
          markStageComplete(12, 13);
        }
      }
    } catch (err) {
      console.error('[CLARIFICATION ERROR]', err);
      setError(err.message || 'Could not process clarification answer.');
    } finally {
      setSubmittingClarificationField(null);
    }
  };

  // Voice recording handlers
  const startRecording = async (field) => {
    browserTranscriptRef.current = '';

    // Initialize Web Speech API concurrently if supported as fallback
    const SpeechRec = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRec) {
      try {
        const rec = new SpeechRec();
        rec.continuous = true;
        rec.interimResults = true;
        rec.lang = `${language || 'en'}-IN`;
        rec.onresult = (e) => {
          let str = '';
          for (let i = 0; i < e.results.length; i++) {
            str += e.results[i][0].transcript + ' ';
          }
          if (str.trim()) {
            browserTranscriptRef.current = str.trim();
          }
        };
        rec.onerror = () => {};
        rec.start();
        browserSpeechRef.current = rec;
      } catch (recErr) {
        console.warn('[BROWSER SPEECH INIT]', recErr);
      }
    }

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        if (browserSpeechRef.current) {
          try { browserSpeechRef.current.stop(); } catch (e) {}
        }
        stream.getTracks().forEach((track) => track.stop());

        const clientTranscript = (browserTranscriptRef.current || '').trim();
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });

        if ((!audioBlob || audioBlob.size < 50) && !clientTranscript) {
          console.warn('[VOICE STT] Recording is empty or too short');
          alert('Could not detect clear speech in the recording. Please speak closer to the microphone or type your answer.');
          return;
        }

        const formData = new FormData();
        if (audioBlob && audioBlob.size >= 50) {
          formData.append('file', audioBlob, 'clarification_recording.webm');
        }
        if (clientTranscript) {
          formData.append('transcript', clientTranscript);
        }
        formData.append('language_code', language || 'en');
        formData.append('selected_language', language || 'en');

        try {
          const sttRes = await apiService.intake.transcribe(formData);

          let resolvedTranscript = '';
          if (sttRes && typeof sttRes === 'object') {
            resolvedTranscript = (sttRes.transcript || '').trim();
          }
          if (!resolvedTranscript && clientTranscript) {
            resolvedTranscript = clientTranscript;
          }

          if (resolvedTranscript.length > 0) {
            setClarificationAnswers((prev) => ({ ...prev, [field]: resolvedTranscript }));
            await handleAnswerSubmit(field, resolvedTranscript);
          } else {
            const failMsg = sttRes?.message || 'Could not detect clear speech in the recording. Please speak closer to the microphone or type your answer.';
            console.warn('[VOICE STT NOTE]', failMsg);
            alert(failMsg);
          }
        } catch (sttErr) {
          if (clientTranscript) {
            setClarificationAnswers((prev) => ({ ...prev, [field]: clientTranscript }));
            await handleAnswerSubmit(field, clientTranscript);
          } else {
            const errMsg = sttErr?.message || (typeof sttErr === 'string' ? sttErr : 'Could not detect clear speech in the recording. Please speak closer to the microphone or type your answer.');
            console.warn('[VOICE STT NOTE] Voice transcription failed:', errMsg);
            alert(errMsg);
          }
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setActiveVoiceField(field);
    } catch (err) {
      if (browserSpeechRef.current) {
        try { browserSpeechRef.current.stop(); } catch (e) {}
      }
      console.error('[MIC ACCESS ERROR]', err);
      alert('Microphone access denied. Please type your answer.');
    }
  };

  const stopRecording = () => {
    if (browserSpeechRef.current) {
      try { browserSpeechRef.current.stop(); } catch (e) {}
    }
    if (mediaRecorderRef.current && isRecording) {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
      setActiveVoiceField(null);
    }
  };

  // Handle Pivot Candidate Selection
  const handleSelectPivot = (candidate) => {
    if (startNewAnalysis) {
      startNewAnalysis(candidate.business_id, candidate.business_name);
    }
    navigate('/intake', {
      state: {
        prefillBusiness: candidate.business_name,
        pivotFrom: businessTitle
      }
    });
  };

  if (!loading && !sessionId && !analysisId) {
    return (
      <div className="min-h-screen flex items-center justify-center p-6 relative">
        <div className="bg-[#FAF2E3] rounded-3xl p-8 border border-[#79563F]/25 shadow-xl max-w-lg w-full text-center space-y-4 animate-fadeIn">
          <div className="w-14 h-14 bg-[#FAF7F2] rounded-2xl flex items-center justify-center mx-auto text-[#79563F] border border-[#79563F]/20">
            <Lock className="w-8 h-8" />
          </div>
          <div className="space-y-1.5">
            <h2 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
              Analysis Context Unavailable
            </h2>
            <p className="text-xs text-stone-600 leading-relaxed">
              No active business session or analysis ID was found. Please complete the business intake and evaluation pipeline first.
            </p>
          </div>
          <div className="pt-2 flex justify-center space-x-3">
            <Link
              to="/intake"
              className="px-4 py-2.5 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition shadow-sm inline-flex items-center"
            >
              Start New Analysis
            </Link>
            <Link
              to="/journey"
              className="px-4 py-2.5 bg-[#FAF7F2] hover:bg-[#F3E8D4] text-[#28231F] rounded-xl text-xs font-bold transition inline-flex items-center border border-[#79563F]/20"
            >
              Return to Journey
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 space-y-8 relative text-[#28231F]">
      {/* Full Calculation Drawers */}
      <CalculationDrawer
        isOpen={isStage10DrawerOpen}
        onClose={() => setIsStage10DrawerOpen(false)}
        title="Stage 10: Entrepreneur Readiness Calculation Trail"
        subtitle={`Deterministic 5-Dimension Evaluation for ${businessTitle}`}
        provenanceData={stage10Data?.calculation_provenance}
        type="stage10"
      />

      <CalculationDrawer
        isOpen={isStage11DrawerOpen}
        onClose={() => setIsStage11DrawerOpen(false)}
        title="Stage 11: Enterprise Risk Synthesis Trail"
        subtitle={`Multi-Vector 7-Category Risk Synthesis for ${businessTitle}`}
        provenanceData={stage11Data?.calculation_provenance}
        type="stage11"
      />

      <CalculationDrawer
        isOpen={isStage12DrawerOpen}
        onClose={() => setIsStage12DrawerOpen(false)}
        title="Stage 12: Master Feasibility Synthesis Trail"
        subtitle={`4-Pillar Decision Matrix & Critical Gates Trace for ${businessTitle}`}
        provenanceData={feasibilityData?.calculation_provenance}
        type="stage12"
      />

      {/* Dynamic Strategic SWOT Modal */}
      <DynamicSWOTModal
        isOpen={isSWOTModalOpen}
        onClose={() => setIsSWOTModalOpen(false)}
        swot={feasibilityData?.dynamic_swot}
        businessTitle={businessTitle}
      />

      <div className="max-w-7xl mx-auto space-y-8">
        {/* 1. Standard KALPA Workflow Navigation Thread */}
        <WorkflowTimeline />

        {/* 2. Feasibility Step Progress Sub-Tracker (Step 1 -> Step 2 -> Step 3) */}
        <div className="bg-[#FAF2E3] p-1.5 rounded-xl border border-[#79563F]/20 flex flex-col sm:flex-row items-stretch sm:items-center gap-1.5 text-xs font-bold shadow-2xs">
          {/* Step 1 Pill */}
          <button
            type="button"
            onClick={() => setCurrentStep('step1')}
            className={`flex-1 px-4 py-2.5 rounded-lg flex items-center justify-between gap-2 transition-all cursor-pointer ${
              currentStep === 'step1'
                ? 'bg-[#79563F] text-[#FAF4E8] shadow-2xs'
                : s10Ready
                ? 'bg-[#FAF7F2] text-[#1B4D3E] hover:bg-white border border-[#1B4D3E]/20'
                : 'text-[#6F746E] hover:text-[#28231F]'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                s10Ready && currentStep !== 'step1'
                  ? 'bg-[#1B4D3E] text-white'
                  : currentStep === 'step1'
                  ? 'bg-white/20 text-white'
                  : 'bg-[#FAF2E3] text-[#79563F]'
              }`}>
                {s10Ready && currentStep !== 'step1' ? <Check className="w-3 h-3 stroke-[3]" /> : '1'}
              </span>
              <span className="font-['Outfit']">01. Entrepreneur Readiness</span>
            </div>
            {s10Ready && (
              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                currentStep === 'step1' ? 'bg-white/20 text-white' : 'bg-[#EAF5EE] text-[#1B4D3E]'
              }`}>
                {stage10Data?.readiness_score !== null && stage10Data?.readiness_score !== undefined ? `${Math.round(stage10Data.readiness_score)}/100` : 'Complete'}
              </span>
            )}
          </button>

          {/* Step 2 Pill */}
          <button
            type="button"
            disabled={!s10Ready}
            onClick={() => {
              if (s10Ready) setCurrentStep('step2');
            }}
            className={`flex-1 px-4 py-2.5 rounded-lg flex items-center justify-between gap-2 transition-all ${
              currentStep === 'step2'
                ? 'bg-[#79563F] text-[#FAF4E8] shadow-2xs cursor-pointer'
                : s11Ready
                ? 'bg-[#FAF7F2] text-[#1B4D3E] hover:bg-white border border-[#1B4D3E]/20 cursor-pointer'
                : s10Ready
                ? 'bg-[#FAF7F2] text-[#79563F] hover:bg-white border border-[#79563F]/20 cursor-pointer'
                : 'bg-[#FAF7F2]/60 text-[#8C7A6B] cursor-not-allowed opacity-60'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                s11Ready && currentStep !== 'step2'
                  ? 'bg-[#1B4D3E] text-white'
                  : currentStep === 'step2'
                  ? 'bg-white/20 text-white'
                  : !s10Ready
                  ? 'bg-[#FAF2E3] text-[#8C7A6B]'
                  : 'bg-[#FAF2E3] text-[#79563F]'
              }`}>
                {s11Ready && currentStep !== 'step2' ? <Check className="w-3 h-3 stroke-[3]" /> : (!s10Ready ? <Lock className="w-2.5 h-2.5" /> : '2')}
              </span>
              <span className="font-['Outfit']">02. Risk Assessment</span>
            </div>
            {s11Ready && (
              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                currentStep === 'step2' ? 'bg-white/20 text-white' : 'bg-[#EAF5EE] text-[#1B4D3E]'
              }`}>
                {formatEnumLabel(stage11Data?.overall_risk_severity || 'Evaluated')}
              </span>
            )}
          </button>

          {/* Step 3 Pill */}
          <button
            type="button"
            disabled={!s11Ready}
            onClick={() => {
              if (s11Ready) setCurrentStep('step3');
            }}
            className={`flex-1 px-4 py-2.5 rounded-lg flex items-center justify-between gap-2 transition-all ${
              currentStep === 'step3'
                ? 'bg-[#79563F] text-[#FAF4E8] shadow-2xs cursor-pointer'
                : s12Ready
                ? 'bg-[#FAF7F2] text-[#1B4D3E] hover:bg-white border border-[#1B4D3E]/20 cursor-pointer'
                : s11Ready
                ? 'bg-[#FAF7F2] text-[#79563F] hover:bg-white border border-[#79563F]/20 cursor-pointer'
                : 'bg-[#FAF7F2]/60 text-[#8C7A6B] cursor-not-allowed opacity-60'
            }`}
          >
            <div className="flex items-center gap-2">
              <span className={`w-5 h-5 rounded-full flex items-center justify-center text-[10px] font-bold ${
                s12Ready && currentStep !== 'step3'
                  ? 'bg-[#1B4D3E] text-white'
                  : currentStep === 'step3'
                  ? 'bg-white/20 text-white'
                  : !s11Ready
                  ? 'bg-[#FAF2E3] text-[#8C7A6B]'
                  : 'bg-[#FAF2E3] text-[#79563F]'
              }`}>
                {s12Ready && currentStep !== 'step3' ? <Check className="w-3 h-3 stroke-[3]" /> : (!s11Ready ? <Lock className="w-2.5 h-2.5" /> : '3')}
              </span>
              <span className="font-['Outfit']">03. Feasibility Synthesis</span>
            </div>
            {s12Ready && (
              <span className={`text-[10px] font-mono font-bold px-1.5 py-0.2 rounded ${
                currentStep === 'step3' ? 'bg-white/20 text-white' : 'bg-[#EAF5EE] text-[#1B4D3E]'
              }`}>
                {feasibilityData?.overall_feasibility_score !== null && feasibilityData?.overall_feasibility_score !== undefined ? `${Math.round(feasibilityData.overall_feasibility_score)}/100` : 'Complete'}
              </span>
            )}
          </button>
        </div>

        {/* Loading Spinner */}
        {loading && (
          <div className="royal-panel rounded-2xl p-12 text-center border border-[#79563F]/15 space-y-4 bg-[#FAF7F2]">
            <RefreshCw className="w-10 h-10 text-[#79563F] animate-spin mx-auto" />
            <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
              Evaluating KALPA Feasibility Pipeline...
            </h3>
            <p className="text-xs text-[#78716C] max-w-md mx-auto">
              Analyzing entrepreneur readiness, multi-vector enterprise risk, and 4-pillar feasibility synthesis.
            </p>
          </div>
        )}

        {/* Error Alert */}
        {error && !loading && (
          <div className="p-4 rounded-xl bg-[#FAF2E3] border border-[#79563F]/30 text-[#79563F] text-xs flex items-center justify-between gap-4">
            <div className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-[#79563F] shrink-0" />
              <span>{formatDisplayValue(error)}</span>
            </div>
            <button
              onClick={fetchData}
              className="px-3 py-1.5 bg-white border border-[#79563F]/30 rounded-lg font-bold text-[#79563F] hover:bg-[#FAF7F2] transition-colors shrink-0 cursor-pointer"
            >
              Retry
            </button>
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 1: ENTREPRENEUR CAPABILITY & READINESS                                */}
        {/* ========================================================================= */}
        {currentStep === 'step1' && !loading && stage10Data && (
          <div className="space-y-8 animate-fadeIn">
            {/* Step 1 Hero Card */}
            <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs relative overflow-hidden bg-[#FAF7F2]">
              <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

              <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                <div className="space-y-2">
                  <div className="flex flex-wrap items-center gap-2 mb-1">
                    <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 font-mono">
                      FEASIBILITY · STEP 1
                    </span>
                    <span
                      className={`px-3 py-1 rounded-full text-xs font-bold border flex items-center gap-1.5 ${
                        s10Ready
                          ? 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/25'
                          : 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25'
                      }`}
                    >
                      {s10Ready ? (
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#1B4D3E]" />
                      ) : (
                        <Clock className="w-3.5 h-3.5 text-[#79563F]" />
                      )}
                      {s10Ready ? 'Readiness Complete' : (pendingQuestions.length > 0 ? `${pendingQuestions.length} Clarifications Pending` : 'Evaluating Capability')}
                    </span>
                    {renderIntegrityBadge('CALCULATED')}
                    {stage10Data?.confidence !== undefined && (
                      <span className="text-xs text-stone-500 font-mono px-2 py-0.5 bg-white/70 rounded-md border border-[#79563F]/10">
                        Confidence: {Math.round((stage10Data.confidence || 1.0) * 100)}%
                      </span>
                    )}
                  </div>

                  <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                    {t('feasibility_step1_title', 'Entrepreneur Capability & Readiness')}
                  </h1>
                  <p className="text-xs sm:text-sm text-[#57534E] leading-relaxed max-w-2xl">
                    {t('feasibility_step1_desc', 'Evaluate the entrepreneur\'s skills, experience, training, resources and operational readiness for the proposed business.')}
                  </p>

                  {/* Verified Sector & Category Metadata */}
                  <div className="flex flex-wrap items-center gap-3 text-xs text-[#57534E] pt-2">
                    <span className="flex items-center gap-1.5 font-bold text-[#1C1917] bg-[#FAF2E3] px-3 py-1 rounded-lg border border-[#79563F]/18">
                      <Building2 className="w-4 h-4 text-[#79563F]" />
                      <TranslatedText text={businessTitle} />
                    </span>
                    <span className="bg-[#FAF2E3] px-2.5 py-1 rounded-md text-[#57534E] border border-[#79563F]/10 font-medium">
                      {t('overview_sector', 'Sector')}: <strong className="text-[#1C1917]"><TranslatedText text={currentSector} /></strong>
                    </span>
                    <span className="bg-[#FAF2E3] px-2.5 py-1 rounded-md text-[#57534E] border border-[#79563F]/10 font-medium">
                      {t('overview_category', 'Category')}: <strong className="text-[#1C1917]"><TranslatedText text={currentCategory} /></strong>
                    </span>
                    {currentSubcategory && (
                      <span className="bg-[#FAF2E3] px-2.5 py-1 rounded-md text-[#57534E] border border-[#79563F]/10 font-medium">
                        {t('overview_subcategory', 'Subcategory')}: <strong className="text-[#1C1917]"><TranslatedText text={currentSubcategory} /></strong>
                      </span>
                    )}
                  </div>
                </div>

                {/* Score & Calculation Trail Gauge */}
                <div className="flex flex-col sm:flex-row lg:flex-col items-center justify-center p-6 bg-[#FAF2E3] rounded-2xl border border-[#79563F]/20 text-center gap-3 shrink-0">
                  <div className="space-y-1">
                    <div className="text-4xl sm:text-5xl font-extrabold text-[#1C1917] font-['Outfit']">
                      {stage10Data?.readiness_score !== null && stage10Data?.readiness_score !== undefined
                        ? Math.round(stage10Data.readiness_score)
                        : '—'}
                      <span className="text-lg font-normal text-stone-500">/100</span>
                    </div>
                    <div className="text-xs font-bold text-[#79563F] uppercase tracking-wider">
                      {formatEnumLabel(stage10Data?.readiness_level || 'Evaluated')} {t('score', 'Readiness')}
                    </div>
                  </div>

                  <button
                    type="button"
                    onClick={() => setIsStage10DrawerOpen(true)}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/80 hover:bg-white text-[#79563F] border border-[#79563F]/20 text-xs font-bold transition shadow-2xs cursor-pointer"
                  >
                    <Calculator className="w-3.5 h-3.5 text-[#79563F]" />
                    <span>{t('feasibility_calc_trail', 'View Calculation Trail')}</span>
                  </button>
                </div>
              </div>

              {/* Dedicated Lower Forward Navigation Area */}
              <div className="mt-6 pt-4 border-t border-[#79563F]/12 flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
                <div className="flex items-center gap-2 text-xs text-[#57534E]">
                  <span className="font-bold text-[#1C1917]">{t('status', 'Workflow State')}:</span>
                  <span>
                    {s10Ready
                      ? t('feas_step1_complete_desc', 'Readiness validated · Continue to Step 2 Enterprise Risk Assessment')
                      : t('feas_step1_pending_desc', 'Complete pending clarifications below to finalize capability scoring')}
                  </span>
                </div>

                {s10Ready && (
                  <button
                    type="button"
                    onClick={() => setCurrentStep('step2')}
                    className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02] shrink-0 self-end sm:self-auto"
                  >
                    <span>{t('feasibility_continue_risk', 'Continue to Risk Assessment')}</span>
                    <ArrowRight className="w-3.5 h-3.5" />
                  </button>
                )}
              </div>
            </div>

            {/* Targeted Clarification Module */}
            {pendingQuestions.length > 0 && (
              <div className="royal-panel rounded-2xl p-6 sm:p-7 border border-[#79563F]/25 bg-[#FAF2E3]/95 shadow-xs space-y-4 animate-fadeIn">
                <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#79563F]/15 pb-3">
                  <div className="flex items-center gap-2.5">
                    <span className="p-2 rounded-xl bg-[#79563F] text-white shadow-xs">
                      <Sparkles className="w-4 h-4" />
                    </span>
                    <div>
                      <span className="text-[10px] font-black uppercase tracking-wider text-[#79563F] bg-[#79563F]/10 px-2 py-0.5 rounded-full font-mono">
                        Action Required · {pendingQuestions.length} Pending {pendingQuestions.length === 1 ? 'Clarification' : 'Clarifications'}
                      </span>
                      <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] mt-0.5">
                        Targeted Entrepreneur Clarification
                      </h3>
                    </div>
                  </div>
                  <span className="text-[11px] text-stone-500 font-medium italic">
                    KALPA No Fake Data Policy · Voice & Text enabled
                  </span>
                </div>

                <p className="text-xs text-[#57534E]">
                  Please answer each pending dimension below to provide verified data for deterministic capability evaluation.
                </p>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-1">
                  {pendingQuestions.map((rawQ, idx) => {
                    const q = normalizeClarification(rawQ);
                    if (!q) return null;

                    const isSubmittingThis = submittingClarificationField === q.field;
                    const isRecThis = isRecording && activeVoiceField === q.field;

                    return (
                      <div
                        key={q.field || idx}
                        className="bg-[#FAF7F2] rounded-xl p-5 border border-[#79563F]/18 hover:border-[#79563F]/35 transition-all shadow-2xs space-y-3 flex flex-col justify-between"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider font-mono">
                              Field: {formatDisplayValue(q.field)}
                            </span>
                            <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25">
                              {formatEnumLabel(q.priority)} Priority
                            </span>
                          </div>

                          <p className="text-sm font-bold text-[#1C1917] leading-snug">
                            {formatDisplayValue(q.question)}
                          </p>

                          {q.reason && (
                            <p className="text-[11px] text-stone-600 italic leading-relaxed">
                              {formatDisplayValue(q.reason)}
                            </p>
                          )}

                          {q.benchmark && (
                            <div className="text-[10px] text-[#79563F] font-mono bg-[#FAF2E3] p-2 rounded-lg border border-[#79563F]/20 leading-tight">
                              <span className="font-bold">Benchmark: </span>
                              {formatDisplayValue(q.benchmark)}
                            </div>
                          )}

                          {q.suggested_options && q.suggested_options.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-medium text-stone-500">Quick select:</span>
                              <div className="flex flex-wrap gap-1.5">
                                {q.suggested_options.map((opt, oIdx) => (
                                  <button
                                    key={oIdx}
                                    type="button"
                                    onClick={() =>
                                      setClarificationAnswers((prev) => ({
                                        ...prev,
                                        [q.field]: opt,
                                      }))
                                    }
                                    className="text-[11px] bg-white hover:bg-[#F3E8D4] text-[#28231F] px-2.5 py-1 rounded-lg border border-[#79563F]/20 transition cursor-pointer font-medium"
                                  >
                                    {opt}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="space-y-2 pt-3 border-t border-[#79563F]/10">
                          <div className="flex items-center space-x-2">
                            <input
                              type="text"
                              value={clarificationAnswers[q.field] || ''}
                              onChange={(e) =>
                                setClarificationAnswers((prev) => ({
                                  ...prev,
                                  [q.field]: e.target.value,
                                }))
                              }
                              onKeyDown={(e) => {
                                if (e.key === 'Enter') handleAnswerSubmit(q.field);
                              }}
                              placeholder={
                                q.input_type === 'number'
                                  ? 'Enter number (e.g. 3)...'
                                  : 'Type your answer here...'
                              }
                              className="flex-1 px-3 py-2 text-xs border border-stone-300 bg-white rounded-xl focus:ring-2 focus:ring-[#79563F] focus:outline-none text-[#1C1917]"
                            />

                            <button
                              type="button"
                              onClick={() => (isRecThis ? stopRecording() : startRecording(q.field))}
                              className={`p-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                                isRecThis
                                  ? 'bg-rose-600 text-white animate-pulse'
                                  : 'bg-[#FAF2E3] hover:bg-[#F3E8D4] text-[#79563F] border border-[#79563F]/25'
                              }`}
                              title={isRecThis ? 'Stop voice recording' : 'Record voice answer'}
                            >
                              {isRecThis ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                            </button>

                            <button
                              type="button"
                              onClick={() => handleAnswerSubmit(q.field)}
                              disabled={isSubmittingThis || !clarificationAnswers[q.field]?.trim()}
                              className="px-3.5 py-2 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition disabled:opacity-40 cursor-pointer flex items-center space-x-1 shadow-2xs"
                            >
                              {isSubmittingThis ? (
                                <RefreshCw className="w-3.5 h-3.5 animate-spin" />
                              ) : (
                                <Send className="w-3.5 h-3.5" />
                              )}
                            </button>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* Five 3D Readiness Cards Matrix */}
            <div className="space-y-4">
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/12 pb-3">
                <div>
                  <h2 className="text-xl font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                    <UserCheck className="w-5 h-5 text-[#79563F]" />
                    Entrepreneur Capability & Readiness Matrix
                  </h2>
                  <p className="text-xs text-stone-600 mt-0.5">
                    Deterministic 5-dimension scoring evaluating skills, experience, training, resources, and operational readiness.
                  </p>
                </div>
                <span className="text-[11px] text-stone-500 font-mono">
                  Interactive 3D Cards · Hover to inspect
                </span>
              </div>

              {/* 5 Cards Grid */}
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
                {READINESS_DIMENSIONS.map((dim) => {
                  const comp =
                    stage10Data.component_scores?.[dim.key] ||
                    stage10Data.component_scores?.[dim.altKey] ||
                    {};

                  const isExpanded = expandedComponent === dim.key;
                  const weightVal = comp.weight !== undefined ? comp.weight : dim.defaultWeight;
                  const weightPct = Math.round(weightVal * 100);
                  const scoreVal = comp.score !== null && comp.score !== undefined ? Math.round(comp.score) : null;
                  const statusLabel = comp.status || 'ADEQUATE';

                  return (
                    <Kalpa3DCard key={dim.key} containerClassName="h-full">
                      <div className="royal-card bg-[#FAF7F2] rounded-2xl border border-[#79563F]/18 p-5 flex flex-col justify-between h-full shadow-2xs hover:shadow-md transition-shadow">
                        <div className="space-y-3">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-black tracking-wider text-[#79563F]/80 uppercase font-mono bg-[#FAF2E3] px-2 py-0.5 rounded border border-[#79563F]/15">
                              {weightPct}% WEIGHT
                            </span>
                            <span
                              className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                                statusLabel === 'STRONG' || statusLabel === 'PASS' || statusLabel === 'LOW'
                                  ? 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/25'
                                  : statusLabel === 'ADEQUATE'
                                  ? 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25'
                                  : 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25'
                              }`}
                            >
                              {formatEnumLabel(statusLabel)}
                            </span>
                          </div>

                          <div className="flex items-center gap-2">
                            <div className="p-1.5 rounded-lg bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/15">
                              <dim.icon className="w-4 h-4" />
                            </div>
                            <h4 className="text-sm font-bold text-[#1C1917] font-['Outfit']">
                              {dim.title}
                            </h4>
                          </div>

                          <div className="flex items-baseline space-x-1">
                            <span className="text-3xl font-extrabold text-[#1C1917] font-['Outfit']">
                              {scoreVal !== null ? scoreVal : '—'}
                            </span>
                            <span className="text-xs text-stone-500 font-medium">/100</span>
                          </div>

                          <div className="pt-0.5">
                            {renderIntegrityBadge(comp.evidence_source || comp.source)}
                          </div>
                        </div>

                        <div className="pt-3 mt-3 border-t border-[#79563F]/10">
                          <button
                            type="button"
                            onClick={() => setExpandedComponent(isExpanded ? null : dim.key)}
                            className="w-full text-left text-[11px] font-bold text-[#79563F] hover:text-[#5C3F2D] flex items-center justify-between py-1 transition cursor-pointer"
                          >
                            <span>{isExpanded ? 'Hide Details' : 'View Breakdown'}</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>
                    </Kalpa3DCard>
                  );
                })}
              </div>

              {/* Expanded Dimension Deep Dive Panel */}
              {expandedComponent && (() => {
                const activeDim = READINESS_DIMENSIONS.find((d) => d.key === expandedComponent);
                const comp =
                  stage10Data.component_scores?.[activeDim?.key] ||
                  stage10Data.component_scores?.[activeDim?.altKey] ||
                  {};

                if (!activeDim) return null;

                return (
                  <div className="royal-panel rounded-2xl border border-[#79563F]/25 bg-[#FAF7F2] p-6 shadow-xs space-y-4 animate-fadeIn">
                    <div className="flex items-center justify-between border-b border-[#79563F]/12 pb-3">
                      <div className="flex items-center space-x-3">
                        <div className="p-2 rounded-xl bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20">
                          <activeDim.icon className="w-5 h-5" />
                        </div>
                        <div>
                          <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                            {activeDim.title} Dimension Breakdown
                          </h3>
                          <p className="text-xs text-stone-600">{activeDim.description}</p>
                        </div>
                      </div>
                      <button
                        type="button"
                        onClick={() => setExpandedComponent(null)}
                        className="text-xs text-stone-500 hover:text-[#1C1917] cursor-pointer"
                      >
                        Close Breakdown
                      </button>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                      <div className="p-4 bg-[#FAF2E3] rounded-xl space-y-2 border border-[#79563F]/15">
                        <span className="font-bold text-[#79563F] font-mono text-[11px] uppercase tracking-wider block">
                          Calculation & Evidence
                        </span>
                        {comp.calculation && (
                          <div className="text-[#1C1917] font-mono text-[11px] leading-relaxed bg-white/70 p-2.5 rounded-lg border border-[#79563F]/10">
                            {formatDisplayValue(comp.calculation)}
                          </div>
                        )}
                        {comp.evidence && (
                          <div className="text-stone-700 pt-1">
                            <strong className="text-[#1C1917]">Evidence Grounding:</strong> {formatDisplayValue(comp.evidence)}
                          </div>
                        )}
                      </div>

                      <div className="p-4 bg-[#FAF2E3] rounded-xl space-y-2 border border-[#79563F]/15">
                        <span className="font-bold text-[#79563F] font-mono text-[11px] uppercase tracking-wider block">
                          Ontology Benchmark & Requirements
                        </span>
                        {comp.benchmark_requirement && (
                          <div className="text-stone-700">
                            <strong className="text-[#1C1917]">Required Standard:</strong> {formatDisplayValue(comp.benchmark_requirement)}
                          </div>
                        )}
                        {comp.matched_requirements && comp.matched_requirements.length > 0 && (
                          <div className="text-[#1B4D3E] text-[11px]">
                            <strong>Matched Standards:</strong> {formatDisplayValue(comp.matched_requirements)}
                          </div>
                        )}
                        {comp.missing_requirements && comp.missing_requirements.length > 0 && (
                          <div className="text-[#79563F] text-[11px]">
                            <strong>Identified Gaps:</strong> {formatDisplayValue(comp.missing_requirements)}
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                );
              })()}
            </div>

            {/* Targeted Support Programs */}
            {stage10Data.required_support && stage10Data.required_support.length > 0 && (
              <div className="royal-panel rounded-2xl p-6 sm:p-7 border border-[#79563F]/18 bg-[#FAF7F2] space-y-4 shadow-xs">
                <div className="flex items-center justify-between border-b border-[#79563F]/12 pb-3">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-[#FAF2E3] text-[#79563F] flex items-center justify-center font-bold border border-[#79563F]/20">
                      <Award className="w-5 h-5" />
                    </div>
                    <div>
                      <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                        Targeted Support Programs (Capability Interventions)
                      </h3>
                      <p className="text-xs text-stone-600">
                        Curated institutional schemes and training programs matched to close identified capability gaps.
                      </p>
                    </div>
                  </div>
                  <span className="text-xs font-bold text-[#79563F] bg-[#FAF2E3] px-3 py-1 rounded-full border border-[#79563F]/25 font-mono">
                    {stage10Data.required_support.length} Interventions
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                  {stage10Data.required_support.map((sup, idx) => (
                    <div
                      key={idx}
                      className="bg-[#FAF2E3] rounded-xl p-5 border border-[#79563F]/15 flex flex-col justify-between space-y-3 shadow-2xs"
                    >
                      <div className="space-y-2">
                        <div className="flex items-center justify-between">
                          <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-white text-[#79563F] border border-[#79563F]/20 uppercase font-mono">
                            {formatEnumLabel(sup.priority || 'MEDIUM')} PRIORITY
                          </span>
                          <span className="text-[10px] text-stone-500 font-medium">
                            {formatEnumLabel(sup.resource_type || 'COURSE')}
                          </span>
                        </div>
                        <h4 className="text-sm font-bold text-[#1C1917] font-['Outfit']">
                          {formatDisplayValue(sup.resource_title || sup.gap)}
                        </h4>
                        <p className="text-[11px] text-stone-600 leading-relaxed">
                          {formatDisplayValue(sup.recommended_action || sup.description)}
                        </p>
                        <div className="text-[10px] text-stone-500 font-mono">
                          Provider: <strong className="text-[#1C1917]">{formatDisplayValue(sup.provider || 'Institutional Portal')}</strong>
                        </div>
                      </div>

                      {sup.official_url ? (
                        <a
                          href={sup.official_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center justify-center w-full px-3 py-2 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition shadow-2xs cursor-pointer"
                        >
                          Open Official Scheme Portal <ExternalLink className="w-3.5 h-3.5 ml-1.5" />
                        </a>
                      ) : (
                        <div className="text-center text-[11px] text-stone-500 py-1 font-medium bg-white/60 rounded-lg border border-[#79563F]/10">
                          Verified Institutional Module
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Step 1 Completion Banner -> Routes to Step 2 (Risk Assessment) */}
            {s10Ready && (
              <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#1B4D3E]/30 bg-[#EAF5EE]/60 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xs animate-fadeIn">
                <div className="space-y-2">
                  <div className="flex items-center space-x-2">
                    <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#1B4D3E] text-white">
                      READINESS VALIDATED
                    </span>
                    <span className="text-xs font-bold text-[#1B4D3E]">
                      Step 1 Assessment Complete
                    </span>
                  </div>
                  <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
                    Entrepreneur Capability Verified
                  </h3>
                  <p className="text-xs text-[#57534E] max-w-2xl leading-relaxed">
                    Readiness assessment complete. Continue to Enterprise Risk Assessment.
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0">
                  <button
                    type="button"
                    onClick={() => setCurrentStep('step2')}
                    className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm cursor-pointer transition-all hover:scale-[1.02]"
                  >
                    <span>Continue to Risk Assessment</span>
                    <ArrowRight className="w-4 h-4" />
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 2: ENTERPRISE RISK ASSESSMENT                                         */}
        {/* ========================================================================= */}
        {currentStep === 'step2' && !loading && (
          <div className="space-y-8 animate-fadeIn">
            {!s10Ready ? (
              <StageLockedNotice
                stepNum={2}
                stepName="Enterprise Risk Assessment"
                reason="Step 2 evaluates 7 business-specific risk categories using your verified skills, experience, and resources from Step 1. Complete pending clarifications first."
                unlockAction="Complete Entrepreneur Readiness (Step 1)"
                onUnlockClick={() => setCurrentStep('step1')}
              />
            ) : stage11Data ? (
              <>
                {/* Step 2 Hero Card */}
                <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs relative overflow-hidden bg-[#FAF7F2]">
                  <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 font-mono">
                          FEASIBILITY · STEP 2
                        </span>
                        {getSeverityBadge(stage11Data.overall_risk_severity)}
                        {renderIntegrityBadge('CALCULATED')}
                        <span className="text-xs text-stone-500 font-mono px-2 py-0.5 bg-white/70 rounded-md border border-[#79563F]/10">
                          Confidence: {Math.round((stage11Data.confidence || 1.0) * 100)}%
                        </span>
                      </div>

                      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                        {t('feasibility_step2_title', 'Enterprise 7-Category Risk Matrix')}
                      </h1>
                      <p className="text-xs sm:text-sm text-[#57534E] leading-relaxed max-w-2xl">
                        {t('feasibility_step2_desc', 'Deterministic multi-vector risk synthesis consuming financial break-even, market competition, capability gaps, and operational seasonality.')}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-[#57534E] pt-2">
                        <span className="flex items-center gap-1.5 font-bold text-[#1C1917] bg-[#FAF2E3] px-3 py-1 rounded-lg border border-[#79563F]/18">
                          <Building2 className="w-4 h-4 text-[#79563F]" />
                          <TranslatedText text={businessTitle} />
                        </span>
                        <span className="bg-[#FAF2E3] px-2.5 py-1 rounded-md text-[#57534E] border border-[#79563F]/10 font-medium">
                          {t('feas_critical_gaps', 'Critical Gaps')}: <strong className="text-[#1C1917]">{stage11Data.critical_risks_count || 0}</strong>
                        </span>
                      </div>
                    </div>

                    {/* Risk Score & Provenance Action */}
                    <div className="flex flex-col sm:flex-row lg:flex-col items-center justify-center p-6 bg-[#FAF2E3] rounded-2xl border border-[#79563F]/20 text-center gap-3 shrink-0">
                      <div className="space-y-1">
                        <div className="text-4xl sm:text-5xl font-extrabold text-[#1C1917] font-['Outfit']">
                          {stage11Data.overall_risk_score !== null && stage11Data.overall_risk_score !== undefined
                            ? stage11Data.overall_risk_score.toFixed(2)
                            : '—'}
                          <span className="text-lg font-normal text-stone-500">/1.0</span>
                        </div>
                        <div className="text-xs font-bold text-[#79563F] uppercase tracking-wider">
                          {formatEnumLabel(stage11Data.overall_risk_severity)} {t('feas_enterprise_risk', 'Enterprise Risk')}
                        </div>
                      </div>

                      <button
                        type="button"
                        onClick={() => setIsStage11DrawerOpen(true)}
                        className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/80 hover:bg-white text-[#79563F] border border-[#79563F]/20 text-xs font-bold transition shadow-2xs cursor-pointer"
                      >
                        <Calculator className="w-3.5 h-3.5 text-[#79563F]" />
                        <span>{t('feas_step2_trail', 'View Risk Calculation Trail')}</span>
                      </button>
                    </div>
                  </div>

                  {/* Dedicated Lower Forward Navigation Area */}
                  <div className="mt-6 pt-4 border-t border-[#79563F]/12 flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
                    <div className="flex items-center gap-2 text-xs text-[#57534E]">
                      <span className="font-bold text-[#1C1917]">{t('status', 'Workflow State')}:</span>
                      <span>
                        {s11Ready
                          ? t('feas_step2_complete_desc', 'Enterprise risk evaluated across 7 categories · Continue to Step 3 Feasibility Synthesis')
                          : t('feas_step2_evaluating', 'Evaluating category risk severity models')}
                      </span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setCurrentStep('step1')}
                        className="px-4 py-2.5 rounded-xl border border-[#79563F]/20 bg-[#FAF7F2] hover:bg-[#F3E8D4] text-xs font-bold text-[#28231F] shadow-2xs cursor-pointer"
                      >
                        ← {t('back', 'Back to Step 1')}
                      </button>
                      <button
                        type="button"
                        disabled={!s11Ready}
                        onClick={() => setCurrentStep('step3')}
                        className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
                      >
                        <span>{t('feas_continue_synthesis', 'Continue to Feasibility Synthesis')}</span>
                        <ArrowRight className="w-3.5 h-3.5" />
                      </button>
                    </div>
                  </div>
                </div>

                {/* 7 Risk Categories Matrix */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between border-b border-[#79563F]/12 pb-3">
                    <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                      {t('feas_7_risk_breakdown', 'Multi-Vector Risk Breakdown (7 Operational Vectors)')}
                    </h3>
                    <span className="text-xs text-stone-500">
                      {t('feas_click_inspect', 'Click any risk category to inspect upstream evidence & mitigation')}
                    </span>
                  </div>

                  <div className="space-y-3">
                    {stage11Data.category_risks &&
                      Object.entries(stage11Data.category_risks).map(([catKey, risk]) => {
                        const isExpanded = expandedRisk === catKey;
                        const weightPct = stage11Data.weights?.[catKey.toLowerCase()]
                          ? Math.round(stage11Data.weights[catKey.toLowerCase()] * 100)
                          : null;

                        const isDataGap = risk.status === 'DATA_GAP' || risk.source_stage === 'UNKNOWN' || risk.score === null;

                        return (
                          <div
                            key={catKey}
                            className={`bg-[#FAF7F2] rounded-2xl border transition shadow-2xs overflow-hidden ${
                              isExpanded ? 'border-[#79563F] ring-1 ring-[#79563F]/20' : 'border-[#79563F]/18'
                            }`}
                          >
                            <button
                              type="button"
                              onClick={() => setExpandedRisk(isExpanded ? null : catKey)}
                              className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-[#FAF2E3]/60 transition cursor-pointer"
                            >
                              <div className="flex items-center space-x-3">
                                <div className="w-9 h-9 rounded-xl bg-[#FAF2E3] border border-[#79563F]/18 flex items-center justify-center text-[#79563F] font-bold text-xs font-mono">
                                  {catKey.slice(0, 3).toUpperCase()}
                                </div>
                                <div>
                                  <div className="text-sm font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                                    <TranslatedText text={`${catKey.replace(/_/g, ' ')} RISK`} />
                                    {weightPct !== null && (
                                      <span className="text-[10px] font-normal text-stone-500 font-mono">
                                        ({weightPct}% {t('weight', 'weight')})
                                      </span>
                                    )}
                                  </div>
                                  <div className="text-[11px] text-stone-500 font-mono">
                                    {t('source', 'Source')}: {formatEnumLabel(risk.source_stage)}
                                  </div>
                                </div>
                              </div>

                              <div className="flex items-center space-x-4">
                                <span className="text-sm font-extrabold text-[#1C1917] font-mono">
                                  {typeof risk.score === 'number' ? risk.score.toFixed(2) : (risk.score || '—')}
                                </span>
                                {getSeverityBadge(isDataGap ? 'DATA_GAP' : (risk.level || risk.severity))}
                                {isExpanded ? <ChevronUp className="w-4 h-4 text-stone-400" /> : <ChevronDown className="w-4 h-4 text-stone-400" />}
                              </div>
                            </button>

                            {isExpanded && (
                              <div className="px-5 pb-5 pt-3 border-t border-[#79563F]/10 bg-[#FAF2E3]/40 space-y-3 text-xs">
                                {risk.evidence && (
                                  <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                                    <strong className="text-[#1C1917]">{t('upstream_evidence', 'Upstream Evidence')}:</strong> <TranslatedText text={formatDisplayValue(risk.evidence)} />
                                  </div>
                                )}
                                {risk.benchmark && (
                                  <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                                    <strong className="text-[#1C1917]">{t('ontology_benchmark', 'Ontology Benchmark')}:</strong> <TranslatedText text={formatDisplayValue(risk.benchmark)} />
                                  </div>
                                )}
                                <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                                  <strong className="text-[#1C1917]">{t('deterministic_formula', 'Deterministic Formula')}:</strong> {formatDisplayValue(risk.formula || risk.calculation)}
                                </div>
                                {risk.impact && (
                                  <div className="p-3 bg-white rounded-xl border border-[#79563F]/15">
                                    <strong className="text-[#1C1917]">{t('business_impact', 'Business Impact')}:</strong> <TranslatedText text={formatDisplayValue(risk.impact || risk.business_impact)} />
                                  </div>
                                )}
                                {risk.mitigation && (
                                  <div className="p-3 bg-[#EAF5EE] rounded-xl border border-[#1B4D3E]/25 text-[#1C1917]">
                                    <strong className="text-[#1B4D3E]">{t('actionable_mitigation', 'Actionable Mitigation')}:</strong> <TranslatedText text={formatDisplayValue(risk.mitigation)} />
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                        );
                      })}
                  </div>
                </div>

                {/* Step 2 Completion Banner -> Routes to Step 3 (Feasibility Synthesis) */}
                {s11Ready && (
                  <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#1B4D3E]/30 bg-[#EAF5EE]/60 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xs animate-fadeIn">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#1B4D3E] text-white">
                          {t('risk_synthesis_complete', 'RISK SYNTHESIS COMPLETE')}
                        </span>
                        <span className="text-xs font-bold text-[#1B4D3E]">
                          {t('step2_complete', 'Step 2 Assessment Complete')}
                        </span>
                      </div>
                      <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
                        {t('feas_risk_complete_title', 'Enterprise Risk Analysis Complete')}
                      </h3>
                      <p className="text-xs text-[#57534E] max-w-2xl leading-relaxed">
                        {t('feas_risk_complete_desc', 'Risk synthesis evaluated across all 7 operational categories. Continue to Feasibility Synthesis.')}
                      </p>
                    </div>

                    <div className="flex items-center gap-3 shrink-0">
                      <button
                        type="button"
                        onClick={() => setCurrentStep('step3')}
                        className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm cursor-pointer transition-all hover:scale-[1.02]"
                      >
                        <span>{t('feas_continue_synthesis', 'Continue to Feasibility Synthesis')}</span>
                        <ArrowRight className="w-4 h-4" />
                      </button>
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}

        {/* ========================================================================= */}
        {/* STEP 3: MASTER FEASIBILITY SYNTHESIS                                       */}
        {/* ========================================================================= */}
        {currentStep === 'step3' && !loading && (
          <div className="space-y-8 animate-fadeIn">
            {!s10Ready ? (
              <StageLockedNotice
                stepNum={3}
                stepName={t('feas_master_engine', 'Master Feasibility Engine')}
                reason={t('feas_step1_req', 'Feasibility Synthesis requires verified Entrepreneur Profile readiness. Please complete Step 1 first.')}
                unlockAction={t('go_step1', 'Go to Step 1 Readiness')}
                onUnlockClick={() => setCurrentStep('step1')}
              />
            ) : !s11Ready ? (
              <StageLockedNotice
                stepNum={3}
                stepName={t('feas_master_engine', 'Master Feasibility Engine')}
                reason={t('feas_step2_req', 'Feasibility Synthesis combines Opportunity, Finance, Readiness, and Risk. Step 2 Risk Analysis must be completed first.')}
                unlockAction={t('evaluate_step2', 'Evaluate Step 2 Risk Engine')}
                onUnlockClick={() => setCurrentStep('step2')}
              />
            ) : feasibilityData ? (
              <>
                {/* Step 3 Hero Card */}
                <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs relative overflow-hidden bg-[#FAF7F2]">
                  <div className="absolute top-0 right-0 w-80 h-80 bg-gradient-to-bl from-orange-100/50 via-amber-50/30 to-transparent rounded-bl-full pointer-events-none" />

                  <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
                    <div className="space-y-2">
                      <div className="flex flex-wrap items-center gap-2 mb-1">
                        <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 font-mono">
                          FEASIBILITY · STEP 3
                        </span>
                        {getFeasibilityDecisionBadge(feasibilityData.decision)}
                        {renderIntegrityBadge('CALCULATED')}
                        <span className="text-xs text-stone-500 font-mono px-2 py-0.5 bg-white/70 rounded-md border border-[#79563F]/10">
                          Confidence: {Math.round((feasibilityData.confidence_score || 1.0) * 100)}%
                        </span>
                      </div>

                      <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
                        {t('feasibility_step3_title', 'Master Feasibility Synthesis')}
                      </h1>
                      <p className="text-xs sm:text-sm text-[#57534E] leading-relaxed max-w-2xl">
                        {t('feasibility_step3_desc', 'Weighted synthesis of market, finance, readiness, and risk.')}
                      </p>

                      <div className="flex flex-wrap items-center gap-3 text-xs text-[#57534E] pt-2">
                        <span className="flex items-center gap-1.5 font-bold text-[#1C1917] bg-[#FAF2E3] px-3 py-1 rounded-lg border border-[#79563F]/18">
                          <Building2 className="w-4 h-4 text-[#79563F]" />
                          <TranslatedText text={businessTitle} />
                        </span>
                        <span className="bg-[#FAF2E3] px-2.5 py-1 rounded-md text-[#57534E] border border-[#79563F]/10 font-medium">
                          {t('recommendations', 'Recommendation')}: <strong className="text-[#1C1917]"><TranslatedText text={formatDisplayValue(feasibilityData.recommendation)} /></strong>
                        </span>
                      </div>
                    </div>

                    {/* Central Feasibility Score Gauge */}
                    <div className="flex flex-col sm:flex-row lg:flex-col items-center justify-center p-6 bg-[#FAF2E3] rounded-2xl border border-[#79563F]/20 text-center gap-3 shrink-0">
                      <div className="space-y-1">
                        <div className="text-4xl sm:text-5xl font-extrabold text-[#1C1917] font-['Outfit']">
                          {Math.round(feasibilityData.overall_feasibility_score)}
                          <span className="text-lg font-normal text-stone-500">/100</span>
                        </div>
                        <div className="text-xs font-bold text-[#79563F] uppercase tracking-wider">
                          {t('feasibility_score', 'Composite Feasibility Score')}
                        </div>
                      </div>

                      <div className="flex flex-col gap-1.5 w-full">
                        <button
                          type="button"
                          onClick={() => setIsStage12DrawerOpen(true)}
                          className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-white/80 hover:bg-white text-[#79563F] border border-[#79563F]/20 text-xs font-bold transition shadow-2xs cursor-pointer"
                        >
                          <Calculator className="w-3.5 h-3.5 text-[#79563F]" />
                          <span>{t('feas_decision_calc', 'View Decision Calculation')}</span>
                        </button>
                        {feasibilityData.dynamic_swot && (
                          <button
                            type="button"
                            onClick={() => setIsSWOTModalOpen(true)}
                            className="inline-flex items-center justify-center gap-1.5 px-3 py-1.5 rounded-lg bg-[#EAF5EE] hover:bg-[#D9EFE0] text-[#1B4D3E] border border-[#1B4D3E]/20 text-xs font-bold transition shadow-2xs cursor-pointer"
                          >
                            <BarChart3 className="w-3.5 h-3.5 text-[#1B4D3E]" />
                            <span>{t('feas_preview_swot', 'Preview SWOT Matrix')}</span>
                          </button>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Dedicated Lower Forward Navigation Area */}
                  <div className="mt-6 pt-4 border-t border-[#79563F]/12 flex flex-col sm:flex-row sm:items-center justify-between gap-4 relative z-10">
                    <div className="flex items-center gap-2 text-xs text-[#57534E]">
                      <span className="font-bold text-[#1C1917]">{t('status', 'Workflow State')}:</span>
                      <span>{t('feas_4_pillars_eval', 'Complete · 4 pillars evaluated')}</span>
                    </div>

                    <div className="flex items-center gap-2">
                      <button
                        type="button"
                        onClick={() => setCurrentStep('step2')}
                        className="px-4 py-2.5 rounded-xl border border-[#79563F]/20 bg-[#FAF7F2] hover:bg-[#F3E8D4] text-xs font-bold text-[#28231F] shadow-2xs cursor-pointer"
                      >
                        ← {t('back', 'Back to Step 2')}
                      </button>
                      <Link
                        to="/swot"
                        state={{
                          analysisId: effectiveAnalysisId,
                          sessionId: effectiveSessionId,
                          feasibilityResult: feasibilityData,
                          businessProfile: { specific_business: businessTitle },
                          entrepreneurReadiness: stage10Data,
                          riskAnalysis: stage11Data,
                          financialAnalysis: (sessionStorage.getItem('kalpa_financial_analysis') ? JSON.parse(sessionStorage.getItem('kalpa_financial_analysis')) : undefined),
                          financialContext: (sessionStorage.getItem('kalpa_financial_context') ? JSON.parse(sessionStorage.getItem('kalpa_financial_context')) : undefined)
                        }}
                      >
                        <button
                          type="button"
                          className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
                        >
                          <span>{t('proceed_to_swot', 'Continue to SWOT')}</span>
                          <ArrowRight className="w-3.5 h-3.5" />
                        </button>
                      </Link>
                    </div>
                  </div>
                </div>

                {/* 4 Core Analytical Pillars Grid with 3D Score Cards */}
                <div className="space-y-4">
                  <div className="flex items-center justify-between border-b border-[#79563F]/12 pb-3">
                    <div>
                      <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                        Four Analytical Pillars (Weighted Synthesis)
                      </h3>
                      <p className="text-xs text-stone-600 mt-0.5">
                        Select a pillar to inspect details.
                      </p>
                    </div>
                    <span className="text-[11px] text-stone-500 font-mono">
                      Weighted Synthesis · Hover to inspect
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
                    {FEASIBILITY_PILLARS.map((pDef) => {
                      const backendPillar = feasibilityData.pillar_scores?.[pDef.key] || {};
                      const title = backendPillar.title || pDef.title;
                      const score = backendPillar.score !== undefined && backendPillar.score !== null ? Math.round(backendPillar.score) : pDef.defaultScore;
                      const weight = backendPillar.weight !== undefined && backendPillar.weight !== null ? Math.round(backendPillar.weight * (backendPillar.weight <= 1 ? 100 : 1)) : pDef.defaultWeight;
                      const contribution = backendPillar.weighted_contribution !== undefined && backendPillar.weighted_contribution !== null ? Number(backendPillar.weighted_contribution).toFixed(1) : pDef.defaultContribution;
                      const status = backendPillar.status || pDef.defaultStatus;
                      const sourceStage = backendPillar.source_stage || pDef.sourceStage;
                      const confidence = backendPillar.confidence !== undefined ? backendPillar.confidence : 1.0;
                      const isExpanded = expandedPillar === pDef.key;

                      return (
                        <FeasibilityScoreCard
                          key={pDef.key}
                          title={title}
                          score={score}
                          weight={weight}
                          contribution={contribution}
                          status={status}
                          sourceStage={sourceStage}
                          confidence={confidence}
                          isExpanded={isExpanded}
                          onToggleExpand={() => setExpandedPillar(isExpanded ? null : pDef.key)}
                        />
                      );
                    })}
                  </div>

                  {/* Expanded Pillar Deep Dive View */}
                  {expandedPillar && (() => {
                    const pDef = FEASIBILITY_PILLARS.find((p) => p.key === expandedPillar);
                    const pil = feasibilityData.pillar_scores?.[expandedPillar] || pDef || {};
                    return (
                      <div className="royal-panel rounded-2xl border border-[#79563F]/25 bg-[#FAF7F2] p-6 shadow-xs space-y-4 animate-fadeIn">
                        <div className="flex items-center justify-between border-b border-[#79563F]/12 pb-3">
                          <div className="flex items-center space-x-2">
                            <span className="text-sm font-bold text-[#1C1917] font-['Outfit']">
                              {formatDisplayValue(pil.title || pDef?.title)} Formula & Inputs Breakdown
                            </span>
                            {renderIntegrityBadge(pil.source_stage || pDef?.sourceStage)}
                            <span className="text-xs text-stone-500 font-mono">
                              Weight: {Math.round((pil.weight || (pDef?.defaultWeight ? pDef.defaultWeight / 100 : 0.25)) * 100)}% (+{pil.weighted_contribution || pDef?.defaultContribution} pts)
                            </span>
                          </div>
                          <button
                            type="button"
                            onClick={() => setExpandedPillar(null)}
                            className="text-xs text-stone-500 hover:text-[#1C1917] cursor-pointer"
                          >
                            Close Breakdown
                          </button>
                        </div>

                        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                          <div className="p-4 bg-[#FAF2E3] rounded-xl space-y-2 border border-[#79563F]/15">
                            <span className="font-bold text-[#79563F] font-mono text-[11px] uppercase tracking-wider block">
                              Calculation Formula:
                            </span>
                            <div className="text-[#1C1917] font-mono text-[11px] leading-relaxed bg-white/70 p-2.5 rounded-lg border border-[#79563F]/10">
                              {formatDisplayValue(pil.calculation || `Pillar Score (${pil.score || pDef?.defaultScore}/100) × Weight (${pDef?.defaultWeight}%)`)}
                            </div>
                          </div>
                          <div className="p-4 bg-[#FAF2E3] rounded-xl space-y-2 border border-[#79563F]/15">
                            <span className="font-bold text-[#79563F] font-mono text-[11px] uppercase tracking-wider block">
                              Key Inputs & Provenance:
                            </span>
                            {pil.inputs && Object.keys(pil.inputs).length > 0 ? (
                              <ul className="space-y-1 text-stone-700">
                                {Object.entries(pil.inputs).map(([ik, iv]) => (
                                  <li key={ik} className="flex justify-between font-mono text-[11px] bg-white/50 px-2 py-1 rounded">
                                    <span className="text-stone-500">{ik}:</span>
                                    <span className="font-bold text-[#1C1917]">{formatDisplayValue(iv)}</span>
                                  </li>
                                ))}
                              </ul>
                            ) : (
                              <div className="text-stone-600 text-[11px] font-mono bg-white/50 p-2.5 rounded">
                                Grounded on upstream {formatEnumLabel(pil.source_stage || pDef?.sourceStage)} verified indicators.
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>

                {/* YES / NO Action Pathway */}
                {feasibilityData.recommendation === 'YES' || feasibilityData.decision === 'VIABLE' || feasibilityData.decision === 'VIABLE_WITH_CAUTION' ? (
                  <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#1B4D3E]/30 bg-[#EAF5EE]/60 flex flex-col md:flex-row items-center justify-between gap-6 shadow-xs animate-fadeIn">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#1B4D3E] text-white">
                          YES PATHWAY UNLOCKED
                        </span>
                        <span className="text-xs font-bold text-[#1B4D3E]">
                          Stage 13 Dynamic Strategic SWOT Ready
                        </span>
                      </div>
                      <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
                        Venture Feasibility Verified — Proceed to Stage 13 SWOT
                      </h3>
                      <p className="text-xs text-[#57534E] max-w-2xl leading-relaxed">
                        Your enterprise metrics satisfy viability thresholds. Stage 13 Dynamic SWOT Agent will synthesize cross-engine findings across Market Intelligence, Financial Model, Capability, and Risk into an evidence-grounded SWOT matrix.
                      </p>
                    </div>

                    <div className="flex flex-wrap items-center gap-3 shrink-0">
                      {feasibilityData?.dynamic_swot && (
                        <button
                          type="button"
                          onClick={() => setIsSWOTModalOpen(true)}
                          className="px-4 py-2.5 bg-white hover:bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 rounded-xl text-xs font-bold transition shadow-2xs cursor-pointer"
                        >
                          Quick Matrix Preview
                        </button>
                      )}
                      <Link
                        to="/swot"
                        state={{
                          analysisId: effectiveAnalysisId,
                          sessionId: effectiveSessionId,
                          feasibilityResult: feasibilityData,
                          businessProfile: { specific_business: businessTitle },
                          entrepreneurReadiness: stage10Data,
                          riskAnalysis: stage11Data,
                          financialAnalysis: (sessionStorage.getItem('kalpa_financial_analysis') ? JSON.parse(sessionStorage.getItem('kalpa_financial_analysis')) : undefined),
                          financialContext: (sessionStorage.getItem('kalpa_financial_context') ? JSON.parse(sessionStorage.getItem('kalpa_financial_context')) : undefined)
                        }}
                      >
                        <button
                          type="button"
                          className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-sm cursor-pointer transition-all hover:scale-[1.02]"
                        >
                          <span>Continue to Dynamic SWOT</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </Link>
                    </div>
                  </div>
                ) : (
                  /* NO / PIVOT PATHWAY */
                  <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/25 bg-[#FAF2E3] space-y-6 shadow-xs animate-fadeIn">
                    <div className="space-y-1.5">
                      <div className="flex items-center space-x-2">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-[#79563F] text-white">
                          PIVOT ADVISOR ACTIVE
                        </span>
                        <span className="text-xs font-bold text-[#79563F]">
                          Alternative Business Recommendations
                        </span>
                      </div>
                      <h3 className="text-xl font-bold text-[#1C1917] font-['Outfit']">
                        Recommended Strategic Pivot Opportunities
                      </h3>
                      <p className="text-xs text-stone-600 max-w-2xl leading-relaxed">
                        The current business configuration has critical risk or capital constraints. KALPA has matched your verified skills and available capital to feasible alternative micro-enterprises.
                      </p>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                      {feasibilityData.pivot_recommendations?.map((cand, idx) => (
                        <div
                          key={cand.business_id || idx}
                          className="bg-[#FAF7F2] rounded-xl p-5 border border-[#79563F]/18 shadow-2xs flex flex-col justify-between space-y-4 hover:border-[#79563F] transition"
                        >
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#FAF2E3] text-[#79563F] uppercase font-mono">
                                {cand.skill_fit_percentage}% Skill Fit
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-[#EAF5EE] text-[#1B4D3E]">
                                {cand.capital_fit}
                              </span>
                            </div>

                            <h4 className="text-sm font-bold text-[#1C1917] font-['Outfit'] leading-snug">
                              {cand.business_name}
                            </h4>

                            <div className="text-xs text-stone-700">
                              <strong>Capital Required:</strong> ₹{(cand.capital_requirement / 100000).toFixed(1)} Lakhs
                            </div>

                            <p className="text-xs text-stone-600 leading-relaxed">
                              {cand.pivot_reason}
                            </p>

                            <div className="pt-2 border-t border-[#79563F]/10 space-y-1">
                              <span className="text-[10px] font-bold text-stone-400 uppercase">Key Advantages:</span>
                              <ul className="space-y-1">
                                {cand.key_advantages?.slice(0, 2).map((adv, aIdx) => (
                                  <li key={aIdx} className="text-[11px] text-stone-600 flex items-start space-x-1.5">
                                    <Check className="w-3 h-3 text-[#1B4D3E] flex-shrink-0 mt-0.5" />
                                    <span>{adv}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>

                          <button
                            type="button"
                            onClick={() => handleSelectPivot(cand)}
                            className="w-full py-2.5 px-3 bg-[#79563F] hover:bg-[#5C3F2D] text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1 shadow-2xs cursor-pointer"
                          >
                            <span>Analyse This Business Idea</span>
                            <ArrowRight className="w-3.5 h-3.5 ml-1" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </>
            ) : null}
          </div>
        )}
      </div>
    </div>
  );
};

export default function FeasibilityPageWithBoundary() {
  return (
    <FeasibilityErrorBoundary>
      <FeasibilityPage />
    </FeasibilityErrorBoundary>
  );
}
