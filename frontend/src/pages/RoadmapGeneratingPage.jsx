import { useState, useEffect, useCallback, useRef } from 'react';
import { Link } from 'react-router-dom';
import { Zap, AlertCircle, RefreshCw } from 'lucide-react';
import { useAppContext, ACTIONS } from '../context/AppContext';
import { generateRoadmap } from '../api/roadmap';

const MESSAGES = [
  'Analysing your current skills…',
  'Mapping skill gaps to your target role…',
  'Selecting the best learning modules…',
  'Estimating your match score…',
  'Structuring your personalised roadmap…',
  'Almost there — finalising tasks…',
];

function SkeletonLine({ w = 'w-full' }) {
  return <div className={`skeleton h-3 rounded ${w}`} />;
}

function SkeletonModuleCard({ delay = 0 }) {
  return (
    <div className="card border border-white/5" style={{ animationDelay: `${delay}ms` }}>
      {/* Module header */}
      <div className="flex items-center gap-3 mb-4">
        <div className="skeleton w-10 h-10 rounded-full flex-shrink-0" />
        <div className="flex-1 space-y-2">
          <SkeletonLine w="w-1/2" />
          <SkeletonLine w="w-1/4" />
        </div>
      </div>
      {/* Task lines */}
      <div className="space-y-3">
        <SkeletonLine />
        <SkeletonLine w="w-5/6" />
        <SkeletonLine w="w-4/6" />
        <SkeletonLine w="w-5/6" />
      </div>
    </div>
  );
}

export default function RoadmapGeneratingPage() {
  const { state, dispatch } = useAppContext();
  const [msgIdx, setMsgIdx] = useState(0);
  const [progress, setProgress] = useState(0);
  const requestRef = useRef(null);
  const timersRef = useRef([]);
  const inputRef = useRef(null);

  useEffect(() => {
    inputRef.current = {
      currentSkills: state.currentSkills,
      targetType: state.targetType,
      targetValue: state.targetValue,
      hasResume: state.resumeFile instanceof File,
    };
  }, [state.currentSkills, state.targetType, state.targetValue, state.resumeFile]);

  const clearTimers = useCallback(() => {
    timersRef.current.forEach(clearTimeout);
    timersRef.current = [];
  }, []);

  const runGeneration = useCallback(async () => {
    if (requestRef.current) return;
    const input = inputRef.current;
    if (!input?.targetValue || (!input.currentSkills.length && !input.hasResume)) {
      dispatch({ type: ACTIONS.GENERATE_ERROR, payload: 'Add your skills or resume and a target before generating a roadmap.' });
      return;
    }

    clearTimers();
    setMsgIdx(0);
    setProgress(0);
    dispatch({ type: ACTIONS.GENERATE_START });

    const controller = new AbortController();
    requestRef.current = controller;
    const messageTimer = setInterval(() => setMsgIdx(prev => Math.min(prev + 1, MESSAGES.length - 1)), 1100);
    const progressTimer = setInterval(() => setProgress(prev => Math.min(prev + Math.random() * 8 + 3, 95)), 350);
    timersRef.current.push(messageTimer, progressTimer);

    try {
      const result = await generateRoadmap({
        currentSkills: input.currentSkills,
        targetType: input.targetType,
        targetValue: input.targetValue,
        resume: state.resumeFile instanceof File ? state.resumeFile : null,
      }, { signal: controller.signal });

      if (!controller.signal.aborted) {
        clearTimers();
        setProgress(100);
        const completionTimer = setTimeout(() => {
          dispatch({ type: ACTIONS.GENERATE_SUCCESS, payload: result });
        }, 400);
        timersRef.current.push(completionTimer);
      }
    } catch (err) {
      if (!controller.signal.aborted) {
        clearTimers();
        dispatch({ type: ACTIONS.GENERATE_ERROR, payload: err.message || 'Unable to generate your roadmap. Please retry.' });
      }
    } finally {
      if (requestRef.current === controller) requestRef.current = null;
    }
  }, [clearTimers, dispatch, state.resumeFile]);

  useEffect(() => {
    // Deferring one tick prevents React Strict Mode's development-only effect replay
    // from sending two generation requests.
    const startTimer = setTimeout(runGeneration, 0);
    return () => {
      clearTimeout(startTimer);
      requestRef.current?.abort();
      requestRef.current = null;
      clearTimers();
    };
  }, [clearTimers, runGeneration]);

  if (state.error) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-screen px-5 text-center">
        <div className="w-16 h-16 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mb-6">
          <AlertCircle size={32} className="text-red-400" />
        </div>
        <h1 className="font-heading font-bold text-3xl text-offwhite mb-3">Oops, something went wrong</h1>
        <p className="text-slate mb-8 max-w-sm">{state.error}</p>
        <div className="flex gap-4">
          <Link to="/onboarding/target" className="btn-secondary text-base px-6 py-3">
            Go Back
          </Link>
          <button onClick={runGeneration} className="btn-primary text-base px-6 py-3 flex items-center gap-2">
            <RefreshCw size={16} /> Retry
          </button>
        </div>
      </div>
    );
  }

  if (state.matchScore !== null && !state.isGenerating && progress >= 100) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-screen px-5 text-center">
        <div className="w-20 h-20 rounded-full bg-green/10 border border-green/30 flex items-center justify-center mb-6 fade-up pulse-glow">
          <Zap size={32} className="text-green" fill="currentColor" />
        </div>
        <h1 className="font-heading font-bold text-3xl text-offwhite mb-3 fade-up">Your roadmap is ready!</h1>
        <p className="text-slate mb-8 max-w-sm fade-up">We've built a personalised learning path tailored to your skills and target role.</p>
        <Link to="/roadmap/review" className="btn-primary text-base px-8 py-3.5 fade-up">
          View My Roadmap →
        </Link>
      </div>
    );
  }

  return (
    <div className="page-container min-h-screen px-5 sm:px-8 py-12">
      <div className="max-w-2xl mx-auto">
        {/* Logo */}
        <div className="flex items-center gap-2 font-heading font-bold text-lg mb-16">
          <div className="w-8 h-8 rounded-lg bg-signal flex items-center justify-center pulse-glow">
            <Zap size={15} className="text-white" fill="white" />
          </div>
          <span className="text-offwhite">Skill<span className="text-signal">Bridge</span><span className="text-amber ml-0.5">AI</span></span>
        </div>

        {/* Status */}
        <div className="mb-10">
          <h1 className="font-heading font-bold text-2xl text-offwhite mb-2">
            Building your roadmap…
          </h1>
          {/* Cycling message */}
          <p key={msgIdx} className="text-slate text-sm fade-up">{MESSAGES[msgIdx]}</p>

          {/* Progress bar */}
          <div className="mt-5 w-full h-1.5 bg-navy-light rounded-full overflow-hidden">
            <div
              className="h-full bg-signal rounded-full transition-all duration-300"
              style={{ width: `${progress}%` }}
            />
          </div>
          <div className="flex justify-between mt-1.5">
            <span className="text-[11px] text-slate">Analysing…</span>
            <span className="text-[11px] text-signal font-heading font-semibold">{Math.round(progress)}%</span>
          </div>
        </div>

        {/* Skeleton trail preview */}
        <div className="mb-8">
          <p className="section-label mb-4">Your learning trail</p>
          <div className="flex items-center mb-8 overflow-hidden">
            {[0, 1, 2, 3].map((_, i) => (
              <div key={i} className="flex items-center flex-1 min-w-0">
                <div className="skeleton w-11 h-11 rounded-full flex-shrink-0" style={{ animationDelay: `${i * 120}ms` }} />
                {i < 3 && <div className="skeleton flex-1 h-0.5 mx-2" style={{ animationDelay: `${i * 120 + 60}ms` }} />}
              </div>
            ))}
          </div>
        </div>

        {/* Skeleton module cards */}
        <div className="space-y-4">
          <SkeletonModuleCard delay={0} />
          <SkeletonModuleCard delay={150} />
          <SkeletonModuleCard delay={300} />
        </div>

        {/* Tip */}
        <p className="text-center text-xs text-slate mt-10 leading-relaxed">
          💡 Tip: Once your roadmap loads, you can ask AI to shorten it,
          add specific topics, or adjust the difficulty.
        </p>
      </div>
    </div>
  );
}
