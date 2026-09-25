import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

export const generateDpr = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Generate DPR request for business_id=${id}`);
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/dpr/generate/${id}`,
      req.body || {},
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 60000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying POST /api/dpr/generate:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to communicate with AI Service DPR Generator',
      details: error.message,
    });
  }
};

export const getDprReport = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Fetch DPR report for report_id=${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/dpr/report/${id}`,
      { timeout: 30000 }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/dpr/report:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to retrieve DPR report',
      details: error.message,
    });
  }
};

export const downloadDprPdf = async (req, res, next) => {
  const { id } = req.params;
  console.log(`[GATEWAY STAGE 14] Download DPR PDF for report_id=${id}`);
  try {
    const aiResponse = await axios.get(
      `${config.aiServiceUrl}/api/v1/dpr/report/${id}/pdf`,
      { responseType: 'stream', timeout: 45000 }
    );
    res.setHeader('Content-Type', 'application/pdf');
    res.setHeader('Content-Disposition', `attachment; filename="Bankable_DPR_${id}.pdf"`);
    aiResponse.data.pipe(res);
  } catch (error) {
    logger.error('Gateway Error proxying GET /api/dpr/report/pdf:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to download DPR PDF',
      details: error.message,
    });
  }
};

export default {
  generateDpr,
  getDprReport,
  downloadDprPdf,
};
