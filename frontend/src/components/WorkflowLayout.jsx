import React from 'react';
import { Link, useLocation } from 'react-router-dom';
import { Home, Sliders, User } from 'lucide-react';
import Sidebar from './Sidebar';
import TopNavigation from './TopNavigation';

/**
 * WorkflowLayout
 * Core React Application Shell for SkillBridge AI internal workflow pages.
 * - Sidebar is fixed & sticky.
 * - TopNavigation is fixed & sticky.
 * - ONLY page content inside <main> scrolls.
 * - Supports integrated right-side panels (such as "Why This Skill") via `sidePanel` prop,
 *   which automatically resizes the main content smoothly with zero blur or modal overlays.
 */
export default function WorkflowLayout({
  children,
  currentStep = 2,
  pageTitle = '',
  sidePanel = null,
}) {
  const location = useLocation();

  return (
    <div className="h-screen w-screen overflow-hidden flex bg-background text-text-primary font-sans select-none">
      {/* ── Fixed Desktop Left Sidebar & Mobile Drawer ── */}
      <Sidebar currentStep={currentStep} />

      {/* ── Main Workspace Area ── */}
      <div className="flex-1 flex flex-col min-w-0 h-full overflow-hidden relative">
        {/* Fixed/Sticky Top Navigation */}
        <TopNavigation pageTitle={pageTitle} />

        {/* Content Row: Scrollable Page Content + Integrated Side Panel */}
        <div className="flex-1 flex overflow-hidden min-h-0 relative pb-14 md:pb-0">
          {/* Scrollable Page Body (ONLY this scrolls) */}
          <main className="flex-1 overflow-y-auto px-4 sm:px-8 lg:px-12 py-6 sm:py-8 h-full transition-all duration-300">
            {children}
          </main>

          {/* Integrated Right-side Panel (e.g. Why This Skill) */}
          {sidePanel}
        </div>
      </div>

      {/* ── Mobile Bottom Navigation Bar ── */}
      <nav
        aria-label="Mobile navigation bar"
        className="md:hidden fixed bottom-0 left-0 right-0 h-14 bg-surface border-t border-border z-30 flex items-center justify-around px-4"
      >
        <Link
          to="/"
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${
            location.pathname === '/' ? 'text-accent font-semibold' : 'text-text-secondary'
          }`}
        >
          <Home size={18} />
          <span>Home</span>
        </Link>
        <Link
          to="/dashboard"
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${
            location.pathname === '/dashboard' ? 'text-accent font-semibold' : 'text-text-secondary'
          }`}
        >
          <Sliders size={18} />
          <span>Roadmap</span>
        </Link>
        <Link
          to="/settings"
          className={`flex flex-col items-center gap-1 text-[10px] font-medium transition-colors ${
            location.pathname === '/settings' ? 'text-accent font-semibold' : 'text-text-secondary'
          }`}
        >
          <User size={18} />
          <span>Profile</span>
        </Link>
      </nav>
    </div>
  );
}
