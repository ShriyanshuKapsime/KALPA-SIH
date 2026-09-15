import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const analyzeEntrepreneurProfile = async (req, res, next) => {
  console.log('[GATEWAY STAGE 10] Analyze request:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/entrepreneur-profile/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    console.log('[GATEWAY STAGE 10] Backend analyze response status:', aiResponse.status);
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 10] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/entrepreneur-profile/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Entrepreneur Profile Engine (Stage 10)',
      details: error.message,
    });
  }
};

export const clarifyEntrepreneurProfile = async (req, res, next) => {
  console.log('[GATEWAY STAGE 10] Clarify request:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/entrepreneur-profile/clarify`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 10] Clarify error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/entrepreneur-profile/clarify:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to extract facts via Entrepreneur Profile Clarification Engine',
      details: error.message,
    });
  }
};

export const getEntrepreneurProfileEngineHealth = async (req, res, next) => {
  console.log('[GATEWAY STAGE 10] Health check request');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/entrepreneur-profile/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 10] Health check error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying GET /api/entrepreneur-profile/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve health status from AI Service Entrepreneur Profile Engine',
      details: error.message,
    });
  }
};

export default {
  analyzeEntrepreneurProfile,
  clarifyEntrepreneurProfile,
  getEntrepreneurProfileEngineHealth,
};
