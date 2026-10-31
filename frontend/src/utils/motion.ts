/**
 * Tiện ích chuyển động dùng chung.
 * Mọi chuyển động do JavaScript điều khiển (cuộn mượt…) phải đi qua đây để tôn trọng
 * thiết lập "giảm chuyển động" của hệ điều hành (WCAG 2.3.3).
 */
export function prefersReducedMotion(): boolean {
  if (typeof window === 'undefined' || typeof window.matchMedia !== 'function') return false
  return window.matchMedia('(prefers-reduced-motion: reduce)').matches
}

export function scrollBehavior(): ScrollBehavior {
  return prefersReducedMotion() ? 'auto' : 'smooth'
}

export function scrollToTop(): void {
  window.scrollTo({ top: 0, behavior: scrollBehavior() })
}

/**
 * Defer non-critical work until the browser is idle without delaying unsupported environments.
 * The timeout keeps below-the-fold content from waiting indefinitely on a busy main thread.
 */
export function scheduleWhenIdle(callback: () => void, timeout = 1200): () => void {
  if (typeof window === 'undefined' || typeof window.requestIdleCallback !== 'function') {
    callback()
    return () => {}
  }

  const idleId = window.requestIdleCallback(callback, { timeout })
  return () => window.cancelIdleCallback(idleId)
}
