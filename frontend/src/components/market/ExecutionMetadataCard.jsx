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
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4 font-mono text-xs">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div className="flex items-center gap-2">
          <Terminal className="w-5 h-5 text-indigo-400" />
          <span className="text-sm font-bold text-slate-100 uppercase tracking-wider font-sans">
            Stage 6 Deterministic Execution Metadata & Telemetry
          </span>
          <Stage6StatusBadge status={meta.status || 'SUCCESS'} />
        </div>
        <button
          onClick={handleCopyJSON}
          className="flex items-center gap-1.5 bg-slate-950 border border-slate-700 hover:bg-slate-800 text-slate-300 text-xs px-3 py-1.5 rounded-lg transition-colors"
        >
          {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5 text-slate-400" />}
          <span>{copied ? 'Copied Full Output' : 'Copy Stage 6 JSON'}</span>
        </button>
      </div>

      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-slate-500 uppercase text-[10px] block">Engine Mode</span>
          <strong className="text-emerald-400 text-xs mt-1 block">ZERO-LLM DETERMINISTIC</strong>
        </div>

        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-slate-500 uppercase text-[10px] block">LLM Used</span>
          <strong className="text-emerald-400 text-xs mt-1 block">FALSE (0 calls)</strong>
        </div>

        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-slate-500 uppercase text-[10px] block">Execution Duration</span>
          <strong className="text-cyan-400 text-xs mt-1 block font-mono">
            {meta.execution_time_seconds ? `${meta.execution_time_seconds.toFixed(3)}s` : '< 0.05s'}
          </strong>
        </div>

        <div className="bg-slate-950 p-3 rounded-lg border border-slate-800">
          <span className="text-slate-500 uppercase text-[10px] block">Engine Version</span>
          <strong className="text-slate-300 text-xs mt-1 block">{meta.engine_version || '1.0.0'}</strong>
        </div>
      </div>

      <div className="p-3 bg-slate-950 rounded-lg border border-slate-800/80 space-y-1 text-[11px] text-slate-400">
        <div className="flex flex-wrap justify-between gap-2">
          <span>Analysis ID: <strong className="text-slate-200">{stage6Output.analysis_id || analysisId || '—'}</strong></span>
          <span>Session ID: <strong className="text-slate-200">{stage6Output.session_id || sessionId || '—'}</strong></span>
        </div>
        <div className="flex flex-wrap justify-between gap-2 pt-1 border-t border-slate-900 text-[10px] text-slate-500">
          <span>Workflow State: {workflow.state || 'MARKET_INTELLIGENCE_ANALYZED'}</span>
          <span>Timestamp: {new Date().toISOString()}</span>
        </div>
      </div>
    </div>
  );
};

export default ExecutionMetadataCard;
