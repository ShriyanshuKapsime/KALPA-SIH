import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const submitTextIntake = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/intake/text', req.body);
  console.log(`[GATEWAY → AI SERVICE] Forwarding to ${config.aiServiceUrl}/api/v1/intake/text`);
  try {
    const response = await axios.post(
      `${config.aiServiceUrl}/api/v1/intake/text`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Error forwarding text intake to AI Service', { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'AI Service communication error' };
    return res.status(status).json(data);
  }
};

export const submitVoiceIntake = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/intake/voice');
  console.log(`[GATEWAY → AI SERVICE] Forwarding audio to ${config.aiServiceUrl}/api/v1/intake/voice`);
  try {
    const response = await axios({
      method: 'POST',
      url: `${config.aiServiceUrl}/api/v1/intake/voice`,
      data: req,
      headers: {
        'content-type': req.headers['content-type'],
      },
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
      timeout: 45000,
    });
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Error forwarding voice intake to AI Service', { 
      status: error.response?.status, 
      message: error.message, 
      data: error.response?.data 
    });
    const status = error.response?.status || 500;
    const data = error.response?.data || { success: false, message: 'Failed to process voice intake', details: error.message };
    return res.status(status).json(data);
  }
};

export const transcribeVoice = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/intake/transcribe');
  console.log(`[GATEWAY → AI SERVICE] Forwarding audio to ${config.aiServiceUrl}/api/v1/intake/transcribe`);
  try {
    const response = await axios({
      method: 'POST',
      url: `${config.aiServiceUrl}/api/v1/intake/transcribe`,
      data: req,
      headers: {
        'content-type': req.headers['content-type'],
      },
      maxBodyLength: Infinity,
      maxContentLength: Infinity,
      timeout: 45000,
    });
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Error forwarding voice transcribe to AI Service', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    });
    const status = error.response?.status || 500;
    const data = error.response?.data || { success: false, message: 'Failed to transcribe voice', details: error.message };
    return res.status(status).json(data);
  }
};

export const continueIntake = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/intake/continue', req.body);
  console.log(`[GATEWAY → AI SERVICE] Forwarding to ${config.aiServiceUrl}/api/v1/intake/continue`);
  try {
    const response = await axios.post(
      `${config.aiServiceUrl}/api/v1/intake/continue`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Error forwarding continue intake to AI Service', { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'AI Service communication error' };
    return res.status(status).json(data);
  }
};

export const getIntakeSession = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/intake/session/${id}`);
  console.log(`[GATEWAY → AI SERVICE] Forwarding to ${config.aiServiceUrl}/api/v1/intake/session/${id}`);
  try {
    const response = await axios.get(
      `${config.aiServiceUrl}/api/v1/intake/session/${id}`,
      { timeout: 15000 }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error(`Error fetching intake session ${req.params.id}`, { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'Session fetch failed' };
    return res.status(status).json(data);
  }
};

export default {
  submitTextIntake,
  submitVoiceIntake,
  transcribeVoice,
  continueIntake,
  getIntakeSession,
};
