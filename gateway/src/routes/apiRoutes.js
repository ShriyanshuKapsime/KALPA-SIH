import { Router } from 'express';
import healthController from '../controllers/healthController.js';
import intakeController from '../controllers/intakeController.js';
import classificationController from '../controllers/classificationController.js';
import profileController from '../controllers/profileController.js';

const router = Router();

// Subsystem health proxy
router.get('/health/ai', healthController.getAIHealth);

// Stage 1 Live Intake Routes
router.post('/intake/text', intakeController.submitTextIntake);
router.post('/intake/voice', intakeController.submitVoiceIntake);
router.post('/intake/continue', intakeController.continueIntake);
router.get('/intake/session/:id', intakeController.getIntakeSession);

// Stage 2 Live Classification Routes
router.post('/classification/classify', classificationController.classifyBusiness);
router.post('/classification/clarify', classificationController.clarifyClassification);
router.get('/classification/nic/:code', classificationController.getNICDetails);
router.get('/classification/:id', classificationController.getClassificationSession);

// Stage 3 Live Profile Store Routes
router.post('/profile/build', profileController.buildProfile);
router.get('/profile/session/:id', profileController.getProfileBySessionId);
router.get('/profile/:id', profileController.getProfileByAnalysisId);

// Locked Future Stages
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
