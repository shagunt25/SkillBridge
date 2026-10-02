import React, { useEffect } from 'react';
import { X, CheckCircle2, ArrowRight, BookOpen, Layers, Target } from 'lucide-react';
import { useAppContext, ACTIONS } from '../context/AppContext';

export default function SkillDrawer({ skill, targetRole, isOpen, onClose }) {
  const { state, dispatch } = useAppContext();

  // Listen for Escape key to close the side panel
  useEffect(() => {
    function handleKeyDown(e) {
      if (e.key === 'Escape' && isOpen) {
        onClose();
      }
    }
    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen, onClose]);

  const skillName = typeof skill === 'string' ? skill : skill?.name || '';
  const roleTitle = targetRole || state.targetValue || 'Target Role';

  // Determine if skill is already in modules
  const isAlreadyInRoadmap = (state.learningModules || []).some((mod) =>
    (mod.tasks || []).some((task) =>
      task.title?.toLowerCase().includes(skillName.toLowerCase())
    )
  );

  const handleAddToRoadmap = () => {
    if (skillName) {
      dispatch({ type: ACTIONS.ADD_SKILL_TO_ROADMAP, payload: skillName });
    }
    onClose();
  };

  return (
    <aside
      aria-label="Why this skill panel"
      className={`h-full flex flex-col border-border bg-surface flex-shrink-0 transition-all duration-300 ease-[cubic-bezier(0.2,0,0,1)] overflow-hidden z-20 ${
        isOpen
          ? 'w-full md:w-[380px] lg:w-[420px] border-l opacity-100 shadow-lg'
          : 'w-0 border-l-0 opacity-0 pointer-events-none'
      }`}
    >
      <div className="w-full md:w-[380px] lg:w-[420px] flex flex-col h-full">
        {/* Header */}
        <div className="p-6 border-b border-border flex items-start justify-between flex-shrink-0 bg-surface">
          <div>
            <div className="flex items-center gap-2 mb-1.5">
              <span className="text-[11px] font-semibold text-text-secondary uppercase tracking-wider">
                Skill Detail
              </span>
              <span className="badge-priority-high">
                High priority
              </span>
            </div>
            <h2 className="text-xl font-bold text-text-primary tracking-tight truncate max-w-[280px]">
              {skillName || 'Skill Analysis'}
            </h2>
          </div>
          <button
            type="button"
            onClick={onClose}
            aria-label="Close skill detail panel"
            className="p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors flex-shrink-0 ml-2"
          >
            <X size={18} />
          </button>
        </div>

        {/* Scrollable Content Body */}
        <div className="p-6 space-y-6 flex-1 overflow-y-auto no-scrollbar">
          {/* Why it matters section */}
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-secondary mb-2">
              <Target size={14} className="text-accent" />
              <span>Why it matters for {roleTitle}</span>
            </div>
            <p className="text-sm text-text-primary/90 leading-relaxed bg-surface-muted/60 p-4 rounded-xl border border-border">
              Proficiency in <strong className="text-text-primary">{skillName}</strong> is frequently required by hiring teams for {roleTitle}. It directly impacts code reliability, scalability, and integration speed in production workflows.
            </p>
          </div>

          {/* Key applications in production */}
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-secondary mb-2.5">
              <Layers size={14} className="text-teal-600 dark:text-teal-400" />
              <span>Key applications in production</span>
            </div>
            <ul className="space-y-2.5 text-xs text-text-secondary">
              <li className="flex items-start gap-2.5">
                <CheckCircle2 size={15} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>Designing, implementing, and deploying core architecture components.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 size={15} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>Collaborating across team boundaries and ensuring adherence to engineering standards.</span>
              </li>
              <li className="flex items-start gap-2.5">
                <CheckCircle2 size={15} className="text-emerald-500 flex-shrink-0 mt-0.5" />
                <span>Optimizing system performance, maintainability, and end-to-end execution latency.</span>
              </li>
            </ul>
          </div>

          {/* Suggested learning path */}
          <div>
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-text-secondary mb-2">
              <BookOpen size={14} className="text-amber-500" />
              <span>Suggested learning direction</span>
            </div>
            <div className="p-3.5 bg-surface-muted rounded-xl border border-border text-xs text-text-primary space-y-1.5">
              <p className="font-medium text-text-primary">
                1. Review foundational concepts and syntax
              </p>
              <p className="text-text-secondary">
                2. Build a standalone practical micro-project to test real-world scenarios
              </p>
              <p className="text-text-secondary">
                3. Integrate with an automated testing and deployment pipeline
              </p>
            </div>
          </div>
        </div>

        {/* Footer Action */}
        <div className="p-5 border-t border-border bg-surface-muted/40 flex-shrink-0">
          <button
            type="button"
            onClick={handleAddToRoadmap}
            disabled={isAlreadyInRoadmap}
            className="w-full btn-accent flex items-center justify-center gap-2 py-3 rounded-xl text-sm font-medium transition-all"
          >
            {isAlreadyInRoadmap ? (
              <span>Already in Roadmap</span>
            ) : (
              <>
                <span>Add {skillName} to Roadmap</span>
                <ArrowRight size={15} />
              </>
            )}
          </button>
        </div>
      </div>
    </aside>
  );
}
