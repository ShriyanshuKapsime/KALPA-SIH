import React from 'react';
import { AlertTriangle, AlertCircle, CheckCircle2, ArrowRight } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';

export const EvidenceGapsCard = ({ evidenceGaps = [] }) => {
  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-4">
      <div className="flex items-center justify-between border-b border-slate-800 pb-4">
        <div>
          <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
            <AlertTriangle className="w-5 h-5 text-amber-400" />
            Structured Evidence Gaps & Uncertainty Tracking ({evidenceGaps.length})
          </h3>
          <p className="text-xs text-slate-400 mt-1">
            Complete transparency into unverified or proxy-dependent vectors. Never hidden from the entrepreneur.
          </p>
        </div>
        <span className="text-xs font-mono px-2.5 py-0.5 rounded-full bg-amber-500/10 text-amber-300 border border-amber-500/30">
          {evidenceGaps.length} Actionable {evidenceGaps.length === 1 ? 'Gap' : 'Gaps'}
        </span>
      </div>

      {evidenceGaps.length === 0 ? (
        <div className="p-4 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-300 text-xs flex items-center gap-2">
          <CheckCircle2 className="w-4 h-4 text-emerald-400 shrink-0" />
          <span>Zero empirical data gaps detected. All domain requirements fully verified.</span>
        </div>
      ) : (
        <div className="space-y-3">
          {evidenceGaps.map((gap, idx) => {
            const isCritical = gap.severity === 'CRITICAL' || gap.severity === 'HIGH';
            return (
              <div
                key={idx}
                className={`p-4 rounded-xl border flex flex-col sm:flex-row sm:items-start justify-between gap-3 text-xs ${
                  isCritical
                    ? 'bg-amber-500/10 border-amber-500/30'
                    : 'bg-slate-950 border-slate-800'
                }`}
              >
                <div className="space-y-1">
                  <div className="flex items-center gap-2">
                    <span className="font-bold text-slate-200 uppercase font-mono">{gap.category || gap.requirement}</span>
                    <Stage6StatusBadge status={gap.severity || 'WARNING'} />
                  </div>
                  <p className="text-slate-300 text-xs">
                    {gap.description || gap.reason}
                  </p>
                  {gap.impact && (
                    <p className="text-[11px] text-slate-400">
                      Impact: {gap.impact}
                    </p>
                  )}
                </div>

                <div className="sm:text-right shrink-0 bg-slate-900/90 p-2.5 rounded-lg border border-slate-800 space-y-0.5">
                  <span className="text-[10px] uppercase font-bold text-slate-400 block">Recommended Action:</span>
                  <p className="text-emerald-400 font-medium text-[11px]">
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
