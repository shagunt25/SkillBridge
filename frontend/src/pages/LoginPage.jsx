import { useState } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, CheckCircle2, ArrowRight, Sparkles, Sun, Moon } from 'lucide-react';
import AuthBackgroundMotion from '../components/AuthBackgroundMotion';
import { useAppContext, ACTIONS } from '../context/AppContext';

const FEATURES = [
  'Personalized skill gap analysis',
  'AI-powered learning roadmap',
  'Track your progress, achieve your goals',
];

export default function LoginPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { state, dispatch } = useAppContext();
  const [showPw, setShowPw] = useState(false);
  const [form, setForm] = useState({
    email: location.state?.email || '',
    password: '',
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [successNotice, setSuccessNotice] = useState(
    location.state?.verified
      ? 'Email verified successfully! Please sign in to continue to your selected feature.'
      : ''
  );

  const handleInput = (e) => {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
    if (error) setError('');
    if (successNotice) setSuccessNotice('');
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!form.email.trim() || !form.password.trim()) {
      setError('Please fill in both email and password.');
      return;
    }

    setIsLoading(true);
    // Real auth dispatch
    setTimeout(() => {
      const email = form.email.trim();
      const name = email.split('@')[0];
      dispatch({
        type: ACTIONS.LOGIN,
        payload: {
          user: { email, name: name.charAt(0).toUpperCase() + name.slice(1) },
          token: 'token-' + Date.now(),
        },
      });
      setIsLoading(false);

      const targetFrom = location.state?.from;
      let destination = typeof targetFrom === 'string'
        ? targetFrom
        : targetFrom?.pathname;

      if (!destination) {
        try {
          destination = sessionStorage.getItem('skillbridge_auth_destination');
        } catch {}
      }

      try {
        sessionStorage.removeItem('skillbridge_auth_destination');
      } catch {}

      navigate(destination || '/onboarding/skills', { replace: true });
    }, 300);
  };

  const toggleTheme = () => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    dispatch({ type: ACTIONS.SET_THEME, payload: next });
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-12 bg-background font-sans text-text-primary">
      {/* ── Left Half: Value Proposition & Subtle Wave Pattern ── */}
      <div className="hidden lg:flex lg:col-span-6 flex-col justify-between bg-surface-muted/70 p-12 xl:p-16 border-r border-border relative overflow-hidden">
        {/* Top: Logo & Theme Switch */}
        <div className="flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-800 dark:bg-emerald-500 flex items-center justify-center text-white dark:text-zinc-950 shadow-sm">
              <Sparkles size={16} />
            </div>
            <span className="font-semibold text-lg tracking-tight text-text-primary flex items-center gap-1">
              SkillBridge
              <span className="text-[10px] font-bold bg-surface text-accent border border-border px-1.5 py-0.5 rounded">
                AI
              </span>
            </span>
          </Link>

          <button
            type="button"
            onClick={toggleTheme}
            aria-label="Toggle theme"
            className="p-2 rounded-xl border border-border text-text-secondary hover:text-text-primary hover:bg-surface transition-colors"
          >
            {state.theme === 'dark' ? <Sun size={15} className="text-amber-400" /> : <Moon size={15} className="text-teal-700" />}
          </button>
        </div>

        {/* Middle: Headline & Tagline */}
        <div className="max-w-md my-auto py-8 z-10">
          <h1 className="text-3xl xl:text-4xl font-bold tracking-tight text-text-primary leading-[1.18] mb-4">
            Your next chapter starts with the right skills.
          </h1>
          <p className="text-text-secondary text-sm leading-relaxed mb-8">
            Sign in to continue your learning journey and build the career you want.
          </p>

          <ul className="space-y-3.5">
            {FEATURES.map((item, i) => (
              <li key={i} className="flex items-center gap-3 text-text-primary text-xs sm:text-sm font-medium">
                <CheckCircle2 size={17} className="text-emerald-500 flex-shrink-0" />
                <span>{item}</span>
              </li>
            ))}
          </ul>
        </div>

        {/* Bottom: Subtle Wave graphic & reassurance */}
        <div className="pt-6 border-t border-border flex items-center justify-between text-xs text-text-secondary z-10">
          <span className="font-medium">Better skills. Brighter future.</span>
          <span className="text-[11px] text-text-secondary/70">Private & Secure</span>
        </div>

        {/* Subtle Animated Background Layer */}
        <AuthBackgroundMotion />
      </div>

      {/* ── Right Half: Sign In Form ── */}
      <div className="lg:col-span-6 flex flex-col justify-center px-6 sm:px-12 xl:px-20 py-12 bg-background relative">
        <AuthBackgroundMotion className="lg:hidden opacity-30" />
        <div className="w-full max-w-[420px] mx-auto relative z-10">
          {/* Mobile Logo & Theme */}
          <div className="lg:hidden flex items-center justify-between mb-8">
            <Link to="/" className="flex items-center gap-2">
              <div className="w-8 h-8 rounded-lg bg-teal-800 dark:bg-emerald-500 flex items-center justify-center text-white dark:text-zinc-950">
                <Sparkles size={16} />
              </div>
              <span className="font-semibold text-base text-text-primary">
                SkillBridge AI
              </span>
            </Link>
            <button
              type="button"
              onClick={toggleTheme}
              className="p-2 rounded-xl border border-border text-text-secondary"
            >
              {state.theme === 'dark' ? <Sun size={15} /> : <Moon size={15} />}
            </button>
          </div>

          {/* Form Tabs: Sign in | Sign up */}
          <div className="flex border-b border-border mb-8">
            <button
              type="button"
              className="pb-3 px-4 font-semibold text-sm border-b-2 border-accent text-text-primary"
            >
              Sign in
            </button>
            <Link
              to="/signup"
              state={location.state}
              className="pb-3 px-4 font-medium text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Sign up
            </Link>
          </div>

          {successNotice && (
            <div className="mb-4 p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2">
              <CheckCircle2 size={16} className="flex-shrink-0" />
              <span>{successNotice}</span>
            </div>
          )}

          {error && (
            <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-danger text-xs">
              {error}
            </div>
          )}

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Email address
              </label>
              <input
                type="email"
                name="email"
                value={form.email}
                onChange={handleInput}
                placeholder="you@example.com"
                required
                className="input-field"
              />
            </div>

            <div>
              <div className="flex items-center justify-between mb-1.5">
                <label className="block text-xs font-medium text-text-secondary">
                  Password
                </label>
                <a href="#forgot" className="text-[11px] text-accent hover:underline">
                  Forgot password?
                </a>
              </div>
              <div className="relative">
                <input
                  type={showPw ? 'text' : 'password'}
                  name="password"
                  value={form.password}
                  onChange={handleInput}
                  placeholder="Enter your password"
                  required
                  className="input-field pr-10"
                />
                <button
                  type="button"
                  onClick={() => setShowPw((v) => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-text-secondary hover:text-text-primary"
                  aria-label="Toggle password visibility"
                >
                  {showPw ? <EyeOff size={16} /> : <Eye size={16} />}
                </button>
              </div>
            </div>

            <button
              type="submit"
              disabled={isLoading}
              className="w-full btn-accent py-3 mt-2 flex items-center justify-center gap-2 text-sm font-semibold"
            >
              {isLoading ? (
                <span>Signing in…</span>
              ) : (
                <>
                  <span>Sign in</span>
                  <ArrowRight size={15} />
                </>
              )}
            </button>
          </form>

          <p className="text-center text-xs text-text-secondary mt-8">
            Don't have an account?{' '}
            <Link to="/signup" state={location.state} className="text-accent font-medium hover:underline">
              Create account
            </Link>
          </p>
        </div>
      </div>
    </div>
  );
}
