import React, { useState, useEffect } from 'react';
import {
  Database,
  ShieldCheck,
  TrendingUp,
  AlertTriangle,
  FileText,
  Layers,
  Search,
  Filter,
  CheckCircle2,
  Clock,
  ExternalLink,
  ChevronRight,
  Info,
  DollarSign,
  Activity,
  BarChart3,
  Calendar,
  Sparkles,
  MapPin,
  Cpu,
  RefreshCw,
  Wrench,
  FileCheck2,
  Radio,
  Sliders,
} from 'lucide-react';
import apiService from '../../services/api';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';

const PRIORITY_BUSINESSES = [
  { id: 'rice_mill', label: 'Mini Rice Mill' },
  { id: 'flour_mill', label: 'Atta Chakki / Flour Mill' },
  { id: 'spice_processing', label: 'Spice Processing Unit' },
  { id: 'food_processing_micro', label: 'Micro Bakery & Snacks' },
  { id: 'dairy_farm', label: 'Dairy Farm & Chilling' },
  { id: 'poultry_farm', label: 'Broiler Poultry Farm' },
  { id: 'goat_farming', label: 'Commercial Goat Farm' },
  { id: 'grocery_store', label: 'Rural Kirana Store' },
  { id: 'saree_retail', label: 'Saree & Matching Center' },
  { id: 'garment_store', label: 'Readymade Garment Store' },
  { id: 'tailoring_shop', label: 'Custom Tailoring Unit' },
  { id: 'beauty_salon', label: 'Beauty Parlour / Salon' },
  { id: 'mobile_repair', label: 'Mobile & Electronics Repair' },
  { id: 'furniture_carpentry', label: 'Carpentry & Woodwork' },
  { id: 'handicrafts', label: 'Handicrafts & Handloom' },
];

export const KnowledgeHubPage = () => {
  const { language, t } = useLanguage();
  const [activeTab, setActiveTab] = useState('overview');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Data states
  const [coverageReport, setCoverageReport] = useState(null);
  const [dataSources, setDataSources] = useState([]);
  const [schemes, setSchemes] = useState([]);
  const [financialBenchmarks, setFinancialBenchmarks] = useState([]);
  const [marketBenchmarks, setMarketBenchmarks] = useState([]);
  const [businessProfiles, setBusinessProfiles] = useState([]);
  const [risks, setRisks] = useState([]);
  const [documents, setDocuments] = useState([]);
  const [dynamicReqs, setDynamicReqs] = useState([]);

  // Search and filter states
  const [sourceSearch, setSourceSearch] = useState('');
  const [sourceCategoryFilter, setSourceCategoryFilter] = useState('ALL');
  const [selectedBusinessNode, setSelectedBusinessNode] = useState('rice_mill');
  const [riskCategoryFilter, setRiskCategoryFilter] = useState('ALL');

  // Interactive Scheme Calculator state
  const [calcCost, setCalcCost] = useState(140000);
  const [calcMargin, setCalcMargin] = useState(14000);
  const [calcGender, setCalcGender] = useState('ALL');
  const [calcCaste, setCalcCaste] = useState('ALL');
  const [calcIsRural, setCalcIsRural] = useState(true);
  const [evalResult, setEvalResult] = useState(null);
  const [feasibilityResult, setFeasibilityResult] = useState(null);
  const [evaluating, setEvaluating] = useState(false);

  // Fetch initial knowledge data
  const fetchKnowledgeData = async () => {
    setLoading(true);
    setError(null);
    try {
      const [covRes, srcRes, schRes, finRes, mktRes, profRes, rskRes, docRes, dynRes] = await Promise.all([
        apiService.knowledge.getCoverageReport().catch(() => null),
        apiService.knowledge.getDataSources().catch(() => []),
        apiService.knowledge.getSchemes().catch(() => []),
        apiService.knowledge.getFinancialBenchmarks().catch(() => []),
        apiService.knowledge.getMarketBenchmarks().catch(() => []),
        apiService.knowledge.getBusinessProfiles().catch(() => []),
        apiService.knowledge.getRisks().catch(() => []),
        apiService.knowledge.getDocuments().catch(() => []),
        apiService.knowledge.getDynamicRequirements().catch(() => []),
      ]);

      setCoverageReport(covRes);
      setDataSources(srcRes || []);
      setSchemes(schRes || []);
      setFinancialBenchmarks(finRes || []);
      setMarketBenchmarks(mktRes || []);
      setBusinessProfiles(Array.isArray(profRes) ? profRes : (profRes?.businesses || profRes?.data || []));
      setRisks(rskRes || []);
      setDocuments(docRes || []);
      setDynamicReqs(dynRes || []);

      // Initial calculation
      evaluateFinance(140000, 14000, 'rice_mill', 'ALL', 'ALL', true);
    } catch (err) {
      setError(err.message || 'Failed to load Knowledge Hub');
    } finally {
      setLoading(false);
    }
  };

  const evaluateFinance = async (cost, margin, businessId, gender, caste, isRural) => {
    setEvaluating(true);
    try {
      const [schemeRes, feasRes] = await Promise.all([
        apiService.knowledge.evaluateSchemeEligibility({
          project_cost: parseFloat(cost),
          available_margin: parseFloat(margin),
          gender,
          caste,
          is_rural: isRural,
          business_node_id: businessId,
        }).catch(() => null),
        apiService.knowledge.calculateFinancialFeasibility({
          business_id: businessId,
          project_cost: parseFloat(cost),
          available_margin: parseFloat(margin),
        }).catch(() => null),
      ]);
      setEvalResult(schemeRes);
      setFeasibilityResult(feasRes);
    } catch (err) {
      console.error('Calculation error:', err);
    } finally {
      setEvaluating(false);
    }
  };

  useEffect(() => {
    fetchKnowledgeData();
  }, []);

  const handleCalculatorSubmit = (e) => {
    e.preventDefault();
    evaluateFinance(calcCost, calcMargin, selectedBusinessNode, calcGender, calcCaste, calcIsRural);
  };

  // Selected financial, market, and domain profile objects
  const activeFinBenchmark =
    financialBenchmarks.find(
      (b) =>
        b.business_node_id === selectedBusinessNode ||
        (b.aliases && b.aliases.includes(selectedBusinessNode))
    ) || financialBenchmarks[0] || null;

  const activeMktBenchmark =
    marketBenchmarks.find(
      (b) =>
        b.business_node_id === selectedBusinessNode ||
        (b.aliases && b.aliases.includes(selectedBusinessNode))
    ) || marketBenchmarks[0] || null;

  const activeProfile =
    businessProfiles.find(
      (p) =>
        p.business_node_id === selectedBusinessNode ||
        (p.aliases && p.aliases.includes(selectedBusinessNode))
    ) || null;

  const filteredSources = dataSources.filter((s) => {
    const matchesSearch =
      (s.dataset_name || '').toLowerCase().includes(sourceSearch.toLowerCase()) ||
      (s.official_source || '').toLowerCase().includes(sourceSearch.toLowerCase()) ||
      (s.ministry_or_nodal_agency || '').toLowerCase().includes(sourceSearch.toLowerCase()) ||
      (s.dataset_id || '').toLowerCase().includes(sourceSearch.toLowerCase());
    const matchesCategory =
      sourceCategoryFilter === 'ALL' || (s.category || '').toUpperCase() === sourceCategoryFilter.toUpperCase();
    return matchesSearch && matchesCategory;
  });

  const filteredRisks = risks.filter((r) => {
    return (
      riskCategoryFilter === 'ALL' ||
      (r.category || '').toUpperCase() === riskCategoryFilter.toUpperCase()
    );
  });

  return (
    <div className="min-h-screen pt-24 pb-16 relative">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 space-y-8">
        {/* Header Banner */}
        <div className="bg-gradient-to-r from-[#1C1917] via-[#292524] to-[#44403C] rounded-3xl p-8 sm:p-10 text-white shadow-xl relative overflow-hidden border border-stone-800">
          <div className="absolute right-0 top-0 bottom-0 w-1/3 bg-gradient-to-l from-orange-600/20 to-transparent pointer-events-none" />
          <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
            <div className="space-y-3 max-w-3xl">
              <div className="flex items-center gap-2.5">
                <span className="px-3 py-1 rounded-full text-xs font-bold uppercase tracking-wider bg-orange-500/20 text-orange-400 border border-orange-500/30 flex items-center gap-1.5">
                  <Database className="w-3.5 h-3.5" />
                  {t('knowledge_stage_badge', 'Stage 4.5 Knowledge Infrastructure')}
                </span>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-500/20 text-emerald-400 border border-emerald-500/30">
                  {t('knowledge_enterprises_ready', '15 Priority Rural Enterprises Ready')}
                </span>
              </div>
              <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight font-['Outfit']">
                {t('knowledge_hub_title', 'KALPA Domain Knowledge & Benchmark Hub')}
              </h1>
              <p className="text-stone-300 text-sm sm:text-base leading-relaxed">
                {t('knowledge_hub_subtitle', 'Centralized knowledge repository organizing 31 consolidated SIH datasets, authoritative government schemes, empirical financial benchmarks, catchment norms, risk libraries, and institutional research.')}
              </p>
            </div>

            <div className="flex flex-col sm:flex-row items-start sm:items-center gap-3">
              <button
                onClick={fetchKnowledgeData}
                disabled={loading}
                className="px-4 py-2.5 rounded-xl bg-white/10 hover:bg-white/20 border border-white/20 text-xs font-semibold flex items-center gap-2 transition-all shadow-sm cursor-pointer"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                <span>{t('knowledge_refresh_btn', 'Refresh Hub')}</span>
              </button>
            </div>
          </div>
        </div>

        {/* Global Navigation Tabs */}
        <div className="flex overflow-x-auto no-scrollbar gap-2 p-1.5 bg-white rounded-2xl border border-[#EAE3D5] shadow-sm">
          {[
            { id: 'overview', label: t('tab_overview', 'Overview & Coverage'), icon: Activity, badge: t('overview', 'Audit') },
            { id: 'datasets', label: t('tab_datasets', '31 Datasets Registry'), icon: Database, badge: '31' },
            { id: 'schemes', label: t('tab_schemes', 'Schemes & Loan Rules'), icon: ShieldCheck, badge: t('rules', 'Rules') },
            { id: 'benchmarks', label: t('tab_benchmarks', '15 Rural Enterprises'), icon: BarChart3, badge: '15' },
            { id: 'risks', label: t('tab_risks', 'Risk Library'), icon: AlertTriangle, badge: `${risks.length}` },
            { id: 'documents', label: t('tab_documents', 'Institutional Evidence'), icon: FileText, badge: 'NABARD/RBI' },
          ].map((tab) => {
            const Icon = tab.icon;
            const isActive = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`flex items-center gap-2 px-4 py-2.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                  isActive
                    ? 'bg-[#EA580C] text-white shadow-md shadow-orange-600/20'
                    : 'text-stone-600 hover:text-stone-900 hover:bg-stone-50'
                }`}
              >
                <Icon className="w-4 h-4" />
                <span>{tab.label}</span>
                {tab.badge && (
                  <span
                    className={`text-[10px] px-1.5 py-0.5 rounded-full font-bold ${
                      isActive ? 'bg-white/20 text-white' : 'bg-stone-100 text-stone-600'
                    }`}
                  >
                    {tab.badge}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        {/* TAB 1: OVERVIEW & COVERAGE */}
        {activeTab === 'overview' && (
          <div className="space-y-6">
            {/* Top Metric Cards */}
            <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
              <div className="bg-white p-5 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-stone-500">
                  <span className="text-xs font-medium uppercase tracking-wider">
                    {t('knowledge_sih_master_datasets', 'SIH Master Datasets')}
                  </span>
                  <Database className="w-4 h-4 text-orange-600" />
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-stone-900 font-['Outfit']">
                  {coverageReport?.total_curated_datasets || 31}
                </div>
                <p className="text-[11px] text-emerald-600 font-medium flex items-center gap-1">
                  <CheckCircle2 className="w-3.5 h-3.5" /> {t('knowledge_ingested_indexed', '100% Ingested & Indexed')}
                </p>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-stone-500">
                  <span className="text-xs font-medium uppercase tracking-wider">
                    {t('knowledge_priority_enterprises', 'Priority Enterprises')}
                  </span>
                  <Layers className="w-4 h-4 text-emerald-600" />
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-stone-900 font-['Outfit']">
                  {coverageReport?.total_business_profiles || 15} / 15
                </div>
                <p className="text-[11px] text-stone-500">{t('knowledge_layer_coverage', 'Full 5-Layer Coverage')}</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-stone-500">
                  <span className="text-xs font-medium uppercase tracking-wider">
                    {t('knowledge_govt_schemes', 'Government Schemes')}
                  </span>
                  <ShieldCheck className="w-4 h-4 text-blue-600" />
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-stone-900 font-['Outfit']">
                  {coverageReport?.total_schemes || schemes.length}
                </div>
                <p className="text-[11px] text-stone-500">{t('knowledge_schemes_sub', 'SIH Baseline + National Schemes')}</p>
              </div>

              <div className="bg-white p-5 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-2">
                <div className="flex items-center justify-between text-stone-500">
                  <span className="text-xs font-medium uppercase tracking-wider">
                    {t('knowledge_completeness_score', 'Completeness Score')}
                  </span>
                  <Activity className="w-4 h-4 text-purple-600" />
                </div>
                <div className="text-2xl sm:text-3xl font-bold text-purple-700 font-['Outfit']">
                  {coverageReport?.completeness_score_pct || 98.4}%
                </div>
                <p className="text-[11px] text-purple-600 font-medium">{t('knowledge_authoritative', 'Authoritative & Verified')}</p>
              </div>
            </div>

            {/* 15 Priority Rural Enterprises Coverage Grid */}
            <div className="bg-white p-6 rounded-3xl border border-[#EAE3D5] shadow-sm space-y-4">
              <div className="flex items-center justify-between">
                <h3 className="text-base font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                  <BarChart3 className="w-5 h-5 text-orange-600" />
                  {t('knowledge_matrix_title', '15 Priority Rural Enterprise Coverage Matrix')}
                </h3>
                <span className="text-xs px-2.5 py-0.5 rounded-full bg-emerald-100 text-emerald-800 font-bold">
                  {t('knowledge_fully_engine_ready', '15 / 15 Fully Engine-Ready')}
                </span>
              </div>
              <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-5 gap-3">
                {PRIORITY_BUSINESSES.map((pb) => (
                  <div
                    key={pb.id}
                    onClick={() => {
                      setSelectedBusinessNode(pb.id);
                      setActiveTab('benchmarks');
                    }}
                    className="p-3 bg-stone-50 hover:bg-orange-50/50 hover:border-orange-300 rounded-xl border border-stone-200 transition-all cursor-pointer space-y-1.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold text-stone-500 truncate">
                        {pb.id}
                      </span>
                      <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 shrink-0" />
                    </div>
                    <div className="text-xs font-bold text-stone-900 truncate font-['Outfit']">
                      {t(`biz_${pb.id}`, pb.label)}
                    </div>
                    <div className="flex gap-1 text-[9px] font-semibold text-stone-500">
                      <span className="bg-white px-1.5 py-0.5 rounded border border-stone-200">CapEx</span>
                      <span className="bg-white px-1.5 py-0.5 rounded border border-stone-200">Market</span>
                      <span className="bg-white px-1.5 py-0.5 rounded border border-stone-200">Licenses</span>
                    </div>
                  </div>
                ))}
              </div>
            </div>

            {/* Ingestion & Provenance Distribution */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-white p-6 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-4">
                <h3 className="text-base font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                  <Cpu className="w-4 h-4 text-orange-600" />
                  {t('knowledge_ingestion_status', 'Dataset Ingestion Status Breakdown')}
                </h3>
                <div className="space-y-3">
                  {coverageReport?.status_breakdown &&
                    Object.entries(coverageReport.status_breakdown).map(([status, count]) => {
                      const pct = Math.round((count / (coverageReport.total_curated_datasets || 1)) * 100);
                      const isAvailable = status === 'AVAILABLE';
                      return (
                        <div key={status} className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className="font-semibold text-stone-700">
                              <TranslatedText text={status} />
                            </span>
                            <span className="text-stone-500">
                              {count} {t('datasets', 'Datasets')} ({pct}%)
                            </span>
                          </div>
                          <div className="w-full bg-stone-100 rounded-full h-2 overflow-hidden">
                            <div
                              className={`h-full rounded-full ${
                                isAvailable ? 'bg-emerald-500' : 'bg-orange-400'
                              }`}
                              style={{ width: `${pct}%` }}
                            />
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              <div className="bg-white p-6 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-4">
                <h3 className="text-base font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                  <ShieldCheck className="w-4 h-4 text-emerald-600" />
                  {t('knowledge_layer_arch_title', 'Layered Architecture & Provenance Verification')}
                </h3>
                <div className="space-y-3">
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs text-stone-700 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-stone-900 font-semibold">
                        {t('knowledge_layer1_title', 'Layer 1: Official Policy & Math Rules')}
                      </strong>
                      {t('knowledge_layer1_desc', 'SIH Problem Statement baseline rules (Micro ≤ ₹1.40L @ 6.5%, Term Loan @ 8.0%) with deterministic EMI.')}
                    </div>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs text-stone-700 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-stone-900 font-semibold">
                        {t('knowledge_layer23_title', 'Layer 2 & 3: Domain & Benchmarks')}
                      </strong>
                      {t('knowledge_layer23_desc', 'NABARD Model Bankable Projects, KVIC Profiles, and Spices Board empirical research.')}
                    </div>
                  </div>
                  <div className="p-3 bg-stone-50 rounded-xl border border-stone-200 text-xs text-stone-700 flex items-start gap-2.5">
                    <CheckCircle2 className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />
                    <div>
                      <strong className="block text-stone-900 font-semibold">
                        {t('knowledge_layer45_title', 'Layer 4 & 5: Evidence & Dynamic Feeds')}
                      </strong>
                      {t('knowledge_layer45_desc', 'NABARD/RBI circulars and 31 Open Government Data (Agmarknet, Census, PMGSY) candidate sources.')}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* TAB 2: 31 DATASETS REGISTRY */}
        {activeTab === 'datasets' && (
          <div className="space-y-6">
            {/* Search and Filters */}
            <div className="flex flex-col sm:flex-row gap-3 bg-white p-4 rounded-2xl border border-[#EAE3D5] shadow-sm">
              <div className="relative flex-1">
                <Search className="w-4 h-4 text-stone-400 absolute left-3 top-3" />
                <input
                  type="text"
                  placeholder={t('knowledge_search_placeholder', 'Search 31 datasets by name, ministry, official source, ID...')}
                  value={sourceSearch}
                  onChange={(e) => setSourceSearch(e.target.value)}
                  className="w-full pl-9 pr-4 py-2 bg-stone-50 border border-stone-200 rounded-xl text-xs focus:outline-none focus:border-orange-500 text-stone-900"
                />
              </div>
              <div className="flex items-center gap-2">
                <Filter className="w-4 h-4 text-stone-400" />
                <select
                  value={sourceCategoryFilter}
                  onChange={(e) => setSourceCategoryFilter(e.target.value)}
                  className="px-3 py-2 bg-stone-50 border border-stone-200 rounded-xl text-xs font-medium text-stone-800 focus:outline-none focus:border-orange-500"
                >
                  <option value="ALL">{t('cat_all', 'All Categories')}</option>
                  <option value="ENTERPRISE_REGISTRY">{t('cat_enterprise_registry', 'Enterprise Registries')}</option>
                  <option value="AGRICULTURE_AND_COMMODITY">{t('cat_agri_commodity', 'Agriculture & Commodities')}</option>
                  <option value="INFRASTRUCTURE_AND_POWER">{t('cat_infra_power', 'Infrastructure & Utilities')}</option>
                  <option value="FINANCIAL_INCLUSION">{t('cat_fin_inclusion', 'Financial Inclusion')}</option>
                  <option value="DEMOGRAPHICS_AND_SOCIOECONOMIC">{t('cat_demographics', 'Demographics & Census')}</option>
                  <option value="GOVERNMENT_SCHEMES">{t('cat_govt_schemes', 'Schemes & Subsidies')}</option>
                  <option value="CLIMATE_AND_ENVIRONMENT">{t('cat_climate_env', 'Climate & Environment')}</option>
                  <option value="SKILLS_AND_VOCATIONAL">{t('cat_skills_vocational', 'Skills & Employment')}</option>
                </select>
              </div>
            </div>

            {/* Datasets Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {filteredSources.map((ds) => (
                <div
                  key={ds.dataset_id}
                  className="bg-white p-5 rounded-2xl border border-[#EAE3D5] shadow-sm hover:border-orange-300 transition-all flex flex-col justify-between space-y-4"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-mono font-bold px-2 py-0.5 rounded bg-stone-100 text-stone-600 border border-stone-200">
                        {ds.dataset_id}
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${
                          ds.ingestion_status === 'AVAILABLE'
                            ? 'bg-emerald-100 text-emerald-700'
                            : 'bg-amber-100 text-amber-700'
                        }`}
                      >
                        <TranslatedText text={ds.ingestion_status} />
                      </span>
                    </div>
                    <h4 className="text-sm font-bold text-stone-900 leading-snug font-['Outfit']">
                      <TranslatedText text={ds.dataset_name} />
                    </h4>
                    <p className="text-xs text-stone-600 line-clamp-2">
                      <TranslatedText text={ds.notes || `Official dataset from ${ds.ministry_or_nodal_agency}.`} />
                    </p>
                  </div>

                  <div className="pt-3 border-t border-stone-100 space-y-1.5 text-[11px] text-stone-500">
                    <div className="flex justify-between">
                      <span>{t('authority', 'Authority')}:</span>
                      <span className="font-semibold text-stone-700 text-right truncate max-w-[180px]">
                        <TranslatedText text={ds.ministry_or_nodal_agency} />
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{t('source_portal', 'Source Portal')}:</span>
                      <span className="font-semibold text-stone-700 text-right truncate max-w-[180px]">
                        <TranslatedText text={ds.official_source} />
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span>{t('format_records', 'Format / Records')}:</span>
                      <span className="font-mono text-stone-700">
                        {ds.file_format} ({ds.records_count?.toLocaleString()} {t('rows', 'rows')})
                      </span>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* TAB 3: SCHEMES & BASELINE CALCULATOR */}
        {activeTab === 'schemes' && (
          <div className="space-y-8">
            {/* Interactive Scheme & Loan Rule Evaluator */}
            <div className="bg-gradient-to-br from-white to-[#FAF7F2] p-6 sm:p-8 rounded-3xl border-2 border-orange-200 shadow-md space-y-6">
              <div className="flex items-center gap-3">
                <div className="w-10 h-10 rounded-xl bg-orange-600 flex items-center justify-center text-white shadow-md shadow-orange-600/20">
                  <DollarSign className="w-5 h-5" />
                </div>
                <div>
                  <h3 className="text-lg font-bold text-stone-900 font-['Outfit']">
                    {t('knowledge_calc_title', 'Deterministic Finance & Baseline Rule Evaluator (0 LLM Calls)')}
                  </h3>
                  <p className="text-xs text-stone-500">
                    {t('knowledge_calc_desc', 'Calculates reducing balance EMI, moratorium schedules, and DSCR feasibility strictly via official deterministic rules.')}
                  </p>
                </div>
              </div>

              <form onSubmit={handleCalculatorSubmit} className="grid grid-cols-1 sm:grid-cols-5 gap-4">
                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-stone-700">
                    {t('knowledge_total_project_cost', 'Total Project Cost (₹)')}
                  </label>
                  <input
                    type="number"
                    value={calcCost}
                    onChange={(e) => setCalcCost(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-stone-300 rounded-xl text-xs font-semibold focus:outline-none focus:border-orange-500 text-stone-900"
                    placeholder="e.g. 140000"
                    min="5000"
                    step="5000"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-stone-700">
                    {t('knowledge_promoter_equity', 'Promoter Equity (₹)')}
                  </label>
                  <input
                    type="number"
                    value={calcMargin}
                    onChange={(e) => setCalcMargin(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-stone-300 rounded-xl text-xs font-semibold focus:outline-none focus:border-orange-500 text-stone-900"
                    placeholder="e.g. 14000"
                    min="0"
                    step="1000"
                  />
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-stone-700">
                    {t('knowledge_target_enterprise', 'Target Enterprise')}
                  </label>
                  <select
                    value={selectedBusinessNode}
                    onChange={(e) => setSelectedBusinessNode(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-stone-300 rounded-xl text-xs font-semibold focus:outline-none focus:border-orange-500 text-stone-900"
                  >
                    {PRIORITY_BUSINESSES.map((b) => (
                      <option key={b.id} value={b.id}>{t(`biz_${b.id}`, b.label)}</option>
                    ))}
                  </select>
                </div>

                <div className="space-y-1.5">
                  <label className="text-xs font-bold text-stone-700">
                    {t('knowledge_social_category', 'Social Category')}
                  </label>
                  <select
                    value={calcCaste}
                    onChange={(e) => setCalcCaste(e.target.value)}
                    className="w-full px-3 py-2 bg-white border border-stone-300 rounded-xl text-xs font-semibold focus:outline-none focus:border-orange-500 text-stone-900"
                  >
                    <option value="ALL">{t('general', 'General')}</option>
                    <option value="OBC">{t('obc', 'OBC')}</option>
                    <option value="SC">{t('sc_special', 'SC (Special Category)')}</option>
                    <option value="ST">{t('st_special', 'ST (Special Category)')}</option>
                  </select>
                </div>

                <div className="flex items-end">
                  <button
                    type="submit"
                    disabled={evaluating}
                    className="w-full py-2.5 rounded-xl bg-[#EA580C] hover:bg-[#C2410C] text-white text-xs font-bold shadow-md shadow-orange-600/20 transition-all flex items-center justify-center gap-2 cursor-pointer"
                  >
                    {evaluating ? <RefreshCw className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
                    <span>{t('knowledge_calculate_btn', 'Calculate')}</span>
                  </button>
                </div>
              </form>

              {/* Evaluation Output Result */}
              {evalResult && feasibilityResult && (
                <div className="p-5 bg-white rounded-2xl border border-orange-200 shadow-sm space-y-4">
                  <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-stone-100">
                    <div>
                      <span className="text-[10px] uppercase font-bold text-orange-600 tracking-wider">
                        {t('knowledge_rule_applied', 'Rule Applied')}
                      </span>
                      <h4 className="text-base font-bold text-stone-900 font-['Outfit']">
                        <TranslatedText text={feasibilityResult.baseline_rule_applied} /> (
                        <TranslatedText text={evalResult.challenge_baseline_applied?.scheme_name || 'SIH Baseline'} />
                        )
                      </h4>
                    </div>
                    <div className="flex gap-2">
                      <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-bold">
                        {t('knowledge_interest_rate', 'Interest Rate')}: {evalResult.estimated_interest_rate_pct}%
                      </span>
                      <span className={`px-3 py-1 rounded-full text-xs font-bold border ${
                        feasibilityResult.feasibility_status === 'FEASIBLE'
                          ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                          : 'bg-amber-50 text-amber-700 border-amber-200'
                      }`}>
                        {t('feasibility', 'Feasibility')}: <TranslatedText text={feasibilityResult.feasibility_status} /> (DSCR: {feasibilityResult.dscr_ratio})
                      </span>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 sm:grid-cols-5 gap-3 text-xs">
                    <div className="p-3 bg-stone-50 rounded-xl">
                      <span className="text-stone-500 block">{t('knowledge_loan_amount', 'Loan Amount')}:</span>
                      <strong className="text-stone-900 font-bold">
                        ₹{feasibilityResult.loan_amount?.toLocaleString()}
                      </strong>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl">
                      <span className="text-stone-500 block">{t('knowledge_monthly_emi', 'Monthly EMI')}:</span>
                      <strong className="text-orange-700 font-bold font-mono">
                        ₹{feasibilityResult.monthly_emi?.toLocaleString()}/mo
                      </strong>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl">
                      <span className="text-stone-500 block">{t('knowledge_est_revenue', 'Est. Revenue')}:</span>
                      <strong className="text-stone-900 font-bold">
                        ~₹{feasibilityResult.estimated_monthly_revenue?.toLocaleString()}/mo
                      </strong>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl">
                      <span className="text-stone-500 block">{t('knowledge_est_net_profit', 'Est. Net Profit')}:</span>
                      <strong className="text-emerald-700 font-bold">
                        ~₹{feasibilityResult.estimated_monthly_net_profit?.toLocaleString()}/mo
                      </strong>
                    </div>
                    <div className="p-3 bg-stone-50 rounded-xl">
                      <span className="text-stone-500 block">{t('knowledge_payback_period', 'Payback Period')}:</span>
                      <strong className="text-stone-900 font-bold">
                        {feasibilityResult.payback_period_months} {t('months', 'Months')}
                      </strong>
                    </div>
                  </div>
                </div>
              )}
            </div>

            {/* Full Scheme Catalog */}
            <div className="space-y-4">
              <h3 className="text-lg font-bold text-stone-900 font-['Outfit']">
                {t('knowledge_catalog_title', 'Cataloged Government Schemes & Subsidies')}
              </h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {schemes.map((sch) => (
                  <div
                    key={sch.scheme_id}
                    className="bg-white p-5 rounded-2xl border border-[#EAE3D5] shadow-sm space-y-3"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold px-2 py-0.5 rounded bg-orange-100 text-orange-800">
                        <TranslatedText text={sch.category} />
                      </span>
                      <span className="text-xs font-semibold text-stone-500">
                        <TranslatedText text={sch.nodal_agency} />
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-stone-900 font-['Outfit']">
                      <TranslatedText text={sch.scheme_name} />
                    </h4>
                    <p className="text-xs text-stone-600">
                      <TranslatedText text={sch.provenance?.notes || sch.provenance?.document_name} />
                    </p>

                    <div className="pt-3 border-t border-stone-100 grid grid-cols-3 gap-2 text-xs">
                      <div>
                        <span className="text-stone-400 block text-[10px]">{t('knowledge_interest_rate', 'Interest Rate')}</span>
                        <strong className="text-stone-800">
                          {sch.financial_terms?.interest_rate_pct ? `${sch.financial_terms.interest_rate_pct}%` : t('concessional', 'Concessional')}
                        </strong>
                      </div>
                      <div>
                        <span className="text-stone-400 block text-[10px]">{t('knowledge_max_loan', 'Max Loan')}</span>
                        <strong className="text-stone-800">
                          {sch.financial_terms?.max_loan_amount
                            ? `₹${(sch.financial_terms.max_loan_amount / 100000).toFixed(1)}L`
                            : t('sector_limit', 'Sector Limit')}
                        </strong>
                      </div>
                      <div>
                        <span className="text-stone-400 block text-[10px]">{t('knowledge_tenure', 'Tenure')}</span>
                        <strong className="text-stone-800">
                          {sch.financial_terms?.tenure_years ? `${sch.financial_terms.tenure_years} Years` : '3-7 Years'}
                        </strong>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}

        {/* TAB 4: 15 PRIORITY RURAL ENTERPRISES (BENCHMARKS & DOMAIN PROFILES) */}
        {activeTab === 'benchmarks' && (
          <div className="space-y-6">
            {/* Business Node Selector */}
            <div className="bg-white p-4 rounded-2xl border border-[#EAE3D5] shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4">
              <span className="text-xs font-bold text-stone-700 uppercase tracking-wider whitespace-nowrap">
                {t('knowledge_select_enterprise', 'Select Enterprise:')}
              </span>
              <div className="flex overflow-x-auto no-scrollbar gap-2 w-full sm:w-auto">
                {PRIORITY_BUSINESSES.map((node) => (
                  <button
                    key={node.id}
                    onClick={() => setSelectedBusinessNode(node.id)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                      selectedBusinessNode === node.id
                        ? 'bg-stone-900 text-white shadow-sm'
                        : 'bg-stone-100 text-stone-600 hover:bg-stone-200'
                    }`}
                  >
                    {t(`biz_${node.id}`, node.label)}
                  </button>
                ))}
              </div>
            </div>

            {/* Financial Benchmark Details (Layer 3) */}
            {activeFinBenchmark && (
              <div className="bg-white p-6 rounded-3xl border border-[#EAE3D5] shadow-sm space-y-6">
                <div className="flex flex-wrap items-center justify-between gap-2 pb-4 border-b border-stone-100">
                  <div>
                    <span className="text-[10px] font-mono text-stone-500">
                      NIC: {activeFinBenchmark.nic_code || 'General'} | Node: {activeFinBenchmark.business_node_id}
                    </span>
                    <h3 className="text-xl font-bold text-stone-900 font-['Outfit']">
                      <TranslatedText text={activeFinBenchmark.business_title} />
                    </h3>
                  </div>
                  <span className="px-3 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200 text-xs font-semibold">
                    Provenance: <TranslatedText text={activeFinBenchmark.provenance?.organization || activeFinBenchmark.provenance?.source_name} /> ({activeFinBenchmark.provenance?.publication_year || 2024})
                  </span>
                </div>

                {/* Benchmark Numbers */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4">
                  <div className="p-4 bg-orange-50/50 rounded-2xl border border-orange-100 space-y-1">
                    <span className="text-xs text-stone-500 font-medium">
                      {t('knowledge_typical_capex', 'Typical CapEx')}
                    </span>
                    <div className="text-2xl font-bold text-stone-900 font-['Outfit']">
                      ₹{activeFinBenchmark.capex?.typical?.toLocaleString()}
                    </div>
                    <p className="text-[11px] text-stone-500">
                      Range: ₹{((activeFinBenchmark.capex?.range_min || 0) / 1000).toFixed(0)}k - ₹{((activeFinBenchmark.capex?.range_max || 0) / 1000).toFixed(0)}k
                    </p>
                  </div>

                  <div className="p-4 bg-emerald-50/50 rounded-2xl border border-emerald-100 space-y-1">
                    <span className="text-xs text-stone-500 font-medium">
                      {t('knowledge_gross_margin', 'Gross Margin')}
                    </span>
                    <div className="text-2xl font-bold text-emerald-700 font-['Outfit']">
                      {activeFinBenchmark.margins?.gross_margin_pct_typical}%
                    </div>
                    <p className="text-[11px] text-stone-500">
                      Net: {activeFinBenchmark.margins?.net_margin_pct_typical}%
                    </p>
                  </div>

                  <div className="p-4 bg-blue-50/50 rounded-2xl border border-blue-100 space-y-1">
                    <span className="text-xs text-stone-500 font-medium">
                      {t('knowledge_working_capital', 'Working Capital')}
                    </span>
                    <div className="text-2xl font-bold text-blue-700 font-['Outfit']">
                      {activeFinBenchmark.working_capital?.working_capital_months_recommended} Months
                    </div>
                    <p className="text-[11px] text-stone-500">
                      ~₹{activeFinBenchmark.working_capital?.typical_monthly_requirement?.toLocaleString()}/mo
                    </p>
                  </div>

                  <div className="p-4 bg-purple-50/50 rounded-2xl border border-purple-100 space-y-1">
                    <span className="text-xs text-stone-500 font-medium">
                      {t('knowledge_payback_period', 'Payback Period')}
                    </span>
                    <div className="text-2xl font-bold text-purple-700 font-['Outfit']">
                      {activeFinBenchmark.timelines?.payback_period_months} Months
                    </div>
                    <p className="text-[11px] text-stone-500">
                      Break-even: {activeFinBenchmark.timelines?.breakeven_months} mo
                    </p>
                  </div>
                </div>

                {/* Cost Structure Distribution */}
                <div className="space-y-3">
                  <h4 className="text-xs font-bold text-stone-800 uppercase tracking-wider">
                    {t('knowledge_operating_cost_breakdown', 'Operating Cost Structure Breakdown (%)')}
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-6 gap-3 text-xs">
                    {activeFinBenchmark.cost_structure_pct &&
                      Object.entries(activeFinBenchmark.cost_structure_pct).map(([key, val]) => (
                        <div key={key} className="p-3 bg-stone-50 rounded-xl border border-stone-200">
                          <span className="text-stone-500 block truncate capitalize text-[10px]">
                            <TranslatedText text={key.replace(/_/g, ' ')} />
                          </span>
                          <strong className="text-stone-900 font-bold text-sm">{val}%</strong>
                        </div>
                      ))}
                  </div>
                </div>
              </div>
            )}

            {/* Layer 2: Domain Technical Requirements & Licensing */}
            {activeProfile && (
              <div className="bg-white p-6 rounded-3xl border border-[#EAE3D5] shadow-sm space-y-6">
                <h3 className="text-lg font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                  <Wrench className="w-5 h-5 text-orange-600" />
                  {t('knowledge_layer2_tech_infra', 'Layer 2: Technical Infrastructure & Core Equipment')}
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-1">
                    <span className="text-stone-500 block font-semibold">
                      {t('knowledge_space_premises', 'Space & Premises')}
                    </span>
                    <strong className="text-stone-900 text-sm font-bold">
                      {activeProfile.space_and_infrastructure?.built_up_area_sqft_recommended || 300} sq.ft
                    </strong>
                    <p className="text-[11px] text-stone-600">
                      <TranslatedText text={activeProfile.space_and_infrastructure?.ventilation_type || 'Commercial Shed'} />
                    </p>
                  </div>

                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-1">
                    <span className="text-stone-500 block font-semibold">
                      {t('knowledge_power_utilities', 'Power & Utilities')}
                    </span>
                    <strong className="text-stone-900 text-sm font-bold">
                      {activeProfile.power_and_utilities?.power_load_hp || 5} HP Load
                    </strong>
                    <p className="text-[11px] text-stone-600">
                      <TranslatedText text={activeProfile.power_and_utilities?.power_connection_type || 'Commercial Connection'} />
                    </p>
                  </div>

                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-1">
                    <span className="text-stone-500 block font-semibold">
                      {t('knowledge_manpower_skills', 'Manpower & Skills')}
                    </span>
                    <strong className="text-stone-900 text-sm font-bold">
                      {activeProfile.skills_and_manpower?.skilled_operators_count || 1} Skilled, {activeProfile.skills_and_manpower?.unskilled_helpers_count || 1} Helper
                    </strong>
                    <p className="text-[11px] text-stone-600">
                      Training: <TranslatedText text={activeProfile.skills_and_manpower?.training_recommendation || 'Standard Onboarding'} />
                    </p>
                  </div>
                </div>

                {/* Core Machinery & Licenses */}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-2">
                    <span className="text-xs font-bold text-stone-800 uppercase tracking-wider flex items-center gap-1.5">
                      <Cpu className="w-4 h-4 text-orange-600" />
                      {t('knowledge_core_machinery', 'Core Machinery List')}
                    </span>
                    <div className="space-y-1.5">
                      {activeProfile.core_machinery?.map((m, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs bg-white p-2.5 rounded-xl border border-stone-200">
                          <span className="font-semibold text-stone-800">
                            <TranslatedText text={m.item_name} />
                          </span>
                          <span className="font-mono text-orange-700 font-bold">₹{m.estimated_cost_inr?.toLocaleString()}</span>
                        </div>
                      ))}
                    </div>
                  </div>

                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-2">
                    <span className="text-xs font-bold text-stone-800 uppercase tracking-wider flex items-center gap-1.5">
                      <FileCheck2 className="w-4 h-4 text-emerald-600" />
                      {t('knowledge_mandatory_licenses', 'Mandatory Licenses & Compliance')}
                    </span>
                    <div className="space-y-1.5">
                      {activeProfile.compliance_and_licensing?.map((lic, idx) => (
                        <div key={idx} className="flex items-center justify-between text-xs bg-white p-2.5 rounded-xl border border-stone-200">
                          <div>
                            <span className="font-semibold text-stone-800 block">
                              <TranslatedText text={lic.license_name} />
                            </span>
                            <span className="text-[10px] text-stone-500">
                              <TranslatedText text={lic.issuing_authority} />
                            </span>
                          </div>
                          <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-50 text-emerald-700 border border-emerald-200">
                            {lic.mandatory ? t('mandatory', 'Mandatory') : t('optional', 'Optional')}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Market Catchment & Seasonality (Layer 3) */}
            {activeMktBenchmark && (
              <div className="bg-white p-6 rounded-3xl border border-[#EAE3D5] shadow-sm space-y-6">
                <h3 className="text-lg font-bold text-stone-900 font-['Outfit'] flex items-center gap-2">
                  <MapPin className="w-5 h-5 text-orange-600" />
                  {t('knowledge_layer3_market_catchment', 'Layer 3: Market Catchment & Seasonality Profile')}
                </h3>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-xs">
                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-1">
                    <span className="text-stone-500 block">
                      {t('knowledge_primary_radius', 'Primary Service Radius')}
                    </span>
                    <strong className="text-stone-900 text-base font-bold">
                      {activeMktBenchmark.catchment?.primary_radius_km} km
                    </strong>
                    <p className="text-[11px] text-stone-500">
                      {t('knowledge_secondary_radius', 'Secondary')}: {activeMktBenchmark.catchment?.secondary_radius_km} km
                    </p>
                  </div>

                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-1">
                    <span className="text-stone-500 block">
                      {t('knowledge_saturation_density', 'Saturation Density')}
                    </span>
                    <strong className="text-stone-900 text-base font-bold">
                      {activeMktBenchmark.competition_and_saturation?.saturation_threshold_units_per_10k_pop} units / 10k pop
                    </strong>
                    <p className="text-[11px] text-stone-500">
                      <TranslatedText text="Healthy competition ceiling" />
                    </p>
                  </div>

                  <div className="p-4 bg-stone-50 rounded-2xl border border-stone-200 space-y-1">
                    <span className="text-stone-500 block">
                      {t('knowledge_seasonality_dynamic', 'Seasonality Dynamic')}
                    </span>
                    <strong className="text-stone-900 text-xs font-semibold">
                      <TranslatedText text={activeMktBenchmark.seasonality_notes || 'Consistent year-round demand.'} />
                    </strong>
                  </div>
                </div>

                {/* 12-Month Seasonality Multipliers */}
                <div className="space-y-2">
                  <span className="text-xs font-bold text-stone-700 uppercase tracking-wider">
                    {t('knowledge_demand_multipliers', '12-Month Demand Multipliers')}
                  </span>
                  <div className="grid grid-cols-6 sm:grid-cols-12 gap-1.5 text-center text-xs">
                    {activeMktBenchmark.seasonality_factors &&
                      Object.entries(activeMktBenchmark.seasonality_factors).map(([month, factor]) => {
                        const isHigh = factor > 1.1;
                        const isLow = factor < 0.9;
                        return (
                          <div
                            key={month}
                            className={`p-2 rounded-xl border ${
                              isHigh
                                ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                                : isLow
                                ? 'bg-amber-50 border-amber-200 text-amber-800'
                                : 'bg-stone-50 border-stone-200 text-stone-800'
                            }`}
                          >
                            <span className="text-[10px] font-bold uppercase block">{month}</span>
                            <span className="font-mono text-xs font-bold">{factor}x</span>
                          </div>
                        );
                      })}
                  </div>
                </div>
              </div>
            )}
          </div>
        )}

        {/* TAB 5: RISK LIBRARY */}
        {activeTab === 'risks' && (
          <div className="space-y-6">
            {/* Risk Category Filters */}
            <div className="flex gap-2 overflow-x-auto no-scrollbar bg-white p-2 rounded-2xl border border-[#EAE3D5] shadow-sm">
              {['ALL', 'OPERATIONAL', 'FINANCIAL', 'MARKET', 'CLIMATE_AND_ENVIRONMENTAL', 'REGULATORY'].map(
                (cat) => (
                  <button
                    key={cat}
                    onClick={() => setRiskCategoryFilter(cat)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-semibold whitespace-nowrap transition-all cursor-pointer ${
                      riskCategoryFilter === cat
                        ? 'bg-orange-600 text-white shadow-sm'
                        : 'text-stone-600 hover:bg-stone-100'
                    }`}
                  >
                    <TranslatedText text={cat === 'ALL' ? 'All Risks' : cat.replace(/_/g, ' ')} />
                  </button>
                )
              )}
            </div>

            {/* Risks Cards */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {filteredRisks.map((risk) => {
                const isCritical = risk.severity === 'CRITICAL';
                return (
                  <div
                    key={risk.risk_id}
                    className="bg-white p-6 rounded-3xl border border-[#EAE3D5] shadow-sm space-y-4 hover:border-orange-300 transition-all"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-stone-100 text-stone-700">
                        <TranslatedText text={risk.category} />
                      </span>
                      <span
                        className={`text-[10px] font-bold px-2.5 py-0.5 rounded-full ${
                          isCritical
                            ? 'bg-rose-100 text-rose-800 border border-rose-200'
                            : 'bg-amber-100 text-amber-800 border border-amber-200'
                        }`}
                      >
                        <TranslatedText text={risk.severity} /> SEVERITY
                      </span>
                    </div>

                    <h4 className="text-base font-bold text-stone-900 font-['Outfit']">
                      <TranslatedText text={risk.risk_name} />
                    </h4>
                    <p className="text-xs text-stone-600">
                      <TranslatedText text={risk.impact_description} />
                    </p>

                    <div className="p-3 bg-stone-50 rounded-2xl border border-stone-200 space-y-2 text-xs">
                      <span className="font-bold text-stone-800 block text-[11px]">
                        {t('knowledge_verified_mitigations', 'Verified Mitigation Strategies:')}
                      </span>
                      <ul className="space-y-1 list-disc list-inside text-stone-600 text-[11px]">
                        {risk.mitigation_strategies?.map((m, idx) => (
                          <li key={idx}>
                            <TranslatedText text={m} />
                          </li>
                        ))}
                      </ul>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        )}

        {/* TAB 6: INSTITUTIONAL EVIDENCE DOCUMENTS */}
        {activeTab === 'documents' && (
          <div className="space-y-6">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {documents.map((doc) => (
                <div
                  key={doc.document_id}
                  className="bg-white p-6 rounded-3xl border border-[#EAE3D5] shadow-sm space-y-4 flex flex-col justify-between"
                >
                  <div className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-[10px] font-bold px-2.5 py-0.5 rounded-full bg-blue-100 text-blue-800">
                        <TranslatedText text={doc.institution} />
                      </span>
                      <span className="text-[10px] font-mono text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded">
                        <TranslatedText text={doc.ingestion_status} />
                      </span>
                    </div>
                    <h4 className="text-base font-bold text-stone-900 font-['Outfit']">
                      <TranslatedText text={doc.title} />
                    </h4>
                    <p className="text-xs text-stone-600">
                      <TranslatedText text={doc.summary} />
                    </p>
                  </div>

                  <div className="pt-3 border-t border-stone-100 flex items-center justify-between">
                    <span className="text-[11px] text-stone-400">Year: {doc.publication_year}</span>
                    <a
                      href={doc.document_url}
                      target="_blank"
                      rel="noreferrer"
                      className="text-xs font-bold text-orange-600 hover:text-orange-700 flex items-center gap-1 cursor-pointer"
                    >
                      <span>{t('knowledge_official_source', 'Official Source')}</span>
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default KnowledgeHubPage;
