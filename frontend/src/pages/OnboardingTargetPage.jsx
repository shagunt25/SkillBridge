import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Briefcase, FileText, Sparkles, CheckCircle2 } from 'lucide-react';
import Navbar from '../components/Navbar';
import { useAppContext, ACTIONS } from '../context/AppContext';

const ROLE_EXAMPLES = ['Backend Engineer', 'Data Engineer', 'Frontend Developer', 'ML Engineer', 'DevOps Engineer'];

export default function OnboardingTargetPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  
  const [mode, setMode] = useState('role');   // 'role' | 'jd'
  const [role, setRole] = useState('');
  const [jd, setJd] = useState('');

  const hasProfileInput = state.currentSkills.length > 0 || state.resumeFile instanceof File;
  const hasValidTarget = mode === 'role' ? role.trim().length > 2 : jd.trim().length > 30;
  const canGenerate = hasProfileInput && hasValidTarget;

  const handleGenerate = () => {
    if (!canGenerate) return;
    
    dispatch({
      type: ACTIONS.SET_TARGET,
      payload: {
        targetType: mode,
        targetValue: mode === 'role' ? role : jd
      }
    });
    
    navigate('/roadmap/generating');
  };

  return (
    <div className="page-container">
      <Navbar />
      <div className="max-w-2xl mx-auto px-5 sm:px-8 py-12">
        {/* Step indicator */}
        <div className="flex items-center gap-3 mb-10">
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-green text-navy text-xs font-heading font-bold flex items-center justify-center">
              <CheckCircle2 size={14} />
            </div>
            <span className="text-sm text-slate">Your Skills</span>
          </div>
          <div className="flex-1 h-px bg-white/10" />
          <div className="flex items-center gap-2">
            <div className="w-7 h-7 rounded-full bg-signal text-white text-xs font-heading font-bold flex items-center justify-center">2</div>
            <span className="text-sm font-medium text-offwhite">Your Target</span>
          </div>
        </div>

        <h1 className="font-heading font-bold text-3xl text-offwhite mb-2">What's your career goal?</h1>
        <p className="text-slate mb-8">Tell us your target role or paste a job description to tailor your roadmap.</p>

        {/* Mode toggle */}
        <div className="flex gap-1 p-1 bg-navy-light rounded-xl mb-8 border border-white/5">
          <button
            id="target-role-tab"
            onClick={() => setMode('role')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
              mode === 'role'
                ? 'bg-signal text-white shadow-soft'
                : 'text-slate hover:text-offwhite'
            }`}
          >
            <Briefcase size={15} /> Target Role
          </button>
          <button
            id="target-jd-tab"
            onClick={() => setMode('jd')}
            className={`flex-1 flex items-center justify-center gap-2 py-2.5 rounded-lg text-sm font-medium transition-all ${
              mode === 'jd'
                ? 'bg-signal text-white shadow-soft'
                : 'text-slate hover:text-offwhite'
            }`}
          >
            <FileText size={15} /> Job Description
          </button>
        </div>

        {/* Role input */}
        {mode === 'role' && (
          <div className="fade-up">
            <label className="block text-sm font-medium text-offwhite mb-1.5" htmlFor="target-role-input">
              Role or career goal
            </label>
            <input
              id="target-role-input"
              value={role}
              onChange={e => setRole(e.target.value)}
              placeholder="e.g. Backend Engineer, Data Engineer…"
              className="input-field text-base mb-4"
            />
            <div className="flex flex-wrap gap-2">
              <p className="w-full text-xs text-slate mb-1">Popular goals:</p>
              {ROLE_EXAMPLES.map(r => (
                <button
                  key={r}
                  onClick={() => setRole(r)}
                  className={`tag transition-colors ${
                    role === r ? 'tag-signal' : 'hover:border-signal hover:text-signal'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        )}

        {/* JD input */}
        {mode === 'jd' && (
          <div className="fade-up">
            <label className="block text-sm font-medium text-offwhite mb-1.5" htmlFor="target-jd-input">
              Paste the job description
            </label>
            <textarea
              id="target-jd-input"
              value={jd}
              onChange={e => setJd(e.target.value)}
              placeholder="Paste the full job description here. The more detail, the better the roadmap…"
              rows={9}
              className="input-field resize-none font-body text-sm leading-relaxed"
            />
            <p className="text-xs text-slate mt-1.5">{jd.length} characters · Minimum 30</p>
          </div>
        )}

        {/* Generate CTA */}
        <button
          onClick={handleGenerate}
          disabled={!canGenerate}
          className={`btn-primary w-full py-4 text-base mt-8 flex items-center justify-center gap-2 ${
            !canGenerate ? 'opacity-40 cursor-not-allowed' : ''
          }`}
        >
          <Sparkles size={17} />
          Generate My Roadmap
        </button>
        {!canGenerate && (
          <p className="text-center text-xs text-slate mt-2">
            {!hasProfileInput
              ? 'Add your skills or upload your resume before generating a roadmap'
              : mode === 'role' ? 'Enter a role name to continue' : 'Paste at least 30 characters to continue'}
          </p>
        )}
      </div>
    </div>
  );
}
