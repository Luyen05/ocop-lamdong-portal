import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'

const FOCUSABLE_SELECTOR = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled]):not([type="hidden"])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

const SCROLL_LOCK_CLASS = 'has-modal-open'
let scrollLocks = 0

function lockScroll(): void {
  scrollLocks += 1
  document.body.classList.add(SCROLL_LOCK_CLASS)
}

function unlockScroll(): void {
  scrollLocks = Math.max(0, scrollLocks - 1)
  if (scrollLocks === 0) document.body.classList.remove(SCROLL_LOCK_CLASS)
}

function isRendered(element: HTMLElement): boolean {
  if (element.closest('[hidden], [inert]')) return false
  const style = window.getComputedStyle(element)
  return style.display !== 'none' && style.visibility !== 'hidden'
}

export interface FocusTrapOptions {
  /** Gọi khi người dùng bấm Esc ở bất kỳ vị trí nào trên trang lúc ngăn kéo đang mở. */
  onEscape: () => void
  /** Phần tử nhận focus đầu tiên khi mở; mặc định là phần tử focus được đầu tiên trong vùng. */
  initialFocus?: () => HTMLElement | null | undefined
  /** Phần tử nhận lại focus khi đóng (ví dụ nút mở); mặc định là phần tử đang focus lúc mở. */
  returnFocusTo?: () => HTMLElement | null | undefined
}

/**
 * Hành vi hộp thoại cho ngăn kéo/bottom sheet khi `active` bật: focus vào trong, Tab và Shift+Tab xoay vòng
 * trong vùng, Esc đóng (nghe ở cấp document nên đúng cả khi focus đang ở ngoài), khóa cuộn trang và trả focus
 * về nút mở khi đóng. Gỡ sạch khi tắt hoặc khi component bị hủy.
 * Không thay đổi `useDialogFocus` (dùng cho các hộp thoại khác).
 */
export function useFocusTrap(
  active: Readonly<Ref<boolean>>,
  container: Ref<HTMLElement | null>,
  options: FocusTrapOptions,
): void {
  let engaged = false
  let opener: HTMLElement | null = null

  function focusables(): HTMLElement[] {
    const root = container.value
    if (!root) return []
    return Array.from(root.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)).filter(isRendered)
  }

  function onKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault()
      options.onEscape()
      return
    }
    if (event.key !== 'Tab') return
    const root = container.value
    if (!root) return
    const items = focusables()
    if (!items.length) {
      event.preventDefault()
      root.focus()
      return
    }
    const first = items[0]
    const last = items[items.length - 1]
    const current = document.activeElement
    if (!root.contains(current)) {
      // Focus đang ở ngoài ngăn kéo (ví dụ trên BODY): kéo vào trong thay vì để Tab đi tiếp ra nền.
      event.preventDefault()
      ;(event.shiftKey ? last : first).focus()
    } else if (event.shiftKey && (current === first || current === root)) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && current === last) {
      event.preventDefault()
      first.focus()
    }
  }

  function engage(): void {
    if (engaged) return
    engaged = true
    opener = document.activeElement instanceof HTMLElement ? document.activeElement : null
    lockScroll()
    document.addEventListener('keydown', onKeydown)
  }

  function release(restoreFocus: boolean): void {
    if (!engaged) return
    engaged = false
    document.removeEventListener('keydown', onKeydown)
    unlockScroll()
    if (restoreFocus) {
      const target = options.returnFocusTo?.() ?? opener
      if (target && target.isConnected) target.focus()
    }
    opener = null
  }

  watch(
    active,
    async (isActive) => {
      if (!isActive) {
        release(true)
        return
      }
      engage()
      await nextTick()
      if (!engaged) return
      const target = options.initialFocus?.() ?? focusables()[0] ?? container.value
      target?.focus()
    },
    { flush: 'post', immediate: true },
  )

  onBeforeUnmount(() => release(false))
}
