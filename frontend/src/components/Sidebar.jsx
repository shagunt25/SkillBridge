import React from 'react';
import { Link } from 'react-router-dom';
import {
  LogIn,
  FileText,
  Crosshair,
  Zap,
  LayoutGrid,
  Sliders,
  Settings,
  Lock,
  PanelLeftClose,
  PanelLeft,
  Sparkles,
  CheckCircle2,
  X,
} from 'lucide-react';
import { useAppContext } from '../context/AppContext';
import { useLayout } from '../context/LayoutContext';
import ProfileDropdown from './ProfileDropdown';

export default function Sidebar({ currentStep = 2 }) {
  const { state } = useAppContext();
  const { sidebarCollapsed, toggleSidebar, mobileOpen, closeMobile } = useLayout();

  const hasSkills = (state.currentSkills && state.currentSkills.length > 0) || state.resumeFile;
  const hasTarget = Boolean(state.targetValue);
  const hasRoadmap = Boolean(state.matchScore && state.learningModules?.length);

  const WORKFLOW_STEPS = [
    {
      id: 1,
      name: 'Sign in',
      path: '/login',
      icon: LogIn,
      isLocked: false,
    },
    {
      id: 2,
      name: 'Upload resume',
      path: '/onboarding/skills',
      icon: FileText,
      isLocked: false,
    },
    {
      id: 3,
      name: 'Target role',
      path: '/onboarding/target',
      icon: Crosshair,
      isLocked: !hasSkills && currentStep < 3,
    },
    {
      id: 4,
      name: 'Analyzing',
      path: '/roadmap/generating',
      icon: Zap,
      isLocked: (!hasSkills || !hasTarget) && currentStep < 4,
    },
    {
      id: 5,
      name: 'Gap analysis',
      path: '/roadmap/review',
      icon: LayoutGrid,
      isLocked: !hasRoadmap && currentStep < 5,
    },
    {
      id: 6,
      name: 'Roadmap',
      path: '/dashboard',
      icon: Sliders,
      isLocked: !hasRoadmap && currentStep < 6,
    },
  ];

  return (
    <>
      {/* ── Desktop Fixed Sidebar ── */}
      <aside
        aria-label="Sidebar navigation"
        className={`hidden md:flex flex-col border-r border-border bg-surface flex-shrink-0 h-screen sticky top-0 z-30 select-none transition-[width] duration-300 ease-[cubic-bezier(0.2,0,0,1)] ${
          sidebarCollapsed ? 'w-[76px]' : 'w-[260px]'
        }`}
      >
        {/* Header: Logo + Toggle */}
        <div className="h-16 px-4 flex items-center justify-between border-b border-border flex-shrink-0">
          <Link
            to="/"
            className="flex items-center gap-2.5 min-w-0"
            title="SkillBridge AI Home"
          >
            <div className="w-8 h-8 rounded-lg bg-teal-800 dark:bg-emerald-500 flex items-center justify-center flex-shrink-0 text-white dark:text-zinc-950 shadow-sm transition-transform hover:scale-105">
              <Sparkles size={16} />
            </div>
            <div
              className={`transition-all duration-200 overflow-hidden whitespace-nowrap ${
                sidebarCollapsed
                  ? 'opacity-0 max-w-0 pointer-events-none -translate-x-2'
                  : 'opacity-100 max-w-[150px] translate-x-0'
              }`}
            >
              <span className="font-semibold text-[15px] tracking-tight text-text-primary flex items-center gap-1">
                SkillBridge
                <span className="text-[10px] font-bold bg-surface-muted text-accent border border-border px-1.5 py-0.5 rounded">
                  AI
                </span>
              </span>
            </div>
          </Link>

          <button
            type="button"
            onClick={toggleSidebar}
            aria-label={sidebarCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors flex-shrink-0"
          >
            {sidebarCollapsed ? <PanelLeft size={16} /> : <PanelLeftClose size={16} />}
          </button>
        </div>

        {/* Workflow Steps - with upward smooth collapse transition */}
        <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto no-scrollbar">
          {/* Section Heading that smoothly collapses upward */}
          <div
            className={`transition-all duration-200 overflow-hidden px-2 mb-2 ${
              sidebarCollapsed
                ? 'opacity-0 max-h-0 -translate-y-1 mb-0 pointer-events-none'
                : 'opacity-100 max-h-6 translate-y-0'
            }`}
          >
            <p className="text-[10px] font-semibold tracking-wider text-text-secondary uppercase">
              WORKFLOW
            </p>
          </div>

          {WORKFLOW_STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isCompleted = currentStep !== null && currentStep > step.id;
            const isClickable = !step.isLocked || isActive;

            const stepNode = (
              <div
                className={`relative group w-full flex items-center h-10 px-2.5 rounded-xl text-sm transition-colors ${
                  isActive
                    ? 'bg-accent/15 text-accent font-semibold'
                    : isClickable
                    ? 'text-text-secondary hover:text-text-primary hover:bg-surface-muted'
                    : 'text-text-secondary/40 cursor-not-allowed'
                }`}
              >
                {/* Icon is fixed width to guarantee alignment */}
                <div className="w-6 h-6 flex items-center justify-center flex-shrink-0">
                  <Icon
                    size={16}
                    className={`transition-colors ${
                      isActive
                        ? 'text-accent'
                        : isCompleted
                        ? 'text-emerald-500'
                        : 'text-text-secondary'
                    }`}
                  />
                </div>

                {/* Step Name - smoothly collapses upward / horizontally without jumping */}
                <div
                  className={`flex-1 min-w-0 ml-2.5 transition-all duration-200 overflow-hidden whitespace-nowrap ${
                    sidebarCollapsed
                      ? 'opacity-0 max-w-0 -translate-x-1 pointer-events-none'
                      : 'opacity-100 max-w-[130px] translate-x-0'
                  }`}
                >
                  <span className="truncate text-[13px] block">{step.name}</span>
                </div>

                {/* Step badge / lock / checkmark */}
                <div
                  className={`transition-all duration-200 overflow-hidden flex-shrink-0 ${
                    sidebarCollapsed
                      ? 'opacity-0 max-w-0 pointer-events-none'
                      : 'opacity-100 max-w-[36px]'
                  }`}
                >
                  {step.isLocked ? (
                    <Lock size={12} className="text-text-secondary/40 ml-1" />
                  ) : isCompleted ? (
                    <CheckCircle2 size={13} className="text-emerald-500" />
                  ) : (
                    <span
                      className={`text-[11px] px-1.5 py-0.5 rounded font-medium ${
                        isActive
                          ? 'bg-accent text-white dark:text-zinc-950 font-bold'
                          : 'text-text-secondary bg-surface-muted border border-border'
                      }`}
                    >
                      {step.id}
                    </span>
                  )}
                </div>

                {/* Tooltip for collapsed state */}
                {sidebarCollapsed && (
                  <div
                    role="tooltip"
                    className="absolute left-full ml-3 px-3 py-1.5 rounded-lg bg-surface border border-border text-xs text-text-primary font-medium whitespace-nowrap shadow-xl opacity-0 pointer-events-none group-hover:opacity-100 transition-opacity duration-150 z-50 flex items-center gap-2"
                  >
                    <span>{step.name}</span>
                    {step.isLocked && <Lock size={11} className="text-text-secondary/60" />}
                    {isCompleted && <CheckCircle2 size={12} className="text-emerald-500" />}
                  </div>
                )}
              </div>
            );

            return isClickable ? (
              <Link key={step.id} to={step.path} className="block">
                {stepNode}
              </Link>
            ) : (
              <div key={step.id}>{stepNode}</div>
            );
          })}
        </div>

        {/* Sidebar Footer: User Profile + Settings */}
        <div className="p-3 border-t border-border flex items-center justify-between flex-shrink-0 bg-surface">
          <div className="flex items-center gap-2.5 min-w-0">
            <ProfileDropdown align="left" />
            <div
              className={`transition-all duration-200 overflow-hidden whitespace-nowrap min-w-0 ${
                sidebarCollapsed
                  ? 'opacity-0 max-w-0 pointer-events-none -translate-x-2'
                  : 'opacity-100 max-w-[130px] translate-x-0'
              }`}
            >
              <p className="text-xs font-semibold text-text-primary truncate">
                {state.user?.name || 'My Account'}
              </p>
              <p className="text-[11px] text-text-secondary truncate">
                {state.user?.email || 'SkillBridge'}
              </p>
            </div>
          </div>

          <div
            className={`transition-all duration-200 overflow-hidden flex-shrink-0 ${
              sidebarCollapsed
                ? 'opacity-0 max-w-0 pointer-events-none'
                : 'opacity-100 max-w-[32px]'
            }`}
          >
            <Link
              to="/settings"
              aria-label="Settings"
              className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors block"
            >
              <Settings size={15} />
            </Link>
          </div>
        </div>
      </aside>

      {/* ── Mobile Drawer Overlay ── */}
      {mobileOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-40 md:hidden transition-opacity"
          onClick={closeMobile}
        />
      )}

      {/* ── Mobile Sidebar Drawer ── */}
      <aside
        className={`fixed top-0 bottom-0 left-0 w-[260px] bg-surface border-r border-border z-50 transform transition-transform duration-300 md:hidden flex flex-col ${
          mobileOpen ? 'translate-x-0' : '-translate-x-full'
        }`}
      >
        <div className="h-16 px-4 flex items-center justify-between border-b border-border">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 rounded-lg bg-teal-800 dark:bg-emerald-500 flex items-center justify-center text-white dark:text-zinc-950">
              <Sparkles size={16} />
            </div>
            <span className="font-semibold text-[15px] tracking-tight text-text-primary flex items-center gap-1">
              SkillBridge
              <span className="text-[10px] font-bold bg-surface-muted text-accent border border-border px-1.5 py-0.5 rounded">
                AI
              </span>
            </span>
          </div>
          <button
            type="button"
            onClick={closeMobile}
            aria-label="Close menu"
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary"
          >
            <X size={18} />
          </button>
        </div>

        <div className="flex-1 px-3 py-4 space-y-1 overflow-y-auto">
          <p className="text-[10px] font-semibold tracking-wider text-text-secondary uppercase px-2 mb-3">
            WORKFLOW
          </p>
          {WORKFLOW_STEPS.map((step) => {
            const Icon = step.icon;
            const isActive = currentStep === step.id;
            const isClickable = !step.isLocked || isActive;

            const item = (
              <div
                onClick={closeMobile}
                className={`w-full flex items-center justify-between px-3 py-2.5 rounded-xl text-sm transition-colors ${
                  isActive
                    ? 'bg-accent/15 text-accent font-semibold'
                    : isClickable
                    ? 'text-text-secondary hover:text-text-primary hover:bg-surface-muted'
                    : 'text-text-secondary/40'
                }`}
              >
                <div className="flex items-center gap-2.5">
                  <Icon size={16} className={isActive ? 'text-accent' : 'text-text-secondary'} />
                  <span className="text-[13px]">{step.name}</span>
                </div>
                {step.isLocked ? (
                  <Lock size={12} className="text-text-secondary/40" />
                ) : (
                  <span
                    className={`text-[11px] px-1.5 py-0.5 rounded font-medium ${
                      isActive
                        ? 'bg-accent text-white dark:text-zinc-950 font-bold'
                        : 'text-text-secondary bg-surface-muted border border-border'
                    }`}
                  >
                    {step.id}
                  </span>
                )}
              </div>
            );

            return isClickable ? (
              <Link key={step.id} to={step.path}>
                {item}
              </Link>
            ) : (
              <div key={step.id}>{item}</div>
            );
          })}
        </div>

        <div className="p-4 border-t border-border flex items-center justify-between">
          <div className="flex items-center gap-2.5">
            <ProfileDropdown align="left" />
            <span className="text-xs font-medium text-text-primary truncate">
              {state.user?.name || 'Account'}
            </span>
          </div>
          <Link
            to="/settings"
            onClick={closeMobile}
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary"
          >
            <Settings size={16} />
          </Link>
        </div>
      </aside>
    </>
  );
}
