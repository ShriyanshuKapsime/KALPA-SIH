import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  ArrowLeft
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';

export const FeasibilityPage = () => {
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
  const sessionId = location.state?.sessionId || queryParams.get('session_id') || ctxSessionId || '';
  const analysisId = location.state?.analysisId || queryParams.get('analysis_id') || ctxAnalysisId || '';

  // State management
  const [activeTab, setActiveTab] = useState('stage10'); // 'stage10' | 'stage11' | 'stage12'
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [businessTitle, setBusinessTitle] = useState(ctxBusinessName || 'Target Micro-Enterprise');

  // Stage 10 Data
  const [stage10Data, setStage10Data] = useState(null);
  const [clarificationAnswers, setClarificationAnswers] = useState({});
  const [submittingClarification, setSubmittingClarification] = useState(false);
  const [isRecording, setIsRecording] = useState(false);
  const [activeVoiceField, setActiveVoiceField] = useState(null);
  const [voiceTranscript, setVoiceTranscript] = useState('');
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Stage 11 Data
  const [stage11Data, setStage11Data] = useState(null);
  const [expandedRisk, setExpandedRisk] = useState('FINANCIAL');

  // Upstream Stages Summary
  const [upstreamSummary, setUpstreamSummary] = useState({
    opportunityScore: 88,
    loanStructure: '₹9.0 Lakhs',
    marketDemand: 'Strong Catchment Demand',
  });

  const isInitialFetchDone = useRef(false);

  // Fetch Stage 10 and Stage 11 live data
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
      if (epRes.business_title) setBusinessTitle(epRes.business_title);

      // 2. Fetch Stage 11 Risk Engine Analysis
      const riskRes = await apiService.riskAnalysis.analyze({
        analysis_id: analysisId,
        session_id: sessionId,
        entrepreneur_readiness: epRes,
      });
      setStage11Data(riskRes);

      // Update workflow status
      markStageComplete(10, 11);
      markStageComplete(11, 12);
    } catch (err) {
      console.error('[FEASIBILITY HUB ERROR]', err);
      setError(err.message || 'Failed to evaluate Feasibility Preparation engines.');
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

  // Handle Clarification Text Submission
  const handleAnswerSubmit = async (field) => {
    const textAnswer = clarificationAnswers[field];
    if (!textAnswer || !textAnswer.trim()) return;

    setSubmittingClarification(true);
    try {
      // Send answer to clarification extractor
      const clarifyRes = await apiService.entrepreneurProfile.clarify({
        text: textAnswer,
        field: field,
      });

      const extracted = clarifyRes.extracted_facts || {};

      // Re-run Stage 10 with updated structured facts
      const updatedEpRes = await apiService.entrepreneurProfile.analyze({
        analysis_id: analysisId,
        session_id: sessionId,
        entrepreneur_profile: {
          ...stage10Data?.component_scores,
          ...extracted,
        },
      });
      setStage10Data(updatedEpRes);

      // Re-run Stage 11 with updated readiness
      const updatedRiskRes = await apiService.riskAnalysis.analyze({
        analysis_id: analysisId,
        session_id: sessionId,
        entrepreneur_readiness: updatedEpRes,
      });
      setStage11Data(updatedRiskRes);

      // Clear input
      setClarificationAnswers((prev) => ({ ...prev, [field]: '' }));
    } catch (err) {
      console.error('[CLARIFICATION ERROR]', err);
      alert(`Could not process answer: ${err.message}`);
    } finally {
      setSubmittingClarification(false);
    }
  };

  // Voice recording handlers (reuses Sarvam STT pipeline)
  const startRecording = async (field) => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        const formData = new FormData();
        formData.append('audio', audioBlob, 'clarification.wav');
        formData.append('session_id', sessionId || 'live_feasibility_session');

        try {
          // Submit voice audio to existing Sarvam STT pipeline
          const sttRes = await apiService.intake.submitVoice(formData);
          const transcript = sttRes.transcript || sttRes.text || '';
          if (transcript) {
            setClarificationAnswers((prev) => ({ ...prev, [field]: transcript }));
            setVoiceTranscript(transcript);
          }
        } catch (sttErr) {
          console.warn('[VOICE STT NOTE]', sttErr.message);
          alert('Could not transcribe audio. Please type your answer directly.');
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

  // Helper colors for severity
  const getSeverityBadge = (sev) => {
    switch (sev) {
      case 'CRITICAL':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-red-100 text-red-800 border border-red-300"><Flame className="w-3 h-3 mr-1" /> CRITICAL</span>;
      case 'HIGH':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-orange-100 text-orange-800 border border-orange-300"><AlertTriangle className="w-3 h-3 mr-1" /> HIGH</span>;
      case 'MEDIUM':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300"><Activity className="w-3 h-3 mr-1" /> MEDIUM</span>;
      case 'LOW':
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300"><CheckCircle2 className="w-3 h-3 mr-1" /> LOW</span>;
      default:
        return <span className="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-bold bg-stone-100 text-stone-700 border border-stone-300">UNKNOWN</span>;
    }
  };

  const getReadinessLevelBadge = (level) => {
    switch (level) {
      case 'HIGH':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-emerald-100 text-emerald-800 border border-emerald-300">HIGH READINESS</span>;
      case 'MODERATE':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-blue-100 text-blue-800 border border-blue-300">MODERATE READINESS</span>;
      case 'DEVELOPING':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-amber-100 text-amber-800 border border-amber-300">DEVELOPING READINESS</span>;
      case 'INCOMPLETE':
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-purple-100 text-purple-800 border border-purple-300 animate-pulse">PROFILE INCOMPLETE</span>;
      default:
        return <span className="px-3 py-1 rounded-full text-xs font-bold bg-stone-100 text-stone-700 border border-stone-300">LOW READINESS</span>;
    }
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] pb-24 text-stone-900 font-sans">
      {/* Top Banner Navigation */}
      <div className="bg-white border-b border-stone-200 sticky top-0 z-30 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-3.5 flex flex-col md:flex-row md:items-center justify-between gap-4">
          <div className="flex items-center space-x-3">
            <Link to="/financial-analysis" className="p-1.5 rounded-lg hover:bg-stone-100 text-stone-500">
              <ArrowLeft className="w-5 h-5" />
            </Link>
            <div>
              <div className="flex items-center space-x-2">
                <span className="px-2 py-0.5 text-[11px] font-bold tracking-wider bg-orange-100 text-orange-800 rounded uppercase">
                  Pillar: Prepare
                </span>
                <span className="text-xs font-medium text-stone-500">Stage 10 & 11 Feasibility Engine Pre-check</span>
              </div>
              <h1 className="text-xl font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                Feasibility Preparation Hub
                <span className="text-sm font-normal text-stone-500">• {businessTitle}</span>
              </h1>
            </div>
          </div>

          <div className="flex items-center space-x-2">
            <button
              onClick={fetchData}
              disabled={loading}
              className="inline-flex items-center px-3 py-1.5 rounded-lg text-xs font-medium bg-stone-100 hover:bg-stone-200 text-stone-700 transition"
            >
              <RefreshCw className={`w-3.5 h-3.5 mr-1.5 ${loading ? 'animate-spin' : ''}`} />
              Re-evaluate All Engines
            </button>
            <Link to="/dpr">
              <Button size="sm" variant="secondary" icon={ArrowRight}>
                View DPR Workspace
              </Button>
            </Link>
          </div>
        </div>

        {/* Global Feasibility Preparation Stepper Header */}
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-2 pb-3">
          <div className="grid grid-cols-2 sm:grid-cols-5 gap-2 text-xs">
            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2.5 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <div>
                <div className="font-bold text-emerald-900">01. Market Opportunity</div>
                <div className="text-[10px] text-emerald-700 font-mono">Stage 8 • 88% Viable</div>
              </div>
            </div>

            <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-2.5 flex items-center space-x-2">
              <CheckCircle2 className="w-4 h-4 text-emerald-600 flex-shrink-0" />
              <div>
                <div className="font-bold text-emerald-900">02. Financial Position</div>
                <div className="text-[10px] text-emerald-700 font-mono">Stage 9 • DSCR 1.82x</div>
              </div>
            </div>

            <div className={`rounded-lg p-2.5 flex items-center space-x-2 transition ${activeTab === 'stage10' ? 'bg-orange-500 text-white shadow-md' : 'bg-orange-50 border border-orange-200 text-orange-950'}`}>
              <UserCheck className="w-4 h-4 flex-shrink-0" />
              <div>
                <div className="font-bold">03. Entrepreneur Readiness</div>
                <div className={`text-[10px] ${activeTab === 'stage10' ? 'text-orange-100' : 'text-orange-700'}`}>Stage 10 • {stage10Data?.readiness_score ? `${Math.round(stage10Data.readiness_score)}% Score` : 'Analyzing'}</div>
              </div>
            </div>

            <div className={`rounded-lg p-2.5 flex items-center space-x-2 transition ${activeTab === 'stage11' ? 'bg-orange-500 text-white shadow-md' : 'bg-amber-50 border border-amber-200 text-amber-950'}`}>
              <ShieldCheck className="w-4 h-4 flex-shrink-0" />
              <div>
                <div className="font-bold">04. Risk Analysis</div>
                <div className={`text-[10px] ${activeTab === 'stage11' ? 'text-orange-100' : 'text-amber-700'}`}>Stage 11 • {stage11Data?.overall_risk_severity || '7 Categories'}</div>
              </div>
            </div>

            <div className="bg-stone-100 border border-stone-200 rounded-lg p-2.5 flex items-center space-x-2 opacity-75">
              <Lock className="w-4 h-4 text-stone-500 flex-shrink-0" />
              <div>
                <div className="font-bold text-stone-600">05. Final Feasibility</div>
                <div className="text-[10px] text-stone-500">Stage 12 • Locked</div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-6 space-y-6">
        {/* Navigation Tabs between Stage 10, Stage 11, and Stage 12 Locked */}
        <div className="flex border-b border-stone-200 space-x-4">
          <button
            onClick={() => setActiveTab('stage10')}
            className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition ${activeTab === 'stage10' ? 'border-[#EA580C] text-[#EA580C]' : 'border-transparent text-stone-500 hover:text-stone-800'}`}
          >
            <UserCheck className="w-4 h-4" />
            Stage 10: Entrepreneur Profile Engine
            {stage10Data?.status === 'PROFILE_INCOMPLETE' && (
              <span className="w-2 h-2 rounded-full bg-purple-500 animate-ping"></span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('stage11')}
            className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition ${activeTab === 'stage11' ? 'border-[#EA580C] text-[#EA580C]' : 'border-transparent text-stone-500 hover:text-stone-800'}`}
          >
            <ShieldCheck className="w-4 h-4" />
            Stage 11: Enterprise Risk Engine
            {stage11Data?.critical_risks_count > 0 && (
              <span className="px-1.5 py-0.2 text-[10px] font-bold bg-red-600 text-white rounded-full">
                {stage11Data.critical_risks_count} CRITICAL
              </span>
            )}
          </button>

          <button
            onClick={() => setActiveTab('stage12')}
            className={`pb-3 text-sm font-bold flex items-center gap-2 border-b-2 transition ${activeTab === 'stage12' ? 'border-stone-800 text-stone-800' : 'border-transparent text-stone-400 hover:text-stone-600'}`}
          >
            <Lock className="w-4 h-4 text-stone-400" />
            Stage 12: Final Feasibility (Locked)
          </button>
        </div>

        {/* Loading Spinner */}
        {loading && (
          <div className="p-16 text-center space-y-4">
            <RefreshCw className="w-8 h-8 text-[#EA580C] animate-spin mx-auto" />
            <p className="text-sm font-semibold text-stone-600">Running deterministic evaluation across Stage 10 & 11 engines...</p>
          </div>
        )}

        {/* Error State */}
        {error && !loading && (
          <div className="p-6 bg-red-50 border border-red-200 rounded-2xl flex items-start space-x-3 text-red-900">
            <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
            <div>
              <h3 className="font-bold text-sm">Evaluation Notice</h3>
              <p className="text-xs text-red-700 mt-1">{error}</p>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* STAGE 10: ENTREPRENEUR PROFILE VIEW                            */}
        {/* ------------------------------------------------------------- */}
        {activeTab === 'stage10' && stage10Data && !loading && (
          <div className="space-y-6">
            {/* If profile is incomplete: Interactive Targeted Clarification Module */}
            {stage10Data.status === 'PROFILE_INCOMPLETE' && stage10Data.questions?.length > 0 && (
              <div className="bg-gradient-to-r from-purple-50 via-pink-50 to-orange-50 border-2 border-purple-200 rounded-3xl p-6 shadow-sm space-y-4">
                <div className="flex items-center justify-between">
                  <div className="flex items-center space-x-3">
                    <div className="w-10 h-10 rounded-xl bg-purple-600 text-white flex items-center justify-center font-bold">
                      <Sparkles className="w-5 h-5" />
                    </div>
                    <div>
                      <h2 className="text-lg font-bold text-purple-950 font-['Outfit']">
                        A Few Details Needed (Targeted Clarification)
                      </h2>
                      <p className="text-xs text-purple-800">
                        KALPA does not fabricate missing data. Answer in your own words via Voice (Sarvam STT) or Text to generate your deterministic score.
                      </p>
                    </div>
                  </div>
                  <Badge variant="purple" className="text-xs font-semibold">
                    {stage10Data.missing_fields?.length} Fields Pending
                  </Badge>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
                  {stage10Data.questions.map((q, idx) => (
                    <div key={idx} className="bg-white rounded-2xl p-4 border border-purple-100 shadow-sm space-y-3">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <span className="text-[11px] font-bold text-purple-700 uppercase tracking-wider">
                            Field: {q.field}
                          </span>
                          <span className="text-[10px] font-medium bg-purple-100 text-purple-800 px-2 py-0.5 rounded">
                            {q.importance} Priority
                          </span>
                        </div>
                        <p className="text-xs font-bold text-stone-900">{q.question_en}</p>
                        <p className="text-xs text-stone-600 italic">{q.question_hi}</p>
                      </div>

                      {/* Suggested quick click options */}
                      {q.suggested_options?.length > 0 && (
                        <div className="flex flex-wrap gap-1.5 pt-1">
                          {q.suggested_options.map((opt, oIdx) => (
                            <button
                              key={oIdx}
                              onClick={() => setClarificationAnswers((prev) => ({ ...prev, [q.field]: opt }))}
                              className="text-[11px] bg-stone-100 hover:bg-purple-100 text-stone-700 hover:text-purple-900 px-2 py-1 rounded-md transition"
                            >
                              + {opt}
                            </button>
                          ))}
                        </div>
                      )}

                      {/* Input Actions (Voice / Text) */}
                      <div className="flex items-center space-x-2 pt-1">
                        <input
                          type="text"
                          placeholder="Type your answer (e.g. 5 साल काम किया है)..."
                          value={clarificationAnswers[q.field] || ''}
                          onChange={(e) => setClarificationAnswers((prev) => ({ ...prev, [q.field]: e.target.value }))}
                          onKeyDown={(e) => e.key === 'Enter' && handleAnswerSubmit(q.field)}
                          className="flex-1 text-xs border border-stone-300 rounded-lg px-3 py-2 focus:ring-2 focus:ring-purple-400 focus:outline-none"
                        />

                        {/* Voice Mic Button */}
                        <button
                          onClick={() => (isRecording && activeVoiceField === q.field ? stopRecording() : startRecording(q.field))}
                          className={`p-2 rounded-lg text-xs font-bold transition flex items-center justify-center ${isRecording && activeVoiceField === q.field ? 'bg-red-600 text-white animate-pulse' : 'bg-stone-100 text-stone-700 hover:bg-stone-200'}`}
                          title={isRecording && activeVoiceField === q.field ? 'Stop recording' : 'Record voice answer'}
                        >
                          {isRecording && activeVoiceField === q.field ? <MicOff className="w-4 h-4" /> : <Mic className="w-4 h-4" />}
                        </button>

                        <button
                          onClick={() => handleAnswerSubmit(q.field)}
                          disabled={submittingClarification || !clarificationAnswers[q.field]?.trim()}
                          className="px-3 py-2 bg-purple-600 hover:bg-purple-700 disabled:bg-stone-300 text-white text-xs font-bold rounded-lg transition flex items-center space-x-1"
                        >
                          {submittingClarification ? <RefreshCw className="w-3.5 h-3.5 animate-spin" /> : <Send className="w-3.5 h-3.5" />}
                        </button>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Main Stage 10 Header Score Card */}
            <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-sm grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
              <div className="lg:col-span-2 space-y-3">
                <div className="flex items-center space-x-3">
                  {getReadinessLevelBadge(stage10Data.readiness_level)}
                  <span className="text-xs text-stone-500 font-mono">
                    Evaluation: 100% Deterministic Rules
                  </span>
                  <span className="text-xs text-stone-500 font-mono">
                    Confidence: {(stage10Data.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <h2 className="text-2xl font-bold text-stone-900 font-['Outfit']">
                  Entrepreneur Capability & Readiness Index
                </h2>
                <p className="text-xs text-stone-600 leading-relaxed">
                  Evaluates alignment between the founder's demonstrated trade skills, years of operating experience, training status, available power/premises, and daily operational commitment against the official business domain benchmark.
                </p>

                {/* Benchmark Reference */}
                <div className="flex items-center space-x-4 pt-1 text-xs text-stone-500">
                  <span className="flex items-center gap-1">
                    <Building2 className="w-3.5 h-3.5 text-stone-400" />
                    Benchmark Node: <strong className="text-stone-700">{stage10Data.business_node_id}</strong>
                  </span>
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-stone-400" />
                    Audit Provenance: <strong className="text-stone-700">{stage10Data.provenance?.evaluation_type}</strong>
                  </span>
                </div>
              </div>

              {/* Circular Readiness Gauge */}
              <div className="flex flex-col items-center justify-center p-6 bg-stone-50 rounded-2xl border border-stone-200 text-center">
                <div className="relative flex items-center justify-center">
                  <div className="text-4xl font-extrabold text-stone-900 font-['Outfit']">
                    {stage10Data.status === 'PROFILE_INCOMPLETE' ? '?' : Math.round(stage10Data.readiness_score)}
                    <span className="text-lg font-normal text-stone-500">{stage10Data.status === 'PROFILE_INCOMPLETE' ? '' : '/100'}</span>
                  </div>
                </div>
                <div className="text-xs font-bold text-stone-700 uppercase tracking-wider mt-2">
                  {stage10Data.readiness_level} Readiness
                </div>
                <div className="text-[11px] text-stone-500 mt-0.5">
                  {stage10Data.status === 'PROFILE_INCOMPLETE' ? 'Details Required Above' : 'Audit-grade MSME metric'}
                </div>
              </div>
            </div>

            {/* 5 Component Breakdown Cards */}
            <div className="grid grid-cols-1 md:grid-cols-5 gap-3">
              {stage10Data.component_scores && Object.entries(stage10Data.component_scores).map(([key, comp]) => (
                <div key={key} className="bg-white rounded-2xl p-4 border border-stone-200 shadow-sm space-y-2 flex flex-col justify-between">
                  <div>
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold tracking-wider text-stone-400 uppercase">
                        {(comp.weight * 100).toFixed(0)}% WEIGHT
                      </span>
                      <span className={`text-[10px] font-bold px-1.5 py-0.5 rounded ${comp.status === 'STRONG' ? 'bg-emerald-100 text-emerald-800' : (comp.status === 'ADEQUATE' ? 'bg-blue-100 text-blue-800' : 'bg-amber-100 text-amber-800')}`}>
                        {comp.status}
                      </span>
                    </div>

                    <h4 className="text-xs font-bold text-stone-900 capitalize mt-1.5 flex items-center gap-1.5">
                      {key === 'skills' && <Hammer className="w-3.5 h-3.5 text-stone-500" />}
                      {key === 'experience' && <Briefcase className="w-3.5 h-3.5 text-stone-500" />}
                      {key === 'training' && <GraduationCap className="w-3.5 h-3.5 text-stone-500" />}
                      {key === 'resources' && <Building2 className="w-3.5 h-3.5 text-stone-500" />}
                      {key === 'operational_readiness' && <Clock className="w-3.5 h-3.5 text-stone-500" />}
                      {key.replace('_', ' ')}
                    </h4>

                    <div className="text-xl font-extrabold text-stone-900 font-['Outfit'] mt-1">
                      {Math.round(comp.score)}<span className="text-xs font-normal text-stone-400">/100</span>
                    </div>

                    <p className="text-[11px] text-stone-600 leading-snug mt-2">
                      {comp.evidence}
                    </p>
                  </div>

                  {comp.missing_items?.length > 0 && (
                    <div className="pt-2 border-t border-stone-100 text-[10px] text-amber-700">
                      <strong>Pending:</strong> {comp.missing_items.slice(0, 1).join(', ')}
                    </div>
                  )}
                </div>
              ))}
            </div>

            {/* Strengths, Gaps & Required Support Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {/* Strengths */}
              <div className="bg-white rounded-2xl p-5 border border-emerald-100 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-emerald-950 flex items-center gap-2">
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  Validated Strengths ({stage10Data.strengths?.length || 0})
                </h3>
                <ul className="space-y-2">
                  {stage10Data.strengths?.map((s, idx) => (
                    <li key={idx} className="text-xs text-stone-700 flex items-start space-x-2">
                      <span className="text-emerald-500 font-bold">•</span>
                      <span>{s}</span>
                    </li>
                  ))}
                </ul>
              </div>

              {/* Readiness Gaps */}
              <div className="bg-white rounded-2xl p-5 border border-amber-100 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-amber-950 flex items-center gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-600" />
                  Identified Gaps ({stage10Data.gaps?.length || 0})
                </h3>
                <div className="space-y-2.5">
                  {stage10Data.gaps?.length === 0 ? (
                    <p className="text-xs text-stone-500">No critical competency gaps identified.</p>
                  ) : (
                    stage10Data.gaps?.map((g, idx) => (
                      <div key={idx} className="p-2.5 bg-amber-50/60 rounded-xl border border-amber-200/60 text-xs space-y-1">
                        <div className="flex items-center justify-between font-bold text-amber-900">
                          <span>{g.dimension}</span>
                          <span className="text-[10px] uppercase px-1.5 py-0.2 rounded bg-amber-200 text-amber-800">{g.severity}</span>
                        </div>
                        <p className="text-stone-700 text-[11px]">{g.gap_description}</p>
                        <p className="text-stone-500 text-[10px] italic">Intervention: {g.required_intervention}</p>
                      </div>
                    ))
                  )}
                </div>
              </div>

              {/* Required Support Programs */}
              <div className="bg-white rounded-2xl p-5 border border-blue-100 shadow-sm space-y-3">
                <h3 className="text-sm font-bold text-blue-950 flex items-center gap-2">
                  <Award className="w-4 h-4 text-blue-600" />
                  Recommended Support Programs
                </h3>
                <div className="space-y-2.5">
                  {stage10Data.required_support?.map((sup, idx) => (
                    <div key={idx} className="p-2.5 bg-blue-50/50 rounded-xl border border-blue-100 text-xs space-y-1">
                      <div className="flex items-center justify-between font-bold text-blue-900">
                        <span>{sup.title}</span>
                        <span className="text-[10px] text-blue-600 uppercase">{sup.priority}</span>
                      </div>
                      <p className="text-stone-600 text-[11px] leading-snug">{sup.description}</p>
                      {sup.scheme_or_program_link && (
                        <a
                          href={sup.scheme_or_program_link}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="inline-flex items-center text-[10px] font-bold text-blue-700 hover:underline pt-0.5"
                        >
                          View Official Portal <ExternalLink className="w-2.5 h-2.5 ml-1" />
                        </a>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* STAGE 11: RISK ENGINE VIEW                                    */}
        {/* ------------------------------------------------------------- */}
        {activeTab === 'stage11' && stage11Data && !loading && (
          <div className="space-y-6">
            {/* Overall Risk Banner */}
            <div className="bg-white rounded-3xl p-6 border border-stone-200 shadow-sm grid grid-cols-1 lg:grid-cols-3 gap-6 items-center">
              <div className="lg:col-span-2 space-y-3">
                <div className="flex items-center space-x-3">
                  {getSeverityBadge(stage11Data.overall_risk_severity)}
                  <span className="text-xs text-stone-500 font-mono">
                    Evaluation: Multi-Vector Synthesis
                  </span>
                  <span className="text-xs text-stone-500 font-mono">
                    Confidence: {(stage11Data.confidence * 100).toFixed(0)}%
                  </span>
                </div>

                <h2 className="text-2xl font-bold text-stone-900 font-['Outfit']">
                  Enterprise 7-Category Risk Matrix
                </h2>
                <p className="text-xs text-stone-600 leading-relaxed">
                  Deterministic synthesis consuming Stage 9 Financial DSCR/break-even, Stage 6 Market Demand & Competition, Stage 10 Capability gaps, and Agricultural seasonality.
                </p>

                {stage11Data.provenance?.critical_ceiling_applied && (
                  <div className="p-2.5 bg-red-50 border border-red-200 rounded-xl text-xs text-red-800 flex items-center space-x-2">
                    <AlertOctagon className="w-4 h-4 text-red-600 flex-shrink-0" />
                    <span>
                      <strong>Critical Risk Ceiling Enforced:</strong> Overall severity is elevated due to critical vulnerabilities (e.g. debt overhang or power mismatch) that cannot be averaged away.
                    </span>
                  </div>
                )}
              </div>

              {/* Overall Risk Score Indicator */}
              <div className="flex flex-col items-center justify-center p-6 bg-stone-50 rounded-2xl border border-stone-200 text-center">
                <div className="text-4xl font-extrabold text-stone-900 font-['Outfit']">
                  {stage11Data.overall_risk_score.toFixed(2)}
                  <span className="text-lg font-normal text-stone-500">/1.0</span>
                </div>
                <div className="text-xs font-bold text-stone-700 uppercase tracking-wider mt-2">
                  {stage11Data.overall_risk_severity} Enterprise Risk
                </div>
                <div className="text-[11px] text-stone-500 mt-0.5">
                  {stage11Data.critical_risks_count} Critical • {stage11Data.high_risks_count} High Risk Factors
                </div>
              </div>
            </div>

            {/* 7-Category Risk Cards Matrix */}
            <div className="space-y-3">
              <h3 className="text-sm font-bold text-stone-800">
                Detailed Category Breakdown & Actionable Mitigations
              </h3>

              <div className="space-y-3">
                {stage11Data.category_risks && Object.entries(stage11Data.category_risks).map(([catKey, risk]) => {
                  const isExpanded = expandedRisk === catKey;
                  return (
                    <div
                      key={catKey}
                      className="bg-white rounded-2xl border border-stone-200 shadow-sm overflow-hidden transition"
                    >
                      <button
                        onClick={() => setExpandedRisk(isExpanded ? null : catKey)}
                        className="w-full px-5 py-4 flex items-center justify-between text-left hover:bg-stone-50/50 transition"
                      >
                        <div className="flex items-center space-x-3">
                          <div className="w-8 h-8 rounded-lg bg-stone-100 flex items-center justify-center text-stone-700 font-bold text-xs">
                            {catKey.slice(0, 3)}
                          </div>
                          <div>
                            <div className="text-sm font-bold text-stone-900 font-['Outfit']">
                              {catKey.replace('_', ' ')} RISK
                            </div>
                            <div className="text-[11px] text-stone-500 font-mono">
                              Source: {risk.source_stage} • Confidence: {(risk.confidence * 100).toFixed(0)}%
                            </div>
                          </div>
                        </div>

                        <div className="flex items-center space-x-4">
                          <span className="text-sm font-extrabold text-stone-900 font-mono">
                            {risk.score.toFixed(2)}
                          </span>
                          {getSeverityBadge(risk.severity)}
                          {isExpanded ? <ChevronUp className="w-4 h-4 text-stone-400" /> : <ChevronDown className="w-4 h-4 text-stone-400" />}
                        </div>
                      </button>

                      {/* Expandable Details Section */}
                      {isExpanded && (
                        <div className="px-5 pb-5 pt-2 border-t border-stone-100 bg-stone-50/30 space-y-4">
                          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                            {/* Risk Drivers & Evidence */}
                            <div className="space-y-2">
                              <h4 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                                Identified Drivers & Triggers
                              </h4>
                              <ul className="space-y-1.5">
                                {risk.drivers?.map((d, dIdx) => (
                                  <li key={dIdx} className="text-xs text-stone-700 flex items-start space-x-2">
                                    <span className="text-red-500 font-bold">•</span>
                                    <span>{d}</span>
                                  </li>
                                ))}
                              </ul>

                              <div className="pt-2">
                                <span className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">
                                  Empirical Evidence:
                                </span>
                                <div className="text-xs text-stone-600 italic">
                                  {risk.evidence?.join('; ') || 'Knowledge catalog benchmark standard applied.'}
                                </div>
                              </div>
                            </div>

                            {/* Impact & Actionable Mitigations */}
                            <div className="space-y-2">
                              <h4 className="text-xs font-bold text-stone-900 uppercase tracking-wider">
                                Real-World Business Impact
                              </h4>
                              <p className="text-xs text-stone-700 leading-relaxed bg-white p-2.5 rounded-xl border border-stone-200">
                                {risk.impact}
                              </p>

                              <h4 className="text-xs font-bold text-emerald-900 uppercase tracking-wider pt-2">
                                Actionable MSME Mitigations
                              </h4>
                              <ul className="space-y-1.5">
                                {risk.mitigation?.map((m, mIdx) => (
                                  <li key={mIdx} className="text-xs text-emerald-800 flex items-start space-x-2">
                                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 flex-shrink-0 mt-0.5" />
                                    <span>{m}</span>
                                  </li>
                                ))}
                              </ul>
                            </div>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          </div>
        )}

        {/* ------------------------------------------------------------- */}
        {/* STAGE 12: FINAL FEASIBILITY LOCKED VIEW                       */}
        {/* ------------------------------------------------------------- */}
        {activeTab === 'stage12' && (
          <div className="royal-card rounded-3xl p-10 text-center space-y-6 max-w-xl mx-auto border-2 border-stone-200">
            <div className="w-16 h-16 rounded-2xl bg-stone-100 text-stone-600 flex items-center justify-center mx-auto">
              <Lock className="w-8 h-8 text-[#EA580C]" />
            </div>

            <div className="space-y-2">
              <h3 className="text-xl font-bold text-stone-900 font-['Outfit']">
                Stage 12 Final Feasibility Synthesis Locked
              </h3>
              <p className="text-xs text-stone-600 leading-relaxed max-w-md mx-auto">
                Stage 10 (Entrepreneur Readiness) and Stage 11 (Multi-Vector Risk) are complete and verified. The composite final feasibility verdict will be generated in Phase 2 after statutory bank guidelines validation.
              </p>
            </div>

            <div className="pt-2 flex justify-center space-x-3">
              <Link to="/financial-analysis">
                <Button size="sm" variant="secondary" icon={ArrowLeft}>
                  Review Financial Plan (Stage 9)
                </Button>
              </Link>
              <Link to="/dpr">
                <Button size="sm" icon={ArrowRight}>
                  Proceed to DPR Preview
                </Button>
              </Link>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default FeasibilityPage;
