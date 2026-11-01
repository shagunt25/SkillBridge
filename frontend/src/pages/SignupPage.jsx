import { useState, useEffect } from 'react';
import { Link, useNavigate, useLocation } from 'react-router-dom';
import { Eye, EyeOff, CheckCircle2, ArrowRight, Sparkles, Sun, Moon, Mail, ArrowLeft, RefreshCw } from 'lucide-react';
import AuthBackgroundMotion from '../components/AuthBackgroundMotion';
import { useAppContext, ACTIONS } from '../context/AppContext';

const FEATURES = [
  'Personalized skill gap analysis',
  'AI-powered learning roadmap',
  'Track your progress, achieve your goals',
];

export default function SignupPage() {
  const navigate = useNavigate();
  const location = useLocation();
  const { state, dispatch } = useAppContext();
  const [showPw, setShowPw] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '' });
  const [otp, setOtp] = useState('');
  const [step, setStep] = useState('signup'); // 'signup' | 'otp'
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [resendCooldown, setResendCooldown] = useState(0);
  const [otpNotice, setOtpNotice] = useState('');

  // Extract destination from location state or session storage
  const targetDestination = (() => {
    const from = location.state?.from;
    if (typeof from === 'string') return from;
    if (from?.pathname) return from.pathname;
    try {
      return sessionStorage.getItem('skillbridge_auth_destination');
    } catch {}
    return null;
  })();

  // Keep target destination persisted in sessionStorage
  useEffect(() => {
    if (targetDestination) {
      try {
        sessionStorage.setItem('skillbridge_auth_destination', targetDestination);
      } catch {}
    }
  }, [targetDestination]);

  // Handle resend countdown timer
  useEffect(() => {
    if (resendCooldown <= 0) return;
    const timer = setInterval(() => {
      setResendCooldown((prev) => (prev > 0 ? prev - 1 : 0));
    }, 1000);
    return () => clearInterval(timer);
  }, [resendCooldown]);

  const handleInput = (e) => {
    setForm((p) => ({ ...p, [e.target.name]: e.target.value }));
    if (error) setError('');
  };

  const handleSignupSubmit = (e) => {
    e.preventDefault();
    const name = form.name.trim();
    const email = form.email.trim();
    const password = form.password.trim();

    if (!name || !email || !password) {
      setError('Please fill in all fields.');
      return;
    }

    if (password.length < 8) {
      setError('Password must be at least 8 characters long.');
      return;
    }

    setIsLoading(true);
    setError('');

    // Trigger account registration and advance to email OTP verification
    // Note: Signup does not authenticate the user; email verification and login must follow.
    setTimeout(() => {
      setIsLoading(false);
      setStep('otp');
      setResendCooldown(60);
      setOtpNotice(`We have sent a 6-digit verification code to ${email}`);
    }, 300);
  };

  const handleVerifyOtp = (e) => {
    e.preventDefault();
    const cleanOtp = otp.trim();

    if (!cleanOtp) {
      setError('Please enter the 6-digit verification code.');
      return;
    }

    if (cleanOtp.length !== 6) {
      setError('The verification code must be 6 digits.');
      return;
    }

    setIsLoading(true);
    setError('');

    // Account verification step — once verified, user is directed to Sign In
    setTimeout(() => {
      setIsLoading(false);
      navigate('/login', {
        state: {
          from: targetDestination || location.state?.from,
          email: form.email.trim(),
          verified: true,
        },
        replace: true,
      });
    }, 300);
  };

  const handleResendOtp = () => {
    if (resendCooldown > 0) return;
    setResendCooldown(60);
    setError('');
    setOtpNotice(`A new 6-digit verification code was sent to ${form.email.trim()}`);
  };

  const toggleTheme = () => {
    const next = state.theme === 'dark' ? 'light' : 'dark';
    dispatch({ type: ACTIONS.SET_THEME, payload: next });
  };

  return (
    <div className="min-h-screen grid lg:grid-cols-12 bg-background font-sans text-text-primary">
      {/* ── Left Half: Value Proposition ── */}
      <div className="hidden lg:flex lg:col-span-6 flex-col justify-between bg-surface-muted/70 p-12 xl:p-16 border-r border-border relative overflow-hidden">
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

        <div className="max-w-md my-auto py-8 z-10">
          <h1 className="text-3xl xl:text-4xl font-bold tracking-tight text-text-primary leading-[1.18] mb-4">
            Your next chapter starts with the right skills.
          </h1>
          <p className="text-text-secondary text-sm leading-relaxed mb-8">
            Create an account to begin your personalized career roadmap and skill gap analysis.
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

        <div className="pt-6 border-t border-border flex items-center justify-between text-xs text-text-secondary z-10">
          <span className="font-medium">Better skills. Brighter future.</span>
          <span className="text-[11px] text-text-secondary/70">Private & Secure</span>
        </div>

        {/* Subtle Animated Background Layer */}
        <AuthBackgroundMotion />
      </div>

      {/* ── Right Half: Sign Up / OTP Form ── */}
      <div className="lg:col-span-6 flex flex-col justify-center px-6 sm:px-12 xl:px-20 py-12 bg-background relative">
        <AuthBackgroundMotion className="lg:hidden opacity-30" />
        <div className="w-full max-w-[420px] mx-auto relative z-10">
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

          <div className="flex border-b border-border mb-8">
            <Link
              to="/login"
              state={location.state}
              className="pb-3 px-4 font-medium text-sm text-text-secondary hover:text-text-primary transition-colors"
            >
              Sign in
            </Link>
            <button
              type="button"
              className="pb-3 px-4 font-semibold text-sm border-b-2 border-accent text-text-primary"
            >
              {step === 'otp' ? 'Verify email' : 'Sign up'}
            </button>
          </div>

          {step === 'otp' ? (
            /* ── Step 2: Email OTP Verification Form ── */
            <div>
              <div className="mb-6">
                <div className="w-10 h-10 rounded-xl bg-accent/10 text-accent flex items-center justify-center mb-3">
                  <Mail size={20} />
                </div>
                <h2 className="text-xl font-bold text-text-primary tracking-tight">
                  Verify your email
                </h2>
                <p className="text-xs text-text-secondary mt-1.5 leading-relaxed">
                  We've sent a 6-digit verification code to{' '}
                  <span className="font-semibold text-text-primary">{form.email}</span>. Enter the code below to complete registration.
                </p>
              </div>

              {otpNotice && (
                <div className="mb-4 p-3 rounded-xl bg-accent/10 border border-accent/20 text-accent text-xs">
                  {otpNotice}
                </div>
              )}

              {error && (
                <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-danger text-xs">
                  {error}
                </div>
              )}

              <form onSubmit={handleVerifyOtp} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">
                    Verification code
                  </label>
                  <input
                    type="text"
                    maxLength={6}
                    value={otp}
                    onChange={(e) => {
                      setOtp(e.target.value.replace(/\D/g, ''));
                      if (error) setError('');
                    }}
                    placeholder="123456"
                    required
                    autoFocus
                    className="input-field text-center text-lg tracking-[0.35em] font-mono"
                  />
                </div>

                <button
                  type="submit"
                  disabled={isLoading}
                  className="w-full btn-accent py-3 mt-2 flex items-center justify-center gap-2 text-sm font-semibold"
                >
                  {isLoading ? (
                    <span>Verifying…</span>
                  ) : (
                    <>
                      <span>Verify & Continue</span>
                      <ArrowRight size={15} />
                    </>
                  )}
                </button>
              </form>

              <div className="mt-6 pt-4 border-t border-border flex items-center justify-between text-xs">
                <button
                  type="button"
                  onClick={() => {
                    setStep('signup');
                    setError('');
                  }}
                  className="inline-flex items-center gap-1.5 text-text-secondary hover:text-text-primary transition-colors"
                >
                  <ArrowLeft size={13} />
                  <span>Change email</span>
                </button>

                <button
                  type="button"
                  onClick={handleResendOtp}
                  disabled={resendCooldown > 0}
                  className={`inline-flex items-center gap-1.5 font-medium transition-colors ${
                    resendCooldown > 0
                      ? 'text-text-secondary/50 cursor-not-allowed'
                      : 'text-accent hover:underline'
                  }`}
                >
                  <RefreshCw size={12} className={resendCooldown > 0 ? '' : 'animate-spin-slow'} />
                  <span>
                    {resendCooldown > 0 ? `Resend in ${resendCooldown}s` : 'Resend code'}
                  </span>
                </button>
              </div>
            </div>
          ) : (
            /* ── Step 1: Initial Registration Form ── */
            <div>
              {error && (
                <div className="mb-4 p-3 rounded-xl bg-rose-500/10 border border-rose-500/20 text-danger text-xs">
                  {error}
                </div>
              )}

              <form onSubmit={handleSignupSubmit} className="space-y-4">
                <div>
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">
                    Full name
                  </label>
                  <input
                    type="text"
                    name="name"
                    value={form.name}
                    onChange={handleInput}
                    placeholder="Alex Sharma"
                    required
                    className="input-field"
                  />
                </div>

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
                  <label className="block text-xs font-medium text-text-secondary mb-1.5">
                    Password
                  </label>
                  <div className="relative">
                    <input
                      type={showPw ? 'text' : 'password'}
                      name="password"
                      value={form.password}
                      onChange={handleInput}
                      placeholder="At least 8 characters"
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
                    <span>Creating account…</span>
                  ) : (
                    <>
                      <span>Create account</span>
                      <ArrowRight size={15} />
                    </>
                  )}
                </button>
              </form>

              <p className="text-center text-xs text-text-secondary mt-8">
                Already have an account?{' '}
                <Link to="/login" state={location.state} className="text-accent font-medium hover:underline">
                  Sign in
                </Link>
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
