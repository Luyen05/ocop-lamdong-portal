import { nextTick, onBeforeUnmount, watch, type Ref } from 'vue'

const focusableSelector = [
  'a[href]',
  'button:not([disabled])',
  'input:not([disabled])',
  'select:not([disabled])',
  'textarea:not([disabled])',
  '[tabindex]:not([tabindex="-1"])',
].join(',')

// Nhiều hộp thoại có thể chồng nhau (ví dụ hộp xác nhận trên hộp duyệt): chỉ gỡ khóa cuộn khi hộp cuối cùng đóng.
let openDialogCount = 0

export interface DialogFocusOptions {
  /** Bộ chọn CSS của phần tử nhận focus đầu tiên trong hộp thoại (mặc định: phần tử focus được đầu tiên). */
  initialFocus?: string
}

export function useDialogFocus(
  isOpen: Readonly<Ref<boolean>>,
  dialogRef: Ref<HTMLElement | null>,
  close: () => void,
  options: DialogFocusOptions = {},
): void {
  let activeDialog: HTMLElement | null = null
  let previousFocus: HTMLElement | null = null

  function handleKeydown(event: KeyboardEvent): void {
    if (event.key === 'Escape') {
      event.preventDefault()
      close()
      return
    }
    if (event.key !== 'Tab' || !activeDialog) return

    const focusable = Array.from(
      activeDialog.querySelectorAll<HTMLElement>(focusableSelector),
    ).filter((element) => element.offsetParent !== null)
    if (!focusable.length) {
      event.preventDefault()
      activeDialog.focus()
      return
    }

    const first = focusable[0]
    const last = focusable[focusable.length - 1]
    if (event.shiftKey && document.activeElement === first) {
      event.preventDefault()
      last.focus()
    } else if (!event.shiftKey && document.activeElement === last) {
      event.preventDefault()
      first.focus()
    }
  }

  let counted = false

  function deactivate(restoreFocus = true): void {
    activeDialog?.removeEventListener('keydown', handleKeydown)
    activeDialog = null
    if (counted) {
      counted = false
      openDialogCount = Math.max(0, openDialogCount - 1)
    }
    if (openDialogCount === 0) document.body.classList.remove('has-modal-open')
    if (restoreFocus) previousFocus?.focus()
    previousFocus = null
  }

  watch(
    isOpen,
    async (open) => {
      if (!open) {
        deactivate()
        return
      }

      previousFocus = document.activeElement instanceof HTMLElement ? document.activeElement : null
      if (!counted) {
        counted = true
        openDialogCount += 1
      }
      document.body.classList.add('has-modal-open')
      await nextTick()
      activeDialog = dialogRef.value
      activeDialog?.addEventListener('keydown', handleKeydown)
      const preferred = options.initialFocus
        ? activeDialog?.querySelector<HTMLElement>(options.initialFocus)
        : null
      const firstFocusable = preferred ?? activeDialog?.querySelector<HTMLElement>(focusableSelector)
      ;(firstFocusable ?? activeDialog)?.focus()
    },
    { flush: 'post' },
  )

  onBeforeUnmount(() => deactivate(false))
}
