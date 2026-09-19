import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const analyzeSWOT = async (req, res, next) => {
  console.log('[GATEWAY STAGE 13] Dynamic SWOT analyze request:', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/swot/analyze`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 120000,
      }
    );
    console.log('[GATEWAY STAGE 13] Backend SWOT analyze response status:', aiResponse.status);
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 13] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/swot/analyze:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Stage 13 Dynamic SWOT Agent',
      details: error.message,
    });
  }
};

export const getSWOTById = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 13] Fetching SWOT for id: ${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/swot/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error(`[GATEWAY STAGE 13] Error fetching SWOT for ${id}:`, error.response?.data || error.message);
    logger.error(`Gateway Error proxying GET /api/swot/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to retrieve SWOT record for id '${id}'`,
      details: error.message,
    });
  }
};

export const getSWOTHealth = async (req, res, next) => {
  console.log('[GATEWAY STAGE 13] SWOT health check request');
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/swot/health`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 13] SWOT health check error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying GET /api/swot/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve health status from AI Service SWOT Agent',
      details: error.message,
    });
  }
};

export default {
  analyzeSWOT,
  getSWOTById,
  getSWOTHealth,
};
