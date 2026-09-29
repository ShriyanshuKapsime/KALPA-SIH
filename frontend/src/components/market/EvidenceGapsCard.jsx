import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const EvidenceGapsCard = ({ evidenceGaps = [] }) => {
  return (
    <div className="royal-panel rounded-2xl p-6 border border-[#79563F]/18 space-y-4 shadow-xs">
      <div className="flex items-center justify-between border-b border-[#79563F]/15 pb-4">
        <div>
          <h3 className="text-lg font-bold text-[#28231F] flex items-center gap-2 font-['Outfit']">
            <AlertTriangle className="w-5 h-5 text-[#C96A3A]" />
            Evidence & Verification Tracking ({evidenceGaps.length})
          </h3>
          <p className="text-xs text-[#62584F] mt-1">
            Tracking indicators pending field proof or baseline calibration.
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-[#C96A3A]/10 text-[#C96A3A] border border-[#C96A3A]/25 font-bold">
          {evidenceGaps.length} Actionable {evidenceGaps.length === 1 ? 'Gap' : 'Gaps'}
        </span>
      </div>

      {evidenceGaps.length === 0 ? (
        <div className="p-4 rounded-xl bg-[#006F5F]/10 border border-[#006F5F]/20 text-[#006F5F] text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-[#006F5F] shrink-0" />
          <span>All domain requirements verified against local and statistical records.</span>
        </div>
      ) : (
        <div className="space-y-3">
          {evidenceGaps.map((gap, idx) => {
            const isCritical = gap.severity === 'CRITICAL' || gap.severity === 'HIGH';
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-start justify-between gap-3 text-xs shadow-2xs ${
                  isCritical
                    ? 'bg-[#FAF2E3] border-[#C96A3A]/30'
                    : 'bg-[#FAF2E3] border-[#79563F]/18'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-[#28231F] uppercase font-mono">{gap.category || gap.requirement}</span>
                    <Stage6StatusBadge status={gap.severity || 'WARNING'} />
                  </div>
                  <p className="text-[#62584F] text-xs">
                    {gap.description || gap.reason}
                  </p>
                  {gap.impact && (
                    <p className="text-[11px] text-[#79563F]">
                      Impact: {gap.impact}
                    </p>
                  )}
                </div>

                <div className="sm:text-right shrink-0 bg-[#F1E4CC] p-2.5 rounded-lg border border-[#79563F]/15 space-y-0.5">
                  <span className="text-[10px] uppercase font-bold text-[#79563F] block">Recommended Action:</span>
                  <p className="text-[#006F5F] font-medium text-[11px]">
                    {gap.recommended_action || 'Field surveyor intake or dynamic API pull'}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
};

export default EvidenceGapsCard;
