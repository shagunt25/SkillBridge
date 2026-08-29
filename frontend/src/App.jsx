import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AppProvider } from './context/AppContext';

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
      <BrowserRouter>
        <Routes>
          <Route path="/"                      element={<LandingPage />} />
          <Route path="/login"                 element={<LoginPage />} />
          <Route path="/signup"                element={<SignupPage />} />
          <Route path="/onboarding/skills"     element={<OnboardingSkillsPage />} />
          <Route path="/onboarding/target"     element={<OnboardingTargetPage />} />
          <Route path="/roadmap/generating"    element={<RoadmapGeneratingPage />} />
          <Route path="/roadmap/review"        element={<RoadmapReviewPage />} />
          <Route path="/dashboard"             element={<DashboardPage />} />
          <Route path="/settings"              element={<SettingsPage />} />
          {/* Catch-all redirect */}
          <Route path="*"                      element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AppProvider>
  );
}

export default App;
