import React, { useState } from 'react';
import { ChevronDown, ChevronUp, Calculator, Check, Copy, Award, Database } from 'lucide-react';

export const CalculationProvenanceViewer = ({
  provenance = [],
  metricName = null,
  title = "Calculation Details & Formula Audit",
  collapsible = true,
  defaultExpanded = false
}) => {
  const [isExpanded, setIsExpanded] = useState(defaultExpanded);
  const [copiedKey, setCopiedKey] = useState(null);

  const items = metricName
    ? provenance.filter(p => p.indicator === metricName || p.indicator?.toLowerCase() === metricName?.toLowerCase())
    : provenance;

  if (!items || items.length === 0) {
    if (metricName) return null;
    return (
      <div className="royal-panel rounded-2xl p-4 border border-[#79563F]/18 text-xs text-[#62584F] shadow-xs self-start">
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
    <div className="royal-panel border border-[#79563F]/18 rounded-2xl overflow-hidden shadow-xs h-auto w-full">
      {collapsible ? (
        <button
          onClick={() => setIsExpanded(!isExpanded)}
          className="w-full flex items-center justify-between p-4 text-left hover:bg-[#FAF2E3]/80 transition-colors cursor-pointer"
        >
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-[#006F5F]" />
            <span className="text-sm font-bold text-[#28231F] font-['Outfit']">{title}</span>
            <span className="text-[10px] px-2 py-0.5 rounded-full bg-[#006F5F]/10 text-[#006F5F] font-mono font-bold">
              {items.length} {items.length === 1 ? 'formula' : 'formulas'}
            </span>
          </div>
          <div className="flex items-center gap-1 text-xs text-[#79563F]">
            <span>{isExpanded ? 'Hide Details' : 'Inspect Audit'}</span>
            {isExpanded ? <ChevronUp className="w-4 h-4" /> : <ChevronDown className="w-4 h-4" />}
          </div>
        </button>
      ) : (
        <div className="p-4 border-b border-[#79563F]/15 flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calculator className="w-4 h-4 text-[#006F5F]" />
            <span className="text-sm font-bold text-[#28231F] font-['Outfit']">{title}</span>
          </div>
          <span className="text-xs text-[#79563F] font-mono">{items.length} calculations</span>
        </div>
      )}

      {(!collapsible || isExpanded) && (
        <div className="p-4 pt-0 space-y-3 border-t border-[#79563F]/15 divide-y divide-[#79563F]/12">
          {items.map((item, idx) => (
            <div key={idx} className="pt-3 first:pt-3">
              <div className="flex items-start justify-between gap-2 mb-1">
                <div>
                  <h4 className="text-xs font-bold text-[#28231F] font-mono">
                    {item.indicator?.replace(/_/g, ' ')}
                  </h4>
                  <p className="text-[10px] text-[#62584F] mt-0.5">
                    Method: <span className="text-[#28231F] font-medium">{item.calculation_method}</span>
                  </p>
                </div>
                <div className="flex items-center gap-1.5 shrink-0">
                  <span className="text-[10px] font-mono font-bold px-1.5 py-0.5 rounded bg-[#006F5F]/10 text-[#006F5F] border border-[#006F5F]/20">
                    Output: {typeof item.value === 'number' ? item.value.toFixed(4) : String(item.value)}
                  </span>
                  <button
                    onClick={() => handleCopy(item, idx)}
                    className="p-1 rounded hover:bg-[#F1E4CC] text-[#79563F] hover:text-[#28231F] transition-colors"
                    title="Copy calculation JSON"
                  >
                    {copiedKey === idx ? <Check className="w-3 h-3 text-[#006F5F]" /> : <Copy className="w-3 h-3" />}
                  </button>
                </div>
              </div>

              {/* Formula Box */}
              <div className="bg-[#FAF2E3]/90 p-2 rounded-lg border border-[#79563F]/12 font-mono text-xs space-y-1">
                <div>
                  <span className="text-[#79563F] select-none block text-[8px] uppercase font-bold tracking-wider">Formula:</span>
                  <code className="text-[#006F5F] break-words block mt-0.5 text-[11px] font-bold">{item.formula}</code>
                </div>

                {item.inputs && item.inputs.length > 0 && (
                  <div className="pt-1 border-t border-[#79563F]/10">
                    <span className="text-[#79563F] select-none block text-[8px] uppercase font-bold tracking-wider">Inputs:</span>
                    <ul className="list-disc list-inside text-[#62584F] space-y-0.5 mt-0.5 text-[9px]">
                      {item.inputs.map((inp, i) => (
                        <li key={i} className="break-words">{inp}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>

              {/* Metadata */}
              <div className="mt-1 flex flex-wrap gap-1 text-[9px] text-[#62584F]">
                {item.benchmarks_used && item.benchmarks_used.length > 0 && (
                  <span className="inline-flex items-center gap-1 bg-[#FAF2E3]/90 px-1.5 py-0.5 rounded border border-[#79563F]/12 text-[#79563F]">
                    <Award className="w-2.5 h-2.5 text-[#C96A3A]" /> {item.benchmarks_used.join(', ')}
                  </span>
                )}
                {item.evidence_refs && item.evidence_refs.length > 0 && (
                  <span className="inline-flex items-center gap-1 bg-[#FAF2E3]/90 px-1.5 py-0.5 rounded border border-[#79563F]/12 text-[#79563F]">
                    <Database className="w-2.5 h-2.5 text-[#006F5F]" /> {item.evidence_refs.join(', ')}
                  </span>
                )}
                <span className="inline-flex items-center gap-1 bg-[#FAF2E3]/90 px-1.5 py-0.5 rounded border border-[#79563F]/12 text-[#79563F]">
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
