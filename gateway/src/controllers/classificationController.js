import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const classifyBusiness = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/classification/classify', req.body);
  console.log(`[GATEWAY → AI SERVICE] Forwarding to ${config.aiServiceUrl}/api/v1/classification/classify`);
  try {
    const response = await axios.post(
      `${config.aiServiceUrl}/api/v1/classification/classify`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Error forwarding classification to AI Service', { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'Classification AI Service communication error' };
    return res.status(status).json(data);
  }
};

export const clarifyClassification = async (req, res, next) => {
  console.log('[GATEWAY ROUTE HIT] POST /api/classification/clarify', req.body);
  console.log(`[GATEWAY → AI SERVICE] Forwarding to ${config.aiServiceUrl}/api/v1/classification/clarify`);
  try {
    const response = await axios.post(
      `${config.aiServiceUrl}/api/v1/classification/clarify`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 30000,
      }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error('Error forwarding clarify classification to AI Service', { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'Clarification AI Service communication error' };
    return res.status(status).json(data);
  }
};

export const getClassificationSession = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/classification/${id}`);
  console.log(`[GATEWAY → AI SERVICE] Forwarding to ${config.aiServiceUrl}/api/v1/classification/${id}`);
  try {
    const response = await axios.get(
      `${config.aiServiceUrl}/api/v1/classification/${id}`,
      { timeout: 15000 }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error(`Error fetching classification session ${id}`, { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'Classification session fetch failed' };
    return res.status(status).json(data);
  }
};

export const getNICDetails = async (req, res, next) => {
  const { code } = req.params;
  console.log(`[GATEWAY ROUTE HIT] GET /api/classification/nic/${code}`);
  try {
    const response = await axios.get(
      `${config.aiServiceUrl}/api/v1/classification/nic/${code}`,
      { timeout: 15000 }
    );
    return res.status(200).json(response.data);
  } catch (error) {
    logger.error(`Error fetching NIC details for ${code}`, { error: error.message });
    const status = error.response?.status || 500;
    const data = error.response?.data || { message: 'NIC fetch failed' };
    return res.status(status).json(data);
  }
};

export default {
  classifyBusiness,
  clarifyClassification,
  getClassificationSession,
  getNICDetails,
};
