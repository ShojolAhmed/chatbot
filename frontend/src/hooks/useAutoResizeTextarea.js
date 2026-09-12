import { useCallback, useLayoutEffect } from 'react'

/**
 * Grows a textarea to fit its content, up to `maxHeight` px, after which it
 * scrolls internally instead of growing further.
 */
export function useAutoResizeTextarea(ref, value, maxHeight = 200) {
  const resize = useCallback(() => {
    const el = ref.current
    if (!el) return
    el.style.height = 'auto'
    const next = Math.min(el.scrollHeight, maxHeight)
    el.style.height = `${next}px`
    el.style.overflowY = el.scrollHeight > maxHeight ? 'auto' : 'hidden'
  }, [ref, maxHeight])

  useLayoutEffect(() => {
    resize()
  }, [resize, value])

  // The textarea's font (loaded from Google Fonts) can finish loading after
  // this first measurement, changing line-height/character width and making
  // the initial size measurement stale. Re-measure once fonts are ready so
  // a cold page load matches a warm/cached one.
  useLayoutEffect(() => {
    if (!('fonts' in document)) return
    let cancelled = false
    document.fonts.ready.then(() => {
      if (!cancelled) resize()
    })
    return () => {
      cancelled = true
    }
  }, [resize])
}
