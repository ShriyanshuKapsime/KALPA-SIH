import axios from 'axios';
import config from '../config/index.js';
import logger from '../utils/logger.js';

const forwardGet = async (urlPath, req, res, errorMsg) => {
  try {
    const aiResponse = await axios.get(`${config.aiServiceUrl}/api/v1/knowledge${urlPath}`, {
      params: req.query,
      timeout: 20000,
    });
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error(`Gateway Error GET /api/knowledge${urlPath}:`, error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: errorMsg || 'Failed to communicate with AI Service Knowledge Hub',
      details: error.message,
    });
  }
};

export const getCoverageReport = async (req, res) => {
  return forwardGet('/coverage', req, res, 'Failed to fetch knowledge coverage report');
};

export const getDataSources = async (req, res) => {
  return forwardGet('/sources', req, res, 'Failed to fetch data sources registry');
};

export const getDataSourceById = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/sources/${encodeURIComponent(id)}`, req, res, 'Failed to fetch data source metadata');
};

export const getSchemes = async (req, res) => {
  return forwardGet('/schemes', req, res, 'Failed to fetch government schemes');
};

export const getSchemeById = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/schemes/${encodeURIComponent(id)}`, req, res, 'Failed to fetch scheme details');
};

export const evaluateSchemeEligibility = async (req, res) => {
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/knowledge/schemes/evaluate`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 20000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error POST /api/knowledge/schemes/evaluate:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to evaluate scheme eligibility',
      details: error.message,
    });
  }
};

export const getBusinessProfiles = async (req, res) => {
  return forwardGet('/business-profiles', req, res, 'Failed to fetch business domain profiles');
};

export const getBusinessProfileById = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/business-profiles/${encodeURIComponent(id)}`, req, res, 'Failed to fetch business profile');
};

export const getFinancialBenchmarks = async (req, res) => {
  return forwardGet('/benchmarks/financial', req, res, 'Failed to fetch financial benchmarks');
};

export const getFinancialBenchmarkById = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/benchmarks/financial/${encodeURIComponent(id)}`, req, res, 'Failed to fetch financial benchmark');
};

export const getMarketBenchmarks = async (req, res) => {
  return forwardGet('/benchmarks/market', req, res, 'Failed to fetch market benchmarks');
};

export const getMarketBenchmarkById = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/benchmarks/market/${encodeURIComponent(id)}`, req, res, 'Failed to fetch market benchmark');
};

export const getMarketKnowledgePack = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/market-pack/${encodeURIComponent(id)}`, req, res, 'Failed to fetch market knowledge pack');
};

export const getFinancialKnowledgePack = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/financial-pack/${encodeURIComponent(id)}`, req, res, 'Failed to fetch financial knowledge pack');
};

export const calculateFinancialFeasibility = async (req, res) => {
  try {
    const aiResponse = await axios.post(
      `${config.aiServiceUrl}/api/v1/knowledge/financial-pack/calculate`,
      req.body,
      {
        headers: { 'Content-Type': 'application/json' },
        timeout: 20000,
      }
    );
    return res.status(aiResponse.status).json(aiResponse.data);
  } catch (error) {
    logger.error('Gateway Error POST /api/knowledge/financial-pack/calculate:', error.message);
    if (error.response) {
      return res.status(error.response.status).json(error.response.data);
    }
    return res.status(502).json({
      error: 'Bad Gateway',
      message: 'Failed to calculate deterministic financial feasibility',
      details: error.message,
    });
  }
};

export const getComprehensivePack = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/comprehensive-pack/${encodeURIComponent(id)}`, req, res, 'Failed to fetch comprehensive knowledge pack');
};

export const getBusinessRequirements = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/business/${encodeURIComponent(id)}/requirements`, req, res, 'Failed to fetch business technical requirements');
};

export const getBusinessKnowledgePack = async (req, res) => {
  const { id } = req.params;
  return forwardGet(`/business/${encodeURIComponent(id)}/pack`, req, res, 'Failed to fetch business knowledge pack');
};

export const getRisks = async (req, res) => {
  return forwardGet('/risks', req, res, 'Failed to fetch risk catalog');
};

export const getDocuments = async (req, res) => {
  return forwardGet('/documents', req, res, 'Failed to fetch institutional documents');
};

export const getDynamicRequirements = async (req, res) => {
  return forwardGet('/dynamic-requirements', req, res, 'Failed to fetch dynamic data requirements');
};

export default {
  getCoverageReport,
  getDataSources,
  getDataSourceById,
  getSchemes,
  getSchemeById,
  evaluateSchemeEligibility,
  getBusinessProfiles,
  getBusinessProfileById,
  getFinancialBenchmarks,
  getFinancialBenchmarkById,
  getMarketBenchmarks,
  getMarketBenchmarkById,
  getMarketKnowledgePack,
  getFinancialKnowledgePack,
  calculateFinancialFeasibility,
  getComprehensivePack,
  getBusinessRequirements,
  getBusinessKnowledgePack,
  getRisks,
  getDocuments,
  getDynamicRequirements,
};
