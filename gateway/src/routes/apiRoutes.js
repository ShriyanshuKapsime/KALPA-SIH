import { Router } from 'express';
import healthController from '../controllers/healthController.js';
import intakeController from '../controllers/intakeController.js';

const router = Router();

// Subsystem health proxy
router.get('/health/ai', healthController.getAIHealth);

// Stage 1 Live Intake Routes
router.post('/intake/text', intakeController.submitTextIntake);
router.post('/intake/voice', intakeController.submitVoiceIntake);
router.post('/intake/continue', intakeController.continueIntake);
router.get('/intake/session/:id', intakeController.getIntakeSession);

router.all('/classification/*', (req, res) => {
  res.status(501).json({
    status: 'scaffold_only',
    message: 'Classification API endpoint will be activated during Phase 1 development.',
  });
});

router.all('/market/*', (req, res) => {
  res.status(501).json({
    status: 'scaffold_only',
    message: 'Market Intelligence API endpoint will be activated in future phases.',
  });
});

router.all('/feasibility/*', (req, res) => {
  res.status(501).json({
    status: 'scaffold_only',
    message: 'Feasibility API endpoint will be activated in future phases.',
  });
});

router.all('/dpr/*', (req, res) => {
  res.status(501).json({
    status: 'scaffold_only',
    message: 'DPR API endpoint will be activated in future phases.',
  });
});

export default router;
