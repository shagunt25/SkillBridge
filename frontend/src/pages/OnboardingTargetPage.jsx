import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, ArrowRight, Briefcase, FileText } from 'lucide-react';
import WorkflowLayout from '../components/WorkflowLayout';
import { useAppContext, ACTIONS } from '../context/AppContext';

const ROLE_SUGGESTIONS = [
  'Backend AI/ML Engineer',
  'Full-Stack Developer',
  'Data Engineer',
  'DevOps Engineer',
  'Platform Engineer',
  'Frontend Engineer',
];

export default function OnboardingTargetPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();

  const [mode, setMode] = useState(state.targetType || 'role');
  const [role, setRole] = useState(
    state.targetValue && state.targetType === 'role'
      ? state.targetValue
      : 'Backend AI/ML Engineer'
  );
  const [jd, setJd] = useState(
    state.targetValue && state.targetType === 'jd' ? state.targetValue : ''
  );

  const targetValue = mode === 'role' ? role : jd;
  const canAnalyze =
    mode === 'role' ? role.trim().length >= 2 : jd.trim().length >= 10;

  const handleAnalyze = () => {
    if (!canAnalyze) return;

    dispatch({
      type: ACTIONS.SET_TARGET,
      payload: {
        targetType: mode,
        targetValue: targetValue.trim(),
      },
    });

    navigate('/roadmap/generating');
  };

  return (
    <WorkflowLayout currentStep={3} pageTitle="Target role">
      <div className="max-w-2xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-left space-y-1.5">
          <p className="text-xs font-semibold uppercase tracking-wider text-accent">
            Step 2 of 4
          </p>
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            What role are you aiming for?
          </h1>
          <p className="text-sm text-text-secondary">
            Specify a target position or paste a job description so we can compare your skills accurately.
          </p>
        </div>

        {/* ── Mode Toggle Tabs ── */}
        <div className="flex bg-surface-muted p-1 rounded-xl border border-border max-w-sm">
          <button
            type="button"
            onClick={() => setMode('role')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
              mode === 'role'
                ? 'bg-surface text-text-primary shadow-sm font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <Briefcase size={14} />
            <span>Role Title</span>
          </button>
          <button
            type="button"
            onClick={() => setMode('jd')}
            className={`flex-1 flex items-center justify-center gap-2 py-2 px-3 rounded-lg text-xs font-medium transition-all ${
              mode === 'jd'
                ? 'bg-surface text-text-primary shadow-sm font-semibold'
                : 'text-text-secondary hover:text-text-primary'
            }`}
          >
            <FileText size={14} />
            <span>Job Description</span>
          </button>
        </div>

        {/* ── Input Fields ── */}
        {mode === 'role' ? (
          <div className="space-y-4">
            <div>
              <label className="block text-xs font-medium text-text-secondary mb-1.5">
                Target Role Title
              </label>
              <input
                type="text"
                value={role}
                onChange={(e) => setRole(e.target.value)}
                placeholder="e.g. Backend AI/ML Engineer"
                className="input-field"
              />
            </div>

            {/* Suggestions */}
            <div>
              <p className="text-xs font-medium text-text-secondary mb-2">
                Popular suggestions:
              </p>
              <div className="flex flex-wrap gap-2">
                {ROLE_SUGGESTIONS.map((suggestion) => (
                  <button
                    key={suggestion}
                    type="button"
                    onClick={() => setRole(suggestion)}
                    className={`px-3 py-1.5 rounded-xl text-xs font-medium border transition-colors ${
                      role === suggestion
                        ? 'bg-accent/15 border-accent text-accent font-semibold'
                        : 'bg-surface border-border text-text-secondary hover:border-accent/50 hover:text-text-primary'
                    }`}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          </div>
        ) : (
          <div>
            <label className="block text-xs font-medium text-text-secondary mb-1.5">
              Paste the Job Description
            </label>
            <textarea
              rows={6}
              value={jd}
              onChange={(e) => setJd(e.target.value)}
              placeholder="Paste responsibilities, qualifications, and requirements…"
              className="input-field resize-none leading-relaxed"
            />
            <p className="text-[11px] text-text-secondary mt-1">
              Minimum 10 characters required for skill extraction.
            </p>
          </div>
        )}

        {/* ── Action Button ── */}
        <div className="pt-6 border-t border-border flex items-center justify-between">
          <button
            type="button"
            onClick={() => navigate('/onboarding/skills')}
            className="btn-outline text-xs px-4 py-2"
          >
            Back
          </button>

          <button
            type="button"
            onClick={handleAnalyze}
            disabled={!canAnalyze}
            className="btn-accent px-6 py-2.5 flex items-center gap-2 text-sm font-semibold"
          >
            <Sparkles size={15} />
            <span>Analyze Skill Gaps</span>
            <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </WorkflowLayout>
  );
}
