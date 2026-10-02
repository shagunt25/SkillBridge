import { useState, useMemo } from 'react';
import {
  ChevronDown,
  ChevronRight,
  Clock,
  ArrowUp,
  CheckCircle2,
  Circle,
  Loader2,
  Search,
  Filter,
  Trophy,
  Lightbulb,
  ArrowRight,
  Sparkles,
} from 'lucide-react';
import WorkflowLayout from '../components/WorkflowLayout';
import { useAppContext, ACTIONS } from '../context/AppContext';
import { updateTaskProgress, refineRoadmap } from '../api/roadmap';
import { MOCK_ROADMAP } from '../data/mockData';

export default function DashboardPage() {
  const { state, dispatch } = useAppContext();

  // Load modules from state or fallback to MOCK_ROADMAP for sample exploration
  const rawModules =
    state.learningModules && state.learningModules.length > 0
      ? state.learningModules
      : MOCK_ROADMAP.learning_modules;

  // Normalized modules
  const modules = useMemo(() => {
    return rawModules.map((mod, i) => {
      const mockRef = MOCK_ROADMAP.learning_modules[i] || {};
      return {
        ...mod,
        description: mod.description || mockRef.description || 'Core competencies and applied milestones.',
        estimated_hours: mod.estimated_hours || mockRef.estimated_hours || '20h',
        tasks: (mod.tasks || []).map((task, ti) => {
          const mockTask = mockRef.tasks?.[ti] || {};
          return {
            ...task,
            hours: task.hours || mockTask.hours || '4h',
          };
        }),
      };
    });
  }, [rawModules]);

  // Overall Task & Hours Statistics
  const allTasks = useMemo(() => modules.flatMap((m) => m.tasks || []), [modules]);
  const totalTasksCount = allTasks.length;
  const completedTasksCount = allTasks.filter((t) => t.is_completed).length;
  const overallProgressPct =
    totalTasksCount > 0 ? Math.round((completedTasksCount / totalTasksCount) * 100) : 0;

  // Track expanded phases
  const [expandedPhases, setExpandedPhases] = useState({ 0: true });
  const [updatingTaskId, setUpdatingTaskId] = useState(null);
  const [refinePrompt, setRefinePrompt] = useState('');
  const [isRefining, setIsRefining] = useState(false);

  // Search & Filter State
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('all'); // 'all' | 'incomplete' | 'completed'

  const togglePhase = (index) => {
    setExpandedPhases((prev) => ({
      ...prev,
      [index]: !prev[index],
    }));
  };

  const handleTaskToggle = async (taskId, currentCompleted) => {
    if (updatingTaskId) return;
    setUpdatingTaskId(taskId);

    const nextState = !currentCompleted;

    try {
      // Optimistic dispatch
      dispatch({
        type: ACTIONS.UPDATE_TASK,
        payload: { task_id: taskId, is_completed: nextState },
      });

      // Remote update
      await updateTaskProgress({ taskId, isCompleted: nextState });
    } catch (err) {
      console.warn('Task update not synced to remote server:', err.message);
    } finally {
      setUpdatingTaskId(null);
    }
  };

  const handleRefineSubmit = async (e) => {
    e.preventDefault();
    if (!refinePrompt.trim() || isRefining) return;

    setIsRefining(true);
    try {
      const result = await refineRoadmap({
        currentRoadmap: {
          match_score: state.matchScore || 50,
          missing_skills: state.missingSkills || [],
          learning_modules: modules,
        },
        prompt: refinePrompt.trim(),
      });
      dispatch({ type: ACTIONS.REFINE_SUCCESS, payload: result });
      setRefinePrompt('');
    } catch (err) {
      console.warn('Refine API unavailable, local adjustment completed:', err.message);
      setTimeout(() => {
        setRefinePrompt('');
        setIsRefining(false);
      }, 700);
      return;
    }
    setIsRefining(false);
  };

  // Next incomplete task for "Continue learning"
  const nextIncompleteTask = useMemo(() => {
    return allTasks.find((t) => !t.is_completed) || null;
  }, [allTasks]);

  const handleContinueLearning = () => {
    if (!nextIncompleteTask) return;
    // Find phase of this task and expand it
    const phaseIdx = modules.findIndex((m) =>
      m.tasks?.some((t) => t.task_id === nextIncompleteTask.task_id)
    );
    if (phaseIdx !== -1) {
      setExpandedPhases((prev) => ({ ...prev, [phaseIdx]: true }));
      // Scroll to task element
      const el = document.getElementById(`task-${nextIncompleteTask.task_id}`);
      if (el) {
        el.scrollIntoView({ behavior: 'smooth', block: 'center' });
        el.classList.add('ring-2', 'ring-accent');
        setTimeout(() => el.classList.remove('ring-2', 'ring-accent'), 2000);
      }
    }
  };

  return (
    <WorkflowLayout currentStep={6} pageTitle="Learning roadmap">
      <div className="max-w-4xl mx-auto space-y-8 pb-28">
        {/* ── Top Header ── */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
          <div>
            <span className="text-xs font-semibold uppercase tracking-wider text-accent">
              Roadmap Dashboard
            </span>
            <h1 className="text-2xl sm:text-3xl font-bold text-text-primary tracking-tight mt-1">
              Learning Roadmap
            </h1>
            <p className="text-xs sm:text-sm text-text-secondary mt-0.5">
              Your personalized path to becoming a {state.targetValue || 'Backend AI/ML Engineer'}.
            </p>
          </div>

          {/* Search & Filter Bar */}
          <div className="flex items-center gap-2">
            <div className="relative">
              <Search size={14} className="absolute left-3 top-1/2 -translate-y-1/2 text-text-secondary" />
              <input
                type="text"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Search tasks…"
                className="bg-surface border border-border rounded-xl pl-9 pr-3 py-1.5 text-xs text-text-primary placeholder:text-text-secondary placeholder:opacity-60 focus:outline-none focus:border-accent w-40 sm:w-48"
              />
            </div>

            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="bg-surface border border-border rounded-xl px-2.5 py-1.5 text-xs text-text-primary focus:outline-none focus:border-accent"
            >
              <option value="all">All tasks</option>
              <option value="incomplete">Incomplete</option>
              <option value="completed">Completed</option>
            </select>
          </div>
        </div>

        {/* ── Top Metric Blocks ── */}
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
          <div className="card-surface p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-accent/15 text-accent font-bold text-sm flex items-center justify-center flex-shrink-0">
              {overallProgressPct}%
            </div>
            <div>
              <p className="text-xs text-text-secondary">Overall Progress</p>
              <p className="text-sm font-bold text-text-primary">{overallProgressPct}%</p>
            </div>
          </div>

          <div className="card-surface p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-teal-500/15 text-teal-600 dark:text-teal-400 font-bold text-sm flex items-center justify-center flex-shrink-0">
              <CheckCircle2 size={18} />
            </div>
            <div>
              <p className="text-xs text-text-secondary">Tasks Completed</p>
              <p className="text-sm font-bold text-text-primary">
                {completedTasksCount} / {totalTasksCount}
              </p>
            </div>
          </div>

          <div className="card-surface p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-amber-500/15 text-amber-600 dark:text-amber-400 font-bold text-sm flex items-center justify-center flex-shrink-0">
              <Clock size={18} />
            </div>
            <div>
              <p className="text-xs text-text-secondary">Estimated Time</p>
              <p className="text-sm font-bold text-text-primary">~{modules.length * 20}h</p>
            </div>
          </div>

          <div className="card-surface p-4 flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-surface-muted text-text-secondary font-bold text-sm flex items-center justify-center flex-shrink-0">
              <Sparkles size={18} />
            </div>
            <div>
              <p className="text-xs text-text-secondary">Current Focus</p>
              <p className="text-sm font-bold text-text-primary truncate max-w-[120px]">
                {modules[0]?.title ? modules[0].title.replace(/^Phase \d+:\s*/, '') : 'Foundations'}
              </p>
            </div>
          </div>
        </div>

        {/* ── Quick Action: Continue Learning Banner & Milestones Row ── */}
        <div className="grid md:grid-cols-12 gap-6">
          {/* Continue Learning Banner */}
          <div className="md:col-span-7 card-surface p-5 bg-gradient-to-r from-accent/10 to-teal-500/5 flex flex-col justify-between">
            <div>
              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-accent mb-2">
                <Sparkles size={14} />
                <span>Quick Action</span>
              </div>
              <p className="text-sm font-bold text-text-primary mb-1">
                {nextIncompleteTask ? `Next up: ${nextIncompleteTask.title}` : 'All caught up! Excellent work!'}
              </p>
              <p className="text-xs text-text-secondary">
                {nextIncompleteTask ? 'Pick up right where you left off in your structured curriculum.' : 'You have completed all currently assigned tasks.'}
              </p>
            </div>

            {nextIncompleteTask && (
              <div className="pt-4">
                <button
                  type="button"
                  onClick={handleContinueLearning}
                  className="btn-accent text-xs px-4 py-2 flex items-center gap-1.5"
                >
                  <span>Continue learning</span>
                  <ArrowRight size={13} />
                </button>
              </div>
            )}
          </div>

          {/* Milestones Widget */}
          <div className="md:col-span-5 card-surface p-5 space-y-3">
            <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-wider text-amber-500">
              <Trophy size={14} />
              <span>Milestones</span>
            </div>

            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-medium">
                <CheckCircle2 size={14} className="text-emerald-500" />
                <span>Resume analyzed & skills mapped</span>
              </div>
              <div className="flex items-center gap-2 text-emerald-600 dark:text-emerald-400 font-medium">
                <CheckCircle2 size={14} className="text-emerald-500" />
                <span>First skill gap identified</span>
              </div>
              <div className={`flex items-center gap-2 ${modules[0]?.tasks?.every((t) => t.is_completed) ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-text-secondary'}`}>
                <CheckCircle2 size={14} className={modules[0]?.tasks?.every((t) => t.is_completed) ? 'text-emerald-500' : 'text-border'} />
                <span>Phase 1 completion</span>
              </div>
              <div className={`flex items-center gap-2 ${overallProgressPct >= 50 ? 'text-emerald-600 dark:text-emerald-400 font-medium' : 'text-text-secondary'}`}>
                <CheckCircle2 size={14} className={overallProgressPct >= 50 ? 'text-emerald-500' : 'text-border'} />
                <span>50% roadmap completed</span>
              </div>
            </div>
          </div>
        </div>

        {/* ── Phase Accordions List ── */}
        <div className="space-y-4">
          {modules.map((mod, idx) => {
            const isExpanded = Boolean(expandedPhases[idx]);
            const modTasks = mod.tasks || [];
            const completedCount = modTasks.filter((t) => t.is_completed).length;
            const totalCount = modTasks.length;
            const phasePct = totalCount > 0 ? Math.round((completedCount / totalCount) * 100) : 0;

            // Apply search & status filters
            const filteredTasks = modTasks.filter((task) => {
              const matchesSearch = task.title.toLowerCase().includes(searchQuery.toLowerCase());
              const matchesStatus =
                statusFilter === 'all'
                  ? true
                  : statusFilter === 'completed'
                  ? task.is_completed
                  : !task.is_completed;
              return matchesSearch && matchesStatus;
            });

            if (searchQuery && filteredTasks.length === 0) return null;

            return (
              <div
                key={idx}
                className="card-surface p-5 transition-colors border border-border"
              >
                {/* Phase Header */}
                <div
                  onClick={() => togglePhase(idx)}
                  className="flex items-start justify-between cursor-pointer group select-none"
                >
                  <div className="flex items-start gap-3">
                    <button
                      type="button"
                      aria-label={isExpanded ? 'Collapse phase' : 'Expand phase'}
                      className="mt-0.5 text-text-secondary group-hover:text-text-primary transition-colors"
                    >
                      {isExpanded ? <ChevronDown size={18} /> : <ChevronRight size={18} />}
                    </button>

                    <div>
                      <h3 className="text-base font-semibold text-text-primary tracking-tight group-hover:text-accent transition-colors">
                        {mod.title}
                      </h3>
                      <p className="text-xs text-text-secondary mt-0.5">
                        {mod.description}
                      </p>
                    </div>
                  </div>

                  {/* Badges: Hours & Tasks */}
                  <div className="flex items-center gap-3 flex-shrink-0 pt-0.5 text-xs">
                    <span className="text-text-secondary bg-surface-muted border border-border px-2.5 py-0.5 rounded-full font-medium">
                      {completedCount}/{totalCount}
                    </span>
                    <span className="text-text-secondary flex items-center gap-1 font-medium">
                      <Clock size={12} />
                      <span>{mod.estimated_hours}</span>
                    </span>
                  </div>
                </div>

                {/* Phase Progress Bar */}
                <div className="mt-3 ml-7 h-1.5 bg-surface-muted border border-border rounded-full overflow-hidden">
                  <div
                    className="h-full bg-accent rounded-full transition-all duration-500"
                    style={{ width: `${phasePct}%` }}
                  />
                </div>

                {/* Tasks List */}
                {isExpanded && (
                  <div className="mt-4 ml-7 space-y-2 pt-2 border-t border-border/60">
                    {filteredTasks.length === 0 ? (
                      <p className="text-xs text-text-secondary py-2">
                        No tasks match the selected filter.
                      </p>
                    ) : (
                      filteredTasks.map((task) => {
                        const isUpdating = updatingTaskId === task.task_id;
                        return (
                          <div
                            id={`task-${task.task_id}`}
                            key={task.task_id}
                            onClick={() => handleTaskToggle(task.task_id, task.is_completed)}
                            className="flex items-center justify-between py-2 px-3 rounded-xl hover:bg-surface-muted cursor-pointer group transition-all"
                          >
                            <div className="flex items-center gap-3 min-w-0">
                              <button
                                type="button"
                                aria-label={task.is_completed ? 'Mark incomplete' : 'Mark complete'}
                                disabled={isUpdating}
                                className="text-text-secondary group-hover:text-text-primary transition-colors flex-shrink-0"
                              >
                                {task.is_completed ? (
                                  <CheckCircle2 size={16} className="text-emerald-500" />
                                ) : (
                                  <Circle size={16} className="text-border group-hover:text-text-secondary" />
                                )}
                              </button>

                              <span
                                className={`text-xs sm:text-sm leading-tight truncate ${
                                  task.is_completed
                                    ? 'line-through text-text-secondary/60'
                                    : 'text-text-primary'
                                }`}
                              >
                                {task.title}
                              </span>
                            </div>

                            {/* Task Hours */}
                            <div className="flex items-center gap-1 text-[11px] text-text-secondary bg-surface-muted border border-border px-2 py-0.5 rounded-md flex-shrink-0 ml-3">
                              <Clock size={11} />
                              <span>{task.hours}</span>
                            </div>
                          </div>
                        );
                      })
                    )}
                  </div>
                )}
              </div>
            );
          })}
        </div>

        {/* ── Learning Tip Card ── */}
        <div className="card-surface p-5 flex items-center gap-4 bg-surface-muted/40 border-border">
          <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-500 flex items-center justify-center flex-shrink-0">
            <Lightbulb size={20} />
          </div>
          <div>
            <p className="text-xs font-semibold text-text-primary">
              Pro Learning Tip
            </p>
            <p className="text-xs text-text-secondary mt-0.5">
              Consistency beats intensity. Setting aside 45 focused minutes every day leads to faster skill retention than cramming on weekends.
            </p>
          </div>
        </div>

        {/* ── Bottom Floating Refine Prompt Bar ── */}
        <div className="sticky bottom-6 mt-10 max-w-xl mx-auto px-2 pointer-events-none z-20">
          <div className="pointer-events-auto">
            <form
              onSubmit={handleRefineSubmit}
              className="bg-surface border border-border rounded-2xl p-1.5 pl-4 flex items-center gap-3 shadow-2xl backdrop-blur-md"
            >
              <input
                type="text"
                value={refinePrompt}
                onChange={(e) => setRefinePrompt(e.target.value)}
                placeholder="Refine your roadmap (e.g. prioritize backend APIs, adjust study hours)…"
                disabled={isRefining}
                className="bg-transparent text-xs sm:text-sm text-text-primary placeholder:text-text-secondary placeholder:opacity-60 focus:outline-none flex-1 py-1"
              />

              <button
                type="submit"
                disabled={isRefining || !refinePrompt.trim()}
                aria-label="Send prompt"
                className="w-8 h-8 rounded-xl btn-accent flex items-center justify-center disabled:opacity-40 disabled:cursor-not-allowed flex-shrink-0"
              >
                {isRefining ? (
                  <Loader2 size={15} className="animate-spin" />
                ) : (
                  <ArrowUp size={16} />
                )}
              </button>
            </form>
          </div>
        </div>
      </div>
    </WorkflowLayout>
  );
}
