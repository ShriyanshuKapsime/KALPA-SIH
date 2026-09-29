import React, { useState, useEffect, useRef } from 'react';
import { useLocation, useNavigate, Link } from 'react-router-dom';
import {
  Compass,
  MapPin,
  Building2,
  TrendingUp,
  Truck,
  Zap,
  Calendar,
  AlertTriangle,
  RefreshCw,
  ArrowRight,
  ShieldCheck,
  Award,
  Layers,
  PieChart
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';
import WorkflowTimeline from '../../components/workflow/WorkflowTimeline';

// Stage 6 Modular Components
import Stage6StatusBadge from '../../components/market/Stage6StatusBadge';
import CalculationProvenanceViewer from '../../components/market/CalculationProvenanceViewer';
import InputEvidenceSummary from '../../components/market/InputEvidenceSummary';
import GeospatialAnalysisCard from '../../components/market/GeospatialAnalysisCard';
import CompetitionAnalysisCard from '../../components/market/CompetitionAnalysisCard';
import InfrastructureAnalysisCard from '../../components/market/InfrastructureAnalysisCard';
import SupplyEcosystemCard from '../../components/market/SupplyEcosystemCard';
import DemandEvidenceCard from '../../components/market/DemandEvidenceCard';
import SeasonalityAnalysisCard from '../../components/market/SeasonalityAnalysisCard';
import MarketCapacityCard from '../../components/market/MarketCapacityCard';
import StructuredIndicatorsGrid from '../../components/market/StructuredIndicatorsGrid';
import BenchmarkComparisonCard from '../../components/market/BenchmarkComparisonCard';

export default function MarketIntelligencePage() {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
    updateWorkflowState,
    markStageComplete
  } = useWorkflow();

  const { t, language } = useLanguage();

  const queryParams = new URLSearchParams(location.search);
  const initialSessionId = location.state?.sessionId || location.state?.session_id || queryParams.get('session_id') || ctxSessionId || '';
  const initialAnalysisId = location.state?.analysisId || location.state?.analysis_id || queryParams.get('analysis_id') || ctxAnalysisId || '';

  const [analysisId, setAnalysisId] = useState(initialAnalysisId);
  const [sessionId, setSessionId] = useState(initialSessionId);

  // Data Containers
  const [evidenceProfile, setEvidenceProfile] = useState(null);
  const [stage6Output, setStage6Output] = useState(null);

  // UI & Loading States
  const [loading, setLoading] = useState(false);
  const [analyzingStage6, setAnalyzingStage6] = useState(false);
  const [collectingStage5, setCollectingStage5] = useState(false);
  const [forceRefresh, setForceRefresh] = useState(false);
  const [error, setError] = useState(null);
  const [selectedEnterprise, setSelectedEnterprise] = useState('poultry_farm_bangalore');

  const isExecutingRef = useRef(false);

  const SAMPLE_ENTERPRISES = [
    { id: 'poultry_farm_bangalore', key: 'poultry_farm', name: 'Broiler Poultry Farm Unit', district: 'Bangalore South', state: 'Karnataka', lat: 12.9716, lon: 77.5946, sector: 'Animal Husbandry', nic: '01461' },
    { id: 'dairy_farm_solapur', key: 'dairy_farm', name: 'Commercial Dairy Farm (10-Cow Unit)', district: 'Solapur', state: 'Maharashtra', lat: 17.6599, lon: 75.9064, sector: 'Animal Husbandry', nic: '01411' },
    { id: 'rice_mill_varanasi', key: 'rice_mill', name: 'Mini / Modern Rice Mill Unit', district: 'Varanasi', state: 'Uttar Pradesh', lat: 25.3176, lon: 82.9739, sector: 'Manufacturing / Agro-Processing', nic: '10612' },
    { id: 'grocery_store_ranchi', key: 'grocery_store', name: 'Rural Super-Kirana & General Store', district: 'Ranchi', state: 'Jharkhand', lat: 23.3441, lon: 85.3096, sector: 'Retail Trade', nic: '47110' },
  ];

  useEffect(() => {
    if (analysisId) {
      loadPipelineData(analysisId);
    } else if (sessionId) {
      apiService.orchestrator.getWorkflowStatus(sessionId)
        .then(wf => {
          if (wf && wf.analysis_id) {
            setAnalysisId(wf.analysis_id);
            loadPipelineData(wf.analysis_id);
          }
        })
        .catch(err => {
          console.log('[STAGE 5/6] Waiting for trigger:', err.message);
        });
    }
  }, [analysisId, sessionId]);

  const loadPipelineData = async (id) => {
    setLoading(true);
    setError(null);
    try {
      const s5Profile = await apiService.marketIntelligence.getById(id);
      if (s5Profile) {
        setEvidenceProfile(s5Profile);
        const sId = s5Profile.session_id || sessionId;
        const aId = s5Profile.analysis_id || id;
        
        setAnalyzingStage6(true);
        try {
          const s6Res = await apiService.marketIntelligence.analyze(s5Profile);
          if (s6Res) {
            setStage6Output(s6Res);
            updateWorkflowState({
              sessionId: sId,
              analysisId: aId,
              businessId: s5Profile.business_context?.business_id || s5Profile.business_context?.specific_business,
              currentStage: 6,
              completedStages: [1, 2, 3, 4, 5, 6],
              nextStage: 8,
              workflowStatus: 'MARKET_INTELLIGENCE_ANALYZED',
              engineOutputs: {
                market_intelligence: 'Demand Strong ✓'
              }
            });
            markStageComplete(5, 8);
          }
        } catch (s6Err) {
          console.error('[STAGE 6 ERROR] Deterministic analysis failed:', s6Err);
          setError(`Stage 6 Market Intelligence Engine error: ${s6Err.message}`);
        } finally {
          setAnalyzingStage6(false);
        }
      }
    } catch (err) {
      console.error('[STAGE 5/6 LOAD ERROR]', err);
      if (err.status === 404) {
        setError('Market evidence profile has not been compiled yet for this analysis. Click "Run Market Pipeline" below to collect evidence and analyze.');
      } else {
        setError(err.message || 'Failed to retrieve market intelligence records.');
      }
    } finally {
      setLoading(false);
    }
  };

  const runFullPipeline = async (enterpriseId = selectedEnterprise, shouldForceRefresh = forceRefresh) => {
    if (isExecutingRef.current) return;
    isExecutingRef.current = true;
    setCollectingStage5(true);
    setError(null);

    try {
      const sample = SAMPLE_ENTERPRISES.find(e => e.id === enterpriseId) || SAMPLE_ENTERPRISES[0];
      const targetAid = analysisId || undefined;
      const targetSid = sessionId || undefined;

      const payload = {
        analysis_id: targetAid,
        session_id: targetSid,
        business_profile: {
          business_profile: {
            business_id: sample.key,
            specific_business: sample.name,
            normalized_concept: sample.key.replace('_', ' '),
            sector: sample.sector,
            category: sample.name,
            nic: { code: sample.nic }
          },
          location_profile: {
            name: `${sample.district} Catchment`,
            village: sample.district,
            district: sample.district,
            state: sample.state,
            country: 'India',
            coordinates: { latitude: sample.lat, longitude: sample.lon }
          },
          financial_profile: { available_capital: 300000.0 },
          analysis_requirements: {
            direct_competitors: [`Local ${sample.name} Farms / Units`],
            adjacent_competitors: ['Feed & Veterinary Hubs', 'Wholesale Mandis'],
            substitute_businesses: ['Imported Meat Retailers', 'Weekly Haats'],
            demand_features: ['catchment_population', 'protein_consumption_proxy', 'household_density'],
            infrastructure_requirements: ['3-phase power grid', 'PMGSY all-weather road', 'veterinary access'],
            required_datasets: ['Census 2011', 'Livestock Census', 'MSME UDYAM', 'LGD']
          }
        },
        force_refresh: shouldForceRefresh,
        force_llm: false
      };

      const s5Res = await apiService.marketIntelligence.collect(payload);
      if (s5Res && s5Res.evidence_profile) {
        setEvidenceProfile(s5Res.evidence_profile);
        const aId = s5Res.analysis_id || targetAid;
        const sId = s5Res.session_id || targetSid;
        if (aId) setAnalysisId(aId);
        if (sId) setSessionId(sId);

        setCollectingStage5(false);
        setAnalyzingStage6(true);

        const s6Res = await apiService.marketIntelligence.analyze(s5Res.evidence_profile);
        if (s6Res) {
          setStage6Output(s6Res);
          updateWorkflowState({
            sessionId: sId,
            analysisId: aId,
            businessId: s5Res.evidence_profile.business_context?.business_id || sample.key,
            currentStage: 6,
            completedStages: [1, 2, 3, 4, 5, 6],
            nextStage: 8,
            workflowStatus: 'MARKET_INTELLIGENCE_ANALYZED',
            engineOutputs: {
              market_intelligence: 'Demand Strong ✓'
            }
          });
          markStageComplete(5, 8);
        }
      }
    } catch (err) {
      console.error('[PIPELINE EXECUTION ERROR]', err);
      setError(err.message || 'Pipeline execution failed.');
    } finally {
      setCollectingStage5(false);
      setAnalyzingStage6(false);
      isExecutingRef.current = false;
    }
  };

  const bizContext = stage6Output?.business_context || evidenceProfile?.business_context || {};
  const locContext = stage6Output?.location_context || evidenceProfile?.location_context || {};
  const resolvedLoc = locContext.resolved_location || locContext;
  const indicators = stage6Output?.market_indicators || {};
  const benchmarkAnalysis = stage6Output?.benchmark_analysis || {};
  const calculationProvenance = stage6Output?.calculation_provenance || [];
  const quality = stage6Output?.evidence_quality || {};

  const bizName = bizContext.specific_business || bizContext.business_name || 'Enterprise Profile';
  const locationName = [resolvedLoc.district, resolvedLoc.state].filter(Boolean).join(', ') || 'Location Not Specified';

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 space-y-6 sm:space-y-8 relative text-[#28231F]">
      <div className="max-w-7xl mx-auto space-y-6 sm:space-y-8">
        
        {/* 1. Workflow Timeline Header */}
        <WorkflowTimeline />

        {/* 2. Page Title & Control Bar */}
        <div className="royal-panel rounded-2xl p-6 sm:p-8 border border-[#79563F]/18 shadow-xs relative overflow-hidden h-auto">
          <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-6 relative z-10">
            <div className="space-y-2">
              <div className="flex flex-wrap items-center gap-2 mb-1">
                <span className="px-3 py-1 rounded-full text-xs font-bold bg-[#C96A3A]/10 text-[#C96A3A] border border-[#C96A3A]/25">
                  {t('step_3', '03 Market Intelligence')}
                </span>
              </div>

              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#28231F] font-['Outfit']">
                {t('market_title', 'Spatial Market Intelligence Engine')}
              </h1>
              <p className="text-xs sm:text-sm text-[#79563F]">
                {t('market_subtitle', 'Data-grounded catchment analysis, demand density, and competitor mapping.')}
              </p>

              <div className="flex flex-wrap items-center gap-4 text-xs text-[#62584F] pt-1">
                <span className="flex items-center gap-1.5 font-bold text-[#28231F]">
                  <Building2 className="w-4 h-4 text-[#C96A3A]" />
                  {bizName}
                </span>
                <span>&middot;</span>
                <span className="flex items-center gap-1 text-[#62584F]">
                  <MapPin className="w-3.5 h-3.5 text-[#006F5F]" />
                  {locationName}
                </span>
              </div>
            </div>

            {/* Actions */}
            <div className="flex flex-wrap items-center gap-3 shrink-0">
              <button
                onClick={() => runFullPipeline(selectedEnterprise, forceRefresh)}
                disabled={collectingStage5 || analyzingStage6 || loading}
                className="saffron-gradient-btn px-4 py-2.5 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md transition-all cursor-pointer disabled:opacity-50"
              >
                <RefreshCw className={`w-3.5 h-3.5 ${(collectingStage5 || analyzingStage6) ? 'animate-spin' : ''}`} />
                <span>
                  {collectingStage5 ? t('loading', 'Collecting...') : analyzingStage6 ? t('analyzing', 'Analyzing...') : t('refresh', 'Run Market Pipeline')}
                </span>
              </button>

              <Link
                to={`/opportunity-evaluation${analysisId ? `?analysis_id=${analysisId}` : ''}`}
                className="px-4 py-2.5 rounded-xl text-xs font-bold bg-[#FAF2E3] hover:bg-[#F1E4CC] border border-[#79563F]/20 text-[#28231F] shadow-2xs flex items-center gap-1.5 transition-colors"
              >
                <span>{t('proceed', 'Proceed to Opportunity')}</span>
                <ArrowRight className="w-3.5 h-3.5 text-[#C96A3A]" />
              </Link>
            </div>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="p-4 rounded-xl bg-rose-50 border border-rose-200 text-rose-800 text-xs flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0" />
            <span>{error}</span>
          </div>
        )}

        {/* PRIMARY VIEW: EDITORIAL MARKET ADVISORY INTERFACE */}
        <div className="space-y-6 sm:space-y-8 animate-fadeIn">
          
          {/* 1. Market Evidence Summary */}
          <InputEvidenceSummary
            stage5Data={evidenceProfile || {}}
            stage6Data={stage6Output || {}}
          />

          {/* 2. Consolidated Market Indicators */}
          <StructuredIndicatorsGrid
            indicators={indicators}
            quality={quality}
          />

          {/* 3. TWO INDEPENDENT MASONRY COLUMNS (Zero row synchronization, packed layout) */}
          <div className="market-analysis-masonry grid grid-cols-1 lg:grid-cols-2 gap-5 sm:gap-6 items-start">
            
            {/* LEFT COLUMN: Seasonality -> Geospatial -> Infrastructure -> Calculation Provenance */}
            <div className="market-analysis-column flex flex-col gap-5 sm:gap-6 w-full min-w-0">
              <SeasonalityAnalysisCard
                seasonality={indicators.seasonality || {}}
              />
              <GeospatialAnalysisCard
                geospatial={indicators.geospatial_analysis || {}}
                marketAccess={indicators.market_access || {}}
              />
              <InfrastructureAnalysisCard
                infrastructure={indicators.infrastructure || {}}
              />
              <CalculationProvenanceViewer
                provenance={calculationProvenance}
                title="Mathematical Calculation Provenance (Audit View)"
                collapsible={true}
                defaultExpanded={false}
              />
            </div>

            {/* RIGHT COLUMN: Competition -> Supply Ecosystem -> Demand Evidence -> Benchmark Deviations */}
            <div className="market-analysis-column flex flex-col gap-5 sm:gap-6 w-full min-w-0">
              <CompetitionAnalysisCard
                competition={indicators.competition || {}}
              />
              <SupplyEcosystemCard
                supply={indicators.supply_ecosystem || {}}
              />
              <DemandEvidenceCard
                demand={indicators.demand_evidence || {}}
              />
              <BenchmarkComparisonCard
                benchmarkAnalysis={benchmarkAnalysis}
              />
            </div>

          </div>

          {/* 4. FULL-WIDTH SYNTHESIS: Net Market Capacity & Expansion Signal */}
          <MarketCapacityCard
            capacity={indicators.market_capacity || {}}
          />

          {/* 5. FULL-WIDTH NEXT STEP: Stage 8 Handoff Banner */}
          <div className="royal-panel rounded-2xl p-6 border border-[#79563F]/18 flex flex-col sm:flex-row items-center justify-between gap-4 shadow-xs h-auto">
            <div className="space-y-1">
              <span className="text-xs font-bold uppercase tracking-wider text-[#006F5F]">
                {t('completed', 'Stage 5 Market Intelligence Established')}
              </span>
              <h3 className="text-base font-bold text-[#28231F] font-['Outfit']">
                {t('opp_title', 'Ready for Stage 8: Opportunity Evaluation Engine')}
              </h3>
              <p className="text-xs text-[#62584F]">
                {t('opp_subtitle', 'Proceed to evaluate multi-factor opportunity scores, competition trade-offs, and critical constraints.')}
              </p>
            </div>

            <Link
              to={`/opportunity-evaluation${analysisId ? `?analysis_id=${analysisId}` : ''}`}
              className="saffron-gradient-btn px-6 py-3 rounded-xl text-xs font-bold flex items-center gap-2 shadow-md shrink-0"
            >
              <span>{t('proceed', 'Proceed to Opportunity Evaluation')}</span>
              <ArrowRight className="w-4 h-4" />
            </Link>
          </div>

        </div>

      </div>
    </div>
  );
}
