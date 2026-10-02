import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  CheckCircle2,
  AlertTriangle,
  ArrowRight,
  Plus,
  Info,
  Sliders,
  Briefcase,
  HelpCircle,
} from 'lucide-react';
import WorkflowLayout from '../components/WorkflowLayout';
import SkillDrawer from '../components/SkillDrawer';
import { useAppContext, ACTIONS } from '../context/AppContext';

// Donut Chart Component with accessible SVG & text
function MatchDonut({ percentage = 50, size = 110, strokeWidth = 9 }) {
  const radius = (size - strokeWidth * 2) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (percentage / 100) * circumference;

  return (
    <div
      className="relative flex items-center justify-center flex-shrink-0"
      style={{ width: size, height: size }}
      role="img"
      aria-label={`Match score: ${percentage}%`}
    >
      <svg width={size} height={size} className="-rotate-90">
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--border)"
          strokeWidth={strokeWidth}
        />
        <circle
          cx={size / 2}
          cy={size / 2}
          r={radius}
          fill="none"
          stroke="var(--accent)"
          strokeWidth={strokeWidth}
          strokeDasharray={circumference}
          strokeDashoffset={strokeDashoffset}
          strokeLinecap="round"
          className="transition-all duration-1000 ease-out"
        />
      </svg>
      <div className="absolute inset-0 flex flex-col items-center justify-center text-center select-none">
        <span className="text-xl font-bold text-text-primary leading-tight">
          {percentage}%
        </span>
        <span className="text-[11px] text-text-secondary font-medium">Match</span>
      </div>
    </div>
  );
}

export default function RoadmapReviewPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const [selectedDrawerSkill, setSelectedDrawerSkill] = useState(null);
  const [showAllMatched, setShowAllMatched] = useState(false);

  const targetRole = state.targetValue || 'Backend AI/ML Engineer';

  // Use actual data from state
  const matchedSkills = state.currentSkills && state.currentSkills.length > 0
    ? state.currentSkills
    : ['Python', 'SQL', 'REST APIs', 'Git', 'Data Analysis'];

  const missingSkills = state.missingSkills && state.missingSkills.length > 0
    ? state.missingSkills
    : ['Docker', 'FastAPI', 'CI/CD', 'System Design'];

  const totalCount = matchedSkills.length + missingSkills.length;
  const matchedCount = matchedSkills.length;
  const missingCount = missingSkills.length;

  const matchScore = typeof state.matchScore === 'number'
    ? state.matchScore
    : totalCount > 0
    ? Math.round((matchedCount / totalCount) * 100)
    : 50;

  // Derive priority distribution without hardcoding
  const highPriorityCount = Math.max(1, Math.ceil(missingCount * 0.5));
  const medPriorityCount = Math.max(0, Math.floor(missingCount * 0.35));
  const lowPriorityCount = Math.max(0, missingCount - highPriorityCount - medPriorityCount);

  const displayedMatched = showAllMatched ? matchedSkills : matchedSkills.slice(0, 8);

  const handleAddSkillToRoadmap = (skillName) => {
    dispatch({ type: ACTIONS.ADD_SKILL_TO_ROADMAP, payload: skillName });
  };

  return (
    <WorkflowLayout
      currentStep={5}
      pageTitle="Gap analysis"
      sidePanel={
        <SkillDrawer
          skill={selectedDrawerSkill}
          targetRole={targetRole}
          isOpen={Boolean(selectedDrawerSkill)}
          onClose={() => setSelectedDrawerSkill(null)}
        />
      }
    >
      <div className="max-w-4xl mx-auto space-y-8">
        {/* ── Top Header Banner ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="text-xs font-semibold uppercase tracking-wider text-accent">
                Skill Gap Analysis
              </span>
              <span className="inline-flex items-center gap-1 text-xs px-2.5 py-0.5 rounded-full bg-surface-muted border border-border text-text-secondary">
                <Briefcase size={12} />
                <span>{targetRole}</span>
              </span>
            </div>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
              See how your skills match your target role
            </h1>
          </div>

          <Link
            to="/onboarding/target"
            className="btn-outline text-xs px-3.5 py-1.5 self-start sm:self-auto"
          >
            Edit Goal
          </Link>
        </div>

        {/* ── Top Match Overview Card ── */}
        <div className="card-surface p-6 sm:p-8">
          <div className="grid md:grid-cols-12 gap-6 items-center">
            {/* Left: Donut Chart & Legend */}
            <div className="md:col-span-6 flex items-center gap-6">
              <MatchDonut percentage={matchScore} />
              <div className="space-y-1.5 text-xs">
                <p className="font-semibold text-text-primary text-sm">
                  {matchedCount} of {totalCount} Skills Matched
                </p>
                <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>Matched skills: <strong>{matchedCount}</strong></span>
                </div>
                <div className="flex items-center gap-2 text-rose-600 dark:text-rose-400">
                  <span className="w-2 h-2 rounded-full bg-rose-500" />
                  <span>Missing skills: <strong>{missingCount}</strong></span>
                </div>
                <div className="flex items-center gap-2 text-text-secondary">
                  <span className="w-2 h-2 rounded-full bg-text-secondary" />
                  <span>Total analyzed: <strong>{totalCount}</strong></span>
                </div>
              </div>
            </div>

            {/* Right: Priority Counts */}
            <div className="md:col-span-6 grid grid-cols-3 gap-3">
              <div className="bg-surface-muted border border-border p-3.5 rounded-xl text-center">
                <span className="badge-priority-high mb-1">High priority</span>
                <p className="text-xl font-bold text-text-primary mt-1">
                  {highPriorityCount}
                </p>
              </div>
              <div className="bg-surface-muted border border-border p-3.5 rounded-xl text-center">
                <span className="badge-priority-med mb-1">Medium</span>
                <p className="text-xl font-bold text-text-primary mt-1">
                  {medPriorityCount}
                </p>
              </div>
              <div className="bg-surface-muted border border-border p-3.5 rounded-xl text-center">
                <span className="badge-priority-low mb-1">Low priority</span>
                <p className="text-xl font-bold text-text-primary mt-1">
                  {lowPriorityCount}
                </p>
              </div>
            </div>
          </div>
        </div>

        {/* ── Two Column Skills Comparison ── */}
        <div className="grid md:grid-cols-2 gap-6 items-start">
          {/* Matched Skills Column */}
          <div className="card-surface p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <CheckCircle2 size={16} className="text-emerald-500" />
                <span>Matched Skills ({matchedSkills.length})</span>
              </div>
              {matchedSkills.length > 8 && (
                <button
                  type="button"
                  onClick={() => setShowAllMatched((v) => !v)}
                  className="text-xs text-accent hover:underline font-medium"
                >
                  {showAllMatched ? 'Show less' : 'View all'}
                </button>
              )}
            </div>

            <div className="space-y-2.5">
              {displayedMatched.map((skill) => (
                <div
                  key={skill}
                  className="p-3 rounded-xl bg-surface-muted/50 border border-border flex items-center justify-between text-xs"
                >
                  <div className="flex items-center gap-2.5 font-medium text-text-primary">
                    <CheckCircle2 size={15} className="text-emerald-500 flex-shrink-0" />
                    <span>{skill}</span>
                  </div>
                  <span className="badge-matched">
                    Proficient
                  </span>
                </div>
              ))}
            </div>
          </div>

          {/* Missing Skills Column */}
          <div className="card-surface p-6 space-y-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2 text-sm font-semibold text-text-primary">
                <AlertTriangle size={16} className="text-amber-500" />
                <span>Missing Skills ({missingSkills.length})</span>
              </div>
              <span className="text-xs text-text-secondary">
                Targeted gaps
              </span>
            </div>

            <div className="space-y-2.5">
              {missingSkills.map((skill, idx) => {
                const priorityClass =
                  idx < highPriorityCount
                    ? 'badge-priority-high'
                    : idx < highPriorityCount + medPriorityCount
                    ? 'badge-priority-med'
                    : 'badge-priority-low';

                const priorityLabel =
                  idx < highPriorityCount ? 'High' : idx < highPriorityCount + medPriorityCount ? 'Medium' : 'Low';

                return (
                  <div
                    key={skill}
                    className="p-3.5 rounded-xl bg-surface border border-border hover:border-accent/40 transition-colors shadow-sm flex flex-col gap-2.5"
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-semibold text-text-primary">
                        {skill}
                      </span>
                      <span className={priorityClass}>
                        {priorityLabel}
                      </span>
                    </div>

                    <div className="flex items-center justify-between text-xs pt-1 border-t border-border/60">
                      <button
                        type="button"
                        onClick={() => setSelectedDrawerSkill(skill)}
                        className="text-accent hover:underline font-medium flex items-center gap-1"
                      >
                        <HelpCircle size={12} />
                        <span>Why this skill?</span>
                      </button>

                      <button
                        type="button"
                        onClick={() => handleAddSkillToRoadmap(skill)}
                        className="btn-outline text-[11px] px-2.5 py-1 flex items-center gap-1"
                      >
                        <Plus size={12} />
                        <span>Add to roadmap</span>
                      </button>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>

        {/* ── Continue Action to Step 6 ── */}
        <div className="pt-4 flex items-center justify-between border-t border-border">
          <Link
            to="/onboarding/target"
            className="btn-outline text-xs px-4 py-2"
          >
            Back
          </Link>

          <button
            type="button"
            onClick={() => navigate('/dashboard')}
            className="btn-accent px-6 py-2.5 flex items-center gap-2 text-sm font-semibold shadow-sm"
          >
            <span>View Learning Roadmap</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </WorkflowLayout>
  );
}
