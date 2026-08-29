import { useState } from 'react';
import { Link } from 'react-router-dom';
import { LayoutDashboard, Compass, CheckCircle2, AlertCircle } from 'lucide-react';
import Navbar from '../components/Navbar';
import MatchScoreRing from '../components/MatchScoreRing';
import RoadmapTrail from '../components/RoadmapTrail';
import { useAppContext, ACTIONS } from '../context/AppContext';
import { updateTaskProgress } from '../api/roadmap';

export default function DashboardPage() {
  const { state, dispatch } = useAppContext();
  const [updatingTask, setUpdatingTask] = useState(null);
  const [updateError, setUpdateError] = useState(null);

  const hasRoadmap = state.learningModules && state.learningModules.length > 0;

  // Calculate overall stats
  let totalTasks = 0;
  let completedTasks = 0;
  if (hasRoadmap) {
    state.learningModules.forEach(m => {
      totalTasks += m.tasks.length;
      completedTasks += m.tasks.filter(t => t.is_completed).length;
    });
  }
  const overallProgress = totalTasks ? Math.round((completedTasks / totalTasks) * 100) : 0;

  const handleTaskToggle = async (taskId, isCompleted) => {
    if (updatingTask) return; // Prevent concurrent toggles on same/different tasks for simplicity
    
    setUpdatingTask(taskId);
    setUpdateError(null);

    try {
      await updateTaskProgress({ taskId, isCompleted });
      dispatch({ 
        type: ACTIONS.UPDATE_TASK, 
        payload: { task_id: taskId, is_completed: isCompleted } 
      });
    } catch (err) {
      console.error('Failed to update task:', err);
      setUpdateError('Failed to save progress. Please try again.');
    } finally {
      setUpdatingTask(null);
    }
  };

  return (
    <div className="page-container">
      <Navbar />
      
      <div className="max-w-6xl mx-auto px-5 sm:px-8 py-8 sm:py-12">
        <div className="flex items-center gap-2 mb-8">
          <LayoutDashboard className="text-slate" size={24} />
          <h1 className="font-heading font-bold text-2xl sm:text-3xl text-offwhite">My Dashboard</h1>
        </div>

        {!hasRoadmap ? (
          // Empty State
          <div className="card border border-white/5 flex flex-col items-center justify-center py-20 text-center fade-up">
            <div className="w-16 h-16 rounded-full bg-signal/10 border border-signal/20 flex items-center justify-center mb-6">
              <Compass size={32} className="text-signal" />
            </div>
            <h2 className="font-heading font-bold text-2xl text-offwhite mb-3">No active roadmap</h2>
            <p className="text-slate mb-8 max-w-sm leading-relaxed">
              You haven't generated a learning path yet. Set your skills and target role to get started.
            </p>
            <Link to="/onboarding/skills" className="btn-primary px-8 py-3.5 text-base">
              Create My Roadmap
            </Link>
          </div>
        ) : (
          // Dashboard Content
          <div className="grid lg:grid-cols-4 gap-8">
            
            {/* Left Col: Trail */}
            <div className="lg:col-span-3 fade-up">
              {updateError && (
                <div className="mb-6 p-4 rounded-lg bg-red-500/10 border border-red-500/20 flex items-start gap-3">
                  <AlertCircle size={18} className="text-red-400 mt-0.5 flex-shrink-0" />
                  <p className="text-sm text-red-200">{updateError}</p>
                </div>
              )}
              
              <div className="bg-navy-light/50 border border-white/5 rounded-2xl p-6 sm:p-8">
                <RoadmapTrail 
                  modules={state.learningModules} 
                  interactive={true} 
                  onTaskToggle={handleTaskToggle}
                />
              </div>
            </div>

            {/* Right Col: Stats */}
            <div className="space-y-6 fade-up" style={{ animationDelay: '100ms' }}>
              
              <div className="card border border-white/5 flex flex-col items-center text-center">
                <p className="text-xs font-semibold text-slate uppercase tracking-wider mb-6">Current Match Score</p>
                <MatchScoreRing score={state.matchScore} size={140} />
                <p className="text-xs text-slate mt-6 leading-relaxed">
                  Completing tasks will gradually increase your match score towards your target role.
                </p>
              </div>

              <div className="stat-card">
                <p className="text-xs font-semibold text-slate uppercase tracking-wider mb-2">Overall Progress</p>
                <div className="flex items-end justify-between mb-2">
                  <span className="font-heading font-bold text-3xl text-offwhite">{overallProgress}%</span>
                  <span className="text-sm text-slate mb-1">{completedTasks} / {totalTasks} tasks</span>
                </div>
                <div className="w-full h-2 bg-navy rounded-full overflow-hidden">
                  <div 
                    className="h-full bg-signal rounded-full transition-all duration-500" 
                    style={{ width: `${overallProgress}%` }}
                  />
                </div>
              </div>

              {overallProgress === 100 && (
                <div className="p-5 rounded-xl bg-green/10 border border-green/20 text-center animate-pulse">
                  <CheckCircle2 size={24} className="text-green mx-auto mb-2" />
                  <p className="font-heading font-bold text-green mb-1">Goal Achieved!</p>
                  <p className="text-xs text-green/80">You've completed all tasks.</p>
                </div>
              )}
              
            </div>

          </div>
        )}
      </div>
    </div>
  );
}
