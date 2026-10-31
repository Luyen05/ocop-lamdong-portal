import { getCurrentInstance, nextTick, watch, type WatchSource } from 'vue'

/** Loại thông báo: `error`, `success` hoặc tên tùy ý (ví dụ `modal-error`) khớp với `data-flash` trên phần tử. */
export type FlashKind = string

/**
 * Đưa thông báo lỗi/thành công vào khung nhìn và focus vào nó (WCAG 3.3.1, 4.1.3).
 * Thông báo cần có `data-flash="error"` hoặc `data-flash="success"` và `tabindex="-1"`.
 * Truyền các ref thông báo để tự kích hoạt khi chúng chuyển sang một chuỗi mới khác rỗng;
 * trường hợp đặt lại đúng chuỗi cũ thì gọi `revealFlash` thủ công.
 */
export function useFlashFocus(sources: Record<FlashKind, WatchSource<string>> = {}) {
  const instance = getCurrentInstance()

  async function revealFlash(kind: FlashKind = 'error'): Promise<void> {
    await nextTick()
    const root = instance?.proxy?.$el
    const scope: ParentNode = root instanceof HTMLElement ? root : document
    const element =
      scope.querySelector<HTMLElement>(`[data-flash="${kind}"]`) ??
      document.querySelector<HTMLElement>(`[data-flash="${kind}"]`)
    if (!element) return
    if (!element.hasAttribute('tabindex')) element.tabIndex = -1
    const reduceMotion =
      typeof window.matchMedia === 'function' && window.matchMedia('(prefers-reduced-motion: reduce)').matches
    element.scrollIntoView?.({ block: 'center', behavior: reduceMotion ? 'auto' : 'smooth' })
    element.focus({ preventScroll: true })
  }

  for (const [kind, source] of Object.entries(sources)) {
    watch(
      source,
      (next, previous) => {
        if (next && next !== previous) void revealFlash(kind)
      },
      { flush: 'post' },
    )
  }

  return { revealFlash }
}
