import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/Home/HomePage';
import JourneyPage from './pages/Journey/JourneyPage';
import IntakePage from './pages/Intake/IntakePage';
import ClassificationPage from './pages/Classification/ClassificationPage';
import ProfilePage from './pages/Profile/ProfilePage';
import OrchestratorPage from './pages/Orchestrator/OrchestratorPage';
import AnalysisPage from './pages/Analysis/AnalysisPage';
import FeasibilityPage from './pages/Feasibility/FeasibilityPage';
import SWOTPage from './pages/SWOT/SWOTPage';
import AssistantPage from './pages/Assistant/AssistantPage';
import DPRPage from './pages/DPR/DPRPage';
import DPREnrichmentPage from './pages/DPR/DPREnrichmentPage';
import DPRDraftingPage from './pages/DPR/DPRDraftingPage';
import GrowthManagerPage from './pages/GrowthManager/GrowthManagerPage';
import KnowledgeHubPage from './pages/Knowledge/KnowledgeHubPage';
import MarketIntelligencePage from './pages/MarketIntelligence/MarketIntelligencePage';
import OpportunityEvaluationPage from './pages/OpportunityEvaluation/OpportunityEvaluationPage';
import FinancialAnalysisPage from './pages/FinancialAnalysis/FinancialAnalysisPage';
import { WorkflowProvider } from './context/WorkflowContext';
import { LanguageProvider } from './context/LanguageContext';

function App() {
  return (
    <LanguageProvider>
      <WorkflowProvider>
      <Routes>
        <Route path="/" element={<Layout />}>
          <Route index element={<HomePage />} />
          <Route path="journey" element={<JourneyPage />} />
          <Route path="intake" element={<IntakePage />} />
          <Route path="classification" element={<ClassificationPage />} />
          <Route path="profile" element={<ProfilePage />} />
          <Route path="orchestrator" element={<JourneyPage />} />
          <Route path="knowledge" element={<KnowledgeHubPage />} />
          <Route path="market-intelligence" element={<MarketIntelligencePage />} />
          <Route path="opportunity-evaluation" element={<OpportunityEvaluationPage />} />
          <Route path="financial-planning" element={<FinancialAnalysisPage />} />
          <Route path="financial-analysis" element={<FinancialAnalysisPage />} />
          <Route path="finance" element={<Navigate to="/financial-planning" replace />} />
          <Route path="analysis" element={<MarketIntelligencePage />} />
          <Route path="feasibility" element={<FeasibilityPage />} />
          <Route path="swot" element={<SWOTPage />} />
          <Route path="assistant" element={<AssistantPage />} />
          <Route path="growth-manager" element={<GrowthManagerPage />} />
          <Route path="grow" element={<Navigate to="/growth-manager" replace />} />
          <Route path="dpr" element={<DPRPage />} />
          <Route path="dpr/enrichment" element={<DPREnrichmentPage />} />
          <Route path="dpr/drafting" element={<DPRDraftingPage />} />
          <Route path="dpr/preview" element={<DPRDraftingPage />} />
          <Route path="*" element={<HomePage />} />
        </Route>
      </Routes>
      </WorkflowProvider>
    </LanguageProvider>
  );
}

export default App;
