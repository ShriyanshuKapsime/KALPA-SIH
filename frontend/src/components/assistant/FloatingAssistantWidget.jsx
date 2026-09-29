import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { MessageCircle } from 'lucide-react';
import AssistantChatCore from './AssistantChatCore';
import { useWorkflow } from '../../context/WorkflowContext';

export default function FloatingAssistantWidget({
  isOpen: controlledIsOpen,
  onOpen: controlledOnOpen,
  onClose: controlledOnClose,
}) {
  const navigate = useNavigate();
  const { sessionId, analysisId } = useWorkflow();
  const [internalIsOpen, setInternalIsOpen] = useState(false);

  useEffect(() => {
    const handleExternalOpen = () => {
      if (controlledOnOpen) {
        controlledOnOpen();
      } else {
        setInternalIsOpen(true);
      }
    };
    window.addEventListener('kalpa:open-ai-advisor', handleExternalOpen);
    return () => window.removeEventListener('kalpa:open-ai-advisor', handleExternalOpen);
  }, [controlledOnOpen]);

  const isControlled = controlledIsOpen !== undefined;
  const isOpen = isControlled ? controlledIsOpen : internalIsOpen;

  const handleOpen = () => {
    if (isControlled && controlledOnOpen) {
      controlledOnOpen();
    } else {
      setInternalIsOpen(true);
    }
  };

  const handleClose = () => {
    if (isControlled && controlledOnClose) {
      controlledOnClose();
    } else {
      setInternalIsOpen(false);
    }
  };

  const handleMaximize = () => {
    const params = new URLSearchParams();
    const effectiveSessionId = sessionId || sessionStorage.getItem('kalpa_session_id');
    const effectiveAnalysisId = analysisId || sessionStorage.getItem('kalpa_analysis_id');
    if (effectiveSessionId) params.set('session_id', effectiveSessionId);
    if (effectiveAnalysisId) params.set('analysis_id', effectiveAnalysisId);
    const qs = params.toString();
    navigate(qs ? `/assistant?${qs}` : '/assistant');
  };

  return (
    <>
      {/* Floating Chat Window Modal/Panel */}
      {isOpen && (
        <div
          role="dialog"
          aria-label="KALPA Business Advisor Floating Window"
          className="fixed z-50 bottom-3 right-3 sm:bottom-6 sm:right-6 w-[calc(100vw-24px)] sm:w-[420px] md:w-[450px] max-w-[460px] h-[calc(100vh-90px)] sm:h-[620px] max-h-[700px] flex flex-col rounded-3xl shadow-2xl overflow-hidden border border-[#79563F]/20 animate-fadeIn"
        >
          <AssistantChatCore
            mode="floating"
            onMaximize={handleMaximize}
            onClose={handleClose}
            className="flex-1 min-h-0"
          />
        </div>
      )}

      {/* Floating Launcher Button (visible when window is closed) */}
      {!isOpen && (
        <button
          type="button"
          onClick={handleOpen}
          aria-label="Ask KALPA"
          className="saffron-gradient-btn kalpa-assistant-floating-btn fixed bottom-4 right-4 sm:bottom-6 sm:right-6 z-40 flex items-center gap-2.5 px-4 py-3 font-bold text-xs rounded-full shadow-2xl transition-all transform hover:scale-105 border border-white/20 cursor-pointer"
        >
          <MessageCircle className="w-4 h-4 text-white" />
          <span>Ask KALPA</span>
        </button>
      )}
    </>
  );
}
