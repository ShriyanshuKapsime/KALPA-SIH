import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import config from './config/index.js';
import requestLogger from './middleware/requestLogger.js';
import errorHandler from './middleware/errorHandler.js';
import healthRoutes from './routes/healthRoutes.js';
import apiRoutes from './routes/apiRoutes.js';

export const createApp = () => {
  const app = express();

  // Security Middleware
  app.use(helmet());

  // CORS Configuration
  app.use(
    cors({
      origin: '*', // Allow all during development or configurable via CORS_ORIGIN
      methods: ['GET', 'POST', 'PUT', 'DELETE', 'PATCH', 'OPTIONS'],
      allowedHeaders: ['Content-Type', 'Authorization', 'X-Requested-With'],
    })
  );

  // Body Parsing
  app.use(express.json({ limit: '10mb' }));
  app.use(express.urlencoded({ extended: true, limit: '10mb' }));

  // Logging Middleware
  app.use(requestLogger);

  // Root & Health Endpoints
  app.use('/', healthRoutes);

  // API Versioned Routing
  app.use('/api', apiRoutes);

  // 404 Handler
  app.use((req, res, next) => {
    res.status(404).json({
      status: 'error',
      statusCode: 404,
      message: `Endpoint ${req.method} ${req.originalUrl} not found`,
    });
  });

  // Centralized Error Handling
  app.use(errorHandler);

  return app;
};

export default createApp;
