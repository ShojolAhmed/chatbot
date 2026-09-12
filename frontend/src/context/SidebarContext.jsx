import { createContext, useCallback, useContext, useEffect, useMemo, useState } from 'react'

const SidebarContext = createContext(null)

const COLLAPSE_STORAGE_KEY = 'sidebar:collapsed'

function readStoredCollapsed() {
  if (typeof window === 'undefined') return false
  try {
    return window.localStorage.getItem(COLLAPSE_STORAGE_KEY) === '1'
  } catch {
    // Storage can be unavailable (private browsing, disabled cookies, etc).
    return false
  }
}

export function SidebarProvider({ children }) {
  // Desktop preference only -- this is a UI layout preference, not user
  // data, so persisting it locally is fine. Mobile drawer state is
  // intentionally never persisted.
  const [isCollapsed, setIsCollapsed] = useState(readStoredCollapsed)
  const [isMobileOpen, setIsMobileOpen] = useState(false)

  useEffect(() => {
    try {
      window.localStorage.setItem(COLLAPSE_STORAGE_KEY, isCollapsed ? '1' : '0')
    } catch {
      // Ignore storage failures -- the preference just won't persist.
    }
  }, [isCollapsed])

  const toggleCollapsed = useCallback(() => setIsCollapsed((v) => !v), [])
  const openMobile = useCallback(() => setIsMobileOpen(true), [])
  const closeMobile = useCallback(() => setIsMobileOpen(false), [])

  const value = useMemo(
    () => ({ isCollapsed, isMobileOpen, toggleCollapsed, openMobile, closeMobile }),
    [isCollapsed, isMobileOpen, toggleCollapsed, openMobile, closeMobile],
  )

  return <SidebarContext.Provider value={value}>{children}</SidebarContext.Provider>
}

export function useSidebar() {
  const ctx = useContext(SidebarContext)
  if (!ctx) throw new Error('useSidebar must be used within a SidebarProvider')
  return ctx
}
