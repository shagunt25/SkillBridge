import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';
import { LayoutProvider } from './context/LayoutContext';
import ProtectedRoute from './components/ProtectedRoute';

// Pages
import LandingPage            from './pages/LandingPage';
import LoginPage              from './pages/LoginPage';
import SignupPage             from './pages/SignupPage';
import OnboardingSkillsPage   from './pages/OnboardingSkillsPage';
import OnboardingTargetPage   from './pages/OnboardingTargetPage';
import RoadmapGeneratingPage  from './pages/RoadmapGeneratingPage';
import RoadmapReviewPage      from './pages/RoadmapReviewPage';
import DashboardPage          from './pages/DashboardPage';
import SettingsPage           from './pages/SettingsPage';

function App() {
  return (
    <AppProvider>
      <LayoutProvider>
        <BrowserRouter>
        <Routes>
          {/* Public Routes */}
          <Route path="/"                      element={<LandingPage />} />
          <Route path="/login"                 element={<LoginPage />} />
          <Route path="/signup"                element={<SignupPage />} />

          {/* Protected Workflow Routes */}
          <Route
            path="/onboarding/skills"
            element={
              <ProtectedRoute>
                <OnboardingSkillsPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/onboarding/target"
            element={
              <ProtectedRoute>
                <OnboardingTargetPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmap/generating"
            element={
              <ProtectedRoute>
                <RoadmapGeneratingPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/roadmap/review"
            element={
              <ProtectedRoute>
                <RoadmapReviewPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />
          <Route
            path="/settings"
            element={
              <ProtectedRoute>
                <SettingsPage />
              </ProtectedRoute>
            }
          />

          {/* Catch-all redirect */}
          <Route path="*"                      element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
      </LayoutProvider>
    </AppProvider>
  );
}

export default App;
