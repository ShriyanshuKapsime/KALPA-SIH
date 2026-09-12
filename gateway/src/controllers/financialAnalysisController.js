import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const analyzeFinancialProfile = async (req, res, next) => {
  console.log('[GATEWAY STAGE 9] Analyze request:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/financial-analysis/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    console.log('[GATEWAY STAGE 9] Backend analyze response status:', aiResponse.status);
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 9] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/financial-analysis/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Financial Engine (Stage 9)',
      details: error.message,
    });
  }
};

export const calculateFinancials = async (req, res, next) => {
  console.log('[GATEWAY STAGE 9] Calculator request:', req.body);
  try {
    const response = await axios.post(
      `${config.aiServiceUrl}/api/v1/financial-analysis/calculator`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    console.log('[GATEWAY STAGE 9] Backend response:', response.data);
    return res.status(response.status).json(response.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 9] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/financial-analysis/calculator:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Financial Calculator',
      details: error.message,
    });
  }
};

export const getFinancialEngineHealth = async (req, res, next) => {
  console.log('[GATEWAY STAGE 9] Health check request');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/financial-analysis/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 9] Health check error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying GET /api/financial-analysis/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve health status from AI Service Financial Engine',
      details: error.message,
    });
  }
};

export default {
  analyzeFinancialProfile,
  calculateFinancials,
  getFinancialEngineHealth,
};
