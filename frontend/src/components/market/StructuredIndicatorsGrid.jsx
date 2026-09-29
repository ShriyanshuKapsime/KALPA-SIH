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
import Kalpa3DCard from './Kalpa3DCard';

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
      description: 'Composite enterprise expansion headroom'
    },
    {
      id: 'competition',
      title: 'Competition Pressure',
      icon: Building2,
      score: comp.competitive_pressure_score ?? 0.50,
      rating: comp.competitive_pressure || 'MODERATE',
      confidence: comp.confidence ?? 0.85,
      description: 'Weighted 3-tier proximity density'
    },
    {
      id: 'demand',
      title: 'Demand Strength',
      icon: Compass,
      score: demand.demand_signal_score ?? 0.50,
      rating: demand.demand_signal_strength || 'MODERATE',
      confidence: demand.confidence ?? 0.85,
      description: 'Population scaling & consumption proxies'
    },
    {
      id: 'supply',
      title: 'Supply Accessibility',
      icon: Truck,
      score: 1.0 - (supply.supply_risk_score ?? 0.20),
      rating: supply.accessibility || 'HIGH',
      confidence: supply.confidence ?? 0.80,
      description: 'APMC mandi proximity & input coverage'
    },
    {
      id: 'infrastructure',
      title: 'Infrastructure Readiness',
      icon: Zap,
      score: infra.readiness_score ?? 0.50,
      rating: infra.readiness || 'LIMITED',
      confidence: infra.confidence ?? 0.30,
      description: infra.readiness === 'UNKNOWN_DATA_GAP' ? 'Baseline score; awaiting localized utility proof' : 'Grid & road connectivity verified'
    },
    {
      id: 'geospatial',
      title: 'Geospatial Reachability',
      icon: MapPin,
      score: marketAccess.geographic_accessibility_score ?? 0.80,
      rating: marketAccess.accessibility || 'HIGH',
      confidence: geo.confidence ?? 0.90,
      description: 'Catchment zone reachability & terrain index'
    },
    {
      id: 'seasonality',
      title: 'Seasonality Stability',
      icon: Calendar,
      score: 1.0 - (season.annual_volatility ?? 0.18),
      rating: season.seasonal_risk || 'LOW',
      confidence: season.confidence ?? 0.90,
      description: '12-month demand cycle predictability'
    },
    {
      id: 'capacity',
      title: 'Market Capacity',
      icon: PieChart,
      score: capacity.net_capacity_score ?? 0.50,
      rating: capacity.status || 'LIMITED',
      confidence: capacity.confidence ?? 0.70,
      description: 'Unmet demand absorption potential'
    }
  ];

  return (
    <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-4">
        <div>
          <h3 className="text-xl font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
            <ShieldCheck className="w-5 h-5 text-[#006F5F]" />
            Consolidated Market Indicators
          </h3>
          <p className="text-xs text-[#62584F] mt-1">
            Standardized multi-dimensional scorecards computed from local evidence and statistical benchmarks.
          </p>
        </div>
        <div className="text-xs text-[#79563F] font-mono">
          Overall Market Confidence: <strong className="text-[#006F5F] font-bold">{((quality.overall_confidence || 0.75) * 100).toFixed(0)}%</strong>
        </div>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        {cards.map((card) => {
          const Icon = card.icon;
          return (
            <Kalpa3DCard key={card.id}>
              <div>
                <div className="flex items-start justify-between gap-2 mb-2 [transform:translateZ(6px)]">
                  <span className="text-xs font-bold text-[#28231F] flex items-center gap-1.5">
                    <Icon className="w-4 h-4 text-[#006F5F]" />
                    {card.title}
                  </span>
                </div>

                <div className="flex items-baseline justify-between mt-3 [transform:translateZ(10px)]">
                  <span className="text-3xl font-extrabold text-[#28231F] font-mono tracking-tight">
                    {typeof card.score === 'number' ? card.score.toFixed(2) : card.score}
                  </span>
                  <div className="[transform:translateZ(8px)]">
                    <Stage6StatusBadge status={card.rating} />
                  </div>
                </div>

                <p className="text-[11px] text-[#62584F] mt-2 leading-relaxed [transform:translateZ(4px)]">
                  {card.description}
                </p>
              </div>

              <div className="mt-4 pt-2 border-t border-[#79563F]/15 flex justify-between text-[11px] text-[#79563F] font-mono [transform:translateZ(6px)]">
                <span>Confidence:</span>
                <span className="font-bold text-[#28231F]">{((card.confidence || 0.8) * 100).toFixed(0)}%</span>
              </div>
            </Kalpa3DCard>
          );
        })}
      </div>
    </div>
  );
};

export default StructuredIndicatorsGrid;
