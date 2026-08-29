/**
 * AppContext — global state via Context + useReducer
 * State shape mirrors the API contract exactly.
 */
import { createContext, useContext, useEffect, useReducer } from 'react';

const STORAGE_KEY = 'skillbridge-roadmap-state';

// ─── Initial State ────────────────────────────────────────────────────────────
const initialState = {
  // Onboarding inputs
  currentSkills: [],       // string[]
  targetType: 'role',      // 'role' | 'jd'
  targetValue: '',         // string
  resumeFile: null,        // File | null (memory only; never persisted)

  // Roadmap data (from API)
  matchScore: null,        // number 0-100
  missingSkills: [],       // string[]
  learningModules: [],     // [{ title, tasks: [{task_id, title, is_completed}], resource_search_terms }]

  // UI state
  isGenerating: false,
  isRefining: false,
  error: null,
};

// ─── Action Types ─────────────────────────────────────────────────────────────
export const ACTIONS = {
  SET_SKILLS:          'SET_SKILLS',
  SET_TARGET:          'SET_TARGET',
  GENERATE_START:      'GENERATE_START',
  GENERATE_SUCCESS:    'GENERATE_SUCCESS',
  GENERATE_ERROR:      'GENERATE_ERROR',
  REFINE_START:        'REFINE_START',
  REFINE_SUCCESS:      'REFINE_SUCCESS',
  REFINE_ERROR:        'REFINE_ERROR',
  UPDATE_TASK:         'UPDATE_TASK',
  CLEAR_ERROR:         'CLEAR_ERROR',
  RESET:               'RESET',
  SET_RESUME:          'SET_RESUME',
};

// ─── Reducer ──────────────────────────────────────────────────────────────────
function appReducer(state, action) {
  switch (action.type) {
    case ACTIONS.SET_SKILLS:
      return { ...state, currentSkills: action.payload, resumeFile: null };

    case ACTIONS.SET_RESUME:
      return { ...state, currentSkills: [], resumeFile: action.payload };

    case ACTIONS.SET_TARGET:
      return { ...state, targetType: action.payload.targetType, targetValue: action.payload.targetValue };

    case ACTIONS.GENERATE_START:
      return { ...state, isGenerating: true, error: null };

    case ACTIONS.GENERATE_SUCCESS:
      return {
        ...state,
        isGenerating: false,
        matchScore:      action.payload.match_score,
        missingSkills:   action.payload.missing_skills,
        learningModules: action.payload.learning_modules,
      };

    case ACTIONS.GENERATE_ERROR:
      return { ...state, isGenerating: false, error: action.payload };

    case ACTIONS.REFINE_START:
      return { ...state, isRefining: true, error: null };

    case ACTIONS.REFINE_SUCCESS:
      return {
        ...state,
        isRefining: false,
        matchScore:      action.payload.match_score,
        missingSkills:   action.payload.missing_skills,
        learningModules: action.payload.learning_modules,
      };

    case ACTIONS.REFINE_ERROR:
      return { ...state, isRefining: false, error: action.payload };

    case ACTIONS.UPDATE_TASK:
      return {
        ...state,
        learningModules: state.learningModules.map(module => ({
          ...module,
          tasks: module.tasks.map(task =>
            task.task_id === action.payload.task_id
              ? { ...task, is_completed: action.payload.is_completed }
              : task
          ),
        })),
      };

    case ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };

    case ACTIONS.RESET:
      return initialState;

    default:
      return state;
  }
}

// ─── Context & Provider ───────────────────────────────────────────────────────
const AppContext = createContext(null);

function loadInitialState() {
  try {
    const savedState = sessionStorage.getItem(STORAGE_KEY);
    if (!savedState) return initialState;
    const parsed = JSON.parse(savedState);
    return {
      ...initialState,
      currentSkills: Array.isArray(parsed.currentSkills) ? parsed.currentSkills : [],
      targetType: parsed.targetType === 'jd' ? 'jd' : 'role',
      targetValue: typeof parsed.targetValue === 'string' ? parsed.targetValue : '',
      matchScore: Number.isFinite(parsed.matchScore) ? parsed.matchScore : null,
      missingSkills: Array.isArray(parsed.missingSkills) ? parsed.missingSkills : [],
      learningModules: Array.isArray(parsed.learningModules) ? parsed.learningModules : [],
    };
  } catch {
    return initialState;
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, undefined, loadInitialState);

  useEffect(() => {
    const { resumeFile, isGenerating, isRefining, error, ...persistedState } = state;
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(persistedState));
  }, [state]);
  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────
export function useAppContext() {
  const ctx = useContext(AppContext);
  if (!ctx) throw new Error('useAppContext must be used within AppProvider');
  return ctx;
}
