import React from 'react';
import { Building2, Scale, Activity } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const CompetitionAnalysisCard = ({ competition = {} }) => {
  const direct = competition.direct || { items: [] };
  const adjacent = competition.adjacent || { items: [] };
  const substitute = competition.substitute || { items: [] };

  const pressureScore = competition.competitive_pressure_score ?? 0.50;
  const pressureLevel = competition.competitive_pressure || 'MODERATE';
  const density = competition.competition_density_per_10k ?? 0.0;
  const drivers = competition.drivers || [];

  const directCount = direct.count ?? direct.items?.length ?? 0;
  const adjacentCount = adjacent.count ?? adjacent.items?.length ?? 0;
  const substituteCount = substitute.count ?? substitute.items?.length ?? 0;

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Building2 className="w-4 h-4 text-[#006F5F]" />
              Multi-Tier Competition Analysis
            </h3>
            <Stage6StatusBadge status={pressureLevel} />
          </div>
          <p className="text-xs text-[#62584F] mt-0.5">
            Proximity-weighted competitive pressure across local trade catchment.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Pressure Index: </span>
          <span className="text-base font-bold text-[#28231F] font-mono">
            {pressureScore.toFixed(2)}
            <span className="text-[11px] font-normal text-[#62584F]"> / 1.00</span>
          </span>
        </div>
      </div>

      {/* 3-Tier Summary Row */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        {/* Direct Tier */}
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#006F5F]/20">
          <div className="flex justify-between items-center mb-0.5">
            <span className="text-[11px] font-bold text-[#006F5F] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#006F5F]" /> Direct
            </span>
            <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-[#006F5F]/10 text-[#006F5F] font-bold">
              1.0x wt
            </span>
          </div>
          <p className="text-lg font-bold text-[#28231F] font-mono mt-0.5">
            {directCount}
            <span className="text-[10px] font-normal text-[#62584F] ml-1">
              ({(direct.proximity_weighted_count ?? directCount).toFixed(1)} wt)
            </span>
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Primary zone competitors
          </p>
        </div>

        {/* Adjacent Tier */}
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/20">
          <div className="flex justify-between items-center mb-0.5">
            <span className="text-[11px] font-bold text-[#79563F] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#79563F]" /> Adjacent
            </span>
            <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-[#79563F]/10 text-[#79563F] font-bold">
              0.5x wt
            </span>
          </div>
          <p className="text-lg font-bold text-[#28231F] font-mono mt-0.5">
            {adjacentCount}
            <span className="text-[10px] font-normal text-[#62584F] ml-1">
              ({(adjacent.proximity_weighted_count ?? adjacentCount).toFixed(1)} wt)
            </span>
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Multi-trade overlap hubs
          </p>
        </div>

        {/* Substitute Tier */}
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#C96A3A]/20">
          <div className="flex justify-between items-center mb-0.5">
            <span className="text-[11px] font-bold text-[#C96A3A] flex items-center gap-1">
              <span className="w-1.5 h-1.5 rounded-full bg-[#C96A3A]" /> Substitute
            </span>
            <span className="text-[9px] font-mono px-1 py-0.5 rounded bg-[#C96A3A]/10 text-[#C96A3A] font-bold">
              0.25x wt
            </span>
          </div>
          <p className="text-lg font-bold text-[#28231F] font-mono mt-0.5">
            {substituteCount}
            <span className="text-[10px] font-normal text-[#62584F] ml-1">
              ({(substitute.proximity_weighted_count ?? substituteCount).toFixed(1)} wt)
            </span>
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Alternative &amp; weekly haats
          </p>
        </div>
      </div>

      {/* Density & Saturation Strip */}
      <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12 flex flex-wrap items-center justify-between gap-2 text-xs">
        <div className="flex items-center gap-1.5">
          <Scale className="w-3.5 h-3.5 text-[#79563F]" />
          <span className="text-[#62584F] text-[11px]">Density:</span>
          <strong className="text-[#28231F] font-mono text-[11px]">{density.toFixed(2)} / 10k pop</strong>
        </div>
        <div className="flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-[#006F5F]" />
          <span className="text-[#62584F] text-[11px]">Saturation Threshold:</span>
          <strong className="text-[#28231F] font-mono text-[11px]">{competition.saturation_threshold || '1.20'}</strong>
        </div>
        {drivers.length > 0 && (
          <div className="w-full pt-1.5 border-t border-[#79563F]/10 flex flex-wrap items-center gap-1">
            <span className="text-[10px] text-[#79563F] font-medium">Key Drivers:</span>
            {drivers.map((d, i) => (
              <span key={i} className="bg-[#F1E4CC]/80 px-1.5 py-0.5 rounded text-[10px] text-[#28231F] border border-[#79563F]/12">
                {d}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Competitor Listings */}
      <div className="space-y-2.5">
        {/* Direct Competitors */}
        <div>
          <h4 className="text-[11px] font-bold text-[#006F5F] uppercase tracking-wider mb-1.5">
            Direct Competitors in Catchment ({direct.items?.length || 0})
          </h4>
          {(!direct.items || direct.items.length === 0) ? (
            <div className="p-2.5 bg-[#FAF2E3]/90 rounded-lg border border-[#79563F]/12 text-xs text-[#62584F]">
              Zero direct competitors identified in MSME/UDYAM registry within 15 km primary catchment.
            </div>
          ) : (
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-1.5">
              {direct.items.map((c, i) => {
                const dist = c.distance_km || 0.0;
                const decay = 1 / (1 + 0.1 * dist);
                const contribution = 1.0 * decay;
                return (
                  <div key={i} className="bg-[#FAF2E3]/90 p-2 rounded-lg border border-[#79563F]/12 flex justify-between items-center text-xs">
                    <div className="truncate pr-2">
                      <p className="font-semibold text-[#28231F] text-xs truncate">{c.business_name}</p>
                      <p className="text-[#62584F] text-[10px] truncate">{c.category || 'Direct Niche'}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-[#006F5F] font-mono font-bold text-xs">{dist.toFixed(1)} km</span>
                      <p className="text-[9px] text-[#79563F] font-mono">wt: {contribution.toFixed(2)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Adjacent & Substitute Compact Rows */}
        {(adjacent.items?.length > 0 || substitute.items?.length > 0) && (
          <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-0.5">
            {/* Adjacent */}
            <div>
              <h4 className="text-[10px] font-bold text-[#79563F] uppercase tracking-wider mb-1">
                Adjacent ({adjacent.items?.length || 0})
              </h4>
              <div className="space-y-1">
                {(adjacent.items || []).slice(0, 3).map((c, i) => (
                  <div key={i} className="bg-[#FAF2E3]/90 px-2 py-1 rounded-lg border border-[#79563F]/12 flex justify-between items-center text-xs">
                    <span className="text-[#28231F] font-medium truncate max-w-[160px] text-[11px]">{c.business_name}</span>
                    <span className="text-[#79563F] font-mono text-[10px] font-bold shrink-0">{c.distance_km} km</span>
                  </div>
                ))}
              </div>
            </div>

            {/* Substitute */}
            <div>
              <h4 className="text-[10px] font-bold text-[#C96A3A] uppercase tracking-wider mb-1">
                Substitute ({substitute.items?.length || 0})
              </h4>
              <div className="space-y-1">
                {(substitute.items || []).slice(0, 3).map((c, i) => (
                  <div key={i} className="bg-[#FAF2E3]/90 px-2 py-1 rounded-lg border border-[#79563F]/12 flex justify-between items-center text-xs">
                    <span className="text-[#28231F] font-medium truncate max-w-[160px] text-[11px]">{c.business_name}</span>
                    <span className="text-[#C96A3A] font-mono text-[10px] font-bold shrink-0">{c.distance_km} km</span>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default CompetitionAnalysisCard;
