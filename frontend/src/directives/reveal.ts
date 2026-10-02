import type { Directive } from 'vue'

/**
 * v-reveal: hiện dần khi phần tử cuộn vào màn hình (IntersectionObserver).
 * - `v-reveal`          : phần tử hiện dần một lần.
 * - `v-reveal.stagger`  : các phần tử con trực tiếp hiện lần lượt, cách nhau 70ms.
 * Không làm gì khi trình duyệt không có IntersectionObserver hoặc người dùng chọn giảm chuyển động,
 * nên nội dung luôn thấy được. Kiểu CSS nằm ở styles/main.css (.reveal, .reveal-in).
 */
interface RevealElement extends HTMLElement {
  __revealObserver?: IntersectionObserver
}

const STEP_MS = 70
const MAX_STEPS = 8

function canAnimate(): boolean {
  if (typeof window === 'undefined' || typeof IntersectionObserver === 'undefined') return false
  return !window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
}

export const vReveal: Directive<RevealElement, undefined> = {
  mounted(el, binding) {
    if (!canAnimate()) return
    const targets = binding.modifiers.stagger ? (Array.from(el.children) as HTMLElement[]) : [el]
    const observer = new IntersectionObserver(
      (entries) => {
        for (const entry of entries) {
          if (!entry.isIntersecting) continue
          entry.target.classList.add('reveal-in')
          observer.unobserve(entry.target)
        }
      },
      { threshold: 0.12, rootMargin: '0px 0px -40px 0px' },
    )
    targets.forEach((target, index) => {
      target.classList.add('reveal')
      target.style.setProperty('--reveal-delay', `${Math.min(index, MAX_STEPS) * STEP_MS}ms`)
      observer.observe(target)
    })
    el.__revealObserver = observer
  },
  unmounted(el) {
    el.__revealObserver?.disconnect()
  },
}
