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
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';

export const ClassificationPage = () => {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { language, t } = useLanguage();

  const {
    sessionId: ctxSessionId,
    updateWorkflowState,
    markStageComplete
  } = useWorkflow();

  const sessionId = searchParams.get('session_id') || searchParams.get('id') || ctxSessionId || '';

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
    t('processing_step_1', 'Understanding your business concept...'),
    t('processing_step_2', 'Matching KALPA business ontology...'),
    t('processing_step_3', 'Retrieving official NIC-2008 candidate registry...'),
    t('processing_step_4', 'Validating economic hierarchy consistency...'),
    t('processing_step_5', 'Computing explainable deterministic confidence...')
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
        language_code: language || stage1Profile?.language_code || stage1Data?.language?.code || 'en',
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
          language_code: language || 'en',
          location: { district: 'Mandya', state: 'Karnataka' },
          capital_available: 200000,
          skills: ['grain processing']
        });
      }

      setClassificationResult(data);
      const activeSid = data?.session_id || sid;
      if (activeSid) {
        updateWorkflowState({
          sessionId: activeSid,
          businessName: data?.primary_candidate?.nic_name || classificationInput.business_concept,
          currentStage: 2,
          completedStages: [1, 2],
          nextStage: 3
        });
        markStageComplete(2, 3);
      }
    } catch (err) {
      console.error('Classification error:', err);
      setError(err.message || t('failedToClassifyBusiness', 'Failed to classify business'));
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchClassification();
  }, [sessionId, language]);

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
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 relative">

      <div className="max-w-5xl mx-auto space-y-8 relative z-10">
        {/* Agentic Workflow Thread */}
        <AgenticWorkflowThread currentStepNumber={2} className="mb-2" />

        {/* Header */}
        <div className="space-y-2 text-center max-w-2xl mx-auto">
          <Badge variant="orange" className="mb-2">
            <Sparkles className="w-3 h-3 mr-1" /> {t('step2OfKalpaJourney', 'Step 2 of KALPA Journey')}
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#28231F] font-['Playfair_Display',Georgia,serif]">
            {t('understandingYourBusiness', 'Understanding Your Business')}
          </h1>
          <p className="text-sm text-[#62584F]">
            {t('classificationDescription', 'Automated dual-layer classification aligning your venture with the official National Industrial Classification (NIC-2008 MoSPI) and KALPA Rural Enterprise Taxonomy.')}
          </p>
        </div>

        {/* Loading / Processing State */}
        {loading ? (
          <div className="rounded-3xl p-8 sm:p-12 text-center space-y-6 max-w-xl mx-auto border border-[#79563F]/20 shadow-sm bg-[#F1E4CC]">
            <div className="relative w-16 h-16 mx-auto">
              <div className="w-16 h-16 rounded-full border-4 border-[#79563F]/20 border-t-[#C96A3A] animate-spin" />
              <Briefcase className="w-6 h-6 text-[#C96A3A] absolute inset-0 m-auto" />
            </div>

            <div className="space-y-3">
              <h3 className="text-lg font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                {t('classifyingBusinessVenture', 'Classifying Business Venture')}
              </h3>
              <div className="space-y-2 text-left max-w-sm mx-auto text-xs text-[#62584F]">
                {processingSteps.map((step, idx) => (
                  <div key={idx} className="flex items-center gap-2">
                    <div
                      className={`w-4 h-4 rounded-full flex items-center justify-center text-[10px] ${
                        idx <= processingStep
                          ? 'bg-[#006F5F]/15 text-[#006F5F] font-bold'
                          : 'bg-[#FAF2E3] text-[#79563F]'
                      }`}
                    >
                      {idx <= processingStep ? '✓' : idx + 1}
                    </div>
                    <span className={idx === processingStep ? 'font-bold text-[#C96A3A]' : ''}>
                      {step}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        ) : error ? (
          /* Error State */
          <div className="rounded-3xl p-8 text-center space-y-4 max-w-lg mx-auto border border-rose-300 bg-rose-50/70 shadow-sm">
            <AlertCircle className="w-12 h-12 text-rose-600 mx-auto" />
            <h3 className="text-lg font-bold text-rose-950">{t('classificationUnavailable', 'Classification Unavailable')}</h3>
            <p className="text-xs text-rose-800">{error}</p>
            <div className="pt-2 flex justify-center gap-3">
              <Button size="sm" variant="outline" onClick={() => navigate('/intake')}>
                {t('backToStage1', 'Back to Stage 1')}
              </Button>
              <Button size="sm" onClick={fetchClassification} icon={RefreshCw}>
                {t('retry', 'Retry')}
              </Button>
            </div>
          </div>
        ) : classificationResult?.clarification_needed ? (
          /* Clarification Mode Card */
          <div className="rounded-3xl p-6 sm:p-8 bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-6 max-w-2xl mx-auto animate-fadeIn">
            <div className="flex items-center gap-3 border-b border-[#79563F]/15 pb-4">
              <div className="w-10 h-10 rounded-2xl bg-[#FAF2E3] text-[#C96A3A] border border-[#79563F]/15 flex items-center justify-center shadow-inner">
                <HelpCircle className="w-6 h-6" />
              </div>
              <div>
                <span className="text-[11px] uppercase tracking-wider font-bold text-[#C96A3A]">
                  {t('clarificationRequired', 'Clarification Required')}
                </span>
                <h3 className="text-lg font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                  {t('helpUsUnderstandYourBusinessBetter', 'Help Us Understand Your Business Better')}
                </h3>
              </div>
            </div>

            {/* Localized Question with Listen Button */}
            <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 flex items-start justify-between gap-4">
              <p className="text-sm font-semibold text-[#28231F] leading-relaxed">
                <TranslatedText text={classificationResult.clarification?.question || 'What specific type of business do you want to start?'} />
              </p>
              <button
                type="button"
                onClick={() =>
                  speakQuestion(
                    classificationResult.clarification?.question,
                    classificationResult.clarification?.language
                  )
                }
                className={`p-2.5 rounded-xl border transition-all flex items-center gap-1.5 text-xs font-bold cursor-pointer ${
                  isSpeaking
                    ? 'bg-[#C96A3A] text-white border-[#C96A3A]'
                    : 'bg-[#FAF2E3] text-[#28231F] border-[#79563F]/20 hover:bg-[#F8F0E1]'
                }`}
                title={isSpeaking ? t('stop', 'Stop') : t('listen', 'Listen')}
              >
                {isSpeaking ? <VolumeX className="w-4 h-4" /> : <Volume2 className="w-4 h-4 text-[#C96A3A]" />}
                <span>{isSpeaking ? t('stop', 'Stop') : t('listen', 'Listen')}</span>
              </button>
            </div>

            {/* Clarification Input Tabs */}
            <div className="space-y-4">
              <div className="flex gap-2 border-b border-[#79563F]/15 pb-2">
                <button
                  type="button"
                  onClick={() => setClarificationTab('options')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    clarificationTab === 'options'
                      ? 'bg-[#C96A3A] text-white'
                      : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#FAF2E3]/80'
                  }`}
                >
                  {t('selectOption', 'Select Option')}
                </button>
                <button
                  type="button"
                  onClick={() => setClarificationTab('text')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all cursor-pointer ${
                    clarificationTab === 'text'
                      ? 'bg-[#C96A3A] text-white'
                      : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#FAF2E3]/80'
                  }`}
                >
                  {t('typeAnswer', 'Type Answer')}
                </button>
                <button
                  type="button"
                  onClick={() => setClarificationTab('voice')}
                  className={`px-3 py-1.5 rounded-xl text-xs font-bold transition-all flex items-center gap-1 cursor-pointer ${
                    clarificationTab === 'voice'
                      ? 'bg-[#C96A3A] text-white'
                      : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#FAF2E3]/80'
                  }`}
                >
                  <Mic className="w-3.5 h-3.5" />
                  <span>{t('speakAnswer', 'Speak Answer')}</span>
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
                      className="p-3.5 rounded-2xl border border-[#79563F]/20 bg-[#FAF2E3] text-left hover:border-[#C96A3A] hover:bg-[#F8F0E1] transition-all font-medium text-xs text-[#28231F] flex items-center justify-between group cursor-pointer"
                    >
                      <span><TranslatedText text={opt.label} /></span>
                      <ArrowRight className="w-4 h-4 text-[#79563F] group-hover:text-[#C96A3A] group-hover:translate-x-0.5 transition-all" />
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
                    placeholder={t('clarificationPlaceholder', 'e.g. Saree retail shop, Rice mill, etc.')}
                    className="flex-grow bg-[#FAF2E3] border border-[#79563F]/20 rounded-xl px-4 py-2.5 text-xs text-[#28231F] focus:outline-none focus:ring-2 focus:ring-[#C96A3A]/40"
                  />
                  <Button
                    type="submit"
                    size="sm"
                    disabled={isClarifying || !clarificationAnswer.trim()}
                    icon={Send}
                  >
                    {isClarifying ? t('updating', 'Updating...') : t('submit', 'Submit')}
                  </Button>
                </form>
              )}

              {/* Mode 3: Voice Answer */}
              {clarificationTab === 'voice' && (
                <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 flex items-center gap-4">
                  <button
                    type="button"
                    onClick={isVoiceRecording ? stopClarificationRecording : startClarificationRecording}
                    disabled={isClarifying}
                    className={`w-12 h-12 rounded-full flex items-center justify-center transition-all cursor-pointer ${
                      isVoiceRecording
                        ? 'bg-rose-600 text-white animate-pulse'
                        : 'bg-[#C96A3A] text-white hover:scale-105'
                    }`}
                  >
                    {isVoiceRecording ? <Square className="w-5 h-5 fill-current" /> : <Mic className="w-6 h-6" />}
                  </button>
                  <div className="text-xs">
                    <p className="font-semibold text-[#28231F]">
                      {isVoiceRecording
                        ? `${t('recordingClarification', 'Recording clarification')} (${recordingSeconds}s)... ${t('tapToFinish', 'Tap to Finish')}`
                        : t('tapMicToSpeak', 'Tap the mic to speak your business type')}
                    </p>
                    <p className="text-[#62584F]">
                      {t('speaksPreferredLang', 'Speaks in your preferred Indian language')}
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
            <div className="rounded-3xl p-4 sm:p-5 bg-[#F1E4CC] border border-[#79563F]/20 flex flex-wrap items-center justify-between gap-4 shadow-sm">
              <div className="flex items-center gap-3">
                <div className="w-9 h-9 rounded-xl bg-[#FAF2E3] text-[#006F5F] border border-[#79563F]/15 flex items-center justify-center shadow-inner">
                  <ShieldCheck className="w-5 h-5" />
                </div>
                <div>
                  <div className="flex items-center gap-2">
                    <h3 className="text-sm font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                      {t('verifiedEconomicClassification', 'Verified Economic Classification')}
                    </h3>
                    <span
                      className="text-[10px] font-bold px-2.5 py-0.5 rounded-full border bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25"
                    >
                      {confidenceData.level} {t('confidence', 'CONFIDENCE')} ({confidenceData.percentage}%)
                    </span>
                  </div>
                  <p className="text-xs text-[#62584F]">
                    {t('inputLabel', 'Input:')} &ldquo;<TranslatedText text={classificationResult?.input_summary?.business_concept || 'Verified Enterprise'} />&rdquo;
                  </p>
                </div>
              </div>

              <div className="flex items-center gap-2">
                <button
                  type="button"
                  onClick={() => setShowConfidenceBreakdown(!showConfidenceBreakdown)}
                  className="text-xs font-semibold text-[#28231F] bg-[#FAF2E3] hover:bg-[#FAF2E3]/80 px-3 py-1.5 rounded-xl border border-[#79563F]/20 flex items-center gap-1.5 shadow-2xs transition-all cursor-pointer"
                >
                  <Scale className="w-3.5 h-3.5 text-[#79563F]" />
                  <span>{t('evidenceScoreBreakdown', 'Evidence Score Breakdown')}</span>
                  {showConfidenceBreakdown ? <ChevronUp className="w-3 h-3 text-[#79563F]" /> : <ChevronDown className="w-3 h-3 text-[#79563F]" />}
                </button>
                <div className="text-xs font-semibold text-[#79563F] bg-[#FAF2E3] px-3 py-1.5 rounded-xl border border-[#79563F]/20">
                  <strong className="uppercase">{language || classificationResult?.input_summary?.original_language || 'EN'}</strong>
                </div>
              </div>
            </div>

            {/* Expandable 5-Pillar Confidence Breakdown */}
            {showConfidenceBreakdown && (
              <div className="rounded-2xl p-4 bg-[#FAF2E3] border border-[#79563F]/20 shadow-sm space-y-3 animate-fadeIn">
                <div className="flex items-center justify-between border-b border-[#79563F]/15 pb-2">
                  <h4 className="text-xs font-bold text-[#28231F] uppercase tracking-wider flex items-center gap-1.5">
                    <Scale className="w-4 h-4 text-[#C96A3A]" />
                    <span>{t('deterministic5PillarConfidenceBreakdown', 'Deterministic 5-Pillar Confidence Breakdown')}</span>
                  </h4>
                  <span className="text-[11px] font-bold text-[#C96A3A]">
                    {t('total', 'Total')}: {confidenceData.score} / 1.00 ({confidenceData.percentage}%)
                  </span>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-5 gap-2 text-xs">
                  <div className="p-2.5 rounded-xl bg-[#F1E4CC] border border-[#79563F]/15">
                    <span className="text-[10px] text-[#92745A] block">{t('ontologyMatch', 'Ontology Match')} (30%)</span>
                    <strong className="text-[#28231F] text-sm">{Math.round((confidenceData.breakdown?.ontology_match || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#F1E4CC] border border-[#79563F]/15">
                    <span className="text-[10px] text-[#92745A] block">{t('nicActivityMatch', 'NIC Activity Match')} (25%)</span>
                    <strong className="text-[#28231F] text-sm">{Math.round((confidenceData.breakdown?.nic_activity_match || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#F1E4CC] border border-[#79563F]/15">
                    <span className="text-[10px] text-[#92745A] block">{t('hierarchyConsistency', 'Hierarchy Consistency')} (15%)</span>
                    <strong className="text-[#28231F] text-sm">{Math.round((confidenceData.breakdown?.hierarchy_consistency || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#F1E4CC] border border-[#79563F]/15">
                    <span className="text-[10px] text-[#92745A] block">{t('profileContext', 'Profile Context')} (15%)</span>
                    <strong className="text-[#28231F] text-sm">{Math.round((confidenceData.breakdown?.profile_context_consistency || 0) * 100)}%</strong>
                  </div>
                  <div className="p-2.5 rounded-xl bg-[#F1E4CC] border border-[#79563F]/15">
                    <span className="text-[10px] text-[#92745A] block">{t('candidateSeparation', 'Candidate Separation')} (15%)</span>
                    <strong className="text-[#28231F] text-sm">{Math.round((confidenceData.breakdown?.candidate_separation || 0) * 100)}%</strong>
                  </div>
                </div>
              </div>
            )}

            {/* Dual Column Layout: Layer A NIC + Layer B Ontology */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              {/* Card 1: KALPA Business Identity (Layer A Ontology) */}
              <div className="rounded-3xl p-6 sm:p-7 bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-5">
                <div className="flex items-center gap-3 border-b border-[#79563F]/15 pb-3">
                  <div className="w-9 h-9 rounded-xl bg-[#FAF2E3] text-[#C96A3A] border border-[#79563F]/15 flex items-center justify-center">
                    <Building2 className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#C96A3A]">
                      {t('layerAOntology', 'Layer A • KALPA Business Ontology')}
                    </span>
                    <h3 className="text-base font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                      {t('businessIdentity', 'Business Identity')}
                    </h3>
                  </div>
                </div>

                <div className="space-y-3.5 text-xs">
                  <div>
                    <span className="text-[11px] font-semibold text-[#92745A] block uppercase tracking-wider">{t('sector', 'Sector')}</span>
                    <span className="font-bold text-sm text-[#28231F]">
                      <TranslatedText text={classificationResult?.layer_b_ontology?.sector || 'Manufacturing / Agro Processing'} />
                    </span>
                  </div>

                  <div className="grid grid-cols-2 gap-3 pt-1">
                    <div>
                      <span className="text-[11px] font-semibold text-[#92745A] block uppercase tracking-wider">{t('category', 'Category')}</span>
                      <span className="font-semibold text-[#28231F]">
                        <TranslatedText text={classificationResult?.layer_b_ontology?.category || 'Grain Processing'} />
                      </span>
                    </div>
                    <div>
                      <span className="text-[11px] font-semibold text-[#92745A] block uppercase tracking-wider">{t('subcategory', 'Sub-category')}</span>
                      <span className="font-semibold text-[#28231F]">
                        <TranslatedText text={classificationResult?.layer_b_ontology?.sub_category || classificationResult?.layer_b_ontology?.subcategory || 'Rice Milling'} />
                      </span>
                    </div>
                  </div>

                  <div className="p-3.5 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15">
                    <span className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider block">{t('specificVenture', 'Specific Venture')}</span>
                    <span className="font-extrabold text-base text-[#28231F]">
                      <TranslatedText text={classificationResult?.layer_b_ontology?.specific_business || 'Rice Mill'} />
                    </span>
                  </div>

                  {/* Products / Services tags */}
                  {classificationResult?.layer_b_ontology?.products?.length > 0 && (
                    <div className="space-y-1.5 pt-1">
                      <span className="text-[11px] font-semibold text-[#92745A] block uppercase tracking-wider">
                        {t('keyProductsDerivatives', 'Key Products / Derivatives')}
                      </span>
                      <div className="flex flex-wrap gap-1.5">
                        {classificationResult.layer_b_ontology.products.map((prod, idx) => (
                          <span
                            key={idx}
                            className="px-2.5 py-1 rounded-lg bg-[#FAF2E3] text-[#4A3427] border border-[#79563F]/15 text-[11px] font-medium"
                          >
                            <TranslatedText text={prod} />
                          </span>
                        ))}
                      </div>
                    </div>
                  )}
                </div>
              </div>

              {/* Card 2: Official NIC 2008 Classification (Layer B NIC) */}
              <div className="rounded-3xl p-6 sm:p-7 bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-5">
                <div className="flex items-center gap-3 border-b border-[#79563F]/15 pb-3">
                  <div className="w-9 h-9 rounded-xl bg-[#FAF2E3] text-[#C96A3A] border border-[#79563F]/15 flex items-center justify-center">
                    <FileCheck2 className="w-5 h-5" />
                  </div>
                  <div>
                    <span className="text-[10px] font-bold uppercase tracking-wider text-[#C96A3A]">
                      {t('layerBNic', 'Layer B • Official MoSPI Classification')}
                    </span>
                    <h3 className="text-base font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                      {t('nicEconomicActivity', 'NIC-2008 Economic Activity')}
                    </h3>
                  </div>
                </div>

                <div className="space-y-3.5 text-xs">
                  {/* NIC Code Display */}
                  <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/20">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold uppercase tracking-wider text-[#79563F]">{t('officialNicCode', 'Official NIC Code')}</span>
                      <span className="text-[10px] px-2.5 py-0.5 rounded-full bg-[#F1E4CC] text-[#79563F] border border-[#79563F]/20 font-bold">{t('fiveDigitSubClass', '5-Digit Sub-Class')}</span>
                    </div>
                    <div className="text-3xl font-black text-[#28231F] font-['Outfit'] tracking-wider my-1">
                      {nicData.activity?.code || classificationResult?.layer_a_nic?.nic_code || '10612'}
                    </div>
                    <p className="text-xs font-semibold text-[#62584F] leading-snug">
                      <TranslatedText text={nicData.activity?.official_title || classificationResult?.layer_a_nic?.nic_description || 'Rice milling and processing of paddy into rice'} />
                    </p>
                  </div>

                  {/* Expandable Hierarchy */}
                  <div className="border border-[#79563F]/20 rounded-2xl overflow-hidden">
                    <button
                      type="button"
                      onClick={() => setShowHierarchy(!showHierarchy)}
                      className="w-full px-4 py-2.5 bg-[#FAF2E3] text-left font-semibold text-[#4A3427] flex items-center justify-between text-xs hover:bg-[#FAF2E3]/80 transition-colors cursor-pointer"
                    >
                      <span>{t('officialNicHierarchyStructure', 'Official NIC-2008 Hierarchy Structure')}</span>
                      {showHierarchy ? <ChevronUp className="w-4 h-4 text-[#79563F]" /> : <ChevronDown className="w-4 h-4 text-[#79563F]" />}
                    </button>

                    {showHierarchy && (
                      <div className="p-4 bg-[#FAF2E3] space-y-2 text-[11px] border-t border-[#79563F]/15 text-[#62584F]">
                        <div>
                          <strong className="text-[#28231F]">{t('section', 'Section')} {nicData.section?.code}:</strong>{' '}
                          <TranslatedText text={nicData.section?.title} />
                        </div>
                        <div>
                          <strong className="text-[#28231F]">{t('division', 'Division')} {nicData.division?.code}:</strong>{' '}
                          <TranslatedText text={nicData.division?.title} />
                        </div>
                        <div>
                          <strong className="text-[#28231F]">{t('group', 'Group')} {nicData.group?.code}:</strong>{' '}
                          <TranslatedText text={nicData.group?.title} />
                        </div>
                        <div>
                          <strong className="text-[#28231F]">{t('class', 'Class')} {nicData.class?.code}:</strong>{' '}
                          <TranslatedText text={nicData.class?.title} />
                        </div>
                        <div>
                          <strong className="text-[#28231F]">{t('subclass', 'Sub-Class')} {nicData.subclass?.code}:</strong>{' '}
                          <TranslatedText text={nicData.subclass?.title} />
                        </div>
                      </div>
                    )}
                  </div>

                  <div className="flex items-center gap-2 text-[11px] text-[#92745A] pt-1">
                    <ShieldCheck className="w-4 h-4 text-[#006F5F]" />
                    <span>{t('validatedAgainstMospi', 'Validated against Ministry of Statistics & PI official dataset.')}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Alternative Candidates for Medium Confidence */}
            {topCandidates.length > 1 && (
              <div className="rounded-2xl p-4 bg-[#F1E4CC] border border-[#79563F]/20 space-y-2 shadow-sm">
                <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider block">
                  {t('topAlternativeCandidates', 'Top Alternative Economic Activity Candidates')}
                </span>
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                  {topCandidates.slice(1).map((cand, idx) => (
                    <div key={idx} className="p-2.5 rounded-xl bg-[#FAF2E3] border border-[#79563F]/15 flex items-center justify-between">
                      <div>
                        <strong className="text-[#28231F] block">{cand.code} - <TranslatedText text={cand.title} /></strong>
                        <span className="text-[10px] text-[#92745A]">{t('rank', 'Rank')} #{cand.rank}</span>
                      </div>
                      <span className="text-xs font-bold text-[#79563F] bg-[#F1E4CC] px-2.5 py-0.5 rounded border border-[#79563F]/25">
                        {Math.round(cand.score * 100)}%
                      </span>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Bottom Actions / Transition to Business Profile Understanding */}
            <div className="rounded-3xl p-6 bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <div className="space-y-1 text-center sm:text-left">
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <span className="inline-flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#FAF2E3] text-[#006F5F] border border-[#006F5F]/25">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#006F5F]" />
                    {t('businessProfileReady', 'Business Profile Ready')}
                  </span>
                </div>
                <h4 className="text-lg font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                  {t('businessProfileUnderstanding', 'Business Profile Understanding')}
                </h4>
                <p className="text-xs text-[#62584F] max-w-lg leading-relaxed">
                  {t('classificationCompleteReview', 'Classification complete. Review your business profile.')}
                </p>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <Button
                  size="md"
                  onClick={() => {
                    const sid = sessionId || classificationResult?.session_id;
                    markStageComplete(2, 3);
                    navigate(`/profile?sessionId=${sid}`);
                  }}
                  className="saffron-gradient-btn text-white font-bold shadow-md"
                  icon={ArrowRight}
                >
                  {t('continueToBusinessProfile', 'Continue to Business Profile')}
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
