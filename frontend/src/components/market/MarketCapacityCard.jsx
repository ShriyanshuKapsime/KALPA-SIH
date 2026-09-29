import React from 'react';
import { PieChart, Scale, ShieldCheck, AlertCircle, Compass, Building2 } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const MarketCapacityCard = ({ capacity = {} }) => {
  const status = capacity.status || 'LIMITED';
  const signal = capacity.capacity_signal || 'MODERATE_PRESSURE';
  const netScore = capacity.net_capacity_score ?? 0.50;
  const demandSignal = capacity.demand_signal || 'MODERATE';
  const compPressure = capacity.competition_pressure || 'MODERATE';
  const confidence = capacity.confidence ?? 0.70;
  const limitations = capacity.limitations || [];

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-7 border border-[#79563F]/18 space-y-5 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 border-b border-[#79563F]/15 pb-4">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-lg sm:text-xl font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <PieChart className="w-5 h-5 text-[#006F5F]" />
              Net Market Capacity &amp; Expansion Signal
            </h3>
            <span className="text-[11px] font-mono px-2 py-0.5 rounded-full bg-[#006F5F]/10 text-[#006F5F] font-bold border border-[#006F5F]/20">
              SYNTHESIS CONCLUSION
            </span>
          </div>
          <p className="text-xs text-[#62584F] mt-1">
            Synthesis of demand absorption headroom versus proximity-weighted competitive saturation.
          </p>
        </div>
        <div className="flex items-center gap-2">
          <Stage6StatusBadge status={signal} />
        </div>
      </div>

      {/* Synthesis Big Signal & 4-Metric Strip */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
        {/* Strategic Signal */}
        <div className="bg-[#FAF2E3]/90 p-4 rounded-xl border border-[#006F5F]/25 shadow-2xs">
          <span className="text-[11px] text-[#79563F] font-medium block">Strategic Signal</span>
          <p className="text-lg font-extrabold text-[#006F5F] mt-1 capitalize font-['Outfit']">
            {signal.replace(/_/g, ' ')}
          </p>
          <p className="text-[11px] text-[#62584F] mt-0.5">
            Status: <strong className="text-[#28231F] uppercase">{status}</strong>
          </p>
        </div>

        {/* Net Capacity Score */}
        <div className="bg-[#FAF2E3]/90 p-4 rounded-xl border border-[#79563F]/12 shadow-2xs">
          <span className="text-[11px] text-[#79563F] font-medium block">Market Capacity Score</span>
          <p className="text-2xl font-bold text-[#28231F] mt-1 font-mono">
            {netScore.toFixed(2)}
            <span className="text-xs font-normal text-[#62584F]"> / 1.00</span>
          </p>
          <p className="text-[11px] text-[#62584F] mt-0.5">
            Headroom absorption index
          </p>
        </div>

        {/* Equilibrium Dynamics */}
        <div className="bg-[#FAF2E3]/90 p-4 rounded-xl border border-[#79563F]/12 shadow-2xs">
          <span className="text-[11px] text-[#79563F] font-medium block">Equilibrium Dynamics</span>
          <div className="mt-1 space-y-0.5 text-xs">
            <div className="flex justify-between">
              <span className="text-[#62584F] text-[11px]">Demand:</span>
              <strong className="text-[#006F5F] font-mono uppercase text-xs">{demandSignal}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-[#62584F] text-[11px]">Saturation:</span>
              <strong className="text-[#79563F] font-mono uppercase text-xs">{compPressure}</strong>
            </div>
          </div>
        </div>

        {/* Evidence Confidence */}
        <div className="bg-[#FAF2E3]/90 p-4 rounded-xl border border-[#79563F]/12 shadow-2xs">
          <span className="text-[11px] text-[#79563F] font-medium flex items-center gap-1">
            <ShieldCheck className="w-3.5 h-3.5 text-[#006F5F]" /> Confidence &amp; Level
          </span>
          <p className="text-2xl font-bold text-[#006F5F] mt-1 font-mono">
            {(confidence * 100).toFixed(0)}%
          </p>
          <p className="text-[11px] text-[#62584F] mt-0.5">
            Evidence: <strong className="text-[#28231F] uppercase">{capacity.evidence_level || 'MODERATE'}</strong>
          </p>
        </div>
      </div>

      {/* Assumptions & Boundary Notes */}
      {limitations.length > 0 && (
        <div className="bg-[#FAF2E3]/90 p-3.5 rounded-xl border border-[#79563F]/12 space-y-1">
          <h4 className="text-[11px] font-bold text-[#28231F] uppercase tracking-wider flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-[#C96A3A]" />
            Modeling Assumptions &amp; Boundary Conditions
          </h4>
          <ul className="list-disc list-inside text-[11px] text-[#62584F] space-y-0.5 leading-relaxed">
            {limitations.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
};

export default MarketCapacityCard;
