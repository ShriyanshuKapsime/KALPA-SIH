import { Router } from 'express';
import healthController from '../controllers/healthController.js';
import intakeController from '../controllers/intakeController.js';
import classificationController from '../controllers/classificationController.js';
import profileController from '../controllers/profileController.js';
import orchestratorController from '../controllers/orchestratorController.js';
import knowledgeController from '../controllers/knowledgeController.js';
import marketIntelligenceController from '../controllers/marketIntelligenceController.js';
import opportunityEvaluationController from '../controllers/opportunityEvaluationController.js';
import financialAnalysisController from '../controllers/financialAnalysisController.js';
import entrepreneurProfileController from '../controllers/entrepreneurProfileController.js';
import riskAnalysisController from '../controllers/riskAnalysisController.js';
import feasibilityController from '../controllers/feasibilityController.js';
import swotController from '../controllers/swotController.js';
import assistantController from '../controllers/assistantController.js';
import dprController from '../controllers/dprController.js';
import translationController from '../controllers/translationController.js';


const router = Router();

// Translation Engine Routes
router.post('/translate/text', translationController.translateText);
router.post('/translate/batch', translationController.translateBatch);
router.post('/translate/object', translationController.translateObject);

// Subsystem health proxy
router.get('/health/ai', healthController.getAIHealth);

// Stage 1 Live Intake Routes
router.post('/intake/text', intakeController.submitTextIntake);
router.post('/intake/voice', intakeController.submitVoiceIntake);
router.post('/intake/transcribe', intakeController.transcribeVoice);
router.post('/intake/continue', intakeController.continueIntake);
router.get('/intake/session/:id', intakeController.getIntakeSession);

// Stage 2 Live Classification Routes
router.post('/classification/classify', classificationController.classifyBusiness);
router.post('/classification/clarify', classificationController.clarifyClassification);
router.get('/classification/nic/:code', classificationController.getNICDetails);
router.get('/classification/:id', classificationController.getClassificationSession);

// Stage 3 Live Profile Store Routes
router.post('/profile/build', profileController.buildProfile);
router.get('/profile/session/:id', profileController.getProfileBySessionId);
router.get('/profile/:id', profileController.getProfileByAnalysisId);

// Stage 4 Live Manager Agent / Orchestrator Routes
router.post('/orchestrator/start', orchestratorController.startOrchestrator);
router.get('/orchestrator/status/:id', orchestratorController.getOrchestratorStatus);
router.get('/orchestrator/session/:id', orchestratorController.getOrchestratorBySessionId);
router.get('/orchestrator/workflow/:id', orchestratorController.getWorkflowStatus);
router.get('/orchestrator/:id', orchestratorController.getOrchestratorByAnalysisId);

// Stage 4.5 Live Domain Knowledge & Benchmark Hub Routes
router.get('/knowledge/coverage', knowledgeController.getCoverageReport);
router.get('/knowledge/sources', knowledgeController.getDataSources);
router.get('/knowledge/sources/:id', knowledgeController.getDataSourceById);
router.get('/knowledge/schemes', knowledgeController.getSchemes);
router.get('/knowledge/schemes/:id', knowledgeController.getSchemeById);
router.post('/knowledge/schemes/evaluate', knowledgeController.evaluateSchemeEligibility);
router.get('/knowledge/business-profiles', knowledgeController.getBusinessProfiles);
router.get('/knowledge/business-profiles/:id', knowledgeController.getBusinessProfileById);
router.get('/knowledge/benchmarks/financial', knowledgeController.getFinancialBenchmarks);
router.get('/knowledge/benchmarks/financial/:id', knowledgeController.getFinancialBenchmarkById);
router.get('/knowledge/benchmarks/market', knowledgeController.getMarketBenchmarks);
router.get('/knowledge/benchmarks/market/:id', knowledgeController.getMarketBenchmarkById);
router.get('/knowledge/market-pack/:id', knowledgeController.getMarketKnowledgePack);
router.get('/knowledge/financial-pack/:id', knowledgeController.getFinancialKnowledgePack);
router.post('/knowledge/financial-pack/calculate', knowledgeController.calculateFinancialFeasibility);
router.get('/knowledge/comprehensive-pack/:id', knowledgeController.getComprehensivePack);
router.get('/knowledge/business/:id/requirements', knowledgeController.getBusinessRequirements);
router.get('/knowledge/business/:id/pack', knowledgeController.getBusinessKnowledgePack);
router.get('/knowledge/risks', knowledgeController.getRisks);
router.get('/knowledge/documents', knowledgeController.getDocuments);
router.get('/knowledge/dynamic-requirements', knowledgeController.getDynamicRequirements);

// Stage 5 & 6 Live Market Intelligence Routes
router.post('/market-intelligence/collect', marketIntelligenceController.collectMarketEvidence);
router.post('/market-intelligence/analyze', marketIntelligenceController.analyzeMarketIntelligence);
router.get('/market-intelligence/tools/health', marketIntelligenceController.getToolHealthReport);
router.get('/market-intelligence/:id', marketIntelligenceController.getMarketEvidenceById);
router.post('/market-intelligence/:id/retry', marketIntelligenceController.retryMarketEvidence);

// Stage 8 Live Opportunity Evaluation Engine Routes
router.post('/opportunity-evaluation/analyze', opportunityEvaluationController.analyzeOpportunity);
router.get('/opportunity-evaluation/health', opportunityEvaluationController.getOpportunityEngineHealth);

// Stage 9 Live Financial Engine Routes
router.post('/financial-analysis/analyze', financialAnalysisController.analyzeFinancialProfile);
router.post('/financial-analysis/calculator', financialAnalysisController.calculateFinancials);
router.post('/financial-analysis/dpr-package', financialAnalysisController.getDprPackage);
router.get('/financial-analysis/health', financialAnalysisController.getFinancialEngineHealth);

// Stage 10 Live Entrepreneur Profile Engine Routes
router.post('/entrepreneur-profile/analyze', entrepreneurProfileController.analyzeEntrepreneurProfile);
router.post('/entrepreneur-profile/clarify', entrepreneurProfileController.clarifyEntrepreneurProfile);
router.get('/entrepreneur-profile/health', entrepreneurProfileController.getEntrepreneurProfileEngineHealth);

// Stage 11 Live Risk Engine Routes
router.post('/risk-analysis/analyze', riskAnalysisController.analyzeRiskProfile);
router.get('/risk-analysis/health', riskAnalysisController.getRiskEngineHealth);

// Stage 12 Live Feasibility Engine Routes
router.post('/feasibility/analyze', feasibilityController.analyzeFeasibility);
router.get('/feasibility/health', feasibilityController.getFeasibilityHealth);
router.get('/feasibility/:id/calculation', feasibilityController.getFeasibilityCalculation);
router.get('/feasibility/:id', feasibilityController.getFeasibilityById);
router.post('/feasibility/pivot-suggestions', feasibilityController.getPivotSuggestions);

// Stage 13 Live Dynamic SWOT Agent Routes
router.post('/swot/analyze', swotController.analyzeSWOT);
router.post('/swot/stream', swotController.streamSWOT);
router.get('/swot/health', swotController.getSWOTHealth);
router.get('/swot/:id', swotController.getSWOTById);

// Stage 15 Live Personal AI Business Assistant Routes
router.get('/assistant/health', assistantController.getAssistantHealth);
router.post('/assistant/chat', assistantController.chatWithAssistant);
router.post('/assistant/stt', assistantController.transcribeAssistantAudio);
router.post('/assistant/tts', assistantController.synthesizeAssistantSpeech);
router.get('/assistant/:id/history', assistantController.getAssistantHistory);
router.get('/assistant/history/:id', assistantController.getAssistantHistory);
router.get('/assistant/:id/context', assistantController.getAssistantContext);
router.get('/assistant/context/:id', assistantController.getAssistantContext);
router.delete('/assistant/:id/history', assistantController.clearAssistantHistory);
router.delete('/assistant/history/:id', assistantController.clearAssistantHistory);

// Locked Future Stages
router.all('/market/*', (req, res) => {
  res.status(501).json({
    status: 'scaffold_only',
    message: 'Market Intelligence Engine analysis endpoint will be activated in future phases.',
  });
});

// Stage 14.1 Live Enterprise DPR Intake & Gap Discovery Routes
router.get('/dpr/context/:id', dprController.getContext);
router.get('/dpr/gap-analysis/:id', dprController.getGapAnalysis);
router.get('/dpr/sections/:id', dprController.getSections);
router.get('/dpr/assumptions/:id', dprController.getAssumptions);
router.get('/dpr/question/next/:id', dprController.getNextQuestion);
router.get('/dpr/question/next', dprController.getNextQuestion);
router.post('/dpr/question/answer/:id', dprController.answerQuestion);
router.post('/dpr/override/:id', dprController.setOverride);
router.post('/dpr/benchmark/accept/:id', dprController.acceptBenchmark);
router.post('/dpr/document/update/:id', dprController.updateDocument);
router.post('/dpr/recalculate/:id', dprController.triggerRecalculation);
router.get('/dpr/readiness/:id', dprController.getReadiness);
router.get('/dpr/package/:id', dprController.getContextPackage);
router.get('/dpr/handoff/:id', dprController.getStage14Handoff);
router.post('/dpr/intake/:id', dprController.submitStage14Intake);
router.post('/dpr/new-scenario/:id', dprController.createNewScenario);
router.get('/dpr/stage1/debug/lineage/:id', dprController.getDebugLineage);
router.get('/dpr/debug/lineage/:id', dprController.getDebugLineage);
router.post('/dpr/audio/transcribe', dprController.transcribeAudio);
router.post('/dpr/audio/synthesize', dprController.synthesizeAudio);

// Stage 14.2 Live DPR Enrichment & Deterministic Inference Routes
router.get('/dpr/14.2/context/:id', dprController.get14_2Context);
router.get('/dpr/14.2/enrichment/:id', dprController.get14_2Enrichment);
router.get('/dpr/14.2/gaps/:id', dprController.get14_2Gaps);
router.post('/dpr/14.2/answer/:id', dprController.answer14_2Question);
router.post('/dpr/14.2/benchmark/accept/:id', dprController.accept14_2Benchmark);
router.post('/dpr/14.2/document/:id', dprController.update14_2Document);
router.post('/dpr/14.2/assumption/:id', dprController.update14_2Assumption);
router.get('/dpr/14.2/validation/:id', dprController.get14_2Validation);
router.get('/dpr/14.2/readiness/:id', dprController.get14_2Readiness);
router.get('/dpr/enrichment/assumptions/:id', dprController.getEnrichmentAssumptions);
router.post('/dpr/enrichment/assumption/:id', dprController.updateEnrichmentAssumption);
router.get('/dpr/enrichment/status/:id', dprController.getEnrichmentStatus);
router.get('/dpr/enrichment/:id', dprController.getEnrichment);
router.post('/dpr/enrichment/run/:id', dprController.runEnrichment);

// Stage 14 Live Bankable DPR Generator Routes
router.post('/dpr/generate/:id', dprController.generateDpr);
router.get('/dpr/report/:id/pdf', dprController.downloadDprPdf);
router.get('/dpr/report/:id', dprController.getDprReport);

// Stage 14.3 Institutional Bank-Review DPR Generator Routes
router.post('/dpr/14.3/generate/:id', dprController.generate14_3Dpr);
router.get('/dpr/14.3/status/:id', dprController.get14_3Status);
router.get('/dpr/14.3/preview/:id', dprController.preview14_3Pdf);
router.get('/dpr/14.3/download/:id', dprController.download14_3Pdf);
router.get('/dpr/14.3/document/:id/preview', dprController.preview14_3Pdf);
router.get('/dpr/14.3/document/:id/download', dprController.download14_3Pdf);

export default router;


