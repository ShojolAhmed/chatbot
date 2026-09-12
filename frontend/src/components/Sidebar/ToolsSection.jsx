import { Wrench } from 'lucide-react'

// No tools exist yet -- this section is a structural placeholder so future
// tools can be dropped in as their own entries without reshaping the sidebar.
export function ToolsSection({ collapsed }) {
  if (collapsed) {
    return (
      <div className="flex flex-col items-center px-2 pt-1">
        <div
          className="flex h-9 w-9 items-center justify-center rounded-lg text-text-faint"
          title="Tools"
          aria-label="Tools"
        >
          <Wrench size={17} strokeWidth={1.75} aria-hidden="true" />
        </div>
      </div>
    )
  }

  return (
    <div className="px-3 pt-5">
      <h2 className="px-0.5 pb-1.5 text-xs font-medium uppercase tracking-wide text-text-faint">Tools</h2>
      <div className="flex items-center gap-2 px-0.5 py-1 text-sm text-text-faint">
        <Wrench size={15} strokeWidth={1.75} aria-hidden="true" />
        No tools available yet
      </div>
    </div>
  )
}
