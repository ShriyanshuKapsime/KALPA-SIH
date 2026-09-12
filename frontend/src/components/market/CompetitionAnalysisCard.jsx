import React from 'react';
import { Building2, ShieldAlert, Activity, Award, Scale, HelpCircle } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const CompetitionAnalysisCard = ({ competition = {}, provenance = [] }) => {
  const direct = competition.direct || { items: [] };
  const adjacent = competition.adjacent || { items: [] };
  const substitute = competition.substitute || { items: [] };

  const pressureScore = competition.competitive_pressure_score ?? 0.50;
  const pressureLevel = competition.competitive_pressure || 'MODERATE';
  const totalComps = competition.total_competitors || (direct.count + adjacent.count + substitute.count) || 0;
  const density = competition.competition_density_per_10k ?? 0.0;
  const drivers = competition.drivers || [];

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Building2 className="w-5 h-5 text-emerald-400" />
              Multi-Tier Competition Analysis
            </h3>
            <Stage6StatusBadge status={pressureLevel} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic 3-tier competitive pressure modeling with distance inverse-square decay. Zero LLM estimations.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Competitive Pressure Index:</span>
          <p className="text-xl font-bold text-emerald-400 font-mono">
            {pressureScore.toFixed(2)} <span className="text-xs font-normal text-slate-400">/ 1.00</span>
          </p>
        </div>
      </div>

      {/* Summary Scorecards Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        {/* Direct Tier */}
        <div className="bg-slate-950 p-4 rounded-xl border border-emerald-500/20">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-emerald-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-emerald-400" /> Direct Competitors
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-emerald-500/10 text-emerald-300">
              Weight: 1.0x
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-1">
            {direct.count ?? direct.items?.length ?? 0}
            <span className="text-xs font-normal text-slate-400 ml-2">
              ({(direct.proximity_weighted_count ?? 0).toFixed(2)} weighted)
            </span>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Same product/service category in immediate catchment
          </p>
        </div>

        {/* Adjacent Tier */}
        <div className="bg-slate-950 p-4 rounded-xl border border-cyan-500/20">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-cyan-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-cyan-400" /> Adjacent Competitors
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-300">
              Weight: 0.5x
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-1">
            {adjacent.count ?? adjacent.items?.length ?? 0}
            <span className="text-xs font-normal text-slate-400 ml-2">
              ({(adjacent.proximity_weighted_count ?? 0).toFixed(2)} weighted)
            </span>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Overlapping customer base or multi-trade rural hubs
          </p>
        </div>

        {/* Substitute Tier */}
        <div className="bg-slate-950 p-4 rounded-xl border border-amber-500/20">
          <div className="flex justify-between items-center mb-1">
            <span className="text-xs font-bold text-amber-400 flex items-center gap-1.5">
              <span className="w-2 h-2 rounded-full bg-amber-400" /> Substitute Channels
            </span>
            <span className="text-[10px] font-mono px-2 py-0.5 rounded bg-amber-500/10 text-amber-300">
              Weight: 0.25x
            </span>
          </div>
          <p className="text-2xl font-bold text-slate-100 mt-1">
            {substitute.count ?? substitute.items?.length ?? 0}
            <span className="text-xs font-normal text-slate-400 ml-2">
              ({(substitute.proximity_weighted_count ?? 0).toFixed(2)} weighted)
            </span>
          </p>
          <p className="text-xs text-slate-400 mt-1">
            Alternative consumption channels & weekly haats
          </p>
        </div>
      </div>

      {/* Drivers & Density Indicators */}
      <div className="bg-slate-950/70 p-4 rounded-xl border border-slate-800 flex flex-wrap items-center justify-between gap-4 text-xs">
        <div className="flex items-center gap-2">
          <Scale className="w-4 h-4 text-indigo-400" />
          <span className="text-slate-400">Competition Density:</span>
          <strong className="text-slate-200 font-mono">{density.toFixed(2)} / 10k population</strong>
        </div>
        <div className="flex items-center gap-2">
          <Activity className="w-4 h-4 text-emerald-400" />
          <span className="text-slate-400">Saturation Threshold:</span>
          <strong className="text-slate-200 font-mono">{competition.saturation_threshold || '1.20'}</strong>
        </div>
        {drivers.length > 0 && (
          <div className="w-full pt-2 border-t border-slate-900 flex flex-wrap items-center gap-2">
            <span className="text-slate-400 font-medium">Primary Drivers:</span>
            {drivers.map((d, i) => (
              <span key={i} className="bg-slate-900 px-2 py-0.5 rounded text-slate-300 border border-slate-800">
                {d}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Individual Competitor Items Tables / Lists */}
      <div className="space-y-4">
        {/* Direct Competitors List */}
        <div>
          <h4 className="text-xs font-bold text-emerald-400 uppercase tracking-wider mb-2">
            Direct Competitors in Catchment ({direct.items?.length || 0})
          </h4>
          {(!direct.items || direct.items.length === 0) ? (
            <div className="p-3 bg-slate-950 rounded-lg border border-slate-800 text-xs text-slate-400">
              Zero direct competitors identified in MSME/UDYAM registry within 15 km primary catchment.
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
              {direct.items.map((c, i) => {
                const dist = c.distance_km || 0.0;
                const decay = 1 / (1 + 0.1 * dist);
                const contribution = 1.0 * decay;
                return (
                  <div key={i} className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex justify-between items-center text-xs">
                    <div>
                      <div className="flex items-center gap-2">
                        <p className="font-semibold text-slate-200">{c.business_name}</p>
                        <Stage6StatusBadge status={c.is_proxy ? 'PROXY' : 'ACTUAL'} />
                      </div>
                      <p className="text-slate-400 text-[11px] mt-0.5">Category: {c.category || 'Direct Niche'}</p>
                    </div>
                    <div className="text-right shrink-0">
                      <span className="text-emerald-400 font-mono font-bold">{dist.toFixed(1)} km</span>
                      <p className="text-[10px] text-slate-500 font-mono">Contrib: {contribution.toFixed(2)}</p>
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Adjacent & Substitute Lists */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-2">
          {/* Adjacent */}
          <div>
            <h4 className="text-xs font-bold text-cyan-400 uppercase tracking-wider mb-2">
              Adjacent Competitors ({adjacent.items?.length || 0})
            </h4>
            <div className="space-y-1.5">
              {(adjacent.items || []).map((c, i) => (
                <div key={i} className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 flex justify-between items-center text-xs">
                  <span className="text-slate-300 font-medium truncate max-w-[200px]">{c.business_name}</span>
                  <span className="text-cyan-400 font-mono text-[11px]">{c.distance_km} km</span>
                </div>
              ))}
            </div>
          </div>

          {/* Substitute */}
          <div>
            <h4 className="text-xs font-bold text-amber-400 uppercase tracking-wider mb-2">
              Substitute Channels ({substitute.items?.length || 0})
            </h4>
            <div className="space-y-1.5">
              {(substitute.items || []).map((c, i) => (
                <div key={i} className="bg-slate-950/70 p-2.5 rounded-lg border border-slate-800/80 flex justify-between items-center text-xs">
                  <span className="text-slate-300 font-medium truncate max-w-[200px]">{c.business_name}</span>
                  <span className="text-amber-400 font-mono text-[11px]">{c.distance_km} km</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Calculation Provenance Box */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="weighted_competitive_pressure"
        title="Competition Pressure Provenance"
      />
    </div>
  );
};

export default CompetitionAnalysisCard;
