import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const buildProfile = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/profile/build', req.body);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/profile/build`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/profile/build:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service profile builder',
      details: error.message,
    });
  }
};

export const getProfileByAnalysisId = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/profile/${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/profile/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/profile/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve profile from AI Service',
      details: error.message,
    });
  }
};

export const getProfileBySessionId = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/profile/session/${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/profile/session/${id}`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/profile/session/${id}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve session profile from AI Service',
      details: error.message,
    });
  }
};

export default {
  buildProfile,
  getProfileByAnalysisId,
  getProfileBySessionId,
};
