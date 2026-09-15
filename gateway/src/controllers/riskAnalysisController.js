import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const analyzeRiskProfile = async (req, res, next) => {
  console.log('[GATEWAY STAGE 11] Risk analyze request:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/risk-analysis/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    console.log('[GATEWAY STAGE 11] Backend risk analyze response status:', aiResponse.status);
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 11] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/risk-analysis/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Risk Engine (Stage 11)',
      details: error.message,
    });
  }
};

export const getRiskEngineHealth = async (req, res, next) => {
  console.log('[GATEWAY STAGE 11] Health check request');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/risk-analysis/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 11] Health check error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying GET /api/risk-analysis/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve health status from AI Service Risk Engine',
      details: error.message,
    });
  }
};

export default {
  analyzeRiskProfile,
  getRiskEngineHealth,
};
