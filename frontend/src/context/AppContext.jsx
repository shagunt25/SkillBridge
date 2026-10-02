/**
 * AppContext — global state via Context + useReducer
 * State shape mirrors the API contract exactly, with theme and session management.
 */
import { createContext, useContext, useEffect, useReducer } from 'react';

const STORAGE_KEY = 'skillbridge-roadmap-state';
const THEME_KEY = 'skillbridge_theme';
const AUTH_USER_KEY = 'skillbridge_auth_user';
const AUTH_TOKEN_KEY = 'skillbridge_auth_token';

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

  // Theme & Session
  theme: 'dark',           // 'light' | 'dark'
  user: null,              // { name, email } | null
  isAuthenticated: false,
};

// ─── Action Types ─────────────────────────────────────────────────────────────
export const ACTIONS = {
  SET_SKILLS:          'SET_SKILLS',
  SET_TARGET:          'SET_TARGET',
  SET_RESUME:          'SET_RESUME',
  GENERATE_START:      'GENERATE_START',
  GENERATE_SUCCESS:    'GENERATE_SUCCESS',
  GENERATE_ERROR:      'GENERATE_ERROR',
  REFINE_START:        'REFINE_START',
  REFINE_SUCCESS:      'REFINE_SUCCESS',
  REFINE_ERROR:        'REFINE_ERROR',
  UPDATE_TASK:         'UPDATE_TASK',
  ADD_SKILL_TO_ROADMAP:'ADD_SKILL_TO_ROADMAP',
  CLEAR_ERROR:         'CLEAR_ERROR',
  RESET:               'RESET',
  SET_THEME:           'SET_THEME',
  LOGIN:               'LOGIN',
  LOGOUT:              'LOGOUT',
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
        error: null,
      };

    case ACTIONS.GENERATE_ERROR:
      return { ...state, isGenerating: false, error: action.payload };

    case ACTIONS.REFINE_START:
      return { ...state, isRefining: true, error: null };

    case ACTIONS.REFINE_SUCCESS:
      return {
        ...state,
        isRefining: false,
        matchScore:      action.payload.match_score ?? state.matchScore,
        missingSkills:   action.payload.missing_skills ?? state.missingSkills,
        learningModules: action.payload.learning_modules ?? state.learningModules,
        error: null,
      };

    case ACTIONS.REFINE_ERROR:
      return { ...state, isRefining: false, error: action.payload };

    case ACTIONS.UPDATE_TASK:
      return {
        ...state,
        learningModules: (state.learningModules || []).map(module => ({
          ...module,
          tasks: (module.tasks || []).map(task =>
            task.task_id === action.payload.task_id
              ? { ...task, is_completed: action.payload.is_completed }
              : task
          ),
        })),
      };

    case ACTIONS.ADD_SKILL_TO_ROADMAP: {
      const skillToAdd = action.payload;
      if (!skillToAdd) return state;

      // Add to existing module or create a new module
      const currentModules = [...(state.learningModules || [])];
      const newTask = {
        task_id: `custom-task-${Date.now()}`,
        title: `Master ${skillToAdd} core principles and hands-on exercises`,
        is_completed: false,
        hours: '4h',
      };

      if (currentModules.length > 0) {
        currentModules[0] = {
          ...currentModules[0],
          tasks: [...(currentModules[0].tasks || []), newTask],
        };
      } else {
        currentModules.push({
          title: `Focus: ${skillToAdd}`,
          description: `Targeted learning path for ${skillToAdd}`,
          estimated_hours: '4h',
          tasks: [newTask],
          resource_search_terms: [`${skillToAdd} tutorial`, `${skillToAdd} best practices`],
        });
      }

      return {
        ...state,
        learningModules: currentModules,
      };
    }

    case ACTIONS.SET_THEME: {
      const newTheme = action.payload === 'light' ? 'light' : 'dark';
      try {
        localStorage.setItem(THEME_KEY, newTheme);
        if (newTheme === 'dark') {
          document.documentElement.classList.add('dark');
        } else {
          document.documentElement.classList.remove('dark');
        }
      } catch (e) {}
      return { ...state, theme: newTheme };
    }

    case ACTIONS.LOGIN: {
      const user = action.payload?.user || { email: 'alex@example.com', name: 'Alex' };
      const token = action.payload?.token || 'session-token-' + Date.now();
      try {
        localStorage.setItem(AUTH_USER_KEY, JSON.stringify(user));
        localStorage.setItem(AUTH_TOKEN_KEY, token);
      } catch (e) {}
      return {
        ...state,
        isAuthenticated: true,
        user,
      };
    }

    case ACTIONS.LOGOUT: {
      try {
        localStorage.removeItem(AUTH_USER_KEY);
        localStorage.removeItem(AUTH_TOKEN_KEY);
        sessionStorage.removeItem(STORAGE_KEY);
      } catch (e) {}
      return {
        ...initialState,
        theme: state.theme,
        isAuthenticated: false,
        user: null,
      };
    }

    case ACTIONS.CLEAR_ERROR:
      return { ...state, error: null };

    case ACTIONS.RESET:
      return {
        ...initialState,
        theme: state.theme,
        user: state.user,
        isAuthenticated: state.isAuthenticated,
      };

    default:
      return state;
  }
}

// ─── Context & Provider ───────────────────────────────────────────────────────
const AppContext = createContext(null);

function loadInitialState() {
  let savedTheme = 'dark';
  let savedUser = null;
  let isAuthed = false;

  try {
    const rawTheme = localStorage.getItem(THEME_KEY);
    if (rawTheme === 'light' || rawTheme === 'dark') {
      savedTheme = rawTheme;
    } else if (typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: light)').matches) {
      savedTheme = 'light';
    }

    const rawUser = localStorage.getItem(AUTH_USER_KEY);
    const rawToken = localStorage.getItem(AUTH_TOKEN_KEY);
    if (rawUser && rawToken) {
      savedUser = JSON.parse(rawUser);
      isAuthed = true;
    }
  } catch {}

  // Apply theme class to document
  if (typeof document !== 'undefined') {
    if (savedTheme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }

  try {
    const savedState = sessionStorage.getItem(STORAGE_KEY);
    if (!savedState) {
      return {
        ...initialState,
        theme: savedTheme,
        user: savedUser,
        isAuthenticated: isAuthed,
      };
    }
    const parsed = JSON.parse(savedState);
    return {
      ...initialState,
      currentSkills: Array.isArray(parsed.currentSkills) ? parsed.currentSkills : [],
      targetType: parsed.targetType === 'jd' ? 'jd' : 'role',
      targetValue: typeof parsed.targetValue === 'string' ? parsed.targetValue : '',
      matchScore: Number.isFinite(parsed.matchScore) ? parsed.matchScore : null,
      missingSkills: Array.isArray(parsed.missingSkills) ? parsed.missingSkills : [],
      learningModules: Array.isArray(parsed.learningModules) ? parsed.learningModules : [],
      theme: savedTheme,
      user: savedUser,
      isAuthenticated: isAuthed,
    };
  } catch {
    return {
      ...initialState,
      theme: savedTheme,
      user: savedUser,
      isAuthenticated: isAuthed,
    };
  }
}

export function AppProvider({ children }) {
  const [state, dispatch] = useReducer(appReducer, undefined, loadInitialState);

  useEffect(() => {
    const { resumeFile, isGenerating, isRefining, error, theme, user, isAuthenticated, ...persistedState } = state;
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(persistedState));
    } catch {}
  }, [state]);

  // Sync theme changes with DOM
  useEffect(() => {
    if (state.theme === 'dark') {
      document.documentElement.classList.add('dark');
    } else {
      document.documentElement.classList.remove('dark');
    }
  }, [state.theme]);

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
