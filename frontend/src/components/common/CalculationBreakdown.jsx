import React from 'react';
import { Calculator, CheckCircle2, AlertTriangle, ShieldCheck, Database, Layers, ArrowRight } from 'lucide-react';

/**
 * Safe String Formatter (Prevents "Objects are not valid as a React child")
 */
export const safeFormat = (val) => {
  if (val === null || val === undefined) return '—';
  if (typeof val === 'boolean') return val ? 'Yes' : 'No';
  if (typeof val === 'number') {
    return Number.isInteger(val) ? val.toString() : val.toFixed(2);
  }
  if (typeof val === 'string') return val;
  if (Array.isArray(val)) {
    return val.map((v) => (typeof v === 'object' ? JSON.stringify(v) : String(v))).join(', ');
  }
  if (typeof val === 'object') {
    if (val.name || val.title || val.description || val.value || val.message) {
      return String(val.name || val.title || val.description || val.value || val.message);
    }
    try {
      return JSON.stringify(val);
    } catch {
      return String(val);
    }
  }
  return String(val);
};

/**
 * Unified Calculation Breakdown Component for Stages 10, 11, and 12.
 * Renders complete audit provenance:
 * - INPUTS: Raw user values and upstream data
 * - BENCHMARK: Domain standards applied
 * - FORMULA: Mathematical formula description
 * - CALCULATION: Step-by-step evaluated arithmetic
 * - RESULT / SCORE: Dimension score & weighted contribution
 * - SOURCE: Originating stage / ontology
 * - CONFIDENCE: Deterministic confidence rating
 */
export const CalculationBreakdown = ({ items = [], title = "Calculation Breakdown & Audit Provenance", stage = "Stage" }) => {
  if (!items || !Array.isArray(items) || items.length === 0) {
    return (
      <div className="p-4 bg-stone-900/60 rounded-2xl border border-stone-800 text-stone-400 text-xs italic">
        No mathematical calculation provenance records available.
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {items.map((item, idx) => {
        if (!item) return null;

        const dim = safeFormat(item.dimension || item.category || item.pillar || `Dimension ${idx + 1}`);
        const score = item.score !== undefined && item.score !== null ? (typeof item.score === 'number' ? Math.round(item.score) : item.score) : null;
        const weightPct = item.weight !== undefined && item.weight !== null ? Math.round(Number(item.weight) * 100) : null;
        const contrib = item.weighted_contribution !== undefined && item.weighted_contribution !== null ? Number(item.weighted_contribution).toFixed(1) : null;
        
        const formula = safeFormat(item.formula || item.calculation_formula || '');
        const calculation = safeFormat(item.calculation || item.math_trace || item.details || '');
        const benchmark = safeFormat(item.benchmark || item.benchmark_norm || item.benchmark_requirement || '');
        const source = safeFormat(item.source || item.source_stage || 'Deterministic Rules Engine');
        const confidence = item.confidence !== undefined && item.confidence !== null ? Math.round(Number(item.confidence) * 100) : null;
        const status = safeFormat(item.status || item.level || 'EVALUATED').toUpperCase();

        const inputs = item.inputs || item.key_inputs || null;

        return (
          <div
            key={idx}
            className="p-4 bg-stone-900/95 rounded-2xl border border-stone-800 hover:border-stone-700 transition space-y-3.5 text-stone-200 shadow-md"
          >
            {/* Header: Dimension Name, Status, Weight & Score */}
            <div className="flex flex-wrap items-center justify-between gap-2 border-b border-stone-800 pb-2.5">
              <div className="flex items-center space-x-2">
                <span className="w-2 h-2 rounded-full bg-[#EA580C]"></span>
                <span className="text-xs font-extrabold text-white uppercase tracking-wider font-mono">
                  {dim}
                </span>
                {weightPct !== null && (
                  <span className="px-2 py-0.5 rounded text-[10px] font-mono bg-stone-800 text-stone-400 border border-stone-700">
                    Weight: {weightPct}%
                  </span>
                )}
                {status && (
                  <span
                    className={`px-2 py-0.5 rounded text-[10px] font-bold font-mono ${
                      status === 'STRONG' || status === 'LOW' || status === 'PASS' || status === 'VIABLE'
                        ? 'bg-emerald-950 text-emerald-400 border border-emerald-800'
                        : status === 'DATA_GAP' || status === 'UNKNOWN'
                        ? 'bg-rose-950 text-rose-400 border border-rose-800'
                        : 'bg-amber-950 text-amber-400 border border-amber-800'
                    }`}
                  >
                    {status}
                  </span>
                )}
              </div>

              <div className="flex items-center space-x-3 font-mono">
                {score !== null ? (
                  <span className="text-sm font-bold text-white bg-stone-950 px-2.5 py-1 rounded-lg border border-stone-800">
                    Score: <strong className="text-orange-400">{score}</strong>/100
                  </span>
                ) : (
                  <span className="text-xs font-bold text-rose-400 bg-rose-950/60 px-2 py-1 rounded-lg border border-rose-900">
                    DATA GAP
                  </span>
                )}
                {contrib !== null && (
                  <span className="text-xs font-semibold text-emerald-400">
                    +{contrib} pts
                  </span>
                )}
              </div>
            </div>

            {/* Step-by-Step Calculation Breakdown Contract */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-3 text-xs">
              {/* Formula & Calculation */}
              <div className="p-3 bg-stone-950/80 rounded-xl border border-stone-800/80 space-y-1.5 md:col-span-2">
                <div className="flex items-center space-x-1.5 text-stone-400 text-[11px] font-mono">
                  <Calculator className="w-3.5 h-3.5 text-[#EA580C]" />
                  <span className="font-bold text-stone-300">CALCULATION & FORMULA</span>
                </div>
                {formula && formula !== '—' && (
                  <div className="text-[11px] text-stone-400 font-mono">
                    <span className="text-stone-500">Formula: </span>{formula}
                  </div>
                )}
                {calculation && calculation !== '—' ? (
                  <div className="text-xs text-stone-200 font-mono font-semibold bg-stone-900/90 p-2 rounded border border-stone-800">
                    {calculation}
                  </div>
                ) : (
                  <div className="text-xs text-stone-400 italic font-mono">
                    Score computed directly from verified upstream evidence benchmarks.
                  </div>
                )}
              </div>

              {/* Inputs Consumed */}
              {inputs && typeof inputs === 'object' && Object.keys(inputs).length > 0 && (
                <div className="p-3 bg-stone-950/60 rounded-xl border border-stone-800/80 space-y-1.5">
                  <div className="text-[11px] font-mono text-stone-400 font-bold flex items-center gap-1">
                    <Database className="w-3 h-3 text-blue-400" />
                    <span>INPUTS CONSUMED</span>
                  </div>
                  <div className="space-y-1 text-[11px] font-mono max-h-28 overflow-y-auto">
                    {Object.entries(inputs).map(([k, v], iIdx) => (
                      <div key={iIdx} className="flex justify-between border-b border-stone-900 pb-0.5">
                        <span className="text-stone-400">{k.replace(/_/g, ' ')}:</span>
                        <span className="text-stone-200 font-semibold">{safeFormat(v)}</span>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {/* Benchmark Applied */}
              {benchmark && benchmark !== '—' && (
                <div className="p-3 bg-stone-950/60 rounded-xl border border-stone-800/80 space-y-1.5">
                  <div className="text-[11px] font-mono text-stone-400 font-bold flex items-center gap-1">
                    <Layers className="w-3 h-3 text-amber-400" />
                    <span>BENCHMARK APPLIED</span>
                  </div>
                  <div className="text-xs text-amber-200/90 font-mono">
                    {benchmark}
                  </div>
                </div>
              )}
            </div>

            {/* Footer: Source & Confidence */}
            <div className="flex flex-wrap items-center justify-between text-[11px] text-stone-400 pt-1 border-t border-stone-800/60 font-mono">
              <div>
                Source: <strong className="text-stone-300">{source}</strong>
              </div>
              {confidence !== null && (
                <div>
                  Confidence: <strong className="text-emerald-400">{confidence}%</strong>
                </div>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
};

export default CalculationBreakdown;
