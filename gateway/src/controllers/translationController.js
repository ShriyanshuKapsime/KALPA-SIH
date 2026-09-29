import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const translateText = async (req, res) => {
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/translate/text`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 15000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/translate/text:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Translation Engine',
      translated_text: req.body?.text || '',
    });
  }
};

export const translateBatch = async (req, res) => {
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/translate/batch`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/translate/batch:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Translation Engine (Batch)',
      translated_texts: req.body?.texts || [],
    });
  }
};

export const translateObject = async (req, res) => {
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/translate/object`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/translate/object:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Translation Engine (Object)',
      data: req.body?.data || null,
    });
  }
};

export default {
  translateText,
  translateBatch,
  translateObject,
};
