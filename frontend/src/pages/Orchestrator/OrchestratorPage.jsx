import React, { useState, useEffect } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';
import {
  Brain,
  Layers,
  Cpu,
  CheckCircle2,
  AlertTriangle,
  Clock,
  ArrowRight,
  ShieldCheck,
  Zap,
  ChevronDown,
  ChevronUp,
  FileCode,
  Copy,
  Check,
  TrendingUp,
  DollarSign,
  Compass,
  Building2,
  RefreshCw,
  Sparkles,
  HelpCircle,
  Database,
  Search
} from 'lucide-react';
import apiService from '../../services/api';
import { useWorkflow } from '../../context/WorkflowContext';

export default function OrchestratorPage() {
  const location = useLocation();
  const navigate = useNavigate();

  const {
    sessionId: ctxSessionId,
    analysisId: ctxAnalysisId,
    updateWorkflowState,
    markStageComplete
  } = useWorkflow();

  // Extract session_id or analysis_id from navigation state, URL search params, or central context
  const queryParams = new URLSearchParams(location.search);
  const initialSessionId = location.state?.sessionId || location.state?.session_id || queryParams.get('session_id') || ctxSessionId || '';
  const initialAnalysisId = location.state?.analysisId || location.state?.analysis_id || queryParams.get('analysis_id') || ctxAnalysisId || '';

  const [sessionId, setSessionId] = useState(initialSessionId);
  const [analysisId, setAnalysisId] = useState(initialAnalysisId);
  const [orchestratorData, setOrchestratorData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [executing, setExecuting] = useState(false);
  const [error, setError] = useState(null);
  const [activeTab, setActiveTab] = useState('plan'); // 'plan' | 'trace' | 'knowledge' | 'adapters' | 'raw'
  const [copied, setCopied] = useState(false);
  const [expandedTraceIdx, setExpandedTraceIdx] = useState(null);

  useEffect(() => {
    if (sessionId || analysisId) {
      loadOrchestration();
    }
  }, [sessionId, analysisId]);

  const loadOrchestration = async () => {
    setLoading(true);
    setError(null);
    try {
      let data = null;
      if (analysisId) {
        data = await apiService.orchestrator.getById(analysisId);
      } else if (sessionId) {
        data = await apiService.orchestrator.getBySessionId(sessionId);
      }
      if (data) {
        setOrchestratorData(data);
        const aId = data.analysis_id || analysisId;
        const sId = data.session_id || sessionId;
        if (aId) setAnalysisId(aId);
        if (sId) setSessionId(sId);
        updateWorkflowState({
          sessionId: sId,
          analysisId: aId,
          businessId: data.business_id || data.business_context?.specific_business,
          currentStage: 4,
          workflowStatus: data.workflow_status || data.orchestration_status || 'ORCHESTRATION_COMPLETE',
          completedStages: data.completed_stages || [1, 2, 3, 4, 5, 6],
          nextStage: 5
        });
        markStageComplete(4, 5);
      }
    } catch (err) {
      console.log('No existing orchestration record found; ready to run orchestrator:', err.message);
      // Auto-trigger if we came from Stage 3 with session_id
      if (sessionId && !orchestratorData) {
        runOrchestrator();
      }
    } finally {
      setLoading(false);
    }
  };

  const runOrchestrator = async (forceLlm = false) => {
    if (!sessionId && !analysisId) {
      setError('Please provide a valid Session ID or Analysis ID to run the Orchestrator.');
      return;
    }
    setExecuting(true);
    setError(null);
    try {
      const payload = {
        session_id: sessionId || undefined,
        analysis_id: analysisId || undefined,
        force_llm: forceLlm
      };
      const response = await apiService.orchestrator.start(sessionId, payload);
      setOrchestratorData(response);
      const aId = response.analysis_id || analysisId;
      const sId = response.session_id || sessionId;
      if (aId) setAnalysisId(aId);
      if (sId) setSessionId(sId);
      updateWorkflowState({
        sessionId: sId,
        analysisId: aId,
        businessId: response.business_id || response.business_context?.specific_business,
        currentStage: 4,
        workflowStatus: response.workflow_status || response.orchestration_status || 'ORCHESTRATION_COMPLETE',
        completedStages: response.completed_stages || [1, 2, 3, 4, 5, 6],
        nextStage: 5
      });
      markStageComplete(4, 5);
    } catch (err) {
      console.error('Error running Stage 4 Orchestrator:', err);
      setError(err.message || 'Failed to execute KALPA Manager Orchestrator');
    } finally {
      setExecuting(false);
    }
  };

  const copyRawJSON = () => {
    if (orchestratorData) {
      navigator.clipboard.writeText(JSON.stringify(orchestratorData, null, 2));
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    }
  };

  const executionPlan = orchestratorData?.execution_plan || [];
  const decisionHistory = orchestratorData?.decision_history || [];
  const routingSummary = orchestratorData?.routing_summary || {};
  const knowledgeContext = orchestratorData?.knowledge_context || {};
  const agentResults = orchestratorData?.agent_results || {};
  const summary = orchestratorData?.agent_execution_summary || {};
  const businessContext = orchestratorData?.business_context || {};

  return (
    <div className="min-h-screen bg-[#FDFBF7] text-[#2C2420] py-8 px-4 sm:px-6 lg:px-8">
      <div className="max-w-7xl mx-auto space-y-6">

        {/* Header Banner */}
        <div className="bg-white rounded-2xl shadow-sm border border-[#EBE3D5] p-6 sm:p-8 flex flex-col md:flex-row md:items-center justify-between gap-6 relative overflow-hidden">
          <div className="absolute top-0 right-0 w-64 h-64 bg-gradient-to-bl from-[#FFF0E0] via-transparent to-transparent rounded-bl-full pointer-events-none" />

          <div className="space-y-2 relative z-10">
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full text-xs font-semibold bg-[#FFF3E5] text-[#D95D0F] border border-[#FED7AA]">
              <Cpu className="w-3.5 h-3.5 animate-spin" style={{ animationDuration: '8s' }} />
              STAGE 4: KALPA MANAGER AGENT &middot; TRUE AGENTIC ORCHESTRATOR
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#1E1915] flex items-center gap-3">
              Multi-Agent Orchestration Engine
              {orchestratorData?.orchestration_status === 'ORCHESTRATION_COMPLETE' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-50 text-emerald-700 border border-emerald-200">
                  <CheckCircle2 className="w-4 h-4" /> COMPLETE
                </span>
              )}
              {orchestratorData?.orchestration_status === 'CLARIFICATION_REQUIRED' && (
                <span className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-semibold bg-amber-50 text-amber-700 border border-amber-200">
                  <HelpCircle className="w-4 h-4" /> CLARIFICATION NEEDED
                </span>
              )}
            </h1>
            <p className="text-sm text-[#736357] max-w-2xl">
              LangGraph-powered stateful agent orchestration with deterministic routing, 6-factor explainable confidence, and benchmark synthesis.
            </p>
          </div>

          <div className="flex flex-wrap items-center gap-3 relative z-10">
            <button
              onClick={() => runOrchestrator(false)}
              disabled={executing || loading}
              className="inline-flex items-center gap-2 px-5 py-2.5 rounded-xl text-sm font-semibold text-white bg-[#D95D0F] hover:bg-[#C24F0A] shadow-md hover:shadow-lg transition-all disabled:opacity-50 cursor-pointer"
            >
              <RefreshCw className={`w-4 h-4 ${executing ? 'animate-spin' : ''}`} />
              {executing ? 'Executing LangGraph...' : 'Run Orchestrator'}
            </button>
            <button
              onClick={() => runOrchestrator(true)}
              disabled={executing || loading}
              title="Runs orchestrator with LLM escalation path enabled"
              className="inline-flex items-center gap-2 px-4 py-2.5 rounded-xl text-sm font-semibold text-[#8C3F0D] bg-[#FFF3E5] hover:bg-[#FFE6CC] border border-[#FED7AA] transition-all disabled:opacity-50 cursor-pointer"
            >
              <Sparkles className="w-4 h-4" />
              Force LLM Escalation
            </button>
          </div>
        </div>

        {/* Input Identifier Toolbar */}
        <div className="bg-white rounded-xl shadow-xs border border-[#EBE3D5] p-4 flex flex-wrap items-center justify-between gap-4">
          <div className="flex flex-wrap items-center gap-4 text-xs font-mono">
            <div>
              <span className="text-[#8C7B70] uppercase">Session ID: </span>
              <span className="text-[#2C2420] font-semibold">{sessionId || 'Not specified'}</span>
            </div>
            <div className="hidden sm:block text-[#EBE3D5]">|</div>
            <div>
              <span className="text-[#8C7B70] uppercase">Analysis ID: </span>
              <span className="text-[#2C2420] font-semibold">{analysisId || 'Generated on run'}</span>
            </div>
            {businessContext.specific_business && (
              <>
                <div className="hidden sm:block text-[#EBE3D5]">|</div>
                <div>
                  <span className="text-[#8C7B70] uppercase">Business: </span>
                  <span className="text-[#D95D0F] font-bold">{businessContext.specific_business} ({businessContext.sector})</span>
                </div>
              </>
            )}
          </div>

          <div className="flex items-center gap-2">
            <input
              type="text"
              placeholder="Load by Session ID..."
              value={sessionId}
              onChange={(e) => setSessionId(e.target.value)}
              className="text-xs px-3 py-1.5 rounded-lg border border-[#D9CFC4] bg-[#FDFBF7] focus:outline-none focus:ring-1 focus:ring-[#D95D0F]"
            />
            <button
              onClick={loadOrchestration}
              disabled={loading || !sessionId}
              className="px-3 py-1.5 rounded-lg text-xs font-semibold text-[#5A4A42] bg-[#EBE3D5] hover:bg-[#DFD4C4] transition-all cursor-pointer"
            >
              Load
            </button>
          </div>
        </div>

        {/* Error Alert */}
        {error && (
          <div className="bg-rose-50 border border-rose-200 rounded-xl p-4 flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 text-rose-600 shrink-0 mt-0.5" />
            <div>
              <h3 className="text-sm font-semibold text-rose-800">Orchestration Notification</h3>
              <p className="text-xs text-rose-700 mt-0.5">{error}</p>
            </div>
          </div>
        )}

        {/* Loading Spinner */}
        {executing && (
          <div className="bg-white rounded-2xl border border-[#EBE3D5] p-12 text-center space-y-4">
            <div className="inline-block p-4 rounded-full bg-[#FFF3E5] text-[#D95D0F] animate-bounce">
              <Cpu className="w-8 h-8 animate-spin" style={{ animationDuration: '4s' }} />
            </div>
            <h3 className="text-lg font-bold text-[#2C2420]">LangGraph Orchestrator Running...</h3>
            <p className="text-sm text-[#736357] max-w-md mx-auto">
              Observing canonical profile &middot; Validating data quality &middot; Resolving DAG dependencies &middot; Invoking registered agent adapters
            </p>
          </div>
        )}

        {/* Orchestrator Content */}
        {!executing && orchestratorData && (
          <div className="space-y-6">

            {/* Hybrid Decision Metrics & Summary */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">

              {/* Card 1: Decision Routing */}
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#8C7B70]">Decision Engine</span>
                  <ShieldCheck className="w-4 h-4 text-[#D95D0F]" />
                </div>
                <div className="text-xl font-bold text-[#1E1915] capitalize flex items-center gap-2">
                  {routingSummary.decision_source === 'deterministic' && 'Deterministic AI'}
                  {routingSummary.decision_source === 'hybrid_llm' && 'Hybrid LLM Planner'}
                  {routingSummary.decision_source === 'deterministic_fallback' && 'Deterministic Fallback'}
                  {!routingSummary.decision_source && 'Hybrid Routing'}
                </div>
                <p className="text-xs text-[#736357] leading-relaxed">
                  {routingSummary.explanation || 'Workflow sequenced based on deterministic profile match and DAG dependencies.'}
                </p>
                <div className="pt-2 border-t border-[#F2EDE4] flex items-center justify-between text-xs">
                  <span className="text-[#8C7B70]">LLM Token Cost:</span>
                  <span className="font-semibold text-emerald-600">
                    {routingSummary.llm_used ? 'Escalated (1 call)' : '0 Calls (Conserved)'}
                  </span>
                </div>
              </div>

              {/* Card 2: Deterministic Confidence */}
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#8C7B70]">Confidence Score</span>
                  <Zap className="w-4 h-4 text-amber-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-[#D95D0F]">
                    {Math.round((routingSummary.deterministic_confidence || 0.95) * 100)}%
                  </span>
                  <span className="text-xs text-[#8C7B70]">Explainable Metric</span>
                </div>

                {/* Factors Mini-bars */}
                <div className="space-y-1.5 pt-1">
                  {Object.entries(routingSummary.factors || {}).map(([key, val]) => (
                    <div key={key} className="flex items-center justify-between text-[11px]">
                      <span className="text-[#736357] capitalize">{key.replace(/_/g, ' ')}</span>
                      <span className="font-semibold text-[#2C2420]">{Math.round(val * 100)}%</span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Card 3: Execution Pipeline Stats */}
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-5 space-y-3">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-bold uppercase tracking-wider text-[#8C7B70]">Agent Execution</span>
                  <Layers className="w-4 h-4 text-blue-500" />
                </div>
                <div className="flex items-baseline gap-2">
                  <span className="text-3xl font-black text-emerald-600">
                    {summary.completed?.length || 0}
                  </span>
                  <span className="text-xs text-[#8C7B70]">/ {summary.total_planned || executionPlan.length} Planned</span>
                </div>
                <div className="space-y-1 text-xs text-[#736357]">
                  <div className="flex justify-between">
                    <span>Completed Agents:</span>
                    <span className="font-semibold text-emerald-600">{summary.completed?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Pending / Scoped:</span>
                    <span className="font-semibold text-amber-600">{summary.pending?.length || 0}</span>
                  </div>
                  <div className="flex justify-between">
                    <span>Failed / Retried:</span>
                    <span className="font-semibold text-slate-500">{summary.failed?.length || 0}</span>
                  </div>
                </div>
              </div>
            </div>

            {/* Navigation Tabs */}
            <div className="bg-white rounded-xl border border-[#EBE3D5] p-1.5 flex flex-wrap gap-1">
              {[
                { id: 'plan', label: 'Agent Execution Plan', icon: Layers },
                { id: 'trace', label: 'Agent Decision Trace', icon: Compass },
                { id: 'knowledge', label: 'Domain Knowledge & Benchmarks', icon: Database },
                { id: 'adapters', label: 'Prototype Engine Scopes', icon: TrendingUp },
                { id: 'raw', label: 'Canonical Orchestration JSON', icon: FileCode }
              ].map((tab) => {
                const Icon = tab.icon;
                const isActive = activeTab === tab.id;
                return (
                  <button
                    key={tab.id}
                    onClick={() => setActiveTab(tab.id)}
                    className={`flex items-center gap-2 px-4 py-2 rounded-lg text-xs font-semibold transition-all cursor-pointer ${
                      isActive
                        ? 'bg-[#FFF3E5] text-[#D95D0F] shadow-xs'
                        : 'text-[#736357] hover:bg-[#FAF6F0] hover:text-[#2C2420]'
                    }`}
                  >
                    <Icon className="w-3.5 h-3.5" />
                    {tab.label}
                  </button>
                );
              })}
            </div>

            {/* TAB 1: Agent Execution Plan */}
            {activeTab === 'plan' && (
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <h3 className="text-base font-bold text-[#1E1915]">Dynamic Agent Execution DAG</h3>
                  <span className="text-xs text-[#8C7B70]">{executionPlan.length} Registered Nodes</span>
                </div>

                <div className="space-y-3">
                  {executionPlan.map((stepItem, idx) => (
                    <div
                      key={idx}
                      className={`p-4 rounded-xl border transition-all flex flex-col sm:flex-row sm:items-center justify-between gap-4 ${
                        stepItem.status === 'completed'
                          ? 'bg-emerald-50/50 border-emerald-200'
                          : stepItem.status === 'ready'
                          ? 'bg-amber-50/50 border-amber-200'
                          : 'bg-[#FAF6F0] border-[#EBE3D5]'
                      }`}
                    >
                      <div className="flex items-start gap-3">
                        <div className={`w-8 h-8 rounded-full flex items-center justify-center font-bold text-xs shrink-0 ${
                          stepItem.status === 'completed'
                            ? 'bg-emerald-600 text-white'
                            : 'bg-[#D95D0F] text-white'
                        }`}>
                          {stepItem.step}
                        </div>
                        <div className="space-y-1">
                          <div className="flex flex-wrap items-center gap-2">
                            <h4 className="text-sm font-bold text-[#2C2420]">{stepItem.agent}</h4>
                            <span className={`text-[10px] px-2 py-0.5 rounded-full font-bold uppercase ${
                              stepItem.priority === 'HIGH' ? 'bg-rose-100 text-rose-700' : 'bg-blue-100 text-blue-700'
                            }`}>
                              {stepItem.priority} Priority
                            </span>
                          </div>
                          <p className="text-xs text-[#736357]">{stepItem.purpose}</p>
                          {stepItem.dependencies?.length > 0 && (
                            <div className="text-[11px] text-[#8C7B70] flex items-center gap-1">
                              <span>Requires:</span>
                              <span className="font-mono text-[#D95D0F]">{stepItem.dependencies.join(', ')}</span>
                            </div>
                          )}
                        </div>
                      </div>

                      <div className="shrink-0">
                        {stepItem.status === 'completed' && (
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-emerald-100 text-emerald-800">
                            <CheckCircle2 className="w-3.5 h-3.5" /> Executed
                          </span>
                        )}
                        {stepItem.status === 'pending' && (
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700">
                            <Clock className="w-3.5 h-3.5" /> Queued
                          </span>
                        )}
                        {stepItem.status === 'ready' && (
                          <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full text-xs font-semibold bg-amber-100 text-amber-800">
                            <Zap className="w-3.5 h-3.5" /> Ready
                          </span>
                        )}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 2: Agent Decision Trace */}
            {activeTab === 'trace' && (
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-[#1E1915]">Agentic Decision Trace</h3>
                    <p className="text-xs text-[#736357]">Explainable step-by-step reasoning recorded at every LangGraph state transition</p>
                  </div>
                  <span className="text-xs px-2.5 py-1 rounded-full bg-[#FFF3E5] text-[#D95D0F] font-bold">
                    {decisionHistory.length} Trace Events
                  </span>
                </div>

                <div className="relative border-l-2 border-[#FED7AA] ml-3 pl-6 space-y-6">
                  {decisionHistory.map((trace, idx) => {
                    const isExpanded = expandedTraceIdx === idx;
                    return (
                      <div key={idx} className="relative group">
                        <div className="absolute -left-[31px] top-1.5 w-3.5 h-3.5 rounded-full bg-[#D95D0F] border-2 border-white ring-2 ring-[#FED7AA]" />
                        <div className="bg-[#FDFBF7] rounded-xl border border-[#EBE3D5] p-4 space-y-2 hover:border-[#D95D0F] transition-all">
                          <div className="flex flex-wrap items-center justify-between gap-2">
                            <span className="text-xs font-mono font-bold text-[#D95D0F] uppercase">
                              [{trace.node}]
                            </span>
                            <span className="text-[11px] text-[#8C7B70]">{trace.timestamp}</span>
                          </div>

                          <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1 text-xs">
                            <div>
                              <span className="font-semibold text-[#8C7B70]">Observation: </span>
                              <span className="text-[#2C2420]">{trace.observation}</span>
                            </div>
                            <div>
                              <span className="font-semibold text-[#8C7B70]">Decision: </span>
                              <span className="text-[#2C2420] font-medium">{trace.decision}</span>
                            </div>
                          </div>

                          <div className="text-xs bg-white rounded-lg p-2.5 border border-[#F2EDE4] text-[#5A4A42]">
                            <span className="font-semibold text-[#D95D0F]">Reason: </span>
                            {trace.reason}
                          </div>

                          <div className="flex items-center justify-between text-[11px] pt-1 text-[#8C7B70]">
                            <span>Confidence: <strong className="text-[#2C2420]">{Math.round((trace.confidence || 1.0) * 100)}%</strong></span>
                            <span>Source: <strong className="text-[#D95D0F] capitalize">{trace.decision_source || 'deterministic'}</strong></span>
                          </div>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </div>
            )}

            {/* TAB 3: Domain Knowledge & Benchmarks */}
            {activeTab === 'knowledge' && (
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-6 space-y-6">
                <div>
                  <h3 className="text-base font-bold text-[#1E1915]">Domain Knowledge & Benchmark Database</h3>
                  <p className="text-xs text-[#736357]">Sector-specific standards and operational rules extracted by DomainKnowledgeAgent</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">

                  {/* Sector Operating Benchmarks */}
                  <div className="bg-[#FDFBF7] rounded-xl border border-[#EBE3D5] p-5 space-y-4">
                    <h4 className="text-sm font-bold text-[#2C2420] flex items-center gap-2">
                      <DollarSign className="w-4 h-4 text-[#D95D0F]" />
                      MSME Financial & Operating Benchmarks
                    </h4>
                    <div className="space-y-2 text-xs">
                      {knowledgeContext.benchmarks && Object.entries(knowledgeContext.benchmarks).map(([k, v]) => (
                        <div key={k} className="flex justify-between py-1 border-b border-[#F2EDE4]">
                          <span className="text-[#736357] capitalize">{k.replace(/_/g, ' ')}:</span>
                          <span className="font-semibold text-[#2C2420]">
                            {Array.isArray(v) ? `INR ${v[0]?.toLocaleString()} - ${v[1]?.toLocaleString()}` : String(v)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>

                  {/* Competitor Landscape */}
                  <div className="bg-[#FDFBF7] rounded-xl border border-[#EBE3D5] p-5 space-y-4">
                    <h4 className="text-sm font-bold text-[#2C2420] flex items-center gap-2">
                      <Building2 className="w-4 h-4 text-[#D95D0F]" />
                      Competitor Landscape Taxonomies
                    </h4>
                    <div className="space-y-3 text-xs">
                      <div>
                        <span className="font-semibold text-[#8C7B70]">Direct Competitors:</span>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {knowledgeContext.competitor_landscape?.direct?.map((c, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-md bg-white border border-[#EBE3D5] text-[#2C2420]">
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>
                      <div>
                        <span className="font-semibold text-[#8C7B70]">Adjacent Competitors:</span>
                        <div className="flex flex-wrap gap-1.5 mt-1">
                          {knowledgeContext.competitor_landscape?.adjacent?.map((c, i) => (
                            <span key={i} className="px-2.5 py-1 rounded-md bg-white border border-[#EBE3D5] text-[#2C2420]">
                              {c}
                            </span>
                          ))}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Infrastructure Specifications */}
                  <div className="bg-[#FDFBF7] rounded-xl border border-[#EBE3D5] p-5 space-y-3 md:col-span-2">
                    <h4 className="text-sm font-bold text-[#2C2420] flex items-center gap-2">
                      <Layers className="w-4 h-4 text-[#D95D0F]" />
                      Prescribed Infrastructure Specifications
                    </h4>
                    <div className="grid grid-cols-1 sm:grid-cols-2 gap-2 text-xs">
                      {knowledgeContext.infrastructure_requirements?.map((req, idx) => (
                        <div key={idx} className="flex items-center gap-2 p-2.5 rounded-lg bg-white border border-[#F2EDE4]">
                          <CheckCircle2 className="w-3.5 h-3.5 text-[#D95D0F] shrink-0" />
                          <span className="text-[#2C2420]">{req}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* TAB 4: Prototype Engine Scopes */}
            {activeTab === 'adapters' && (
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-6 space-y-6">
                <div>
                  <h3 className="text-base font-bold text-[#1E1915]">Prototype Engine Adapter Results</h3>
                  <p className="text-xs text-[#736357]">Structured scopes prepared for future Market, Finance, Opportunity, and Feasibility engines</p>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  {Object.entries(agentResults).map(([agentKey, resultData]) => (
                    <div key={agentKey} className="bg-[#FDFBF7] rounded-xl border border-[#EBE3D5] p-5 space-y-3">
                      <div className="flex items-center justify-between">
                        <h4 className="text-sm font-bold text-[#2C2420] font-mono">{agentKey}</h4>
                        <span className="text-[10px] px-2 py-0.5 rounded-full font-bold bg-emerald-100 text-emerald-800 uppercase">
                          {resultData.status || 'Complete'}
                        </span>
                      </div>
                      <div className="bg-white p-3 rounded-lg border border-[#F2EDE4] text-xs font-mono text-[#5A4A42] max-h-48 overflow-y-auto">
                        <pre className="whitespace-pre-wrap">{JSON.stringify(resultData, null, 2)}</pre>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* TAB 5: Raw Orchestration JSON */}
            {activeTab === 'raw' && (
              <div className="bg-white rounded-2xl border border-[#EBE3D5] p-6 space-y-4">
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="text-base font-bold text-[#1E1915]">Canonical Stage 4 Orchestration Document</h3>
                    <p className="text-xs text-[#736357]">Machine-readable JSON schema consumable by downstream KALPA agents</p>
                  </div>
                  <button
                    onClick={copyRawJSON}
                    className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-semibold text-[#5A4A42] bg-[#FDFBF7] border border-[#D9CFC4] hover:bg-[#FAF6F0] transition-all cursor-pointer"
                  >
                    {copied ? <Check className="w-3.5 h-3.5 text-emerald-600" /> : <Copy className="w-3.5 h-3.5" />}
                    {copied ? 'Copied' : 'Copy JSON'}
                  </button>
                </div>

                <div className="bg-[#1E1915] text-[#F3EFEA] rounded-xl p-4 font-mono text-xs max-h-[500px] overflow-auto">
                  <pre>{JSON.stringify(orchestratorData, null, 2)}</pre>
                </div>
              </div>
            )}

            {/* Next Stage 5 Handoff Banner */}
            <div className="bg-gradient-to-r from-[#FFF0E0] via-[#FFF8F0] to-[#FFF0E0] rounded-2xl border border-[#FED7AA] p-6 flex flex-col md:flex-row items-center justify-between gap-4">
              <div className="space-y-1 text-center md:text-left">
                <h3 className="text-sm font-bold text-[#8C3F0D] uppercase tracking-wider flex items-center justify-center md:justify-start gap-2">
                  <Sparkles className="w-4 h-4 text-[#D95D0F]" />
                  Stage 4 Orchestration Complete &middot; Ready for Stage 5
                </h3>
                <p className="text-xs text-[#736357]">
                  DAG execution plan, benchmark context, and prototype engine requirements have been verified and persisted to PostgreSQL.
                </p>
              </div>

              <button
                disabled
                title="Stage 5 Opportunity Evaluation Engine will be unlocked in next phase"
                className="inline-flex items-center gap-2 px-6 py-3 rounded-xl text-xs font-bold text-white bg-slate-400 opacity-80 cursor-not-allowed shadow-sm"
              >
                Proceed to Stage 5: Opportunity Evaluation (Locked)
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>

          </div>
        )}

      </div>
    </div>
  );
}
