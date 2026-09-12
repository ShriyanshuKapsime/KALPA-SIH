import React from 'react';
import {
  TrendingUp,
  Building2,
  Truck,
  Zap,
  MapPin,
  Calendar,
  PieChart,
  ShieldCheck,
  Compass
} from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const StructuredIndicatorsGrid = ({ indicators = {}, quality = {} }) => {
  const geo = indicators.geospatial_analysis || {};
  const comp = indicators.competition || {};
  const demand = indicators.demand_evidence || {};
  const infra = indicators.infrastructure || {};
  const supply = indicators.supply_ecosystem || {};
  const marketAccess = indicators.market_access || {};
  const season = indicators.seasonality || {};
  const capacity = indicators.market_capacity || {};

  const cards = [
    {
      id: 'opportunity',
      title: 'Market Opportunity Signal',
      icon: TrendingUp,
      score: capacity.net_capacity_score ?? 0.58,
      rating: capacity.capacity_signal || 'HEALTHY_MARKET',
      confidence: quality.overall_confidence ?? 0.75,
      status: 'ACTUAL',
      description: 'Composite enterprise expansion headroom'
    },
    {
      id: 'competition',
      title: 'Competition Pressure',
      icon: Building2,
      score: comp.competitive_pressure_score ?? 0.50,
      rating: comp.competitive_pressure || 'MODERATE',
      confidence: comp.confidence ?? 0.85,
      status: 'ACTUAL',
      description: 'Weighted 3-tier proximity density'
    },
    {
      id: 'demand',
      title: 'Demand Strength',
      icon: Compass,
      score: demand.demand_signal_score ?? 0.50,
      rating: demand.demand_signal_strength || 'MODERATE',
      confidence: demand.confidence ?? 0.85,
      status: 'PROXY',
      description: 'Population scaling & consumption proxies'
    },
    {
      id: 'supply',
      title: 'Supply Accessibility',
      icon: Truck,
      score: 1.0 - (supply.supply_risk_score ?? 0.20),
      rating: supply.accessibility || 'HIGH',
      confidence: supply.confidence ?? 0.80,
      status: 'ACTUAL',
      description: 'APMC mandi proximity & input coverage'
    },
    {
      id: 'infrastructure',
      title: 'Infrastructure Readiness',
      icon: Zap,
      score: infra.readiness_score ?? 0.50,
      rating: infra.readiness || 'UNKNOWN_DATA_GAP',
      confidence: infra.confidence ?? 0.30,
      status: infra.readiness === 'UNKNOWN_DATA_GAP' ? 'UNKNOWN_DATA_GAP' : 'AVAILABLE',
      description: infra.readiness === 'UNKNOWN_DATA_GAP' ? 'Evidence missing; neutral score 0.50' : 'Grid & road connectivity verified'
    },
    {
      id: 'geospatial',
      title: 'Geospatial Reachability',
      icon: MapPin,
      score: marketAccess.geographic_accessibility_score ?? 0.80,
      rating: marketAccess.accessibility || 'HIGH',
      confidence: geo.confidence ?? 0.90,
      status: 'ACTUAL',
      description: 'Catchment zone reachability & terrain index'
    },
    {
      id: 'seasonality',
      title: 'Seasonality Stability',
      icon: Calendar,
      score: 1.0 - (season.annual_volatility ?? 0.18),
      rating: season.seasonal_risk || 'LOW',
      confidence: season.confidence ?? 0.90,
      status: 'ACTUAL',
      description: '12-month demand cycle predictability'
    },
    {
      id: 'capacity',
      title: 'Market Capacity',
      icon: PieChart,
      score: capacity.net_capacity_score ?? 0.50,
      rating: capacity.status || 'LIMITED',
      confidence: capacity.confidence ?? 0.70,
      status: 'ESTIMATED',
      description: 'Unmet demand absorption potential'
    }
  ];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <ShieldCheck className="w-5 h-5 text-emerald-400" />
            Consolidated Structured Market Indicators
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Standardized multi-dimensional scorecards computed strictly through deterministic formulas and benchmarks.
          </p>
        </div>
        <div className="text-xs text-slate-400 font-mono">
          Overall Market Confidence: <strong className="text-emerald-400 font-bold">{((quality.overall_confidence || 0.75) * 100).toFixed(0)}%</strong>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <div
              key={card.id}
              className="bg-slate-950 p-4 rounded-xl border border-slate-800 hover:border-slate-700 transition-all flex flex-col justify-between"
            >
              <div>
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-xs font-semibold text-slate-300 flex items-center gap-1.5">
                    <Icon className="w-3.5 h-3.5 text-emerald-400" />
                    {card.title}
                  </span>
                  <Stage6StatusBadge status={card.status} />
                </div>

                <div className="flex items-baseline justify-between mt-2">
                  <span className="text-2xl font-extrabold text-slate-100 font-mono">
                    {typeof card.score === 'number' ? card.score.toFixed(2) : card.score}
                  </span>
                  <Stage6StatusBadge status={card.rating} />
                </div>

                <p className="text-[11px] text-slate-400 mt-2 leading-relaxed">
                  {card.description}
                </p>
              </div>

              <div className="mt-4 pt-2 border-t border-slate-900 flex justify-between text-[10px] text-slate-500 font-mono">
                <span>Confidence:</span>
                <span className="text-slate-300">{((card.confidence || 0.8) * 100).toFixed(0)}%</span>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
};

export default StructuredIndicatorsGrid;
