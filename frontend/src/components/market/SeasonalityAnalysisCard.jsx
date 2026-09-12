import React from 'react';
import { Calendar, TrendingUp, TrendingDown, Activity, AlertTriangle } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const SeasonalityAnalysisCard = ({ seasonality = {}, provenance = [] }) => {
  const peakMonths = seasonality.peak_months || [];
  const leanMonths = seasonality.lean_months || [];
  const multipliers = seasonality.monthly_multipliers || {};
  const volatility = seasonality.annual_volatility ?? 0.0;
  const risk = seasonality.seasonal_risk || 'LOW';
  const notes = seasonality.seasonal_notes;

  const months = [
    { key: 'jan', label: 'Jan' },
    { key: 'feb', label: 'Feb' },
    { key: 'mar', label: 'Mar' },
    { key: 'apr', label: 'Apr' },
    { key: 'may', label: 'May' },
    { key: 'jun', label: 'Jun' },
    { key: 'jul', label: 'Jul' },
    { key: 'aug', label: 'Aug' },
    { key: 'sep', label: 'Sep' },
    { key: 'oct', label: 'Oct' },
    { key: 'nov', label: 'Nov' },
    { key: 'dec', label: 'Dec' },
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Calendar className="w-5 h-5 text-emerald-400" />
              Annual Seasonality & Volatility Modeling
            </h3>
            <Stage6StatusBadge status={risk} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic 12-month cyclical multiplier synthesis, peak/lean window detection, and risk profiling.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Volatility Index (σ):</span>
          <p className="text-xl font-bold text-emerald-400 font-mono">
            {volatility.toFixed(4)}
          </p>
        </div>
      </div>

      {/* Top Peak/Lean/Volatility Highlights */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Peak Period */}
        <div className="bg-slate-950 p-4 rounded-xl border border-emerald-500/20">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <TrendingUp className="w-3.5 h-3.5 text-emerald-400" /> Peak Months
            </span>
            <span className="text-xs font-mono font-bold text-emerald-300">
              {(seasonality.peak_multiplier || 1.25).toFixed(2)}x
            </span>
          </div>
          <p className="text-sm font-bold text-slate-100 mt-2 font-mono">
            {peakMonths.length > 0 ? peakMonths.join(', ') : 'Oct, Nov, Dec, Jan'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Festival, wedding & post-harvest demand surge
          </p>
        </div>

        {/* Lean Period */}
        <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/20">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
              <TrendingDown className="w-3.5 h-3.5 text-amber-400" /> Lean Months
            </span>
            <span className="text-xs font-mono font-bold text-amber-300">
              {(seasonality.lean_multiplier || 0.75).toFixed(2)}x
            </span>
          </div>
          <p className="text-sm font-bold text-slate-100 mt-2 font-mono">
            {leanMonths.length > 0 ? leanMonths.join(', ') : 'May, Jun, Jul'}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Monsoon lean period & reduced consumption
          </p>
        </div>

        {/* Seasonal Risk Rating */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-medium text-slate-400 flex items-center gap-1.5">
              <Activity className="w-3.5 h-3.5 text-cyan-400" /> Seasonal Risk
            </span>
            <Stage6StatusBadge status={risk} />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-1 uppercase">
            {risk}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Standard deviation volatility: {(volatility * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {notes && (
        <div className="p-3.5 rounded-xl bg-slate-950 border border-slate-800 text-xs text-slate-300 flex items-start gap-2">
          <span className="text-emerald-400 font-bold shrink-0">Context Note:</span>
          <span>{notes}</span>
        </div>
      )}

      {/* 12-Month Multiplier Table & Visualization */}
      <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800 space-y-3">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          12-Month Demand Multiplier Curve
        </h4>
        <div className="grid grid-cols-3 sm:grid-cols-6 lg:grid-cols-12 gap-2">
          {months.map((m) => {
            const mult = multipliers[m.key] ?? multipliers[m.label.toLowerCase()] ?? multipliers[m.label] ?? 1.0;
            const isPeak = mult > 1.10;
            const isLean = mult < 0.90;
            return (
              <div
                key={m.key}
                className={`p-2.5 rounded-lg border text-center transition-all ${
                  isPeak
                    ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300'
                    : isLean
                    ? 'bg-amber-500/10 border-amber-500/30 text-amber-300'
                    : 'bg-slate-900 border-slate-800 text-slate-300'
                }`}
              >
                <span className="text-[11px] font-bold block">{m.label}</span>
                <span className="text-xs font-mono font-extrabold mt-1 block">
                  {mult.toFixed(2)}x
                </span>
                <span className={`text-[9px] uppercase font-mono block mt-1 ${
                  isPeak ? 'text-emerald-400' : isLean ? 'text-amber-400' : 'text-slate-500'
                }`}>
                  {isPeak ? 'Peak' : isLean ? 'Lean' : 'Base'}
                </span>
              </div>
            );
          })}
        </div>
      </div>

      {/* Provenance */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="annual_seasonality_volatility"
        title="Seasonality Volatility Provenance"
      />
    </div>
  );
};

export default SeasonalityAnalysisCard;
