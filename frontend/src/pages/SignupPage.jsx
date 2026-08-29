import { useState } from 'react';
import { Link } from 'react-router-dom';
import { Eye, EyeOff, Zap, CheckCircle2 } from 'lucide-react';

const PERKS = [
  'AI-generated roadmap in seconds',
  'Track progress with checkpoints',
  'Refine with natural language',
];

export default function SignupPage() {
  const [showPw, setShowPw] = useState(false);
  const [form, setForm] = useState({ name: '', email: '', password: '' });

  const handle = (e) => setForm(p => ({ ...p, [e.target.name]: e.target.value }));

  return (
    <div className="page-container flex flex-col items-center justify-center px-5 py-16">
      {/* Logo */}
      <Link to="/" className="flex items-center gap-2 font-heading font-bold text-xl mb-10">
        <div className="w-9 h-9 rounded-xl bg-signal flex items-center justify-center">
          <Zap size={17} className="text-white" fill="white" />
        </div>
        <span className="text-offwhite">
          Skill<span className="text-signal">Bridge</span>
          <span className="text-amber ml-0.5">AI</span>
        </span>
      </Link>

      <div className="w-full max-w-4xl grid sm:grid-cols-2 gap-6 items-start">
        {/* Left: value prop */}
        <div className="hidden sm:flex flex-col justify-center card border border-white/5 h-full">
          <h2 className="font-heading font-bold text-2xl text-offwhite mb-3">
            Build your path<br />to the role you want.
          </h2>
          <p className="text-slate text-sm leading-relaxed mb-8">
            SkillBridge AI analyses your current skills, identifies your gaps,
            and creates a structured, trackable roadmap — personalised for your goal.
          </p>
          <ul className="space-y-3">
            {PERKS.map((p, i) => (
              <li key={i} className="flex items-center gap-3 text-sm text-offwhite">
                <CheckCircle2 size={16} className="text-green flex-shrink-0" />
                {p}
              </li>
            ))}
          </ul>
        </div>

        {/* Right: form */}
        <div className="card border border-white/5 fade-up">
          <h1 className="font-heading font-bold text-2xl text-offwhite mb-1">Create your account</h1>
          <p className="text-slate text-sm mb-8">Free forever, no credit card needed.</p>

          {/* Google SSO (visual) */}
          <button className="w-full flex items-center justify-center gap-3 py-3 rounded-lg border border-white/10 text-offwhite text-sm font-medium hover:bg-white/5 transition-colors mb-6">
            <svg width="18" height="18" viewBox="0 0 48 48">
              <path fill="#FFC107" d="M43.6 20H24v8h11.3C33.7 32.5 29.3 35 24 35c-6.1 0-11-4.9-11-11s4.9-11 11-11c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.5 7.2 29 5 24 5 12.4 5 3 14.4 3 26s9.4 21 21 21 21-9.4 21-21c0-1.3-.1-2.7-.4-4z"/>
              <path fill="#FF3D00" d="M6.3 16.7l6.6 4.8C14.5 18 19 15 24 15c2.8 0 5.3 1 7.2 2.7l5.7-5.7C33.5 8.2 29 6 24 6c-7.7 0-14.3 4.5-17.7 10.7z"/>
              <path fill="#4CAF50" d="M24 47c5.2 0 9.9-1.9 13.5-5l-6.2-5.2C29.5 38.5 26.9 39 24 39c-5.2 0-9.6-3.5-11.2-8.3l-6.6 5.1C9.7 43.1 16.4 47 24 47z"/>
              <path fill="#1976D2" d="M43.6 20H24v8h11.3c-.9 2.5-2.6 4.5-4.8 5.8l6.2 5.2C40.3 35.5 44 31 44 26c0-1.3-.1-2.7-.4-4z"/>
            </svg>
            Continue with Google
          </button>

          <div className="flex items-center gap-3 mb-6">
            <div className="flex-1 h-px bg-white/8" />
            <span className="text-xs text-slate">or</span>
            <div className="flex-1 h-px bg-white/8" />
          </div>

          <form onSubmit={e => e.preventDefault()} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-offwhite mb-1.5" htmlFor="signup-name">Full name</label>
              <input id="signup-name" name="name" type="text" placeholder="Alex Chen"
                value={form.name} onChange={handle} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-offwhite mb-1.5" htmlFor="signup-email">Email</label>
              <input id="signup-email" name="email" type="email" placeholder="you@example.com"
                value={form.email} onChange={handle} className="input-field" />
            </div>
            <div>
              <label className="block text-sm font-medium text-offwhite mb-1.5" htmlFor="signup-password">Password</label>
              <div className="relative">
                <input id="signup-password" name="password" type={showPw ? 'text' : 'password'}
                  placeholder="At least 8 characters" value={form.password} onChange={handle}
                  className="input-field pr-11" />
                <button type="button" onClick={() => setShowPw(v => !v)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate hover:text-offwhite transition-colors">
                  {showPw ? <EyeOff size={17} /> : <Eye size={17} />}
                </button>
              </div>
            </div>

            <Link to="/onboarding/skills">
              <button type="submit" className="btn-primary w-full mt-2 py-3 text-base justify-center">
                Create Free Account
              </button>
            </Link>
          </form>

          <p className="text-center text-sm text-slate mt-6">
            Already have an account?{' '}
            <Link to="/login" className="text-signal hover:underline font-medium">Sign in</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
