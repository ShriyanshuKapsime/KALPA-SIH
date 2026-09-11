import React from 'react';
import { Routes, Route } from 'react-router-dom';
import Layout from './components/layout/Layout';
import HomePage from './pages/Home/HomePage';
import IntakePage from './pages/Intake/IntakePage';
import ClassificationPage from './pages/Classification/ClassificationPage';
import ProfilePage from './pages/Profile/ProfilePage';
import AnalysisPage from './pages/Analysis/AnalysisPage';
import FeasibilityPage from './pages/Feasibility/FeasibilityPage';
import AssistantPage from './pages/Assistant/AssistantPage';
import DPRPage from './pages/DPR/DPRPage';

function App() {
  return (
    <Routes>
      <Route path="/" element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="intake" element={<IntakePage />} />
        <Route path="classification" element={<ClassificationPage />} />
        <Route path="profile" element={<ProfilePage />} />
        <Route path="analysis" element={<ProfilePage />} />
        <Route path="feasibility" element={<FeasibilityPage />} />
        <Route path="assistant" element={<AssistantPage />} />
        <Route path="dpr" element={<DPRPage />} />
        <Route path="*" element={<HomePage />} />
      </Route>
    </Routes>
  );
}

export default App;
