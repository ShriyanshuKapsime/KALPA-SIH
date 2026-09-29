import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  ShieldCheck,
  AlertTriangle,
  MapPin,
  IndianRupee,
  Briefcase,
  Layers,
  ArrowRight,
  ArrowLeft,
  Building2,
  TrendingUp,
  Cpu,
  ShieldAlert,
  Database,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage, TranslatedText } from '../../context/LanguageContext';
import AgenticWorkflowThread from '../../components/workflow/AgenticWorkflowThread';
import Badge from '../../components/ui/Badge';
import Button from '../../components/ui/Button';

export default function ProfilePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();
  const { language, t } = useLanguage();

  const {
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
    updateWorkflowState,
    markStageComplete
  } = useWorkflow();

  const sessionId = searchParams.get('sessionId') || searchParams.get('session_id') || searchParams.get('id') || ctxSessionId || '';
  const analysisIdParam = searchParams.get('analysisId') || searchParams.get('analysis_id') || ctxAnalysisId || '';

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (analysisIdParam) {
      loadProfileByAnalysisId(analysisIdParam);
    } else if (sessionId) {
      loadOrBuildProfile(sessionId);
    }
  }, [sessionId, analysisIdParam, language]);

  const loadOrBuildProfile = async (sid) => {
    setLoading(true);
    setError(null);
    try {
      // First try to get existing profile
      try {
        const existing = await apiService.profile.getProfileBySessionId(sid);
        if (existing && (existing.analysis_id || existing.id)) {
          setProfileData(existing);
          const aid = existing.analysis_id || existing.id;
          updateWorkflowState({
            sessionId: sid,
            analysisId: aid,
            businessName: existing.specific_business,
            currentStage: 3,
            completedStages: [1, 2, 3],
            nextStage: 4
          });
          markStageComplete(3, 4);
          setLoading(false);
          return;
        }
      } catch (e) {
        // If not found, build it
      }

      // Build canonical profile
      const built = await apiService.profile.buildProfile(sid);
      const prof = built?.profile || (built?.analysis_id ? built : null);
      if (prof) {
        setProfileData(prof);
        const aid = prof.analysis_id || prof.id;
        updateWorkflowState({
          sessionId: sid,
          analysisId: aid,
          businessName: prof.specific_business,
          currentStage: 3,
          completedStages: [1, 2, 3],
          nextStage: 4
        });
        markStageComplete(3, 4);
      }
    } catch (err) {
      console.error('Failed to load/build business profile:', err);
      setError(err.message || t('failedToGenerateProfile', 'Failed to generate canonical business profile.'));
    } finally {
      setLoading(false);
    }
  };

  const loadProfileByAnalysisId = async (aid) => {
    setLoading(true);
    setError(null);
    try {
      const data = await apiService.profile.getProfileByAnalysisId(aid);
      setProfileData(data);
    } catch (err) {
      console.error('Failed to load profile by analysis ID:', err);
      setError(err.message || t('failedToRetrieveProfile', 'Failed to retrieve profile.'));
    } finally {
      setLoading(false);
    }
  };

  const handleManualBuild = () => {
    if (sessionId) {
      loadOrBuildProfile(sessionId);
    }
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return t('notSpecified', 'Not specified');
    if (typeof val === 'number') {
      if (val >= 100000) {
        return `₹${(val / 100000).toFixed(2)} Lakhs (₹${val.toLocaleString('en-IN')})`;
      }
      return `₹${val.toLocaleString('en-IN')}`;
    }
    return `₹${val}`;
  };

  return (
    <div className="min-h-screen py-6 px-4 sm:px-6 lg:px-8 relative">
      <div className="max-w-5xl mx-auto space-y-8 relative z-10">
        {/* Agentic Workflow Thread */}
        <AgenticWorkflowThread currentStepNumber={2} className="mb-2" />

        {/* Page Heading */}
        <div className="space-y-2 text-center max-w-2xl mx-auto">
          <Badge variant="orange" className="mb-2">
            <Sparkles className="w-3 h-3 mr-1" /> {t('stage02ProfileUnderstanding', 'Stage 02 / Business Profile Understanding')}
          </Badge>
          <h1 className="text-3xl sm:text-4xl font-extrabold tracking-tight text-[#28231F] font-['Playfair_Display',Georgia,serif]">
            {t('canonicalBusinessProfile', 'Canonical Business Profile')}
          </h1>
          <p className="text-sm text-[#62584F]">
            {t('canonicalProfileSubtitle', 'Synthesized enterprise identity aligning verified multi-lingual intake and official MoSPI NIC classification.')}
          </p>
        </div>

        {/* Loading State */}
        {loading && (
          <div className="rounded-3xl p-8 sm:p-12 text-center space-y-4 max-w-xl mx-auto border border-[#79563F]/20 shadow-sm bg-[#F1E4CC]">
            <div className="relative w-16 h-16 mx-auto">
              <div className="w-16 h-16 rounded-full border-4 border-[#79563F]/20 border-t-[#C96A3A] animate-spin" />
              <RefreshCw className="w-6 h-6 text-[#C96A3A] absolute inset-0 m-auto" />
            </div>
            <div className="space-y-2">
              <h3 className="text-lg font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                {t('assemblingCanonicalProfile', 'Assembling Canonical Business Profile...')}
              </h3>
              <p className="text-xs text-[#62584F] max-w-md mx-auto">
                {t('mergingStageIntakeIntelligence', 'Merging Stage 1 multi-lingual intake, Stage 2 official NIC taxonomy, and KALPA Business Ontology intelligence.')}
              </p>
            </div>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="max-w-xl mx-auto p-6 rounded-3xl bg-rose-50/80 border border-rose-300 text-rose-900 my-8 shadow-sm space-y-3">
            <div className="flex items-center gap-2 font-bold text-rose-950">
              <AlertTriangle className="w-5 h-5 text-rose-600" />
              <span>{t('failedToLoadProfile', 'Failed to Load Business Profile')}</span>
            </div>
            <p className="text-xs text-rose-800">{error}</p>
            <div className="flex gap-3 pt-2">
              <Button size="sm" onClick={handleManualBuild} icon={RefreshCw}>
                {t('retryBuildingProfile', 'Retry Building Profile')}
              </Button>
              <Button size="sm" variant="outline" onClick={() => navigate('/intake')}>
                {t('returnToIntake', 'Return to Intake')}
              </Button>
            </div>
          </div>
        )}

        {/* Empty / Not Built State */}
        {!loading && !error && !profileData && (
          <div className="max-w-xl mx-auto text-center py-12 px-6 bg-[#F1E4CC] rounded-3xl border border-[#79563F]/20 shadow-sm space-y-4 my-8">
            <div className="w-16 h-16 mx-auto rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 flex items-center justify-center text-[#C96A3A]">
              <FileText className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
              {t('createCanonicalProfile', 'Create Canonical Business Profile')}
            </h3>
            <p className="text-xs text-[#62584F] max-w-md mx-auto">
              {t('synthesizeStageIntakeDescription', 'Synthesize Stage 1 multi-lingual user inputs and Stage 2 NIC classification into the verified profile for KALPA.')}
            </p>
            <Button
              size="md"
              onClick={handleManualBuild}
              icon={Sparkles}
            >
              {t('createBusinessProfile', 'Create Business Profile')}
            </Button>
          </div>
        )}

        {/* Active Profile Display */}
        {!loading && profileData && (
          <div className="space-y-8 animate-fadeIn">
            {/* Hero Header Banner */}
            <div className="p-6 sm:p-8 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm relative overflow-hidden">
              <div className="flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-[#28231F] font-['Playfair_Display',Georgia,serif] tracking-tight">
                    <TranslatedText text={profileData.business_profile?.specific_business || profileData.business_profile?.original_concept || 'Rural Enterprise'} />
                  </h2>
                  <p className="text-xs sm:text-sm text-[#62584F] mt-1.5 font-medium">
                    {t('sector', 'Sector')}: <strong className="font-semibold text-[#28231F]"><TranslatedText text={profileData.business_profile?.sector || 'Agriculture & Allied'} /></strong> • {t('category', 'Category')}:{' '}
                    <strong className="font-semibold text-[#28231F]"><TranslatedText text={profileData.business_profile?.category || 'Dairy'} /></strong>
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  <div className="bg-[#FAF2E3] border border-[#79563F]/20 px-4 py-3 rounded-2xl shadow-2xs">
                    <div className="text-[10px] uppercase tracking-wider font-bold text-[#79563F]">{t('officialNicCode', 'Official NIC Code')}</div>
                    <div className="text-2xl font-black text-[#28231F] font-mono tracking-wider mt-0.5">
                      {profileData.business_profile?.nic?.code || 'N/A'}
                    </div>
                  </div>

                  <div className="bg-[#FAF2E3] border border-[#79563F]/20 px-4 py-3 rounded-2xl shadow-2xs">
                    <div className="text-[10px] uppercase tracking-wider font-bold text-[#79563F]">{t('classificationConfidence', 'Classification Confidence')}</div>
                    <div className="text-2xl font-black text-[#28231F] flex items-center gap-1.5 mt-0.5">
                      <ShieldCheck className="w-5 h-5 text-[#006F5F]" />
                      <span>{Math.round((profileData.business_profile?.nic?.confidence || 0.9) * 100)}%</span>
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-[#79563F]/15 gap-2 overflow-x-auto pb-1">
              {[
                { id: 'overview', label: t('overviewIdentity', 'Overview & Identity'), icon: Building2 },
                { id: 'analysis', label: t('analysisRequirements', 'Analysis Requirements'), icon: TrendingUp },
                { id: 'readiness', label: t('dataQualityReadiness', 'Data Quality & Readiness'), icon: ShieldAlert },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs sm:text-sm font-bold transition whitespace-nowrap cursor-pointer ${
                      isActive
                        ? 'bg-[#C96A3A] text-white shadow-sm'
                        : 'bg-[#FAF2E3]/60 text-[#79563F] hover:bg-[#FAF2E3] hover:text-[#28231F]'
                    }`}
                  >
                    <Icon className="w-4 h-4" />
                    <span>{tab.label}</span>
                  </button>
                );
              })}
            </div>

            {/* TAB 1: Overview & Identity */}
            {activeTab === 'overview' && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* 1. Business Identity Card */}
                <div className="p-6 sm:p-7 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-4">
                  <div className="flex items-center gap-2.5 text-[#28231F] font-bold border-b border-[#79563F]/15 pb-3">
                    <Building2 className="w-5 h-5 text-[#C96A3A]" />
                    <h3 className="text-base font-['Playfair_Display',Georgia,serif]">{t('businessIdentityTitle', '1. Business Identity')}</h3>
                  </div>

                  <div className="space-y-3.5 text-xs sm:text-sm">
                    <div>
                      <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('specificBusiness', 'Specific Business')}</span>
                      <span className="font-extrabold text-base text-[#28231F]"><TranslatedText text={profileData.business_profile?.specific_business} /></span>
                    </div>

                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('sector', 'Sector')}</span>
                        <span className="font-semibold text-xs text-[#28231F]"><TranslatedText text={profileData.business_profile?.sector} /></span>
                      </div>
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('subcategory', 'Sub-Category')}</span>
                        <span className="font-semibold text-xs text-[#28231F]"><TranslatedText text={profileData.business_profile?.sub_category || 'General'} /></span>
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15">
                      <span className="text-[#79563F] block text-[10px] uppercase font-bold mb-1">{t('officialNicActivity', 'Official NIC Activity')}</span>
                      <div className="font-mono text-xs text-[#28231F]">
                        <span className="font-bold text-[#C96A3A] mr-2">[{profileData.business_profile?.nic?.code}]</span>
                        <TranslatedText text={profileData.business_profile?.nic?.description} />
                      </div>
                    </div>

                    {profileData.business_profile?.products?.length > 0 && (
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold mb-1.5">{t('products', 'Products')}</span>
                        <div className="flex flex-wrap gap-1.5">
                          {profileData.business_profile.products.map((p, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-[#FAF2E3] text-[#4A3427] text-xs font-medium border border-[#79563F]/15">
                              <TranslatedText text={p} />
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. Entrepreneur Profile Card */}
                <div className="p-6 sm:p-7 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-4">
                  <div className="flex items-center gap-2.5 text-[#28231F] font-bold border-b border-[#79563F]/15 pb-3">
                    <Briefcase className="w-5 h-5 text-[#C96A3A]" />
                    <h3 className="text-base font-['Playfair_Display',Georgia,serif]">{t('entrepreneurProfileTitle', '2. Entrepreneur Profile')}</h3>
                  </div>

                  <div className="space-y-3.5 text-xs sm:text-sm">
                    <div>
                      <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('businessStage', 'Business Stage')}</span>
                      <span className="font-semibold text-xs text-[#28231F] capitalize">
                        <TranslatedText text={profileData.entrepreneur_profile?.business_stage?.replace('_', ' ') || 'Planning'} />
                      </span>
                    </div>

                    <div>
                      <span className="text-[#92745A] block text-[10px] uppercase font-bold mb-1.5">{t('skillsBackground', 'Skills & Background')}</span>
                      {profileData.entrepreneur_profile?.skills?.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {profileData.entrepreneur_profile.skills.map((s, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-[#FAF2E3] text-[#4A3427] text-xs font-medium border border-[#79563F]/15">
                              <TranslatedText text={s} />
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-[#92745A] italic text-xs">{t('noPriorExperienceRequired', 'No prior experience required / unspecified')}</span>
                      )}
                    </div>

                    {profileData.entrepreneur_profile?.experience?.length > 0 && (
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold mb-1">{t('priorExperience', 'Prior Experience')}</span>
                        <p className="text-[#62584F] text-xs"><TranslatedText text={profileData.entrepreneur_profile.experience.join(', ')} /></p>
                      </div>
                    )}

                    <div>
                      <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('languageProvenance', 'Language & Provenance')}</span>
                      <span className="font-semibold text-xs text-[#28231F]">
                        {profileData.provenance?.language?.toUpperCase()} ({profileData.provenance?.input_mode || 'text'})
                      </span>
                    </div>
                  </div>
                </div>

                {/* 3. Location Profile Card */}
                <div className="p-6 sm:p-7 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-4">
                  <div className="flex items-center gap-2.5 text-[#28231F] font-bold border-b border-[#79563F]/15 pb-3">
                    <MapPin className="w-5 h-5 text-[#C96A3A]" />
                    <h3 className="text-base font-['Playfair_Display',Georgia,serif]">{t('locationProfileTitle', '3. Location Profile')}</h3>
                  </div>

                  <div className="space-y-3.5 text-xs sm:text-sm">
                    <div className="grid grid-cols-2 gap-3">
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('district', 'District')}</span>
                        <span className="font-semibold text-xs text-[#28231F]"><TranslatedText text={profileData.location_profile?.district || 'Not specified'} /></span>
                      </div>
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('state', 'State')}</span>
                        <span className="font-semibold text-xs text-[#28231F]"><TranslatedText text={profileData.location_profile?.state || 'India'} /></span>
                      </div>
                    </div>

                    <div>
                      <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('proposedVillagePlace', 'Proposed Village / Place')}</span>
                      <span className="font-semibold text-xs text-[#28231F]"><TranslatedText text={profileData.location_profile?.name || 'Local rural cluster'} /></span>
                    </div>

                    <div className="flex items-center justify-between p-3 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 text-xs">
                      <div>
                        <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('coordinates', 'Coordinates')}</span>
                        <span className="font-mono text-xs text-[#28231F]">
                          {profileData.location_profile?.coordinates?.latitude
                            ? `${profileData.location_profile.coordinates.latitude.toFixed(4)}, ${profileData.location_profile.coordinates.longitude.toFixed(4)}`
                            : t('derivedFromDistrict', 'Derived from district')}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-[#F1E4CC] text-[#79563F] border border-[#79563F]/20">
                        {t('source', 'Source')}: {profileData.location_profile?.source || 'User'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 4. Financial Profile Card */}
                <div className="p-6 sm:p-7 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-4">
                  <div className="flex items-center gap-2.5 text-[#28231F] font-bold border-b border-[#79563F]/15 pb-3">
                    <IndianRupee className="w-5 h-5 text-[#C96A3A]" />
                    <h3 className="text-base font-['Playfair_Display',Georgia,serif]">{t('financialProfileTitle', '4. Financial Profile')}</h3>
                  </div>

                  <div className="space-y-3.5 text-xs sm:text-sm">
                    <div>
                      <span className="text-[#92745A] block text-[10px] uppercase font-bold">{t('declaredAvailableCapital', 'Declared Available Capital')}</span>
                      <div className="text-2xl font-black text-[#28231F] mt-1 font-mono">
                        {formatCurrency(profileData.financial_profile?.available_capital)}
                      </div>
                    </div>

                    <div className="p-3.5 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 text-xs text-[#62584F]">
                      <span className="font-bold text-[#79563F] block mb-0.5">{t('capitalAssessment', 'Capital Assessment')}</span>
                      {t('capitalAssessmentNote', 'This capital figure is locked into the canonical profile for downstream Stage 5 Feasibility and Stage 6 DPR debt/equity structuring.')}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Analysis Requirements */}
            {activeTab === 'analysis' && (
              <div className="space-y-6">
                <div className="p-6 sm:p-7 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-5">
                  <div className="flex items-center gap-2.5 text-[#28231F] font-bold border-b border-[#79563F]/15 pb-3">
                    <Cpu className="w-5 h-5 text-[#C96A3A]" />
                    <h3 className="text-base font-['Playfair_Display',Georgia,serif]">{t('downstreamMarketIntelRequirements', 'Downstream Market Intelligence Requirements (Ontology-Guided)')}</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-xs">
                    {/* Direct Competitors */}
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 space-y-2">
                      <span className="text-[#79563F] font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-[#C96A3A]" />
                        {t('directCompetitorsToMap', 'Direct Competitors to Map')}
                      </span>
                      <ul className="list-disc list-inside text-[#28231F] space-y-1">
                        {profileData.analysis_requirements?.direct_competitors?.map((item, idx) => (
                          <li key={idx}><TranslatedText text={item} /></li>
                        ))}
                      </ul>
                    </div>

                    {/* Adjacent & Substitutes */}
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 space-y-2">
                      <span className="text-[#79563F] font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-[#C96A3A]" />
                        {t('substituteAdjacentBusinesses', 'Substitute & Adjacent Businesses')}
                      </span>
                      <ul className="list-disc list-inside text-[#28231F] space-y-1">
                        {profileData.analysis_requirements?.substitute_businesses?.map((item, idx) => (
                          <li key={idx}><TranslatedText text={item} /></li>
                        ))}
                      </ul>
                    </div>

                    {/* Demand Features */}
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 space-y-2">
                      <span className="text-[#79563F] font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-[#006F5F]" />
                        {t('keyDemandDrivers', 'Key Demand Drivers')}
                      </span>
                      <ul className="list-disc list-inside text-[#28231F] space-y-1">
                        {profileData.analysis_requirements?.demand_features?.map((item, idx) => (
                          <li key={idx}><TranslatedText text={item} /></li>
                        ))}
                      </ul>
                    </div>

                    {/* Infrastructure */}
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 space-y-2">
                      <span className="text-[#79563F] font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-[#79563F]" />
                        {t('infrastructureRequirements', 'Infrastructure Requirements')}
                      </span>
                      <ul className="list-disc list-inside text-[#28231F] space-y-1">
                        {profileData.analysis_requirements?.infrastructure_requirements?.map((item, idx) => (
                          <li key={idx}><TranslatedText text={item} /></li>
                        ))}
                      </ul>
                    </div>

                    {/* Risk Factors */}
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 space-y-2">
                      <span className="text-[#79563F] font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5 text-[#92745A]" />
                        {t('primaryRiskFactors', 'Primary Risk Factors')}
                      </span>
                      <ul className="list-disc list-inside text-[#28231F] space-y-1">
                        {profileData.analysis_requirements?.risk_factors?.map((item, idx) => (
                          <li key={idx}><TranslatedText text={item} /></li>
                        ))}
                      </ul>
                    </div>

                    {/* Required Datasets */}
                    <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15 space-y-2">
                      <span className="text-[#79563F] font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5 text-[#79563F]" />
                        {t('requiredVerifiedDatasets', 'Required Verified Datasets')}
                      </span>
                      <ul className="list-disc list-inside text-[#28231F] space-y-1">
                        {profileData.analysis_requirements?.required_datasets?.map((item, idx) => (
                          <li key={idx}><TranslatedText text={item} /></li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: Data Quality & Readiness */}
            {activeTab === 'readiness' && (
              <div className="p-6 sm:p-7 rounded-3xl bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm space-y-6">
                <div className="flex items-center gap-2.5 text-[#28231F] font-bold border-b border-[#79563F]/15 pb-3">
                  <ShieldAlert className="w-5 h-5 text-[#C96A3A]" />
                  <h3 className="text-base font-['Playfair_Display',Georgia,serif]">{t('dataQualityValidationAudit', 'Data Quality & Validation Audit')}</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15">
                    <span className="text-[10px] uppercase font-bold text-[#92745A]">{t('validationStatus', 'Validation Status')}</span>
                    <div className="text-lg font-black text-[#006F5F] mt-1">
                      {profileData.data_quality?.validation_status || 'PASSED'}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15">
                    <span className="text-[10px] uppercase font-bold text-[#92745A]">{t('completeness', 'Completeness')}</span>
                    <div className="text-lg font-black text-[#28231F] mt-1">
                      {profileData.data_quality?.profile_complete ? t('oneHundredPercentComplete', '100% Complete') : t('incomplete', 'Incomplete')}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/15">
                    <span className="text-[10px] uppercase font-bold text-[#92745A]">{t('warningsCount', 'Warnings Count')}</span>
                    <div className="text-lg font-black text-[#28231F] mt-1">
                      {profileData.data_quality?.warnings?.length || 0}
                    </div>
                  </div>
                </div>

                {profileData.data_quality?.warnings?.length > 0 && (
                  <div className="p-4 rounded-2xl bg-[#FAF2E3] border border-[#79563F]/20 text-[#79563F] space-y-2">
                    <span className="font-bold text-xs uppercase tracking-wider block text-[#28231F]">{t('auditWarnings', 'Audit Warnings')}</span>
                    <ul className="list-disc list-inside text-xs space-y-1">
                      {profileData.data_quality.warnings.map((w, idx) => (
                        <li key={idx}><TranslatedText text={w} /></li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* Bottom Actions / Transition to Stage 3 KALPA Manager */}
            <div className="rounded-3xl p-6 bg-[#F1E4CC] border border-[#79563F]/20 shadow-sm flex flex-col sm:flex-row items-center justify-between gap-4 mt-8">
              <div className="space-y-1 text-center sm:text-left">
                <div className="flex items-center gap-2 justify-center sm:justify-start">
                  <span className="inline-flex items-center gap-1.5 text-[10px] uppercase font-bold tracking-wider px-2.5 py-0.5 rounded-full bg-[#FAF2E3] text-[#006F5F] border border-[#006F5F]/25">
                    <ShieldCheck className="w-3.5 h-3.5 text-[#006F5F]" />
                    {t('stage2CompleteReady', 'Stage 2 Complete · Ready for KALPA Manager')}
                  </span>
                </div>
                <h4 className="text-lg font-bold text-[#28231F] font-['Playfair_Display',Georgia,serif]">
                  {t('readyForAutonomousIntelligence', 'Ready for Autonomous Livelihood Intelligence')}
                </h4>
                <p className="text-xs text-[#62584F] max-w-lg leading-relaxed">
                  {t('canonicalProfileVerifiedNext', 'Canonical profile verified. Next: Stage 3 KALPA Manager orchestrates market, finance, and DPR advisory.')}
                </p>
              </div>

              <div className="flex items-center gap-3 flex-shrink-0">
                <Button
                  size="md"
                  onClick={() => navigate('/orchestrator', {
                    state: {
                      sessionId: profileData.session_id,
                      analysisId: profileData.analysis_id
                    }
                  })}
                  className="saffron-gradient-btn text-white font-bold shadow-md"
                  icon={ArrowRight}
                >
                  {t('continueToKalpaManager', 'Continue to KALPA Manager')}
                </Button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
