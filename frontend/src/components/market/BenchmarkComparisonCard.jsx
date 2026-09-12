import React from 'react';
import { Award, ExternalLink, ArrowUpDown, Database } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const BenchmarkComparisonCard = ({ benchmarkAnalysis = {} }) => {
  const comparisons = benchmarkAnalysis.comparisons || [];
  const benchmarksUsed = benchmarkAnalysis.benchmarks_used || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Award className="w-5 h-5 text-blue-400" />
              Official Dataset Benchmarks & Deviations
            </h3>
            <span className="text-xs px-2 py-0.5 rounded bg-blue-500/10 text-blue-400 border border-blue-500/20 font-mono">
              Census 2011 / NABARD / MSME
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic normalization against official Indian national and state-level statistical baselines.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Datasets Loaded:</span>
          <p className="text-sm font-bold text-blue-400 font-mono">{benchmarksUsed.length} Curated Repositories</p>
        </div>
      </div>

      {/* Benchmarks Used Badges */}
      {benchmarksUsed.length > 0 && (
        <div className="flex flex-wrap gap-2">
          {benchmarksUsed.map((b, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1.5 bg-slate-950 px-3 py-1 rounded-lg border border-slate-800 text-xs text-slate-300 font-mono"
            >
              <Database className="w-3 h-3 text-blue-400" /> {b}
            </span>
          ))}
        </div>
      )}

      {/* Comparisons Table */}
      {comparisons.length === 0 ? (
        <div className="p-4 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-400">
          No explicit benchmark deviation records returned for this business context.
        </div>
      ) : (
        <div className="space-y-3">
          {comparisons.map((c, idx) => {
            const variance = c.variance_percentage;
            const isPositive = variance !== null && variance !== undefined && variance > 0;
            return (
              <div
                key={idx}
                className="bg-slate-950 p-4 rounded-xl border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-3 text-xs"
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-200 text-sm">{c.benchmark_name}</span>
                    <span className="text-[10px] font-mono text-slate-500 bg-slate-900 px-2 py-0.5 rounded border border-slate-800">
                      ID: {c.benchmark_id}
                    </span>
                  </div>
                  <p className="text-slate-400 text-[11px]">
                    Evaluation: <strong className="text-slate-300">{c.comparison_result}</strong>
                  </p>
                  {c.source && (
                    <p className="text-[10px] text-slate-500">
                      Source: {c.source}
                    </p>
                  )}
                </div>

                <div className="flex items-center gap-6 shrink-0 font-mono">
                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Actual</span>
                    <strong className="text-slate-200 text-sm">{typeof c.actual_value === 'number' ? c.actual_value.toLocaleString('en-IN') : String(c.actual_value)}</strong>
                  </div>

                  <div>
                    <span className="text-[10px] text-slate-500 uppercase block">Benchmark</span>
                    <strong className="text-blue-300 text-sm">{typeof c.benchmark_value === 'number' ? c.benchmark_value.toLocaleString('en-IN') : String(c.benchmark_value)}</strong>
                  </div>

                  {variance !== null && variance !== undefined && (
                    <div className="text-right">
                      <span className="text-[10px] text-slate-500 uppercase block">Variance</span>
                      <span className={`font-bold text-sm ${isPositive ? 'text-emerald-400' : 'text-amber-400'}`}>
                        {isPositive ? `+${variance.toFixed(1)}%` : `${variance.toFixed(1)}%`}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default BenchmarkComparisonCard;
