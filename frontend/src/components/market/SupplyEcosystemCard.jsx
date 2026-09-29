import React from 'react';
import { Truck, ShoppingBag } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const SupplyEcosystemCard = ({ supply = {} }) => {
  const hubs = supply.hubs || [];
  const coverage = supply.critical_input_coverage || {};
  const risk = supply.supply_risk || 'LOW';
  const riskScore = supply.supply_risk_score ?? 0.20;
  const nearestDist = supply.nearest_hub_distance_km ?? (hubs[0]?.distance_km || 10.0);

  const inputEntries = Object.entries(coverage);

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Truck className="w-4 h-4 text-[#006F5F]" />
              Supply Ecosystem &amp; Sourcing Hubs
            </h3>
            <Stage6StatusBadge status={risk} />
          </div>
          <p className="text-xs text-[#62584F] mt-0.5">
            APMC Mandi accessibility, critical input coverage, and sourcing network.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Supply Risk: </span>
          <span className="text-base font-bold text-[#28231F] font-mono">
            {riskScore.toFixed(2)}
            <span className="text-[11px] font-normal text-[#62584F]"> / 1.00</span>
          </span>
        </div>
      </div>

      {/* 3 Metric Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium">Nearest Sourcing Hub</span>
          <p className="text-lg font-bold text-[#28231F] mt-0.5 font-mono">
            {nearestDist.toFixed(1)} <span className="text-xs font-normal text-[#62584F]">km</span>
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Access: <strong className="text-[#006F5F] uppercase font-semibold">{supply.distance_assessment || 'ACCEPTABLE'}</strong>
          </p>
        </div>

        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium">Wholesale Hubs</span>
          <p className="text-lg font-bold text-[#006F5F] mt-0.5 font-mono">
            {supply.hub_count ?? hubs.length}
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            APMC mandis &amp; clusters
          </p>
        </div>

        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium">Input Accessibility</span>
          <p className="text-lg font-bold text-[#006F5F] mt-0.5 uppercase">
            {supply.accessibility || 'HIGH'}
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Confidence: {((supply.confidence || 0.80) * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Critical Input Coverage Chips */}
      {inputEntries.length > 0 && (
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12 space-y-1.5">
          <h4 className="text-[10px] font-bold text-[#28231F] uppercase tracking-wider flex items-center gap-1.5">
            <ShoppingBag className="w-3 h-3 text-[#006F5F]" />
            Critical Input Categories Verified ({inputEntries.length})
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
            {inputEntries.map(([inputName, isAvailable], idx) => (
              <div
                key={idx}
                className="bg-[#F1E4CC]/80 px-2 py-1 rounded-lg border border-[#79563F]/12 flex items-center justify-between text-xs"
              >
                <span className="font-medium text-[#28231F] capitalize truncate mr-1 text-[10px]">{inputName.replace(/_/g, ' ')}</span>
                <span className={`text-[8px] font-mono px-1 py-0.5 rounded font-bold shrink-0 ${
                  isAvailable ? 'bg-[#006F5F]/10 text-[#006F5F]' : 'bg-[#C96A3A]/15 text-[#C96A3A]'
                }`}>
                  {isAvailable ? 'OK' : 'GAP'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Mapped Sourcing Hubs List */}
      <div>
        <h4 className="text-[11px] font-bold text-[#28231F] uppercase tracking-wider mb-1.5">
          Mapped Sourcing Hubs ({hubs.length})
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
          {hubs.map((hub, idx) => (
            <div key={idx} className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12 space-y-1 text-xs">
              <div className="flex justify-between items-start gap-2">
                <div className="truncate">
                  <p className="font-bold text-[#28231F] truncate text-xs">{hub.hub_name}</p>
                  <p className="text-[#62584F] text-[10px] capitalize truncate">{hub.hub_type?.replace(/_/g, ' ')}</p>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-xs font-bold text-[#006F5F] font-mono">{hub.distance_km} km</span>
                  <p className="text-[9px] text-[#79563F] capitalize">{hub.accessibility_rating || 'Good'}</p>
                </div>
              </div>

              {hub.commodities_available && hub.commodities_available.length > 0 && (
                <div className="pt-1 border-t border-[#79563F]/10 flex flex-wrap gap-1">
                  {hub.commodities_available.map((c, i) => (
                    <span key={i} className="text-[9px] bg-[#F1E4CC]/80 px-1.5 py-0.5 rounded text-[#28231F] border border-[#79563F]/12">
                      {c}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  );
};

export default SupplyEcosystemCard;
