import React from 'react';
import { Truck, CheckCircle2, AlertTriangle, ShieldCheck, ShoppingBag } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const SupplyEcosystemCard = ({ supply = {}, provenance = [] }) => {
  const hubs = supply.hubs || [];
  const coverage = supply.critical_input_coverage || {};
  const risk = supply.supply_risk || 'LOW';
  const riskScore = supply.supply_risk_score ?? 0.20;
  const nearestDist = supply.nearest_hub_distance_km ?? (hubs[0]?.distance_km || 10.0);

  // Critical inputs mapping (dynamic)
  const inputEntries = Object.entries(coverage);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Truck className="w-5 h-5 text-emerald-400" />
              Supply Ecosystem & Sourcing Hubs
            </h3>
            <Stage6StatusBadge status={risk} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            APMC Mandi accessibility, critical input coverage, and logistics friction analysis.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Supply Risk Score:</span>
          <p className="text-xl font-bold text-emerald-400 font-mono">
            {riskScore.toFixed(2)} <span className="text-xs font-normal text-slate-400">/ 1.00</span>
          </p>
        </div>
      </div>

      {/* Overview Cards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Nearest Sourcing Hub</span>
          <p className="text-2xl font-bold text-slate-100 mt-1">
            {nearestDist.toFixed(1)} <span className="text-sm font-normal text-slate-400">km</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Distance: <strong className="text-emerald-400 uppercase">{supply.distance_assessment || 'ACCEPTABLE'}</strong>
          </p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Wholesale Hubs Mapped</span>
          <p className="text-2xl font-bold text-cyan-400 mt-1 font-mono">
            {supply.hub_count ?? hubs.length}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            APMC mandis & raw material clusters
          </p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Input Accessibility</span>
          <p className="text-2xl font-bold text-emerald-400 mt-1 uppercase">
            {supply.accessibility || 'HIGH'}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Confidence: {((supply.confidence || 0.80) * 100).toFixed(0)}%
          </p>
        </div>
      </div>

      {/* Critical Input Coverage Badges */}
      {inputEntries.length > 0 && (
        <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 space-y-2">
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider flex items-center gap-1.5">
            <ShoppingBag className="w-3.5 h-3.5 text-emerald-400" />
            Critical Input Categories Verified ({inputEntries.length})
          </h4>
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-2 pt-1">
            {inputEntries.map(([inputName, isAvailable], idx) => (
              <div
                key={idx}
                className="bg-slate-900 p-2.5 rounded-lg border border-slate-800 flex items-center justify-between text-xs"
              >
                <span className="font-medium text-slate-200 capitalize">{inputName.replace(/_/g, ' ')}</span>
                <span className={`text-[10px] font-mono px-2 py-0.5 rounded font-bold ${
                  isAvailable ? 'bg-emerald-500/10 text-emerald-400' : 'bg-rose-500/10 text-rose-400'
                }`}>
                  {isAvailable ? 'COVERED' : 'GAP'}
                </span>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Sourcing Hubs List */}
      <div>
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
          Mapped Supply Hubs & Mandis ({hubs.length})
        </h4>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
          {hubs.map((hub, idx) => (
            <div key={idx} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-2 text-xs">
              <div className="flex justify-between items-start gap-2">
                <div>
                  <p className="font-bold text-slate-100 text-sm">{hub.hub_name}</p>
                  <p className="text-slate-400 text-[11px] capitalize">{hub.hub_type?.replace(/_/g, ' ')}</p>
                </div>
                <div className="text-right shrink-0">
                  <span className="text-sm font-bold text-emerald-400 font-mono">{hub.distance_km} km</span>
                  <p className="text-[10px] text-slate-500 capitalize">Rating: {hub.accessibility_rating}</p>
                </div>
              </div>

              {hub.commodities_available && hub.commodities_available.length > 0 && (
                <div className="pt-2 border-t border-slate-900">
                  <span className="text-[10px] text-slate-500 uppercase font-bold">Commodities:</span>
                  <div className="flex flex-wrap gap-1 mt-1">
                    {hub.commodities_available.map((c, i) => (
                      <span key={i} className="text-[10px] bg-slate-900 px-1.5 py-0.5 rounded text-slate-300 border border-slate-800">
                        {c}
                      </span>
                    ))}
                  </div>
                </div>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Provenance */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="supply_accessibility_score"
        title="Supply Accessibility Provenance"
      />
    </div>
  );
};

export default SupplyEcosystemCard;
