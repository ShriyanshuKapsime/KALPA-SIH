import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const analyzeOpportunity = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/opportunity-evaluation/analyze', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/opportunity-evaluation/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/opportunity-evaluation/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Opportunity Evaluation Engine (Stage 8)',
      details: error.message,
    });
  }
};

export const getOpportunityEngineHealth = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] GET /api/opportunity-evaluation/health');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/opportunity-evaluation/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/opportunity-evaluation/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve health status from AI Service Opportunity Evaluation Engine',
      details: error.message,
    });
  }
};

export default {
  analyzeOpportunity,
  getOpportunityEngineHealth,
};
