import React from 'react';
import { Menu } from 'lucide-react';
import { useLayout } from '../context/LayoutContext';
import ProfileDropdown from './ProfileDropdown';

export default function TopNavigation({ pageTitle = '' }) {
  const { toggleMobile } = useLayout();

  return (
    <header className="h-16 px-6 sm:px-8 border-b border-border bg-surface/75 backdrop-blur-md flex items-center justify-between flex-shrink-0 sticky top-0 z-20 select-none">
      <div className="flex items-center gap-3 min-w-0">
        <button
          type="button"
          onClick={toggleMobile}
          aria-label="Open mobile navigation"
          className="md:hidden p-1.5 rounded-lg text-text-secondary hover:text-text-primary hover:bg-surface-muted transition-colors flex-shrink-0"
        >
          <Menu size={18} />
        </button>
        {pageTitle && (
          <h1 className="text-sm font-semibold text-text-primary truncate">
            {pageTitle}
          </h1>
        )}
      </div>

      <div className="flex items-center gap-3 flex-shrink-0">
        <ProfileDropdown align="right" />
      </div>
    </header>
  );
}
