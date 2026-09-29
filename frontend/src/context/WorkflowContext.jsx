import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import apiService from '../services/api';

const WorkflowContext = createContext(null);

const STORAGE_KEYS = {
  STATE: 'kalpa_workflow_state',
  SESSION_ID: 'kalpa_session_id',
  ANALYSIS_ID: 'kalpa_analysis_id',
  BUSINESS_ID: 'kalpa_business_id',
  BUSINESS_NAME: 'kalpa_business_name',
  FINANCIAL_CONTEXT: 'kalpa_financial_context',
  FINANCIAL_ANALYSIS: 'kalpa_financial_analysis',
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
  const [completedStages, setCompletedStages] = useState(stored?.completed_stages || []);
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

  const getSessionIdKey = (bId) => (bId ? `kalpa_session_id_${bId}` : STORAGE_KEYS.SESSION_ID);
  const getAnalysisIdKey = (bId) => (bId ? `kalpa_analysis_id_${bId}` : STORAGE_KEYS.ANALYSIS_ID);
  const getFinancialContextKey = (bId) => (bId ? `kalpa_financial_context_${bId}` : STORAGE_KEYS.FINANCIAL_CONTEXT);
  const getFinancialAnalysisKey = (bId) => (bId ? `kalpa_financial_analysis_${bId}` : STORAGE_KEYS.FINANCIAL_ANALYSIS);

  const [financialContext, setFinancialContext] = useState(() => {
    try {
      const bId = stored?.business_id || sessionStorage.getItem(STORAGE_KEYS.BUSINESS_ID);
      const key = getFinancialContextKey(bId);
      const raw = sessionStorage.getItem(key) || sessionStorage.getItem(STORAGE_KEYS.FINANCIAL_CONTEXT);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const currSession = sessionStorage.getItem(STORAGE_KEYS.SESSION_ID);
      if (currSession && parsed?.session_id && parsed.session_id !== currSession) {
        sessionStorage.removeItem(key);
        return null;
      }
      return parsed;
    } catch (e) {
      return null;
    }
  });

  const [financialAnalysis, setFinancialAnalysis] = useState(() => {
    try {
      const bId = stored?.business_id || sessionStorage.getItem(STORAGE_KEYS.BUSINESS_ID);
      const key = getFinancialAnalysisKey(bId);
      const raw = sessionStorage.getItem(key) || sessionStorage.getItem(STORAGE_KEYS.FINANCIAL_ANALYSIS);
      if (!raw) return null;
      const parsed = JSON.parse(raw);
      const currSession = sessionStorage.getItem(STORAGE_KEYS.SESSION_ID);
      const storedSid = parsed?.session_id || parsed?.sessionId || parsed?.data?.session_id;
      if (currSession && storedSid && storedSid !== currSession) {
        sessionStorage.removeItem(key);
        return null;
      }
      return parsed;
    } catch (e) {
      return null;
    }
  });

  // Sync to sessionStorage on state change
  useEffect(() => {
    try {
      if (sessionId) {
        sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
        if (businessId) sessionStorage.setItem(getSessionIdKey(businessId), sessionId);
      }
      if (analysisId) {
        sessionStorage.setItem(STORAGE_KEYS.ANALYSIS_ID, analysisId);
        if (businessId) sessionStorage.setItem(getAnalysisIdKey(businessId), analysisId);
      }
      if (businessId) sessionStorage.setItem(STORAGE_KEYS.BUSINESS_ID, businessId);
      if (businessName) sessionStorage.setItem(STORAGE_KEYS.BUSINESS_NAME, businessName);
      if (financialContext) {
        sessionStorage.setItem(STORAGE_KEYS.FINANCIAL_CONTEXT, JSON.stringify(financialContext));
        if (businessId) {
          sessionStorage.setItem(getFinancialContextKey(businessId), JSON.stringify(financialContext));
        }
      }
      if (financialAnalysis) {
        sessionStorage.setItem(STORAGE_KEYS.FINANCIAL_ANALYSIS, JSON.stringify(financialAnalysis));
        if (businessId) {
          sessionStorage.setItem(getFinancialAnalysisKey(businessId), JSON.stringify(financialAnalysis));
        }
      }

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
        financial_context: financialContext,
        financial_analysis: financialAnalysis,
        timestamp: new Date().toISOString()
      };
      sessionStorage.setItem(STORAGE_KEYS.STATE, JSON.stringify(stateObj));
    } catch (e) {
      console.warn('[WORKFLOW CONTEXT] Error persisting workflow state to sessionStorage:', e);
    }
  }, [sessionId, analysisId, businessId, businessName, currentStage, workflowStatus, completedStages, availableStages, lockedStages, activeAgent, nextStage, engineOutputs, journeyStatus, financialContext, financialAnalysis]);

  // Bulk state updater
  const updateWorkflowState = useCallback((patch) => {
    if (!patch) return;
    if (patch.sessionId || patch.session_id) {
      const sId = patch.sessionId || patch.session_id;
      setSessionId(sId);
      sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sId);
      const currBId = patch.businessId || patch.business_id || businessId;
      if (currBId) {
        sessionStorage.setItem(getSessionIdKey(currBId), sId);
      }
    }
    if (patch.analysisId || patch.analysis_id) {
      const aId = patch.analysisId || patch.analysis_id;
      setAnalysisId(aId);
      sessionStorage.setItem(STORAGE_KEYS.ANALYSIS_ID, aId);
      const currBId = patch.businessId || patch.business_id || businessId;
      if (currBId) {
        sessionStorage.setItem(getAnalysisIdKey(currBId), aId);
      }
    }
    if (patch.businessId || patch.business_id) {
      const bId = patch.businessId || patch.business_id;
      setBusinessId(bId);
      sessionStorage.setItem(STORAGE_KEYS.BUSINESS_ID, bId);
      if (bId !== businessId) {
        // Business switched! Retrieve business-scoped state so Grocery never leaks into Dairy or Saree
        const scopedSid = sessionStorage.getItem(getSessionIdKey(bId)) || '';
        setSessionId(scopedSid);

        const scopedAid = sessionStorage.getItem(getAnalysisIdKey(bId)) || '';
        setAnalysisId(scopedAid);

        let scopedFc = null;
        try {
          const raw = sessionStorage.getItem(getFinancialContextKey(bId));
          if (raw) scopedFc = JSON.parse(raw);
        } catch (e) {}
        setFinancialContext(scopedFc);

        let scopedFa = null;
        try {
          const raw = sessionStorage.getItem(getFinancialAnalysisKey(bId));
          if (raw) scopedFa = JSON.parse(raw);
        } catch (e) {}
        setFinancialAnalysis(scopedFa);
      }
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
    const currentBId = patch.businessId || patch.business_id || businessId;
    if (patch.financialContext !== undefined || patch.financial_context !== undefined) {
      const fc = patch.financialContext !== undefined ? patch.financialContext : patch.financial_context;
      setFinancialContext(fc);
      if (fc) {
        try {
          sessionStorage.setItem(STORAGE_KEYS.FINANCIAL_CONTEXT, JSON.stringify(fc));
          if (currentBId) sessionStorage.setItem(getFinancialContextKey(currentBId), JSON.stringify(fc));
        } catch (e) {}
      } else {
        try {
          sessionStorage.removeItem(STORAGE_KEYS.FINANCIAL_CONTEXT);
          if (currentBId) sessionStorage.removeItem(getFinancialContextKey(currentBId));
        } catch (e) {}
      }
    }
    if (patch.financialAnalysis !== undefined || patch.financial_analysis !== undefined) {
      const fa = patch.financialAnalysis !== undefined ? patch.financialAnalysis : patch.financial_analysis;
      setFinancialAnalysis(fa);
      if (fa) {
        try {
          sessionStorage.setItem(STORAGE_KEYS.FINANCIAL_ANALYSIS, JSON.stringify(fa));
          if (currentBId) sessionStorage.setItem(getFinancialAnalysisKey(currentBId), JSON.stringify(fa));
        } catch (e) {}
      } else {
        try {
          sessionStorage.removeItem(STORAGE_KEYS.FINANCIAL_ANALYSIS);
          if (currentBId) sessionStorage.removeItem(getFinancialAnalysisKey(currentBId));
        } catch (e) {}
      }
    }
  }, [businessId]);

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

  // Asynchronous Orchestrator Execution: Starts backend DAG and polls status
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
      // Step 1: Start Orchestrator Pipeline Asynchronously (returns 202 Accepted)
      const startRes = await apiService.orchestrator.start(sId, { session_id: sId, analysis_id: aId });
      const activeAid = startRes.analysis_id || aId || sId;
      if (activeAid && activeAid !== analysisId) {
        setAnalysisId(activeAid);
      }

      // If already complete, immediately finish
      if (startRes.status === 'ALREADY_COMPLETE' && startRes.result) {
        setOrchestrationProgress(100);
        updateWorkflowState({
          sessionId: sId,
          analysisId: activeAid,
          currentStage: 12,
          completedStages: [1, 2, 3, 4, 5, 8, 9, 10, 11, 12],
          availableStages: [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13],
          lockedStages: [14, 15],
          workflowStatus: 'FEASIBILITY_COMPLETE',
          journeyStatus: {
            understand: 'COMPLETED',
            discover: 'COMPLETED',
            validate: 'COMPLETED',
            finance: 'COMPLETED',
            prepare: 'COMPLETED',
            grow: 'ACTIVE'
          }
        });
        return { success: true, status: 'FEASIBILITY_COMPLETE' };
      }

      // Step 2: Poll backend status endpoint until completion
      const maxPollAttempts = 40; // 60 seconds max
      let pollCount = 0;
      let finalStatus = null;

      while (pollCount < maxPollAttempts) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
        pollCount += 1;

        try {
          const pollData = await apiService.orchestrator.getStatus(activeAid);
          if (pollData) {
            if (pollData.progress) {
              setOrchestrationProgress(pollData.progress);
            }

            // Update live stage outputs as agents complete
            const completed = pollData.completed_agents || [];
            const newOutputs = {};
            if (completed.includes('market_intelligence_agent')) newOutputs.market_intelligence = 'Demand Strong ✓';
            if (completed.includes('opportunity_evaluation_engine')) newOutputs.opportunity_evaluation = 'Opportunity Synthesized ✓';
            if (completed.includes('finance_engine')) newOutputs.financial_planning = 'Financing Structured ✓';
            if (completed.includes('entrepreneur_profile_engine')) newOutputs.entrepreneur_profile = 'Readiness Assessed ✓';
            if (completed.includes('risk_engine')) newOutputs.risk_analysis = 'Risk Vectors Evaluated ✓';
            if (completed.includes('feasibility_engine')) newOutputs.feasibility_assessment = 'Feasibility Viable ✓';
            if (Object.keys(newOutputs).length > 0) {
              setEngineOutputs(prev => ({ ...prev, ...newOutputs }));
            }

            if (pollData.workflow_status === 'COMPLETED' || pollData.workflow_status === 'ORCHESTRATION_COMPLETE' || pollData.workflow_status === 'FEASIBILITY_COMPLETE') {
              finalStatus = pollData;
              break;
            }

            if (pollData.workflow_status === 'STAGE_10_CLARIFICATION_REQUIRED') {
              finalStatus = pollData;
              break;
            }

            if (pollData.workflow_status === 'FAILED') {
              throw new Error(pollData.error || 'Orchestrator pipeline execution failed on backend');
            }
          }
        } catch (pollErr) {
          console.warn('[ORCHESTRATOR POLL NOTE]', pollErr.message);
        }
      }

      setOrchestrationProgress(100);

      // Step 3: Handle Final State
      if (finalStatus?.workflow_status === 'STAGE_10_CLARIFICATION_REQUIRED') {
        updateWorkflowState({
          sessionId: sId,
          analysisId: activeAid,
          currentStage: 10,
          completedStages: [1, 2, 3, 4, 5, 8, 9],
          availableStages: [1, 2, 3, 4, 5, 8, 9, 10],
          lockedStages: [11, 12, 13, 14, 15],
          workflowStatus: 'STAGE_10_CLARIFICATION_REQUIRED',
          journeyStatus: {
            understand: 'COMPLETED',
            discover: 'COMPLETED',
            validate: 'COMPLETED',
            finance: 'COMPLETED',
            prepare: 'ACTIVE',
            grow: 'LOCKED'
          }
        });
        return { success: true, status: 'STAGE_10_CLARIFICATION_REQUIRED' };
      }

      setEngineOutputs((prev) => ({
        ...prev,
        market_intelligence: 'Demand Strong ✓',
        opportunity_evaluation: 'Opportunity Synthesized ✓',
        financial_planning: 'Financing Structured ✓',
        entrepreneur_profile: 'Readiness Assessed ✓',
        risk_analysis: 'Risk Vectors Evaluated ✓',
        feasibility_assessment: 'Feasibility Viable ✓',
      }));

      updateWorkflowState({
        sessionId: sId,
        analysisId: activeAid,
        currentStage: 13,
        completedStages: [1, 2, 3, 4, 5, 8, 9, 10, 11, 12],
        availableStages: [1, 2, 3, 4, 5, 8, 9, 10, 11, 12, 13],
        lockedStages: [14, 15],
        workflowStatus: 'FEASIBILITY_COMPLETE',
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
        status: 'FEASIBILITY_COMPLETE'
      };

    } catch (err) {
      console.error('[ORCHESTRATOR EXECUTION ERROR]', err);
      setWorkflowError(err.message || 'Orchestration execution failed');
      throw err;
    } finally {
      setIsOrchestrating(false);
    }
  }, [sessionId, analysisId, updateWorkflowState]);

  // Reset workflow for new session
  const resetWorkflow = useCallback(() => {
    setSessionId('');
    setAnalysisId('');
    setBusinessId('');
    setBusinessName('');
    setCurrentStage(1);
    setWorkflowStatus('IDLE');
    setCompletedStages([]);
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
    setFinancialContext(null);
    setFinancialAnalysis(null);
    setWorkflowError(null);
    try {
      sessionStorage.removeItem(STORAGE_KEYS.STATE);
      sessionStorage.removeItem(STORAGE_KEYS.SESSION_ID);
      sessionStorage.removeItem(STORAGE_KEYS.ANALYSIS_ID);
      sessionStorage.removeItem(STORAGE_KEYS.BUSINESS_ID);
      sessionStorage.removeItem(STORAGE_KEYS.BUSINESS_NAME);
      sessionStorage.removeItem(STORAGE_KEYS.FINANCIAL_CONTEXT);
      sessionStorage.removeItem(STORAGE_KEYS.FINANCIAL_ANALYSIS);
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
    financialContext,
    financialAnalysis,
    setFinancialContext,
    setFinancialAnalysis,
    setSessionId,
    setAnalysisId,
    setBusinessId,
    setBusinessName,
    updateWorkflowState,
    markStageComplete,
    restoreWorkflowState,
    runOrchestratorPipeline,
    resetWorkflow,
    setEngineOutputs,
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
