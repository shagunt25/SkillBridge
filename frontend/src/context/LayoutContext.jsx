import React, { createContext, useContext, useState, useEffect } from 'react';

const LayoutContext = createContext(null);

const STORAGE_KEY = 'skillbridge_sidebar_collapsed';

export function LayoutProvider({ children }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(() => {
    try {
      return localStorage.getItem(STORAGE_KEY) === 'true';
    } catch {
      return false;
    }
  });

  const [mobileOpen, setMobileOpen] = useState(false);

  // Sync sidebarCollapsed to localStorage
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, String(sidebarCollapsed));
    } catch {
      // Ignore storage errors in restricted environments
    }
  }, [sidebarCollapsed]);

  const toggleSidebar = () => {
    setSidebarCollapsed((prev) => !prev);
  };

  const toggleMobile = () => {
    setMobileOpen((prev) => !prev);
  };

  const closeMobile = () => {
    setMobileOpen(false);
  };

  const openMobile = () => {
    setMobileOpen(true);
  };

  return (
    <LayoutContext.Provider
      value={{
        sidebarCollapsed,
        setSidebarCollapsed,
        toggleSidebar,
        mobileOpen,
        toggleMobile,
        closeMobile,
        openMobile,
      }}
    >
      {children}
    </LayoutContext.Provider>
  );
}

export function useLayout() {
  const context = useContext(LayoutContext);
  if (!context) {
    throw new Error('useLayout must be used within a LayoutProvider');
  }
  return context;
}
