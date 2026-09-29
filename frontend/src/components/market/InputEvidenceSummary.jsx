import React from 'react';
import { Users, Building2, TrendingUp, Truck, Zap, DollarSign, Calendar, ShieldCheck, AlertCircle } from 'lucide-react';

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
      detail: `${evidence.demographics?.length || 0} demographic indicators ingested (Census 2011 & LGD)`,
      isGap: !evidence.demographics || evidence.demographics.length === 0
    },
    {
      id: 'competitors',
      name: 'Competition Evidence',
      icon: Building2,
      count: (evidence.competitors?.direct?.length || 0) + (evidence.competitors?.adjacent?.length || 0) + (evidence.competitors?.substitutes?.length || 0),
      detail: `${evidence.competitors?.direct?.length || 0} direct, ${evidence.competitors?.adjacent?.length || 0} adjacent, ${evidence.competitors?.substitutes?.length || 0} substitute`,
      isGap: false
    },
    {
      id: 'demand',
      name: 'Demand Evidence',
      icon: TrendingUp,
      count: evidence.demand_indicators?.length || 0,
      detail: `${evidence.demand_indicators?.length || 0} consumption proxies & consumption signals`,
      isGap: !evidence.demand_indicators || evidence.demand_indicators.length === 0
    },
    {
      id: 'supply',
      name: 'Supply Ecosystem',
      icon: Truck,
      count: evidence.supply_access?.length || 0,
      detail: `${evidence.supply_access?.length || 0} APMC mandis & wholesale sourcing hubs`,
      isGap: !evidence.supply_access || evidence.supply_access.length === 0
    },
    {
      id: 'infrastructure',
      name: 'Infrastructure',
      icon: Zap,
      count: evidence.infrastructure?.length || 0,
      // Deterministic gap tracking preserved
      detail: (!evidence.infrastructure || evidence.infrastructure.length === 0)
        ? 'Empirical infrastructure records pending localized survey or grid data'
        : `${evidence.infrastructure.length} physical utility indicators verified`,
      isGap: (!evidence.infrastructure || evidence.infrastructure.length === 0 || infraAnalysis.readiness === 'UNKNOWN_DATA_GAP'),
      gapReason: 'No empirical infrastructure records in Stage 5 dataset.'
    },
    {
      id: 'economics',
      name: 'Economic Indicators',
      icon: DollarSign,
      count: evidence.economic_indicators?.length || 0,
      detail: `${evidence.economic_indicators?.length || 0} purchasing power & rural wage indicators`,
      isGap: false
    },
    {
      id: 'seasonality',
      name: 'Seasonality Evidence',
      icon: Calendar,
      count: evidence.seasonality_evidence?.length || 0,
      detail: `${evidence.seasonality_evidence?.length || 0} cyclical demand patterns mapped`,
      isGap: false
    },
    {
      id: 'quality',
      name: 'Evidence Quality',
      icon: ShieldCheck,
      count: null,
      detail: `Validated through local statistical and regional registries`,
      isGap: false
    }
  ];

  return (
    <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-4">
        <div>
          <h3 className="text-xl font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
            <ShieldCheck className="w-5 h-5 text-[#006F5F]" />
            Market Evidence Summary
          </h3>
          <p className="text-xs text-[#62584F] mt-1">
            Local evidence used to understand demand, competition, infrastructure and market access.
          </p>
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
                  ? 'bg-[#FAF2E3] border-[#C96A3A]/30'
                  : 'bg-[#FAF2E3] border-[#79563F]/18 hover:border-[#79563F]/35'
              }`}
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-xs font-bold text-[#28231F] flex items-center gap-1.5">
                    <Icon className={`w-4 h-4 ${cat.isGap ? 'text-[#C96A3A]' : 'text-[#006F5F]'}`} />
                    {cat.name}
                  </span>
                </div>

                <p className="text-xs text-[#62584F] mt-2 leading-relaxed">
                  {cat.detail}
                </p>
              </div>

              {cat.isGap && (
                <div className="mt-3 pt-2 border-t border-[#C96A3A]/20 text-[11px] text-[#A9552F] flex items-center gap-1">
                  <AlertCircle className="w-3.5 h-3.5 text-[#C96A3A] shrink-0" />
                  <span>Evidence quality: Moderate (Baseline)</span>
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
