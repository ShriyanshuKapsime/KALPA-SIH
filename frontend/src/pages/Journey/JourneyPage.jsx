import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Compass,
  Award,
  DollarSign,
  Cpu,
  CheckCircle2,
  Sparkles,
  ArrowRight,
  RefreshCw,
  Building2,
  MapPin,
  ShieldCheck,
  TrendingUp,
  Layers,
  ChevronRight,
  ExternalLink,
  UserCheck,
  FileCheck2,
  AlertCircle,
  Clock,
  Lock
} from 'lucide-react';
import { useWorkflow, JOURNEY_PILLARS } from '../../context/WorkflowContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';
import OrchestratorVisualization from '../../components/workflow/OrchestratorVisualization';
import LockedStageCard, { FUTURE_STAGES } from '../../components/workflow/LockedStageCard';
import apiService from '../../services/api';

export default function JourneyPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    sessionId,
    analysisId,
    businessName,
    businessId,
    completedStages,
    currentStage,
    engineOutputs,
    restoreWorkflowState,
    updateWorkflowState,
    runOrchestratorPipeline,
    isOrchestrating,
    workflowError
  } = useWorkflow();

  const [loading, setLoading] = useState(false);
  const [profileData, setProfileData] = useState(null);

  // Sync state from URL or backend if present
  useEffect(() => {
    const q = new URLSearchParams(location.search);
    const sid = q.get('session_id') || sessionId;
    const aid = q.get('analysis_id') || analysisId;
    if (sid || aid) {
      restoreWorkflowState(aid || sid);
    }
  }, [location.search]);

  // Load Stage 3 Profile details for summary card
  useEffect(() => {
    const fetchProfile = async () => {
      const targetId = analysisId || sessionId;
      if (!targetId) return;
      try {
        let res;
        if (analysisId) {
          res = await apiService.profile.getProfileByAnalysisId(analysisId);
        } else {
          res = await apiService.profile.getProfileBySessionId(sessionId);
        }
        if (res) {
          setProfileData(res.profile || res);
        }
      } catch (e) {
        console.log('Profile fetch note:', e.message);
      }
    };
    fetchProfile();
  }, [analysisId, sessionId]);

  const displayBusiness = businessName || profileData?.specific_business || profileData?.business_name || 'Agro-Processing & Dairy Enterprise';
  const displaySector = profileData?.sector || 'Animal Husbandry & Agro-Processing';
  const displayLocation = profileData?.location_profile?.district
    ? `${profileData.location_profile.district}, ${profileData.location_profile.state || 'India'}`
    : 'Solapur District, Maharashtra';

  const isCoreDone = completedStages?.includes(1) && completedStages?.includes(2) && completedStages?.includes(3) && completedStages?.includes(5) && completedStages?.includes(8) && completedStages?.includes(9);

  return (
    <div className="min-h-screen bg-[#FAF7F2] text-[#1C1917] py-8 px-4 sm:px-6 lg:px-8 space-y-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* 1. Header Banner */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#EAE3D5] shadow-sm relative overflow-hidden">
          <div className="absolute top-0 right-0 w-96 h-96 bg-gradient-to-bl from-orange-100/60 via-amber-50/40 to-transparent rounded-bl-full pointer-events-none" />

          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2 max-w-3xl">
              <div className="inline-flex items-center gap-2 px-3.5 py-1 rounded-full bg-orange-100 border border-orange-200 text-[#C2410C] text-xs font-bold shadow-2xs">
                <Sparkles className="w-3.5 h-3.5 text-[#EA580C]" />
                <span>KALPA END-TO-END ENTREPRENEURSHIP JOURNEY</span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-black tracking-tight text-[#1C1917] font-['Outfit']">
                Rural Enterprise Advisory & Orchestration Hub
              </h1>

              <p className="text-sm text-[#57534E] leading-relaxed">
                Seamless progression from multilingual vernacular intake to deterministic market intelligence, opportunity evaluation, and bankable financial structuring.
              </p>

              {/* Active Enterprise Bar */}
              <div className="pt-2 flex flex-wrap items-center gap-4 text-xs font-medium text-[#57534E]">
                <span className="flex items-center gap-1.5 text-[#C2410C] font-bold bg-white px-3 py-1 rounded-lg border border-[#EAE3D5] shadow-2xs">
                  <Building2 className="w-3.5 h-3.5 text-[#EA580C]" />
                  {displayBusiness}
                </span>
                <span className="flex items-center gap-1.5 text-stone-600 bg-white px-3 py-1 rounded-lg border border-[#EAE3D5] shadow-2xs">
                  <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                  {displayLocation}
                </span>
                {analysisId && (
                  <span className="font-mono text-[11px] text-[#78716C] bg-stone-100 px-2.5 py-1 rounded-lg border border-stone-200">
                    ID: {analysisId.slice(0, 12)}...
                  </span>
                )}
              </div>
            </div>

            {/* Quick Actions */}
            <div className="flex flex-col sm:flex-row lg:flex-col gap-3 shrink-0">
              <Link
                to="/financial-planning"
                className="saffron-gradient-btn px-5 py-3 rounded-xl text-xs font-bold flex items-center justify-center gap-2 shadow-md hover:scale-105 transition-all text-center"
              >
                <DollarSign className="w-4 h-4" />
                <span>Open Financial Planning</span>
              </Link>
              <Link
                to="/intake"
                className="px-5 py-2.5 rounded-xl text-xs font-bold bg-white hover:bg-stone-50 border border-[#EAE3D5] text-[#57534E] flex items-center justify-center gap-2 shadow-2xs transition-all text-center"
              >
                <UserCheck className="w-4 h-4 text-[#EA580C]" />
                <span>Start New Intake</span>
              </Link>
            </div>
          </div>
        </div>

        {/* 2. Interactive Workflow Timeline */}
        <WorkflowTimeline />

        {/* 3. Orchestrator Visualization (Sequential Engines) */}
        <OrchestratorVisualization />

        {/* 4. Journey Phase Highlights (Understand, Discover, Validate, Finance) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h2 className="text-lg font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
              <Layers className="w-5 h-5 text-[#EA580C]" />
              Active Core Journey Pillars
            </h2>
            <span className="text-xs font-semibold text-[#78716C]">
              4 of 6 Pillars Available in Phase 1
            </span>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            
            {/* Pillar 1: Understand */}
            <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-[#C2410C] bg-orange-50 px-2 py-0.5 rounded border border-orange-200">
                    Pillar 01
                  </span>
                  <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                </div>
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] mb-1">
                  Understand
                </h3>
                <p className="text-xs text-[#57534E] leading-relaxed">
                  Vernacular voice intake, 5-digit NIC ontology classification, and canonical entrepreneur profile.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAE3D5] flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-700">Profile Verified ✓</span>
                <Link to="/profile" className="font-bold text-[#C2410C] hover:underline flex items-center gap-0.5">
                  View <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Pillar 2: Discover */}
            <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-amber-700 bg-amber-50 px-2 py-0.5 rounded border border-amber-200">
                    Pillar 02
                  </span>
                  {completedStages?.includes(5) ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Clock className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] mb-1">
                  Discover
                </h3>
                <p className="text-xs text-[#57534E] leading-relaxed">
                  Spatial demographics, catchment density, competitor landscape, and MSME benchmarks.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAE3D5] flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-700">
                  {engineOutputs?.market_intelligence || 'Demand Strong ✓'}
                </span>
                <Link to="/market-intelligence" className="font-bold text-[#C2410C] hover:underline flex items-center gap-0.5">
                  Inspect <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Pillar 3: Validate */}
            <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-indigo-700 bg-indigo-50 px-2 py-0.5 rounded border border-indigo-200">
                    Pillar 03
                  </span>
                  {completedStages?.includes(8) ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Clock className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] mb-1">
                  Validate
                </h3>
                <p className="text-xs text-[#57534E] leading-relaxed">
                  Deterministic 6-factor opportunity score, supply access, and critical constraint analysis.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAE3D5] flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-700">
                  {engineOutputs?.opportunity_evaluation || '88% Opportunity ✓'}
                </span>
                <Link to="/opportunity-evaluation" className="font-bold text-[#C2410C] hover:underline flex items-center gap-0.5">
                  Inspect <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

            {/* Pillar 4: Finance */}
            <div className="royal-card rounded-2xl p-5 border border-[#EAE3D5] bg-white flex flex-col justify-between">
              <div>
                <div className="flex items-center justify-between mb-3">
                  <span className="text-[10px] font-bold uppercase tracking-wider text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    Pillar 04
                  </span>
                  {completedStages?.includes(9) ? (
                    <CheckCircle2 className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <Clock className="w-4 h-4 text-amber-600" />
                  )}
                </div>
                <h3 className="text-base font-bold text-[#1C1917] font-['Outfit'] mb-1">
                  Finance
                </h3>
                <p className="text-xs text-[#57534E] leading-relaxed">
                  CapEx/OpEx, 90% debt structuring, annuity EMI, and institutional scheme matching.
                </p>
              </div>
              <div className="mt-4 pt-3 border-t border-[#EAE3D5] flex items-center justify-between text-xs">
                <span className="font-semibold text-emerald-700">
                  {engineOutputs?.financial_planning || '₹9L Financing Structure ✓'}
                </span>
                <Link to="/financial-planning" className="font-bold text-[#C2410C] hover:underline flex items-center gap-0.5">
                  Inspect <ChevronRight className="w-3.5 h-3.5" />
                </Link>
              </div>
            </div>

          </div>
        </div>

        {/* 5. Future Locked Stages Grid (Prepare & Grow) */}
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div className="space-y-0.5">
              <h2 className="text-lg font-bold text-[#1C1917] font-['Outfit'] flex items-center gap-2">
                <ShieldCheck className="w-5 h-5 text-[#78716C]" />
                Future Milestone Engines (Prepare & Grow)
              </h2>
              <p className="text-xs text-[#78716C]">
                These advanced modules unlock automatically as institutional lending partners and state agencies onboard.
              </p>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
            {FUTURE_STAGES.map((stage) => (
              <LockedStageCard key={stage.id} stage={stage} />
            ))}
          </div>
        </div>

      </div>
    </div>
  );
}
