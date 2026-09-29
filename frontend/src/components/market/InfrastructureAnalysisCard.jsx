import React from 'react';
import { Zap, HelpCircle } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const InfrastructureAnalysisCard = ({ infrastructure = {} }) => {
  const readiness = infrastructure.readiness || 'LIMITED';
  const readinessScore = infrastructure.readiness_score ?? 0.50;
  const confidence = infrastructure.confidence ?? 0.30;
  const requirements = infrastructure.requirements || [];

  const isUnknownGap = readiness === 'UNKNOWN_DATA_GAP' || requirements.every(r => r.status === 'UNKNOWN');

  return (
    <div className="royal-panel rounded-2xl p-5 sm:p-6 border border-[#79563F]/18 space-y-4 shadow-xs h-auto w-full">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-[#79563F]/15 pb-3">
        <div>
          <div className="flex items-center gap-2 flex-wrap">
            <h3 className="text-base sm:text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
              <Zap className="w-4 h-4 text-[#79563F]" />
              Infrastructure &amp; Utility Readiness
            </h3>
            <Stage6StatusBadge status={readiness} />
          </div>
          <p className="text-xs text-[#62584F] mt-0.5">
            Local power grid, road connectivity, and utility requirement matching.
          </p>
        </div>
        <div className="text-left sm:text-right shrink-0">
          <span className="text-[11px] text-[#79563F] font-mono">Readiness: </span>
          <span className="text-base font-bold text-[#28231F] font-mono">
            {readinessScore.toFixed(2)}
            <span className="text-[11px] font-normal text-[#62584F]"> / 1.00</span>
          </span>
        </div>
      </div>

      {/* Subtle Missing Evidence Notice */}
      {isUnknownGap && (
        <div className="bg-[#FAF2E3]/90 border border-[#79563F]/15 rounded-xl p-2.5 flex items-start gap-2 text-xs">
          <HelpCircle className="w-3.5 h-3.5 text-[#79563F] shrink-0 mt-0.5" />
          <div className="space-y-0.5">
            <p className="font-semibold text-[#28231F] text-xs">
              Evidence verification required during field survey
            </p>
            <p className="text-[#62584F] text-[10px] leading-relaxed">
              Open spatial registries have limited local utility data for power grid and road connectivity. Baseline score of 0.50 applied ({((confidence || 0.35) * 100).toFixed(0)}% calibrated confidence).
            </p>
          </div>
        </div>
      )}

      {/* Summary Indicators Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5">
        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium">Readiness Level</span>
          <div className="mt-1">
            <Stage6StatusBadge status={readiness} />
          </div>
          <p className="text-[10px] text-[#62584F] mt-1">
            {isUnknownGap ? 'Baseline estimate' : 'Empirical verification'}
          </p>
        </div>

        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium">Requirements Verified</span>
          <p className="text-lg font-bold text-[#28231F] mt-0.5 font-mono">
            {infrastructure.satisfied_requirements_count || 0} / {requirements.length || 0}
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            {requirements.length - (infrastructure.satisfied_requirements_count || 0)} pending confirmation
          </p>
        </div>

        <div className="bg-[#FAF2E3]/90 p-3 rounded-xl border border-[#79563F]/12">
          <span className="text-[11px] text-[#79563F] font-medium">Evidence Confidence</span>
          <p className={`text-lg font-bold mt-0.5 font-mono ${confidence <= 0.35 ? 'text-[#79563F]' : 'text-[#006F5F]'}`}>
            {(confidence * 100).toFixed(0)}%
          </p>
          <p className="text-[10px] text-[#62584F] mt-0.5">
            {confidence <= 0.35 ? 'Calibrated baseline' : 'Open data verified'}
          </p>
        </div>
      </div>

      {/* Requirements List */}
      {requirements.length > 0 && (
        <div>
          <h4 className="text-[10px] font-bold text-[#28231F] uppercase tracking-wider mb-1.5">
            Domain Infrastructure Checklist ({requirements.length})
          </h4>
          <div className="space-y-1">
            {requirements.map((req, idx) => (
              <div
                key={idx}
                className="bg-[#FAF2E3]/90 px-2.5 py-1.5 rounded-lg border border-[#79563F]/12 flex flex-col sm:flex-row sm:items-center justify-between gap-1 text-xs"
              >
                <div className="truncate pr-2">
                  <span className="font-semibold text-[#28231F] text-xs">{req.requirement}</span>
                  <p className="text-[#62584F] text-[10px] truncate">
                    {req.evidence_detail || 'Field verification recommended'}
                  </p>
                </div>

                <div className="flex items-center gap-2 shrink-0 text-[10px]">
                  <span className="text-[#79563F]">
                    Impact: <strong className="text-[#28231F]">{req.impact || 'HIGH'}</strong>
                  </span>
                  <span className={`font-mono px-1.5 py-0.5 rounded text-[9px] font-bold ${
                    req.evidence_available ? 'bg-[#006F5F]/10 text-[#006F5F]' : 'bg-[#79563F]/10 text-[#62584F]'
                  }`}>
                    {req.evidence_available ? 'Verified' : 'Unconfirmed'}
                  </span>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default InfrastructureAnalysisCard;
