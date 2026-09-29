import React from 'react';
import { MapPin, Navigation, Compass, Globe, CheckCircle2 } from 'lucide-react';

export const GeospatialAnalysisCard = ({ geospatial = {}, marketAccess = {} }) => {
  const coords = geospatial.coordinates || {};
  const resolved = geospatial.resolved_location || {};

  const primaryRadius = geospatial.primary_radius_km || 15.0;
  const secondaryRadius = geospatial.secondary_radius_km || 50.0;
  const entitiesPrimary = geospatial.entities_in_primary_zone || 0;
  const entitiesSecondary = geospatial.entities_in_secondary_zone || 0;
  const accessScore = marketAccess.geographic_accessibility_score ?? 0.80;

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
            <MapPin className="w-4 h-4 text-[#006F5F]" />
            Geospatial &amp; Catchment Zone Analysis
          </h3>
          <p className="text-xs text-[#62584F] mt-0.5">
            Distance mapping, dynamic catchment boundaries, and spatial accessibility.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Precision: </span>
          <span className="text-xs font-bold text-[#006F5F] capitalize">
            {geospatial.data_precision || 'District'}
          </span>
        </div>
      </div>

      {/* Main 4 Stats Row */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
        {/* Coordinates */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium flex items-center gap-1">
            <Globe className="w-3 h-3 text-[#006F5F]" /> Coordinates
          </span>
          <p className="text-xs font-bold text-[#28231F] mt-1 font-mono">
            {coords.latitude ? coords.latitude.toFixed(2) : '—'}°N, {coords.longitude ? coords.longitude.toFixed(2) : '—'}°E
          </p>
          <p className="text-[10px] text-[#62584F] truncate mt-0.5">
            {resolved.district || 'District'}
          </p>
        </div>

        {/* Catchment Radius */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium flex items-center gap-1">
            <Compass className="w-3 h-3 text-[#006F5F]" /> Radius
          </span>
          <p className="text-xs font-bold text-[#006F5F] mt-1">
            {primaryRadius} km <span className="text-[10px] text-[#62584F] font-normal">/ {secondaryRadius} km</span>
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            Primary / Secondary
          </p>
        </div>

        {/* Spatial Reachability */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium flex items-center gap-1">
            <Navigation className="w-3 h-3 text-[#79563F]" /> Access
          </span>
          <p className="text-xs font-bold text-[#28231F] mt-1 font-mono">
            {(accessScore * 100).toFixed(0)} / 100
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5 uppercase font-semibold">
            {marketAccess.accessibility || 'HIGH'}
          </p>
        </div>

        {/* Spatial Confidence */}
        <div className="bg-[#FAF2E3]/90 p-2.5 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium flex items-center gap-1">
            <CheckCircle2 className="w-3 h-3 text-[#006F5F]" /> Confidence
          </span>
          <p className="text-xs font-bold text-[#006F5F] mt-1 font-mono">
            {((geospatial.confidence || 0.90) * 100).toFixed(0)}%
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5 truncate">
            {geospatial.precision_gap ? 'District proxy' : 'Target aligned'}
          </p>
        </div>
      </div>

      {/* Catchment Zones Visual Tiering */}
      <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12 space-y-1.5">
        <h4 className="text-[10px] font-bold text-[#28231F] uppercase tracking-wider">
          Catchment Zone Density Distribution
        </h4>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-1.5">
          <div className="bg-[#F1E4CC]/80 p-2 rounded-lg border border-[#006F5F]/20 text-center">
            <span className="text-[9px] font-bold text-[#006F5F] block">PRIMARY (≤5km)</span>
            <p className="text-base font-bold text-[#28231F] mt-0.5">{entitiesPrimary}</p>
            <p className="text-[9px] text-[#62584F]">Direct catchment</p>
          </div>

          <div className="bg-[#F1E4CC]/80 p-2 rounded-lg border border-[#79563F]/20 text-center">
            <span className="text-[9px] font-bold text-[#79563F] block">SECONDARY (≤15km)</span>
            <p className="text-base font-bold text-[#28231F] mt-0.5">{entitiesSecondary}</p>
            <p className="text-[9px] text-[#62584F]">Mandi radius</p>
          </div>

          <div className="bg-[#F1E4CC]/80 p-2 rounded-lg border border-[#79563F]/20 text-center">
            <span className="text-[9px] font-bold text-[#62584F] block">EXTENDED (≤30km)</span>
            <p className="text-base font-bold text-[#28231F] font-mono mt-0.5">1.2x</p>
            <p className="text-[9px] text-[#62584F]">Regional link</p>
          </div>

          <div className="bg-[#F1E4CC]/80 p-2 rounded-lg border border-[#79563F]/12 text-center">
            <span className="text-[9px] font-bold text-[#92745A] block">OUTSIDE (&gt;30km)</span>
            <p className="text-base font-bold text-[#92745A] font-mono mt-0.5">0.0x</p>
            <p className="text-[9px] text-[#92745A]">Minimal pull</p>
          </div>
        </div>
      </div>
    </div>
  );
};

export default GeospatialAnalysisCard;
