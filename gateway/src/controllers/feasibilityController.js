import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const analyzeFeasibility = async (req, res, next) => {
  console.log('[GATEWAY STAGE 12] Feasibility analyze request:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/feasibility/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    console.log('[GATEWAY STAGE 12] Backend feasibility analyze response status:', aiResponse.status);
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 12] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/feasibility/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Feasibility Engine (Stage 12)',
      details: error.message,
    });
  }
};

export const getFeasibilityById = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 12] Fetching feasibility for id: ${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/feasibility/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error(`[GATEWAY STAGE 12] Error fetching feasibility for ${id}:`, error.response?.data || error.message);
    logger.error(`Gateway Error proxying GET /api/feasibility/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to retrieve feasibility record for id '${id}'`,
      details: error.message,
    });
  }
};

export const getFeasibilityCalculation = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 12] Fetching calculation trail for id: ${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/feasibility/${id}/calculation`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error(`[GATEWAY STAGE 12] Error fetching calculation trail for ${id}:`, error.response?.data || error.message);
    logger.error(`Gateway Error proxying GET /api/feasibility/${id}/calculation:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to retrieve calculation trail for id '${id}'`,
      details: error.message,
    });
  }
};

export const getPivotSuggestions = async (req, res, next) => {
  console.log('[GATEWAY STAGE 12] Fetching pivot suggestions:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/feasibility/pivot-suggestions`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 15000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 12] Error fetching pivot suggestions:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/feasibility/pivot-suggestions:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve pivot suggestions from AI Service Feasibility Engine',
      details: error.message,
    });
  }
};

export const getFeasibilityHealth = async (req, res, next) => {
  console.log('[GATEWAY STAGE 12] Feasibility health check request');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/feasibility/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 12] Feasibility health check error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying GET /api/feasibility/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve health status from AI Service Feasibility Engine',
      details: error.message,
    });
  }
};

export default {
  analyzeFeasibility,
  getFeasibilityById,
  getFeasibilityCalculation,
  getPivotSuggestions,
  getFeasibilityHealth,
};
