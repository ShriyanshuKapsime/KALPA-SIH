import React from 'react';
import { TrendingUp, Users, DollarSign, Award, CheckCircle2, AlertCircle } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const DemandEvidenceCard = ({ demand = {}, provenance = [] }) => {
  const strength = demand.demand_signal_strength || 'MODERATE';
  const score = demand.demand_signal_score ?? 0.50;
  const confidence = demand.confidence ?? 0.85;

  const popFeature = demand.population_feature || {};
  const hhFeature = demand.household_feature || {};
  const consumptionProxy = demand.consumption_proxy || {};
  const purchasingPower = demand.purchasing_power_proxy || {};

  const consumptionSignals = demand.consumption_signals || [];
  const demographicSignals = demand.demographic_signals || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <TrendingUp className="w-5 h-5 text-emerald-400" />
              Demand Evidence & Consumption Analysis
            </h3>
            <Stage6StatusBadge status={strength} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Empirical demand indicators synthesized with district population scaling and purchasing power proxies.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Demand Signal Score:</span>
          <p className="text-xl font-bold text-emerald-400 font-mono">
            {score.toFixed(2)} <span className="text-xs font-normal text-slate-400">/ 1.00</span>
          </p>
        </div>
      </div>

      {/* Aggregate Indicators Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-4 gap-4">
        {/* Population Base */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-start">
            <span className="text-xs text-slate-400 font-medium">Catchment Population</span>
            <Stage6StatusBadge status="ACTUAL" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">
            {popFeature.value ? popFeature.value.toLocaleString('en-IN') : '—'}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Source: Census 2011 / LGD
          </p>
        </div>

        {/* Household Scale */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <div className="flex justify-between items-start">
            <span className="text-xs text-slate-400 font-medium">Household Density</span>
            <Stage6StatusBadge status="ACTUAL" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">
            {hhFeature.value ? hhFeature.value.toLocaleString('en-IN') : '—'}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Target purchasing units
          </p>
        </div>

        {/* Consumption Proxy */}
        <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/20">
          <div className="flex justify-between items-start">
            <span className="text-xs text-slate-400 font-medium">Consumption Proxy</span>
            <Stage6StatusBadge status="PROXY" />
          </div>
          <p className="text-2xl font-bold text-amber-300 mt-2 font-mono">
            {consumptionProxy.value ? consumptionProxy.value.toLocaleString('en-IN') : '—'}
            <span className="text-xs font-normal text-slate-400 ml-1.5">{consumptionProxy.unit || ''}</span>
          </p>
          <p className="text-[11px] text-amber-400/90 mt-1">
            ⚠️ Derived via NSSO consumption model
          </p>
        </div>

        {/* Purchasing Power */}
        <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/20">
          <div className="flex justify-between items-start">
            <span className="text-xs text-slate-400 font-medium">Purchasing Power</span>
            <Stage6StatusBadge status="PROXY" />
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-2 font-mono">
            ₹{purchasingPower.value ? Number(purchasingPower.value).toLocaleString('en-IN') : '—'}
          </p>
          <p className="text-[11px] text-slate-500 mt-1">
            Per capita income proxy (DES/RBI)
          </p>
        </div>
      </div>

      {/* Demand Signals & Proxies Table */}
      {consumptionSignals.length > 0 && (
        <div className="space-y-3">
          <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider">
            Synthesized Demand Signals ({consumptionSignals.length})
          </h4>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
            {consumptionSignals.map((sig, idx) => (
              <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
                <div className="flex justify-between items-start gap-2">
                  <div>
                    <p className="font-bold text-slate-200">{sig.indicator_name || sig.name}</p>
                    <p className="text-slate-400 text-[11px] mt-0.5 capitalize">Category: {sig.category}</p>
                  </div>
                  <Stage6StatusBadge status={sig.data_status || 'PROXY'} />
                </div>
                <div className="flex justify-between items-baseline pt-2 border-t border-slate-900">
                  <span className="text-lg font-bold text-emerald-400 font-mono">
                    {typeof sig.normalized_value === 'number' ? sig.normalized_value.toFixed(2) : String(sig.normalized_value || sig.value || '—')}
                    <span className="text-xs text-slate-400 ml-1">{sig.unit}</span>
                  </span>
                  <span className="text-[11px] text-slate-500">Confidence: {((sig.confidence || 0.85) * 100).toFixed(0)}%</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Provenance */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="demand_signal_strength"
        title="Demand Signal Calculation Provenance"
      />
    </div>
  );
};

export default DemandEvidenceCard;
