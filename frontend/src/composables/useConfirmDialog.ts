import { reactive } from 'vue'

export interface ConfirmOptions {
  title: string
  message?: string
  confirmLabel?: string
  cancelLabel?: string
  tone?: 'danger' | 'primary'
}

/**
 * Thay `window.confirm` bằng hộp thoại ConfirmDialog nhưng giữ cách viết `if (!(await ask({...}))) return`.
 * Dùng: `<ConfirmDialog v-bind="confirm.props" @confirm="confirm.accept" @cancel="confirm.dismiss" />`.
 */
export function useConfirmDialog() {
  const props = reactive({
    open: false,
    title: '',
    message: '',
    confirmLabel: 'Xác nhận',
    cancelLabel: 'Hủy',
    tone: 'primary' as 'danger' | 'primary',
  })
  let resolver: ((value: boolean) => void) | null = null

  function settle(value: boolean): void {
    props.open = false
    const resolve = resolver
    resolver = null
    resolve?.(value)
  }

  function ask(options: ConfirmOptions): Promise<boolean> {
    // Đang có câu hỏi dở thì coi như đã hủy câu cũ.
    if (resolver) settle(false)
    props.title = options.title
    props.message = options.message ?? ''
    props.confirmLabel = options.confirmLabel ?? 'Xác nhận'
    props.cancelLabel = options.cancelLabel ?? 'Hủy'
    props.tone = options.tone ?? 'primary'
    props.open = true
    return new Promise<boolean>((resolve) => {
      resolver = resolve
    })
  }

  return {
    props,
    ask,
    accept: () => settle(true),
    dismiss: () => settle(false),
  }
}
