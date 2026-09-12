export function Logo({ size = 'md', showLabel = true }) {
  const dims = size === 'sm' ? 'w-6 h-6 text-sm' : 'w-7 h-7 text-base'
  return (
    <div className="flex items-center gap-2.5 select-none">
      <span
        className={`${dims} shrink-0 rounded-lg bg-accent text-[#1a140f] font-semibold flex items-center justify-center`}
        aria-hidden="true"
      >
        S
      </span>
      {showLabel && <span className="text-[15px] font-medium tracking-tight text-text">Sable</span>}
    </div>
  )
}
