import { useEffect } from 'react'
import { useSidebar } from '../../context/SidebarContext'
import { useMediaQuery } from '../../hooks/useMediaQuery'
import { SidebarHeader } from './SidebarHeader'
import { NewChatButton } from './NewChatButton'
import { ConversationList } from './ConversationList'
import { ToolsSection } from './ToolsSection'
import { AccountSection } from './AccountSection'

export function Sidebar({ onNewChat, canStartNewChat }) {
  const { isCollapsed, isMobileOpen, toggleCollapsed, closeMobile } = useSidebar()
  const isDesktop = useMediaQuery('(min-width: 1024px)')

  // The collapsed icon-rail is a desktop-only concept -- on mobile the
  // drawer is always shown at full width when open.
  const collapsed = isCollapsed && isDesktop

  useEffect(() => {
    if (!isMobileOpen) return
    function onKeyDown(e) {
      if (e.key === 'Escape') closeMobile()
    }
    document.addEventListener('keydown', onKeyDown)
    document.body.style.overflow = 'hidden'
    return () => {
      document.removeEventListener('keydown', onKeyDown)
      document.body.style.overflow = ''
    }
  }, [isMobileOpen, closeMobile])

  // Close the mobile drawer automatically if the viewport grows into the
  // desktop layout while it's open.
  useEffect(() => {
    if (isDesktop && isMobileOpen) closeMobile()
  }, [isDesktop, isMobileOpen, closeMobile])

  return (
    <>
      {isMobileOpen && (
        <div
          className="animate-fade-in fixed inset-0 z-30 bg-black/60 lg:hidden"
          onClick={closeMobile}
          aria-hidden="true"
        />
      )}

      <aside
        aria-label="Sidebar"
        className={`fixed inset-y-0 left-0 z-40 flex h-dvh w-[270px] flex-col border-r border-sidebar-border bg-sidebar transition-transform duration-200 ease-out lg:static lg:h-full lg:translate-x-0 lg:transition-[width] lg:duration-200 ${
          isMobileOpen ? 'translate-x-0' : '-translate-x-full'
        } ${collapsed ? 'lg:w-[72px]' : 'lg:w-[270px]'}`}
      >
        <SidebarHeader collapsed={collapsed} onToggleCollapsed={toggleCollapsed} onCloseMobile={closeMobile} />

        <NewChatButton collapsed={collapsed} onClick={onNewChat} disabled={!canStartNewChat} />

        <div className="min-h-0 flex-1 overflow-y-auto pb-2">
          <ConversationList collapsed={collapsed} />
          <ToolsSection collapsed={collapsed} />
        </div>

        <AccountSection collapsed={collapsed} onExpand={toggleCollapsed} />
      </aside>
    </>
  )
}
