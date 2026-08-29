import { useState } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import { Sparkles, Save, ArrowLeft, Send } from 'lucide-react';
import Navbar from '../components/Navbar';
import MatchScoreRing from '../components/MatchScoreRing';
import RoadmapTrail from '../components/RoadmapTrail';
import { useAppContext, ACTIONS } from '../context/AppContext';
import { refineRoadmap } from '../api/roadmap';

export default function RoadmapReviewPage() {
  const navigate = useNavigate();
  const { state, dispatch } = useAppContext();
  const [prompt, setPrompt] = useState('');

  // If no roadmap data, send them back
  if (!state.matchScore || !state.learningModules?.length) {
    return (
      <div className="page-container flex flex-col items-center justify-center min-h-screen px-5 text-center">
        <h1 className="font-heading font-bold text-2xl text-offwhite mb-3">No Roadmap Found</h1>
        <p className="text-slate mb-6">Let's build one for you.</p>
        <Link to="/onboarding/skills" className="btn-primary px-6 py-2">Start Here</Link>
      </div>
    );
  }

  const handleRefine = async (e) => {
    e.preventDefault();
    if (!prompt.trim() || state.isRefining) return;

    dispatch({ type: ACTIONS.REFINE_START });
    try {
      const result = await refineRoadmap({
        currentRoadmap: {
          match_score: state.matchScore,
          missing_skills: state.missingSkills,
          learning_modules: state.learningModules,
        },
        prompt: prompt.trim()
      });
      dispatch({ type: ACTIONS.REFINE_SUCCESS, payload: result });
      setPrompt('');
    } catch (err) {
      console.error(err);
      dispatch({ type: ACTIONS.REFINE_ERROR, payload: 'Failed to refine roadmap.' });
    }
  };

  return (
    <div className="page-container">
      <Navbar />
      
      {/* Header Area */}
      <div className="bg-navy border-b border-white/5 py-8 px-5 sm:px-8">
        <div className="max-w-6xl mx-auto flex flex-col md:flex-row items-center gap-8">
          
          <div className="flex-1">
            <Link to="/onboarding/target" className="inline-flex items-center gap-1.5 text-sm text-slate hover:text-offwhite transition-colors mb-4">
              <ArrowLeft size={14} /> Back to setup
            </Link>
            <h1 className="font-heading font-bold text-3xl text-offwhite mb-2">Your Personalised Roadmap</h1>
            <p className="text-slate text-sm max-w-xl leading-relaxed">
              Based on your target of <strong className="text-offwhite">"{state.targetValue}"</strong>. 
              Here is your match score and the path to close your skill gaps.
            </p>
          </div>

          <div className="flex items-center gap-6 p-4 rounded-xl border border-white/5 bg-[#1A2642]/50">
            <MatchScoreRing score={state.matchScore} size={90} />
            <div className="max-w-[200px]">
              <p className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Missing Skills</p>
              <div className="flex flex-wrap gap-1.5">
                {state.missingSkills.map(s => (
                  <span key={s} className="text-[10px] bg-red-500/10 text-red-300 px-2 py-0.5 rounded-full border border-red-500/20">
                    {s}
                  </span>
                ))}
              </div>
            </div>
          </div>
          
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-5 sm:px-8 py-10 grid lg:grid-cols-3 gap-8">
        
        {/* Left Col: Trail */}
        <div className="lg:col-span-2">
          <div className="flex items-center justify-between mb-6">
            <p className="section-label">Learning Modules</p>
            <span className="text-xs text-slate">{state.learningModules.length} steps</span>
          </div>
          <div className={`transition-opacity duration-300 ${state.isRefining ? 'opacity-40 pointer-events-none' : 'opacity-100'}`}>
            <RoadmapTrail modules={state.learningModules} interactive={false} />
          </div>
        </div>

        {/* Right Col: Refine & Save */}
        <div className="space-y-6">
          <div className="card border border-white/5 sticky top-24">
            <h3 className="font-heading font-bold text-lg text-offwhite mb-2 flex items-center gap-2">
              <Sparkles size={18} className="text-signal" /> Refine with AI
            </h3>
            <p className="text-sm text-slate mb-4 leading-relaxed">
              Want changes? Ask the AI to adjust difficulty, shorten the path, or focus on specific tools.
            </p>
            
            <form onSubmit={handleRefine} className="mb-6">
              <div className="relative">
                <input
                  value={prompt}
                  onChange={e => setPrompt(e.target.value)}
                  placeholder="e.g. 'Make it shorter' or 'Add AWS'"
                  className="input-field pr-10 text-sm"
                  disabled={state.isRefining}
                />
                <button
                  type="submit"
                  disabled={state.isRefining || !prompt.trim()}
                  className="absolute right-2 top-1/2 -translate-y-1/2 text-signal hover:text-white transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {state.isRefining ? <div className="w-4 h-4 border-2 border-signal border-t-transparent rounded-full animate-spin" /> : <Send size={16} />}
                </button>
              </div>
              {state.error && <p className="text-xs text-red-400 mt-2">{state.error}</p>}
            </form>

            <div className="h-px bg-white/5 w-full mb-6" />

            <button
              onClick={() => navigate('/dashboard')}
              className="btn-primary w-full py-3.5 text-sm flex items-center justify-center gap-2"
            >
              <Save size={16} /> Save & Go to Dashboard
            </button>
          </div>
        </div>

      </div>
    </div>
  );
}
