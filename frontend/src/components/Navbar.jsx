import { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Menu, X, Zap } from 'lucide-react';

const NAV_LINKS = [
  { label: 'Home', to: '/' },
  { label: 'Dashboard', to: '/dashboard' },
  { label: 'My Roadmap', to: '/roadmap/review' },
  { label: 'Settings', to: '/settings' },
];

export default function Navbar() {
  const [open, setOpen] = useState(false);
  const { pathname } = useLocation();

  return (
    <nav className="sticky top-0 z-50 bg-navy/90 backdrop-blur border-b border-white/5">
      <div className="max-w-6xl mx-auto px-5 sm:px-8 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2 font-heading font-bold text-lg">
          <div className="w-8 h-8 rounded-lg bg-signal flex items-center justify-center">
            <Zap size={16} className="text-white" fill="white" />
          </div>
          <span className="text-offwhite">
            Skill<span className="text-signal">Bridge</span>
            <span className="text-amber ml-0.5">AI</span>
          </span>
        </Link>

        {/* Desktop links */}
        <div className="hidden sm:flex items-center gap-1">
          {NAV_LINKS.map(l => (
            <Link
              key={l.to}
              to={l.to}
              className={`px-4 py-2 rounded-lg text-sm font-body font-medium transition-colors ${
                pathname === l.to
                  ? 'bg-signal/10 text-signal'
                  : 'text-slate hover:text-offwhite hover:bg-white/5'
              }`}
            >
              {l.label}
            </Link>
          ))}
        </div>

        {/* Desktop CTA */}
        <div className="hidden sm:flex items-center gap-3">
          <Link to="/onboarding/skills" className="btn-primary text-sm py-2 px-5">
            New Roadmap
          </Link>
        </div>

        {/* Mobile hamburger */}
        <button
          onClick={() => setOpen(v => !v)}
          className="sm:hidden p-2 rounded-lg text-slate hover:text-offwhite hover:bg-white/5 transition-colors"
          aria-label="Toggle menu"
        >
          {open ? <X size={20} /> : <Menu size={20} />}
        </button>
      </div>

      {/* Mobile menu */}
      {open && (
        <div className="sm:hidden border-t border-white/5 bg-navy px-5 pb-4 pt-2 space-y-1">
          {NAV_LINKS.map(l => (
            <Link
              key={l.to}
              to={l.to}
              onClick={() => setOpen(false)}
              className={`block px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                pathname === l.to
                  ? 'bg-signal/10 text-signal'
                  : 'text-slate hover:text-offwhite hover:bg-white/5'
              }`}
            >
              {l.label}
            </Link>
          ))}
          <Link
            to="/onboarding/skills"
            onClick={() => setOpen(false)}
            className="block btn-primary text-sm text-center mt-2"
          >
            New Roadmap
          </Link>
        </div>
      )}
    </nav>
  );
}
