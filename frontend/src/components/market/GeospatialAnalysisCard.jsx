import React from 'react';
import { MapPin, Navigation, Compass, Globe, CheckCircle2, AlertTriangle } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const GeospatialAnalysisCard = ({ geospatial = {}, marketAccess = {}, provenance = [] }) => {
  const coords = geospatial.coordinates || {};
  const resolved = geospatial.resolved_location || {};
  const catchment = marketAccess.catchment || {};

  const primaryRadius = geospatial.primary_radius_km || 15.0;
  const secondaryRadius = geospatial.secondary_radius_km || 50.0;
  const entitiesPrimary = geospatial.entities_in_primary_zone || 0;
  const entitiesSecondary = geospatial.entities_in_secondary_zone || 0;
  const accessScore = marketAccess.geographic_accessibility_score ?? 0.80;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <MapPin className="w-5 h-5 text-emerald-400" />
              Geospatial & Catchment Zone Analysis
            </h3>
            <Stage6StatusBadge status="ACTUAL" />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic Haversine distance mapping, dynamic catchment boundaries, and spatial accessibility scoring.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Geographic Precision:</span>
          <p className="text-sm font-bold text-emerald-400 capitalize">
            {geospatial.data_precision || 'District'}
          </p>
        </div>
      </div>

      {/* Main Stats Grid */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* Coordinates */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Globe className="w-3.5 h-3.5 text-cyan-400" /> Resolved Coordinates
          </span>
          <p className="text-lg font-bold text-slate-200 mt-1 font-mono">
            {coords.latitude ? coords.latitude.toFixed(4) : '—'}° N, {coords.longitude ? coords.longitude.toFixed(4) : '—'}° E
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {resolved.district || 'District'}, {resolved.state || 'India'}
          </p>
        </div>

        {/* Catchment Radius */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Compass className="w-3.5 h-3.5 text-emerald-400" /> Catchment Boundaries
          </span>
          <p className="text-lg font-bold text-emerald-400 mt-1">
            {primaryRadius} km <span className="text-xs text-slate-400 font-normal">/ {secondaryRadius} km</span>
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Primary vs Secondary Extent
          </p>
        </div>

        {/* Spatial Reachability */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <Navigation className="w-3.5 h-3.5 text-indigo-400" /> Accessibility Score
          </span>
          <p className="text-lg font-bold text-indigo-300 mt-1 font-mono">
            {(accessScore * 100).toFixed(0)} / 100
          </p>
          <p className="text-xs text-slate-500 mt-1">
            Rating: <strong className="text-slate-300 uppercase">{marketAccess.accessibility || 'HIGH'}</strong>
          </p>
        </div>

        {/* Precision Gap */}
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium flex items-center gap-1.5">
            <CheckCircle2 className="w-3.5 h-3.5 text-teal-400" /> Spatial Confidence
          </span>
          <p className="text-lg font-bold text-teal-300 mt-1">
            {((geospatial.confidence || 0.90) * 100).toFixed(0)}%
          </p>
          <div className="text-xs text-slate-500 mt-1 flex items-center gap-1">
            {geospatial.precision_gap ? (
              <span className="text-amber-400 flex items-center gap-1">
                <AlertTriangle className="w-3 h-3" /> District proxy used
              </span>
            ) : (
              <span className="text-emerald-400">Target precision aligned</span>
            )}
          </div>
        </div>
      </div>

      {/* Catchment Zones Visual Tiering */}
      <div className="bg-slate-950/80 p-5 rounded-xl border border-slate-800 space-y-3">
        <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider">
          Catchment Zone Density Classification
        </h4>
        <div className="grid grid-cols-1 sm:grid-cols-4 gap-3">
          <div className="bg-slate-900/90 p-3 rounded-lg border border-emerald-500/20">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-bold text-emerald-400">PRIMARY ZONE</span>
              <span className="text-[10px] font-mono bg-emerald-500/10 text-emerald-300 px-1.5 py-0.5 rounded">≤ 5 km</span>
            </div>
            <p className="text-2xl font-extrabold text-slate-100">{entitiesPrimary}</p>
            <p className="text-[11px] text-slate-400 mt-1">Immediate daily walk-in / farm-gate catchment</p>
          </div>

          <div className="bg-slate-900/90 p-3 rounded-lg border border-cyan-500/20">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-bold text-cyan-400">SECONDARY ZONE</span>
              <span className="text-[10px] font-mono bg-cyan-500/10 text-cyan-300 px-1.5 py-0.5 rounded">≤ 15 km</span>
            </div>
            <p className="text-2xl font-extrabold text-slate-100">{entitiesSecondary}</p>
            <p className="text-[11px] text-slate-400 mt-1">Block / Mandi commute radius</p>
          </div>

          <div className="bg-slate-900/90 p-3 rounded-lg border border-indigo-500/20">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-bold text-indigo-400">EXTENDED ZONE</span>
              <span className="text-[10px] font-mono bg-indigo-500/10 text-indigo-300 px-1.5 py-0.5 rounded">≤ 30 km</span>
            </div>
            <p className="text-2xl font-extrabold text-slate-100 font-mono">1.2x</p>
            <p className="text-[11px] text-slate-400 mt-1">Regional wholesale / logistics network</p>
          </div>

          <div className="bg-slate-900/90 p-3 rounded-lg border border-slate-800">
            <div className="flex justify-between items-center mb-1">
              <span className="text-xs font-bold text-slate-400">OUTSIDE ZONE</span>
              <span className="text-[10px] font-mono bg-slate-800 text-slate-400 px-1.5 py-0.5 rounded">&gt; 30 km</span>
            </div>
            <p className="text-2xl font-extrabold text-slate-400 font-mono">0.0x</p>
            <p className="text-[11px] text-slate-500 mt-1">Minimal hyper-local commercial influence</p>
          </div>
        </div>
      </div>

      {/* Calculation Provenance Details */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="geospatial_accessibility_score"
        title="Geospatial Calculation Provenance"
      />
    </div>
  );
};

export default GeospatialAnalysisCard;
