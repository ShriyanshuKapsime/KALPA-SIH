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
    const contentType = req.headers['content-type'] || '';
    let response;

    if (contentType.includes('multipart/form-data')) {
      response = await axios({
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
    } else if (req.body && Object.keys(req.body).length > 0) {
      const params = new URLSearchParams();
      for (const [key, val] of Object.entries(req.body)) {
        params.append(key, typeof val === 'object' ? JSON.stringify(val) : String(val));
      }
      response = await axios.post(
        `${config.aiServiceUrl}/api/v1/intake/voice`,
        params.toString(),
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          timeout: 45000,
        }
      );
    } else {
      response = await axios({
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
    }

    return res.status(200).json(response.data);
  } catch (error) {
    logger.warn('Error forwarding voice intake to AI Service', { 
      status: error.response?.status, 
      message: error.message, 
      data: error.response?.data 
    });
    const respData = error.response?.data;
    let data;
    if (respData && typeof respData === 'object') {
      data = (respData.detail && typeof respData.detail === 'object') ? respData.detail : respData;
    } else {
      data = {
        success: false,
        error: 'STT_PROCESSING_FAILED',
        message: error.message || 'Failed to process voice intake',
        details: error.message
      };
    }
    const errMsg = typeof data.message === 'string' ? data.message : (typeof data.detail === 'string' ? data.detail : 'Could not detect clear speech in the recording. Please speak closer to the microphone or type your answer.');
    return res.status(200).json({
      success: false,
      error: data.error || 'STT_PROCESSING_FAILED',
      message: errMsg,
      details: data.details || null
    });
  }
};

export const transcribeVoice = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/intake/transcribe');
  console.log(`[GATEWAY → AI SERVICE] Forwarding audio to ${config.aiServiceUrl}/api/v1/intake/transcribe`);
  try {
    const contentType = req.headers['content-type'] || '';
    let response;

    if (contentType.includes('multipart/form-data')) {
      response = await axios({
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
    } else if (req.body && Object.keys(req.body).length > 0) {
      const params = new URLSearchParams();
      for (const [key, val] of Object.entries(req.body)) {
        params.append(key, typeof val === 'object' ? JSON.stringify(val) : String(val));
      }
      response = await axios.post(
        `${config.aiServiceUrl}/api/v1/intake/transcribe`,
        params.toString(),
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          timeout: 45000,
        }
      );
    } else {
      response = await axios({
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
    }

    return res.status(200).json(response.data);
  } catch (error) {
    logger.warn('Voice transcribe fallback handled gracefully in Gateway', {
      status: error.response?.status,
      message: error.message,
      data: error.response?.data
    });
    const respData = error.response?.data;
    let data;
    if (respData && typeof respData === 'object') {
      data = (respData.detail && typeof respData.detail === 'object') ? respData.detail : respData;
    } else {
      data = {
        success: false,
        transcript: null,
        provider: 'sarvam',
        model: 'saaras:v4',
        error: {
          code: 'GATEWAY_ERROR',
          message: error.message || 'Failed to transcribe voice'
        }
      };
    }

    const errCode = data?.error?.code || (typeof data?.error === 'string' ? data.error : 'STT_FAILED');
    const errMsg = data?.error?.message || (typeof data?.message === 'string' ? data.message : (typeof data?.detail === 'string' ? data.detail : 'Could not detect clear speech in the recording. Please speak closer to the microphone or type your answer.'));

    // Always return HTTP 200 with success: false so the browser never logs 422 Unprocessable Entity
    return res.status(200).json({
      success: false,
      transcript: null,
      provider: data.provider || 'sarvam',
      model: data.model || 'saaras:v4',
      error: {
        code: errCode,
        message: errMsg
      }
    });
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
