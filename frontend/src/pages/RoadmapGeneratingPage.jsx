import { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { Zap, AlertCircle, RefreshCw, CheckCircle2, Sparkles, Sliders } from 'lucide-react';
import WorkflowLayout from '../components/WorkflowLayout';
import { useAppContext, ACTIONS } from '../context/AppContext';
import { generateRoadmap } from '../api/roadmap';
import { MOCK_ROADMAP } from '../data/mockData';

const MESSAGES = [
  'Reading your selected career goal…',
  'Comparing your current skills…',
  'Identifying important skill gaps…',
  'Building your personalized roadmap…',
];

export default function RoadmapGeneratingPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();

  const [msgIdx, setMsgIdx] = useState(0);
  const [progress, setProgress] = useState(20);
  const [error, setError] = useState(null);
  const [isRetrying, setIsRetrying] = useState(false);
  const hasTriggered = useRef(false);

  const startAnalysis = async () => {
    setError(null);
    setProgress(20);
    dispatch({ type: ACTIONS.GENERATE_START });

    const msgInterval = setInterval(() => {
      setMsgIdx((prev) => (prev + 1) % MESSAGES.length);
    }, 1800);

    const progressInterval = setInterval(() => {
      setProgress((prev) => {
        if (prev >= 88) return prev;
        return prev + Math.floor(Math.random() * 8 + 4);
      });
    }, 400);

    const controller = new AbortController();

    try {
      const skillsToUse =
        state.currentSkills && state.currentSkills.length > 0
          ? state.currentSkills
          : ['Python', 'Git', 'REST APIs', 'Pandas', 'PostgreSQL', 'Linux', 'Data Analysis'];

      const targetValue = state.targetValue || 'Backend AI/ML Engineer';

      const result = await generateRoadmap(
        {
          currentSkills: skillsToUse,
          targetType: state.targetType || 'role',
          targetValue: targetValue,
          resume: state.resumeFile instanceof File ? state.resumeFile : null,
        },
        { signal: controller.signal }
      );

      clearInterval(msgInterval);
      clearInterval(progressInterval);
      setProgress(100);

      dispatch({ type: ACTIONS.GENERATE_SUCCESS, payload: result });
      setTimeout(() => {
        navigate('/roadmap/review');
      }, 500);
    } catch (err) {
      clearInterval(msgInterval);
      clearInterval(progressInterval);
      dispatch({ type: ACTIONS.GENERATE_ERROR, payload: err.message });
      setError(err.message || 'Unable to connect to the roadmap service.');
    } finally {
      setIsRetrying(false);
    }
  };

  useEffect(() => {
    if (hasTriggered.current) return;
    hasTriggered.current = true;
    startAnalysis();
  }, []);

  const handleRetry = () => {
    setIsRetrying(true);
    startAnalysis();
  };

  const handleUseSampleRoadmap = () => {
    dispatch({ type: ACTIONS.GENERATE_SUCCESS, payload: MOCK_ROADMAP });
    navigate('/roadmap/review');
  };

  return (
    <WorkflowLayout currentStep={4} pageTitle="Analyzing profile">
      <div className="max-w-xl mx-auto py-12 text-center space-y-8">
        {/* Animated Central Node */}
        <div className="relative w-24 h-24 mx-auto flex items-center justify-center">
          <div className="absolute inset-0 rounded-3xl bg-accent/20 animate-ping opacity-30" />
          <div className="relative w-20 h-20 rounded-3xl bg-teal-800 dark:bg-emerald-500 text-white dark:text-zinc-950 flex items-center justify-center shadow-xl pulse-glow">
            {error ? <AlertCircle size={32} className="text-rose-200" /> : <Sparkles size={32} />}
          </div>
        </div>

        {/* Heading & Rotating Message */}
        <div className="space-y-2">
          <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight">
            {error ? 'Analysis Encountered an Issue' : 'Analyzing your profile…'}
          </h1>
          {!error && (
            <p className="text-sm text-text-secondary h-6 transition-all duration-300">
              {MESSAGES[msgIdx]}
            </p>
          )}
        </div>

        {/* Progress Bar */}
        {!error ? (
          <div className="space-y-3 max-w-md mx-auto">
            <div className="h-2 bg-surface-muted border border-border rounded-full overflow-hidden">
              <div
                className="h-full bg-accent rounded-full transition-all duration-500 ease-out"
                style={{ width: `${progress}%` }}
              />
            </div>
            <div className="flex justify-between items-center text-xs text-text-secondary px-1">
              <span>Comparing skill requirements</span>
              <span className="font-semibold text-text-primary">{progress}%</span>
            </div>
          </div>
        ) : (
          /* Error feedback & real retry state */
          <div className="card-surface p-6 text-left space-y-4 border-rose-500/30 bg-rose-500/5">
            <div className="flex items-start gap-3">
              <AlertCircle size={20} className="text-danger flex-shrink-0 mt-0.5" />
              <div>
                <h2 className="text-sm font-semibold text-text-primary">
                  API Request Notice
                </h2>
                <p className="text-xs text-text-secondary mt-1 leading-relaxed">
                  {error}
                </p>
                <p className="text-[11px] text-text-secondary/80 mt-2">
                  Please verify that your backend roadmap server is active at your configured API base URL, or retry the connection.
                </p>
              </div>
            </div>

            <div className="flex flex-wrap gap-3 pt-2">
              <button
                type="button"
                onClick={handleRetry}
                disabled={isRetrying}
                className="btn-accent text-xs px-4 py-2 flex items-center gap-2"
              >
                <RefreshCw size={13} className={isRetrying ? 'animate-spin' : ''} />
                <span>{isRetrying ? 'Retrying…' : 'Retry Request'}</span>
              </button>

              <button
                type="button"
                onClick={handleUseSampleRoadmap}
                className="btn-outline text-xs px-4 py-2 flex items-center gap-2"
              >
                <Sliders size={13} />
                <span>Explore with Sample Roadmap</span>
              </button>
            </div>
          </div>
        )}

        {/* Rotating checklist items */}
        {!error && (
          <div className="card-surface p-5 max-w-md mx-auto text-left space-y-3">
            {MESSAGES.map((msg, i) => {
              const isDone = i < msgIdx;
              const isCurrent = i === msgIdx;
              return (
                <div
                  key={i}
                  className={`flex items-center gap-3 text-xs transition-colors ${
                    isDone
                      ? 'text-emerald-600 dark:text-emerald-400 font-medium'
                      : isCurrent
                      ? 'text-text-primary font-semibold'
                      : 'text-text-secondary/40'
                  }`}
                >
                  <CheckCircle2
                    size={15}
                    className={`flex-shrink-0 ${
                      isDone
                        ? 'text-emerald-500'
                        : isCurrent
                        ? 'text-accent animate-pulse'
                        : 'text-text-secondary/30'
                    }`}
                  />
                  <span>{msg}</span>
                </div>
              );
            })}
          </div>
        )}
      </div>
    </WorkflowLayout>
  );
}
