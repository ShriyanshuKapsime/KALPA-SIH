import React, { useState, useEffect } from 'react';
import { useSearchParams, useNavigate, Link } from 'react-router-dom';
import {
  FileText,
  CheckCircle2,
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
  Lock,
  Copy,
  Check,
  RefreshCw,
  Sparkles
} from 'lucide-react';
import apiService from '../../services/api';

export default function ProfilePage() {
  const [searchParams] = useSearchParams();
  const navigate = useNavigate();

  const sessionId = searchParams.get('sessionId') || searchParams.get('session_id') || searchParams.get('id');
  const analysisIdParam = searchParams.get('analysisId') || searchParams.get('analysis_id');

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [profileData, setProfileData] = useState(null);
  const [copied, setCopied] = useState(false);
  const [activeTab, setActiveTab] = useState('overview');

  useEffect(() => {
    if (analysisIdParam) {
      loadProfileByAnalysisId(analysisIdParam);
    } else if (sessionId) {
      loadOrBuildProfile(sessionId);
    }
  }, [sessionId, analysisIdParam]);

  const loadOrBuildProfile = async (sid) => {
    setLoading(true);
    setError(null);
    try {
      // First try to get existing profile
      try {
        const existing = await apiService.profile.getProfileBySessionId(sid);
        if (existing && existing.analysis_id) {
          setProfileData(existing);
          setLoading(false);
          return;
        }
      } catch (e) {
        // If not found, build it
      }

      // Build canonical profile
      const built = await apiService.profile.buildProfile(sid);
      if (built && built.profile) {
        setProfileData(built.profile);
      } else if (built && built.analysis_id) {
        setProfileData(built);
      }
    } catch (err) {
      console.error('Failed to load/build business profile:', err);
      setError(err.message || 'Failed to generate canonical business profile.');
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
      setError(err.message || 'Failed to retrieve profile.');
    } finally {
      setLoading(false);
    }
  };

  const handleManualBuild = () => {
    if (sessionId) {
      loadOrBuildProfile(sessionId);
    }
  };

  const copyAnalysisId = () => {
    if (profileData?.analysis_id) {
      navigator.clipboard.writeText(profileData.analysis_id);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const formatCurrency = (val) => {
    if (val === null || val === undefined) return 'Not specified';
    if (typeof val === 'number') {
      if (val >= 100000) {
        return `₹${(val / 100000).toFixed(2)} Lakhs (₹${val.toLocaleString('en-IN')})`;
      }
      return `₹${val.toLocaleString('en-IN')}`;
    }
    return `₹${val}`;
  };

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#1C1917] font-sans pb-24">
      {/* Top Header & Breadcrumb */}
      <div className="border-b border-[#E7E5E4] bg-white/70 backdrop-blur-md sticky top-0 z-30">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 py-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={() => navigate(-1)}
              className="p-2 rounded-xl border border-stone-200 hover:bg-stone-50 text-stone-600 transition"
              title="Go back"
            >
              <ArrowLeft className="w-4 h-4" />
            </button>
            <div>
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold uppercase tracking-wider text-[#C2410C] bg-orange-50 px-2 py-0.5 rounded border border-orange-200">
                  Stage 03
                </span>
                <span className="text-xs text-stone-400">/</span>
                <span className="text-xs font-semibold text-stone-600">Structured Profile Store</span>
              </div>
              <h1 className="text-lg sm:text-xl font-bold text-stone-900 tracking-tight">
                Canonical Business Profile
              </h1>
            </div>
          </div>

          {profileData && (
            <div className="flex items-center gap-3">
              <div className="hidden sm:flex items-center gap-1.5 bg-stone-100 border border-stone-200 px-3 py-1.5 rounded-xl text-xs font-mono text-stone-700">
                <span className="text-stone-400">ID:</span>
                <span>{profileData.analysis_id?.slice(0, 8)}...</span>
                <button
                  type="button"
                  onClick={copyAnalysisId}
                  className="ml-1 text-stone-500 hover:text-stone-900"
                  title="Copy Full Analysis ID"
                >
                  {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                </button>
              </div>

              <span
                className={`inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-bold border ${
                  profileData.workflow?.state === 'BUSINESS_PROFILE_READY'
                    ? 'bg-emerald-50 text-emerald-800 border-emerald-300'
                    : 'bg-amber-50 text-amber-800 border-amber-300'
                }`}
              >
                <span
                  className={`w-2 h-2 rounded-full ${
                    profileData.workflow?.state === 'BUSINESS_PROFILE_READY' ? 'bg-emerald-500 animate-pulse' : 'bg-amber-500'
                  }`}
                />
                {profileData.workflow?.state || 'READY'}
              </span>
            </div>
          )}
        </div>
      </div>

      {/* Main Container */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 pt-8">
        {/* Loading State */}
        {loading && (
          <div className="py-20 flex flex-col items-center justify-center text-center">
            <div className="w-16 h-16 rounded-2xl bg-orange-100 border border-orange-300 flex items-center justify-center text-[#C2410C] animate-spin mb-4">
              <RefreshCw className="w-8 h-8" />
            </div>
            <h3 className="text-lg font-bold text-stone-900">Assembling Canonical Business Profile...</h3>
            <p className="text-sm text-stone-500 max-w-md mt-1">
              Merging Stage 1 verified intake, Stage 2 official NIC taxonomy, and KALPA Business Ontology intelligence.
            </p>
          </div>
        )}

        {/* Error State */}
        {!loading && error && (
          <div className="max-w-xl mx-auto p-6 rounded-3xl bg-red-50 border border-red-200 text-red-900 my-8 shadow-sm">
            <div className="flex items-center gap-3 mb-2 font-bold">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              <span>Failed to Load Business Profile</span>
            </div>
            <p className="text-sm text-red-700 mb-4">{error}</p>
            <div className="flex gap-3">
              <button
                type="button"
                onClick={handleManualBuild}
                className="px-4 py-2 rounded-xl bg-red-600 text-white text-xs font-bold hover:bg-red-700 transition"
              >
                Retry Building Profile
              </button>
              <Link
                to="/intake"
                className="px-4 py-2 rounded-xl bg-white border border-red-300 text-red-800 text-xs font-bold hover:bg-red-50 transition"
              >
                Return to Intake
              </Link>
            </div>
          </div>
        )}

        {/* Empty / Not Built State */}
        {!loading && !error && !profileData && (
          <div className="max-w-xl mx-auto text-center py-16 px-6 bg-white rounded-3xl border border-stone-200 shadow-sm my-8">
            <div className="w-16 h-16 mx-auto rounded-3xl bg-orange-50 border border-orange-200 flex items-center justify-center text-[#C2410C] mb-4">
              <FileText className="w-8 h-8" />
            </div>
            <h3 className="text-xl font-bold text-stone-900 mb-2">Create Canonical Business Profile</h3>
            <p className="text-sm text-stone-600 mb-6">
              Synthesize Stage 1 multi-lingual user inputs and Stage 2 NIC classification into the single source of truth for KALPA.
            </p>
            <button
              type="button"
              onClick={handleManualBuild}
              className="inline-flex items-center gap-2 px-6 py-3 rounded-2xl bg-[#C2410C] text-white font-bold text-sm shadow-md hover:bg-[#9A3412] transition"
            >
              <Sparkles className="w-4 h-4" />
              <span>Create Business Profile</span>
            </button>
          </div>
        )}

        {/* Active Profile Display */}
        {!loading && profileData && (
          <div className="space-y-8 animate-fadeIn">
            {/* Hero Header Banner */}
            <div className="p-6 sm:p-8 rounded-3xl bg-gradient-to-br from-[#FFFBF5] to-[#FDF4E7] border border-[#FED7AA] shadow-sm relative overflow-hidden">
              <div className="absolute right-0 top-0 w-80 h-80 bg-orange-200/20 rounded-full blur-3xl pointer-events-none" />

              <div className="relative z-10 flex flex-col md:flex-row md:items-center justify-between gap-6">
                <div>
                  <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-white/80 border border-orange-200 text-[#C2410C] text-xs font-bold mb-3 shadow-xs">
                    <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
                    <span>Single Source of Truth • Schema v{profileData.schema_version}</span>
                  </div>
                  <h2 className="text-2xl sm:text-3xl font-extrabold text-stone-900 tracking-tight">
                    {profileData.business_profile?.specific_business || profileData.business_profile?.original_concept || 'Rural Enterprise'}
                  </h2>
                  <p className="text-sm text-stone-600 mt-1 max-w-2xl">
                    Sector: <span className="font-semibold text-stone-800">{profileData.business_profile?.sector}</span> • Category:{' '}
                    <span className="font-semibold text-stone-800">{profileData.business_profile?.category}</span>
                  </p>
                </div>

                <div className="flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
                  <div className="bg-white/90 border border-orange-200 px-4 py-3 rounded-2xl shadow-xs">
                    <div className="text-[11px] uppercase tracking-wider font-bold text-stone-500">Official NIC Code</div>
                    <div className="text-xl font-extrabold text-[#C2410C] font-mono">
                      {profileData.business_profile?.nic?.code || 'N/A'}
                    </div>
                  </div>

                  <div className="bg-white/90 border border-orange-200 px-4 py-3 rounded-2xl shadow-xs">
                    <div className="text-[11px] uppercase tracking-wider font-bold text-stone-500">Classification Confidence</div>
                    <div className="text-xl font-extrabold text-emerald-700">
                      {Math.round((profileData.business_profile?.nic?.confidence || 0.9) * 100)}%
                    </div>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="flex border-b border-stone-200 gap-2 overflow-x-auto pb-1">
              {[
                { id: 'overview', label: 'Overview & Identity', icon: Building2 },
                { id: 'analysis', label: 'Analysis Requirements', icon: TrendingUp },
                { id: 'readiness', label: 'Data Quality & Readiness', icon: ShieldAlert },
                { id: 'json', label: 'Raw Canonical JSON', icon: Database },
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    type="button"
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2.5 rounded-2xl text-xs sm:text-sm font-bold transition whitespace-nowrap ${
                      isActive
                        ? 'bg-[#C2410C] text-white shadow-sm'
                        : 'text-stone-600 hover:text-stone-900 hover:bg-stone-100'
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
                <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-xs space-y-4">
                  <div className="flex items-center gap-2.5 text-stone-900 font-bold border-b border-stone-100 pb-3">
                    <Building2 className="w-5 h-5 text-[#C2410C]" />
                    <h3 className="text-base">1. Business Identity</h3>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm">
                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold">Specific Business</span>
                      <span className="font-semibold text-stone-800">{profileData.business_profile?.specific_business}</span>
                    </div>

                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <span className="text-stone-400 block text-[11px] uppercase font-bold">Sector</span>
                        <span className="font-medium text-stone-700">{profileData.business_profile?.sector}</span>
                      </div>
                      <div>
                        <span className="text-stone-400 block text-[11px] uppercase font-bold">Sub-Category</span>
                        <span className="font-medium text-stone-700">{profileData.business_profile?.sub_category || 'General'}</span>
                      </div>
                    </div>

                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold">Official NIC Activity</span>
                      <div className="mt-1 p-2.5 rounded-xl bg-stone-50 border border-stone-100 font-mono text-xs text-stone-800">
                        <span className="font-bold text-[#C2410C] mr-2">[{profileData.business_profile?.nic?.code}]</span>
                        {profileData.business_profile?.nic?.description}
                      </div>
                    </div>

                    {profileData.business_profile?.products?.length > 0 && (
                      <div>
                        <span className="text-stone-400 block text-[11px] uppercase font-bold mb-1.5">Products</span>
                        <div className="flex flex-wrap gap-1.5">
                          {profileData.business_profile.products.map((p, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-orange-50 text-[#C2410C] text-xs font-medium border border-orange-100">
                              {p}
                            </span>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>

                {/* 2. Entrepreneur Profile Card */}
                <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-xs space-y-4">
                  <div className="flex items-center gap-2.5 text-stone-900 font-bold border-b border-stone-100 pb-3">
                    <Briefcase className="w-5 h-5 text-[#C2410C]" />
                    <h3 className="text-base">2. Entrepreneur Profile</h3>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm">
                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold">Business Stage</span>
                      <span className="font-semibold text-stone-800 capitalize">
                        {profileData.entrepreneur_profile?.business_stage?.replace('_', ' ') || 'Planning'}
                      </span>
                    </div>

                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold mb-1.5">Skills & Background</span>
                      {profileData.entrepreneur_profile?.skills?.length > 0 ? (
                        <div className="flex flex-wrap gap-1.5">
                          {profileData.entrepreneur_profile.skills.map((s, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-lg bg-stone-100 text-stone-800 text-xs font-medium border border-stone-200">
                              {s}
                            </span>
                          ))}
                        </div>
                      ) : (
                        <span className="text-stone-500 italic text-xs">No prior experience required / unspecified</span>
                      )}
                    </div>

                    {profileData.entrepreneur_profile?.experience?.length > 0 && (
                      <div>
                        <span className="text-stone-400 block text-[11px] uppercase font-bold mb-1">Prior Experience</span>
                        <p className="text-stone-700 text-xs">{profileData.entrepreneur_profile.experience.join(', ')}</p>
                      </div>
                    )}

                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold">Language & Provenance</span>
                      <span className="font-medium text-stone-700">
                        {profileData.provenance?.language?.toUpperCase()} ({profileData.provenance?.input_mode || 'text'})
                      </span>
                    </div>
                  </div>
                </div>

                {/* 3. Location Profile Card */}
                <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-xs space-y-4">
                  <div className="flex items-center gap-2.5 text-stone-900 font-bold border-b border-stone-100 pb-3">
                    <MapPin className="w-5 h-5 text-[#C2410C]" />
                    <h3 className="text-base">3. Location Profile</h3>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm">
                    <div className="grid grid-cols-2 gap-2">
                      <div>
                        <span className="text-stone-400 block text-[11px] uppercase font-bold">District</span>
                        <span className="font-semibold text-stone-800">{profileData.location_profile?.district || 'Not specified'}</span>
                      </div>
                      <div>
                        <span className="text-stone-400 block text-[11px] uppercase font-bold">State</span>
                        <span className="font-semibold text-stone-800">{profileData.location_profile?.state || 'India'}</span>
                      </div>
                    </div>

                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold">Proposed Village / Place</span>
                      <span className="font-medium text-stone-700">{profileData.location_profile?.name || 'Local rural cluster'}</span>
                    </div>

                    <div className="flex items-center justify-between p-2.5 rounded-xl bg-stone-50 border border-stone-100 text-xs">
                      <div>
                        <span className="text-stone-400 block text-[10px] uppercase font-bold">Coordinates</span>
                        <span className="font-mono text-stone-800">
                          {profileData.location_profile?.coordinates?.latitude
                            ? `${profileData.location_profile.coordinates.latitude.toFixed(4)}, ${profileData.location_profile.coordinates.longitude.toFixed(4)}`
                            : 'Derived from district'}
                        </span>
                      </div>
                      <span className="px-2 py-0.5 rounded text-[10px] uppercase font-bold bg-stone-200 text-stone-700">
                        Source: {profileData.location_profile?.source || 'User'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* 4. Financial Profile Card */}
                <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-xs space-y-4">
                  <div className="flex items-center gap-2.5 text-stone-900 font-bold border-b border-stone-100 pb-3">
                    <IndianRupee className="w-5 h-5 text-[#C2410C]" />
                    <h3 className="text-base">4. Financial Profile</h3>
                  </div>

                  <div className="space-y-3 text-xs sm:text-sm">
                    <div>
                      <span className="text-stone-400 block text-[11px] uppercase font-bold">Declared Available Capital</span>
                      <div className="text-2xl font-extrabold text-[#C2410C] mt-1 font-mono">
                        {formatCurrency(profileData.financial_profile?.available_capital)}
                      </div>
                    </div>

                    <div className="p-3 rounded-2xl bg-orange-50/60 border border-orange-100 text-xs text-stone-700">
                      <span className="font-bold text-[#C2410C] block mb-0.5">Capital Assessment</span>
                      This capital figure is locked into the canonical profile for downstream Stage 5 Feasibility and Stage 6 DPR debt/equity structuring.
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 2: Analysis Requirements */}
            {activeTab === 'analysis' && (
              <div className="space-y-6">
                <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-xs">
                  <div className="flex items-center gap-2.5 text-stone-900 font-bold border-b border-stone-100 pb-3 mb-4">
                    <Cpu className="w-5 h-5 text-[#C2410C]" />
                    <h3 className="text-base">Downstream Market Intelligence Requirements (Ontology-Guided)</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-xs sm:text-sm">
                    {/* Direct Competitors */}
                    <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                      <span className="text-stone-500 font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-orange-600" />
                        Direct Competitors to Map
                      </span>
                      <ul className="list-disc list-inside text-stone-800 space-y-1">
                        {profileData.analysis_requirements?.direct_competitors?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Adjacent & Substitutes */}
                    <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                      <span className="text-stone-500 font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <Layers className="w-3.5 h-3.5 text-orange-600" />
                        Substitute & Adjacent Businesses
                      </span>
                      <ul className="list-disc list-inside text-stone-800 space-y-1">
                        {profileData.analysis_requirements?.substitute_businesses?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Demand Features */}
                    <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                      <span className="text-stone-500 font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <TrendingUp className="w-3.5 h-3.5 text-emerald-600" />
                        Key Demand Drivers
                      </span>
                      <ul className="list-disc list-inside text-stone-800 space-y-1">
                        {profileData.analysis_requirements?.demand_features?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Infrastructure */}
                    <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                      <span className="text-stone-500 font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <Building2 className="w-3.5 h-3.5 text-blue-600" />
                        Infrastructure Requirements
                      </span>
                      <ul className="list-disc list-inside text-stone-800 space-y-1">
                        {profileData.analysis_requirements?.infrastructure_requirements?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Risk Factors */}
                    <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                      <span className="text-stone-500 font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <ShieldAlert className="w-3.5 h-3.5 text-rose-600" />
                        Primary Risk Factors
                      </span>
                      <ul className="list-disc list-inside text-stone-800 space-y-1">
                        {profileData.analysis_requirements?.risk_factors?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>

                    {/* Required Datasets */}
                    <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200 space-y-2">
                      <span className="text-stone-500 font-bold uppercase text-[11px] flex items-center gap-1.5">
                        <Database className="w-3.5 h-3.5 text-purple-600" />
                        Required Verified Datasets
                      </span>
                      <ul className="list-disc list-inside text-stone-800 space-y-1">
                        {profileData.analysis_requirements?.required_datasets?.map((item, idx) => (
                          <li key={idx}>{item}</li>
                        ))}
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 3: Data Quality & Readiness */}
            {activeTab === 'readiness' && (
              <div className="p-6 rounded-3xl bg-white border border-stone-200 shadow-xs space-y-6">
                <div className="flex items-center gap-2.5 text-stone-900 font-bold border-b border-stone-100 pb-3">
                  <ShieldAlert className="w-5 h-5 text-[#C2410C]" />
                  <h3 className="text-base">Data Quality & Validation Audit</h3>
                </div>

                <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                  <div className="p-4 rounded-2xl bg-emerald-50 border border-emerald-200">
                    <span className="text-xs uppercase font-bold text-emerald-800">Validation Status</span>
                    <div className="text-lg font-extrabold text-emerald-700 mt-1">
                      {profileData.data_quality?.validation_status || 'PASSED'}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200">
                    <span className="text-xs uppercase font-bold text-stone-600">Completeness</span>
                    <div className="text-lg font-extrabold text-stone-800 mt-1">
                      {profileData.data_quality?.profile_complete ? '100% Complete' : 'Incomplete'}
                    </div>
                  </div>

                  <div className="p-4 rounded-2xl bg-stone-50 border border-stone-200">
                    <span className="text-xs uppercase font-bold text-stone-600">Warnings Count</span>
                    <div className="text-lg font-extrabold text-stone-800 mt-1">
                      {profileData.data_quality?.warnings?.length || 0}
                    </div>
                  </div>
                </div>

                {profileData.data_quality?.warnings?.length > 0 && (
                  <div className="p-4 rounded-2xl bg-amber-50 border border-amber-200 text-amber-900 space-y-2">
                    <span className="font-bold text-xs uppercase tracking-wider block">Audit Warnings</span>
                    <ul className="list-disc list-inside text-xs space-y-1">
                      {profileData.data_quality.warnings.map((w, idx) => (
                        <li key={idx}>{w}</li>
                      ))}
                    </ul>
                  </div>
                )}
              </div>
            )}

            {/* TAB 4: Raw Canonical JSON */}
            {activeTab === 'json' && (
              <div className="p-6 rounded-3xl bg-stone-900 text-stone-100 shadow-md">
                <div className="flex items-center justify-between pb-3 border-b border-stone-800 mb-4">
                  <div className="flex items-center gap-2 text-xs font-mono text-stone-400">
                    <Database className="w-4 h-4 text-orange-400" />
                    <span>canonical_business_profile.json</span>
                  </div>
                  <button
                    type="button"
                    onClick={() => {
                      navigator.clipboard.writeText(JSON.stringify(profileData, null, 2));
                      setCopied(true);
                      setTimeout(() => setCopied(false), 2000);
                    }}
                    className="flex items-center gap-1.5 px-3 py-1 rounded-lg bg-stone-800 hover:bg-stone-700 text-xs text-stone-300 transition"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-400" /> : <Copy className="w-3.5 h-3.5" />}
                    <span>{copied ? 'Copied' : 'Copy JSON'}</span>
                  </button>
                </div>
                <pre className="text-xs font-mono overflow-x-auto p-4 bg-stone-950 rounded-2xl text-emerald-400 max-h-96">
                  {JSON.stringify(profileData, null, 2)}
                </pre>
              </div>
            )}

            {/* Bottom Proceed Action Bar */}
            <div className="pt-6 border-t border-stone-200 flex flex-col sm:flex-row items-center justify-between gap-4">
              <Link
                to={`/classification?sessionId=${profileData.session_id}`}
                className="inline-flex items-center gap-2 text-xs font-bold text-stone-600 hover:text-stone-900"
              >
                <ArrowLeft className="w-4 h-4" />
                <span>Back to Stage 2 Classification</span>
              </Link>

              <div className="flex items-center gap-3">
                <button
                  type="button"
                  disabled
                  className="inline-flex items-center gap-2 px-6 py-3.5 rounded-2xl bg-stone-100 border border-stone-300 text-stone-500 text-xs sm:text-sm font-bold shadow-xs cursor-not-allowed"
                >
                  <Lock className="w-4 h-4" />
                  <span>Business Profile Ready for Orchestration</span>
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
