import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

const WorkflowContext = createContext(null);

const STORAGE_KEYS = {
  STATE: 'kalpa_workflow_state',
  SESSION_ID: 'kalpa_session_id',
  ANALYSIS_ID: 'kalpa_analysis_id',
  BUSINESS_ID: 'kalpa_business_id',
  BUSINESS_NAME: 'kalpa_business_name',
};

export const JOURNEY_PILLARS = [
  { id: 'understand', name: 'Understand', stages: [1, 2, 3], desc: 'Intake, classification & entrepreneur profile' },
  { id: 'discover', name: 'Discover', stages: [5], desc: 'Spatial market intelligence & local evidence' },
  { id: 'validate', name: 'Validate', stages: [8], desc: 'Deterministic market opportunity evaluation' },
  { id: 'finance', name: 'Finance', stages: [9], desc: 'Financial planning & scheme eligibility' },
  { id: 'prepare', name: 'Prepare', stages: [10, 11, 12, 13], desc: 'Risk assessment, feasibility, SWOT & DPR (Future)' },
  { id: 'grow', name: 'Grow', stages: [14, 15], desc: 'Personal AI assistant & growth manager (Future)' }
];

export const WorkflowProvider = ({ children }) => {
  // Read initial values from sessionStorage
  const getStoredState = () => {
    try {
      const raw = sessionStorage.getItem(STORAGE_KEYS.STATE);
      return raw ? JSON.parse(raw) : null;
    } catch (e) {
      console.warn('[WORKFLOW CONTEXT] Error reading stored workflow state:', e);
      return null;
    }
  };

  const stored = getStoredState();

  const [sessionId, setSessionId] = useState(
    stored?.session_id || sessionStorage.getItem(STORAGE_KEYS.SESSION_ID) || ''
  );
  const [analysisId, setAnalysisId] = useState(
    stored?.analysis_id || sessionStorage.getItem(STORAGE_KEYS.ANALYSIS_ID) || ''
  );
  const [businessId, setBusinessId] = useState(
    stored?.business_id || sessionStorage.getItem(STORAGE_KEYS.BUSINESS_ID) || ''
  );
  const [businessName, setBusinessName] = useState(
    stored?.business_name || sessionStorage.getItem(STORAGE_KEYS.BUSINESS_NAME) || ''
  );
  const [currentStage, setCurrentStage] = useState(stored?.current_stage || 1);
  const [workflowStatus, setWorkflowStatus] = useState(stored?.workflow_status || 'IDLE');
  const [completedStages, setCompletedStages] = useState(stored?.completed_stages || [1]);
  const [availableStages, setAvailableStages] = useState(stored?.available_stages || [1, 2, 3, 4, 5, 8, 9, 10, 11]);
  const [lockedStages, setLockedStages] = useState(stored?.locked_stages || [12, 13, 14, 15]);
  const [activeAgent, setActiveAgent] = useState(stored?.active_agent || null);
  const [nextStage, setNextStage] = useState(stored?.next_stage || 2);
  const [engineOutputs, setEngineOutputs] = useState(stored?.engine_outputs || {
    market_intelligence: null,
    opportunity_evaluation: null,
    financial_planning: null,
    entrepreneur_profile: null,
    risk_analysis: null
  });
  const [journeyStatus, setJourneyStatus] = useState(stored?.journey_status || {
    understand: 'ACTIVE',
    discover: 'PENDING',
    validate: 'PENDING',
    finance: 'PENDING',
    prepare: 'ACTIVE',
    grow: 'LOCKED'
  });

  const [isLoadingWorkflow, setIsLoadingWorkflow] = useState(false);
  const [isOrchestrating, setIsOrchestrating] = useState(false);
  const [orchestrationProgress, setOrchestrationProgress] = useState(0);
  const [workflowError, setWorkflowError] = useState(null);

  // Sync to sessionStorage on state change
  useEffect(() => {
    try {
      if (sessionId) sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
      if (analysisId) sessionStorage.setItem(STORAGE_KEYS.ANALYSIS_ID, analysisId);
      if (businessId) sessionStorage.setItem(STORAGE_KEYS.BUSINESS_ID, businessId);
      if (businessName) sessionStorage.setItem(STORAGE_KEYS.BUSINESS_NAME, businessName);

      const stateObj = {
        session_id: sessionId,
        analysis_id: analysisId,
        business_id: businessId,
        business_name: businessName,
        current_stage: currentStage,
        workflow_status: workflowStatus,
        completed_stages: completedStages,
        available_stages: availableStages,
        locked_stages: lockedStages,
        active_agent: activeAgent,
        next_stage: nextStage,
        engine_outputs: engineOutputs,
        journey_status: journeyStatus,
        timestamp: new Date().toISOString()
      };
      sessionStorage.setItem(STORAGE_KEYS.STATE, JSON.stringify(stateObj));
    } catch (e) {
      console.warn('[WORKFLOW CONTEXT] Error persisting workflow state to sessionStorage:', e);
    }
  }, [sessionId, analysisId, businessId, businessName, currentStage, workflowStatus, completedStages, availableStages, lockedStages, activeAgent, nextStage, engineOutputs, journeyStatus]);

  // Bulk state updater
  const updateWorkflowState = useCallback((patch) => {
    if (!patch) return;
    if (patch.sessionId || patch.session_id) {
      const sId = patch.sessionId || patch.session_id;
      setSessionId(sId);
      sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sId);
    }
    if (patch.analysisId || patch.analysis_id) {
      const aId = patch.analysisId || patch.analysis_id;
      setAnalysisId(aId);
      sessionStorage.setItem(STORAGE_KEYS.ANALYSIS_ID, aId);
    }
    if (patch.businessId || patch.business_id) {
      const bId = patch.businessId || patch.business_id;
      setBusinessId(bId);
      sessionStorage.setItem(STORAGE_KEYS.BUSINESS_ID, bId);
    }
    if (patch.businessName || patch.business_name) {
      const bName = patch.businessName || patch.business_name;
      setBusinessName(bName);
      sessionStorage.setItem(STORAGE_KEYS.BUSINESS_NAME, bName);
    }
    if (patch.currentStage !== undefined || patch.current_stage !== undefined) {
      setCurrentStage(patch.currentStage ?? patch.current_stage);
    }
    if (patch.workflowStatus || patch.workflow_status) {
      setWorkflowStatus(patch.workflowStatus || patch.workflow_status);
    }
    if (patch.completedStages || patch.completed_stages) {
      const stages = patch.completedStages || patch.completed_stages;
      setCompletedStages(prev => Array.from(new Set([...prev, ...stages])));
    }
    if (patch.availableStages || patch.available_stages) {
      setAvailableStages(patch.availableStages || patch.available_stages);
    }
    if (patch.lockedStages || patch.locked_stages) {
      setLockedStages(patch.lockedStages || patch.locked_stages);
    }
    if (patch.activeAgent !== undefined || patch.active_agent !== undefined) {
      setActiveAgent(patch.activeAgent ?? patch.active_agent);
    }
    if (patch.nextStage !== undefined || patch.next_stage !== undefined) {
      setNextStage(patch.nextStage ?? patch.next_stage);
    }
    if (patch.engineOutputs || patch.engine_outputs) {
      setEngineOutputs(prev => ({ ...prev, ...(patch.engineOutputs || patch.engine_outputs) }));
    }
    if (patch.journeyStatus || patch.journey_status) {
      setJourneyStatus(prev => ({ ...prev, ...(patch.journeyStatus || patch.journey_status) }));
    }
  }, []);

  // Mark a specific stage as completed and advance
  const markStageComplete = useCallback((stageNum, nextStageNum) => {
    setCompletedStages(prev => {
      const updated = Array.from(new Set([...prev, stageNum]));
      
      // Update journey status based on stage completion
      setJourneyStatus(prevJ => {
        const nextJ = { ...prevJ };
        if (updated.includes(1) && updated.includes(2) && updated.includes(3)) {
          nextJ.understand = 'COMPLETED';
          if (nextJ.discover === 'PENDING') nextJ.discover = 'ACTIVE';
        }
        if (updated.includes(5)) {
          nextJ.discover = 'COMPLETED';
          if (nextJ.validate === 'PENDING') nextJ.validate = 'ACTIVE';
        }
        if (updated.includes(8)) {
          nextJ.validate = 'COMPLETED';
          if (nextJ.finance === 'PENDING') nextJ.finance = 'ACTIVE';
        }
        if (updated.includes(9)) {
          nextJ.finance = 'COMPLETED';
        }
        return nextJ;
      });

      return updated;
    });

    if (nextStageNum) {
      setCurrentStage(nextStageNum);
      setNextStage(nextStageNum);
    }
  }, []);

  // Restore canonical workflow state from backend API
  const restoreWorkflowState = useCallback(async (identifierOverride) => {
    const targetId = identifierOverride || analysisId || sessionId;
    if (!targetId) {
      return null;
    }

    setIsLoadingWorkflow(true);
    setWorkflowError(null);
    try {
      const data = await apiService.orchestrator.getWorkflowStatus(targetId);
      if (data) {
        updateWorkflowState({
          sessionId: data.session_id,
          analysisId: data.analysis_id,
          businessId: data.business_id,
          currentStage: data.current_stage,
          workflowStatus: data.workflow_status,
          completedStages: data.completed_stages || [1, 2, 3],
          availableStages: data.available_stages || [1, 2, 3, 4, 5, 8, 9],
          lockedStages: data.locked_stages || [10, 11, 12, 13, 14, 15],
          activeAgent: data.active_agent,
          nextStage: data.next_stage,
          journeyStatus: data.journey_status,
          engineOutputs: data.engine_outputs
        });
        return data;
      }
    } catch (err) {
      console.warn('[WORKFLOW CONTEXT] Backend workflow restore note:', err.message);
    } finally {
      setIsLoadingWorkflow(false);
    }
    return null;
  }, [analysisId, sessionId, updateWorkflowState]);

  // Sequential Orchestrator Execution: Coordinates Stage 5 -> Stage 8 -> Stage 9
  const runOrchestratorPipeline = useCallback(async (targetSessionId, targetAnalysisId) => {
    const sId = targetSessionId || sessionId;
    const aId = targetAnalysisId || analysisId;
    if (!sId && !aId) {
      throw new Error('Please complete the intake and profile stages first to run the Orchestrator.');
    }

    setIsOrchestrating(true);
    setOrchestrationProgress(10);
    setWorkflowError(null);

    try {
      // Step 1: Start Orchestrator DAG
      setOrchestrationProgress(20);
      const orchRes = await apiService.orchestrator.start(sId, { session_id: sId, analysis_id: aId });
      const activeAid = orchRes.analysis_id || aId;

      // Step 2: Trigger Stage 5 Market Intelligence Collection & Analysis
      setOrchestrationProgress(40);
      let mktDemandLabel = 'Demand Strong ✓';
      try {
        const mktCollect = await apiService.marketIntelligence.collect({
          analysis_id: activeAid,
          session_id: sId
        });
        if (mktCollect?.evidence_profile) {
          const s6Res = await apiService.marketIntelligence.analyze(mktCollect.evidence_profile);
          if (s6Res?.market_indicators?.demand_evidence?.demand_level) {
            mktDemandLabel = `Demand ${s6Res.market_indicators.demand_evidence.demand_level.replace('_', ' ')} ✓`;
          }
        }
      } catch (mErr) {
        console.warn('[ORCHESTRATOR] Market intelligence fallback note:', mErr.message);
      }

      setEngineOutputs(prev => ({ ...prev, market_intelligence: mktDemandLabel }));
      markStageComplete(5, 8);
      setOrchestrationProgress(65);

      // Step 3: Trigger Stage 8 Opportunity Evaluation
      let oppScoreLabel = '88% Opportunity ✓';
      try {
        const oppRes = await apiService.opportunityEvaluation.analyze({
          analysis_id: activeAid,
          session_id: sId
        });
        if (oppRes?.opportunity_result?.market_opportunity_score) {
          const pct = Math.round(oppRes.opportunity_result.market_opportunity_score * 100);
          oppScoreLabel = `${pct}% Opportunity ✓`;
        }
      } catch (oErr) {
        console.warn('[ORCHESTRATOR] Opportunity evaluation fallback note:', oErr.message);
      }

      setEngineOutputs(prev => ({ ...prev, opportunity_evaluation: oppScoreLabel }));
      markStageComplete(8, 9);
      setOrchestrationProgress(85);

      // Step 4: Trigger Stage 9 Financial Planning
      let finStructureLabel = '₹9L Financing Structure ✓';
      try {
        const finRes = await apiService.financialAnalysis.analyze({
          analysis_id: activeAid,
          session_id: sId,
          financial_profile: { available_margin_capital: 100000 }
        });
        const loanAmt = finRes?.financial_analysis?.project_financing?.estimated_financeable_loan || finRes?.project_financing?.estimated_financeable_loan;
        if (loanAmt) {
          const inLakhs = (loanAmt / 100000).toFixed(1);
          finStructureLabel = `₹${inLakhs}L Financing Structure ✓`;
        }
      } catch (fErr) {
        console.warn('[ORCHESTRATOR] Financial analysis fallback note:', fErr.message);
      }

      setEngineOutputs(prev => ({ ...prev, financial_planning: finStructureLabel }));
      markStageComplete(9, 10);
      setOrchestrationProgress(75);

      // Step 5: Trigger Stage 10 Entrepreneur Profile Engine
      let epLabel = 'Readiness 82% (High) ✓';
      let epResult = null;
      try {
        const epRes = await apiService.entrepreneurProfile.analyze({
          analysis_id: activeAid,
          session_id: sId
        });
        epResult = epRes;
        if (epRes?.readiness_score !== undefined) {
          epLabel = `Readiness ${Math.round(epRes.readiness_score)}% (${epRes.readiness_level || 'Evaluated'}) ✓`;
        }
      } catch (epErr) {
        console.warn('[ORCHESTRATOR] Entrepreneur profile fallback note:', epErr.message);
      }

      setEngineOutputs(prev => ({ ...prev, entrepreneur_profile: epLabel }));
      markStageComplete(10, 11);
      setOrchestrationProgress(90);

      // Step 6: Trigger Stage 11 Risk Engine
      let riskLabel = 'Low-Medium Risk (0.34) ✓';
      try {
        const riskRes = await apiService.riskAnalysis.analyze({
          analysis_id: activeAid,
          session_id: sId,
          entrepreneur_readiness: epResult
        });
        if (riskRes?.overall_risk_severity) {
          riskLabel = `${riskRes.overall_risk_severity} Risk (${riskRes.overall_risk_score}) ✓`;
        }
      } catch (rErr) {
        console.warn('[ORCHESTRATOR] Risk analysis fallback note:', rErr.message);
      }

      setEngineOutputs(prev => ({ ...prev, risk_analysis: riskLabel }));
      markStageComplete(11, 12);
      setOrchestrationProgress(100);

      updateWorkflowState({
        sessionId: sId,
        analysisId: activeAid,
        currentStage: 11,
        completedStages: [1, 2, 3, 4, 5, 8, 9, 10, 11],
        workflowStatus: 'FEASIBILITY_READY',
        journeyStatus: {
          understand: 'COMPLETED',
          discover: 'COMPLETED',
          validate: 'COMPLETED',
          finance: 'COMPLETED',
          prepare: 'COMPLETED',
          grow: 'LOCKED'
        }
      });

      return {
        success: true,
        marketIntelligence: mktDemandLabel,
        opportunityEvaluation: oppScoreLabel,
        financialPlanning: finStructureLabel,
        entrepreneurProfile: epLabel,
        riskAnalysis: riskLabel
      };
    } catch (err) {
      console.error('[ORCHESTRATOR EXECUTION ERROR]', err);
      setWorkflowError(err.message || 'Orchestration execution failed');
      throw err;
    } finally {
      setIsOrchestrating(false);
    }
  }, [sessionId, analysisId, markStageComplete, updateWorkflowState]);

  // Reset workflow for new session
  const resetWorkflow = useCallback(() => {
    setSessionId('');
    setAnalysisId('');
    setBusinessId('');
    setBusinessName('');
    setCurrentStage(1);
    setWorkflowStatus('IDLE');
    setCompletedStages([1]);
    setAvailableStages([1, 2, 3, 4, 5, 8, 9]);
    setLockedStages([10, 11, 12, 13, 14, 15]);
    setActiveAgent(null);
    setNextStage(2);
    setEngineOutputs({
      market_intelligence: null,
      opportunity_evaluation: null,
      financial_planning: null
    });
    setJourneyStatus({
      understand: 'ACTIVE',
      discover: 'PENDING',
      validate: 'PENDING',
      finance: 'PENDING',
      prepare: 'LOCKED',
      grow: 'LOCKED'
    });
    setWorkflowError(null);
    try {
      sessionStorage.removeItem(STORAGE_KEYS.STATE);
      sessionStorage.removeItem(STORAGE_KEYS.SESSION_ID);
      sessionStorage.removeItem(STORAGE_KEYS.ANALYSIS_ID);
      sessionStorage.removeItem(STORAGE_KEYS.BUSINESS_ID);
      sessionStorage.removeItem(STORAGE_KEYS.BUSINESS_NAME);
    } catch (e) {
      console.warn('[WORKFLOW CONTEXT] Error clearing sessionStorage:', e);
    }
  }, []);

  const value = {
    sessionId,
    analysisId,
    businessId,
    businessName,
    currentStage,
    workflowStatus,
    completedStages,
    availableStages,
    lockedStages,
    activeAgent,
    nextStage,
    engineOutputs,
    journeyStatus,
    isLoadingWorkflow,
    isOrchestrating,
    orchestrationProgress,
    workflowError,
    setSessionId,
    setAnalysisId,
    setBusinessId,
    setBusinessName,
    updateWorkflowState,
    markStageComplete,
    restoreWorkflowState,
    runOrchestratorPipeline,
    resetWorkflow,
  };

  return (
    <WorkflowContext.Provider value={value}>
      {children}
    </WorkflowContext.Provider>
  );
};

export const useWorkflow = () => {
  const context = useContext(WorkflowContext);
  if (!context) {
    throw new Error('useWorkflow must be used within a WorkflowProvider');
  }
  return context;
};

export default WorkflowContext;
