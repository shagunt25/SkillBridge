import { Link } from 'react-router-dom';
import { ArrowRight, BarChart2, Map, Sparkles, CheckCircle2, Zap } from 'lucide-react';

const FEATURES = [
  {
    icon: <BarChart2 size={22} className="text-signal" />,
    title: 'Skill Gap Analysis',
    desc: "Upload your resume or list your skills. We pinpoint exactly what's missing for your target role.",
  },
  {
    icon: <Map size={22} className="text-amber" />,
    title: 'AI Learning Roadmap',
    desc: 'A structured, module-by-module path built for your specific gap — not a generic course list.',
  },
  {
    icon: <Sparkles size={22} className="text-green" />,
    title: 'Refine with AI',
    desc: 'Too much? Too little? Tell the AI in plain English and your roadmap updates instantly.',
  },
];

const STEPS = [
  { num: '01', title: 'Add Your Skills', desc: 'Upload a resume or type your skills manually.' },
  { num: '02', title: 'Set Your Target', desc: 'Paste a job description or name your goal role.' },
  { num: '03', title: 'Get Your Roadmap', desc: 'Receive a structured, trackable learning path in seconds.' },
];

export default function LandingPage() {
  return (
    <div className="page-container">
      {/* ── Navbar ── */}
      <nav className="max-w-6xl mx-auto px-5 sm:px-8 h-16 flex items-center justify-between">
        <div className="flex items-center gap-2 font-heading font-bold text-lg">
          <div className="w-8 h-8 rounded-lg bg-signal flex items-center justify-center">
            <Zap size={15} className="text-white" fill="white" />
          </div>
          <span className="text-offwhite">
            Skill<span className="text-signal">Bridge</span>
            <span className="text-amber ml-0.5">AI</span>
          </span>
        </div>
        <div className="flex items-center gap-3">
          <Link to="/login" className="text-slate hover:text-offwhite text-sm transition-colors hidden sm:block">
            Sign in
          </Link>
          <Link to="/signup" className="btn-primary text-sm py-2 px-5">
            Get Started Free
          </Link>
        </div>
      </nav>

      {/* ── Hero ── */}
      <section className="relative overflow-hidden pt-16 pb-24 px-5 sm:px-8 text-center">
        {/* Background glow blobs */}
        <div className="absolute top-0 left-1/2 -translate-x-1/2 w-[600px] h-[400px] rounded-full opacity-[0.07] bg-signal blur-[120px] pointer-events-none" />
        <div className="absolute top-1/4 right-0 w-[300px] h-[300px] rounded-full opacity-[0.05] bg-green blur-[100px] pointer-events-none" />

        <div className="relative max-w-3xl mx-auto fade-up">
          <span className="tag-signal mb-6 inline-flex">
            <Sparkles size={11} /> Powered by AI · Free to Start
          </span>

          <h1 className="font-heading font-bold text-4xl sm:text-5xl lg:text-6xl text-offwhite leading-tight mt-4">
            Your Career Gap,
            <br />
            <span className="text-signal">Bridged by AI.</span>
          </h1>

          <p className="mt-6 text-slate text-base sm:text-lg max-w-xl mx-auto leading-relaxed">
            Upload your resume, name your target role, and get a personalized,
            step-by-step learning roadmap — built in seconds, tracked as you go.
          </p>

          <div className="mt-10 flex flex-col sm:flex-row items-center justify-center gap-4">
            <Link to="/onboarding/skills" className="btn-primary flex items-center gap-2 text-base px-7 py-3.5 w-full sm:w-auto justify-center">
              Build My Roadmap <ArrowRight size={17} />
            </Link>
            <Link to="/roadmap/review" className="btn-secondary text-base px-7 py-3.5 w-full sm:w-auto justify-center flex">
              See a Sample
            </Link>
          </div>

          {/* Social proof */}
          <p className="mt-8 text-xs text-slate">
            No credit card required &nbsp;·&nbsp; Results in under 10 seconds
          </p>
        </div>

        {/* Mini trail preview */}
        <div className="relative max-w-2xl mx-auto mt-16 card border border-white/5 overflow-hidden">
          <p className="section-label mb-4">Your learning trail</p>
          <div className="flex items-center gap-0">
            {['Python Basics', 'SQL & DBs', 'REST APIs', 'Cloud & DevOps'].map((label, i) => (
              <div key={i} className="flex items-center flex-1 min-w-0">
                <div className="flex flex-col items-center gap-1.5 flex-shrink-0">
                  <div className={`w-9 h-9 rounded-full flex items-center justify-center text-xs font-heading font-bold ${
                    i === 0 ? 'bg-green text-navy' :
                    i === 1 ? 'bg-signal text-white' :
                    'bg-navy-light border border-white/10 text-slate'
                  }`}>
                    {i === 0 ? <CheckCircle2 size={15} /> : i + 1}
                  </div>
                  <span className="text-[9px] text-slate text-center leading-tight max-w-[60px]">{label}</span>
                </div>
                {i < 3 && <div className="flex-1 h-px bg-white/10 mb-5" />}
              </div>
            ))}
          </div>
          {/* Gradient overlay at bottom */}
          <div className="absolute bottom-0 left-0 right-0 h-16 bg-gradient-to-t from-navy-light to-transparent pointer-events-none" />
        </div>
      </section>

      {/* ── Features ── */}
      <section className="py-20 px-5 sm:px-8 border-t border-white/5">
        <div className="max-w-6xl mx-auto">
          <p className="section-label text-center mb-4">Why SkillBridge AI</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-center text-offwhite mb-12">
            Not just a course recommendation.
            <br className="hidden sm:block" /> A structured path to your goal.
          </h2>

          <div className="grid sm:grid-cols-3 gap-5">
            {FEATURES.map((f, i) => (
              <div
                key={i}
                className="card border border-white/5 hover:border-white/10 transition-colors group"
              >
                <div className="w-10 h-10 rounded-lg bg-navy flex items-center justify-center mb-4 group-hover:scale-110 transition-transform">
                  {f.icon}
                </div>
                <h3 className="font-heading font-semibold text-offwhite mb-2">{f.title}</h3>
                <p className="text-sm text-slate leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── How it Works ── */}
      <section className="py-20 px-5 sm:px-8 bg-navy-light">
        <div className="max-w-4xl mx-auto text-center">
          <p className="section-label mb-4">How it works</p>
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-offwhite mb-14">
            Three steps to a clearer career path.
          </h2>

          <div className="grid sm:grid-cols-3 gap-8 relative">
            {/* Connector line on desktop */}
            <div className="hidden sm:block absolute top-8 left-[calc(16.6%+16px)] right-[calc(16.6%+16px)] h-px bg-white/10" />

            {STEPS.map((s, i) => (
              <div key={i} className="flex flex-col items-center text-center relative">
                <div className="w-16 h-16 rounded-full bg-navy border border-white/10 flex items-center justify-center mb-4 relative z-10">
                  <span className="font-heading font-bold text-signal text-lg">{s.num}</span>
                </div>
                <h3 className="font-heading font-semibold text-offwhite mb-2">{s.title}</h3>
                <p className="text-sm text-slate leading-relaxed">{s.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA Footer ── */}
      <section className="py-20 px-5 sm:px-8 text-center">
        <div className="max-w-xl mx-auto">
          <h2 className="font-heading font-bold text-2xl sm:text-3xl text-offwhite mb-4">
            Ready to close your skill gap?
          </h2>
          <p className="text-slate mb-8">
            Join thousands building toward their next role with AI-powered roadmaps.
          </p>
          <Link to="/signup" className="btn-primary text-base px-8 py-3.5 inline-flex items-center gap-2">
            Get Started Free <ArrowRight size={17} />
          </Link>
        </div>
      </section>

      {/* Simple footer */}
      <footer className="border-t border-white/5 py-6 px-5 text-center text-xs text-slate">
        © 2024 SkillBridge AI · Built for learners.
      </footer>
    </div>
  );
}
