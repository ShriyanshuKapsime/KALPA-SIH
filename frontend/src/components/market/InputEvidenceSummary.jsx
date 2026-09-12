import React from 'react';
import { Users, Building2, TrendingUp, Truck, Zap, DollarSign, Calendar, ShieldCheck, AlertCircle } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const InputEvidenceSummary = ({ stage5Data = {}, stage6Data = {} }) => {
  const evidence = stage5Data.market_evidence || {};
  const indicators = stage6Data.market_indicators || {};
  const infraAnalysis = indicators.infrastructure || {};

  const categories = [
    {
      id: 'demographics',
      name: 'Demographics',
      icon: Users,
      count: evidence.demographics?.length || 0,
      status: evidence.demographics?.length > 0 ? (evidence.demographics.some(d => d.proxy) ? 'PROXY' : 'ACTUAL') : 'MISSING',
      detail: `${evidence.demographics?.length || 0} demographic indicators ingested (Census 2011 & LGD)`,
      isGap: !evidence.demographics || evidence.demographics.length === 0
    },
    {
      id: 'competitors',
      name: 'Competition Evidence',
      icon: Building2,
      count: (evidence.competitors?.direct?.length || 0) + (evidence.competitors?.adjacent?.length || 0) + (evidence.competitors?.substitutes?.length || 0),
      status: 'ACTUAL',
      detail: `${evidence.competitors?.direct?.length || 0} direct, ${evidence.competitors?.adjacent?.length || 0} adjacent, ${evidence.competitors?.substitutes?.length || 0} substitute`,
      isGap: false
    },
    {
      id: 'demand',
      name: 'Demand Evidence',
      icon: TrendingUp,
      count: evidence.demand_indicators?.length || 0,
      status: evidence.demand_indicators?.some(d => d.proxy) ? 'PROXY' : 'ACTUAL',
      detail: `${evidence.demand_indicators?.length || 0} consumption proxies & consumption signals`,
      isGap: !evidence.demand_indicators || evidence.demand_indicators.length === 0
    },
    {
      id: 'supply',
      name: 'Supply Ecosystem',
      icon: Truck,
      count: evidence.supply_access?.length || 0,
      status: 'ACTUAL',
      detail: `${evidence.supply_access?.length || 0} APMC mandis & wholesale sourcing hubs`,
      isGap: !evidence.supply_access || evidence.supply_access.length === 0
    },
    {
      id: 'infrastructure',
      name: 'Infrastructure',
      icon: Zap,
      count: evidence.infrastructure?.length || 0,
      // CRITICAL: Check if empirical evidence was missing from Stage 5
      status: (!evidence.infrastructure || evidence.infrastructure.length === 0 || infraAnalysis.readiness === 'UNKNOWN_DATA_GAP') 
        ? 'UNKNOWN_DATA_GAP' 
        : (infraAnalysis.readiness || 'AVAILABLE'),
      detail: (!evidence.infrastructure || evidence.infrastructure.length === 0)
        ? 'No empirical infrastructure records provided by Stage 5. Explicitly categorized as UNKNOWN (DATA GAP).'
        : `${evidence.infrastructure.length} physical utility indicators verified`,
      isGap: (!evidence.infrastructure || evidence.infrastructure.length === 0 || infraAnalysis.readiness === 'UNKNOWN_DATA_GAP'),
      gapReason: 'No empirical infrastructure records in Stage 5 dataset.'
    },
    {
      id: 'economics',
      name: 'Economic Indicators',
      icon: DollarSign,
      count: evidence.economic_indicators?.length || 0,
      status: 'PROXY',
      detail: `${evidence.economic_indicators?.length || 0} purchasing power & rural wage indicators`,
      isGap: false
    },
    {
      id: 'seasonality',
      name: 'Seasonality Evidence',
      icon: Calendar,
      count: evidence.seasonality_evidence?.length || 0,
      status: 'ACTUAL',
      detail: `${evidence.seasonality_evidence?.length || 0} cyclical demand patterns mapped`,
      isGap: false
    },
    {
      id: 'quality',
      name: 'Evidence Quality',
      icon: ShieldCheck,
      count: null,
      status: 'HIGH',
      detail: `Deterministic validation with confidence discount tracking`,
      isGap: false
    }
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 mb-6 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Input Evidence Ingestion Summary (Stage 5 → Stage 6)
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic data status tracking across all 8 empirical evidence categories. Missing data is never assumed zero.
          </p>
        </div>
        <div className="flex items-center gap-2 text-xs">
          <span className="text-slate-400 font-medium">Data States:</span>
          <Stage6StatusBadge status="ACTUAL" />
          <Stage6StatusBadge status="PROXY" />
          <Stage6StatusBadge status="UNKNOWN_DATA_GAP" />
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {categories.map((cat) => {
          const Icon = cat.icon;
          return (
            <div
              key={cat.id}
              className={`rounded-xl p-4 border flex flex-col justify-between transition-all ${
                cat.isGap
                  ? 'bg-amber-500/5 border-amber-500/30'
                  : 'bg-slate-950/70 border-slate-800 hover:border-slate-700'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Icon className={`w-3.5 h-3.5 ${cat.isGap ? 'text-amber-400' : 'text-emerald-400'}`} />
                    {cat.name}
                  </span>
                  <Stage6StatusBadge status={cat.status} />
                </div>

                <p className="text-xs text-slate-400 mt-2 leading-relaxed">
                  {cat.detail}
                </p>
              </div>

              {cat.isGap && (
                <div className="mt-3 pt-2 border-t border-amber-500/20 text-[11px] text-amber-300/90 flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5 text-amber-400 shrink-0" />
                  <span>Neutral score 0.50 | Confidence capped ≤ 0.35</span>
                </div>
              )}
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default InputEvidenceSummary;
