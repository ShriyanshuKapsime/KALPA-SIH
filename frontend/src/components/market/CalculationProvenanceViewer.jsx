import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Calculator, Check, Copy, HelpCircle, Database, Award } from 'lucide-react';

export const CalculationProvenanceViewer = ({
  provenance = [],
  metricName = null, // If provided, filters to single metric
  title = "Calculation Provenance & Audit Trail",
  collapsible = true,
  defaultExpanded = false
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [copiedKey, setCopiedKey] = useState(null);

  // Filter if specific metric requested
  const items = metricName
    ? provenance.filter(p => p.indicator === metricName || p.indicator?.toLowerCase() === metricName?.toLowerCase())
    : provenance;

  if (!items || items.length === 0) {
    if (metricName) return null;
    return (
      <div className="p-4 rounded-xl bg-slate-900/60 border border-slate-800 text-xs text-slate-400">
        No calculation provenance records available.
      </div>
    );
  }

  const handleCopy = (item, idx) => {
    const text = JSON.stringify(item, null, 2);
    navigator.clipboard.writeText(text);
    setCopiedKey(idx);
    setTimeout(() => setCopiedKey(null), 1500);
  };

  return (
    <div className="bg-slate-900/80 border border-slate-800 rounded-xl overflow-hidden">
      {collapsible ? (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-slate-850 transition-colors"
        >
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-semibold text-slate-200">{title}</span>
            <span className="text-xs px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-300 font-mono">
              {items.length} {items.length === 1 ? 'formula' : 'formulas'}
            </span>
          </div>
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <span>{isExpanded ? 'Hide Provenance' : 'Inspect Calculations'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>
      ) : (
        <div className="p-4 border-b border-slate-800 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-cyan-400" />
            <span className="text-sm font-semibold text-slate-200">{title}</span>
          </div>
          <span className="text-xs text-slate-400 font-mono">{items.length} calculations</span>
        </div>
      )}

      {(!collapsible || isExpanded) && (
        <div className="p-4 pt-0 space-y-4 border-t border-slate-800/80 divide-y divide-slate-800/60">
          {items.map((item, idx) => (
            <div key={idx} className="pt-4 first:pt-4">
              <div className="flex items-start justify-between gap-3 mb-2">
                <div>
                  <h4 className="text-sm font-bold text-cyan-300 font-mono">
                    {item.indicator?.replace(/_/g, ' ')}
                  </h4>
                  <p className="text-xs text-slate-400 mt-0.5 font-sans">
                    Method: <span className="text-slate-300 font-medium">{item.calculation_method}</span>
                  </p>
                </div>
                <div className="flex items-center gap-2 shrink-0">
                  <span className="text-xs font-mono font-bold px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">
                    Output: {typeof item.value === 'number' ? item.value.toFixed(4) : String(item.value)}
                  </span>
                  <button
                    onClick={() => handleCopy(item, idx)}
                    className="p-1 rounded hover:bg-slate-800 text-slate-400 hover:text-slate-200 transition-colors"
                    title="Copy calculation JSON"
                  >
                    {copiedKey === idx ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                  </button>
                </div>
              </div>

              {/* Mathematical Formula Box */}
              <div className="bg-slate-950 p-3 rounded-lg border border-slate-800 font-mono text-xs space-y-2">
                <div>
                  <span className="text-slate-500 select-none block text-[10px] uppercase font-bold tracking-wider">Formula:</span>
                  <code className="text-emerald-300 break-words block mt-0.5">{item.formula}</code>
                </div>

                {item.inputs && item.inputs.length > 0 && (
                  <div className="pt-2 border-t border-slate-900">
                    <span className="text-slate-500 select-none block text-[10px] uppercase font-bold tracking-wider">Inputs & Variables:</span>
                    <ul className="list-disc list-inside text-slate-300 space-y-0.5 mt-1 text-[11px]">
                      {item.inputs.map((inp, i) => (
                        <li key={i} className="break-words">{inp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Benchmarks & Assumptions Metadata */}
              <div className="mt-2 flex flex-wrap gap-2 text-[11px] text-slate-400">
                {item.benchmarks_used && item.benchmarks_used.length > 0 && (
                  <span className="inline-flex items-center gap-1 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-blue-300">
                    <Award className="w-3 h-3 text-blue-400" /> Benchmarks: {item.benchmarks_used.join(', ')}
                  </span>
                )}
                {item.evidence_refs && item.evidence_refs.length > 0 && (
                  <span className="inline-flex items-center gap-1 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-purple-300">
                    <Database className="w-3 h-3 text-purple-400" /> Refs: {item.evidence_refs.join(', ')}
                  </span>
                )}
                <span className="inline-flex items-center gap-1 bg-slate-950 px-2 py-0.5 rounded border border-slate-800 text-slate-400">
                  Confidence: {((item.confidence || 0.85) * 100).toFixed(0)}%
                </span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

export default CalculationProvenanceViewer;
