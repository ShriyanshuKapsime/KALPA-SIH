import dotenv from 'dotenv';
import path from 'path';

dotenv.config();

export const config = {
  port: parseInt(process.env.PORT, 10) || 3000,
  nodeEnv: process.env.NODE_ENV || 'development',
  aiServiceUrl: process.env.AI_SERVICE_URL || 'http://localhost:8000',
  corsOrigin: process.env.CORS_ORIGIN || 'http://localhost:5173',
};

export default config;
