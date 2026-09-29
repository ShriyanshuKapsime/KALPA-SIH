import React from 'react';
import { useNavigate, useLocation } from 'react-router-dom';
import { Check } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useWorkflow } from '../../context/WorkflowContext';
import { useLanguage } from '../../context/LanguageContext';

/**
 * 4-Level Agentic Workflow Definition:
 * Level 1: 01 User Intake
 * Level 2: 02 Classification / Profile (Encompasses 2.1 Classification & 2.2 Profile)
 * Level 3: 03 KALPA Manager (Orchestrator, parent of 6 downstream engines)
 *          ├── Market Intelligence
 *          ├── Opportunity
 *          ├── Finance
 *          ├── Feasibility
 *          ├── SWOT
 *          └── DPR
 * Level 4: 04 KALPA Growth Manager (Final downstream autonomous assistant)
 */
export const TOP_LEVEL_STAGES = [
  {
    stepNum: 1,
    id: 'intake',
    labelKey: 'step_1',
    label: '01 User Intake',
    shortLabel: 'User Intake',
    path: '/intake',
    backendStageNums: [1],
  },
  {
    stepNum: 2,
    id: 'classification_profile',
    labelKey: 'step_2',
    label: '02 Classification / Profile',
    shortLabel: 'Classification / Profile',
    path: '/classification',
    backendStageNums: [2, 3],
  },
  {
    stepNum: 3,
    id: 'manager',
    labelKey: 'step_manager',
    label: '03 KALPA Manager',
    shortLabel: 'KALPA Manager',
    path: '/orchestrator',
    backendStageNums: [4, 5, 8, 9, 10, 11, 12, 13],
  },
  {
    stepNum: 4,
    id: 'growth_manager',
    labelKey: 'step_growth_manager',
    label: '04 KALPA Growth Manager',
    shortLabel: 'Growth Manager',
    path: '/growth-manager',
    backendStageNums: [14, 15, 16],
  },
];

export const ORCHESTRATOR_CHILDREN = [
  {
    id: 'market_intelligence',
    labelKey: 'market_intel',
    label: 'Market Intelligence',
    shortLabel: 'Market Intel',
    path: '/market-intelligence',
    backendStageNums: [5],
  },
  {
    id: 'opportunity',
    labelKey: 'opportunity',
    label: 'Opportunity',
    shortLabel: 'Opportunity',
    path: '/opportunity-evaluation',
    backendStageNums: [8],
  },
  {
    id: 'finance',
    labelKey: 'finance',
    label: 'Finance',
    shortLabel: 'Finance',
    path: '/financial-planning',
    backendStageNums: [9],
  },
  {
    id: 'feasibility',
    labelKey: 'feasibility',
    label: 'Feasibility',
    shortLabel: 'Feasibility',
    path: '/feasibility',
    backendStageNums: [10],
  },
  {
    id: 'swot',
    labelKey: 'swot',
    label: 'SWOT',
    shortLabel: 'SWOT',
    path: '/swot',
    backendStageNums: [11],
  },
  {
    id: 'dpr',
    labelKey: 'dpr',
    label: 'DPR',
    shortLabel: 'DPR',
    path: '/dpr',
    backendStageNums: [12, 13, 14],
  },
];

export const AgenticWorkflowThread = ({ currentStepNumber = null, className = '' }) => {
  const navigate = useNavigate();
  const location = useLocation();
  const { sessionId, analysisId, completedStages = [], currentStage: ctxStage } = useWorkflow();
  const { t } = useLanguage();

  const currentPath = location.pathname;

  // Determine active top-level step and active child if inside orchestrator
  let activeStep = currentStepNumber;
  let activeChildId = null;

  if (activeStep === null) {
    if (currentPath.startsWith('/intake')) {
      activeStep = 1;
    } else if (currentPath.startsWith('/classification') || currentPath.startsWith('/profile')) {
      activeStep = 2;
    } else if (currentPath.startsWith('/growth-manager') || currentPath.startsWith('/assistant') || currentPath.startsWith('/grow')) {
      activeStep = 4;
    } else {
      // Orchestrator routes
      activeStep = 3;
      const matchedChild = ORCHESTRATOR_CHILDREN.find((c) => currentPath.startsWith(c.path));
      activeChildId = matchedChild ? matchedChild.id : null;
    }
  } else if (activeStep === 3) {
    const matchedChild = ORCHESTRATOR_CHILDREN.find((c) => currentPath.startsWith(c.path));
    activeChildId = matchedChild ? matchedChild.id : null;
  }

  // Active top-level stage object
  const activeStageObj = TOP_LEVEL_STAGES.find((s) => s.stepNum === activeStep) || TOP_LEVEL_STAGES[0];
  const activeChildObj = ORCHESTRATOR_CHILDREN.find((c) => c.id === activeChildId);

  // Helper to preserve URL params for clean stateful routing
  const getStageUrl = (basePath) => {
    const params = new URLSearchParams();
    if (sessionId) params.set('session_id', sessionId);
    if (analysisId) params.set('analysis_id', analysisId);
    const qs = params.toString();
    return qs ? `${basePath}?${qs}` : basePath;
  };

  // State evaluation helper for top-level stages: strictly from actual completedStages
  const isTopStageCompleted = (stage) => {
    if (stage.stepNum === 1) {
      return completedStages.includes(1);
    }
    if (stage.stepNum === 2) {
      return (
        (completedStages.includes(2) && completedStages.includes(3)) ||
        completedStages.some((num) => [4, 5, 8, 9, 10, 11, 12, 13, 14, 15, 16].includes(num))
      );
    }
    if (stage.stepNum === 3) {
      return (
        completedStages.includes(12) ||
        completedStages.includes(13) ||
        completedStages.includes(14) ||
        completedStages.includes(15) ||
        completedStages.includes(16) ||
        activeStep === 4
      );
    }
    if (stage.stepNum === 4) {
      return (
        completedStages.includes(14) ||
        completedStages.includes(15) ||
        completedStages.includes(16) ||
        Boolean(sessionStorage.getItem('kalpa_business_launched'))
      );
    }
    return false;
  };

  // State evaluation helper for orchestrator child items
  const isChildCompleted = (child) => {
    if (child.id === 'dpr') {
      return (
        completedStages.includes(11) ||
        completedStages.includes(12) ||
        completedStages.includes(13) ||
        completedStages.includes(14) ||
        completedStages.includes(15) ||
        currentPath.startsWith('/dpr') ||
        currentPath.startsWith('/swot')
      );
    }
    return child.backendStageNums.some((num) => completedStages.includes(num));
  };

  // Enforce access control on navigation: only genuinely completed stages or current stage
  const handleNodeClick = (stage, isCompleted) => {
    if (!isCompleted && stage.stepNum !== activeStep) return;
    navigate(getStageUrl(stage.path));
  };

  const handleChildClick = (child, isCompleted) => {
    if (!isCompleted) return;
    navigate(getStageUrl(child.path));
  };

  return (
    <div className={`w-full ${className}`}>
      {/* Subtle Progress Header Indicator */}
      <div className="flex items-center justify-between gap-4 mb-2.5 px-1">
        <div className="flex items-center gap-2">
          <span className="text-xs font-bold text-[#7A563E] uppercase tracking-wider">
            {activeStep === 3 && activeChildObj
              ? `${t('step_manager', 'KALPA MANAGER')} · ${t(activeChildObj.labelKey, activeChildObj.label)}`
              : t(activeStageObj.labelKey, activeStageObj.label)}
          </span>
          <span className="text-xs text-[#7A563E]/60 font-medium">·</span>
          <span className="text-xs font-semibold text-[#6F746E]">
            {t('step_of', 'Step')} {activeStep} {t('of_steps', 'of 4')}
          </span>
        </div>
        <span className="text-[11px] text-[#7A563E]/75 font-medium hidden sm:inline-block">
          Autonomous Livelihood Pipeline
        </span>
      </div>

      {/* Lightweight Horizontal Workflow Thread */}
      <div className="w-full overflow-x-auto pb-2 pt-1 no-scrollbar">
        <div className="flex flex-col gap-2 min-w-[780px] lg:min-w-full px-1 py-1">
          {/* Top-Level Journey Path */}
          <div className="flex items-center justify-between relative">
            {TOP_LEVEL_STAGES.map((stage, idx) => {
              const isCurrent = stage.stepNum === activeStep;
              const isCompleted = isTopStageCompleted(stage);
              const stageLabel = t(stage.labelKey, stage.label);

              return (
                <React.Fragment key={stage.id}>
                  {/* Top-Level Node */}
                  <div
                    className={`flex items-center gap-2 transition-all relative py-1 px-1.5 rounded-xl ${
                      isCompleted
                        ? 'cursor-pointer group'
                        : isCurrent
                        ? 'cursor-default'
                        : 'cursor-not-allowed opacity-60'
                    }`}
                    onClick={() => handleNodeClick(stage, isCompleted)}
                    role={isCompleted ? 'button' : 'presentation'}
                    tabIndex={isCompleted ? 0 : -1}
                    aria-label={`${stageLabel} ${
                      isCurrent ? '(Current)' : isCompleted ? '(Completed)' : '(Locked)'
                    }`}
                  >
                    {/* Active State Travelling Pill Background (Framer Motion) */}
                    {isCurrent && (
                      <motion.div
                        layoutId="activeWorkflowPill"
                        className="absolute inset-0 bg-[#7A563E]/10 border border-[#7A563E]/25 rounded-xl -z-0"
                        transition={{ type: 'spring', stiffness: 350, damping: 30 }}
                      />
                    )}

                    {/* Node Circle */}
                    <div
                      className={`w-6 h-6 rounded-full flex items-center justify-center transition-all duration-300 text-[11px] font-bold shrink-0 relative z-10 ${
                        isCurrent
                          ? 'bg-[#7A563E] text-[#FAF4E8] ring-4 ring-[#7A563E]/20 shadow-sm'
                          : isCompleted
                          ? 'bg-[#006B59] text-white shadow-2xs'
                          : 'bg-[#F5EBD9] border border-[#BFA47D]/50 text-[#8C7E72]'
                      }`}
                    >
                      {isCompleted && !isCurrent ? (
                        <Check className="w-3.5 h-3.5 stroke-[2.5]" />
                      ) : (
                        stage.stepNum
                      )}
                    </div>

                    {/* Node Label */}
                    <span
                      className={`text-xs whitespace-nowrap transition-colors relative z-10 ${
                        isCurrent
                          ? 'font-bold text-[#7A563E]'
                          : isCompleted
                          ? 'font-semibold text-[#26332F] group-hover:text-[#006B59]'
                          : 'font-medium text-[#8C7E72]'
                      }`}
                    >
                      {stageLabel}
                    </span>
                  </div>

                  {/* Connecting Line between stages */}
                  {idx < TOP_LEVEL_STAGES.length - 1 && (
                    <div className="flex-grow flex items-center mx-3 min-w-[24px]">
                      <div
                        className={`h-[2px] w-full transition-colors duration-300 ${
                          isCompleted ? 'bg-[#006B59]' : 'bg-[#BFA47D]/35'
                        }`}
                      />
                    </div>
                  )}
                </React.Fragment>
              );
            })}
          </div>

          {/* Level 3: Nested Orchestrator Branch (Inside KALPA Manager) */}
          <AnimatePresence>
            {activeStep === 3 && (
              <motion.div
                initial={{ opacity: 1, height: 'auto' }}
                exit={{ opacity: 0, height: 0, overflow: 'hidden' }}
                transition={{ duration: 0.3 }}
                className="mt-1 pl-4 sm:pl-8"
              >
                <div className="bg-[#FAF2E3] border border-[#BFA47D]/40 rounded-xl px-3 py-2 shadow-2xs">
                  <div className="flex items-center justify-between mb-1.5 px-0.5">
                    <div className="flex items-center gap-1.5">
                      <span className="text-[10px] font-extrabold uppercase tracking-widest text-[#7A563E]">
                        ORCHESTRATOR
                      </span>
                      <span className="text-[10px] text-[#7A563E]/70 font-medium">
                        · Internal Agent Pipeline
                      </span>
                    </div>
                    <span className="text-[10px] text-[#6F746E] italic hidden sm:inline-block">
                      Automated Autonomous Multi-Agent Synthesis
                    </span>
                  </div>

                  {/* 6 Orchestrator Child Stages */}
                  <div className="grid grid-cols-6 gap-1.5">
                    {ORCHESTRATOR_CHILDREN.map((child) => {
                      const isCurrent = activeStep === 3 && activeChildId === child.id;
                      const isCompleted = isChildCompleted(child);
                      const childLabel = t(child.labelKey, child.shortLabel);

                      return (
                        <button
                          key={child.id}
                          type="button"
                          disabled={!isCompleted}
                          onClick={() => handleChildClick(child, isCompleted)}
                          className={`flex items-center justify-center gap-1.5 px-2 py-1 rounded-lg text-[11px] transition-all whitespace-nowrap ${
                            isCurrent
                              ? 'bg-[#7A563E] text-[#FAF4E8] font-bold shadow-2xs cursor-default'
                              : isCompleted
                              ? 'text-[#006B59] hover:bg-[#006B59]/10 cursor-pointer font-semibold'
                              : 'text-[#8C7E72]/70 cursor-not-allowed font-medium'
                          }`}
                          aria-label={`${childLabel} ${
                            isCurrent ? '(Current)' : isCompleted ? '(Completed)' : '(Locked)'
                          }`}
                        >
                          <span
                            className={`w-1.5 h-1.5 rounded-full shrink-0 ${
                              isCurrent
                                ? 'bg-[#FAF4E8]'
                                : isCompleted
                                ? 'bg-[#006B59]'
                                : 'bg-[#BFA47D]/60'
                            }`}
                          />
                          <span className="truncate">{childLabel}</span>
                        </button>
                      );
                    })}
                  </div>
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      </div>
    </div>
  );
};

export default AgenticWorkflowThread;
