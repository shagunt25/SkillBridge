import { useNavigate } from 'react-router-dom';
import { Sun, Moon, LogOut, RotateCcw, User, Shield } from 'lucide-react';
import WorkflowLayout from '../components/WorkflowLayout';
import { useAppContext, ACTIONS } from '../context/AppContext';

export default function SettingsPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();

  const user = state.user || {
    name: 'SkillBridge Learner',
    email: 'learner@skillbridge.ai',
  };

  const handleThemeChange = (newTheme) => {
    dispatch({ type: ACTIONS.SET_THEME, payload: newTheme });
  };

  const handleReset = () => {
    if (window.confirm('Reset all roadmap data and start over?')) {
      dispatch({ type: ACTIONS.RESET });
      navigate('/onboarding/skills');
    }
  };

  const handleLogout = () => {
    dispatch({ type: ACTIONS.LOGOUT });
    navigate('/login', { replace: true });
  };

  return (
    <WorkflowLayout currentStep={null} pageTitle="Settings">
      <div className="max-w-2xl mx-auto space-y-6">
        <div>
          <h1 className="text-2xl font-bold text-text-primary tracking-tight">Settings</h1>
          <p className="text-text-secondary text-xs sm:text-sm mt-0.5">
            Manage your profile, theme appearance, and learning preferences.
          </p>
        </div>

        {/* ── Theme Switcher Card ── */}
        <div className="card-surface p-6 space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Interface Theme</h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Select between Light and Dark mode. Your selection is automatically saved.
            </p>
          </div>

          <div className="grid grid-cols-2 gap-3 pt-1">
            <button
              type="button"
              onClick={() => handleThemeChange('light')}
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                state.theme === 'light'
                  ? 'bg-surface-muted border-accent text-accent font-semibold shadow-sm'
                  : 'bg-surface border-border text-text-secondary hover:border-border-subtle'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-amber-500/10 text-amber-500 flex items-center justify-center">
                  <Sun size={18} />
                </div>
                <div className="text-left">
                  <p className="text-xs font-semibold text-text-primary">Light Mode</p>
                  <p className="text-[11px] text-text-secondary">Clean & crisp</p>
                </div>
              </div>
              {state.theme === 'light' && (
                <span className="w-2 h-2 rounded-full bg-accent" />
              )}
            </button>

            <button
              type="button"
              onClick={() => handleThemeChange('dark')}
              className={`p-4 rounded-xl border flex items-center justify-between transition-all ${
                state.theme === 'dark'
                  ? 'bg-surface-muted border-accent text-accent font-semibold shadow-sm'
                  : 'bg-surface border-border text-text-secondary hover:border-border-subtle'
              }`}
            >
              <div className="flex items-center gap-3">
                <div className="w-8 h-8 rounded-lg bg-teal-500/10 text-teal-400 flex items-center justify-center">
                  <Moon size={18} />
                </div>
                <div className="text-left">
                  <p className="text-xs font-semibold text-text-primary">Dark Mode</p>
                  <p className="text-[11px] text-text-secondary">Forest & deep teal</p>
                </div>
              </div>
              {state.theme === 'dark' && (
                <span className="w-2 h-2 rounded-full bg-accent" />
              )}
            </button>
          </div>
        </div>

        {/* ── Profile Card ── */}
        <div className="card-surface p-6 space-y-4">
          <h2 className="text-sm font-semibold text-text-primary">Account Details</h2>

          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-full bg-accent/15 text-accent font-bold text-base flex items-center justify-center border border-border">
              {(user.name || 'A').charAt(0).toUpperCase()}
            </div>
            <div>
              <p className="font-semibold text-text-primary text-sm">{user.name}</p>
              <p className="text-xs text-text-secondary">{user.email}</p>
            </div>
          </div>

          <div className="pt-2 border-t border-border grid sm:grid-cols-2 gap-4 text-xs">
            <div>
              <span className="text-text-secondary block">Target Career Role</span>
              <span className="text-text-primary font-medium">
                {state.targetValue || 'Backend AI/ML Engineer'}
              </span>
            </div>
            <div>
              <span className="text-text-secondary block">Active Skills Recorded</span>
              <span className="text-text-primary font-medium">
                {state.currentSkills?.length ? `${state.currentSkills.length} skills listed` : 'Skills configured'}
              </span>
            </div>
          </div>
        </div>

        {/* ── Data & Reset ── */}
        <div className="card-surface p-6 space-y-4">
          <div>
            <h2 className="text-sm font-semibold text-text-primary">Session & Data Management</h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Reset your roadmap progress or sign out of your current session.
            </p>
          </div>

          <div className="flex flex-wrap gap-3 pt-1">
            <button
              type="button"
              onClick={handleReset}
              className="px-4 py-2 rounded-xl bg-surface border border-border text-danger hover:bg-rose-500/10 text-xs font-medium transition-colors flex items-center gap-2"
            >
              <RotateCcw size={13} />
              <span>Reset Roadmap Data</span>
            </button>

            <button
              type="button"
              onClick={handleLogout}
              className="px-4 py-2 rounded-xl bg-rose-500/10 border border-rose-500/20 text-danger hover:bg-rose-500/20 text-xs font-semibold transition-colors flex items-center gap-2"
            >
              <LogOut size={13} />
              <span>Log out</span>
            </button>
          </div>
        </div>
      </div>
    </WorkflowLayout>
  );
}
