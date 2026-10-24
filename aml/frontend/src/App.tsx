import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './context/AuthContext';
import { Layout } from './components/layout/Layout';
import { LoginPage } from './pages/LoginPage';
import { DashboardPage } from './pages/DashboardPage';
import { SimulatorPage } from './pages/SimulatorPage';
import { AlertQueuePage } from './pages/AlertQueuePage';
import { InvestigationWorkspacePage } from './pages/InvestigationWorkspacePage';
import { GraphVisualizerPage } from './pages/GraphVisualizerPage';
import { FundFlowTrackerPage } from './pages/FundFlowTrackerPage';
import { CaseManagementPage } from './pages/CaseManagementPage';
import { STRReportPage } from './pages/STRReportPage';
import { AdminPanelPage } from './pages/AdminPanelPage';

const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { token, loading } = useAuth();
  if (loading) return <div className="p-8 text-center text-slate-500 font-mono text-xs">Authenticating user session...</div>;
  if (!token) return <Navigate to="/login" replace />;
  return <Layout>{children}</Layout>;
};

export const App: React.FC = () => {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/simulator" element={<ProtectedRoute><SimulatorPage /></ProtectedRoute>} />
          <Route path="/alerts" element={<ProtectedRoute><AlertQueuePage /></ProtectedRoute>} />
          <Route path="/investigation" element={<ProtectedRoute><InvestigationWorkspacePage /></ProtectedRoute>} />
          <Route path="/graph" element={<ProtectedRoute><GraphVisualizerPage /></ProtectedRoute>} />
          <Route path="/fund-flow" element={<ProtectedRoute><FundFlowTrackerPage /></ProtectedRoute>} />
          <Route path="/cases" element={<ProtectedRoute><CaseManagementPage /></ProtectedRoute>} />
          <Route path="/str-reports" element={<ProtectedRoute><STRReportPage /></ProtectedRoute>} />
          <Route path="/admin" element={<ProtectedRoute><AdminPanelPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
};

export default App;
