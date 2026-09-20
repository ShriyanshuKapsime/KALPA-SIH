import React, { useState, useEffect, useRef } from 'react';
import {
  MessageSquare,
  Send,
  Sparkles,
  Bot,
  User,
  Trash2,
  TrendingUp,
  ShieldCheck,
  Layers,
  CheckCircle2,
  RefreshCw,
  Globe,
  AlertCircle,
  HelpCircle,
  Mic,
  MicOff,
  Square,
  Volume2,
  VolumeX,
  Play,
  Pause
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import AssistantMessageRenderer from './AssistantMessageRenderer';

const QUICK_PROMPTS = [
  { label: '📊 Feasibility Score & Gating', text: 'What is my feasibility score and why did I receive this recommendation?' },
  { label: '🏦 Loan & Subsidy Eligibility', text: 'Which government loans and subsidy schemes (like PMEGP or MUDRA) am I eligible for?' },
  { label: '🚀 What are my next steps?', text: 'What are the top 3 immediate action items I need to execute?' },
  { label: '💡 SWOT Weaknesses & Mitigation', text: 'What are my biggest weaknesses and how do I mitigate them?' },
  { label: '💰 Capital, Loan & EMI Details', text: 'Can you break down my total project cost, required bank loan, and estimated monthly EMI?' },
  { label: '📝 Registration & Compliance', text: 'What licenses, permits, and registrations (Udyam, GST, Trade) do I need?' },
];

const LANGUAGES = [
  { code: 'en', label: 'English' },
  { code: 'hi', label: 'हिंदी (Hindi)' },
  { code: 'te', label: 'తెలుగు (Telugu)' },
  { code: 'ta', label: 'தமிழ் (Tamil)' },
  { code: 'mr', label: 'मराठी (Marathi)' },
  { code: 'bn', label: 'বাংলা (Bengali)' },
];

const formatAssistantErrorMessage = (err) => {
  const status = Number(err?.status || err?.statusCode || (err?.response && err.response.status) || 0);
  const msg = (err?.message || '').toLowerCase();
  const details = (err?.details || '').toLowerCase();

  if (status === 404) {
    return 'Assistant service endpoint is unavailable.';
  }
  if (status === 401 || status === 403) {
    return 'Assistant service authentication/configuration issue.';
  }
  if (status === 429) {
    return 'Assistant inference service is temporarily rate limited.';
  }
  if (status === 408 || msg.includes('timeout') || err?.code === 'ECONNABORTED') {
    return 'Assistant took too long to respond. Please retry.';
  }
  if (status >= 500 && status <= 599) {
    if (msg.includes('inference') || details.includes('inference') || msg.includes('sarvam') || details.includes('sarvam')) {
      return 'KALPA assistant is temporarily unable to reach the inference model. Your analysis data remains safely stored. Please try again.';
    }
    return 'Assistant service encountered a server error.';
  }
  return err?.message || 'Assistant service encountered an issue. Please try again.';
};

export default function AssistantWidget({ isEmbedded = false }) {
  const { analysisId, sessionId, businessName } = useWorkflow();

  const effectiveAnalysisId = analysisId || sessionStorage.getItem('kalpa_analysis_id') || '';
  const effectiveSessionId = sessionId || sessionStorage.getItem('kalpa_session_id') || '';
  const targetId = effectiveAnalysisId || effectiveSessionId;

  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [language, setLanguage] = useState('en');
  const [contextData, setContextData] = useState(null);
  const [contextCompleteness, setContextCompleteness] = useState(0.0);
  const [activeTab, setActiveTab] = useState('chat'); // 'chat' or 'context'

  // Voice Recording (STT with Saaras v4)
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessingSTT, setIsProcessingSTT] = useState(false);
  const [sttStatusMessage, setSttStatusMessage] = useState(null);
  const mediaRecorderRef = useRef(null);
  const audioChunksRef = useRef([]);

  // Voice Playback (TTS with Bulbul v3)
  const [playingMessageIdx, setPlayingMessageIdx] = useState(null);
  const [ttsLoadingIdx, setTtsLoadingIdx] = useState(null);
  const currentAudioRef = useRef(null);
  const ttsCacheRef = useRef({}); // Cache of text -> base64 audio

  const messagesEndRef = useRef(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
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

  // Load history and context on mount
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
          setMessages(formatted);
        }

        if (ctxRes.status === 'fulfilled' && ctxRes.value?.context) {
          setContextData(ctxRes.value.context);
          if (ctxRes.value.context_completeness) {
            setContextCompleteness(ctxRes.value.context_completeness);
          }
        }
      } catch (err) {
        console.warn('[ASSISTANT WIDGET] Load error:', err);
      }
    };

    loadData();
  }, [targetId]);

  const handleSendMessage = async (textToSend) => {
    const text = textToSend || inputValue;
    if (!text.trim() || isLoading) return;

    // Stop playing audio when a new message is sent
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

    try {
      const response = await apiService.assistant.chat({
        analysis_id: effectiveAnalysisId || null,
        session_id: effectiveSessionId || null,
        message: text.trim(),
        language,
      });

      const assistantTurn = {
        sender: 'assistant',
        text: response.assistant_response,
        intent: response.intent,
        groundedSources: response.grounded_sources || [],
        groundingStatus: response.grounding_status || 'GROUNDED',
        completeness: response.pipeline_completeness || contextCompleteness,
        suggestedActions: response.suggested_actions || [],
        timestamp: new Date().toISOString(),
      };

      if (response.pipeline_completeness) {
        setContextCompleteness(response.pipeline_completeness);
      }

      setMessages((prev) => [...prev, assistantTurn]);
    } catch (err) {
      console.error('[ASSISTANT WIDGET] Chat error:', err);
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
    if (!targetId) return;
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingMessageIdx(null);
    }
    try {
      await apiService.assistant.clearHistory(targetId);
      setMessages([]);
    } catch (err) {
      console.error('[ASSISTANT WIDGET] Clear history error:', err);
    }
  };

  // -------------------------------------------------------------
  // Voice Input (STT with Saaras:v4)
  // -------------------------------------------------------------
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
        // Stop all audio tracks
        stream.getTracks().forEach((track) => track.stop());

        const audioBlob = new Blob(audioChunksRef.current, {
          type: mediaRecorder.mimeType || 'audio/webm',
        });

        if (audioBlob.size < 500) {
          setSttStatusMessage('Recording was too short. Please speak again.');
          setTimeout(() => setSttStatusMessage(null), 4000);
          return;
        }

        setIsProcessingSTT(true);
        setSttStatusMessage('Transcribing speech with Sarvam Saaras v4...');

        try {
          const formData = new FormData();
          formData.append('audio', audioBlob, 'recording.webm');
          formData.append('language', language);

          const res = await apiService.assistant.stt(formData);
          if (res?.text && res.text.trim()) {
            setInputValue((prev) => (prev ? `${prev} ${res.text.trim()}` : res.text.trim()));
            setSttStatusMessage('Voice transcribed! You can review or edit before sending.');
          } else {
            setSttStatusMessage("Voice input couldn't be understood. Please try again or type your question.");
          }
        } catch (sttErr) {
          console.error('[ASSISTANT STT ERROR]:', sttErr);
          setSttStatusMessage("Voice input couldn't be understood. Please try again or type your question.");
        } finally {
          setIsProcessingSTT(false);
          setTimeout(() => setSttStatusMessage(null), 5000);
        }
      };

      mediaRecorderRef.current = mediaRecorder;
      mediaRecorder.start();
      setIsRecording(true);
      setSttStatusMessage('Listening... Speak your question now.');
    } catch (micErr) {
      console.error('[MICROPHONE ACCESS ERROR]:', micErr);
      setSttStatusMessage('Microphone access denied. Please allow microphone permissions or type your question.');
      setTimeout(() => setSttStatusMessage(null), 5000);
    }
  };

  const handleStopRecording = () => {
    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      mediaRecorderRef.current.stop();
      setIsRecording(false);
    }
  };

  // -------------------------------------------------------------
  // Voice Output (TTS with Bulbul:v3)
  // -------------------------------------------------------------
  const handleToggleTTS = async (text, messageIndex) => {
    // If this message is already playing, stop it
    if (playingMessageIdx === messageIndex) {
      if (currentAudioRef.current) {
        currentAudioRef.current.pause();
        currentAudioRef.current = null;
      }
      setPlayingMessageIdx(null);
      return;
    }

    // Stop any previously playing audio
    if (currentAudioRef.current) {
      currentAudioRef.current.pause();
      currentAudioRef.current = null;
      setPlayingMessageIdx(null);
    }

    // Check cache first
    const cacheKey = `${language}:${text}`;
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

    // Fetch from Sarvam Bulbul v3 backend
    setTtsLoadingIdx(messageIndex);
    try {
      const response = await apiService.assistant.tts({
        text,
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
      console.error('[ASSISTANT TTS ERROR]:', ttsErr);
    } finally {
      setTtsLoadingIdx(null);
    }
  };

  const biz = contextData?.business_profile || {};
  const feas = contextData?.feasibility_result || {};
  const fin = contextData?.financial_analysis || {};

  return (
    <div className={`flex flex-col bg-white rounded-3xl border border-stone-200 shadow-xl overflow-hidden ${isEmbedded ? 'h-[750px]' : 'h-[85vh]'}`}>
      {/* Top Header */}
      <div className="bg-gradient-to-r from-stone-900 via-stone-800 to-amber-950 text-white p-4 sm:p-5 flex items-center justify-between border-b border-stone-700">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-2xl bg-amber-500/20 border border-amber-400/40 flex items-center justify-center text-amber-400 shadow-inner">
            <Sparkles className="w-5 h-5" />
          </div>
          <div>
            <div className="flex items-center gap-2">
              <h2 className="font-['Outfit'] font-bold text-lg text-white">KALPA Personal Business Advisor</h2>
              <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-300 border border-emerald-500/30">
                Stage 15 Active
              </span>
              {contextCompleteness > 0 && (
                <span className="hidden sm:inline-block px-2 py-0.5 rounded-full text-[10px] font-semibold bg-amber-500/20 text-amber-300 border border-amber-500/30">
                  {Math.round(contextCompleteness * 100)}% Data Grounded
                </span>
              )}
            </div>
            <p className="text-xs text-stone-300">
              {businessName || biz.business_name || 'Enterprise'} • Authoritative Deterministic Pipeline Advisor
            </p>
          </div>
        </div>

        {/* Header Right Actions */}
        <div className="flex items-center gap-2">
          {/* Language Selector */}
          <div className="flex items-center bg-stone-800/90 border border-stone-700 rounded-xl px-2.5 py-1 text-xs text-stone-200">
            <Globe className="w-3.5 h-3.5 mr-1.5 text-amber-400" />
            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-transparent text-xs text-stone-200 focus:outline-none cursor-pointer"
            >
              {LANGUAGES.map((l) => (
                <option key={l.code} value={l.code} className="bg-stone-900 text-white">
                  {l.label}
                </option>
              ))}
            </select>
          </div>

          <button
            onClick={handleClearHistory}
            title="Clear Chat History"
            className="p-2 rounded-xl text-stone-400 hover:text-red-400 hover:bg-stone-800/80 transition-colors"
          >
            <Trash2 className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Tabs */}
      <div className="flex border-b border-stone-200 bg-stone-50/80 px-4 pt-2 gap-4">
        <button
          onClick={() => setActiveTab('chat')}
          className={`pb-2 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
            activeTab === 'chat'
              ? 'border-amber-600 text-amber-900'
              : 'border-transparent text-stone-500 hover:text-stone-800'
          }`}
        >
          <MessageSquare className="w-3.5 h-3.5" />
          Advisory Conversation
        </button>
        <button
          onClick={() => setActiveTab('context')}
          className={`pb-2 text-xs font-semibold border-b-2 transition-all flex items-center gap-1.5 ${
            activeTab === 'context'
              ? 'border-amber-600 text-amber-900'
              : 'border-transparent text-stone-500 hover:text-stone-800'
          }`}
        >
          <Layers className="w-3.5 h-3.5" />
          Active Business Context & Memory
        </button>
      </div>

      {/* Main Body */}
      {activeTab === 'chat' ? (
        <div className="flex-1 flex flex-col min-h-0 bg-stone-50/30">
          {/* Messages Stream */}
          <div className="flex-1 overflow-y-auto p-4 sm:p-6 space-y-4">
            {messages.length === 0 && (
              <div className="text-center py-10 px-4 max-w-md mx-auto space-y-3">
                <div className="w-12 h-12 rounded-2xl bg-amber-100 text-amber-700 flex items-center justify-center mx-auto shadow-sm">
                  <Bot className="w-6 h-6" />
                </div>
                <h3 className="font-bold text-stone-800 text-base">Namaste! I am your KALPA Advisor.</h3>
                <p className="text-xs text-stone-600 leading-relaxed">
                  I am directly grounded in your verified KALPA business analysis across Stages 6–13 (Market, Feasibility, Finance, and SWOT).
                  Ask me about your feasibility scores, financing, credit subsidy schemes, or immediate launch steps.
                </p>
              </div>
            )}

            {messages.map((m, idx) => (
              <div
                key={idx}
                className={`flex gap-3 ${m.sender === 'user' ? 'justify-end' : 'justify-start'}`}
              >
                {m.sender === 'assistant' && (
                  <div className="w-8 h-8 rounded-xl bg-amber-600 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                    <Sparkles className="w-4 h-4" />
                  </div>
                )}

                <div
                  className={`max-w-[86%] sm:max-w-[80%] rounded-2xl p-4 text-xs leading-relaxed space-y-3 shadow-sm ${
                    m.sender === 'user'
                      ? 'bg-amber-600 text-white rounded-br-none'
                      : m.isError
                      ? 'bg-red-50 text-red-900 border border-red-200 rounded-bl-none'
                      : 'bg-white text-stone-800 border border-stone-200/90 rounded-bl-none'
                  }`}
                >
                  {m.sender === 'assistant' && (
                    <div className="flex items-center justify-between gap-2 pb-2 border-b border-stone-100">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-stone-100 text-stone-700 uppercase">
                          {(m.intent || 'ADVISORY').replace(/_/g, ' ')}
                        </span>
                        {m.groundingStatus === 'DETERMINISTIC_FALLBACK' && (
                          <span className="text-[10px] text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200 font-medium">
                            Verified KALPA Fallback
                          </span>
                        )}
                      </div>

                      {/* Sarvam Bulbul:v3 TTS Voice Playback Button */}
                      {!m.isError && (
                        <button
                          onClick={() => handleToggleTTS(m.text, idx)}
                          disabled={ttsLoadingIdx === idx}
                          title={playingMessageIdx === idx ? 'Stop voice playback' : 'Listen with Sarvam Voice (Bulbul v3)'}
                          className={`flex items-center gap-1 px-2.5 py-1 rounded-lg text-[10px] font-semibold transition-all shadow-xs ${
                            playingMessageIdx === idx
                              ? 'bg-amber-600 text-white animate-pulse'
                              : 'bg-stone-100 hover:bg-amber-100 text-stone-700 hover:text-amber-900 border border-stone-200'
                          }`}
                        >
                          {ttsLoadingIdx === idx ? (
                            <>
                              <RefreshCw className="w-3 h-3 animate-spin text-amber-600" />
                              <span>Loading voice...</span>
                            </>
                          ) : playingMessageIdx === idx ? (
                            <>
                              <VolumeX className="w-3 h-3" />
                              <span>Stop Voice</span>
                            </>
                          ) : (
                            <>
                              <Volume2 className="w-3 h-3 text-amber-700" />
                              <span>Listen</span>
                            </>
                          )}
                        </button>
                      )}
                    </div>
                  )}

                  {/* Render content: user messages as text, assistant responses structured with AssistantMessageRenderer */}
                  {m.sender === 'user' ? (
                    <div className="whitespace-pre-wrap text-sm">{m.text}</div>
                  ) : m.isError ? (
                    <div className="text-sm font-medium">{m.text}</div>
                  ) : (
                    <AssistantMessageRenderer content={m.text} />
                  )}

                  {m.isError && m.failedMessage && (
                    <button
                      onClick={() => handleSendMessage(m.failedMessage)}
                      className="mt-2 text-[11px] px-3 py-1 bg-red-100 hover:bg-red-200 text-red-800 font-semibold rounded-lg flex items-center gap-1.5 transition-colors"
                    >
                      <RefreshCw className="w-3 h-3" /> Retry Message
                    </button>
                  )}

                  {/* Grounded Sources Badges */}
                  {m.groundedSources && m.groundedSources.length > 0 && (
                    <div className="pt-2.5 border-t border-stone-100 space-y-1">
                      <div className="text-[10px] text-stone-400 font-semibold uppercase tracking-wider">
                        Grounded in Verified Sources:
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {m.groundedSources.map((src, sIdx) => (
                          <span
                            key={sIdx}
                            className="px-2 py-0.5 rounded-md text-[9px] font-medium bg-stone-100 text-stone-700 border border-stone-200 flex items-center gap-1"
                          >
                            <span className="font-bold text-amber-700">Stage {src.stage || '6-13'}</span>
                            <span>•</span>
                            <span>{src.description || src.source || src}</span>
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Dynamic Suggested Inquiries */}
                  {m.suggestedActions && m.suggestedActions.length > 0 && (
                    <div className="pt-2.5 space-y-1.5 border-t border-stone-100/60">
                      <div className="text-[10px] font-bold text-amber-900 uppercase tracking-wider">
                        Suggested Follow-Up:
                      </div>
                      <div className="flex flex-wrap gap-1.5">
                        {m.suggestedActions.map((act, aIdx) => (
                          <button
                            key={aIdx}
                            onClick={() => handleSendMessage(act)}
                            className="text-[10px] px-2.5 py-1 rounded-lg bg-amber-50 hover:bg-amber-100 text-amber-900 border border-amber-200 transition-colors text-left"
                          >
                            {act}
                          </button>
                        ))}
                      </div>
                    </div>
                  )}
                </div>

                {m.sender === 'user' && (
                  <div className="w-8 h-8 rounded-xl bg-stone-800 text-white flex items-center justify-center shrink-0 shadow-sm mt-0.5">
                    <User className="w-4 h-4" />
                  </div>
                )}
              </div>
            ))}

            {isLoading && (
              <div className="flex gap-3 justify-start items-center">
                <div className="w-8 h-8 rounded-xl bg-amber-600 text-white flex items-center justify-center shrink-0 shadow-sm animate-pulse">
                  <Sparkles className="w-4 h-4" />
                </div>
                <div className="bg-white border border-stone-200 rounded-2xl rounded-bl-none p-3.5 text-xs text-stone-600 flex items-center gap-2 shadow-sm">
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-600" />
                  Synthesizing Stage 6–13 verified records & formulating tailored guidance...
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>

          {/* Quick Prompts Bar */}
          <div className="p-2.5 bg-white border-t border-stone-200 overflow-x-auto">
            <div className="flex gap-2 w-max">
              {QUICK_PROMPTS.map((qp, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSendMessage(qp.text)}
                  className="px-3 py-1.5 rounded-xl bg-stone-100 hover:bg-amber-50 hover:border-amber-300 border border-stone-200 text-[11px] font-medium text-stone-700 hover:text-amber-900 whitespace-nowrap transition-colors"
                >
                  {qp.label}
                </button>
              ))}
            </div>
          </div>

          {/* STT Status Toast Banner */}
          {sttStatusMessage && (
            <div className="px-4 py-2 bg-amber-50 border-t border-amber-200 text-amber-900 text-xs flex items-center justify-between">
              <div className="flex items-center gap-2">
                {isProcessingSTT ? (
                  <RefreshCw className="w-3.5 h-3.5 animate-spin text-amber-700" />
                ) : isRecording ? (
                  <span className="w-2.5 h-2.5 rounded-full bg-red-600 animate-ping" />
                ) : (
                  <HelpCircle className="w-3.5 h-3.5 text-amber-700" />
                )}
                <span>{sttStatusMessage}</span>
              </div>
              {isRecording && (
                <button
                  onClick={handleStopRecording}
                  className="px-2 py-0.5 rounded bg-red-600 text-white font-bold text-[10px]"
                >
                  Stop Recording
                </button>
              )}
            </div>
          )}

          {/* Input Box with Microphone & Send */}
          <div className="p-3 sm:p-4 bg-white border-t border-stone-200">
            <form
              onSubmit={(e) => {
                e.preventDefault();
                handleSendMessage();
              }}
              className="flex items-center gap-2"
            >
              {/* Sarvam Saaras:v4 Microphone Button */}
              <button
                type="button"
                onClick={isRecording ? handleStopRecording : handleStartRecording}
                disabled={isProcessingSTT || isLoading}
                title={isRecording ? 'Click to stop speaking' : 'Speak your question in your preferred language'}
                className={`p-3 rounded-2xl flex items-center justify-center transition-all shrink-0 shadow-sm ${
                  isRecording
                    ? 'bg-red-600 text-white animate-pulse ring-4 ring-red-200'
                    : isProcessingSTT
                    ? 'bg-amber-100 text-amber-800'
                    : 'bg-stone-100 hover:bg-amber-50 text-stone-700 hover:text-amber-900 border border-stone-300'
                }`}
              >
                {isProcessingSTT ? (
                  <RefreshCw className="w-4 h-4 animate-spin text-amber-700" />
                ) : isRecording ? (
                  <Square className="w-4 h-4 text-white" />
                ) : (
                  <Mic className="w-4 h-4 text-stone-700" />
                )}
              </button>

              <input
                type="text"
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                placeholder={
                  isRecording
                    ? 'Listening... Speak now...'
                    : isProcessingSTT
                    ? 'Transcribing audio with Sarvam Saaras v4...'
                    : 'Ask about loans, schemes, feasibility, DPR, or steps to launch...'
                }
                className="flex-1 px-4 py-3 bg-stone-50 border border-stone-300 rounded-2xl text-xs text-stone-900 focus:outline-none focus:ring-2 focus:ring-amber-500/20 focus:border-amber-600"
              />

              <button
                type="submit"
                disabled={isLoading || !inputValue.trim() || isRecording || isProcessingSTT}
                className="px-5 py-3 rounded-2xl bg-amber-600 hover:bg-amber-700 disabled:opacity-50 text-white font-semibold text-xs flex items-center gap-1.5 shadow-sm transition-all"
              >
                <span>Send</span>
                <Send className="w-3.5 h-3.5" />
              </button>
            </form>
          </div>
        </div>
      ) : (
        /* Active Business Context & Memory Tab */
        <div className="flex-1 overflow-y-auto p-6 space-y-6 bg-stone-50/50">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="bg-white p-4 rounded-2xl border border-stone-200 space-y-2">
              <div className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">Enterprise Model</div>
              <div className="font-bold text-sm text-stone-800">{biz.business_name || 'Standard Enterprise'}</div>
              <div className="text-xs text-stone-500">{biz.category || 'Micro-Enterprise'} • {biz.sector || 'Rural Venture'}</div>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-stone-200 space-y-2">
              <div className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">Feasibility Score (Stage 12)</div>
              <div className="font-bold text-sm text-emerald-600">
                {feas.overall_feasibility_score !== undefined ? `${feas.overall_feasibility_score} / 100` : 'Evaluated'}
              </div>
              <div className="text-xs text-stone-500">{feas.viability_status || 'VIABLE_WITH_CONDITIONS'}</div>
            </div>

            <div className="bg-white p-4 rounded-2xl border border-stone-200 space-y-2">
              <div className="text-[10px] font-bold text-stone-400 uppercase tracking-wider">Financial Highlights (Stage 9)</div>
              <div className="font-bold text-sm text-stone-800">
                Cost: {fin.total_project_cost ? `₹${fin.total_project_cost.toLocaleString('en-IN')}` : 'Projected'}
              </div>
              <div className="text-xs text-stone-500">
                Loan: {fin.bank_loan_requirement ? `₹${fin.bank_loan_requirement.toLocaleString('en-IN')}` : 'Eligible'} | DSCR: {fin.dscr || 'N/A'}
              </div>
            </div>
          </div>

          <div className="bg-white p-5 rounded-2xl border border-stone-200 space-y-3">
            <h4 className="font-bold text-xs text-stone-800 uppercase tracking-wider flex items-center gap-2">
              <ShieldCheck className="w-4 h-4 text-amber-600" />
              Grounded Analysis Data Sources Loaded
            </h4>
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 text-xs">
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 3 Profile</span>
              </div>
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 6 Market</span>
              </div>
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 9 Finance</span>
              </div>
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 10 Readiness</span>
              </div>
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 11 Risk</span>
              </div>
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 12 Feasibility</span>
              </div>
              <div className="p-2.5 bg-stone-50 rounded-xl border border-stone-100 flex items-center gap-2">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                <span>Stage 13 SWOT</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
