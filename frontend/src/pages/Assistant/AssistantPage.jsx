import React, { useEffect, useRef } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { ArrowLeft, Trash2 } from 'lucide-react';
import AssistantChatCore from '../../components/assistant/AssistantChatCore';
import LanguageSelector from '../../components/ui/LanguageSelector';
import { useLanguage } from '../../context/LanguageContext';
import { useWorkflow } from '../../context/WorkflowContext';

export const AssistantPage = () => {
  const navigate = useNavigate();
  const { sessionId, analysisId } = useWorkflow();
  const { language, setLanguage, t } = useLanguage();
  const chatRef = useRef(null);

  // Dedicated AI Advisor route must open at TOP on initial mount
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const handleClearChat = async () => {
    if (window.confirm(t('assistant_clear_conversation_confirm', 'Are you sure you want to clear this advisory conversation?'))) {
      if (chatRef.current?.clearHistory) {
        await chatRef.current.clearHistory();
      }
    }
  };

  const getSwotUrl = () => {
    const params = new URLSearchParams();
    const effectiveSessionId = sessionId || sessionStorage.getItem('kalpa_session_id');
    const effectiveAnalysisId = analysisId || sessionStorage.getItem('kalpa_analysis_id');
    if (effectiveSessionId) params.set('session_id', effectiveSessionId);
    if (effectiveAnalysisId) params.set('analysis_id', effectiveAnalysisId);
    const qs = params.toString();
    return qs ? `/swot?${qs}` : '/swot';
  };

  return (
    <div className="w-full h-full flex flex-col min-h-screen px-3 sm:px-6 md:px-8 py-4 sm:py-5 max-w-6xl mx-auto animate-fadeIn">
      {/* 1. Clean Dedicated KALPA Header */}
      <header className="w-full flex items-center justify-between pb-3 sm:pb-4 border-b border-[#79563F]/15 flex-shrink-0">
        {/* Brand Left */}
        <Link
          to="/"
          className="text-2xl sm:text-3xl font-bold tracking-tight text-[#006B59] font-['Playfair_Display',Georgia,serif] hover:opacity-85 transition-opacity"
          aria-label="KALPA - Return to Home"
        >
          KALPA
        </Link>

        {/* Right Navigation & Control Suite */}
        <div className="flex items-center gap-2 sm:gap-3">
          {/* Universal Language Selector */}
          <LanguageSelector compact />

          {/* Clear Conversation Button */}
          <button
            type="button"
            onClick={handleClearChat}
            title={t('assistant_clear_conversation_confirm', 'Clear Conversation')}
            className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[#FAF2E3] hover:bg-[#F2E8D5] text-[#79563F] hover:text-rose-700 border border-[#79563F]/25 text-xs font-semibold transition-colors cursor-pointer shadow-2xs"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span className="hidden sm:inline">{t('clear', 'Clear')}</span>
          </button>

          {/* Back to SWOT Matrix Button */}
          <Link
            to={getSwotUrl()}
            className="px-3 sm:px-4 py-1.5 rounded-xl bg-[#FAF7F2] hover:bg-white text-[#79563F] border border-[#79563F]/30 text-xs font-bold transition-all shadow-2xs cursor-pointer flex items-center gap-1.5 whitespace-nowrap"
          >
            <ArrowLeft className="w-3.5 h-3.5" />
            <span>{t('assistant_back_swot', 'Back to SWOT Matrix')}</span>
          </Link>
        </div>
      </header>

      {/* 2. Chat Workspace Container */}
      <main className="flex-1 min-h-0 w-full max-w-[960px] mx-auto pt-3 sm:pt-4 flex flex-col">
        <AssistantChatCore
          ref={chatRef}
          mode="fullpage"
          externalLanguage={language}
          onLanguageChange={setLanguage}
          className="flex-1 min-h-0"
        />
      </main>
    </div>
  );
};

export default AssistantPage;
