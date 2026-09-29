import React from 'react';
import { Calendar, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const SeasonalityAnalysisCard = ({ seasonality = {} }) => {
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
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Calendar className="w-4 h-4 text-[#006F5F]" />
              Annual Seasonality &amp; Volatility Modeling
            </h3>
            <Stage6StatusBadge status={risk} />
          </div>
          <p className="text-xs text-[#62584F] mt-0.5">
            12-month cyclical demand multipliers, peak/lean window detection, and risk profiling.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Volatility Index (σ): </span>
          <span className="text-base font-bold text-[#28231F] font-mono">
            {volatility.toFixed(4)}
          </span>
        </div>
      </div>

      {/* Top 3 Summary Metrics */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {/* Peak Period */}
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#006F5F]/20">
          <div className="flex justify-between items-center mb-0.5">
            <span className="text-[11px] font-bold text-[#006F5F] flex items-center gap-1">
              <TrendingUp className="w-3 h-3 text-[#006F5F]" /> Peak Window
            </span>
            <span className="text-xs font-mono font-bold text-[#006F5F]">
              {(seasonality.peak_multiplier || 1.25).toFixed(2)}x
            </span>
          </div>
          <p className="text-xs font-bold text-[#28231F] font-mono mt-0.5">
            {peakMonths.length > 0 ? peakMonths.join(', ') : 'Oct, Nov, Dec, Jan'}
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Festival &amp; post-harvest surge
          </p>
        </div>

        {/* Lean Period */}
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#C96A3A]/20">
          <div className="flex justify-between items-center mb-0.5">
            <span className="text-[11px] font-bold text-[#C96A3A] flex items-center gap-1">
              <TrendingDown className="w-3 h-3 text-[#C96A3A]" /> Lean Window
            </span>
            <span className="text-xs font-mono font-bold text-[#C96A3A]">
              {(seasonality.lean_multiplier || 0.75).toFixed(2)}x
            </span>
          </div>
          <p className="text-xs font-bold text-[#28231F] font-mono mt-0.5">
            {leanMonths.length > 0 ? leanMonths.join(', ') : 'May, Jun, Jul'}
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Monsoon lean period
          </p>
        </div>

        {/* Seasonal Risk */}
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <div className="flex justify-between items-center mb-0.5">
            <span className="text-[11px] font-medium text-[#79563F] flex items-center gap-1">
              <Activity className="w-3 h-3 text-[#79563F]" /> Seasonal Risk
            </span>
            <Stage6StatusBadge status={risk} />
          </div>
          <p className="text-base font-bold text-[#28231F] uppercase mt-0.5 font-mono">
            {risk}
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Margin: {(volatility * 100).toFixed(1)}%
          </p>
        </div>
      </div>

      {notes && (
        <div className="p-2.5 rounded-lg bg-[#FAF2E3]/90 border border-[#79563F]/12 text-xs text-[#28231F] flex items-start gap-2">
          <span className="text-[#006F5F] font-bold shrink-0 text-[11px]">Context:</span>
          <span className="text-[#62584F] text-[11px] leading-relaxed">{notes}</span>
        </div>
      )}

      {/* 12-Month Multiplier Visualization */}
      <div className="bg-[#FAF2E3]/90 p-3.5 rounded-xl border border-[#79563F]/12 space-y-2">
        <h4 className="text-[11px] font-bold text-[#28231F] uppercase tracking-wider">
          12-Month Demand Multiplier Curve
        </h4>
        <div className="grid grid-cols-4 sm:grid-cols-6 lg:grid-cols-12 gap-1.5">
          {months.map((m) => {
            const mult = multipliers[m.key] ?? multipliers[m.label.toLowerCase()] ?? multipliers[m.label] ?? 1.0;
            const isPeak = mult > 1.10;
            const isLean = mult < 0.90;
            return (
              <div
                key={m.key}
                className={`p-1.5 rounded-lg border text-center transition-all ${
                  isPeak
                    ? 'bg-[#006F5F]/10 border-[#006F5F]/25 text-[#006F5F]'
                    : isLean
                    ? 'bg-[#C96A3A]/10 border-[#C96A3A]/25 text-[#C96A3A]'
                    : 'bg-[#F1E4CC]/80 border-[#79563F]/12 text-[#28231F]'
                }`}
              >
                <span className="text-[10px] font-bold block">{m.label}</span>
                <span className="text-xs font-mono font-extrabold mt-0.5 block">
                  {mult.toFixed(2)}x
                </span>
                <span className={`text-[8px] uppercase font-mono block font-bold ${
                  isPeak ? 'text-[#006F5F]' : isLean ? 'text-[#C96A3A]' : 'text-[#79563F]'
                }`}>
                  {isPeak ? 'Peak' : isLean ? 'Lean' : 'Base'}
                </span>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default SeasonalityAnalysisCard;
