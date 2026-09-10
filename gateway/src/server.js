import createApp from './app.js';
import config from './config/index.js';
import logger from './utils/logger.js';

const app = createApp();

const server = app.listen(config.port, () => {
  logger.info(`KALPA API Gateway running on port ${config.port} in ${config.nodeEnv} mode`);
  logger.info(`Health check available at http://localhost:${config.port}/health`);
});

// Graceful shutdown handling
const shutdown = (signal) => {
  logger.info(`${signal} signal received: closing HTTP server`);
  server.close(() => {
    logger.info('HTTP server closed');
    process.exit(0);
  });
};

process.on('SIGTERM', () => shutdown('SIGTERM'));
process.on('SIGINT', () => shutdown('SIGINT'));
