import React, { useState } from 'react';
import { Cpu, CheckCircle2, ShieldCheck, Clock, Copy, Check, Terminal } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const ExecutionMetadataCard = ({
  stage6Output = {},
  analysisId = '',
  sessionId = '',
}) => {
  const [copied, setCopied] = useState(false);
  const meta = stage6Output.execution_metadata || {};
  const workflow = stage6Output.workflow || {};

  const handleCopyJSON = () => {
    navigator.clipboard.writeText(JSON.stringify(stage6Output, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  return (
    <div className="royal-panel border border-[#79563F]/18 rounded-2xl p-6 space-y-4 font-mono text-xs shadow-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-[#006F5F]" />
          <span className="text-sm font-bold text-[#28231F] uppercase tracking-wider font-sans">
            Execution Telemetry & Audit
          </span>
          <Stage6StatusBadge status={meta.status || 'SUCCESS'} />
        </div>
        <button
          onClick={handleCopyJSON}
          className="flex items-center gap-1.5 bg-[#FAF2E3] border border-[#79563F]/20 hover:bg-[#F1E4CC] text-[#28231F] text-xs px-3 py-1.5 rounded-lg transition-colors font-bold shadow-2xs"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-[#006F5F]" /> : <Copy className="w-3.5 h-3.5 text-[#79563F]" />}
          <span>{copied ? 'Copied Full Output' : 'Copy Output JSON'}</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-[#FAF2E3] p-3 rounded-lg border border-[#79563F]/18 shadow-2xs">
          <span className="text-[#79563F] uppercase text-[10px] block font-bold">Engine Mode</span>
          <strong className="text-[#006F5F] text-xs mt-1 block font-bold">DETERMINISTIC PIPELINE</strong>
        </div>

        <div className="bg-[#FAF2E3] p-3 rounded-lg border border-[#79563F]/18 shadow-2xs">
          <span className="text-[#79563F] uppercase text-[10px] block font-bold">Model Calls</span>
          <strong className="text-[#006F5F] text-xs mt-1 block font-bold">0 CALLS (PURE SPATIAL)</strong>
        </div>

        <div className="bg-[#FAF2E3] p-3 rounded-lg border border-[#79563F]/18 shadow-2xs">
          <span className="text-[#79563F] uppercase text-[10px] block font-bold">Execution Duration</span>
          <strong className="text-[#28231F] text-xs mt-1 block font-mono">
            {meta.execution_time_seconds ? `${meta.execution_time_seconds.toFixed(3)}s` : '< 0.05s'}
          </strong>
        </div>

        <div className="bg-[#FAF2E3] p-3 rounded-lg border border-[#79563F]/18 shadow-2xs">
          <span className="text-[#79563F] uppercase text-[10px] block font-bold">Engine Version</span>
          <strong className="text-[#28231F] text-xs mt-1 block font-bold">{meta.engine_version || '1.0.0'}</strong>
        </div>
      </div>

      <div className="p-3 bg-[#FAF2E3] rounded-lg border border-[#79563F]/18 space-y-1 text-[11px] text-[#62584F] shadow-2xs">
        <div className="flex flex-wrap justify-between gap-2">
          <span>Analysis ID: <strong className="text-[#28231F]">{stage6Output.analysis_id || analysisId || '—'}</strong></span>
          <span>Session ID: <strong className="text-[#28231F]">{stage6Output.session_id || sessionId || '—'}</strong></span>
        </div>
        <div className="flex flex-wrap justify-between gap-2 pt-1 border-t border-[#79563F]/15 text-[10px] text-[#79563F]">
          <span>Workflow State: {workflow.state || 'MARKET_INTELLIGENCE_ANALYZED'}</span>
          <span>Timestamp: {new Date().toISOString()}</span>
        </div>
      </div>
    </div>
  );
};

export default ExecutionMetadataCard;
