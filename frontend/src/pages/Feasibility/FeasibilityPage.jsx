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
  Flame,
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
  CheckCheck
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import Button from '../../components/ui/Button';
import CalculationBreakdown from '../../components/common/CalculationBreakdown';

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
// Clarification Item Normalizer (Standardizes Backend Contract across versions)
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
// Authoritative Stage Completion & Validity Checkers
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
// Reusable Safe Data Integrity Badge Renderer
// ---------------------------------------------------------------------------
export const renderIntegrityBadge = (sourceType) => {
  const norm = (sourceType || '').toUpperCase();
  if (norm.includes('USER') || norm === 'USER_INPUT' || norm === 'USER_VOICE' || norm === 'USER_CLARIFICATION') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-purple-100 text-purple-800 border border-purple-200">
        USER INPUT
      </span>
    );
  }
  if (norm === 'ACTUAL' || norm === 'VERIFIED') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
        ACTUAL / VERIFIED
      </span>
    );
  }
  if (norm === 'CALCULATED') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-blue-100 text-blue-800 border border-blue-200">
        CALCULATED
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
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
        BENCHMARK
      </span>
    );
  }
  if (norm === 'STAGE_6_MARKET_INTELLIGENCE' || norm === 'STAGE_6' || norm === 'STAGE_6_MARKET') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-indigo-100 text-indigo-800 border border-indigo-200">
        STAGE 6 MARKET
      </span>
    );
  }
  if (norm === 'STAGE_8_OPPORTUNITY' || norm === 'STAGE_8') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-100 text-cyan-800 border border-cyan-200">
        STAGE 8 OPPORTUNITY
      </span>
    );
  }
  if (norm === 'STAGE_9_FINANCIAL' || norm === 'STAGE_9_FINANCIAL_ANALYSIS' || norm === 'STAGE_9') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 border border-emerald-200">
        STAGE 9 FINANCE
      </span>
    );
  }
  if (norm === 'STAGE_10_ENTREPRENEUR_PROFILE' || norm === 'STAGE_10' || norm === 'STAGE_10_ENTREPRENEUR') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-orange-100 text-orange-800 border border-orange-200">
        STAGE 10 PROFILE
      </span>
    );
  }
  if (norm === 'STAGE_11_RISK' || norm === 'STAGE_11') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-amber-100 text-amber-800 border border-amber-200">
        STAGE 11 RISK
      </span>
    );
  }
  if (norm === 'PROXY' || norm === 'PROXY_DATA') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-stone-100 text-stone-700 border border-stone-200">
        PROXY DATA
      </span>
    );
  }
  if (norm === 'UNKNOWN' || norm === 'UNKNOWN_DATA_GAP' || norm === 'DATA_GAP' || norm === 'BENCHMARK_DATA_UNAVAILABLE') {
    return (
      <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-rose-100 text-rose-800 border border-rose-200 animate-pulse">
        DATA GAP
      </span>
    );
  }
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-bold bg-stone-100 text-stone-600 border border-stone-200">
      {sourceType || 'PROVENANCE'}
    </span>
  );
};

// ---------------------------------------------------------------------------
// Severity & Level Helpers
// ---------------------------------------------------------------------------
export const getSeverityBadge = (sev) => {
  const s = String(sev || '').toUpperCase();
  switch (s) {
    case 'CRITICAL':
    case 'RESTRICT':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300">
          <Flame className="w-3 h-3 mr-1 text-red-600" /> {s}
        </span>
      );
    case 'HIGH':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-300">
          <AlertTriangle className="w-3 h-3 mr-1 text-orange-600" /> HIGH
        </span>
      );
    case 'MEDIUM':
    case 'CAUTION':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">
          <Activity className="w-3 h-3 mr-1 text-amber-600" /> {s}
        </span>
      );
    case 'LOW':
    case 'PASS':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">
          <CheckCircle2 className="w-3 h-3 mr-1 text-emerald-600" /> {s}
        </span>
      );
    case 'UNKNOWN':
    case 'DATA_GAP':
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-stone-100 text-stone-700 border border-stone-300">
          DATA GAP
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-stone-100 text-stone-700 border border-stone-300">
          {sev || 'EVALUATED'}
        </span>
      );
  }
};

export const getFeasibilityDecisionBadge = (decision) => {
  const d = String(decision || '').toUpperCase();
  switch (d) {
    case 'VIABLE':
      return (
        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-extrabold bg-emerald-600 text-white shadow-md">
          <CheckCircle className="w-4 h-4 mr-1.5" /> VIABLE FOR VENTURE LAUNCH
        </span>
      );
    case 'VIABLE_WITH_CAUTION':
      return (
        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-extrabold bg-blue-600 text-white shadow-md">
          <AlertTriangle className="w-4 h-4 mr-1.5" /> VIABLE WITH OPERATIONAL CAUTION
        </span>
      );
    case 'CONDITIONALLY_VIABLE':
      return (
        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-extrabold bg-amber-500 text-white shadow-md">
          <Activity className="w-4 h-4 mr-1.5" /> CONDITIONALLY VIABLE
        </span>
      );
    case 'NOT_FEASIBLE':
      return (
        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-extrabold bg-red-600 text-white shadow-md">
          <AlertOctagon className="w-4 h-4 mr-1.5" /> NOT FEASIBLE IN CURRENT CONFIGURATION
        </span>
      );
    case 'DATA_INSUFFICIENT':
      return (
        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-extrabold bg-purple-600 text-white shadow-md animate-pulse">
          <HelpCircle className="w-4 h-4 mr-1.5" /> DATA INSUFFICIENT
        </span>
      );
    default:
      return (
        <span className="inline-flex items-center px-4 py-1.5 rounded-full text-sm font-extrabold bg-stone-700 text-white shadow-md">
          {decision || 'PENDING EVALUATION'}
        </span>
      );
  }
};

// ---------------------------------------------------------------------------
// Safe Calculation Breakdown Step Renderer
// ---------------------------------------------------------------------------
export const CalculationStepItem = ({ step, index }) => {
  if (!step) return null;

  if (typeof step === 'string') {
    return (
      <li className="flex items-start space-x-2 text-stone-300 text-xs font-mono">
        <span className="text-[#EA580C] font-bold">[{index + 1}]</span>
        <span className="leading-relaxed">{step}</span>
      </li>
    );
  }

  if (typeof step === 'object') {
    const dim = formatDisplayValue(step.dimension || step.category || `STEP ${index + 1}`);
    const weightPct = step.weight !== undefined ? (step.weight * 100).toFixed(0) : null;
    const scoreVal = step.score !== undefined ? (typeof step.score === 'number' ? Math.round(step.score) : step.score) : null;
    const contrib = step.weighted_contribution !== undefined ? Number(step.weighted_contribution).toFixed(1) : null;
    const calcText = typeof step.calculation === 'object' ? JSON.stringify(step.calculation) : (step.calculation || step.formula || '');
    const evidenceText = step.evidence ? formatDisplayValue(step.evidence) : null;
    const benchmarkText = step.benchmark || step.benchmark_requirement ? formatDisplayValue(step.benchmark || step.benchmark_requirement) : null;

    return (
      <li className="p-3.5 bg-stone-800/90 rounded-xl border border-stone-700 space-y-2 text-stone-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <span className="text-xs font-bold text-[#EA580C] uppercase font-mono tracking-wider">
              {dim}
            </span>
            {weightPct && (
              <span className="text-[10px] text-stone-400 font-mono">
                ({weightPct}% weight)
              </span>
            )}
            {step.status && (
              <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                step.status === 'STRONG' || step.status === 'LOW' || step.status === 'PASS'
                  ? 'bg-emerald-900/60 text-emerald-300'
                  : 'bg-amber-900/60 text-amber-300'
              }`}>
                {formatDisplayValue(step.status)}
              </span>
            )}
          </div>
          <div className="flex items-center space-x-2 font-mono">
            {scoreVal !== null && (
              <span className="text-sm font-bold text-white">
                {scoreVal}/100
              </span>
            )}
            {contrib !== null && (
              <span className="text-xs font-semibold text-emerald-400">
                +{contrib} pts
              </span>
            )}
          </div>
        </div>

        {calcText && (
          <div className="text-xs text-stone-300 font-mono bg-stone-950/70 p-2 rounded border border-stone-800 leading-snug">
            {calcText}
          </div>
        )}

        {evidenceText && (
          <div className="text-[11px] text-stone-400">
            <span className="text-stone-500 font-mono">Evidence: </span>{evidenceText}
          </div>
        )}

        {benchmarkText && (
          <div className="text-[11px] text-amber-400/90">
            <span className="text-stone-500 font-mono">Benchmark: </span>{benchmarkText}
          </div>
        )}

        <div className="flex items-center justify-between text-[11px] text-stone-400 pt-0.5">
          <span>Source: <strong className="text-stone-300">{formatDisplayValue(step.source || 'CALCULATED')}</strong></span>
          {step.confidence !== undefined && (
            <span>Conf: <strong className="text-stone-300">{Math.round(step.confidence * 100)}%</strong></span>
          )}
        </div>
      </li>
    );
  }

  return null;
};

// ---------------------------------------------------------------------------
// Slide-Over Full Calculation Drawer Component
// ---------------------------------------------------------------------------
export const CalculationDrawer = ({ isOpen, onClose, title, subtitle, provenanceData, type = 'stage12' }) => {
  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex justify-end bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="w-full max-w-2xl bg-stone-900 text-stone-100 h-full shadow-2xl flex flex-col justify-between border-l border-stone-800 animate-slideLeft">
        {/* Drawer Header */}
        <div className="p-6 border-b border-stone-800 flex items-center justify-between bg-stone-950">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#EA580C] text-white uppercase tracking-wider font-mono">
                {type === 'stage10' ? 'Stage 10 Provenance' : (type === 'stage11' ? 'Stage 11 Risk Trail' : 'Stage 12 Feasibility Synthesis')}
              </span>
              <span className="text-xs text-stone-400 font-mono">100% Deterministic</span>
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
              <Calculator className="w-4 h-4 text-[#EA580C]" />
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
          <span>Audit Source: KALPA Deterministic Synthesis Engine</span>
          <button
            onClick={onClose}
            className="px-4 py-2 bg-stone-800 hover:bg-stone-700 text-white rounded-lg text-xs font-bold transition cursor-pointer"
          >
            Close Audit Trail
          </button>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Dynamic SWOT Modal Viewer Component
// ---------------------------------------------------------------------------
export const DynamicSWOTModal = ({ isOpen, onClose, swot, businessTitle }) => {
  if (!isOpen || !swot) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fadeIn">
      <div className="bg-white rounded-3xl max-w-4xl w-full max-h-[90vh] overflow-y-auto shadow-2xl border border-stone-200 p-6 space-y-6 animate-scaleUp">
        <div className="flex items-center justify-between border-b border-stone-100 pb-4">
          <div className="space-y-1">
            <div className="flex items-center space-x-2">
              <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-100 text-emerald-800 uppercase font-mono">
                Evidence-Grounded SWOT
              </span>
              <span className="text-xs text-stone-500">Stage 12 Strategic Planning</span>
            </div>
            <h3 className="text-xl font-bold text-stone-900 font-['Outfit']">
              Dynamic Strategic SWOT: {businessTitle}
            </h3>
          </div>
          <button
            onClick={onClose}
            className="p-2 rounded-xl bg-stone-100 hover:bg-stone-200 text-stone-600 transition cursor-pointer"
          >
            <X className="w-5 h-5" />
          </button>
        </div>

        {/* 2x2 SWOT Matrix */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Strengths */}
          <div className="p-5 bg-emerald-50/70 border border-emerald-200 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-emerald-900 font-bold text-sm uppercase tracking-wider">
              <CheckCircle className="w-4 h-4 text-emerald-600" />
              <span>Strengths (Internal Advantages)</span>
            </div>
            <ul className="space-y-2">
              {swot.strengths?.map((s, idx) => (
                <li key={idx} className="text-xs text-emerald-950 bg-white p-3 rounded-xl border border-emerald-100 space-y-1">
                  <div className="font-bold">{formatDisplayValue(s.title || s)}</div>
                  {s.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(s.description)}</div>}
                  {s.evidence && (
                    <div className="text-[10px] text-emerald-700 italic font-mono pt-1">
                      Evidence: {formatDisplayValue(s.evidence)} ({formatDisplayValue(s.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Weaknesses */}
          <div className="p-5 bg-amber-50/70 border border-amber-200 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-amber-900 font-bold text-sm uppercase tracking-wider">
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
          <div className="p-5 bg-blue-50/70 border border-blue-200 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-blue-900 font-bold text-sm uppercase tracking-wider">
              <Compass className="w-4 h-4 text-blue-600" />
              <span>Opportunities (External Growth Vectors)</span>
            </div>
            <ul className="space-y-2">
              {swot.opportunities?.map((o, idx) => (
                <li key={idx} className="text-xs text-blue-950 bg-white p-3 rounded-xl border border-blue-100 space-y-1">
                  <div className="font-bold">{formatDisplayValue(o.title || o)}</div>
                  {o.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(o.description)}</div>}
                  {o.evidence && (
                    <div className="text-[10px] text-blue-700 italic font-mono pt-1">
                      Evidence: {formatDisplayValue(o.evidence)} ({formatDisplayValue(o.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>

          {/* Threats */}
          <div className="p-5 bg-rose-50/70 border border-rose-200 rounded-2xl space-y-3">
            <div className="flex items-center space-x-2 text-rose-900 font-bold text-sm uppercase tracking-wider">
              <Flame className="w-4 h-4 text-rose-600" />
              <span>Threats (External Risks & Stress)</span>
            </div>
            <ul className="space-y-2">
              {swot.threats?.map((t, idx) => (
                <li key={idx} className="text-xs text-rose-950 bg-white p-3 rounded-xl border border-rose-100 space-y-1">
                  <div className="font-bold">{formatDisplayValue(t.title || t)}</div>
                  {t.description && <div className="text-stone-600 text-[11px]">{formatDisplayValue(t.description)}</div>}
                  {t.evidence && (
                    <div className="text-[10px] text-rose-700 italic font-mono pt-1">
                      Evidence: {formatDisplayValue(t.evidence)} ({formatDisplayValue(t.source_stage)})
                    </div>
                  )}
                </li>
              ))}
            </ul>
          </div>
        </div>

        <div className="flex justify-end pt-2">
          <Button size="sm" onClick={onClose}>
            Close Strategic SWOT
          </Button>
        </div>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Informative Stage Locked Notice Component
// ---------------------------------------------------------------------------
export const StageLockedNotice = ({ stageNum, stageName, reason, unlockAction, onUnlockClick }) => {
  return (
    <div className="bg-stone-50 rounded-3xl p-8 border-2 border-stone-200 text-center space-y-4 max-w-xl mx-auto my-12 animate-fadeIn">
      <div className="w-14 h-14 bg-stone-200 rounded-2xl flex items-center justify-center mx-auto text-stone-600 shadow-inner">
        <Lock className="w-7 h-7" />
      </div>
      <div className="space-y-1.5">
        <span className="text-[11px] font-bold text-stone-500 uppercase tracking-widest font-mono">
          Stage {stageNum} Dependency Guard Active
        </span>
        <h3 className="text-xl font-bold text-stone-900 font-['Outfit']">
          {stageName} is Locked
        </h3>
        <p className="text-xs text-stone-600 leading-relaxed max-w-md mx-auto">
          {reason}
        </p>
      </div>

      <div className="pt-2">
        <button
          onClick={onUnlockClick}
          className="inline-flex items-center px-4 py-2.5 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition shadow-sm cursor-pointer space-x-1.5"
        >
          <span>{unlockAction || 'Complete Required Upstream Stage'}</span>
          <ArrowRight className="w-4 h-4 ml-1" />
        </button>
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Robust ErrorBoundary Class Component
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
        <div className="min-h-screen bg-[#FDFBF7] flex items-center justify-center p-6">
          <div className="bg-white rounded-3xl p-8 border-2 border-red-200 shadow-xl max-w-lg w-full text-center space-y-4">
            <div className="w-14 h-14 bg-red-100 rounded-2xl flex items-center justify-center mx-auto text-red-600">
              <AlertOctagon className="w-8 h-8" />
            </div>
            <div className="space-y-1">
              <h2 className="text-xl font-bold text-stone-900 font-['Outfit']">
                Feasibility Display Render Error
              </h2>
              <p className="text-xs text-stone-600 leading-relaxed">
                An unexpected error occurred while rendering the assessment. Your session and inputs are safe.
              </p>
            </div>
            <div className="p-3 bg-stone-50 rounded-xl text-xs text-stone-500 font-mono text-left max-h-32 overflow-y-auto">
              {String(this.state.error?.message || this.state.error)}
            </div>
            <div className="pt-2 flex justify-center space-x-3">
              <button
                onClick={() => window.location.reload()}
                className="px-4 py-2 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition shadow-sm cursor-pointer"
              >
                Reload Assessment
              </button>
              <Link
                to="/journey"
                className="px-4 py-2 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl text-xs font-bold transition inline-flex items-center"
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
// Main Feasibility Page (Stage 10, 11 & Stage 12 Synthesis)
// ---------------------------------------------------------------------------
export const FeasibilityPage = () => {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
    businessName: ctxBusinessName,
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

  // Tab state: 'stage12' | 'stage10' | 'stage11'
  const [activeTab, setActiveTab] = useState('stage10');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [businessTitle, setBusinessTitle] = useState(ctxBusinessName || 'Target Micro-Enterprise');

  // Stage 10 Data
  const [stage10Data, setStage10Data] = useState(null);
  const [expandedComponent, setExpandedComponent] = useState(null);
  const [clarificationAnswers, setClarificationAnswers] = useState({});
  const [submittingClarificationField, setSubmittingClarificationField] = useState(null);

  // Stage 11 Data
  const [stage11Data, setStage11Data] = useState(null);
  const [expandedRisk, setExpandedRisk] = useState('FINANCIAL');

  // Stage 12 Feasibility Data
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

  const isInitialFetchDone = useRef(false);

  // ---------------------------------------------------------------------------
  // Canonical Derived Upstream Status (Single Source of Truth)
  // ---------------------------------------------------------------------------
  const isS10Ready = isStage10Complete(stage10Data);
  const isS11Ready = isStage11Complete(stage11Data);
  const isS12Ready = Boolean(feasibilityData && feasibilityData.overall_feasibility_score !== undefined && feasibilityData.overall_feasibility_score !== null);

  const upstreamStatus = {
    stage8: {
      ready: true,
      name: 'Stage 08 • Market Opportunity',
      status: 'COMPLETED',
    },
    stage9: {
      ready: true,
      name: 'Stage 09 • Financial Position',
      status: 'COMPLETED',
    },
    stage10: {
      ready: isS10Ready,
      data: stage10Data,
      name: 'Stage 10 • Entrepreneur Profile',
      status: isS10Ready ? 'COMPLETED' : (stage10Data?.questions?.length > 0 ? 'CLARIFICATION_REQUIRED' : 'PENDING'),
    },
    stage11: {
      ready: isS11Ready,
      data: stage11Data,
      name: 'Stage 11 • Enterprise Risk Engine',
      status: isS11Ready ? 'COMPLETED' : (!isS10Ready ? 'LOCKED' : 'PENDING'),
    },
    stage12: {
      ready: isS12Ready,
      data: feasibilityData,
      name: 'Stage 12 • Final Feasibility Synthesis',
      status: isS12Ready ? 'COMPLETED' : (!isS11Ready ? 'LOCKED' : 'PENDING'),
    }
  };

  const s10Ready = upstreamStatus.stage10.ready;
  const s11Ready = upstreamStatus.stage11.ready;
  const s12Ready = upstreamStatus.stage12.ready;
  const allUpstreamReady = s10Ready && s11Ready;

  // Fetch full pipeline hydration with strict Stage 10 -> Stage 11 -> Stage 12 hard gating
  const fetchData = useCallback(async () => {
    if (!analysisId && !sessionId) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setError(null);

    try {
      // 1. Fetch Stage 10 Entrepreneur Readiness
      const epRes = await apiService.entrepreneurProfile.analyze({
        analysis_id: analysisId,
        session_id: sessionId,
      });
      setStage10Data(epRes);
      if (epRes?.business_title) setBusinessTitle(epRes.business_title);

      const isS10CompleteNow = isStage10Complete(epRes);

      // HARD GATE: If Stage 10 is NOT complete, STOP! Do not call Stage 11 or Stage 12!
      if (!isS10CompleteNow) {
        setStage11Data(null);
        setFeasibilityData(null);
        setActiveTab('stage10');
        setLoading(false);
        return;
      }

      // 2. Fetch Stage 11 Risk Analysis ONLY after Stage 10 is complete
      let riskRes = null;
      try {
        riskRes = await apiService.riskAnalysis.analyze({
          analysis_id: analysisId,
          session_id: sessionId,
          entrepreneur_readiness: epRes,
        });
        setStage11Data(riskRes);
      } catch (riskErr) {
        if (riskErr.response?.status === 409 || riskErr.status === 409) {
          console.warn('[STAGE 11 BLOCKED BY HARD GATE]', riskErr);
          setActiveTab('stage10');
          setLoading(false);
          return;
        }
        throw riskErr;
      }

      const isS11CompleteNow = isStage11Complete(riskRes);
      if (!isS11CompleteNow) {
        setFeasibilityData(null);
        setActiveTab('stage11');
        setLoading(false);
        return;
      }

      // 3. Fetch Stage 12 Final Feasibility Analysis ONLY after Stage 11 is complete
      try {
        const feasRes = await apiService.feasibility.analyze({
          analysis_id: analysisId,
          session_id: sessionId,
          entrepreneur_readiness: epRes,
          risk_analysis: riskRes,
        });
        setFeasibilityData(feasRes);

        // Advance tab to Stage 12 on full completion
        setActiveTab('stage12');

        // Mark workflow stage progression
        if (markStageComplete) {
          markStageComplete(10, 11);
          markStageComplete(11, 12);
          markStageComplete(12, 13);
        }
      } catch (feasErr) {
        if (feasErr.response?.status === 409 || feasErr.status === 409) {
          console.warn('[STAGE 12 BLOCKED BY HARD GATE]', feasErr);
          setActiveTab('stage11');
          setLoading(false);
          return;
        }
        throw feasErr;
      }
    } catch (err) {
      console.error('[FEASIBILITY HUB ERROR]', err);
      setError(err.message || 'Failed to evaluate Feasibility Synthesis engine.');
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

  // Handle Clarification Submission in Stage 10 (Voice and Text)
  const handleAnswerSubmit = async (field) => {
    const textAnswer = clarificationAnswers[field];
    if (!textAnswer || !textAnswer.trim()) return;

    setSubmittingClarificationField(field);
    setError(null);

    try {
      const clarifyRes = await apiService.entrepreneurProfile.clarify({
        text: textAnswer.trim(),
        field: field,
        analysis_id: analysisId,
        session_id: sessionId,
      });

      const updatedStage10 = clarifyRes.readiness_response || clarifyRes;
      setStage10Data(updatedStage10);
      setClarificationAnswers((prev) => ({ ...prev, [field]: '' }));

      const isCompleteNow = isStage10Complete(updatedStage10);

      // If Stage 10 is now completely answered, unlock and execute Stage 11 & Stage 12
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
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/webm' });
        const formData = new FormData();
        formData.append('file', audioBlob, 'clarification_recording.webm');
        formData.append('language_code', 'unknown');

        try {
          const sttRes = await apiService.intake.transcribe(formData);
          const transcript = sttRes.transcript || '';
          if (transcript) {
            setClarificationAnswers((prev) => ({ ...prev, [field]: transcript }));
          }
        } catch (sttErr) {
          console.warn('[VOICE STT NOTE]', sttErr.message);
          alert('Could not detect clear speech. Please type your answer.');
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
      setActiveVoiceField(field);
    } catch (err) {
      console.error('[MIC ACCESS ERROR]', err);
      alert('Microphone access denied. Please type your answer.');
    }
  };

  const stopRecording = () => {
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
      <div className="min-h-screen bg-[#FDFBF7] flex items-center justify-center p-6">
        <div className="bg-white rounded-3xl p-8 border-2 border-stone-200 shadow-xl max-w-lg w-full text-center space-y-4 animate-fadeIn">
          <div className="w-14 h-14 bg-stone-100 rounded-2xl flex items-center justify-center mx-auto text-stone-600">
            <Lock className="w-8 h-8" />
          </div>
          <div className="space-y-1.5">
            <h2 className="text-xl font-bold text-stone-900 font-['Outfit']">
              Analysis Context Unavailable
            </h2>
            <p className="text-xs text-stone-600 leading-relaxed">
              No active business session or analysis ID was found. Please complete the business intake and evaluation pipeline first.
            </p>
          </div>
          <div className="pt-2 flex justify-center space-x-3">
            <Link
              to="/intake"
              className="px-4 py-2.5 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition shadow-sm inline-flex items-center"
            >
              Start New Analysis
            </Link>
            <Link
              to="/journey"
              className="px-4 py-2.5 bg-stone-100 hover:bg-stone-200 text-stone-700 rounded-xl text-xs font-bold transition inline-flex items-center"
            >
              Return to Journey
            </Link>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#FDFBF7] pb-24 text-stone-900 font-sans">
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

      {/* Top Banner Header & Stepper */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link to="/financial-analysis" className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-500">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 text-[11px] font-bold tracking-wider bg-orange-100 text-orange-800 rounded uppercase">
                  Pillar: Validate & Decide
                </span>
                <span className="text-xs font-medium text-stone-500">
                  Stage 12 Master Feasibility Decision Engine
                </span>
              </div>
              <h1 className="text-xl font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                Feasibility Assessment Dashboard
                <span className="text-sm font-normal text-stone-500">• {businessTitle}</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={fetchData}
              disabled={loading}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-stone-100 hover:bg-stone-200 text-stone-700 transition cursor-pointer"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
              Re-evaluate All Engines
            </button>
            <Link to="/dpr">
              <Button size="sm" variant="secondary" icon={ArrowRight}>
                DPR Workspace
              </Button>
            </Link>
          </div>
        </div>

        {/* Global Pipeline Progress Stepper Header */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-2 pb-3">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2.5 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <div>
                <div className="font-bold text-emerald-900">01. Market Opportunity</div>
                <div className="text-[10px] text-emerald-700 font-mono">Stage 8 • Analyzed</div>
              </div>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2.5 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <div>
                <div className="font-bold text-emerald-900">02. Financial Position</div>
                <div className="text-[10px] text-emerald-700 font-mono">Stage 9 • Evaluated</div>
              </div>
            </div>

            {/* Stage 10 Stepper */}
            <div
              onClick={() => setActiveTab('stage10')}
              className={`rounded-lg p-2.5 flex items-center space-x-2 transition cursor-pointer ${
                activeTab === 'stage10'
                  ? 'bg-purple-600 text-white shadow-md'
                  : (s10Ready
                      ? 'bg-emerald-50 border border-emerald-200 text-emerald-950'
                      : 'bg-purple-50 border border-purple-200 text-purple-950')
              }`}
            >
              {s10Ready ? (
                <CheckCircle2 className="w-4 h-4 flex-shrink-0 text-emerald-600" />
              ) : (
                <UserCheck className="w-4 h-4 flex-shrink-0" />
              )}
              <div>
                <div className="font-bold">03. Entrepreneur Profile</div>
                <div className="text-[10px] opacity-90 font-mono">
                  Stage 10 • {s10Ready && stage10Data?.readiness_score !== null && stage10Data?.readiness_score !== undefined ? `${Math.round(stage10Data.readiness_score)}/100` : 'Clarifications Needed'}
                </div>
              </div>
            </div>

            {/* Stage 11 Stepper */}
            <div
              onClick={() => setActiveTab('stage11')}
              className={`rounded-lg p-2.5 flex items-center space-x-2 transition cursor-pointer ${
                activeTab === 'stage11'
                  ? 'bg-amber-500 text-white shadow-md'
                  : (!s10Ready
                      ? 'bg-stone-100 border border-stone-200 text-stone-400 cursor-not-allowed opacity-75'
                      : 'bg-amber-50 border border-amber-200 text-amber-950')
              }`}
            >
              {!s10Ready ? (
                <Lock className="w-4 h-4 flex-shrink-0 text-stone-400" />
              ) : (
                <ShieldCheck className="w-4 h-4 flex-shrink-0" />
              )}
              <div>
                <div className="font-bold">04. Risk Engine</div>
                <div className="text-[10px] opacity-90 font-mono">
                  Stage 11 • {!s10Ready ? 'Locked (Needs S10)' : (stage11Data?.overall_risk_severity || '7 Categories')}
                </div>
              </div>
            </div>

            {/* Stage 12 Stepper */}
            <div
              onClick={() => setActiveTab('stage12')}
              className={`rounded-lg p-2.5 flex items-center space-x-2 transition cursor-pointer ${
                activeTab === 'stage12'
                  ? 'bg-[#EA580C] text-white shadow-md'
                  : (!s11Ready
                      ? 'bg-stone-100 border border-stone-200 text-stone-400 cursor-not-allowed opacity-75'
                      : 'bg-stone-100 border border-stone-200 text-stone-900')
              }`}
            >
              {!s11Ready ? (
                <Lock className="w-4 h-4 flex-shrink-0 text-stone-400" />
              ) : (
                <Scale className="w-4 h-4 flex-shrink-0" />
              )}
              <div>
                <div className="font-bold">05. Final Feasibility</div>
                <div className="text-[10px] font-mono">
                  {!s11Ready ? 'Stage 12 • Locked' : (feasibilityData?.overall_feasibility_score !== undefined && feasibilityData?.overall_feasibility_score !== null ? `${Math.round(feasibilityData.overall_feasibility_score)}/100` : 'Stage 12')}
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Navigation Tabs */}
        <div className="flex border-b border-stone-200 space-x-4">
          <button
            onClick={() => setActiveTab('stage10')}
            className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'stage10'
                ? 'border-purple-600 text-purple-700'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
          >
            <UserCheck className="w-4 h-4" />
            Stage 10: Entrepreneur Profile Engine
            {stage10Data?.questions?.length > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] font-bold bg-purple-600 text-white rounded-full animate-pulse">
                {stage10Data.questions.length} PENDING
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('stage11')}
            className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'stage11'
                ? 'border-amber-500 text-amber-700'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
          >
            {!s10Ready ? <Lock className="w-3.5 h-3.5 text-stone-400" /> : <ShieldCheck className="w-4 h-4" />}
            Stage 11: Enterprise Risk Engine
            {!s10Ready && (
              <span className="text-[10px] font-mono text-stone-400 font-normal">(Locked)</span>
            )}
            {stage11Data?.critical_risks_count > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] font-bold bg-red-600 text-white rounded-full">
                {stage11Data.critical_risks_count} CRITICAL
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('stage12')}
            className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition cursor-pointer ${
              activeTab === 'stage12'
                ? 'border-[#EA580C] text-[#EA580C]'
                : 'border-transparent text-stone-500 hover:text-stone-800'
            }`}
          >
            {!s11Ready ? <Lock className="w-3.5 h-3.5 text-stone-400" /> : <Scale className="w-4 h-4" />}
            Stage 12: Final Feasibility Synthesis
            {!s11Ready && (
              <span className="text-[10px] font-mono text-stone-400 font-normal">(Locked)</span>
            )}
          </button>
        </div>

        {/* Loading Spinner */}
        {loading && (
          <div className="p-16 text-center space-y-4">
            <RefreshCw className="w-8 h-8 text-[#EA580C] animate-spin mx-auto" />
            <p className="text-sm font-semibold text-stone-600">
              Evaluating KALPA Agentic Synthesis across Opportunity, Finance, Readiness & Risk...
            </p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-6 bg-red-50 border-2 border-red-200 rounded-3xl flex flex-col sm:flex-row items-start justify-between gap-4 text-red-900 shadow-sm animate-fadeIn">
            <div className="flex items-start space-x-3">
              <AlertOctagon className="w-6 h-6 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="space-y-1">
                <h3 className="font-bold text-base text-red-950 font-['Outfit']">
                  Feasibility analysis could not be completed
                </h3>
                <p className="text-xs text-red-800 leading-relaxed max-w-xl">
                  {formatDisplayValue(error)}
                </p>
                <div className="text-[11px] text-red-600 font-mono pt-1">
                  Ensure all upstream pipeline stages (Opportunity, Finance, Entrepreneur Profile, and Risk) have completed without data gaps.
                </div>
              </div>
            </div>
            <div className="flex items-center space-x-2 flex-shrink-0">
              <button
                onClick={fetchData}
                className="px-4 py-2 bg-red-600 hover:bg-red-700 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-sm cursor-pointer"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                Retry Evaluation
              </button>
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* STAGE 10: ENTREPRENEUR PROFILE VIEW                           */}
        {/* ============================================================= */}
        {activeTab === 'stage10' && stage10Data && !loading && (
          <div className="space-y-6">
            {/* Targeted Clarification Module */}
            {stage10Data.questions && stage10Data.questions.length > 0 && (
              <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-orange-50 border-2 border-purple-300 rounded-3xl p-6 shadow-sm space-y-4 animate-fadeIn">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center font-bold shadow">
                      <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-purple-950 font-['Outfit'] flex items-center gap-2">
                        Targeted Clarification Required
                        <span className="px-2 py-0.5 text-xs font-bold bg-purple-200 text-purple-900 rounded-full font-mono">
                          {stage10Data.questions.length} Pending
                        </span>
                      </h2>
                      <p className="text-xs text-purple-800">
                        KALPA adheres to a strict <strong>No Fake Data Policy</strong>. Please answer each pending dimension below using Voice or Text. Answering one question preserves all other pending questions.
                      </p>
                    </div>
                  </div>
                  <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-200 text-purple-900">
                    Stage 10 Hard Gate Active
                  </span>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {stage10Data.questions.map((rawQ, idx) => {
                    const q = normalizeClarification(rawQ);
                    if (!q) return null;

                    const isSubmittingThis = submittingClarificationField === q.field;
                    const isRecThis = isRecording && activeVoiceField === q.field;

                    return (
                      <div
                        key={q.field || idx}
                        className="bg-white rounded-2xl p-4 border border-purple-200 shadow-sm space-y-3 flex flex-col justify-between hover:border-purple-300 transition"
                      >
                        <div className="space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider font-mono">
                              Field: {formatDisplayValue(q.field)}
                            </span>
                            <span className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                              q.priority === 'CRITICAL' || q.priority === 'HIGH'
                                ? 'bg-purple-100 text-purple-800'
                                : 'bg-stone-100 text-stone-700'
                            }`}>
                              {formatDisplayValue(q.priority)} Priority
                            </span>
                          </div>

                          <p className="text-xs font-bold text-stone-900 leading-snug">
                            {formatDisplayValue(q.question)}
                          </p>

                          {q.reason && (
                            <p className="text-[11px] text-stone-500 italic leading-relaxed">
                              {formatDisplayValue(q.reason)}
                            </p>
                          )}

                          {q.benchmark && (
                            <div className="text-[10px] text-purple-900 font-mono bg-purple-50/70 p-2 rounded-lg border border-purple-100 leading-tight">
                              <span className="font-bold text-purple-700">Benchmark: </span>
                              {formatDisplayValue(q.benchmark)}
                            </div>
                          )}

                          {q.suggested_options && q.suggested_options.length > 0 && (
                            <div className="space-y-1 pt-1">
                              <span className="text-[10px] font-medium text-stone-400">Quick select:</span>
                              <div className="flex flex-wrap gap-1">
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
                                    className="text-[10px] bg-stone-100 hover:bg-purple-100 hover:text-purple-900 text-stone-600 px-2 py-0.5 rounded-md border border-stone-200 transition cursor-pointer"
                                  >
                                    {opt}
                                  </button>
                                ))}
                              </div>
                            </div>
                          )}
                        </div>

                        <div className="space-y-2 pt-2 border-t border-purple-50">
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
                                  ? 'Enter number (e.g. 2)...'
                                  : 'Type your answer here...'
                              }
                              className="flex-1 px-3 py-2 text-xs border border-stone-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:outline-none"
                            />

                            <button
                              onClick={() => (isRecThis ? stopRecording() : startRecording(q.field))}
                              className={`p-2 rounded-xl text-xs font-bold transition cursor-pointer ${
                                isRecThis
                                  ? 'bg-red-600 text-white animate-pulse'
                                  : 'bg-stone-100 hover:bg-stone-200 text-stone-700'
                              }`}
                              title={isRecThis ? 'Stop voice recording' : 'Record voice answer'}
                            >
                              {isRecThis ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                            </button>

                            <button
                              onClick={() => handleAnswerSubmit(q.field)}
                              disabled={isSubmittingThis || !clarificationAnswers[q.field]?.trim()}
                              className="px-3 py-2 bg-purple-600 hover:bg-purple-700 text-white rounded-xl text-xs font-bold transition disabled:opacity-40 cursor-pointer flex items-center space-x-1"
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

            {/* Stage 10 Header & Provenance */}
            <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-sm grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
              <div className="lg:col-span-2 space-y-3">
                <div className="flex flex-wrap items-center gap-2">
                  <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                    s10Ready
                      ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                      : 'bg-purple-100 text-purple-800 border-purple-300'
                  }`}>
                    {stage10Data.readiness_level || (s10Ready ? 'HIGH' : 'CLARIFICATION REQUIRED')} READINESS
                  </span>
                  {renderIntegrityBadge('CALCULATED')}
                  <span className="text-xs text-stone-500 font-mono">
                    Confidence: {((stage10Data.confidence || 0) * 100).toFixed(0)}%
                  </span>
                </div>

                <h2 className="text-2xl font-bold text-stone-900 font-['Outfit']">
                  Entrepreneur Capability & Readiness Matrix
                </h2>
                <p className="text-xs text-stone-600 leading-relaxed">
                  Deterministic 5-dimension scoring evaluating skills, experience, statutory training, premises area, and operational commitment against curated business ontology standards.
                </p>

                <div className="flex items-center space-x-4 pt-1 text-xs">
                  <button
                    onClick={() => setIsStage10DrawerOpen(true)}
                    className="inline-flex items-center gap-1 text-[#EA580C] hover:underline font-bold text-xs cursor-pointer"
                  >
                    <Calculator className="w-3.5 h-3.5" />
                    View Full Calculation Trail
                  </button>
                </div>
              </div>

              <div className="flex flex-col items-center justify-center p-6 bg-stone-50 rounded-2xl border border-stone-200 text-center">
                <div className="text-4xl font-extrabold text-stone-900 font-['Outfit']">
                  {stage10Data.readiness_score !== null && stage10Data.readiness_score !== undefined
                    ? Math.round(stage10Data.readiness_score)
                    : '—'}
                  <span className="text-lg font-normal text-stone-500">/100</span>
                </div>
                <div className="text-xs font-bold text-stone-700 uppercase tracking-wider mt-2">
                  {stage10Data.readiness_level || 'Evaluated'} Readiness
                </div>
              </div>
            </div>

            {/* 5 Evaluated Dimensions */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {stage10Data.component_scores &&
                Object.entries(stage10Data.component_scores)
                  .filter(([key]) => key !== 'operational')
                  .map(([key, comp]) => {
                    const isExpanded = expandedComponent === key;
                    const weightPct = ((comp.weight || 0) * 100).toFixed(0);

                    return (
                      <div
                        key={key}
                        className={`bg-white rounded-2xl border transition shadow-sm overflow-hidden flex flex-col justify-between ${
                          isExpanded ? 'border-[#EA580C] ring-1 ring-[#EA580C]/20' : 'border-stone-200'
                        }`}
                      >
                        <div className="p-4 space-y-2">
                          <div className="flex items-center justify-between">
                            <span className="text-[10px] font-bold tracking-wider text-stone-400 uppercase font-mono">
                              {weightPct}% WEIGHT
                            </span>
                            <span
                              className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${
                                comp.status === 'STRONG'
                                  ? 'bg-emerald-100 text-emerald-800'
                                  : comp.status === 'ADEQUATE'
                                  ? 'bg-blue-100 text-blue-800'
                                  : 'bg-amber-100 text-amber-800'
                              }`}
                            >
                              {formatDisplayValue(comp.status)}
                            </span>
                          </div>

                          <h4 className="text-xs font-bold text-stone-900 capitalize">
                            {key.replace('_', ' ')}
                          </h4>

                          <div className="flex items-baseline space-x-1 mt-1">
                            <span className="text-2xl font-extrabold text-stone-900 font-['Outfit']">
                              {comp.score !== null && comp.score !== undefined ? Math.round(comp.score) : '—'}
                            </span>
                            <span className="text-xs text-stone-400">/100</span>
                          </div>

                          <div className="pt-1">
                            {renderIntegrityBadge(comp.evidence_source || comp.source)}
                          </div>
                        </div>

                        <div className="border-t border-stone-100 bg-stone-50/50 p-2">
                          <button
                            onClick={() => setExpandedComponent(isExpanded ? null : key)}
                            className="w-full text-left text-[11px] font-bold text-stone-700 hover:text-[#EA580C] flex items-center justify-between px-2 py-1 rounded transition cursor-pointer"
                          >
                            <span>Breakdown</span>
                            {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                          </button>
                        </div>
                      </div>
                    );
                  })}
            </div>

            {/* Contextual Support Programs */}
            <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 rounded-xl bg-blue-50 text-blue-600 flex items-center justify-center font-bold">
                    <Award className="w-5 h-5" />
                  </div>
                  <div>
                    <h3 className="text-base font-bold text-stone-900 font-['Outfit']">
                      How to Close Identified Gaps (Targeted Support Programs)
                    </h3>
                    <p className="text-xs text-stone-500">
                      Interventions matched specifically to your identified capability gaps.
                    </p>
                  </div>
                </div>
                <span className="text-xs font-bold text-blue-800 bg-blue-50 px-2.5 py-1 rounded-full border border-blue-200">
                  {stage10Data.required_support?.length || 0} Actions
                </span>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-1">
                {stage10Data.required_support?.map((sup, idx) => (
                  <div
                    key={idx}
                    className="bg-stone-50/60 rounded-2xl p-4 border border-stone-200 flex flex-col justify-between space-y-3"
                  >
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-amber-100 text-amber-800 uppercase">
                          {formatDisplayValue(sup.priority || 'MEDIUM')} PRIORITY
                        </span>
                        <span className="text-[10px] text-stone-500 font-medium">
                          {formatDisplayValue(sup.resource_type || 'COURSE')}
                        </span>
                      </div>
                      <h4 className="text-xs font-bold text-stone-900">{formatDisplayValue(sup.resource_title || sup.gap)}</h4>
                      <p className="text-[11px] text-stone-600">{formatDisplayValue(sup.recommended_action)}</p>
                      <div className="text-[10px] text-stone-400">Provider: {formatDisplayValue(sup.provider)}</div>
                    </div>

                    {sup.official_url ? (
                      <a
                        href={sup.official_url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="inline-flex items-center justify-center w-full px-3 py-1.5 bg-blue-600 hover:bg-blue-700 text-white rounded-xl text-xs font-bold transition shadow-sm cursor-pointer"
                      >
                        Open Official Portal <ExternalLink className="w-3 h-3 ml-1.5" />
                      </a>
                    ) : (
                      <div className="text-center text-[11px] text-stone-400 py-1 font-medium bg-stone-100 rounded-lg">
                        Verified Institutional Module
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* ============================================================= */}
        {/* STAGE 11: RISK ENGINE VIEW                                    */}
        {/* ============================================================= */}
        {activeTab === 'stage11' && !loading && (
          <>
            {!s10Ready ? (
              <StageLockedNotice
                stageNum={11}
                stageName="Enterprise Risk Engine"
                reason="Stage 11 evaluates 7 business-specific risk categories using your verified skills, experience, and resources from Stage 10. Complete pending clarifications to continue."
                unlockAction="Complete Entrepreneur Profile (Stage 10)"
                onUnlockClick={() => setActiveTab('stage10')}
              />
            ) : stage11Data ? (
              <div className="space-y-6">
                <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-sm grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
                  <div className="lg:col-span-2 space-y-3">
                    <div className="flex flex-wrap items-center gap-2">
                      {getSeverityBadge(stage11Data.overall_risk_severity)}
                      {renderIntegrityBadge('CALCULATED')}
                      <span className="text-xs text-stone-500 font-mono">
                        Confidence: {((stage11Data.confidence || 0) * 100).toFixed(0)}%
                      </span>
                    </div>

                    <h2 className="text-2xl font-bold text-stone-900 font-['Outfit']">
                      Enterprise 7-Category Risk Matrix
                    </h2>
                    <p className="text-xs text-stone-600 leading-relaxed">
                      Deterministic synthesis consuming <strong>Stage 9 Financial DSCR & Break-Even</strong>, <strong>Stage 6 Market Demand & Competition</strong>, <strong>Stage 10 Capability gaps</strong>, and <strong>Agricultural Seasonality</strong>.
                    </p>

                    <div className="flex items-center space-x-4 pt-1 text-xs">
                      <button
                        onClick={() => setIsStage11DrawerOpen(true)}
                        className="inline-flex items-center gap-1 text-[#EA580C] hover:underline font-bold text-xs cursor-pointer"
                      >
                        <Calculator className="w-3.5 h-3.5" />
                        View Full Risk Synthesis Trail
                      </button>
                    </div>
                  </div>

                  <div className="flex flex-col items-center justify-center p-6 bg-stone-50 rounded-2xl border border-stone-200 text-center">
                    <div className="text-4xl font-extrabold text-stone-900 font-['Outfit']">
                      {stage11Data.overall_risk_score !== null && stage11Data.overall_risk_score !== undefined
                        ? stage11Data.overall_risk_score.toFixed(2)
                        : '—'}
                      <span className="text-lg font-normal text-stone-500">/1.0</span>
                    </div>
                    <div className="text-xs font-bold text-stone-700 uppercase tracking-wider mt-2">
                      {formatDisplayValue(stage11Data.overall_risk_severity)} Enterprise Risk
                    </div>
                  </div>
                </div>

                {/* 7 Categories Matrix */}
                <div className="space-y-3">
                  {stage11Data.category_risks &&
                    Object.entries(stage11Data.category_risks).map(([catKey, risk]) => {
                      const isExpanded = expandedRisk === catKey;
                      const weightPct = stage11Data.weights?.[catKey.toLowerCase()]
                        ? (stage11Data.weights[catKey.toLowerCase()] * 100).toFixed(0)
                        : null;

                      const isDataGap = risk.status === 'DATA_GAP' || risk.source_stage === 'UNKNOWN' || risk.score === null;

                      return (
                        <div
                          key={catKey}
                          className={`bg-white rounded-2xl border transition shadow-sm overflow-hidden ${
                            isExpanded ? 'border-stone-400 ring-1 ring-stone-300' : 'border-stone-200'
                          }`}
                        >
                          <button
                            onClick={() => setExpandedRisk(isExpanded ? null : catKey)}
                            className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-stone-50/50 transition cursor-pointer"
                          >
                            <div className="flex items-center space-x-3">
                              <div className="w-9 h-9 rounded-xl bg-stone-100 flex items-center justify-center text-stone-700 font-bold text-xs font-mono">
                                {catKey.slice(0, 3)}
                              </div>
                              <div>
                                <div className="text-sm font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                                  {catKey.replace('_', ' ')} RISK
                                  {weightPct && (
                                    <span className="text-[10px] font-normal text-stone-400 font-mono">
                                      ({weightPct}% weight)
                                    </span>
                                  )}
                                </div>
                                <div className="text-[11px] text-stone-500 font-mono">
                                  Source: {formatDisplayValue(risk.source_stage)}
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center space-x-4">
                              <span className="text-sm font-extrabold text-stone-900 font-mono">
                                {typeof risk.score === 'number' ? risk.score.toFixed(2) : (risk.score || '—')}
                              </span>
                              {getSeverityBadge(isDataGap ? 'DATA_GAP' : (risk.level || risk.severity))}
                              {isExpanded ? <ChevronUp className="w-4 h-4 text-stone-400" /> : <ChevronDown className="w-4 h-4 text-stone-400" />}
                            </div>
                          </button>

                          {isExpanded && (
                            <div className="px-5 pb-5 pt-3 border-t border-stone-100 bg-stone-50/40 space-y-3 text-xs">
                              {risk.evidence && (
                                <div className="p-3 bg-white rounded-xl border border-stone-200">
                                  <strong>Upstream Evidence:</strong> {formatDisplayValue(risk.evidence)}
                                </div>
                              )}
                              {risk.benchmark && (
                                <div className="p-3 bg-white rounded-xl border border-stone-200">
                                  <strong>Ontology Benchmark:</strong> {formatDisplayValue(risk.benchmark)}
                                </div>
                              )}
                              <div className="p-3 bg-white rounded-xl border border-stone-200">
                                <strong>Deterministic Formula:</strong> {formatDisplayValue(risk.formula || risk.calculation)}
                              </div>
                              {risk.impact && (
                                <div className="p-3 bg-white rounded-xl border border-stone-200">
                                  <strong>Business Impact:</strong> {formatDisplayValue(risk.impact || risk.business_impact)}
                                </div>
                              )}
                              {risk.mitigation && (
                                <div className="p-3 bg-emerald-50 rounded-xl border border-emerald-200 text-emerald-950">
                                  <strong>Actionable Mitigation:</strong> {formatDisplayValue(risk.mitigation)}
                                </div>
                              )}
                            </div>
                          )}
                        </div>
                      );
                    })}
                </div>
              </div>
            ) : null}
          </>
        )}

        {/* ============================================================= */}
        {/* STAGE 12: MASTER FEASIBILITY VIEW                             */}
        {/* ============================================================= */}
        {activeTab === 'stage12' && !loading && (
          <>
            {!s10Ready ? (
              <StageLockedNotice
                stageNum={12}
                stageName="Master Feasibility Engine"
                reason="Feasibility Synthesis requires verified Entrepreneur Profile readiness. Please complete Stage 10 clarifications first."
                unlockAction="Go to Stage 10 Clarifications"
                onUnlockClick={() => setActiveTab('stage10')}
              />
            ) : !s11Ready ? (
              <StageLockedNotice
                stageNum={12}
                stageName="Master Feasibility Engine"
                reason="Feasibility Synthesis combines Opportunity, Finance, Readiness, and Risk. Stage 11 Risk Analysis must be completed first."
                unlockAction="Evaluate Stage 11 Risk Engine"
                onUnlockClick={() => setActiveTab('stage11')}
              />
            ) : feasibilityData ? (
              <div className="space-y-6">
                {/* Master Decision Hero Card */}
                <div className="bg-white rounded-3xl p-6 sm:p-8 border border-stone-200 shadow-sm grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
                  <div className="lg:col-span-2 space-y-4">
                    <div className="flex flex-wrap items-center gap-2">
                      {getFeasibilityDecisionBadge(feasibilityData.decision)}
                      {renderIntegrityBadge('CALCULATED')}
                      <span className="text-xs text-stone-500 font-mono">
                        Confidence: {((feasibilityData.confidence_score || 0) * 100).toFixed(0)}%
                      </span>
                    </div>

                    <div className="space-y-1">
                      <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 font-['Outfit']">
                        Venture Feasibility Assessment
                      </h2>
                      <p className="text-xs text-stone-500 font-mono">
                        Location: <strong>{formatDisplayValue(feasibilityData.location_summary)}</strong> • Analysis ID: {feasibilityData.analysis_id?.slice(0, 8)}
                      </p>
                    </div>

                    <p className="text-xs text-stone-600 leading-relaxed">
                      Deterministic synthesis combining <strong>Stage 8 Market Opportunity (25%)</strong>, <strong>Stage 9 Financial Viability (35%)</strong>, <strong>Stage 10 Entrepreneur Competency (20%)</strong>, and <strong>Stage 11 Risk Resilience (20%)</strong> with non-negotiable critical gates.
                    </p>

                    {/* ML Model Interface Indicator */}
                    <div className="p-2.5 bg-stone-50 border border-stone-200 rounded-xl text-xs text-stone-600 flex items-center justify-between">
                      <div className="flex items-center space-x-2">
                        <Sparkles className="w-4 h-4 text-stone-400" />
                        <span>
                          <strong>ML Model Slot:</strong> {feasibilityData.ml_prediction?.status === 'CONFIGURED' ? 'Inference Active' : 'Not Configured (100% Deterministic Engine Active)'}
                        </span>
                      </div>
                      <span className="text-[10px] font-bold text-stone-400 font-mono">v1.0-rules</span>
                    </div>

                    {/* Calculation Provenance Opener */}
                    <div className="flex flex-wrap items-center gap-4 pt-1 text-xs">
                      <button
                        onClick={() => setIsStage12DrawerOpen(true)}
                        className="inline-flex items-center gap-1 text-[#EA580C] hover:underline font-bold text-xs cursor-pointer"
                      >
                        <Calculator className="w-3.5 h-3.5" />
                        View Complete Decision Calculation
                      </button>
                      {feasibilityData.dynamic_swot && (
                        <button
                          onClick={() => setIsSWOTModalOpen(true)}
                          className="inline-flex items-center gap-1 text-emerald-700 hover:underline font-bold text-xs cursor-pointer"
                        >
                          <BarChart3 className="w-3.5 h-3.5" />
                          View Dynamic Strategic SWOT
                        </button>
                      )}
                    </div>
                  </div>

                  {/* Central Feasibility Score Gauge */}
                  <div className="flex flex-col items-center justify-center p-6 bg-stone-50 rounded-2xl border border-stone-200 text-center">
                    <div className="text-5xl font-extrabold text-stone-900 font-['Outfit']">
                      {Math.round(feasibilityData.overall_feasibility_score)}
                      <span className="text-xl font-normal text-stone-500">/100</span>
                    </div>
                    <div className="text-xs font-bold text-stone-700 uppercase tracking-wider mt-2">
                      Composite Feasibility Score
                    </div>
                    <div className="text-[11px] text-stone-500 mt-1">
                      Recommendation: <strong className="text-stone-900">{formatDisplayValue(feasibilityData.recommendation)}</strong>
                    </div>
                  </div>
                </div>

                {/* 4 Core Analytical Pillars Grid */}
                <div className="space-y-3">
                  <div className="flex items-center justify-between">
                    <h3 className="text-sm font-bold text-stone-900">
                      Four Analytical Pillars (Weighted Synthesis)
                    </h3>
                    <span className="text-xs text-stone-500">
                      Click any pillar to inspect formula, inputs & weighted contribution
                    </span>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    {feasibilityData.pillar_scores &&
                      Object.entries(feasibilityData.pillar_scores).map(([key, pillar]) => {
                        const isExpanded = expandedPillar === key;
                        const weightPct = ((pillar.weight || 0) * 100).toFixed(0);

                        return (
                          <div
                            key={key}
                            className={`bg-white rounded-2xl border transition shadow-sm overflow-hidden flex flex-col justify-between ${
                              isExpanded ? 'border-[#EA580C] ring-1 ring-[#EA580C]/20' : 'border-stone-200'
                            }`}
                          >
                            <div className="p-4 space-y-2">
                              <div className="flex items-center justify-between">
                                <span className="text-[10px] font-bold tracking-wider text-stone-400 uppercase font-mono">
                                  {weightPct}% WEIGHT
                                </span>
                                <span
                                  className={`text-[10px] font-bold px-2 py-0.5 rounded ${
                                    pillar.status === 'STRONG'
                                      ? 'bg-emerald-100 text-emerald-800'
                                      : pillar.status === 'ADEQUATE'
                                      ? 'bg-blue-100 text-blue-800'
                                      : pillar.status === 'CAUTION'
                                      ? 'bg-amber-100 text-amber-800'
                                      : 'bg-red-100 text-red-800'
                                  }`}
                                >
                                  {formatDisplayValue(pillar.status)}
                                </span>
                              </div>

                              <h4 className="text-xs font-bold text-stone-900 leading-snug">
                                {formatDisplayValue(pillar.title)}
                              </h4>

                              <div className="flex items-baseline space-x-1.5 mt-1">
                                <span className="text-2xl font-extrabold text-stone-900 font-['Outfit']">
                                  {Math.round(pillar.score)}
                                </span>
                                <span className="text-xs text-stone-400">/100</span>
                                <span className="text-xs font-bold text-emerald-600 font-mono ml-auto">
                                  +{Number(pillar.weighted_contribution).toFixed(1)} pts
                                </span>
                              </div>

                              <div className="flex items-center justify-between pt-1">
                                {renderIntegrityBadge(pillar.source_stage)}
                                <span className="text-[10px] text-stone-400 font-mono">
                                  {((pillar.confidence || 0) * 100).toFixed(0)}% conf
                                </span>
                              </div>
                            </div>

                            {/* Expandable Formula Toggle */}
                            <div className="border-t border-stone-100 bg-stone-50/50 p-2">
                              <button
                                onClick={() => setExpandedPillar(isExpanded ? null : key)}
                                className="w-full text-left text-[11px] font-bold text-stone-700 hover:text-[#EA580C] flex items-center justify-between px-2 py-1 rounded transition cursor-pointer"
                              >
                                <span>How was this calculated?</span>
                                {isExpanded ? (
                                  <ChevronUp className="w-3.5 h-3.5" />
                                ) : (
                                  <ChevronDown className="w-3.5 h-3.5" />
                                )}
                              </button>
                            </div>
                          </div>
                        );
                      })}
                  </div>

                  {/* Expanded Pillar Deep Dive View */}
                  {expandedPillar && feasibilityData.pillar_scores?.[expandedPillar] && (
                    <div className="bg-white rounded-2xl border-2 border-stone-200 p-5 shadow-sm space-y-4 animate-fadeIn">
                      {(() => {
                        const pil = feasibilityData.pillar_scores[expandedPillar];
                        return (
                          <>
                            <div className="flex items-center justify-between border-b border-stone-100 pb-3">
                              <div className="flex items-center space-x-2">
                                <span className="text-sm font-bold text-stone-900">
                                  {formatDisplayValue(pil.title)} Formula & Inputs Breakdown
                                </span>
                                {renderIntegrityBadge(pil.source_stage)}
                                <span className="text-xs text-stone-500 font-mono">
                                  Weight: {((pil.weight || 0) * 100).toFixed(0)}% (+{pil.weighted_contribution} pts)
                                </span>
                              </div>
                              <button
                                onClick={() => setExpandedPillar(null)}
                                className="text-xs text-stone-400 hover:text-stone-700 cursor-pointer"
                              >
                                Close Breakdown
                              </button>
                            </div>

                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                              <div className="p-3 bg-stone-50 rounded-xl space-y-1.5">
                                <span className="font-bold text-stone-700 font-mono text-[11px] uppercase">
                                  Calculation Formula:
                                </span>
                                <div className="text-stone-900 font-mono leading-relaxed">
                                  {formatDisplayValue(pil.calculation)}
                                </div>
                              </div>
                              <div className="p-3 bg-stone-50 rounded-xl space-y-1.5">
                                <span className="font-bold text-stone-700 font-mono text-[11px] uppercase">
                                  Key Inputs & Provenance:
                                </span>
                                <ul className="space-y-1 text-stone-700">
                                  {pil.inputs &&
                                    Object.entries(pil.inputs).map(([ik, iv]) => (
                                      <li key={ik} className="flex justify-between font-mono text-[11px]">
                                        <span className="text-stone-500">{ik}:</span>
                                        <span className="font-bold text-stone-900">{formatDisplayValue(iv)}</span>
                                      </li>
                                    ))}
                                </ul>
                              </div>
                            </div>
                          </>
                        );
                      })()}
                    </div>
                  )}
                </div>

                {/* YES / NO Action Pathway */}
                {feasibilityData.recommendation === 'YES' || feasibilityData.decision === 'VIABLE' || feasibilityData.decision === 'VIABLE_WITH_CAUTION' ? (
                  <div className="bg-emerald-50 border-2 border-emerald-300 rounded-3xl p-6 sm:p-8 flex flex-col md:flex-row items-center justify-between gap-6 shadow-sm">
                    <div className="space-y-2">
                      <div className="flex items-center space-x-2">
                        <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-600 text-white">
                          YES PATHWAY UNLOCKED
                        </span>
                        <span className="text-xs font-bold text-emerald-800">
                          Stage 13 Dynamic SWOT & Strategic Advisory Ready
                        </span>
                      </div>
                      <h3 className="text-xl font-bold text-emerald-950 font-['Outfit']">
                        Venture Feasibility Verified — Proceed to Stage 13 SWOT
                      </h3>
                      <p className="text-xs text-emerald-800 max-w-2xl">
                        Your enterprise metrics satisfy viability thresholds. Stage 13 Dynamic SWOT Agent will synthesize cross-engine findings across market, finance, readiness, and risk into an evidence-grounded SWOT matrix and strategic roadmap.
                      </p>
                    </div>
                    <div className="flex flex-wrap items-center gap-3">
                      <button
                        onClick={() => setIsSWOTModalOpen(true)}
                        className="px-4 py-2.5 bg-white hover:bg-emerald-100 text-emerald-900 border border-emerald-300 rounded-xl text-xs font-bold transition shadow-xs cursor-pointer"
                      >
                        Quick Matrix Preview
                      </button>
                      <Link
                        to="/swot"
                        state={{
                          analysisId: effectiveAnalysisId,
                          sessionId: effectiveSessionId,
                          feasibilityResult: feasibilityData,
                          businessProfile: feasibilityData?.business_name ? { specific_business: feasibilityData.business_name } : undefined,
                          locationProfile: feasibilityData?.location_summary ? { location_summary: feasibilityData.location_summary } : undefined,
                          entrepreneurReadiness: stage10Data,
                          riskAnalysis: stage11Data,
                          financialAnalysis: (sessionStorage.getItem('kalpa_financial_analysis') ? JSON.parse(sessionStorage.getItem('kalpa_financial_analysis')) : undefined),
                          financialContext: (sessionStorage.getItem('kalpa_financial_context') ? JSON.parse(sessionStorage.getItem('kalpa_financial_context')) : undefined)
                        }}
                      >
                        <button className="px-5 py-2.5 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition flex items-center gap-1.5 shadow-md cursor-pointer">
                          <span>Proceed to Stage 13 SWOT</span>
                          <ArrowRight className="w-4 h-4" />
                        </button>
                      </Link>
                    </div>
                  </div>
                ) : (
                  /* NO / PIVOT PATHWAY */
                  <div className="bg-gradient-to-r from-amber-50 via-orange-50 to-red-50 border-2 border-orange-300 rounded-3xl p-6 sm:p-8 space-y-6 shadow-sm">
                    <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                      <div className="space-y-1.5">
                        <div className="flex items-center space-x-2">
                          <span className="px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-600 text-white">
                            PIVOT ADVISOR ACTIVE
                          </span>
                          <span className="text-xs font-bold text-orange-900">
                            Alternative Business Recommendations
                          </span>
                        </div>
                        <h3 className="text-xl font-bold text-stone-900 font-['Outfit']">
                          Recommended Strategic Pivot Opportunities
                        </h3>
                        <p className="text-xs text-stone-700 max-w-2xl">
                          The current business configuration has critical risk or capital constraints. KALPA has matched your verified skills and available capital to feasible alternative micro-enterprises.
                        </p>
                      </div>
                    </div>

                    <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
                      {feasibilityData.pivot_recommendations?.map((cand, idx) => (
                        <div
                          key={cand.business_id || idx}
                          className="bg-white rounded-2xl p-5 border border-orange-200 shadow-sm flex flex-col justify-between space-y-4 hover:border-[#EA580C] transition"
                        >
                          <div className="space-y-2">
                            <div className="flex items-center justify-between">
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-100 text-orange-800 uppercase font-mono">
                                {cand.skill_fit_percentage}% Skill Fit
                              </span>
                              <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-emerald-100 text-emerald-800">
                                {cand.capital_fit}
                              </span>
                            </div>

                            <h4 className="text-sm font-bold text-stone-900 leading-snug">
                              {cand.business_name}
                            </h4>

                            <div className="text-xs text-stone-700">
                              <strong>Capital Required:</strong> ₹{(cand.capital_requirement / 100000).toFixed(1)} Lakhs
                            </div>

                            <p className="text-xs text-stone-600 leading-relaxed">
                              {cand.pivot_reason}
                            </p>

                            <div className="pt-2 border-t border-stone-200/60 space-y-1">
                              <span className="text-[10px] font-bold text-stone-400 uppercase">Key Advantages:</span>
                              <ul className="space-y-1">
                                {cand.key_advantages?.slice(0, 2).map((adv, aIdx) => (
                                  <li key={aIdx} className="text-[11px] text-stone-600 flex items-start space-x-1.5">
                                    <Check className="w-3 h-3 text-emerald-600 flex-shrink-0 mt-0.5" />
                                    <span>{adv}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>

                          <button
                            onClick={() => handleSelectPivot(cand)}
                            className="w-full py-2.5 px-3 bg-[#EA580C] hover:bg-orange-600 text-white rounded-xl text-xs font-bold transition flex items-center justify-center space-x-1 shadow-sm cursor-pointer"
                          >
                            <span>Analyse This Business Idea</span>
                            <ArrowRight className="w-3.5 h-3.5 ml-1" />
                          </button>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            ) : null}
          </>
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
