import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const startOrchestrator = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/orchestrator/start', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/orchestrator/start`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/orchestrator/start:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Orchestrator',
      details: error.message,
    });
  }
};

export const getOrchestratorByAnalysisId = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/orchestrator/${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/orchestrator/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/orchestrator/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve orchestration record from AI Service',
      details: error.message,
    });
  }
};

export const getOrchestratorBySessionId = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/orchestrator/session/${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/orchestrator/session/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/orchestrator/session/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve session orchestration record from AI Service',
      details: error.message,
    });
  }
};

export const getWorkflowStatus = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/orchestrator/workflow/${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/orchestrator/workflow/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/orchestrator/workflow/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve workflow status from AI Service',
      details: error.message,
    });
  }
};

export default {
  startOrchestrator,
  getOrchestratorByAnalysisId,
  getOrchestratorBySessionId,
  getWorkflowStatus,
};
