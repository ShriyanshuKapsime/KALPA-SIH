import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const aiClient = axios.create({
  baseURL: config.aiServiceUrl,
  timeout: 10000,
  headers: {
    'Content-Type': 'application/json',
  },
});

export const aiService = {
  getHealth: async () => {
    try {
      const response = await aiClient.get('/health');
      return response.data;
    } catch (error) {
      logger.error('Failed to connect to AI Backend service', { error: error.message });
      throw {
        status: 503,
        message: 'AI Backend Service is currently unreachable',
        details: error.message,
      };
    }
  },

  // Forwarding stubs for future phases
  forwardRequest: async (method, path, data = null, headers = {}) => {
    try {
      const response = await aiClient({
        method,
        url: path,
        data,
        headers,
      });
      return response.data;
    } catch (error) {
      const status = error.response?.status || 500;
      const message = error.response?.data?.message || error.message || 'AI Service Error';
      throw { status, message, details: error.response?.data };
    }
  },
};

export default aiService;
