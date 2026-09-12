import React, { useState } from 'react';
import { Cpu, Check, Copy, ArrowRight, Database, CheckCircle2 } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const MarketFeaturesHandoff = ({ marketFeatures = {}, nextStage = {} }) => {
  const [copied, setCopied] = useState(false);
  const [activeCategory, setActiveCategory] = useState('all');

  const categories = [
    { key: 'demographic_features', label: 'Demographics', data: marketFeatures.demographic_features || {} },
    { key: 'competition_features', label: 'Competition', data: marketFeatures.competition_features || {} },
    { key: 'demand_evidence_features', label: 'Demand Proxies', data: marketFeatures.demand_evidence_features || {} },
    { key: 'supply_features', label: 'Supply Chain', data: marketFeatures.supply_features || {} },
    { key: 'infrastructure_features', label: 'Infrastructure', data: marketFeatures.infrastructure_features || {} },
    { key: 'market_access_features', label: 'Spatial & Access', data: marketFeatures.market_access_features || {} },
    { key: 'seasonal_features', label: 'Seasonality', data: marketFeatures.seasonal_features || {} },
    { key: 'economic_features', label: 'Economic Benchmarks', data: marketFeatures.economic_features || {} },
    { key: 'business_features', label: 'Business Profile', data: marketFeatures.business_features || {} },
    { key: 'location_features', label: 'Location Context', data: marketFeatures.location_features || {} },
  ];

  const totalFeatures = categories.reduce((acc, cat) => acc + Object.keys(cat.data).length, 0);

  const handleCopy = () => {
    navigator.clipboard.writeText(JSON.stringify(marketFeatures, null, 2));
    setCopied(true);
    setTimeout(() => setCopied(false), 2000);
  };

  const filteredCategories = activeCategory === 'all'
    ? categories
    : categories.filter(c => c.key === activeCategory);

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Cpu className="w-5 h-5 text-indigo-400" />
              Stage 7 Machine Learning Feature Vector (`market_features`)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20 flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5" /> READY FOR STAGE 7 ML
            </span>
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Standardized 10-tier numerical feature contract generated strictly for Stage 7 Demand Prediction model ingestion.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <span className="text-xs text-slate-400 font-mono">Total Features:</span>
            <p className="text-sm font-bold text-cyan-400 font-mono">{totalFeatures} Vector Dimensions</p>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 bg-slate-950 border border-slate-700 hover:bg-slate-800 text-slate-200 text-xs px-3 py-2 rounded-lg transition-colors font-mono"
          >
            {copied ? <Check className="w-4 h-4 text-emerald-400" /> : <Copy className="w-4 h-4 text-indigo-400" />}
            {copied ? 'Copied Vector' : 'Copy Features JSON'}
          </button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap gap-1.5 pb-2">
        <button
          onClick={() => setActiveCategory('all')}
          className={`px-3 py-1 rounded-lg text-xs font-medium transition-colors ${
            activeCategory === 'all'
              ? 'bg-indigo-600 text-white font-semibold'
              : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
          }`}
        >
          All Categories ({totalFeatures})
        </button>
        {categories.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-2.5 py-1 rounded-lg text-xs font-medium transition-colors ${
              activeCategory === cat.key
                ? 'bg-indigo-600 text-white font-semibold'
                : 'bg-slate-950 text-slate-400 hover:text-slate-200 border border-slate-800'
            }`}
          >
            {cat.label} ({Object.keys(cat.data).length})
          </button>
        ))}
      </div>

      {/* Feature Tiers Grid */}
      <div className="space-y-4">
        {filteredCategories.map((cat) => {
          const entries = Object.entries(cat.data);
          if (entries.length === 0) return null;
          return (
            <div key={cat.key} className="bg-slate-950 p-4 rounded-xl border border-slate-800 space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-indigo-300 uppercase tracking-wider font-mono">
                  {cat.label} Feature Set
                </span>
                <span className="text-[11px] font-mono text-slate-500">
                  {entries.length} dimensions
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {entries.map(([key, val]) => (
                  <div
                    key={key}
                    className="bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 flex flex-col justify-between text-xs"
                  >
                    <span className="text-[11px] font-mono text-slate-400 truncate" title={key}>
                      {key}
                    </span>
                    <div className="flex items-baseline justify-between mt-1.5 pt-1 border-t border-slate-800/80">
                      <span className="font-mono font-bold text-slate-100 text-sm">
                        {typeof val === 'number'
                          ? Number.isInteger(val)
                            ? val.toLocaleString('en-IN')
                            : val.toFixed(3)
                          : typeof val === 'boolean'
                          ? val ? 'TRUE' : 'FALSE'
                          : String(val || '—')}
                      </span>
                      <span className="text-[10px] font-mono text-slate-500 uppercase">
                        {typeof val}
                      </span>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          );
        })}
      </div>

      {/* Handoff Contract Note */}
      <div className="p-3.5 rounded-xl bg-indigo-950/30 border border-indigo-500/30 flex items-center justify-between text-xs text-indigo-200">
        <div className="flex items-center gap-2">
          <ArrowRight className="w-4 h-4 text-indigo-400 shrink-0" />
          <span>Handoff Target: <strong>Stage 7 Demand Prediction ML Model</strong> (Interface: <code>market_features</code>)</span>
        </div>
        <span className="font-mono text-indigo-300 bg-indigo-900/50 px-2 py-0.5 rounded border border-indigo-500/30">
          Status: STANDBY FOR ML CONNECTION
        </span>
      </div>
    </div>
  );
};

export default MarketFeaturesHandoff;
