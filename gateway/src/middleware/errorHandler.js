import logger from '../utils/logger.js';

export const errorHandler = (err, req, res, next) => {
  const status = err.status || err.statusCode || 500;
  const message = err.message || 'Internal Server Error';

  logger.error(`Error processing ${req.method} ${req.originalUrl}: ${message}`, {
    stack: process.env.NODE_ENV === 'development' ? err.stack : undefined,
  });

  res.status(status).json({
    status: 'error',
    statusCode: status,
    message,
    timestamp: new Date().toISOString(),
    path: req.originalUrl,
    ...(process.env.NODE_ENV === 'development' && { stack: err.stack }),
  });
};

export default errorHandler;
