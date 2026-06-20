import { Routes, Route, Navigate } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AppLayout } from './layouts/AppLayout';

// Pages
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import DashboardPage from './pages/DashboardPage';
import NewRepositoryPage from './pages/NewRepositoryPage';
import NotFoundPage from './pages/NotFoundPage';
import RepoLayout from './pages/repo/RepoLayout';
import RepoOverviewPage from './pages/repo/RepoOverviewPage';
import RepoDocsPage from './pages/repo/RepoDocsPage';
import RepoDiagramsPage from './pages/repo/RepoDiagramsPage';
import RepoReportsPage from './pages/repo/RepoReportsPage';
import RepoChatPage from './pages/repo/RepoChatPage';
import RepoReviewPage from './pages/repo/RepoReviewPage';
import RepoExecutiveSummaryPage from './pages/repo/RepoExecutiveSummaryPage';
import RepoArchitecturePage from './pages/repo/RepoArchitecturePage';

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<LandingPage />} />
      <Route path="/login" element={<LoginPage />} />
      
      <Route path="/dashboard" element={
        <ProtectedRoute>
          <AppLayout>
            <DashboardPage />
          </AppLayout>
        </ProtectedRoute>
      } />
      
      <Route path="/repositories" element={<Navigate to="/dashboard" replace />} />
      
      <Route path="/repositories/new" element={
        <ProtectedRoute>
          <AppLayout>
            <NewRepositoryPage />
          </AppLayout>
        </ProtectedRoute>
      } />

      <Route path="/repositories/:id" element={
        <ProtectedRoute>
          <AppLayout>
            <RepoLayout />
          </AppLayout>
        </ProtectedRoute>
      }>
        <Route index element={<RepoOverviewPage />} />
        <Route path="docs" element={<RepoDocsPage />} />
        <Route path="diagrams" element={<RepoDiagramsPage />} />
        <Route path="reports/:type" element={<RepoReportsPage />} />
        <Route path="chat" element={<RepoChatPage />} />
        <Route path="review" element={<RepoReviewPage />} />
        <Route path="executive-summary" element={<RepoExecutiveSummaryPage />} />
        <Route path="architecture" element={<RepoArchitecturePage />} />
      </Route>

      {/* Fallback */}
      <Route path="*" element={<NotFoundPage />} />
    </Routes>
  );
}
