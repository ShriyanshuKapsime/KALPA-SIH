import { Router } from 'express';
import healthController from '../controllers/healthController.js';

const router = Router();

router.get('/', healthController.getRoot);
router.get('/health', healthController.getGatewayHealth);
router.get('/health/ai', healthController.getAIHealth);

export default router;

