import { useState } from 'react';
import { Link } from 'react-router-dom';
import {
  ArrowRight,
  Sparkles,
  CheckCircle2,
  Sliders,
  LayoutGrid,
  Sun,
  Moon,
  Shield,
  User,
  BarChart3,
  TrendingUp,
  Cpu,
  Search,
  Star,
  BookOpen,
} from 'lucide-react';
import LandingBackgroundMotion from '../components/LandingBackgroundMotion';
import { useAppContext, ACTIONS } from '../context/AppContext';

const FEATURE_PILLS = [
  { icon: Sparkles, text: 'AI-powered skill extraction' },
  { icon: Sliders, text: 'Personalized learning roadmap' },
  { icon: LayoutGrid, text: 'Visual skill-gap analysis' },
  { icon: CheckCircle2, text: 'Progress tracking' },
  { icon: Shield, text: 'Privacy-focused experience' },
];

const HERO_CARDS = [
  {
    icon: User,
    title: 'Personalized Roadmaps',
    link: '/onboarding/skills',
  },
  {
    icon: BarChart3,
    title: 'Skill Gap Analysis',
    link: '/onboarding/skills',
  },
  {
    icon: TrendingUp,
    title: 'Progress Tracking',
    link: '/onboarding/skills',
  },
  {
    icon: Cpu,
    title: 'AI-Powered Insights',
    link: '/onboarding/skills',
  },
];

const WORKFLOW_STEPS = [
  {
    step: '1',
    title: 'Discover Role',
    desc: 'Explore potential career paths and relevant skills based on your interests.',
    icon: Search,
  },
  {
    step: '2',
    title: 'Analyze Skills',
    desc: 'Identify your current skills and find the gaps for your target role.',
    icon: BarChart3,
  },
  {
    step: '3',
    title: 'Prioritize',
    desc: 'Focus on the most important skills for faster progress.',
    icon: Star,
  },
  {
    step: '4',
    title: 'Roadmap',
    desc: 'Get a personalized learning plan with clear milestones.',
    icon: BookOpen,
  },
  {
    step: '5',
    title: 'Track Progress',
    desc: 'Monitor your progress and stay on track toward your goal.',
    icon: TrendingUp,
  },
];

export default function LandingPage() {
  const { state, dispatch } = useAppContext();
  const [isCtaHovered, setIsCtaHovered] = useState(false);

  const toggleTheme = () => {
    const nextTheme = state.theme === 'dark' ? 'light' : 'dark';
    dispatch({ type: ACTIONS.SET_THEME, payload: nextTheme });
  };

  return (
    <div className="min-h-screen bg-background text-text-primary font-sans selection:bg-accent/20 flex flex-col relative overflow-x-hidden">
      {/* ── Full-Viewport Ambient Career Path Background ── */}
      <LandingBackgroundMotion isCtaHovered={isCtaHovered} />

      {/* ── Top Navigation ── */}
      <header className="border-b border-border/80 sticky top-0 z-30 bg-background/80 backdrop-blur-md">
        <nav className="max-w-6xl mx-auto px-6 h-16 flex items-center justify-between">
          <Link to="/" className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-800 dark:bg-emerald-500 flex items-center justify-center text-white dark:text-zinc-950 shadow-sm">
              <Sparkles size={16} />
            </div>
            <span className="font-semibold text-[15px] tracking-tight text-text-primary flex items-center gap-1">
              SkillBridge
              <span className="text-[10px] font-bold bg-surface-muted text-accent border border-border px-1.5 py-0.5 rounded">
                AI
              </span>
            </span>
          </Link>

          {/* Nav Links */}
          <div className="hidden md:flex items-center gap-8 text-xs font-medium text-text-secondary">
            <a href="#features" className="hover:text-text-primary transition-colors">
              Features
            </a>
            <a href="#how-it-works" className="hover:text-text-primary transition-colors">
              How It Works
            </a>
            <a href="#about" className="hover:text-text-primary transition-colors">
              About
            </a>
          </div>

          {/* Action buttons + Theme switcher */}
          <div className="flex items-center gap-3">
            <button
              type="button"
              onClick={toggleTheme}
              aria-label="Toggle light/dark theme"
              className="p-2 rounded-xl border border-border text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors cursor-pointer"
            >
              {state.theme === 'dark' ? (
                <Sun size={15} className="text-amber-400" />
              ) : (
                <Moon size={15} className="text-teal-700" />
              )}
            </button>

            <Link
              to="/login"
              className="text-xs font-medium text-text-secondary hover:text-text-primary px-3 py-2 transition-colors"
            >
              Sign In
            </Link>

            <Link
              to="/onboarding/skills"
              className="btn-accent text-xs px-4 py-2"
            >
              <span>Get Started</span>
              <ArrowRight size={13} />
            </Link>
          </div>
        </nav>
      </header>

      {/* ── Top Feature Pills Bar ── */}
      <section id="features" className="w-full z-10 pt-5 pb-1">
        <div className="max-w-6xl mx-auto px-6 flex flex-wrap items-center justify-center sm:justify-start gap-2.5">
          {FEATURE_PILLS.map((pill, i) => {
            const Icon = pill.icon;
            return (
              <div
                key={i}
                className="inline-flex items-center gap-1.5 px-3 py-1 rounded-full bg-surface/70 dark:bg-surface/40 backdrop-blur-sm border border-border/80 text-[11px] font-medium text-text-secondary shadow-xs hover:border-accent/40 transition-colors"
              >
                <Icon size={12} className="text-accent" />
                <span>{pill.text}</span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Hero Section (Open Space for Career Path Ambient Background) ── */}
      <section className="relative max-w-6xl mx-auto px-6 pt-10 pb-16 grid lg:grid-cols-12 gap-8 items-center w-full z-10">
        {/* Left Column: Headline & Action */}
        <div className="lg:col-span-6 space-y-6 text-left">
          <div className="inline-flex items-center gap-2">
            <span className="text-xs font-semibold tracking-wider text-teal-600 dark:text-emerald-400 uppercase">
              YOUR CAREER. A CLEARER PATH.
            </span>
          </div>

          <h1 className="text-4xl sm:text-5xl lg:text-[3.25rem] font-bold tracking-tight text-text-primary leading-[1.12]">
            Close the gap between<br />
            where you are and<br />
            <span className="text-transparent bg-clip-text bg-gradient-to-r from-teal-400 to-emerald-400 dark:from-emerald-400 dark:to-teal-300">
              where you want to be.
            </span>
          </h1>

          <p className="text-base sm:text-lg text-text-secondary leading-relaxed max-w-lg">
            Skill Bridge AI helps you understand the skills you need for your target job role, creates a personalized learning roadmap, and lets you track your progress — all in one place.
          </p>

          <div className="pt-2 flex flex-col sm:flex-row items-stretch sm:items-center gap-3">
            <Link
              to="/onboarding/skills"
              onMouseEnter={() => setIsCtaHovered(true)}
              onMouseLeave={() => setIsCtaHovered(false)}
              className="btn-accent py-3 px-6 text-sm flex items-center justify-center gap-2 shadow-sm rounded-xl font-medium"
            >
              <span>Build My Roadmap</span>
              <ArrowRight size={15} />
            </Link>
          </div>
        </div>

        {/* Right Column: Open Natural Spacer for the Full-Viewport Career Animation */}
        <div
          className="hidden lg:block lg:col-span-6 min-h-[380px] pointer-events-none"
          aria-hidden="true"
        />
      </section>

      {/* ── 4 Feature Cards Row ── */}
      <section className="max-w-6xl mx-auto px-6 py-4 w-full z-10 relative">
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {HERO_CARDS.map((card, i) => {
            const Icon = card.icon;
            return (
              <Link
                to={card.link}
                key={i}
                className="bg-surface/80 dark:bg-surface/40 backdrop-blur-sm border border-border/80 rounded-2xl p-4 sm:p-5 hover:border-accent/50 transition-all flex items-center justify-between group shadow-xs hover:shadow-sm"
              >
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-xl bg-surface-muted dark:bg-emerald-950/40 border border-border/80 flex items-center justify-center text-accent group-hover:text-emerald-400 group-hover:border-accent/40 transition-colors">
                    <Icon size={16} />
                  </div>
                  <span className="text-xs sm:text-sm font-semibold text-text-primary group-hover:text-accent transition-colors">
                    {card.title}
                  </span>
                </div>
                <ArrowRight
                  size={14}
                  className="text-text-secondary group-hover:text-accent group-hover:translate-x-1 transition-all"
                />
              </Link>
            );
          })}
        </div>
      </section>

      {/* ── How It Works Section ── */}
      <section id="how-it-works" className="max-w-6xl mx-auto px-6 pt-16 pb-24 w-full z-10 relative">
        <div className="flex flex-col sm:flex-row sm:items-end justify-between mb-12 gap-4">
          <div>
            <p className="text-xs font-semibold uppercase tracking-wider text-accent mb-2">
              YOUR JOURNEY, SIMPLIFIED
            </p>
            <h2 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
              How SkillBridge AI Works
            </h2>
            <p className="text-xs sm:text-sm text-text-secondary mt-2 max-w-lg">
              From where you are to where you want to be — we guide you through every step of your career journey.
            </p>
          </div>
          <div>
            <a
              href="#about"
              className="btn-outline text-xs px-4 py-2 inline-flex items-center gap-1.5"
            >
              <span>Learn More</span>
              <ArrowRight size={13} />
            </a>
          </div>
        </div>

        {/* 5 Process Steps Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-4">
          {WORKFLOW_STEPS.map((step, idx) => {
            const Icon = step.icon;
            return (
              <div
                key={idx}
                className="bg-surface/80 dark:bg-surface/40 backdrop-blur-sm border border-border/80 rounded-2xl p-5 flex flex-col justify-between hover:border-accent/50 transition-colors group relative"
              >
                <div>
                  <div className="flex items-center justify-between mb-4">
                    <div className="w-8 h-8 rounded-full bg-surface-muted dark:bg-surface/80 border border-border flex items-center justify-center text-text-secondary group-hover:text-accent group-hover:border-accent/40 transition-colors">
                      <Icon size={15} />
                    </div>
                    <span className="w-5 h-5 rounded-full bg-surface-muted border border-border/70 text-[10px] font-bold text-text-secondary flex items-center justify-center">
                      {step.step}
                    </span>
                  </div>
                  <h3 className="text-xs sm:text-sm font-semibold text-text-primary mb-1.5">
                    {step.title}
                  </h3>
                  <p className="text-[11px] text-text-secondary leading-relaxed">
                    {step.desc}
                  </p>
                </div>
              </div>
            );
          })}
        </div>
      </section>

      {/* ── Footer ── */}
      <footer id="about" className="border-t border-border/80 bg-surface/80 dark:bg-surface/30 backdrop-blur-sm mt-auto py-8 px-6 text-xs text-text-secondary z-10 relative">
        <div className="max-w-6xl mx-auto flex flex-col sm:flex-row items-center justify-between gap-4">
          <div className="flex items-center gap-2">
            <div className="w-5 h-5 rounded-md bg-teal-800 dark:bg-emerald-500 flex items-center justify-center text-white dark:text-zinc-950">
              <Sparkles size={11} />
            </div>
            <span className="font-semibold text-text-primary">SkillBridge AI</span>
            <span className="text-text-secondary/80">— Personalized Career Progression</span>
          </div>

          <p className="text-[11px] text-text-secondary/70">
            © 2026 SkillBridge AI. Better skills. Brighter future.
          </p>
        </div>
      </footer>
    </div>
  );
}
