import React from 'react';
import { Zap, AlertTriangle, CheckCircle2, HelpCircle, ShieldAlert, ArrowRight } from 'lucide-react';
import Stage6StatusBadge from './Stage6StatusBadge';
import CalculationProvenanceViewer from './CalculationProvenanceViewer';

export const InfrastructureAnalysisCard = ({ infrastructure = {}, provenance = [] }) => {
  const readiness = infrastructure.readiness || 'UNKNOWN_DATA_GAP';
  const readinessScore = infrastructure.readiness_score ?? 0.50;
  const confidence = infrastructure.confidence ?? 0.30;
  const requirements = infrastructure.requirements || [];
  const criticalGaps = infrastructure.critical_gaps || [];

  const isUnknownGap = readiness === 'UNKNOWN_DATA_GAP' || requirements.every(r => r.status === 'UNKNOWN');

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-2xl p-6 space-y-6">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-2 border-b border-slate-800 pb-4">
        <div>
          <div className="flex items-center gap-2">
            <h3 className="text-lg font-bold text-slate-100 flex items-center gap-2">
              <Zap className="w-5 h-5 text-amber-400" />
              Infrastructure & Utility Readiness Analysis
            </h3>
            <Stage6StatusBadge status={readiness} />
          </div>
          <p className="text-xs text-slate-400 mt-1">
            Deterministic domain requirement matching. Missing evidence is never assumed unavailable or zero.
          </p>
        </div>
        <div className="text-right">
          <span className="text-xs text-slate-400 font-mono">Readiness Score:</span>
          <p className="text-xl font-bold text-slate-100 font-mono">
            {readinessScore.toFixed(2)} <span className="text-xs font-normal text-slate-400">/ 1.00</span>
          </p>
        </div>
      </div>

      {/* Critical Missing Data Notice Banner */}
      {isUnknownGap && (
        <div className="bg-amber-500/10 border border-amber-500/30 rounded-xl p-4 flex items-start gap-3 text-xs">
          <ShieldAlert className="w-5 h-5 text-amber-400 shrink-0 mt-0.5" />
          <div className="space-y-1">
            <p className="font-bold text-amber-200 uppercase tracking-wide">
              Empirical Infrastructure Evidence Missing (Data Gap)
            </p>
            <p className="text-slate-300 leading-relaxed">
              No empirical infrastructure records were returned by Stage 5. Under KALPA's strict Zero-LLM integrity principles, this metric is assigned a neutral score of <strong>0.50</strong> and component confidence is capped at <strong>≤ 0.35</strong>.
            </p>
            <div className="pt-2 flex flex-wrap items-center gap-2 text-[11px] text-amber-300">
              <span>👉 <strong>Recommended Action:</strong> Field surveyor intake or dynamic PMGSY / DISCOM API integration.</span>
            </div>
          </div>
        </div>
      )}

      {/* Summary Indicators Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Readiness Classification</span>
          <div className="mt-1">
            <Stage6StatusBadge status={readiness} />
          </div>
          <p className="text-xs text-slate-500 mt-2">
            Status: {isUnknownGap ? 'Neutral Uncertainty' : 'Empirical Verification'}
          </p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Requirements Verified</span>
          <p className="text-xl font-bold text-slate-100 mt-1 font-mono">
            {infrastructure.satisfied_requirements_count || 0} / {requirements.length || 0}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {requirements.length - (infrastructure.satisfied_requirements_count || 0)} requirements pending field proof
          </p>
        </div>

        <div className="bg-slate-950 p-4 rounded-xl border border-slate-800">
          <span className="text-xs text-slate-400 font-medium">Infrastructure Confidence</span>
          <p className={`text-xl font-bold mt-1 font-mono ${confidence <= 0.35 ? 'text-amber-400' : 'text-emerald-400'}`}>
            {(confidence * 100).toFixed(0)}% {confidence <= 0.35 && <span className="text-xs font-normal text-amber-300">(Discounted)</span>}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {confidence <= 0.35 ? 'Capped due to data gap' : 'Verified from open data'}
          </p>
        </div>
      </div>

      {/* Requirements Table */}
      <div>
        <h4 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-3">
          Domain Infrastructure Requirements ({requirements.length})
        </h4>
        <div className="space-y-2">
          {requirements.map((req, idx) => (
            <div
              key={idx}
              className="bg-slate-950 p-3 rounded-lg border border-slate-800 flex flex-col sm:flex-row sm:items-center justify-between gap-2 text-xs"
            >
              <div className="space-y-0.5">
                <div className="flex items-center gap-2">
                  <span className="font-semibold text-slate-200">{req.requirement}</span>
                  <Stage6StatusBadge status={req.status || req.data_status || 'UNKNOWN'} />
                </div>
                <p className="text-slate-400 text-[11px]">
                  {req.evidence_detail || 'No empirical record in Stage 5 dataset'}
                </p>
              </div>

              <div className="flex items-center gap-3 shrink-0 text-[11px]">
                <span className="text-slate-500">
                  Impact: <strong className="text-slate-300">{req.impact || 'HIGH'}</strong>
                </span>
                <span className={`font-mono px-2 py-0.5 rounded ${req.evidence_available ? 'bg-emerald-500/10 text-emerald-400' : 'bg-slate-900 text-slate-500'}`}>
                  {req.evidence_available ? 'Verified' : 'Unconfirmed'}
                </span>
              </div>
            </div>
          ))}
        </div>
      </div>

      {/* Provenance Details */}
      <CalculationProvenanceViewer
        provenance={provenance}
        metricName="infrastructure_readiness_score"
        title="Infrastructure Scoring Provenance"
      />
    </div>
  );
};

export default InfrastructureAnalysisCard;
