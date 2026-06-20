import { Navigate, Route, Routes } from 'react-router-dom';

import './App.css';
import RequireAuth from './components/RequireAuth';
import AuthCallbackPage from './pages/AuthCallbackPage';
import LoginPage from './pages/LoginPage';
import PatternsPage from './pages/PatternsPage';
import ProblemListPage from './pages/ProblemListPage';
import ProblemPage from './pages/ProblemPage';
import RoadmapPage from './pages/RoadmapPage';

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<LoginPage />} />
      <Route path="/auth/callback" element={<AuthCallbackPage />} />
      <Route
        path="/"
        element={
          <RequireAuth>
            <ProblemListPage />
          </RequireAuth>
        }
      />
      <Route
        path="/problems/:id"
        element={
          <RequireAuth>
            <ProblemPage />
          </RequireAuth>
        }
      />
      <Route
        path="/roadmap"
        element={
          <RequireAuth>
            <RoadmapPage />
          </RequireAuth>
        }
      />
      <Route
        path="/patterns"
        element={
          <RequireAuth>
            <PatternsPage />
          </RequireAuth>
        }
      />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
