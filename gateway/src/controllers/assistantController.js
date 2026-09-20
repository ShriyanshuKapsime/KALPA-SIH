import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const getAssistantHealth = async (req, res, next) => {
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/assistant/health`,
      { timeout: 5000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/v1/assistant/health:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      status: 'error',
      service: 'stage15-assistant',
      message: 'Failed to communicate with AI Service Personal Assistant',
      details: error.message,
    });
  }
};

export const chatWithAssistant = async (req, res, next) => {
  console.log('[GATEWAY STAGE 15] Assistant chat request:', req.body?.message?.substring(0, 60));
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/assistant/chat`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 95000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    console.error('[GATEWAY STAGE 15] Error:', error.response?.data || error.message);
    logger.error('Gateway Error proxying POST /api/v1/assistant/chat:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service Personal Assistant',
      details: error.message,
    });
  }
};

export const getAssistantHistory = async (req, res, next) => {
  const id = req.params.id || req.params.analysis_id || req.params.target_id;
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/assistant/${id}/history`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/v1/assistant/${id}/history:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to retrieve assistant history for '${id}'`,
      details: error.message,
    });
  }
};

export const getAssistantContext = async (req, res, next) => {
  const id = req.params.id || req.params.analysis_id || req.params.target_id;
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/assistant/${id}/context`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying GET /api/v1/assistant/${id}/context:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to retrieve assistant context for '${id}'`,
      details: error.message,
    });
  }
};

export const transcribeAssistantAudio = async (req, res, next) => {
  console.log('[GATEWAY STAGE 15] Transcribing audio with Sarvam Saaras v4...');
  try {
    const response = await axios({
      method: 'POST',
      url: `${config.aiServiceUrl}/api/v1/assistant/stt`,
      data: req,
      headers: {
        'content-type': req.headers['content-type'],
      },
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
      timeout: 45000,
    });
    return res.status(response.status).json(response.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/v1/assistant/stt:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      success: false,
      message: "Voice input couldn't be understood. Please try again or type your question.",
      details: error.message,
    });
  }
};

export const synthesizeAssistantSpeech = async (req, res, next) => {
  console.log('[GATEWAY STAGE 15] Synthesizing speech with Sarvam Bulbul v3...', req.body?.text?.substring(0, 40));
  try {
    const response = await axios.post(
      `${config.aiServiceUrl}/api/v1/assistant/tts`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 45000,
      }
    );
    return res.status(response.status).json(response.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/v1/assistant/tts:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      success: false,
      message: "Voice playback isn't available right now. You can still read the answer.",
      details: error.message,
    });
  }
};

export const clearAssistantHistory = async (req, res, next) => {
  const id = req.params.id || req.params.analysis_id || req.params.target_id;
  try {
    const aiResponse = await axios.delete(
      `${config.aiServiceUrl}/api/v1/assistant/${id}/history`,
      { timeout: 15000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error proxying DELETE /api/v1/assistant/${id}/history:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: `Failed to clear assistant history for '${id}'`,
      details: error.message,
    });
  }
};

export default {
  getAssistantHealth,
  chatWithAssistant,
  transcribeAssistantAudio,
  synthesizeAssistantSpeech,
  getAssistantHistory,
  getAssistantContext,
  clearAssistantHistory,
};
