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
    <div className="royal-panel rounded-2xl p-6 border border-[#79563F]/18 space-y-6 shadow-xs">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b border-[#79563F]/15 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Cpu className="w-5 h-5 text-[#006F5F]" />
              Synthesized Market Feature Vector (`market_features`)
            </h3>
            <span className="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-[#006F5F]/10 text-[#006F5F] border border-[#006F5F]/20 flex items-center gap-1 font-bold">
              <CheckCircle2 className="w-3.5 h-3.5" /> READY FOR PIPELINE
            </span>
          </div>
          <p className="text-xs text-[#62584F] mt-1">
            Standardized numerical feature contract generated for downstream pipeline stages.
          </p>
        </div>

        <div className="flex items-center gap-3">
          <div className="text-right hidden sm:block">
            <span className="text-xs text-[#79563F] font-mono">Total Features:</span>
            <p className="text-sm font-bold text-[#006F5F] font-mono">{totalFeatures} Vector Dimensions</p>
          </div>
          <button
            onClick={handleCopy}
            className="flex items-center gap-1.5 bg-[#FAF2E3] border border-[#79563F]/20 hover:bg-[#F1E4CC] text-[#28231F] text-xs px-3 py-2 rounded-lg transition-colors font-mono font-bold shadow-2xs"
          >
            {copied ? <Check className="w-4 h-4 text-[#006F5F]" /> : <Copy className="w-4 h-4 text-[#79563F]" />}
            {copied ? 'Copied Vector' : 'Copy Features JSON'}
          </button>
        </div>
      </div>

      {/* Category Filter Pills */}
      <div className="flex flex-wrap gap-1.5 pb-2">
        <button
          onClick={() => setActiveCategory('all')}
          className={`px-3 py-1 rounded-lg text-xs font-semibold transition-colors ${
            activeCategory === 'all'
              ? 'bg-[#006F5F] text-white'
              : 'bg-[#FAF2E3] text-[#62584F] hover:text-[#28231F] border border-[#79563F]/18'
          }`}
        >
          All Categories ({totalFeatures})
        </button>
        {categories.map((cat) => (
          <button
            key={cat.key}
            onClick={() => setActiveCategory(cat.key)}
            className={`px-2.5 py-1 rounded-lg text-xs font-semibold transition-colors ${
              activeCategory === cat.key
                ? 'bg-[#006F5F] text-white'
                : 'bg-[#FAF2E3] text-[#62584F] hover:text-[#28231F] border border-[#79563F]/18'
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
            <div key={cat.key} className="bg-[#FAF2E3] p-4 rounded-xl border border-[#79563F]/18 space-y-3 shadow-2xs">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-[#006F5F] uppercase tracking-wider font-mono">
                  {cat.label} Feature Set
                </span>
                <span className="text-[11px] font-mono text-[#79563F]">
                  {entries.length} dimensions
                </span>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-2.5">
                {entries.map(([key, val]) => (
                  <div
                    key={key}
                    className="bg-[#F1E4CC] p-2.5 rounded-lg border border-[#79563F]/15 flex flex-col justify-between text-xs"
                  >
                    <span className="text-[11px] font-mono text-[#62584F] truncate" title={key}>
                      {key}
                    </span>
                    <div className="flex items-baseline justify-between mt-1.5 pt-1 border-t border-[#79563F]/15">
                      <span className="font-mono font-bold text-[#28231F] text-sm">
                        {typeof val === 'number'
                          ? Number.isInteger(val)
                            ? val.toLocaleString('en-IN')
                            : val.toFixed(3)
                          : typeof val === 'boolean'
                          ? val ? 'TRUE' : 'FALSE'
                          : String(val || '—')}
                      </span>
                      <span className="text-[10px] font-mono text-[#79563F] uppercase">
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
      <div className="p-3.5 rounded-xl bg-[#FAF2E3] border border-[#006F5F]/30 flex items-center justify-between text-xs text-[#006F5F] shadow-2xs">
        <div className="flex items-center gap-2">
          <ArrowRight className="w-4 h-4 text-[#006F5F] shrink-0" />
          <span>Handoff Target: <strong>Opportunity Evaluation & Financial Modeling</strong> (Interface: <code>market_features</code>)</span>
        </div>
        <span className="font-mono text-[#006F5F] bg-[#006F5F]/10 px-2 py-0.5 rounded border border-[#006F5F]/20 font-bold">
          Status: READY
        </span>
      </div>
    </div>
  );
};

export default MarketFeaturesHandoff;
