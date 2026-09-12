import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const collectMarketEvidence = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/market-intelligence/collect', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/market-intelligence/collect`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/market-intelligence/collect:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Market Intelligence Agent',
      details: error.message,
    });
  }
};

export const getMarketEvidenceById = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/market-intelligence/${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/market-intelligence/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/market-intelligence/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve market evidence profile from AI Service',
      details: error.message,
    });
  }
};

export const getToolHealthReport = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] GET /api/market-intelligence/tools/health');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/market-intelligence/tools/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/market-intelligence/tools/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve tool health report from AI Service',
      details: error.message,
    });
  }
};

export const retryMarketEvidence = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] POST /api/market-intelligence/${id}/retry`, req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/market-intelligence/${id}/retry`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying POST /api/market-intelligence/${id}/retry:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retry market evidence collection',
      details: error.message,
    });
  }
};

export const analyzeMarketIntelligence = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/market-intelligence/analyze', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/market-intelligence/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/market-intelligence/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Market Intelligence Engine (Stage 6)',
      details: error.message,
    });
  }
};

export default {
  collectMarketEvidence,
  getMarketEvidenceById,
  getToolHealthReport,
  retryMarketEvidence,
  analyzeMarketIntelligence,
};

