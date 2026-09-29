import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

// Helper for proxying GET requests
const proxyGet = async (url, req, res, errorContext, timeout = 30000) => {
  try {
    const aiResponse = await axios.get(url, {
      params: req.query,
      timeout,
    });

    // Hard Cross-Business Contamination Check
    const reqBizId = (req.params?.id || req.query?.business_id || '').trim();
    const retBizId = (aiResponse.data?.business_id || '').trim();
    if (reqBizId && retBizId && reqBizId.toLowerCase() !== retBizId.toLowerCase()) {
      logger.error(`[DPR_STATE_ISOLATION_ERROR] Gateway detected business mismatch! requested=${reqBizId}, returned=${retBizId}`);
      return res.status(409).json({
        error: 'DPR_STATE_ISOLATION_ERROR',
        message: `Gateway state isolation error: requested_business_id=${reqBizId}, returned_business_id=${retBizId}`
      });
    }

    if (process.env.NODE_ENV !== 'production' || true) {
      const sId = req.query?.scenario_id || req.body?.scenario_id || aiResponse.data?.scenario_id || (req.params?.id ? `DPR-${req.params.id.trim().slice(0, 8)}` : 'none');
      console.log(`[DPR_STATE_TRACE]
route: ${req.originalUrl || req.url}
business_id: ${req.params?.id ? req.params.id.trim() : (req.query?.business_id || 'none')}
scenario_id: ${sId}
intake_id: ${req.query?.intake_id || req.body?.intake_id || aiResponse.data?.intake_id || 'none'}
session_id: ${req.headers?.['x-session-id'] || 'none'}
context_key: dpr_context:${req.params?.id ? req.params.id.trim() : 'none'}:${sId}
enrichment_key: dpr_enrichment:${req.params?.id ? req.params.id.trim() : 'none'}:${sId}
financial_package_key: fin:${req.params?.id ? req.params.id.trim() : 'none'}`);
    }

    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET ${url}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to communicate with AI Service (${errorContext})`,
      details: error.message,
    });
  }
};

// Helper for proxying POST requests
const proxyPost = async (url, req, res, errorContext, timeout = 45000) => {
  try {
    const aiResponse = await axios.post(url, req.body || {}, {
      params: req.query,
      headers: { 'Content-Type': 'application/json' },
      timeout,
    });

    // Hard Cross-Business Contamination Check
    const reqBizId = (req.params?.id || req.query?.business_id || '').trim();
    const retBizId = (aiResponse.data?.business_id || '').trim();
    if (reqBizId && retBizId && reqBizId.toLowerCase() !== retBizId.toLowerCase()) {
      logger.error(`[DPR_STATE_ISOLATION_ERROR] Gateway detected business mismatch! requested=${reqBizId}, returned=${retBizId}`);
      return res.status(409).json({
        error: 'DPR_STATE_ISOLATION_ERROR',
        message: `Gateway state isolation error: requested_business_id=${reqBizId}, returned_business_id=${retBizId}`
      });
    }

    if (process.env.NODE_ENV !== 'production' || true) {
      const sId = req.query?.scenario_id || req.body?.scenario_id || aiResponse.data?.scenario_id || (req.params?.id ? `DPR-${req.params.id.slice(0, 8)}` : 'none');
      console.log(`[DPR_STATE_TRACE]
route: ${req.originalUrl || req.url}
business_id: ${req.params?.id || req.query?.business_id || 'none'}
scenario_id: ${sId}
intake_id: ${req.query?.intake_id || req.body?.intake_id || aiResponse.data?.intake_id || 'none'}
session_id: ${req.headers?.['x-session-id'] || 'none'}
context_key: dpr_context:${req.params?.id || 'none'}:${sId}
enrichment_key: dpr_enrichment:${req.params?.id || 'none'}:${sId}
financial_package_key: fin:${req.params?.id || 'none'}`);
    }

    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying POST ${url}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to communicate with AI Service (${errorContext})`,
      details: error.message,
    });
  }
};

// ============================================================================
// STAGE 14.1 CONTROLLER METHODS
// ============================================================================

export const getContext = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Fetch DPR context for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/context/${id}`, req, res, 'DPR Context');
};

export const getGapAnalysis = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Fetch DPR gap analysis for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/gap-analysis/${id}`, req, res, 'DPR Gap Analysis');
};

export const getSections = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Fetch DPR sections for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/sections/${id}`, req, res, 'DPR Sections');
};

export const getAssumptions = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Fetch DPR assumptions for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/assumptions/${id}`, req, res, 'DPR Assumptions');
};

export const getNextQuestion = async (req, res, next) => {
  const id = req.params.id || req.query.business_id;
  console.log(`[GATEWAY STAGE 14.1] Fetch next DPR question for business_id=${id}`);
  if (req.params.id) {
    return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/question/next/${id}`, req, res, 'DPR Next Question');
  }
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/question/next`, req, res, 'DPR Next Question');
};

export const answerQuestion = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Answer DPR question for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/question/answer/${id}`, req, res, 'DPR Answer Question', 60000);
};

export const setOverride = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Set DPR override for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/override/${id}`, req, res, 'DPR Set Override', 60000);
};

export const acceptBenchmark = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Accept benchmark for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/benchmark/accept/${id}`, req, res, 'DPR Accept Benchmark', 60000);
};

export const updateDocument = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Update DPR document for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/document/update/${id}`, req, res, 'DPR Update Document');
};

export const triggerRecalculation = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Trigger DPR recalculation for business_id=${id}`);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/recalculate/${id}`, req, res, 'DPR Recalculate', 60000);
};

export const getReadiness = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Get DPR readiness for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/readiness/${id}`, req, res, 'DPR Readiness');
};

export const getContextPackage = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Get DPR context package for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/package/${id}`, req, res, 'DPR Context Package');
};

export const getStage14Handoff = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Get Stage 14 handoff for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/handoff/${id}`, req, res, 'DPR Stage 14 Handoff');
};

export const submitStage14Intake = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Submit Stage 14 intake for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/intake/${id}`, req, res, 'DPR Submit Intake');
};

export const createNewScenario = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Create new scenario for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/new-scenario/${id}`, req, res, 'DPR Create New Scenario', 30000);
};

// Audio Transcribe & Synthesize
export const transcribeAudio = async (req, res, next) => {
  console.log('[GATEWAY STAGE 14.1] Forwarding DPR audio for transcription');
  try {
    const lang = req.query.language_code || req.query.language || 'en';
    const response = await axios({
      method: 'POST',
      url: `${config.aiServiceUrl}/api/v1/dpr/audio/transcribe?language_code=${encodeURIComponent(lang)}`,
      data: req,
      headers: {
        'content-type': req.headers['content-type'],
      },
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
      timeout: 45000,
    });
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/dpr/audio/transcribe:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      transcript: '',
      error: 'Audio transcription proxy error',
      details: error.message,
    });
  }
};

export const synthesizeAudio = async (req, res, next) => {
  console.log('[GATEWAY STAGE 14.1] Forwarding DPR audio synthesis');
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/audio/synthesize`, req, res, 'DPR Audio Synthesize');
};

export const getDebugLineage = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.1] Get debug lineage for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/stage1/debug/lineage/${id}`, req, res, 'DPR Stage 1 Debug Lineage');
};

// ============================================================================
// STAGE 14.2 CONTROLLER METHODS
// ============================================================================

export const get14_2Context = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get 14.2 context for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/14.2/context/${id}`, req, res, 'DPR 14.2 Context');
};

export const get14_2Enrichment = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get 14.2 enrichment for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/14.2/enrichment/${id}`, req, res, 'DPR 14.2 Enrichment');
};

export const get14_2Gaps = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get 14.2 gaps for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/14.2/gaps/${id}`, req, res, 'DPR 14.2 Gaps');
};

export const answer14_2Question = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Answer 14.2 question for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/14.2/answer/${id}`, req, res, 'DPR 14.2 Answer Question', 60000);
};

export const accept14_2Benchmark = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Accept 14.2 benchmark for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/14.2/benchmark/accept/${id}`, req, res, 'DPR 14.2 Accept Benchmark', 60000);
};

export const update14_2Document = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Update 14.2 document for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/14.2/document/${id}`, req, res, 'DPR 14.2 Update Document');
};

export const update14_2Assumption = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Update 14.2 assumption for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/14.2/assumption/${id}`, req, res, 'DPR 14.2 Update Assumption', 60000);
};

export const get14_2Validation = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get 14.2 validation for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/14.2/validation/${id}`, req, res, 'DPR 14.2 Validation');
};

export const get14_2Readiness = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get 14.2 readiness for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/14.2/readiness/${id}`, req, res, 'DPR 14.2 Readiness');
};

export const getEnrichment = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get enrichment for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/enrichment/${id}`, req, res, 'DPR Enrichment');
};

export const runEnrichment = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Run enrichment for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/enrichment/run/${id}`, req, res, 'DPR Run Enrichment', 60000);
};

export const getEnrichmentAssumptions = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get enrichment assumptions for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/enrichment/assumptions/${id}`, req, res, 'DPR Enrichment Assumptions');
};

export const updateEnrichmentAssumption = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Update enrichment assumption for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/enrichment/assumption/${id}`, req, res, 'DPR Update Enrichment Assumption', 60000);
};

export const getEnrichmentStatus = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.2] Get enrichment status for business_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/enrichment/status/${id}`, req, res, 'DPR Enrichment Status');
};

// ============================================================================
// STAGE 14 GENERATION & PDF EXPORT
// ============================================================================

export const generateDpr = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Generate DPR request for business_id=${id}`);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/generate/${id}`, req, res, 'DPR Generator', 60000);
};

export const getDprReport = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Fetch DPR report for report_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/report/${id}`, req, res, 'DPR Report');
};

export const downloadDprPdf = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Download DPR PDF for report_id=${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/dpr/report/${id}/pdf`,
      { responseType: 'stream', timeout: 45000 }
    );
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="Bankable_DPR_${id}.pdf"`);
    aiResponse.data.pipe(res);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/dpr/report/pdf:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to download DPR PDF',
      details: error.message,
    });
  }
};

// ============================================================================
// STAGE 14.3: INSTITUTIONAL BANK-REVIEW DPR ENGINE
// ============================================================================

export const generate14_3Dpr = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.3] Generate Institutional DPR for business_id=${id}`, req.body);
  return proxyPost(`${config.aiServiceUrl}/api/v1/dpr/14.3/generate/${id}`, req, res, 'DPR 14.3 Generator', 180000);
};

export const get14_3Status = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.3] Fetch DPR status for document_id=${id}`);
  return proxyGet(`${config.aiServiceUrl}/api/v1/dpr/14.3/status/${id}`, req, res, 'DPR 14.3 Status');
};

export const preview14_3Pdf = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.3] Preview DPR PDF for document_id=${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/dpr/14.3/preview/${id}`,
      { responseType: 'stream', timeout: 60000 }
    );
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `inline; filename="${id}.pdf"`);
    res.setHeader('Content-Security-Policy', "frame-ancestors 'self' http://localhost:5173 http://localhost:5174 http://127.0.0.1:5173 http://127.0.0.1:5174");
    res.removeHeader('X-Frame-Options');
    aiResponse.data.pipe(res);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/dpr/14.3/preview:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to preview DPR PDF',
      details: error.message,
    });
  }
};

export const download14_3Pdf = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14.3] Download DPR PDF for document_id=${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/dpr/14.3/download/${id}`,
      { responseType: 'stream', timeout: 60000 }
    );
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="Bank_Review_DPR_${id}.pdf"`);
    aiResponse.data.pipe(res);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/dpr/14.3/download:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to download DPR PDF',
      details: error.message,
    });
  }
};

export default {
  getContext,
  getGapAnalysis,
  getSections,
  getAssumptions,
  getNextQuestion,
  answerQuestion,
  setOverride,
  acceptBenchmark,
  updateDocument,
  triggerRecalculation,
  getReadiness,
  getContextPackage,
  getStage14Handoff,
  submitStage14Intake,
  createNewScenario,
  transcribeAudio,
  synthesizeAudio,
  getDebugLineage,
  get14_2Context,
  get14_2Enrichment,
  get14_2Gaps,
  answer14_2Question,
  accept14_2Benchmark,
  update14_2Document,
  update14_2Assumption,
  get14_2Validation,
  get14_2Readiness,
  getEnrichment,
  runEnrichment,
  getEnrichmentAssumptions,
  updateEnrichmentAssumption,
  getEnrichmentStatus,
  generateDpr,
  getDprReport,
  downloadDprPdf,
  generate14_3Dpr,
  get14_3Status,
  preview14_3Pdf,
  download14_3Pdf,
};
