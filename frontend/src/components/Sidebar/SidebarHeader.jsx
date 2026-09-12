import { PanelLeftClose, PanelLeft, X } from 'lucide-react'
import { Logo } from '../UI/Logo'
import { SidebarIconButton } from './SidebarToggle'

export function SidebarHeader({ collapsed, onToggleCollapsed, onCloseMobile }) {
  if (collapsed) {
    // Desktop-only state: the sidebar is a narrow icon rail, so the expand
    // control doubles as the brand mark's position.
    return (
      <div className="flex h-14 shrink-0 items-center justify-center">
        <SidebarIconButton icon={PanelLeft} label="Expand sidebar" onClick={onToggleCollapsed} />
      </div>
    )
  }

  return (
    <div className="flex h-14 shrink-0 items-center justify-between px-3">
      <Logo />
      <SidebarIconButton
        icon={PanelLeftClose}
        label="Collapse sidebar"
        onClick={onToggleCollapsed}
        className="hidden lg:flex"
      />
      <SidebarIconButton icon={X} label="Close sidebar" onClick={onCloseMobile} className="lg:hidden" />
    </div>
  )
}
