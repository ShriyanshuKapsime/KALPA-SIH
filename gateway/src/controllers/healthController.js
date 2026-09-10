import aiService from '../services/aiService.js';

export const healthController = {
  getRoot: (req, res) => {
    res.status(200).json({
      service: 'KALPA API Gateway',
      status: 'running',
    });
  },

  getGatewayHealth: (req, res) => {
    res.status(200).json({
      service: 'KALPA API Gateway',
      status: 'running',
    });
  },

  getAIHealth: async (req, res, next) => {
    try {
      const aiHealth = await aiService.getHealth();
      res.status(200).json({
        service: 'KALPA API Gateway',
        status: 'running',
        downstream: {
          aiService: aiHealth,
        },
      });
    } catch (error) {
      next(error);
    }
  },
};

export default healthController;

