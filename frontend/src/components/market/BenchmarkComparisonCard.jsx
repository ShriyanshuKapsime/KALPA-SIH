import React from 'react';
import { Award, Database } from 'lucide-react';

export const BenchmarkComparisonCard = ({ benchmarkAnalysis = {} }) => {
  const comparisons = benchmarkAnalysis.comparisons || [];
  const benchmarksUsed = benchmarkAnalysis.benchmarks_used || [];

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Award className="w-4 h-4 text-[#006F5F]" />
              Official Dataset Benchmarks &amp; Deviations
            </h3>
            <span className="text-[10px] px-2 py-0.5 rounded bg-[#006F5F]/10 text-[#006F5F] border border-[#006F5F]/20 font-mono font-bold">
              Census 2011 / NABARD / MSME
            </span>
          </div>
          <p className="text-xs text-[#62584F] mt-0.5">
            Statistical normalization against official Indian national and state-level baselines.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Repositories: </span>
          <span className="text-xs font-bold text-[#006F5F] font-mono">{benchmarksUsed.length} Datasets</span>
        </div>
      </div>

      {/* Benchmarks Used Badges */}
      {benchmarksUsed.length > 0 && (
        <div className="flex flex-wrap gap-1">
          {benchmarksUsed.map((b, idx) => (
            <span
              key={idx}
              className="inline-flex items-center gap-1 bg-[#FAF2E3]/90 px-2 py-0.5 rounded-lg border border-[#79563F]/12 text-[10px] text-[#28231F] font-mono shadow-2xs"
            >
              <Database className="w-2.5 h-2.5 text-[#006F5F]" /> {b}
            </span>
          ))}
        </div>
      )}

      {/* Comparisons List */}
      {comparisons.length === 0 ? (
        <div className="p-2.5 rounded-xl bg-[#FAF2E3]/90 border border-[#79563F]/12 text-xs text-[#62584F]">
          No explicit benchmark deviation records returned for this business context.
        </div>
      ) : (
        <div className="space-y-1.5">
          {comparisons.map((c, idx) => {
            const variance = c.variance_percentage;
            const isPositive = variance !== null && variance !== undefined && variance > 0;
            return (
              <div
                key={idx}
                className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12 flex flex-col sm:flex-row sm:items-center justify-between gap-1.5 text-xs"
              >
                <div className="space-y-0.5 truncate pr-2">
                  <div className="flex items-center gap-1.5">
                    <span className="font-bold text-[#28231F] text-xs truncate">{c.benchmark_name}</span>
                    <span className="text-[9px] font-mono text-[#79563F] bg-[#F1E4CC]/80 px-1.5 py-0.5 rounded border border-[#79563F]/12 shrink-0">
                      {c.benchmark_id}
                    </span>
                  </div>
                  <p className="text-[#62584F] text-[10px] truncate">
                    Evaluation: <strong className="text-[#28231F]">{c.comparison_result}</strong>
                  </p>
                </div>

                <div className="flex items-center gap-3 shrink-0 font-mono text-xs">
                  <div>
                    <span className="text-[8px] text-[#79563F] uppercase block">Actual</span>
                    <strong className="text-[#28231F]">{typeof c.actual_value === 'number' ? c.actual_value.toLocaleString('en-IN') : String(c.actual_value)}</strong>
                  </div>

                  <div>
                    <span className="text-[8px] text-[#79563F] uppercase block">Benchmark</span>
                    <strong className="text-[#006F5F]">{typeof c.benchmark_value === 'number' ? c.benchmark_value.toLocaleString('en-IN') : String(c.benchmark_value)}</strong>
                  </div>

                  {variance !== null && variance !== undefined && (
                    <div className="text-right">
                      <span className="text-[8px] text-[#79563F] uppercase block">Variance</span>
                      <span className={`font-bold ${isPositive ? 'text-[#006F5F]' : 'text-[#C96A3A]'}`}>
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
