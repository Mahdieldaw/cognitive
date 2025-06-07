
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import MainLayout from './components/layout/MainLayout';
import DashboardPage from './pages/DashboardPage';
import WorkflowsPage from './pages/WorkflowsPage';
import WorkflowDetailPageRouter from './pages/WorkflowDetailPageRouter';
import TemplatesPage from './pages/TemplatesPage'; // Added for completeness

const App: React.FC = () => {
  return (
    <MainLayout>
      <Routes>
        <Route path="/" element={<Navigate replace to="/dashboard" />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/workflows" element={<WorkflowsPage />} />
        <Route path="/workflows/:workflowId" element={<WorkflowDetailPageRouter />} />
        <Route path="/templates" element={<TemplatesPage />} />
        {/* Add other routes here as needed */}
      </Routes>
    </MainLayout>
  );
};

export default App;
