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
