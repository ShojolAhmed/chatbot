import { Menu } from 'lucide-react'
import { useSidebar } from '../../context/SidebarContext'
import { Logo } from '../UI/Logo'

export function MobileTopBar() {
  const { openMobile } = useSidebar()

  return (
    <div className="flex h-14 shrink-0 items-center gap-1 border-b border-border-soft bg-bg px-2 lg:hidden">
      <button
        type="button"
        onClick={openMobile}
        aria-label="Open sidebar"
        className="flex h-9 w-9 shrink-0 items-center justify-center rounded-lg text-text-muted transition-colors hover:bg-surface-2 hover:text-text"
      >
        <Menu size={19} strokeWidth={1.75} aria-hidden="true" />
      </button>
      <Logo size="sm" />
    </div>
  )
}
