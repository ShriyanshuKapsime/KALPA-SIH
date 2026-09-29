import React, {
  useState,
  useEffect,
  useRef,
  useCallback,
  forwardRef,
  useImperativeHandle,
} from 'react';
import {
  Send,
  Sparkles,
  User,
  Trash2,
  RefreshCw,
  Globe,
  HelpCircle,
  Mic,
  MicOff,
  Square,
  Volume2,
  VolumeX,
  Maximize2,
  X,
  Compass,
  ArrowRight,
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';
import { SUPPORTED_LANGUAGES } from '../../i18n/translations';
import AssistantMessageRenderer, { sanitizeAssistantText } from './AssistantMessageRenderer';

export const QUICK_PROMPTS = [
  { key: 'advisor.quick.loans', label: 'Loan & Subsidy Eligibility', text: 'Which government loans and subsidy schemes (like PMEGP, MUDRA or CGTMSE) am I eligible for?' },
  { key: 'advisor.quick.feasibility', label: 'Explain Feasibility Score', text: 'What is my composite feasibility score and what factors contributed to it?' },
  { key: 'advisor.quick.steps', label: 'Top Immediate Next Steps', text: 'What are the top 3 immediate action items I need to execute for venture launch?' },
  { key: 'advisor.quick.market', label: 'Market & Demand Findings', text: 'What are the main market demand findings and customer cluster insights?' },
  { key: 'advisor.quick.risks', label: 'Risk Factors & Mitigation', text: 'What are the key operational and financial risk factors identified and how do I mitigate them?' },
  { key: 'advisor.quick.emi', label: 'Capital, Loan & EMI Details', text: 'Can you break down my total project cost, required bank loan, and estimated monthly EMI?' },
];

export const LANGUAGES = SUPPORTED_LANGUAGES;

const formatAssistantErrorMessage = (err) => {
  const status = Number(err?.status || err?.statusCode || (err?.response && err.response.status) || 0);
  const msg = (err?.message || '').toLowerCase();
  const details = (err?.details || '').toLowerCase();

  if (status === 404) {
    return 'Assistant service endpoint is unavailable.';
  }
  if (status === 401 || status === 403) {
    return 'Assistant service authentication or configuration issue.';
  }
  if (status === 429) {
    return 'Assistant service is temporarily busy. Please retry in a moment.';
  }
  if (status === 408 || msg.includes('timeout') || err?.code === 'ECONNABORTED') {
    return 'Assistant took too long to respond. Please retry.';
  }
  if (status >= 500 && status <= 599) {
    if (msg.includes('inference') || details.includes('inference') || msg.includes('sarvam') || details.includes('sarvam')) {
      return 'KALPA assistant is temporarily unable to reach the AI model. Your analysis data remains safely stored. Please try again.';
    }
    return 'Assistant service encountered an issue. Please try again.';
  }
  return err?.message || 'Assistant service encountered an issue. Please try again.';
};

export const AssistantChatCore = forwardRef(function AssistantChatCore(
  {
    mode = 'fullpage', // 'floating' | 'fullpage'
    onMaximize,
    onClose,
    className = '',
    externalLanguage,
    onLanguageChange: onExternalLanguageChange,
  },
  ref
) {
  const { analysisId, sessionId, businessName, businessId } = useWorkflow();
  const { language: globalLanguage, setLanguage: setGlobalLanguage, t } = useLanguage();

  const effectiveAnalysisId = analysisId || sessionStorage.getItem('kalpa_analysis_id') || '';
  const effectiveSessionId = sessionId || sessionStorage.getItem('kalpa_session_id') || '';
  const effectiveBusinessId = businessId || sessionStorage.getItem('kalpa_business_id') || '';
  const targetId = effectiveAnalysisId || effectiveSessionId || effectiveBusinessId;

  const [messages, setMessages] = useState(() => {
    try {
      const raw = sessionStorage.getItem('kalpa_assistant_cached_messages');
      return raw ? JSON.parse(raw) : [];
    } catch {
      return [];
    }
  });

  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);

  const language = externalLanguage || globalLanguage || 'en';

  const [contextData, setContextData] = useState(null);
  const [contextCompleteness, setContextCompleteness] = useState(0.0);

  // Voice Recording (STT)
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingSTT, setIsProcessingSTT] = useState(false);
  const [sttStatusMessage, setSttStatusMessage] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Voice Playback (TTS)
  const [playingMessageIdx, setPlayingMessageIdx] = useState(null);
  const [ttsLoadingIdx, setTtsLoadingIdx] = useState(null);
  const currentAudioRef = useRef(null);
  const ttsCacheRef = useRef({});

  // Chat scroll container ref and sentinel
  const scrollContainerRef = useRef(null);
  const messagesEndRef = useRef(null);
  const isUserNearBottomRef = useRef(true);

  // Persist language to global state & session
  const handleLanguageChange = (newLang) => {
    if (setGlobalLanguage) {
      setGlobalLanguage(newLang);
    }
    sessionStorage.setItem('kalpa_assistant_language', newLang);
    if (onExternalLanguageChange) {
      onExternalLanguageChange(newLang);
    }
  };

  // Persist messages cache to session storage
  useEffect(() => {
    try {
      if (messages.length > 0) {
        sessionStorage.setItem('kalpa_assistant_cached_messages', JSON.stringify(messages));
      }
    } catch (e) {}
  }, [messages]);

  // Track if user is scrolled near bottom of the chat container
  const handleScroll = useCallback(() => {
    if (!scrollContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = scrollContainerRef.current;
    const distanceToBottom = scrollHeight - scrollTop - clientHeight;
    isUserNearBottomRef.current = distanceToBottom <= 100;
  }, []);

  const scrollToBottomSmooth = (force = false) => {
    if (force || isUserNearBottomRef.current) {
      messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }
  };

  // Scroll to bottom when messages change if user was near bottom
  useEffect(() => {
    scrollToBottomSmooth(false);
  }, [messages, isLoading, isRecording, isProcessingSTT]);

  // Clean up audio on unmount
  useEffect(() => {
    return () => {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
        mediaRecorderRef.current.stop();
      }
    };
  }, []);

  // Load history & context on mount
  useEffect(() => {
    if (!targetId) return;

    const loadData = async () => {
      try {
        const [histRes, ctxRes] = await Promise.allSettled([
          apiService.assistant.getHistory(targetId),
          apiService.assistant.getContext(targetId),
        ]);

        if (histRes.status === 'fulfilled' && histRes.value?.messages) {
          const formatted = [];
          histRes.value.messages.forEach((m) => {
            if (m.user_message) {
              formatted.push({
                sender: 'user',
                text: m.user_message,
                timestamp: m.created_at,
              });
            }
            if (m.assistant_response) {
              formatted.push({
                sender: 'assistant',
                text: m.assistant_response,
                intent: m.intent,
                groundedSources: m.grounded_sources || [],
                suggestedActions: m.suggested_actions || [],
                timestamp: m.created_at,
              });
            }
          });
          if (formatted.length > 0) {
            setMessages(formatted);
          }
        }

        if (ctxRes.status === 'fulfilled' && ctxRes.value?.context) {
          setContextData(ctxRes.value.context);
          if (ctxRes.value.context_completeness) {
            setContextCompleteness(ctxRes.value.context_completeness);
          }
        }
      } catch (err) {
        console.warn('[ASSISTANT CHAT] Load error:', err);
      }
    };

    loadData();
  }, [targetId]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputValue;
    if (!text.trim() || isLoading) return;

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingMessageIdx(null);
    }

    const userTurn = {
      sender: 'user',
      text: text.trim(),
      timestamp: new Date().toISOString(),
    };

    setMessages((prev) => [...prev, userTurn]);
    setInputValue('');
    setIsLoading(true);

    // Force scroll container to bottom when user explicitly sends a message
    setTimeout(() => scrollToBottomSmooth(true), 50);

    try {
      let storedFinContext = null;
      let storedFinAnalysis = null;
      try {
        const rawCtx = sessionStorage.getItem('kalpa_financial_context');
        if (rawCtx) storedFinContext = JSON.parse(rawCtx);
        const rawFa = sessionStorage.getItem('kalpa_financial_analysis');
        if (rawFa) storedFinAnalysis = JSON.parse(rawFa);
      } catch (e) {}

      const response = await apiService.assistant.chat({
        analysis_id: effectiveAnalysisId || null,
        session_id: effectiveSessionId || null,
        business_id: effectiveBusinessId || undefined,
        message: text.trim(),
        language,
        financial_context: storedFinContext || undefined,
        financial_analysis: storedFinAnalysis || undefined,
      });

      const assistantTurn = {
        sender: 'assistant',
        text: response.assistant_response,
        intent: response.intent,
        groundedSources: response.grounded_sources || [],
        groundingStatus: response.grounding_status || 'GROUNDED',
        modelProvider: response.model_provider || 'KALPA AI Advisor',
        completeness: response.pipeline_completeness || contextCompleteness,
        suggestedActions: response.suggested_actions || [],
        timestamp: new Date().toISOString(),
      };

      if (response.pipeline_completeness) {
        setContextCompleteness(response.pipeline_completeness);
      }

      setMessages((prev) => [...prev, assistantTurn]);
    } catch (err) {
      console.error('[ASSISTANT CHAT ERROR]:', err);
      setMessages((prev) => [
        ...prev,
        {
          sender: 'assistant',
          text: formatAssistantErrorMessage(err),
          isError: true,
          failedMessage: text.trim(),
          timestamp: new Date().toISOString(),
        },
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleClearHistory = async () => {
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingMessageIdx(null);
    }
    try {
      if (targetId) {
        await apiService.assistant.clearHistory(targetId);
      }
      setMessages([]);
      sessionStorage.removeItem('kalpa_assistant_cached_messages');
    } catch (err) {
      console.error('[ASSISTANT CHAT] Clear history error:', err);
      setMessages([]);
      sessionStorage.removeItem('kalpa_assistant_cached_messages');
    }
  };

  // Expose imperative handle for parent components
  useImperativeHandle(ref, () => ({
    clearHistory: handleClearHistory,
    setLanguage: handleLanguageChange,
    language,
    sendMessage: handleSendMessage,
    hasMessages: messages.length > 0,
  }));

  // Voice Input (STT)
  const handleStartRecording = async () => {
    if (isRecording || isProcessingSTT) return;
    setSttStatusMessage(null);

    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      audioChunksRef.current = [];

      const mediaRecorder = new MediaRecorder(stream, {
        mimeType: MediaRecorder.isTypeSupported('audio/webm') ? 'audio/webm' : 'audio/mp4',
      });

      mediaRecorder.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorder.onstop = async () => {
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || 'audio/webm',
        });

        if (audioBlob.size < 500) {
          setSttStatusMessage('Recording too short. Please speak again.');
          setTimeout(() => setSttStatusMessage(null), 3500);
          return;
        }

        setIsProcessingSTT(true);
        setSttStatusMessage('Transcribing speech...');

        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          formData.append('language', language);

          const res = await apiService.assistant.stt(formData);
          if (res?.text && res.text.trim()) {
            setInputValue((prev) => (prev ? `${prev} ${res.text.trim()}` : res.text.trim()));
            setSttStatusMessage('Voice transcribed! You can review or edit before sending.');
          } else {
            setSttStatusMessage("Could not understand audio. Please try again or type.");
          }
        } catch (sttErr) {
          console.error('[STT ERROR]:', sttErr);
          setSttStatusMessage("Voice transcription unavailable. Please type your query.");
        } finally {
          setIsProcessingSTT(false);
          setTimeout(() => setSttStatusMessage(null), 4000);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setSttStatusMessage('Listening... Speak your question.');
    } catch (micErr) {
      console.error('[MIC ERROR]:', micErr);
      setSttStatusMessage('Microphone access denied. Please check browser permissions.');
      setTimeout(() => setSttStatusMessage(null), 4000);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // Voice Output (TTS)
  const handleToggleTTS = async (text, messageIndex) => {
    if (playingMessageIdx === messageIndex) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      setPlayingMessageIdx(null);
      return;
    }

    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingMessageIdx(null);
    }

    const cleanText = sanitizeAssistantText(text);
    const cacheKey = `${language}:${cleanText}`;

    if (ttsCacheRef.current[cacheKey]) {
      const audio = new Audio(`data:audio/wav;base64,${ttsCacheRef.current[cacheKey]}`);
      currentAudioRef.current = audio;
      setPlayingMessageIdx(messageIndex);

      audio.onended = () => {
        setPlayingMessageIdx(null);
        currentAudioRef.current = null;
      };
      audio.onerror = () => {
        setPlayingMessageIdx(null);
        currentAudioRef.current = null;
      };

      try {
        await audio.play();
      } catch (playErr) {
        console.warn('[TTS PLAY ERROR]:', playErr);
        setPlayingMessageIdx(null);
      }
      return;
    }

    setTtsLoadingIdx(messageIndex);
    try {
      const response = await apiService.assistant.tts({
        text: cleanText,
        language,
      });

      if (response?.audio_base64) {
        ttsCacheRef.current[cacheKey] = response.audio_base64;
        const audio = new Audio(`data:audio/wav;base64,${response.audio_base64}`);
        currentAudioRef.current = audio;
        setPlayingMessageIdx(messageIndex);

        audio.onended = () => {
          setPlayingMessageIdx(null);
          currentAudioRef.current = null;
        };
        audio.onerror = () => {
          setPlayingMessageIdx(null);
          currentAudioRef.current = null;
        };

        await audio.play();
      }
    } catch (ttsErr) {
      console.error('[TTS ERROR]:', ttsErr);
    } finally {
      setTtsLoadingIdx(null);
    }
  };

  const isFloating = mode === 'floating';

  return (
    <div
      className={`flex flex-col bg-[#FAF7F2] border border-[#79563F]/20 rounded-3xl overflow-hidden shadow-xs h-full w-full ${className}`}
    >
      {/* Top Floating Chat Header (if in floating mode) */}
      {isFloating ? (
        <div className="bg-[#FAF2E3] px-4 py-3.5 border-b border-[#79563F]/18 flex items-center justify-between gap-3 select-none flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-[#FAF7F2] border border-[#79563F]/25 text-[#79563F] flex items-center justify-center flex-shrink-0 shadow-2xs">
              <Sparkles className="w-4 h-4 text-[#79563F]" />
            </div>
            <div className="min-w-0">
              <h3 className="font-['Outfit'] font-bold text-sm text-[#1C1917] truncate">
                {t('advisor.title', 'KALPA AI Advisor')}
              </h3>
              <p className="text-[11px] text-[#79563F] truncate">
                {businessName || t('advisor.subtitle', 'Business analysis context active')}
              </p>
            </div>
          </div>

          <div className="flex items-center gap-1.5 flex-shrink-0">
            {/* Language Selector in Floating Header */}
            <div className="flex items-center bg-[#FAF7F2] border border-[#79563F]/20 rounded-lg px-2 py-1 text-[11px] text-[#79563F]">
              <Globe className="w-3 h-3 mr-1 text-[#79563F]" />
              <select
                value={language}
                onChange={(e) => handleLanguageChange(e.target.value)}
                className="bg-transparent text-[11px] text-[#79563F] font-semibold focus:outline-none cursor-pointer"
              >
                {LANGUAGES.map((l) => (
                  <option key={l.code} value={l.code} className="bg-white text-[#1C1917]">
                    {l.native}
                  </option>
                ))}
              </select>
            </div>

            {onMaximize && (
              <button
                type="button"
                onClick={onMaximize}
                title="Maximize to full-page workspace"
                className="p-1.5 rounded-lg hover:bg-[#FAF7F2] text-[#79563F] transition-colors cursor-pointer"
                aria-label="Maximize"
              >
                <Maximize2 className="w-4 h-4" />
              </button>
            )}

            {onClose && (
              <button
                type="button"
                onClick={onClose}
                title="Close chat"
                className="p-1.5 rounded-lg hover:bg-[#FAF7F2] text-[#79563F] transition-colors cursor-pointer"
                aria-label="Close"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>
      ) : (
        /* Full-page Chat Internal Header */
        <div className="bg-[#FAF2E3]/90 px-5 py-3 border-b border-[#79563F]/15 flex items-center justify-between gap-3 select-none flex-shrink-0">
          <div className="flex items-center gap-2.5 min-w-0">
            <div className="w-8 h-8 rounded-xl bg-[#FAF7F2] border border-[#79563F]/25 text-[#79563F] flex items-center justify-center flex-shrink-0 shadow-2xs">
              <Sparkles className="w-4 h-4 text-[#79563F]" />
            </div>
            <div className="min-w-0">
              <h2 className="font-['Outfit'] font-bold text-sm sm:text-base text-[#1C1917] truncate">
                {t('advisor.title', 'KALPA AI Advisor')}
              </h2>
              <p className="text-[11px] text-[#79563F] truncate">
                {businessName ? `${businessName} • ` : ''}{t('advisor.subtitle', 'Business analysis context available')}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Internal Independent Message Scroll Container */}
      <div
        ref={scrollContainerRef}
        onScroll={handleScroll}
        className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4 min-h-0 bg-[#FAF7F2]"
      >
        {/* Clean Empty State */}
        {messages.length === 0 && (
          <div className="text-center py-8 sm:py-12 px-4 max-w-md mx-auto space-y-4 animate-fadeIn">
            <div className="w-12 h-12 rounded-2xl bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 flex items-center justify-center mx-auto shadow-2xs">
              <Sparkles className="w-6 h-6 text-[#79563F]" />
            </div>
            <div className="space-y-1">
              <h3 className="font-['Outfit'] font-bold text-base sm:text-lg text-[#1C1917]">
                {t('advisor.how_help', 'How can I help?')}
              </h3>
              <p className="text-xs text-[#79563F] leading-relaxed">
                {t('advisor.empty_desc', 'Ask about your business analysis, financing options, risk mitigations or next steps.')}
              </p>
            </div>

            {/* Quick Questions (No Emojis) */}
            <div className="pt-2 flex flex-wrap justify-center gap-2 text-left">
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  type="button"
                  onClick={() => handleSendMessage(qp.text)}
                  className="px-3 py-1.5 rounded-xl bg-[#FAF2E3] hover:bg-[#F2E8D5] text-[#79563F] hover:text-[#1C1917] border border-[#79563F]/20 text-xs font-semibold transition-colors cursor-pointer text-left shadow-2xs"
                >
                  {t(qp.key, qp.label)}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* Message Bubble List */}
        {messages.map((m, idx) => (
          <div
            key={idx}
            className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'} animate-fadeIn`}
          >
            {m.sender === 'assistant' && (
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 flex items-center justify-center shrink-0 shadow-2xs mt-0.5">
                <Sparkles className="w-4 h-4 text-[#79563F]" />
              </div>
            )}

            <div
              className={`max-w-[88%] sm:max-w-[82%] rounded-2xl p-4 text-xs sm:text-[13px] leading-relaxed space-y-2.5 shadow-2xs ${
                m.sender === 'user'
                  ? 'bg-[#FAF2E3] text-[#1C1917] border border-[#79563F]/20 rounded-br-xs'
                  : m.isError
                  ? 'bg-rose-50 text-rose-900 border border-rose-200 rounded-bl-xs'
                  : 'bg-white text-[#1C1917] border border-[#79563F]/15 rounded-bl-xs'
              }`}
            >
              {/* Assistant Message Header Bar */}
              {m.sender === 'assistant' && (
                <div className="flex items-center justify-between gap-2 pb-2 border-b border-[#79563F]/10">
                  <div className="flex items-center gap-2">
                    <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20 uppercase tracking-wider">
                      {(m.intent || 'ADVISORY').replace(/_/g, ' ')}
                    </span>
                    <span className="text-[10px] text-[#1B4D3E] bg-[#EAF5EE] px-2 py-0.5 rounded border border-[#1B4D3E]/20 font-medium flex items-center gap-1">
                      <span className="w-1.5 h-1.5 rounded-full bg-[#1B4D3E] animate-pulse"></span>
                      KALPA AI
                    </span>
                  </div>

                  {/* TTS Voice Listen Button */}
                  {!m.isError && (
                    <button
                      type="button"
                      onClick={() => handleToggleTTS(m.text, idx)}
                      disabled={ttsLoadingIdx === idx}
                      title={playingMessageIdx === idx ? 'Stop voice playback' : 'Listen to voice playback'}
                      className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-semibold transition-all cursor-pointer shadow-2xs ${
                        playingMessageIdx === idx
                          ? 'bg-[#79563F] text-white animate-pulse'
                          : 'bg-[#FAF2E3] hover:bg-[#F2E8D5] text-[#79563F] border border-[#79563F]/25'
                      }`}
                    >
                      {ttsLoadingIdx === idx ? (
                        <>
                          <RefreshCw className="w-3 h-3 animate-spin text-[#79563F]" />
                          <span>Voice loading...</span>
                        </>
                      ) : playingMessageIdx === idx ? (
                        <>
                          <VolumeX className="w-3 h-3" />
                          <span>Stop</span>
                        </>
                      ) : (
                        <>
                          <Volume2 className="w-3 h-3 text-[#79563F]" />
                          <span>Listen</span>
                        </>
                      )}
                    </button>
                  )}
                </div>
              )}

              {/* Message Content */}
              {m.sender === 'user' ? (
                <div className="whitespace-pre-wrap font-medium">{m.text}</div>
              ) : m.isError ? (
                <div className="font-medium text-rose-800">{m.text}</div>
              ) : (
                <AssistantMessageRenderer content={m.text} />
              )}

              {/* Retry on Error */}
              {m.isError && m.failedMessage && (
                <button
                  type="button"
                  onClick={() => handleSendMessage(m.failedMessage)}
                  className="mt-2 text-[11px] px-3 py-1 bg-rose-100 hover:bg-rose-200 text-rose-800 font-semibold rounded-lg flex items-center gap-1.5 transition-colors cursor-pointer"
                >
                  <RefreshCw className="w-3 h-3" /> Retry Message
                </button>
              )}

              {/* Grounded Sources */}
              {m.groundedSources && m.groundedSources.length > 0 && (
                <div className="pt-2 border-t border-[#79563F]/10 space-y-1">
                  <div className="text-[10px] text-[#79563F]/70 font-bold uppercase tracking-wider">
                    Grounded In Verified Sources:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.groundedSources.map((src, sIdx) => {
                      const desc = typeof src === 'string' ? src : (src.description || src.source || '');
                      const cleanDesc = sanitizeAssistantText(desc);
                      return (
                        <span
                          key={sIdx}
                          className="px-2 py-0.5 rounded-md text-[10px] font-medium bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/20 flex items-center gap-1"
                        >
                          <span>{cleanDesc}</span>
                        </span>
                      );
                    })}
                  </div>
                </div>
              )}

              {/* Dynamic Suggested Follow-ups */}
              {m.suggestedActions && m.suggestedActions.length > 0 && (
                <div className="pt-2 space-y-1.5 border-t border-[#79563F]/10">
                  <div className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider">
                    Suggested Follow-Up:
                  </div>
                  <div className="flex flex-wrap gap-1.5">
                    {m.suggestedActions.map((act, aIdx) => (
                      <button
                        key={aIdx}
                        type="button"
                        onClick={() => handleSendMessage(act)}
                        className="text-[11px] px-2.5 py-1 rounded-lg bg-[#FAF2E3] hover:bg-[#F2E8D5] text-[#79563F] border border-[#79563F]/25 transition-colors text-left cursor-pointer"
                      >
                        {sanitizeAssistantText(act)}
                      </button>
                    ))}
                  </div>
                </div>
              )}
            </div>

            {m.sender === 'user' && (
              <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-[#79563F] text-[#FAF4E8] flex items-center justify-center shrink-0 shadow-2xs mt-0.5">
                <User className="w-4 h-4" />
              </div>
            )}
          </div>
        ))}

        {/* Loading Bubble */}
        {isLoading && (
          <div className="flex gap-3 justify-start items-center animate-fadeIn">
            <div className="w-7 h-7 sm:w-8 sm:h-8 rounded-xl bg-[#FAF2E3] text-[#79563F] border border-[#79563F]/25 flex items-center justify-center shrink-0 shadow-2xs animate-pulse">
              <Sparkles className="w-4 h-4 text-[#79563F]" />
            </div>
            <div className="bg-white border border-[#79563F]/18 rounded-2xl rounded-bl-xs p-3.5 text-xs text-[#79563F] flex items-center gap-2 shadow-2xs">
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#79563F]" />
              <span>{t('advisor.analyzing', 'Analyzing verified business evidence & formulating tailored guidance...')}</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* STT Status Toast Banner */}
      {sttStatusMessage && (
        <div className="px-4 py-2 bg-[#FAF2E3] border-t border-[#79563F]/15 text-[#79563F] text-xs flex items-center justify-between flex-shrink-0 animate-fadeIn">
          <div className="flex items-center gap-2">
            {isProcessingSTT ? (
              <RefreshCw className="w-3.5 h-3.5 animate-spin text-[#79563F]" />
            ) : isRecording ? (
              <span className="w-2.5 h-2.5 rounded-full bg-rose-600 animate-ping" />
            ) : (
              <HelpCircle className="w-3.5 h-3.5 text-[#79563F]" />
            )}
            <span className="font-medium">{sttStatusMessage}</span>
          </div>
          {isRecording && (
            <button
              type="button"
              onClick={handleStopRecording}
              className="px-2 py-0.5 rounded bg-rose-700 text-white font-bold text-[10px] cursor-pointer"
            >
              {t('common.stop', 'Stop')}
            </button>
          )}
        </div>
      )}

      {/* Sticky Bottom Chat Composer */}
      <div className="p-3 sm:p-4 bg-[#FAF2E3]/90 backdrop-blur-xs border-t border-[#79563F]/18 flex-shrink-0">
        <form
          onSubmit={(e) => {
            e.preventDefault();
            handleSendMessage();
          }}
          className="flex items-center gap-2"
        >
          {/* Microphone Voice Button (Minimum 40px touch target) */}
          <button
            type="button"
            onClick={isRecording ? handleStopRecording : handleStartRecording}
            disabled={isProcessingSTT || isLoading}
            title={isRecording ? 'Click to stop speaking' : 'Speak your question in your preferred language'}
            className={`w-10 h-10 min-w-[40px] rounded-xl flex items-center justify-center transition-all shrink-0 cursor-pointer shadow-2xs ${
              isRecording
                ? 'bg-rose-700 text-white animate-pulse ring-4 ring-rose-200'
                : isProcessingSTT
                ? 'bg-[#FAF7F2] text-[#79563F]'
                : 'bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/25 hover:border-[#79563F]/40'
            }`}
          >
            {isProcessingSTT ? (
              <RefreshCw className="w-4 h-4 animate-spin text-[#79563F]" />
            ) : isRecording ? (
              <Square className="w-4 h-4 text-white" />
            ) : (
              <Mic className="w-4 h-4 text-[#79563F]" />
            )}
          </button>

          {/* Text Input */}
          <input
            type="text"
            value={inputValue}
            onChange={(e) => setInputValue(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                handleSendMessage();
              }
            }}
            placeholder={
              isRecording
                ? t('advisor.listening', 'Listening to speech...')
                : isProcessingSTT
                ? t('advisor.transcribing', 'Transcribing audio...')
                : t('advisor.placeholder', 'Ask about your business, finance, market or next steps...')
            }
            disabled={isRecording || isProcessingSTT || isLoading}
            className="flex-1 px-4 py-2.5 bg-white rounded-xl border border-[#79563F]/25 text-xs sm:text-sm text-[#1C1917] placeholder:text-[#79563F]/50 focus:outline-none focus:border-[#79563F] focus:ring-1 focus:ring-[#79563F]/30 transition-all"
          />

          {/* Saffron/Terracotta Send Button */}
          <button
            type="submit"
            disabled={!inputValue.trim() || isLoading || isRecording || isProcessingSTT}
            className="saffron-gradient-btn h-10 px-4 rounded-xl text-xs font-bold flex items-center gap-1.5 shadow-xs cursor-pointer transition-all hover:scale-[1.02] disabled:opacity-50 disabled:hover:scale-100 shrink-0"
          >
            <span>{t('advisor.send', 'Send')}</span>
            <Send className="w-3.5 h-3.5" />
          </button>
        </form>
      </div>
    </div>
  );
});

export default AssistantChatCore;
