import React from 'react';
import { PieChart, Scale, ArrowUpRight, AlertCircle, ShieldCheck, TrendingUp } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const MarketCapacityCard = ({ capacity = {}, provenance = [] }) => {
  const status = capacity.status || 'LIMITED';
  const signal = capacity.capacity_signal || 'MODERATE_PRESSURE';
  const netScore = capacity.net_capacity_score ?? 0.50;
  const demandSignal = capacity.demand_signal || 'MODERATE';
  const compPressure = capacity.competition_pressure || 'MODERATE';
  const confidence = capacity.confidence ?? 0.70;
  const limitations = capacity.limitations || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <PieChart className="w-5 h-5 text-emerald-400" />
              Net Market Capacity & Expansion Signal
            </h3>
            <Stage6StatusBadge status={signal} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic synthesis of demand absorption headroom versus proximity-weighted competitive saturation.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Net Capacity Score:</span>
          <p className="text-xl font-bold text-emerald-400 font-mono">
            {netScore.toFixed(2)} <span className="text-xs font-normal text-slate-400">/ 1.00</span>
          </p>
        </div>
      </div>

      {/* Main Capacity Balance Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Capacity Signal */}
        <div className="bg-slate-950 p-4 rounded-xl border border-emerald-500/20">
          <div className="flex justify-between items-start">
            <span className="text-xs text-slate-400 font-medium">Strategic Signal</span>
            <Stage6StatusBadge status={signal} />
          </div>
          <p className="text-lg font-bold text-slate-100 mt-2 capitalize">
            {signal.replace(/_/g, ' ')}
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Capacity Status: <strong className="text-emerald-400 uppercase">{status}</strong>
          </p>
        </div>

        {/* Demand vs Competition Balance */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Scale className="w-3.5 h-3.5 text-cyan-400" /> Equilibrium Dynamics
          </span>
          <div className="mt-2 space-y-1.5 text-xs">
            <div className="flex justify-between">
              <span className="text-slate-400">Demand Signal:</span>
              <strong className="text-slate-200 font-mono uppercase">{demandSignal}</strong>
            </div>
            <div className="flex justify-between">
              <span className="text-slate-400">Competition Saturation:</span>
              <strong className="text-slate-200 font-mono uppercase">{compPressure}</strong>
            </div>
          </div>
        </div>

        {/* Confidence & Evidence Level */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <ShieldCheck className="w-3.5 h-3.5 text-teal-400" /> Evidence Confidence
          </span>
          <p className="text-2xl font-bold text-teal-300 mt-1 font-mono">
            {(confidence * 100).toFixed(0)}%
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Evidence Level: <strong className="text-slate-300 uppercase">{capacity.evidence_level || 'MODERATE'}</strong>
          </p>
        </div>
      </div>

      {/* Limitations and Assumptions */}
      {limitations.length > 0 && (
        <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <AlertCircle className="w-3.5 h-3.5 text-amber-400" />
            Deterministic Modeling Assumptions & Boundary Conditions
          </h4>
          <ul className="list-disc list-inside text-xs text-slate-400 space-y-1">
            {limitations.map((lim, idx) => (
              <li key={idx}>{lim}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Provenance */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="net_market_capacity_score"
        title="Market Capacity Provenance"
      />
    </div>
  );
};

export default MarketCapacityCard;
