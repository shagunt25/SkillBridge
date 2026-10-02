import React, { useState, useRef, useEffect } from 'react';
import { Link, useNavigate } from 'react-router-dom';
import {
  User,
  Settings,
  Sun,
  Moon,
  LogOut,
  Check,
} from 'lucide-react';
import { useAppContext, ACTIONS } from '../context/AppContext';

export default function ProfileDropdown({ align = 'right', className = '' }) {
  const { state, dispatch } = useAppContext();
  const navigate = useNavigate();
  const [isOpen, setIsOpen] = useState(false);
  const menuRef = useRef(null);

  const user = state.user || {
    name: 'Student Profile',
    email: 'learner@skillbridge.ai',
  };

  const initial = (user.name || user.email || 'A').charAt(0).toUpperCase();

  // Close when clicking outside or pressing Escape
  useEffect(() => {
    function handleClickOutside(e) {
      if (menuRef.current && !menuRef.current.contains(e.target)) {
        setIsOpen(false);
      }
    }
    function handleKeyDown(e) {
      if (e.key === 'Escape') {
        setIsOpen(false);
      }
    }
    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside);
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [isOpen]);

  const handleLogout = () => {
    dispatch({ type: ACTIONS.LOGOUT });
    setIsOpen(false);
    navigate('/login', { replace: true });
  };

  const setTheme = (themeMode) => {
    dispatch({ type: ACTIONS.SET_THEME, payload: themeMode });
  };

  return (
    <div className={`relative inline-block ${className}`} ref={menuRef}>
      {/* Trigger Avatar */}
      <button
        type="button"
        onClick={() => setIsOpen((prev) => !prev)}
        aria-haspopup="true"
        aria-expanded={isOpen}
        aria-label="User account and theme settings"
        className="w-8 h-8 rounded-full bg-accent/20 text-accent font-semibold text-xs flex items-center justify-center border border-border hover:border-accent transition-all select-none focus:outline-none focus:ring-2 focus:ring-accent/40"
      >
        {initial}
      </button>

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          role="menu"
          className={`absolute ${
            align === 'left' ? 'left-0' : 'right-0'
          } bottom-full mb-2 md:bottom-auto md:top-full md:mt-2 w-64 rounded-2xl bg-surface border border-border shadow-xl p-3 z-50 fade-up`}
        >
          {/* User Info Header */}
          <div className="flex items-center gap-3 px-2 py-2 border-b border-border mb-2">
            <div className="w-10 h-10 rounded-full bg-accent/15 text-accent font-bold text-sm flex items-center justify-center border border-border flex-shrink-0">
              {initial}
            </div>
            <div className="min-w-0 flex-1">
              <p className="text-sm font-semibold text-text-primary truncate">
                {user.name || 'SkillBridge Learner'}
              </p>
              <p className="text-xs text-text-secondary truncate">
                {user.email}
              </p>
            </div>
          </div>

          {/* Navigation Links */}
          <div className="space-y-1 mb-2">
            <Link
              to="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors"
            >
              <User size={14} />
              <span>Profile</span>
            </Link>
            <Link
              to="/settings"
              onClick={() => setIsOpen(false)}
              className="flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors"
            >
              <Settings size={14} />
              <span>Settings</span>
            </Link>
          </div>

          {/* Theme Selector */}
          <div className="border-t border-border pt-2 mb-2">
            <p className="text-[10px] font-semibold uppercase tracking-wider text-text-secondary px-3 mb-1.5">
              Theme
            </p>
            <div className="space-y-1">
              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                  state.theme === 'light'
                    ? 'bg-surface-muted text-accent font-semibold'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-muted'
                }`}
              >
                <span className="flex items-center gap-2">
                  <Sun size={14} className="text-amber-500" />
                  <span>Light Mode</span>
                </span>
                {state.theme === 'light' && <Check size={14} />}
              </button>

              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`w-full flex items-center justify-between px-3 py-2 rounded-xl text-xs font-medium transition-colors ${
                  state.theme === 'dark'
                    ? 'bg-surface-muted text-accent font-semibold'
                    : 'text-text-secondary hover:text-text-primary hover:bg-surface-muted'
                }`}
              >
                <span className="flex items-center gap-2">
                  <Moon size={14} className="text-teal-400" />
                  <span>Dark Mode</span>
                </span>
                {state.theme === 'dark' && <Check size={14} />}
              </button>
            </div>
          </div>

          {/* Logout Option */}
          <div className="border-t border-border pt-1">
            <button
              type="button"
              onClick={handleLogout}
              className="w-full flex items-center gap-2.5 px-3 py-2 rounded-xl text-xs font-medium text-danger hover:bg-rose-500/10 transition-colors"
            >
              <LogOut size={14} />
              <span>Log out</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}
