import { useEffect } from 'react'
import { useLocation } from 'react-router-dom'

// O8 acceptance: "focus moves to the view's h2 on route change" (design-review
// finding — the old hash-toggle UI never moved focus, so screen-reader/
// keyboard users stayed on a now-hidden control). Every route's top-level h2
// carries `data-view-heading` + `tabIndex={-1}`; this hook is mounted once,
// above the <Outlet/>, so it fires for every navigation regardless of which
// route rendered. Also resets scroll to the top of the content pane — back-
// button navigation should land you looking at the top of the restored view,
// not wherever the previous page happened to be scrolled.
export function useRouteA11y(contentRef: React.RefObject<HTMLElement | null>) {
  const location = useLocation()

  useEffect(() => {
    contentRef.current?.scrollTo({ top: 0 })
    const heading = document.querySelector<HTMLElement>('[data-view-heading]')
    if (heading) {
      heading.focus()
    }
    // location.key changes on every navigation (push, replace, pop/back) —
    // pathname alone would miss a re-navigation to the same path.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [location.key])
}
