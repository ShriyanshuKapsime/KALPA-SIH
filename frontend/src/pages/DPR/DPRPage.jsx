import React, { useState, useEffect, useRef, useCallback } from 'react';
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
  Volume2,
  VolumeX,
  Mic,
  MicOff,
  AlertTriangle,
  Building2,
  FileCheck,
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';
import LanguageSelector from '../../components/ui/LanguageSelector';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';
import { validatePackageIdentity } from './dprIdentityValidator';

// Formatting helpers ensuring UNKNOWN != 0 and zero is explicitly preserved
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

// KALPA Source & Provenance Badge Helper (Restrained, no bright neons)
const renderSourceBadge = (sourceType, status) => {
  const rawTag = (sourceType || status || 'UNKNOWN').toUpperCase().replace(/_/g, ' ');
  let colorClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/25';

  if (rawTag.includes('OVERRIDE')) {
    colorClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/40 font-bold';
  } else if (rawTag.includes('USER') || rawTag.includes('ANSWER') || rawTag.includes('VERIFIED') || rawTag.includes('COMPLETE')) {
    colorClass = 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/30 font-semibold';
  } else if (rawTag.includes('BENCHMARK') || rawTag.includes('ENGINE') || rawTag.includes('CALCULATED') || rawTag.includes('POLICY') || rawTag.includes('MARKET')) {
    colorClass = 'bg-[#FAF2E3] text-[#79563F] border-[#79563F]/20 font-medium';
  } else if (rawTag.includes('PENDING') || rawTag.includes('REQUIRED') || rawTag.includes('NEEDS')) {
    colorClass = 'bg-[#FFF7ED] text-[#C2410C] border-[#C2410C]/30 font-semibold';
  }

  return (
    <span className={`text-[10px] px-2 py-0.5 rounded-md border tracking-wide uppercase ${colorClass}`}>
      {rawTag}
    </span>
  );
};

export const DPRPage = () => {
  const location = useLocation();
  const navigate = useNavigate();
  const {
    currentBusiness,
    businessId: ctxBusinessId,
    businessName: ctxBusinessName,
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
  } = useWorkflow();

  const queryParams = new URLSearchParams(location.search);
  const urlBizId = queryParams.get('business_id');

  // Robust business context resolution
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

  const isMatchingContext = ctxBusinessId && businessId && ctxBusinessId.toLowerCase() === businessId.toLowerCase();
  const activeSessionId =
    location.state?.sessionId ||
    location.state?.session_id ||
    queryParams.get('session_id') ||
    (isMatchingContext ? ctxSessionId : '') ||
    sessionStorage.getItem('kalpa_session_id') ||
    '';

  const getDprScenarioKey = (bId, sId) => {
    const cleanB = (bId || '').trim();
    const cleanS = (sId || '').trim();
    if (cleanB && cleanS) return `kalpa_dpr_scenario_${cleanB}_${cleanS}`;
    if (cleanB) return `kalpa_dpr_scenario_${cleanB}`;
    return 'kalpa_dpr_scenario_active';
  };

  const initialExplicitScenarioId = (
    queryParams.get('scenario_id') ||
    location.state?.scenarioId ||
    location.state?.scenario_id ||
    ''
  ).trim();

  // State: Initialize with explicit scenario or saved active scenario for current business & session
  const [scenarioId, setScenarioId] = useState(() => {
    if (initialExplicitScenarioId) return initialExplicitScenarioId;
    const savedScen = sessionStorage.getItem(getDprScenarioKey(businessId, activeSessionId));
    return (savedScen || '').trim();
  });

  const [activeTab, setActiveTab] = useState('overview'); // overview, assumptions, sections, documents
  const [loading, setLoading] = useState(true);
  const [recalculating, setRecalculating] = useState(false);
  const [contextPackage, setContextPackage] = useState(null);
  const [gapAnalysis, setGapAnalysis] = useState(null);
  const [currentQuestion, setCurrentQuestion] = useState(null);
  const [questionAnswer, setQuestionAnswer] = useState('');
  
  // Universal Reactive Language Context Hook
  const { language: universalLanguage, setLanguage: setUniversalLanguage, t } = useLanguage();
  const selectedLanguage = universalLanguage || 'en';
  const setSelectedLanguage = setUniversalLanguage;

  const [error, setError] = useState(null);
  const [expandedModule, setExpandedModule] = useState('module_0');

  // Edit Modal State
  const [editModalField, setEditModalField] = useState(null);
  const [editModalValue, setEditModalValue] = useState('');

  // Audio STT / TTS State
  const [voiceState, setVoiceState] = useState('IDLE'); // 'IDLE' | 'RECORDING' | 'PROCESSING' | 'SUCCESS' | 'ERROR'
  const [voiceError, setVoiceError] = useState('');
  const [isRecording, setIsRecording] = useState(false);
  const [isPlayingAudio, setIsPlayingAudio] = useState(false);
  const [sttLoading, setSttLoading] = useState(false);
  const [impactAlert, setImpactAlert] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);
  const currentAudioRef = useRef(null);

  // Re-fetch question in newly selected language if language is changed on the page
  useEffect(() => {
    if (!businessId || !scenarioId || !contextPackage) return;
    const refetchQuestionForLanguage = async () => {
      try {
        const qRes = await apiService.dpr.getNextQuestion(businessId, {
          language: selectedLanguage,
          scenario_id: scenarioId,
        });
        const qData = qRes?.data || qRes;
        if (qData?.has_question) {
          setCurrentQuestion(qData.question);
        }
      } catch (e) {
        console.warn('[DPR LANGUAGE Q REFETCH ERROR]:', e);
      }
    };
    refetchQuestionForLanguage();
  }, [selectedLanguage, businessId, scenarioId]);

  // Initialization ref & in-flight promise guards to prevent double-calls in React Strict Mode
  const initRef = useRef(false);
  const inFlightInitRef = useRef(null);

  // Main Guarded DPR Initialization & Loader
  const loadDPRState = useCallback(
    async (forcedScenarioId = null, forcedMode = null) => {
      if (!businessId) {
        setLoading(false);
        setError({
          title: 'No Active Business Found',
          message: 'Please complete the business intake step first.',
        });
        return;
      }

      // Deduplicate in-flight initializations (e.g. React StrictMode mount)
      if (inFlightInitRef.current && !forcedScenarioId) {
        return inFlightInitRef.current;
      }

      const executeLoad = async () => {
        try {
          setLoading(true);
          setError(null);

          const dprKey = getDprScenarioKey(businessId, activeSessionId);
          const currentSavedScen = (sessionStorage.getItem(dprKey) || '').trim();

          let targetScenId = (
            forcedScenarioId ||
            initialExplicitScenarioId ||
            currentSavedScen ||
            scenarioId ||
            ''
          ).trim();

          // Verify targetScenId belongs to current business if it contains business prefix
          const cleanBizPrefix = businessId.replace(/[-_]/g, '').slice(0, 5).toLowerCase();
          const isValidScenForBiz =
            targetScenId &&
            (targetScenId.toLowerCase().includes(cleanBizPrefix) ||
              targetScenId.toLowerCase().startsWith('dpr-'));

          let initAction = 'RESUMED_EXISTING_DPR';
          let reqMode = forcedMode || (targetScenId && isValidScenForBiz ? 'resume' : 'new');

          // If starting new or no valid existing scenario for this business & session:
          if (!targetScenId || !isValidScenForBiz || reqMode === 'new') {
            reqMode = 'new';
            initAction = 'CREATED_NEW_DPR';

            // Create fresh isolated scenario with empty user inputs
            const createRes = await apiService.dpr.createNewScenario(businessId, {
              session_id: activeSessionId || undefined,
            });
            const createData = createRes?.data || createRes;
            targetScenId = createData?.scenario_id;

            if (!targetScenId) {
              throw new Error('Failed to generate fresh DPR scenario.');
            }

            // Immediately persist active scenario for this business & session
            sessionStorage.setItem(dprKey, targetScenId);

            // Reset all transient user input state for fresh intake
            setQuestionAnswer('');
            setCurrentQuestion(null);
            setEditModalField(null);
            setEditModalValue('');
            setImpactAlert(null);
          } else {
            // Resumed existing scenario - ensure stored in sessionStorage
            sessionStorage.setItem(dprKey, targetScenId);
          }

          // Section 18 Development Lifecycle Logging
          console.log('[DPR INIT]', {
            businessId: businessId,
            existingDprId: reqMode === 'resume' ? targetScenId : null,
            existingDprStatus: reqMode === 'resume' ? 'IN_PROGRESS' : null,
            requestedMode: reqMode,
            resolvedDprId: targetScenId,
            initializationAction: initAction,
          });

          setScenarioId(targetScenId);

          // Fetch context package, gap analysis, and next intake question
          const params = { scenario_id: targetScenId };
          const [ctxRes, gapRes, qRes] = await Promise.allSettled([
            apiService.dpr.getContext(businessId, params),
            apiService.dpr.getGapAnalysis(businessId, params),
            apiService.dpr.getNextQuestion(businessId, { language: selectedLanguage, ...params }),
          ]);

          if (ctxRes.status === 'rejected') {
            const httpStatus = ctxRes.reason?.response?.status || 500;
            const errDetail =
              ctxRes.reason?.response?.data?.message ||
              ctxRes.reason?.response?.data?.detail ||
              ctxRes.reason?.message ||
              'Unable to load DPR context package.';

            setContextPackage(null);
            setError({
              title: 'Unable to prepare DPR Workspace',
              http_error: httpStatus,
              message: typeof errDetail === 'string' ? errDetail : JSON.stringify(errDetail),
            });
            return;
          }

          const ctxData = ctxRes.value?.data || ctxRes.value;
          const gapData = gapRes.status === 'fulfilled' ? gapRes.value?.data || gapRes.value : null;
          const qData = qRes.status === 'fulfilled' ? qRes.value?.data || qRes.value : null;

          // Validate package identity & cross-scenario isolation
          const ctxValidation = validatePackageIdentity(ctxData, {
            business_id: businessId,
            scenario_id: targetScenId,
          });
          if (!ctxValidation.valid) {
            throw new Error(`DPR_STATE_ISOLATION_ERROR: ${ctxValidation.reason}`);
          }

          if (ctxData) {
            setContextPackage(ctxData);
            if (ctxData.scenario_id) {
              setScenarioId(ctxData.scenario_id.trim());
            }
          }
          if (gapData) {
            setGapAnalysis(gapData);
          }
          if (qData?.has_question) {
            setCurrentQuestion(qData.question);
            setQuestionAnswer('');
          } else {
            setCurrentQuestion(null);
          }
        } catch (err) {
          console.error('[DPR LOAD ERROR]:', err);
          const httpStatus = err.response?.status || 500;
          const errMsg = err.message || 'Failed to load project report state. Please try again.';
          setContextPackage(null);
          setError({
            title: 'Unable to load project report',
            http_error: httpStatus,
            message: errMsg,
          });
        } finally {
          setLoading(false);
          inFlightInitRef.current = null;
        }
      };

      inFlightInitRef.current = executeLoad();
      return inFlightInitRef.current;
    },
    [businessId, activeSessionId, initialExplicitScenarioId, selectedLanguage, scenarioId]
  );

  // Auto-run guarded initialization on mount
  useEffect(() => {
    if (!initRef.current) {
      initRef.current = true;
      loadDPRState();
    }
  }, [loadDPRState]);

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
    };
  }, []);

  // Handle Question Submission
  const handleAnswerSubmit = async (customAns = null) => {
    if (!currentQuestion) return;
    const ansToSubmit = customAns !== null ? customAns : questionAnswer;
    if (ansToSubmit === '' || ansToSubmit === undefined) return;

    try {
      setRecalculating(true);
      const activeScen = contextPackage?.scenario_id || scenarioId;
      const res = await apiService.dpr.answerQuestion(businessId, {
        field_id: currentQuestion.field_id,
        answer: ansToSubmit,
        scenario_id: activeScen,
      });

      const resData = res?.data || res;
      if (resData?.success) {
        if (resData?.impact) {
          setImpactAlert(resData.impact);
        }
        setQuestionAnswer('');
        setVoiceState('IDLE');
        setVoiceError('');
        console.log('[DPR PROGRESS UPDATE]', {
          fieldId: currentQuestion.field_id,
          sectionId: currentQuestion.section_id,
          previousCompleted: completedSecCount,
        });
        await loadDPRState(activeScen, 'resume');
      } else if (resData?.validation_error) {
        setError({ title: 'Validation Error', message: resData.validation_error });
      }
    } catch (err) {
      console.error('[DPR ANSWER ERROR]:', err);
      setError({ title: 'Answer Submission Failed', message: 'Please verify input.' });
    } finally {
      setRecalculating(false);
    }
  };

  // Handle Assumption Override
  const handleApplyOverride = async () => {
    if (!editModalField) return;
    try {
      setRecalculating(true);
      const activeScen = contextPackage?.scenario_id || scenarioId;
      const res = await apiService.dpr.setOverride(businessId, {
        field_id: editModalField.field_id,
        override_value: editModalValue,
        scenario_id: activeScen,
      });
      const resData = res?.data || res;
      if (resData?.impact) {
        setImpactAlert(resData.impact);
      }
      setEditModalField(null);
      await loadDPRState(activeScen, 'resume');
    } catch (err) {
      console.error('[DPR OVERRIDE ERROR]:', err);
      setError({ title: 'Override Failed', message: 'Unable to apply assumption override.' });
    } finally {
      setRecalculating(false);
    }
  };

  // Handle Reset Override
  const handleAcceptBenchmark = async (fieldId) => {
    try {
      setRecalculating(true);
      const activeScen = contextPackage?.scenario_id || scenarioId;
      await apiService.dpr.acceptBenchmark(businessId, {
        field_id: fieldId,
        scenario_id: activeScen,
      });
      await loadDPRState(activeScen, 'resume');
    } catch (err) {
      console.error('[DPR BENCHMARK ERROR]:', err);
      setError({ title: 'Reset Failed', message: 'Unable to reset assumption to benchmark.' });
    } finally {
      setRecalculating(false);
    }
  };

  // Voice Input (STT) Pipeline
  const startRecording = async () => {
    setVoiceError('');
    try {
      if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
        setVoiceState('ERROR');
        setVoiceError('Microphone recording is not supported on this browser.');
        return;
      }

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      // Audio Format Handling: Preferred audio/webm;codecs=opus, fallback to audio/webm or default
      let mimeType = 'audio/webm;codecs=opus';
      if (typeof MediaRecorder.isTypeSupported === 'function') {
        if (!MediaRecorder.isTypeSupported(mimeType)) {
          mimeType = MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : '';
        }
      } else {
        mimeType = '';
      }

      const options = mimeType ? { mimeType } : {};
      const mediaRecorder = new MediaRecorder(stream, options);

      mediaRecorder.ondataavailable = (e) => {
        if (e.data && e.data.size > 0) {
          audioChunksRef.current.push(e.data);
        }
      };

      mediaRecorder.onstop = async () => {
        // Release mic stream tracks
        stream.getTracks().forEach((track) => track.stop());

        const finalMimeType = mediaRecorder.mimeType || mimeType || 'audio/webm';
        const audioBlob = new Blob(audioChunksRef.current, { type: finalMimeType });

        console.log('[DPR VOICE] Recorded audio blob:', {
          size: audioBlob.size,
          type: audioBlob.type,
          chunksCount: audioChunksRef.current.length,
        });

        // Do not send empty blobs
        if (!audioBlob || audioBlob.size < 100 || audioChunksRef.current.length === 0) {
          setVoiceState('ERROR');
          setVoiceError('Please record audio before submitting.');
          setIsRecording(false);
          setSttLoading(false);
          return;
        }

        setVoiceState('PROCESSING');
        setSttLoading(true);

        try {
          // Prepare FormData strictly matching backend contract (field name: 'file')
          const formData = new FormData();
          formData.append('file', audioBlob, 'recording.webm');

          // Validation verification
          const attachedFile = formData.get('file');
          console.log('[DPR VOICE] Attached FormData file:', attachedFile);

          if (!attachedFile || (attachedFile instanceof Blob && attachedFile.size === 0)) {
            setVoiceState('ERROR');
            setVoiceError('Please record audio before submitting.');
            return;
          }

          const res = await apiService.dpr.transcribeAudio(formData, selectedLanguage);
          const resData = res?.data || res;
          console.log('[DPR VOICE] STT Response received:', resData);

          if (resData?.success === false && resData?.error) {
            setVoiceState('ERROR');
            setVoiceError(resData.error);
          } else if (resData?.text || resData?.transcript) {
            const transcript = (resData.text || resData.transcript).trim();
            setQuestionAnswer(transcript);
            setVoiceState('SUCCESS');
            // Revert state to IDLE after brief success confirmation
            setTimeout(() => {
              setVoiceState((prev) => (prev === 'SUCCESS' ? 'IDLE' : prev));
            }, 3500);
          } else {
            setVoiceState('ERROR');
            setVoiceError("Could not recognize clear speech. Please try again or type your answer.");
          }
        } catch (err) {
          console.error('[DPR STT ERROR]:', err);
          setVoiceState('ERROR');
          setVoiceError(err.message || 'Speech conversion failed. You can type your answer directly.');
        } finally {
          setSttLoading(false);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start(250); // Capture chunk slices every 250ms
      setIsRecording(true);
      setVoiceState('RECORDING');
    } catch (err) {
      console.error('[MIC ACCESS ERROR]:', err);
      setIsRecording(false);
      setVoiceState('ERROR');
      if (err.name === 'NotAllowedError' || err.name === 'PermissionDeniedError') {
        setVoiceError('Microphone permission denied. Please enable microphone access in your browser settings.');
      } else {
        setVoiceError('Could not start microphone recording. Please type your answer directly.');
      }
    }
  };

  const stopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
    }
    setIsRecording(false);
  };

  // Audio Playback (TTS)
  const handlePlayTTS = async (text) => {
    if (isPlayingAudio) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      setIsPlayingAudio(false);
      return;
    }
    try {
      setIsPlayingAudio(true);
      const res = await apiService.dpr.synthesizeAudio({ text, language: selectedLanguage });
      const resData = res?.data || res;
      if (resData?.audio_base64) {
        const audio = new Audio(`data:audio/wav;base64,${resData.audio_base64}`);
        currentAudioRef.current = audio;
        audio.onended = () => setIsPlayingAudio(false);
        audio.onerror = () => setIsPlayingAudio(false);
        await audio.play();
      } else {
        setIsPlayingAudio(false);
      }
    } catch (err) {
      console.error('[DPR TTS ERROR]:', err);
      setIsPlayingAudio(false);
    }
  };

  // Derived Values
  const fields = contextPackage?.fields || {};
  const modules = contextPackage?.modules || {};
  const bp = contextPackage?.business_profile || {};
  const sections = contextPackage?.sections || {};

  // Compute total and completed sections strictly from authoritative state
  const totalSectionsCount =
    gapAnalysis?.total_sections ||
    contextPackage?.total_sections_count ||
    (sections && Object.keys(sections).length > 0 ? Object.keys(sections).length : 39);

  const completedSecCount =
    gapAnalysis?.completed_sections_count !== undefined
      ? gapAnalysis.completed_sections_count
      : contextPackage?.completed_sections_count !== undefined
      ? contextPackage.completed_sections_count
      : sections && Object.keys(sections).length > 0
      ? Object.values(sections).filter((s) => s.completeness_status === 'COMPLETE').length
      : 0;

  const isReadyForNextStep = gapAnalysis?.blocking_gaps?.length === 0;

  // Development progress logging as per Section 7
  useEffect(() => {
    if (contextPackage) {
      console.log('[DPR PROGRESS]', {
        totalSections: totalSectionsCount,
        completedSections: completedSecCount,
        completedSectionIds: Object.entries(sections)
          .filter(([_, s]) => s.completeness_status === 'COMPLETE')
          .map(([id]) => id),
        source: 'canonical_sections',
      });
    }
  }, [contextPackage, totalSectionsCount, completedSecCount]);

  // -------------------------------------------------------------
  // 1. Initial Skeleton / Loading State (Clean KALPA Parchment Theme)
  // -------------------------------------------------------------
  if (loading) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6 animate-fadeIn">
        <AgenticWorkflowThread />
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 rounded-2xl bg-[#FAF7F2] border border-[#79563F]/25 flex items-center justify-center mx-auto text-[#79563F] shadow-2xs">
            <RefreshCw className="w-6 h-6 animate-spin text-[#79563F]" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
              Preparing your Bank-Ready Project Report...
            </h3>
            <p className="text-xs text-[#79563F]">
              Assembling verified evidence from Market Intelligence, Financial Model, Readiness, and Feasibility.
            </p>
          </div>
          <div className="max-w-md mx-auto space-y-2 pt-2">
            <div className="h-3 bg-[#FAF7F2] rounded-full animate-pulse" />
            <div className="h-3 bg-[#FAF7F2] rounded-full animate-pulse w-3/4 mx-auto" />
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 2. Error State (Graceful KALPA Card)
  // -------------------------------------------------------------
  if (error && !contextPackage) {
    return (
      <div className="max-w-6xl mx-auto px-4 sm:px-6 py-6 space-y-6 animate-fadeIn">
        <AgenticWorkflowThread />
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-8 text-center space-y-4 shadow-2xs">
          <div className="w-12 h-12 rounded-2xl bg-rose-50 border border-rose-200 flex items-center justify-center mx-auto text-rose-700 shadow-2xs">
            <AlertTriangle className="w-6 h-6 text-rose-700" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
              {error.title || 'Unable to prepare project report'}
            </h3>
            <p className="text-xs text-[#79563F] max-w-md mx-auto leading-relaxed">
              {error.message || "We couldn't initialize the project report right now."}
            </p>
          </div>
          <div className="pt-2">
            <button
              type="button"
              onClick={() => loadDPRState()}
              className="saffron-gradient-btn px-5 py-2.5 rounded-xl text-xs font-bold shadow-xs cursor-pointer inline-flex items-center gap-2"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Try Again</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // -------------------------------------------------------------
  // 3. Main DPR Workspace
  // -------------------------------------------------------------
  return (
    <div className="max-w-6xl mx-auto px-3 sm:px-6 py-5 sm:py-6 space-y-5 sm:space-y-6 animate-fadeIn">
      {/* Top Standard KALPA Workflow */}
      <AgenticWorkflowThread />

      {/* Clean KALPA DPR Header */}
      <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="px-2.5 py-0.5 rounded-full text-[11px] font-bold bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/25 uppercase tracking-wider">
                {t('dpr_step_1_title', 'DPR · STEP 1')}
              </span>
              <span className="text-xs text-[#79563F]/80 font-medium">
                {t('dpr_step_1_subtitle', 'Bank-Ready Project Report Intake & Gap Resolution')}
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-extrabold text-[#1C1917] font-['Outfit']">
              {businessName || ctxBusinessName || bp.business_name || 'Enterprise Project Report'}
            </h1>
            <p className="text-xs text-[#79563F] max-w-2xl leading-relaxed">
              {t('dpr_institutional_desc', 'Prepare and review your project report using the validated KALPA analysis.')}
            </p>
          </div>

          {/* Secondary Header Controls */}
          <div className="flex items-center gap-2.5 self-start sm:self-center">
            {/* Universal Language Selector Dropdown */}
            <LanguageSelector compact />

            {/* Refresh Button */}
            <button
              type="button"
              onClick={() => loadDPRState()}
              disabled={recalculating}
              title="Refresh Project Report State"
              className="p-2 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/20 transition-all cursor-pointer shadow-2xs"
            >
              <RefreshCw className={`w-3.5 h-3.5 ${recalculating ? 'animate-spin text-[#79563F]' : ''}`} />
            </button>
          </div>
        </div>
      </div>

      {/* Change Impact Alert Panel (if user changed an assumption) */}
      {impactAlert && (
        <div className="bg-[#EAF5EE] border border-[#1B4D3E]/30 rounded-2xl p-4 animate-fadeIn shadow-2xs">
          <div className="flex items-start justify-between">
            <div className="flex items-center gap-2">
              <Sparkles className="w-4 h-4 text-[#1B4D3E]" />
              <h4 className="font-bold text-xs sm:text-sm text-[#1B4D3E]">
                Assumption Updated: {impactAlert.changed_field_label}
              </h4>
            </div>
            <button
              type="button"
              onClick={() => setImpactAlert(null)}
              className="text-xs text-[#79563F] hover:text-[#1C1917] font-semibold cursor-pointer"
            >
              {t('close', 'Dismiss')}
            </button>
          </div>
          <p className="text-xs text-[#1B4D3E]/90 mt-1">{impactAlert.recalculation_summary}</p>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5 mt-3">
            {impactAlert.affected_metrics?.map((m, idx) => (
              <div key={idx} className="bg-white/80 border border-[#1B4D3E]/20 rounded-xl p-2.5">
                <div className="text-[10px] text-[#79563F] font-semibold uppercase">{m.label}</div>
                <div className="flex items-baseline gap-1.5 mt-0.5">
                  <span className="text-[11px] text-[#79563F]/70 line-through">{m.formatted_old}</span>
                  <span className="text-xs font-bold text-[#1B4D3E]">{m.formatted_new}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Summary Row Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 sm:gap-4">
        {/* Card 1: 39 Sections Status */}
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
            {t('dpr_sections_status', '39 Sections Status')}
          </div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {completedSecCount} <span className="text-xs font-medium text-[#79563F]">/ {totalSectionsCount} {t('complete', 'Complete')}</span>
          </div>
          <div className="w-full bg-[#FAF7F2] h-2 rounded-full mt-3 overflow-hidden border border-[#79563F]/15">
            <div
              className="bg-[#1B4D3E] h-full rounded-full transition-all duration-500"
              style={{
                width: `${Math.min(
                  100,
                  Math.round((completedSecCount / (totalSectionsCount || 39)) * 100)
                )}%`,
              }}
            />
          </div>
        </div>

        {/* Card 2: Total Project Cost */}
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
            {t('dpr_total_project_cost', 'Total Project Cost')}
          </div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {formatINR(fields.total_project_cost?.value)}
          </div>
          <div className="text-[11px] text-[#1B4D3E] mt-2 flex items-center gap-1 font-medium">
            <CheckCircle2 className="w-3.5 h-3.5 text-[#1B4D3E]" />
            <span>{t('dpr_reconciled_tables', 'Calculated via Financial Model')}</span>
          </div>
        </div>

        {/* Card 3: Bank Term Loan */}
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
            {t('dpr_bank_term_loan', 'Bank Term Loan')}
          </div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {formatINR(fields.bank_term_loan_amount?.value)}
          </div>
          <div className="text-[11px] text-[#79563F] mt-2">
            {t('dpr_promoter_margin', 'Promoter Margin')}: {formatINR(fields.promoter_equity_amount?.value)}
          </div>
        </div>

        {/* Card 4: Average DSCR */}
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs flex flex-col justify-between">
          <div className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
            {t('dpr_average_dscr', 'Average DSCR')}
          </div>
          <div className="text-2xl font-black text-[#1C1917] font-['Outfit'] mt-1">
            {formatRatio(fields.glance_average_dscr?.value)}
          </div>
          <div className="text-[11px] text-[#79563F] mt-2">
            {t('dpr_break_even', 'Break-Even')}: {formatPct(fields.glance_break_even_utilization?.value)}
          </div>
        </div>
      </div>

      {/* 4 Segmented DPR Tabs */}
      <div className="flex border-b border-[#79563F]/20 gap-2 overflow-x-auto pb-1 no-scrollbar">
        <button
          type="button"
          onClick={() => setActiveTab('overview')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs ${
            activeTab === 'overview'
              ? 'bg-[#79563F] text-white shadow-xs'
              : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#F2E8D5] border border-[#79563F]/20'
          }`}
        >
          <Sparkles className="w-3.5 h-3.5" />
          <span>Overview & Inputs</span>
          {gapAnalysis?.blocking_gaps?.length > 0 && (
            <span className="bg-rose-100 text-rose-800 text-[10px] font-bold px-1.5 py-0.2 rounded-full">
              {gapAnalysis.blocking_gaps.length}
            </span>
          )}
        </button>

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
          <span>Assumptions & Overrides</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('sections')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs ${
            activeTab === 'sections'
              ? 'bg-[#79563F] text-white shadow-xs'
              : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#F2E8D5] border border-[#79563F]/20'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          <span>All 39 Sections</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('documents')}
          className={`px-4 py-2 rounded-xl text-xs font-bold transition flex items-center gap-1.5 cursor-pointer whitespace-nowrap shadow-2xs ${
            activeTab === 'documents'
              ? 'bg-[#79563F] text-white shadow-xs'
              : 'bg-[#FAF2E3] text-[#79563F] hover:bg-[#F2E8D5] border border-[#79563F]/20'
          }`}
        >
          <FileText className="w-3.5 h-3.5" />
          <span>Document Checklist</span>
          {gapAnalysis?.document_pending > 0 && (
            <span className="bg-amber-100 text-amber-900 text-[10px] font-bold px-1.5 py-0.2 rounded-full">
              {gapAnalysis.document_pending}
            </span>
          )}
        </button>
      </div>

      {/* ========================================================= */}
      {/* TAB 1: OVERVIEW & TARGETED QUESTIONING */}
      {/* ========================================================= */}
      {activeTab === 'overview' && (
        <div className="space-y-5 animate-fadeIn">
          {/* Interactive Question Card if there is an active question */}
          {currentQuestion ? (
            <div className="bg-[#FAF2E3] border-2 border-[#79563F]/30 rounded-3xl p-5 sm:p-6 shadow-xs space-y-4">
              {/* Question Header */}
              <div className="flex items-center justify-between gap-3">
                <div className="flex items-center gap-2">
                  <span className="bg-[#79563F] text-white text-[11px] font-bold px-2.5 py-0.5 rounded-full uppercase tracking-wider">
                    Action Required
                  </span>
                  <span className="text-xs text-[#79563F] font-semibold">
                    Section {currentQuestion.section_id}
                  </span>
                  {renderSourceBadge(currentQuestion.source_status || 'USER_REQUIRED')}
                </div>

                {/* TTS Audio Listen Button */}
                <button
                  type="button"
                  onClick={() => {
                    const speechText = [
                      currentQuestion.question || currentQuestion.question_text,
                      currentQuestion.helper_text,
                      currentQuestion.example,
                    ]
                      .filter(Boolean)
                      .join('\n');
                    handlePlayTTS(speechText);
                  }}
                  disabled={isPlayingAudio}
                  className="text-xs bg-[#FAF7F2] hover:bg-white text-[#79563F] px-3 py-1.5 rounded-xl flex items-center gap-1.5 border border-[#79563F]/25 font-semibold transition cursor-pointer shadow-2xs"
                >
                  {isPlayingAudio ? (
                    <>
                      <VolumeX className="w-3.5 h-3.5 text-[#79563F] animate-pulse" />
                      <span>Stop Voice</span>
                    </>
                  ) : (
                    <>
                      <Volume2 className="w-3.5 h-3.5 text-[#79563F]" />
                      <span>Listen (बोलकर सुनें)</span>
                    </>
                  )}
                </button>
              </div>

              {/* Question Title */}
              <h3 className="text-lg sm:text-xl font-bold text-[#1C1917] font-['Outfit']">
                {currentQuestion.title || currentQuestion.question || currentQuestion.question_text}
              </h3>

              {/* Purpose Description */}
              {(currentQuestion.description || currentQuestion.helper_text || currentQuestion.explanation) && (
                <p className="text-xs sm:text-sm text-[#79563F] leading-relaxed">
                  {currentQuestion.description || currentQuestion.helper_text || currentQuestion.explanation}
                </p>
              )}

              {/* Example Callout */}
              {currentQuestion.example && (
                <div className="bg-[#FAF7F2] border-l-4 border-[#79563F] rounded-r-xl px-4 py-2.5 text-xs text-[#79563F] italic">
                  {currentQuestion.example}
                </div>
              )}

              {/* Input Area + 5-State Voice Pipeline + Confirm */}
              <div className="pt-2">
                {currentQuestion.options ? (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                    {currentQuestion.options.map((opt, idx) => (
                      <button
                        key={idx}
                        type="button"
                        onClick={() => handleAnswerSubmit(opt.value)}
                        disabled={recalculating}
                        className="text-left bg-white hover:bg-[#FAF7F2] border border-[#79563F]/25 hover:border-[#79563F] p-3.5 rounded-xl text-xs sm:text-sm font-semibold text-[#1C1917] transition flex items-center justify-between group cursor-pointer shadow-2xs"
                      >
                        <span>{opt.label}</span>
                        <ArrowRight className="w-4 h-4 text-[#79563F] group-hover:translate-x-0.5 transition-transform" />
                      </button>
                    ))}
                  </div>
                ) : (
                  <div className="space-y-3">
                    <div className="flex items-center gap-2">
                      <input
                        type={
                          currentQuestion.input_type === 'currency' || currentQuestion.input_type === 'number'
                            ? 'number'
                            : 'text'
                        }
                        value={questionAnswer}
                        onChange={(e) => {
                          setQuestionAnswer(e.target.value);
                          if (voiceError) setVoiceError('');
                        }}
                        placeholder={
                          currentQuestion.example
                            ? currentQuestion.example.replace(/^Example:\s*/i, 'e.g. ')
                            : currentQuestion.unit
                            ? `Enter value in ${currentQuestion.unit}`
                            : 'Type your answer...'
                        }
                        className="flex-1 bg-white border border-[#79563F]/25 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-[#1C1917] placeholder:text-[#79563F]/50 focus:outline-none focus:border-[#79563F] focus:ring-1 focus:ring-[#79563F]/30"
                      />

                      {/* Microphone Voice Button with 5 Discrete UI States */}
                      <button
                        type="button"
                        onClick={voiceState === 'RECORDING' ? stopRecording : startRecording}
                        disabled={voiceState === 'PROCESSING' || recalculating}
                        title={
                          voiceState === 'RECORDING'
                            ? 'Click to stop recording'
                            : voiceState === 'PROCESSING'
                            ? 'Converting voice...'
                            : `Speak answer in ${(selectedLanguage || 'en').toUpperCase()}`
                        }
                        className={`h-10 px-3.5 rounded-xl border flex items-center gap-2 transition cursor-pointer shadow-2xs shrink-0 font-medium text-xs ${
                          voiceState === 'RECORDING'
                            ? 'bg-rose-600 text-white animate-pulse ring-4 ring-rose-200 border-rose-600'
                            : voiceState === 'PROCESSING'
                            ? 'bg-[#FAF7F2] text-[#79563F] border-[#79563F]/30 cursor-not-allowed opacity-80'
                            : voiceState === 'SUCCESS'
                            ? 'bg-[#EAF5EE] text-[#1B4D3E] border-[#1B4D3E]/40'
                            : 'bg-[#FAF7F2] hover:bg-white text-[#79563F] border-[#79563F]/25 hover:border-[#79563F]'
                        }`}
                      >
                        {voiceState === 'RECORDING' ? (
                          <>
                            <span className="w-2 h-2 rounded-full bg-white animate-ping" />
                            <MicOff className="w-4 h-4 text-white" />
                            <span className="hidden sm:inline font-bold">Listening...</span>
                          </>
                        ) : voiceState === 'PROCESSING' ? (
                          <>
                            <RefreshCw className="w-4 h-4 animate-spin text-[#79563F]" />
                            <span className="hidden sm:inline">Converting...</span>
                          </>
                        ) : voiceState === 'SUCCESS' ? (
                          <>
                            <CheckCircle2 className="w-4 h-4 text-[#1B4D3E]" />
                            <span className="hidden sm:inline font-bold">Converted</span>
                          </>
                        ) : (
                          <>
                            <Mic className="w-4 h-4 text-[#79563F]" />
                            <span className="hidden sm:inline">Speak</span>
                          </>
                        )}
                      </button>

                      {/* Confirm Button */}
                      <button
                        type="button"
                        onClick={() => handleAnswerSubmit()}
                        disabled={!questionAnswer || recalculating || voiceState === 'PROCESSING'}
                        className="saffron-gradient-btn px-5 h-10 rounded-xl text-xs font-bold shadow-xs cursor-pointer disabled:opacity-50 shrink-0"
                      >
                        Confirm
                      </button>
                    </div>

                    {/* Live Voice State Indicator Banners */}
                    {voiceState === 'RECORDING' && (
                      <div className="flex items-center gap-2 text-xs font-semibold text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-2.5 animate-fadeIn">
                        <span className="w-2 h-2 rounded-full bg-rose-600 animate-ping" />
                        <span>Listening in {(selectedLanguage || 'en').toUpperCase()}... Speak your answer clearly, then click Stop.</span>
                      </div>
                    )}

                    {voiceState === 'PROCESSING' && (
                      <div className="flex items-center gap-2 text-xs font-medium text-[#79563F] bg-[#FAF7F2] border border-[#79563F]/20 rounded-xl p-2.5 animate-fadeIn">
                        <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#79563F]" />
                        <span>Converting voice audio to text using Sarvam AI...</span>
                      </div>
                    )}

                    {voiceState === 'SUCCESS' && (
                      <div className="flex items-center gap-2 text-xs font-semibold text-[#1B4D3E] bg-[#EAF5EE] border border-[#1B4D3E]/30 rounded-xl p-2.5 animate-fadeIn">
                        <CheckCircle2 className="w-3.5 h-3.5 text-[#1B4D3E]" />
                        <span>Transcript populated. Review your answer above and click Confirm.</span>
                      </div>
                    )}

                    {voiceState === 'ERROR' && voiceError && (
                      <div className="flex items-start justify-between gap-2 text-xs text-rose-700 bg-rose-50 border border-rose-200 rounded-xl p-2.5 animate-fadeIn">
                        <div className="flex items-center gap-1.5">
                          <AlertCircle className="w-4 h-4 text-rose-600 shrink-0" />
                          <span>{voiceError}</span>
                        </div>
                        <button
                          type="button"
                          onClick={() => {
                            setVoiceState('IDLE');
                            setVoiceError('');
                          }}
                          className="text-[10px] text-rose-800 underline font-semibold cursor-pointer shrink-0"
                        >
                          Dismiss
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Purpose & Validation Guidance */}
              <div className="bg-[#FAF7F2] border border-[#79563F]/15 rounded-2xl p-3.5 space-y-1">
                <div className="text-[10px] font-bold uppercase tracking-wider text-[#79563F] flex items-center gap-1">
                  <Info className="w-3.5 h-3.5" />
                  <span>Why We Are Asking (Purpose & Bank Appraisal)</span>
                </div>
                <p className="text-xs text-[#79563F] leading-relaxed">
                  {currentQuestion.validationHint ||
                    currentQuestion.validation_hint ||
                    currentQuestion.why_we_are_asking ||
                    currentQuestion.reason ||
                    'This detail is required to evaluate entity profile, capital adequacy, and statutory loan eligibility.'}
                </p>
              </div>
            </div>
          ) : isReadyForNextStep ? (
            /* All Critical Inputs Resolved */
            <div className="bg-[#FAF2E3] border border-[#1B4D3E]/30 rounded-3xl p-6 sm:p-8 text-center space-y-4 shadow-2xs">
              <div className="w-12 h-12 rounded-2xl bg-[#EAF5EE] text-[#1B4D3E] border border-[#1B4D3E]/30 flex items-center justify-center mx-auto shadow-2xs">
                <CheckCircle2 className="w-6 h-6 text-[#1B4D3E]" />
              </div>
              <div className="space-y-1">
                <h3 className="text-lg font-bold text-[#1C1917] font-['Outfit']">
                  Critical Project Report Inputs Resolved!
                </h3>
                <p className="text-xs sm:text-sm text-[#79563F] max-w-xl mx-auto leading-relaxed">
                  All critical intake inputs have been resolved. You are ready to review the document sections or proceed to DPR Enrichment & Drafting.
                </p>
              </div>
              <div className="pt-2 flex justify-center gap-3">
                <button
                  type="button"
                  onClick={() => {
                    navigate(`/dpr/enrichment?business_id=${businessId}&scenario_id=${scenarioId}`, {
                      state: { businessId, scenarioId },
                    });
                  }}
                  className="saffron-gradient-btn px-6 py-2.5 rounded-xl text-xs font-bold shadow-xs cursor-pointer inline-flex items-center gap-2"
                >
                  <span>Continue to DPR Enrichment →</span>
                </button>
              </div>
            </div>
          ) : (
            <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-6 text-center space-y-2 shadow-2xs">
              <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                DPR Intake In Progress
              </h3>
              <p className="text-xs text-[#79563F]">
                Review the sections and document checklist to complete intake verification.
              </p>
            </div>
          )}

          {/* Upstream Evidence Resolved Card */}
          <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#1B4D3E]" />
                <span>Resolved Upstream Business Evidence</span>
              </h3>
              <span className="text-xs text-[#79563F] font-medium">Source: Validated KALPA Pipeline</span>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div className="bg-white border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
                  Legal Constitution
                </span>
                <div className="text-sm font-bold text-[#1C1917] mt-1">
                  {fields.legal_constitution?.value || 'Proprietorship / Micro-Unit'}
                </div>
                <div className="mt-2">
                  {renderSourceBadge(fields.legal_constitution?.source_type, fields.legal_constitution?.status)}
                </div>
              </div>

              <div className="bg-white border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
                  Operating Premises
                </span>
                <div className="text-sm font-bold text-[#1C1917] mt-1">
                  {fields.premises_status?.value || 'Owned / Long Lease'}
                </div>
                <div className="mt-2">
                  {renderSourceBadge(fields.premises_status?.source_type, fields.premises_status?.status)}
                </div>
              </div>

              <div className="bg-white border border-[#79563F]/20 rounded-2xl p-4 shadow-2xs">
                <span className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
                  Target Financing Scheme
                </span>
                <div className="text-sm font-bold text-[#1C1917] mt-1">
                  {fields.target_scheme_code?.value || 'PMEGP / MUDRA Category'}
                </div>
                <div className="mt-2">
                  {renderSourceBadge(fields.target_scheme_code?.source_type, fields.target_scheme_code?.status)}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 2: ASSUMPTIONS & BENCHMARK OVERRIDES */}
      {/* ========================================================= */}
      {activeTab === 'assumptions' && (
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
          <div className="flex items-center justify-between pb-2 border-b border-[#79563F]/15">
            <div>
              <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
                Baseline Benchmarks vs Active Scenario
              </h3>
              <p className="text-xs text-[#79563F] mt-0.5">
                Authoritative benchmarks are immutable. You can customize any assumption; downstream financials recalculate deterministically.
              </p>
            </div>
          </div>

          <div className="divide-y divide-[#79563F]/15">
            {Object.entries(contextPackage?.assumptions || {}).map(([key, val], idx) => {
              const fieldRec = fields[key] || {};
              const isOverridden = contextPackage?.overrides && contextPackage.overrides[key] !== undefined;

              return (
                <div key={idx} className="py-4 flex flex-col md:flex-row md:items-center justify-between gap-3">
                  <div>
                    <div className="font-bold text-sm text-[#1C1917] flex items-center gap-2">
                      <span>{fieldRec.label || key.replace(/_/g, ' ').toUpperCase()}</span>
                      {renderSourceBadge(fieldRec.source_type, isOverridden ? 'USER_OVERRIDE' : fieldRec.status)}
                    </div>
                    <div className="text-xs text-[#79563F] mt-1 flex flex-wrap items-center gap-3">
                      <span>
                        Benchmark Baseline:{' '}
                        <strong className="text-[#1C1917]">
                          {typeof val === 'object'
                            ? 'Configured Schedule'
                            : val !== null && val !== undefined
                            ? String(val)
                            : 'Not available'}
                        </strong>
                      </span>
                      <span>
                        Active Value:{' '}
                        <strong className="text-[#1B4D3E]">
                          {typeof fieldRec.value === 'object' && fieldRec.value !== null && Object.keys(fieldRec.value).length > 0
                            ? 'Verified Schedule'
                            : fieldRec.value !== null && fieldRec.value !== undefined && typeof fieldRec.value !== 'object'
                            ? String(fieldRec.value)
                            : 'Not resolved'}
                        </strong>
                      </span>
                    </div>
                  </div>

                  <div className="flex items-center gap-2">
                    {isOverridden && (
                      <button
                        type="button"
                        onClick={() => handleAcceptBenchmark(key)}
                        disabled={recalculating}
                        className="text-xs px-3 py-1.5 bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/25 rounded-xl font-semibold transition cursor-pointer shadow-2xs"
                      >
                        Reset to Benchmark
                      </button>
                    )}
                    <button
                      type="button"
                      onClick={() => {
                        setEditModalField({ field_id: key, ...fieldRec, benchmark_val: val });
                        setEditModalValue(fieldRec.value !== null && fieldRec.value !== undefined ? fieldRec.value : '');
                      }}
                      className="text-xs px-3 py-1.5 bg-white hover:bg-[#FAF7F2] text-[#79563F] border border-[#79563F]/30 rounded-xl font-bold flex items-center gap-1.5 transition cursor-pointer shadow-2xs"
                    >
                      <Edit3 className="w-3.5 h-3.5" />
                      <span>Change</span>
                    </button>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 3: ALL 39 SECTIONS EXPLORER */}
      {/* ========================================================= */}
      {activeTab === 'sections' && (
        <div className="space-y-3 animate-fadeIn">
          {Object.values(modules).map((mod) => (
            <div
              key={mod.module_id}
              className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl overflow-hidden shadow-2xs transition"
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
                        {renderSourceBadge(sec.completeness_status, sec.completeness_status)}
                      </div>
                      <p className="text-xs text-[#79563F] mt-1">{sec.description}</p>

                      {/* Field list within section */}
                      <div className="mt-3 pt-3 border-t border-[#79563F]/10 grid grid-cols-1 sm:grid-cols-2 gap-2">
                        {Object.values(sec.fields || {}).map((f) => (
                          <div
                            key={f.field_id}
                            className="bg-[#FAF2E3]/60 border border-[#79563F]/15 rounded-xl p-2.5 text-xs"
                          >
                            <div className="text-[#79563F] font-medium text-[11px]">{f.label}</div>
                            <div className="flex items-center justify-between mt-1">
                              <span className="font-bold text-[#1C1917]">
                                {typeof f.value === 'object' && f.value !== null && Object.keys(f.value).length > 0
                                  ? 'Verified Schedule'
                                  : f.value !== null && f.value !== undefined && typeof f.value !== 'object'
                                  ? String(f.value)
                                  : 'Not resolved'}
                              </span>
                              {renderSourceBadge(f.source_type, f.status)}
                            </div>
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* ========================================================= */}
      {/* TAB 4: DOCUMENT CHECKLIST */}
      {/* ========================================================= */}
      {activeTab === 'documents' && (
        <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-5 sm:p-6 shadow-2xs space-y-4 animate-fadeIn">
          <div>
            <h3 className="text-base font-bold text-[#1C1917] font-['Outfit']">
              Bank & Scheme Document Enclosure Checklist
            </h3>
            <p className="text-xs text-[#79563F] mt-0.5">
              Track statutory registrations, vendor quotations, and promoter KYC required for bank sanction.
            </p>
          </div>

          <div className="space-y-2.5">
            {contextPackage?.documents && Object.keys(contextPackage.documents).length > 0 ? (
              Object.entries(contextPackage.documents).map(([key, doc], idx) => (
                <div
                  key={idx}
                  className="p-4 bg-white border border-[#79563F]/20 rounded-2xl flex items-center justify-between shadow-2xs"
                >
                  <div>
                    <div className="font-bold text-sm text-[#1C1917]">
                      {doc.document_name || key.replace(/_/g, ' ').toUpperCase()}
                    </div>
                    <div className="text-[11px] text-[#79563F] mt-0.5">
                      Updated: {doc.updated_at ? new Date(doc.updated_at).toLocaleDateString() : 'Initial'}
                    </div>
                  </div>
                  {renderSourceBadge(doc.status, doc.status)}
                </div>
              ))
            ) : (
              <div className="text-xs text-[#79563F] p-4 bg-white border border-dashed border-[#79563F]/25 rounded-2xl text-center">
                No extra document enclosures pending for this project report.
              </div>
            )}
          </div>
        </div>
      )}

      {/* ========================================================= */}
      {/* BOTTOM ACTION BAR */}
      {/* ========================================================= */}
      <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-3xl p-4 sm:p-5 flex flex-col sm:flex-row items-center justify-between gap-3 shadow-2xs">
        <Link
          to={`/swot?session_id=${activeSessionId}&analysis_id=${businessId}`}
          className="px-4 py-2.5 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/25 text-xs font-bold transition flex items-center gap-1.5 shadow-2xs cursor-pointer"
        >
          <ArrowLeft className="w-3.5 h-3.5" />
          <span>Back to SWOT Matrix</span>
        </Link>

        <div className="flex items-center gap-3">
          <button
            type="button"
            onClick={() => {
              navigate(`/dpr/enrichment?business_id=${businessId}&scenario_id=${scenarioId}`, {
                state: { businessId, scenarioId },
              });
            }}
            className="saffron-gradient-btn px-6 py-2.5 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-xs cursor-pointer transition-all hover:scale-[1.02]"
          >
            <span>Proceed to DPR Enrichment →</span>
          </button>
        </div>
      </div>

      {/* ========================================================= */}
      {/* ASSUMPTION EDIT MODAL */}
      {/* ========================================================= */}
      {editModalField && (
        <div className="fixed inset-0 bg-black/40 backdrop-blur-xs z-50 flex items-center justify-center p-4 animate-fadeIn">
          <div className="bg-[#FAF7F2] border border-[#79563F]/30 rounded-3xl max-w-lg w-full p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-[#79563F]/15 pb-3">
              <h3 className="font-bold text-base text-[#1C1917] font-['Outfit']">Edit Assumption</h3>
              <button
                type="button"
                onClick={() => setEditModalField(null)}
                className="text-[#79563F] hover:text-[#1C1917] font-bold text-base cursor-pointer"
              >
                ✕
              </button>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">Field</label>
              <div className="font-bold text-[#1C1917] text-sm">{editModalField.label}</div>
            </div>

            <div className="bg-[#FAF2E3] p-3 rounded-2xl border border-[#79563F]/15 text-xs text-[#79563F]">
              <span>Benchmark Baseline: </span>
              <strong className="text-[#1C1917]">
                {editModalField.benchmark_val !== null && editModalField.benchmark_val !== undefined
                  ? String(editModalField.benchmark_val)
                  : 'Not available'}
              </strong>
            </div>

            <div className="space-y-1">
              <label className="text-[11px] font-bold text-[#79563F] uppercase tracking-wider">
                Your Target Assumption Value
              </label>
              <input
                type="text"
                value={editModalValue}
                onChange={(e) => setEditModalValue(e.target.value)}
                className="w-full bg-white border border-[#79563F]/25 rounded-xl px-4 py-2.5 text-xs sm:text-sm text-[#1C1917] focus:outline-none focus:border-[#79563F] focus:ring-1 focus:ring-[#79563F]/30"
              />
            </div>

            <div className="bg-[#FAF2E3] border border-[#79563F]/20 rounded-2xl p-3 text-xs text-[#79563F] leading-relaxed">
              <strong className="block font-bold text-[#1C1917] mb-0.5">Recalculation Impact:</strong>
              Changing this assumption records an explicit user override, preserving the benchmark baseline, and triggers authoritative financial recalculation.
            </div>

            <div className="flex justify-end gap-3 pt-3 border-t border-[#79563F]/15">
              <button
                type="button"
                onClick={() => setEditModalField(null)}
                className="px-4 py-2 rounded-xl bg-[#FAF2E3] hover:bg-[#F2E8D5] text-[#79563F] text-xs font-bold border border-[#79563F]/20 cursor-pointer"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleApplyOverride}
                disabled={recalculating}
                className="saffron-gradient-btn px-5 py-2 rounded-xl text-xs font-bold shadow-xs cursor-pointer disabled:opacity-50"
              >
                Apply & Recalculate
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default DPRPage;
