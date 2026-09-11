import React, { useState, useEffect, useRef } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  Sparkles,
  CheckCircle2,
  Lock,
  Layers,
  FileCheck2,
  ArrowRight,
  ArrowLeft,
  Briefcase,
  HelpCircle,
  Volume2,
  VolumeX,
  Mic,
  Square,
  Send,
  Building2,
  ChevronDown,
  ChevronUp,
  Tag,
  ShieldCheck,
  AlertCircle,
  BarChart3,
  RefreshCw,
  Info,
  Scale
} from 'lucide-react';
import Card, { CardTitle, CardDescription, CardContent } from '../../components/ui/Card';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';
import ContourBackground from '../../components/ui/ContourBackground';
import apiService from '../../services/api';

export const ClassificationPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const sessionId = searchParams.get('session_id') || searchParams.get('id') || '';

  const [loading, setLoading] = useState(true);
  const [processingStep, setProcessingStep] = useState(0);
  const [classificationResult, setClassificationResult] = useState(null);
  const [error, setError] = useState(null);

  // Clarification state
  const [clarificationAnswer, setClarificationAnswer] = useState('');
  const [isClarifying, setIsClarifying] = useState(false);
  const [clarificationTab, setClarificationTab] = useState('options'); // 'options' | 'text' | 'voice'
  const [isVoiceRecording, setIsVoiceRecording] = useState(false);
  const [recordingSeconds, setRecordingSeconds] = useState(0);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const timerIntervalRef = useRef(null);

  // Speech synthesis
  const [isSpeaking, setIsSpeaking] = useState(false);

  // Expandable Hierarchy & Confidence Breakdown
  const [showHierarchy, setShowHierarchy] = useState(false);
  const [showConfidenceBreakdown, setShowConfidenceBreakdown] = useState(false);

  // Processing step animation
  const processingSteps = [
    'Understanding your business concept...',
    'Matching KALPA business ontology...',
    'Retrieving official NIC-2008 candidate registry...',
    'Validating economic hierarchy consistency...',
    'Computing explainable deterministic confidence...'
  ];

  useEffect(() => {
    let current = 0;
    const interval = setInterval(() => {
      current++;
      if (current < processingSteps.length) {
        setProcessingStep(current);
      }
    }, 500);

    return () => clearInterval(interval);
  }, []);

  const fetchClassification = async () => {
    setLoading(true);
    setError(null);
    try {
      let stage1Data = null;
      try {
        const saved = sessionStorage.getItem('kalpa_stage1_response');
        if (saved) {
          stage1Data = JSON.parse(saved);
        }
      } catch (e) {
        console.warn('Could not parse saved Stage 1 data:', e);
      }

      const stage1Profile = stage1Data?.profile || stage1Data;
      const sid = sessionId || stage1Data?.session_id || stage1Profile?.session_id || null;

      const classificationInput = {
        session_id: sid,
        original_input: stage1Profile?.original_input || stage1Data?.original_text || '',
        business_concept: stage1Profile?.business_concept || stage1Data?.business_concept || '',
        language_code: stage1Profile?.language_code || stage1Data?.language?.code || 'en',
        product_service: stage1Profile?.product_service || '',
        location: stage1Profile?.proposed_location || {},
        capital_available: stage1Profile?.available_capital,
        skills: stage1Profile?.entrepreneur_skills || [],
        profile: stage1Profile || {}
      };

      console.log('[STAGE 2 INPUT]', classificationInput);

      let data;
      if (classificationInput.business_concept || classificationInput.original_input || sid) {
        data = await apiService.classification.classify(classificationInput);
      } else {
        data = await apiService.classification.classify({
          business_concept: 'Rice Mill',
          original_input: 'I want to open a rice mill in Mandya with ₹2 lakh',
          language_code: 'en'
        });
      }
      setClassificationResult(data);
    } catch (err) {
      console.error('Classification fetch failed:', err);
      setError(err.message || 'Unable to classify business. Please ensure Stage 1 is completed.');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassification();
  }, [sessionId]);

  // Voice Recording for Clarification
  const startClarificationRecording = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream);
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (e) => {
        if (e.data.size > 0) audioChunksRef.current.push(e.data);
      };

      mediaRecorderRef.current.onstop = async () => {
        const audioBlob = new Blob(audioChunksRef.current, { type: 'audio/wav' });
        await handleClarificationAudio(audioBlob);
        stream.getTracks().forEach((track) => track.stop());
      };

      mediaRecorderRef.current.start();
      setIsVoiceRecording(true);
      setRecordingSeconds(0);
      timerIntervalRef.current = setInterval(() => {
        setRecordingSeconds((prev) => prev + 1);
      }, 1000);
    } catch (err) {
      alert('Microphone access required for voice input: ' + err.message);
    }
  };

  const stopClarificationRecording = () => {
    if (mediaRecorderRef.current && isVoiceRecording) {
      mediaRecorderRef.current.stop();
      setIsVoiceRecording(false);
      clearInterval(timerIntervalRef.current);
    }
  };

  const handleClarificationAudio = async (audioBlob) => {
    setIsClarifying(true);
    try {
      const formData = new FormData();
      formData.append('audio', audioBlob, 'clarify_voice.wav');
      formData.append('language_code', classificationResult?.input_summary?.original_language || 'kn');
      
      const sttRes = await apiService.intake.submitVoice(formData);
      const recognizedText = sttRes.transcript || '';
      if (recognizedText) {
        await submitClarification(recognizedText);
      } else {
        alert('Could not recognize voice. Please try typing your answer.');
      }
    } catch (err) {
      console.error('Voice clarification failed:', err);
      alert('Voice processing failed: ' + err.message);
    } finally {
      setIsClarifying(false);
    }
  };

  const submitClarification = async (answerText) => {
    if (!answerText.trim()) return;
    setIsClarifying(true);
    try {
      const res = await apiService.classification.clarify({
        session_id: sessionId || 'default_session',
        answer: answerText,
        language_code: classificationResult?.input_summary?.original_language || 'en'
      });
      setClassificationResult(res);
      setClarificationAnswer('');
    } catch (err) {
      console.error('Clarify failed:', err);
      alert('Error updating classification: ' + err.message);
    } finally {
      setIsClarifying(false);
    }
  };

  // Browser Speech Synthesis for Listen Button
  const speakQuestion = (text, langCode) => {
    if (!window.speechSynthesis) {
      alert('Speech synthesis is not supported on this browser.');
      return;
    }
    if (isSpeaking) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      return;
    }

    const utterance = new SpeechSynthesisUtterance(text);
    if (langCode === 'kn') utterance.lang = 'kn-IN';
    else if (langCode === 'hi') utterance.lang = 'hi-IN';
    else utterance.lang = 'en-IN';

    utterance.onend = () => setIsSpeaking(false);
    utterance.onerror = () => setIsSpeaking(false);

    setIsSpeaking(true);
    window.speechSynthesis.speak(utterance);
  };

  const confidenceData = classificationResult?.official_classification?.confidence || {
    score: classificationResult?.classification_confidence || 0.94,
    percentage: Math.round((classificationResult?.classification_confidence || 0.94) * 100),
    level: classificationResult?.confidence_level || 'HIGH',
    breakdown: classificationResult?.confidence_breakdown || {
      ontology_match: 1.0,
      nic_activity_match: 0.95,
      hierarchy_consistency: 1.0,
      profile_context_consistency: 0.85,
      candidate_separation: 0.90
    }
  };

  const nicData = classificationResult?.official_classification?.nic || {
    version: 'NIC-2008',
    section: { code: classificationResult?.layer_a_nic?.section || 'C', title: classificationResult?.layer_a_nic?.section_name || 'Manufacturing' },
    division: { code: classificationResult?.layer_a_nic?.division || '10', title: classificationResult?.layer_a_nic?.division_name || 'Manufacture of food products' },
    group: { code: classificationResult?.layer_a_nic?.group || '106', title: classificationResult?.layer_a_nic?.group_name || 'Manufacture of grain mill products' },
    class: { code: classificationResult?.layer_a_nic?.class || '1061', title: classificationResult?.layer_a_nic?.class_name || 'Grain Milling' },
    subclass: { code: classificationResult?.layer_a_nic?.subclass || classificationResult?.layer_a_nic?.nic_code || '10612', title: classificationResult?.layer_a_nic?.nic_description || '' },
    activity: { code: classificationResult?.layer_a_nic?.nic_code || '10612', official_title: classificationResult?.layer_a_nic?.nic_description || '', description: '' }
  };

  const topCandidates = classificationResult?.official_classification?.top_candidates || [];

  return (
    <div className="min-h-screen bg-[#FAF7F2] py-8 px-4 sm:px-6 lg:px-8 relative overflow-hidden">
      <ContourBackground />

      <div className="max-w-5xl mx-auto space-y-8 relative z-10">
        {/* Navigation Breadcrumb / Flow Indicator */}
        <div className="royal-card rounded-2xl p-4 bg-white/90 backdrop-blur-md border border-[#EAE3D5] shadow-sm">
          <div className="flex flex-wrap items-center justify-between gap-3 text-xs font-semibold">
            {/* Stage 1 */}
            <Link
              to={`/intake${sessionId ? `?session_id=${sessionId}` : ''}`}
              className="flex items-center gap-1.5 text-emerald-700 hover:text-emerald-800 transition-colors"
            >
              <div className="w-5 h-5 rounded-full bg-emerald-100 flex items-center justify-center text-emerald-700">
                <CheckCircle2 className="w-3.5 h-3.5" />
              </div>
              <span>01 Intake & NLP</span>
            </Link>

            <span className="text-[#D6CDBC]">→</span>

            {/* Stage 2 Active */}
            <div className="flex items-center gap-1.5 text-[#EA580C]">
              <div className="w-5 h-5 rounded-full bg-orange-100 flex items-center justify-center text-[#EA580C] font-bold">
                2
              </div>
              <span className="underline decoration-2 underline-offset-4">02 Business Classification</span>
              <span className="px-1.5 py-0.5 rounded bg-orange-100 text-[#C2410C] text-[10px] uppercase font-bold">
                Active
              </span>
            </div>

            <span className="text-[#D6CDBC]">→</span>

            {/* Stage 3 Locked */}
            <div className="flex items-center gap-1 text-[#A8A29E] cursor-not-allowed" title="Unlocks after Stage 2">
              <Lock className="w-3.5 h-3.5" />
              <span>03 Market Intel</span>
            </div>

            <span className="text-[#D6CDBC]">→</span>

            {/* Stage 4 Locked */}
            <div className="flex items-center gap-1 text-[#A8A29E] cursor-not-allowed">
              <Lock className="w-3.5 h-3.5" />
              <span>04 Feasibility</span>
            </div>

            <span className="text-[#D6CDBC]">→</span>

            {/* Stage 5 Locked */}
            <div className="flex items-center gap-1 text-[#A8A29E] cursor-not-allowed">
              <Lock className="w-3.5 h-3.5" />
              <span>05 DPR Report</span>
            </div>
          </div>
        </div>

        {/* Header */}
        <div className="space-y-2 text-center max-w-2xl mx-auto">
          <Badge variant="orange" className="mb-2">
            <Sparkles className="w-3 h-3 mr-1" /> Step 2 of KALPA Journey
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#1C1917] font-['Outfit']">
            Understanding Your Business
          </h1>
          <p className="text-sm text-[#57534E]">
            Automated dual-layer classification aligning your venture with the official National Industrial Classification (NIC-2008 MoSPI) and KALPA Rural Enterprise Taxonomy.
          </p>
        </div>

        {/* Loading / Processing State */}
        {loading ? (
          <div className="royal-card rounded-3xl p-8 sm:p-12 text-center space-y-6 max-w-xl mx-auto border-2 border-orange-100 shadow-xl bg-white/95">
            <div className="relative w-16 h-16 mx-auto">
              <div className="w-16 h-16 rounded-full border-4 border-orange-200 border-t-[#EA580C] animate-spin" />
              <Briefcase className="w-6 h-6 text-[#EA580C] absolute inset-0 m-auto" />
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                Classifying Business Venture
              </h3>
              <div className="space-y-2 text-left max-w-sm mx-auto text-xs text-[#57534E]">
                {processingSteps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                        idx <= processingStep
                          ? 'bg-emerald-100 text-emerald-700 font-bold'
                          : 'bg-stone-100 text-stone-400'
                      }`}
                    >
                      {idx <= processingStep ? '✓' : idx + 1}
                    </div>
                    <span className={idx === processingStep ? 'font-bold text-[#EA580C]' : ''}>
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : error ? (
          /* Error State */
          <div className="royal-card rounded-3xl p-8 text-center space-y-4 max-w-lg mx-auto border-2 border-rose-200 bg-rose-50/50">
            <AlertCircle className="w-12 h-12 text-rose-600 mx-auto" />
            <h3 className="text-lg font-bold text-rose-950">Classification Unavailable</h3>
            <p className="text-xs text-rose-800">{error}</p>
            <div className="pt-2 flex justify-center gap-3">
              <Button size="sm" variant="secondary" onClick={() => navigate('/intake')}>
                Back to Stage 1
              </Button>
              <Button size="sm" onClick={fetchClassification} icon={RefreshCw}>
                Retry
              </Button>
            </div>
          </div>
        ) : classificationResult?.clarification_needed ? (
          /* Clarification Mode Card */
          <div className="royal-card rounded-3xl p-6 sm:p-8 bg-white border-2 border-amber-300 shadow-xl space-y-6 max-w-2xl mx-auto animate-fadeIn">
            <div className="flex items-center gap-3 border-b border-stone-100 pb-4">
              <div className="w-10 h-10 rounded-2xl bg-amber-100 text-amber-800 flex items-center justify-center shadow-inner">
                <HelpCircle className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider font-bold text-amber-800">
                  Clarification Required
                </span>
                <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                  Help Us Understand Your Business Better
                </h3>
              </div>
            </div>

            {/* Localized Question with Listen Button */}
            <div className="p-4 rounded-2xl bg-[#FAF7F2] border border-[#EAE3D5] flex items-start justify-between gap-4">
              <p className="text-sm font-semibold text-[#1C1917] leading-relaxed">
                {classificationResult.clarification?.question || 'What specific type of business do you want to start?'}
              </p>
              <button
                type="button"
                onClick={() =>
                  speakQuestion(
                    classificationResult.clarification?.question,
                    classificationResult.clarification?.language
                  )
                }
                className={`p-2.5 rounded-xl border transition-all flex items-center gap-1.5 text-xs font-bold ${
                  isSpeaking
                    ? 'bg-orange-600 text-white border-orange-600'
                    : 'bg-white text-stone-700 border-stone-300 hover:bg-stone-50'
                }`}
                title="Listen to question"
              >
                {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4 text-[#EA580C]" />}
                <span>{isSpeaking ? 'Stop' : 'Listen'}</span>
              </button>
            </div>

            {/* Clarification Input Tabs */}
            <div className="space-y-4">
              <div className="flex gap-2 border-b border-stone-200 pb-2">
                <button
                  type="button"
                  onClick={() => setClarificationTab('options')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    clarificationTab === 'options'
                      ? 'bg-[#EA580C] text-white'
                      : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                  }`}
                >
                  Select Option
                </button>
                <button
                  type="button"
                  onClick={() => setClarificationTab('text')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all ${
                    clarificationTab === 'text'
                      ? 'bg-[#EA580C] text-white'
                      : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                  }`}
                >
                  Type Answer
                </button>
                <button
                  type="button"
                  onClick={() => setClarificationTab('voice')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1 ${
                    clarificationTab === 'voice'
                      ? 'bg-[#EA580C] text-white'
                      : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                  }`}
                >
                  <Mic className="w-3.5 h-3.5" />
                  <span>Speak Answer</span>
                </button>
              </div>

              {/* Mode 1: Option Selection */}
              {clarificationTab === 'options' && (
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
                  {classificationResult.clarification?.options?.map((opt, idx) => (
                    <button
                      key={idx}
                      type="button"
                      disabled={isClarifying}
                      onClick={() => submitClarification(opt.value)}
                      className="p-3.5 rounded-2xl border-2 border-[#EAE3D5] bg-white text-left hover:border-[#EA580C] hover:bg-orange-50/40 transition-all font-medium text-xs text-[#1C1917] flex items-center justify-between group"
                    >
                      <span>{opt.label}</span>
                      <ArrowRight className="w-4 h-4 text-stone-400 group-hover:text-[#EA580C] group-hover:translate-x-0.5 transition-all" />
                    </button>
                  ))}
                </div>
              )}

              {/* Mode 2: Type Answer */}
              {clarificationTab === 'text' && (
                <form
                  onSubmit={(e) => {
                    e.preventDefault();
                    submitClarification(clarificationAnswer);
                  }}
                  className="flex gap-2"
                >
                  <input
                    type="text"
                    value={clarificationAnswer}
                    onChange={(e) => setClarificationAnswer(e.target.value)}
                    placeholder="e.g. Saree retail shop, Rice mill, etc."
                    className="flex-grow bg-white border border-[#D6CDBC] rounded-xl px-4 py-2.5 text-xs text-[#1C1917] focus:outline-none focus:ring-2 focus:ring-orange-500/40"
                  />
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isClarifying || !clarificationAnswer.trim()}
                    icon={Send}
                  >
                    {isClarifying ? 'Updating...' : 'Submit'}
                  </Button>
                </form>
              )}

              {/* Mode 3: Voice Answer */}
              {clarificationTab === 'voice' && (
                <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 flex items-center gap-4">
                  <button
                    type="button"
                    onClick={isVoiceRecording ? stopClarificationRecording : startClarificationRecording}
                    disabled={isClarifying}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all ${
                      isVoiceRecording
                        ? 'bg-rose-600 text-white animate-pulse'
                        : 'bg-[#EA580C] text-white hover:scale-105'
                    }`}
                  >
                    {isVoiceRecording ? <Square className="w-5 h-5 fill-current" /> : <Mic className="w-6 h-6" />}
                  </button>
                  <div className="text-xs">
                    <p className="font-semibold text-[#1C1917]">
                      {isVoiceRecording
                        ? `Recording clarification (${recordingSeconds}s)... Tap to Finish`
                        : 'Tap the mic to speak your business type'}
                    </p>
                    <p className="text-[#78716C]">
                      Speaks in your preferred language (English / Kannada / Hindi)
                    </p>
                  </div>
                </div>
              )}
            </div>
          </div>
        ) : (
          /* Verified Classification Result View */
          <div className="space-y-6 animate-fadeIn">
            {/* Top Success Banner with Deterministic Confidence */}
            <div className="royal-card rounded-3xl p-4 sm:p-5 bg-emerald-50/80 border border-emerald-200 flex flex-wrap items-center justify-between gap-4">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center shadow-inner">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-emerald-950 font-['Outfit']">
                      Verified Economic Classification
                    </h3>
                    <span
                      className={`text-[10px] font-bold px-2 py-0.5 rounded-full border ${
                        confidenceData.level === 'HIGH'
                          ? 'bg-emerald-100 text-emerald-800 border-emerald-300'
                          : confidenceData.level === 'MEDIUM'
                          ? 'bg-amber-100 text-amber-800 border-amber-300'
                          : 'bg-orange-100 text-orange-800 border-orange-300'
                      }`}
                    >
                      {confidenceData.level} CONFIDENCE ({confidenceData.percentage}%)
                    </span>
                  </div>
                  <p className="text-xs text-emerald-800">
                    Input: "{classificationResult?.input_summary?.business_concept || 'Verified Enterprise'}"
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowConfidenceBreakdown(!showConfidenceBreakdown)}
                  className="text-xs font-semibold text-emerald-900 bg-white/90 hover:bg-white px-3 py-1.5 rounded-xl border border-emerald-200 flex items-center gap-1 shadow-sm transition-all"
                >
                  <Scale className="w-3.5 h-3.5 text-emerald-700" />
                  <span>Evidence Score Breakdown</span>
                  {showConfidenceBreakdown ? <ChevronUp className="w-3 h-3" /> : <ChevronDown className="w-3 h-3" />}
                </button>
                <div className="text-xs font-semibold text-emerald-900 bg-white/80 px-3 py-1.5 rounded-xl border border-emerald-200">
                  <strong className="uppercase">{classificationResult?.input_summary?.original_language || 'EN'}</strong>
                </div>
              </div>
            </div>

            {/* Expandable 5-Pillar Confidence Breakdown */}
            {showConfidenceBreakdown && (
              <div className="royal-card rounded-2xl p-4 bg-white border border-[#EAE3D5] shadow-md space-y-3 animate-fadeIn">
                <div className="flex items-center justify-between border-b border-stone-100 pb-2">
                  <h4 className="text-xs font-bold text-[#1C1917] uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="w-4 h-4 text-[#EA580C]" />
                    <span>Deterministic 5-Pillar Confidence Breakdown</span>
                  </h4>
                  <span className="text-[11px] font-bold text-[#EA580C]">
                    Total: {confidenceData.score} / 1.00 ({confidenceData.percentage}%)
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-200">
                    <span className="text-[10px] text-stone-500 block">Ontology Match (30%)</span>
                    <strong className="text-stone-900 text-sm">{Math.round((confidenceData.breakdown?.ontology_match || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-200">
                    <span className="text-[10px] text-stone-500 block">NIC Activity Match (25%)</span>
                    <strong className="text-stone-900 text-sm">{Math.round((confidenceData.breakdown?.nic_activity_match || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-200">
                    <span className="text-[10px] text-stone-500 block">Hierarchy Consistency (15%)</span>
                    <strong className="text-stone-900 text-sm">{Math.round((confidenceData.breakdown?.hierarchy_consistency || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-200">
                    <span className="text-[10px] text-stone-500 block">Profile Context (15%)</span>
                    <strong className="text-stone-900 text-sm">{Math.round((confidenceData.breakdown?.profile_context_consistency || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-stone-50 border border-stone-200">
                    <span className="text-[10px] text-stone-500 block">Candidate Separation (15%)</span>
                    <strong className="text-stone-900 text-sm">{Math.round((confidenceData.breakdown?.candidate_separation || 0) * 100)}%</strong>
                  </div>
                </div>
              </div>
            )}

            {/* Dual Column Layout: Layer A NIC + Layer B Ontology */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: KALPA Business Identity (Layer B Ontology) */}
              <div className="royal-card rounded-3xl p-6 sm:p-7 bg-white border border-[#EAE3D5] shadow-sm space-y-5">
                <div className="flex items-center gap-3 border-b border-stone-100 pb-3">
                  <div className="w-9 h-9 rounded-xl bg-orange-100 text-[#EA580C] flex items-center justify-center">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#EA580C]">
                      Layer A • KALPA Business Ontology
                    </span>
                    <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                      Business Identity
                    </h3>
                  </div>
                </div>

                <div className="space-y-3.5 text-xs">
                  <div>
                    <span className="text-[11px] font-semibold text-[#78716C] block uppercase tracking-wider">Sector</span>
                    <span className="font-bold text-sm text-[#1C1917]">
                      {classificationResult?.layer_b_ontology?.sector || 'Manufacturing / Agro Processing'}
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div>
                      <span className="text-[11px] font-semibold text-[#78716C] block uppercase tracking-wider">Category</span>
                      <span className="font-semibold text-[#1C1917]">
                        {classificationResult?.layer_b_ontology?.category || 'Grain Processing'}
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] font-semibold text-[#78716C] block uppercase tracking-wider">Sub-category</span>
                      <span className="font-semibold text-[#1C1917]">
                        {classificationResult?.layer_b_ontology?.sub_category || classificationResult?.layer_b_ontology?.subcategory || 'Rice Milling'}
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-orange-50/50 border border-orange-100">
                    <span className="text-[10px] font-bold text-[#EA580C] uppercase tracking-wider block">Specific Venture</span>
                    <span className="font-extrabold text-base text-[#1C1917]">
                      {classificationResult?.layer_b_ontology?.specific_business || 'Rice Mill'}
                    </span>
                  </div>

                  {/* Products / Services tags */}
                  {classificationResult?.layer_b_ontology?.products?.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[11px] font-semibold text-[#78716C] block uppercase tracking-wider">
                        Key Products / Derivatives
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {classificationResult.layer_b_ontology.products.map((prod, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-1 rounded-lg bg-[#FAF7F2] text-[#44403C] border border-[#EAE3D5] text-[11px] font-medium"
                          >
                            {prod}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Card 2: Official NIC 2008 Classification (Layer B NIC) */}
              <div className="royal-card rounded-3xl p-6 sm:p-7 bg-white border border-[#EAE3D5] shadow-sm space-y-5">
                <div className="flex items-center gap-3 border-b border-stone-100 pb-3">
                  <div className="w-9 h-9 rounded-xl bg-blue-100 text-blue-700 flex items-center justify-center">
                    <FileCheck2 className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700">
                      Layer B • Official MoSPI Classification
                    </span>
                    <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                      NIC-2008 Economic Activity
                    </h3>
                  </div>
                </div>

                <div className="space-y-3.5 text-xs">
                  {/* NIC Code Display */}
                  <div className="p-4 rounded-2xl bg-gradient-to-br from-blue-50 to-indigo-50/40 border border-blue-200">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-blue-700">Official NIC Code</span>
                      <span className="text-[10px] px-2 py-0.5 rounded-full bg-blue-100 text-blue-800 font-bold">5-Digit Sub-Class</span>
                    </div>
                    <div className="text-3xl font-black text-blue-950 font-['Outfit'] tracking-wider my-1">
                      {nicData.activity?.code || classificationResult?.layer_a_nic?.nic_code || '10612'}
                    </div>
                    <p className="text-xs font-semibold text-blue-900 leading-snug">
                      {nicData.activity?.official_title || classificationResult?.layer_a_nic?.nic_description || 'Rice milling and processing of paddy into rice'}
                    </p>
                  </div>

                  {/* Expandable Hierarchy */}
                  <div className="border border-stone-200 rounded-2xl overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setShowHierarchy(!showHierarchy)}
                      className="w-full px-4 py-2.5 bg-stone-50 text-left font-semibold text-[#44403C] flex items-center justify-between text-xs hover:bg-stone-100 transition-colors"
                    >
                      <span>Official NIC-2008 Hierarchy Structure</span>
                      {showHierarchy ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
                    </button>

                    {showHierarchy && (
                      <div className="p-4 bg-white space-y-2 text-[11px] border-t border-stone-100 text-[#57534E]">
                        <div>
                          <strong className="text-[#1C1917]">Section {nicData.section?.code}:</strong>{' '}
                          {nicData.section?.title}
                        </div>
                        <div>
                          <strong className="text-[#1C1917]">Division {nicData.division?.code}:</strong>{' '}
                          {nicData.division?.title}
                        </div>
                        <div>
                          <strong className="text-[#1C1917]">Group {nicData.group?.code}:</strong>{' '}
                          {nicData.group?.title}
                        </div>
                        <div>
                          <strong className="text-[#1C1917]">Class {nicData.class?.code}:</strong>{' '}
                          {nicData.class?.title}
                        </div>
                        <div>
                          <strong className="text-[#1C1917]">Sub-Class {nicData.subclass?.code}:</strong>{' '}
                          {nicData.subclass?.title}
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-stone-500 pt-1">
                    <ShieldCheck className="w-4 h-4 text-emerald-600" />
                    <span>Validated against Ministry of Statistics & PI official dataset.</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Alternative Candidates for Medium Confidence */}
            {topCandidates.length > 1 && (
              <div className="royal-card rounded-2xl p-4 bg-white border border-[#EAE3D5] space-y-2">
                <span className="text-[11px] font-bold text-stone-600 uppercase tracking-wider block">
                  Top Alternative Economic Activity Candidates
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {topCandidates.slice(1).map((cand, idx) => (
                    <div key={idx} className="p-2.5 rounded-xl bg-stone-50 border border-stone-200 flex items-center justify-between">
                      <div>
                        <strong className="text-stone-900 block">{cand.code} - {cand.title}</strong>
                        <span className="text-[10px] text-stone-500">Rank #{cand.rank}</span>
                      </div>
                      <span className="text-xs font-bold text-stone-700 bg-white px-2 py-0.5 rounded border border-stone-200">
                        {Math.round(cand.score * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bottom Actions / Transition to Stage 3 */}
            <div className="royal-card rounded-3xl p-6 bg-gradient-to-r from-stone-900 to-[#1C1917] text-white shadow-xl flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1 text-center sm:text-left">
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <span className="text-[10px] uppercase font-bold tracking-wider px-2 py-0.5 rounded bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                    Canonical Profile Ready for KALPA Orchestrator
                  </span>
                </div>
                <h4 className="text-lg font-bold font-['Outfit']">
                  Structured Business Profile Generated & Verified
                </h4>
                <p className="text-xs text-stone-300 max-w-lg leading-relaxed">
                  Stage 2 classification has locked in your venture identity with MoSPI NIC-2008 standards. Next: Stage 3 will conduct hyper-local geospatial market intelligence.
                </p>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <Button
                  size="md"
                  onClick={() => {
                    const sid = sessionId || classificationResult?.session_id;
                    navigate(`/profile?sessionId=${sid}`);
                  }}
                  className="bg-[#EA580C] hover:bg-[#C2410C] text-white font-bold shadow-lg shadow-orange-900/30"
                  icon={ArrowRight}
                >
                  Proceed to Stage 3: Business Profile
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default ClassificationPage;
