// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { nextTick } from 'vue'

import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'

// jsdom không có bố cục nên offsetParent luôn null; useDialogFocus dùng nó để bỏ qua phần tử ẩn.
Object.defineProperty(HTMLElement.prototype, 'offsetParent', {
  configurable: true,
  get() {
    return this.parentNode
  },
})

// Hộp thoại được dựng sẵn rồi mới đổi `open`, đúng cách các trang dùng.
function mountDialog(props: Record<string, unknown> = {}) {
  const wrapper = mount(ConfirmDialog, {
    props: { open: false, title: 'Xóa bản nháp?', message: 'Không hoàn tác được.', ...props },
    attachTo: document.body,
    global: { stubs: { transition: false } },
  })
  return wrapper
}

async function open(wrapper: ReturnType<typeof mountDialog>, props: Record<string, unknown> = {}) {
  await wrapper.setProps({ open: true, ...props })
  await nextTick()
  await nextTick()
}

afterEach(() => {
  document.body.innerHTML = ''
  document.body.className = ''
})

describe('ConfirmDialog', () => {
  it('co role alertdialog, aria-modal, tieu de va mo ta gan nhan', async () => {
    const wrapper = mountDialog()
    await open(wrapper)
    const dialog = wrapper.get('[role="alertdialog"]')
    expect(dialog.attributes('aria-modal')).toBe('true')
    const titleId = dialog.attributes('aria-labelledby') as string
    const descId = dialog.attributes('aria-describedby') as string
    expect(document.getElementById(titleId)?.textContent).toBe('Xóa bản nháp?')
    expect(document.getElementById(descId)?.textContent).toContain('Không hoàn tác được.')
    wrapper.unmount()
  })

  it('focus vao nut an toan (Huy) khi mo', async () => {
    const wrapper = mountDialog({ cancelLabel: 'Giữ lại', confirmLabel: 'Xóa' })
    await open(wrapper)
    expect(document.activeElement?.textContent).toBe('Giữ lại')
    wrapper.unmount()
  })

  it('phat confirm/cancel, nhan tuy chinh va Esc huy', async () => {
    const wrapper = mountDialog({ confirmLabel: 'Xóa bản nháp', tone: 'danger' })
    await open(wrapper)
    const [cancel, confirm] = wrapper.findAll('button')
    expect(confirm.text()).toBe('Xóa bản nháp')
    expect(confirm.classes()).toContain('is-danger')
    await confirm.trigger('click')
    expect(wrapper.emitted('confirm')).toHaveLength(1)
    await cancel.trigger('click')
    expect(wrapper.emitted('cancel')).toHaveLength(1)
    await wrapper.get('[role="alertdialog"]').trigger('keydown', { key: 'Escape' })
    expect(wrapper.emitted('cancel')).toHaveLength(2)
    wrapper.unmount()
  })

  it('giu Tab trong hop thoai', async () => {
    const wrapper = mountDialog()
    await open(wrapper)
    const [cancel, confirm] = wrapper.findAll('button').map((button) => button.element as HTMLButtonElement)
    confirm.focus()
    await wrapper.get('[role="alertdialog"]').trigger('keydown', { key: 'Tab' })
    expect(document.activeElement).toBe(cancel)
    cancel.focus()
    await wrapper.get('[role="alertdialog"]').trigger('keydown', { key: 'Tab', shiftKey: true })
    expect(document.activeElement).toBe(confirm)
    wrapper.unmount()
  })

  it('dang xu ly: khoa nut, doi nhan, Esc va bam nen khong dong', async () => {
    const wrapper = mountDialog({ busyLabel: 'Đang xóa...' })
    await open(wrapper, { busy: true })
    const buttons = wrapper.findAll('button')
    expect(buttons.every((button) => button.attributes('disabled') !== undefined)).toBe(true)
    expect(buttons[1].text()).toBe('Đang xóa...')
    await wrapper.get('[role="alertdialog"]').trigger('keydown', { key: 'Escape' })
    await wrapper.get('.cd-layer').trigger('click')
    expect(wrapper.emitted('cancel')).toBeUndefined()
    wrapper.unmount()
  })

  it('tra focus ve phan tu truoc do khi dong', async () => {
    const trigger = document.createElement('button')
    document.body.appendChild(trigger)
    trigger.focus()
    const wrapper = mountDialog()
    await open(wrapper)
    expect(document.activeElement).not.toBe(trigger)
    await wrapper.setProps({ open: false })
    await nextTick()
    expect(document.activeElement).toBe(trigger)
    wrapper.unmount()
  })
})
