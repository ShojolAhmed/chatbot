import { useEffect, useState } from 'react'

/**
 * Tracks whether a media query currently matches, updating on viewport
 * changes. Used sparingly -- most responsive behavior should stay in CSS;
 * this is only for the handful of cases where JS needs to know too (e.g.
 * deciding whether "collapsed" should visually apply).
 */
export function useMediaQuery(query) {
  const [matches, setMatches] = useState(() =>
    typeof window !== 'undefined' ? window.matchMedia(query).matches : false,
  )

  useEffect(() => {
    const mql = window.matchMedia(query)
    const onChange = () => setMatches(mql.matches)
    onChange()
    mql.addEventListener('change', onChange)
    return () => mql.removeEventListener('change', onChange)
  }, [query])

  return matches
}
