import React from 'react';
import { Compass } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const DemandEvidenceCard = ({ demand = {} }) => {
  const strength = demand.demand_signal_strength || 'MODERATE';
  const score = demand.demand_signal_score ?? 0.50;

  const popFeature = demand.population_feature || {};
  const hhFeature = demand.household_feature || {};
  const consumptionProxy = demand.consumption_proxy || {};
  const purchasingPower = demand.purchasing_power_proxy || {};
  const consumptionSignals = demand.consumption_signals || [];

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Compass className="w-4 h-4 text-[#006F5F]" />
              Demand Evidence &amp; Consumption Analysis
            </h3>
            <Stage6StatusBadge status={strength} />
          </div>
          <p className="text-xs text-[#62584F] mt-0.5">
            Local demand indicators synthesized with district population and purchasing power baselines.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Demand Score: </span>
          <span className="text-base font-bold text-[#28231F] font-mono">
            {score.toFixed(2)}
            <span className="text-[11px] font-normal text-[#62584F]"> / 1.00</span>
          </span>
        </div>
      </div>

      {/* Aggregate Indicators Grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Population Base */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[10px] text-[#79563F] font-medium block">Population</span>
          <p className="text-sm font-bold text-[#28231F] mt-0.5 font-mono">
            {popFeature.value != null ? Number(popFeature.value).toLocaleString('en-IN') : (
              <span className="text-[11px] font-normal text-[#79563F]/70 font-sans italic">Data not available</span>
            )}
          </p>
          <p className="text-[9px] text-[#62584F] mt-0.5">
            Census 2011 / LGD
          </p>
        </div>

        {/* Household Scale */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[10px] text-[#79563F] font-medium block">Household Density</span>
          <p className="text-sm font-bold text-[#28231F] mt-0.5 font-mono">
            {hhFeature.value != null ? Number(hhFeature.value).toLocaleString('en-IN') : (
              <span className="text-[11px] font-normal text-[#79563F]/70 font-sans italic">Data not available</span>
            )}
          </p>
          <p className="text-[9px] text-[#62584F] mt-0.5">
            Purchasing units
          </p>
        </div>

        {/* Consumption Benchmark */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[10px] text-[#79563F] font-medium block">Benchmark</span>
          <p className="text-sm font-bold text-[#28231F] mt-0.5 font-mono">
            {consumptionProxy.value != null ? (
              <>
                {Number(consumptionProxy.value).toLocaleString('en-IN')}
                <span className="text-[9px] font-normal text-[#62584F] ml-0.5">{consumptionProxy.unit || ''}</span>
              </>
            ) : (
              <span className="text-[11px] font-normal text-[#79563F]/70 font-sans italic">Data not available</span>
            )}
          </p>
          <p className="text-[9px] text-[#62584F] mt-0.5">
            Regional baseline
          </p>
        </div>

        {/* Purchasing Power */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[10px] text-[#79563F] font-medium block">Purchasing Power</span>
          <p className="text-sm font-bold text-[#28231F] mt-0.5 font-mono">
            {purchasingPower.value != null ? (
              `₹${Number(purchasingPower.value).toLocaleString('en-IN')}`
            ) : (
              <span className="text-[11px] font-normal text-[#79563F]/70 font-sans italic">Data not available</span>
            )}
          </p>
          <p className="text-[9px] text-[#62584F] mt-0.5">
            Per capita income
          </p>
        </div>
      </div>

      {/* Synthesized Demand Signals List */}
      {consumptionSignals.length > 0 ? (
        <div className="space-y-1.5">
          <h4 className="text-[10px] font-bold text-[#28231F] uppercase tracking-wider">
            Synthesized Demand Signals ({consumptionSignals.length})
          </h4>
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
            {consumptionSignals.map((sig, idx) => (
              <div key={idx} className="bg-[#FAF2E3]/90 p-2 rounded-lg border border-[#79563F]/12 space-y-0.5 text-xs">
                <div className="flex justify-between items-start gap-1">
                  <div className="truncate">
                    <p className="font-bold text-[#28231F] truncate text-xs">{sig.indicator_name || sig.name}</p>
                    <p className="text-[#62584F] text-[9px] capitalize truncate">{sig.category || 'General'}</p>
                  </div>
                  <span className="text-[9px] text-[#79563F] font-mono shrink-0">
                    Conf: {((sig.confidence || 0.85) * 100).toFixed(0)}%
                  </span>
                </div>
                <div className="pt-1 border-t border-[#79563F]/10 flex justify-between items-baseline">
                  <span className="text-sm font-bold text-[#006F5F] font-mono">
                    {typeof sig.normalized_value === 'number' ? sig.normalized_value.toFixed(2) : String(sig.normalized_value || sig.value || '—')}
                    {sig.unit && <span className="text-[9px] text-[#62584F] ml-0.5">{sig.unit}</span>}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-lg border border-[#79563F]/12 text-xs text-[#62584F] italic">
          Additional micro-level consumption telemetry will synchronize from primary field surveys.
        </div>
      )}
    </div>
  );
};

export default DemandEvidenceCard;
