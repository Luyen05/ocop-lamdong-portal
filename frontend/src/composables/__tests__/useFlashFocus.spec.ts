// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { defineComponent, nextTick, ref } from 'vue'

import { useFlashFocus } from '@/composables/useFlashFocus'

const Host = defineComponent({
  setup() {
    const error = ref('')
    const success = ref('')
    const { revealFlash } = useFlashFocus({ error, success })
    return { error, success, revealFlash }
  },
  template: `<div>
    <div v-if="error" data-flash="error" role="alert">{{ error }}</div>
    <div v-if="success" data-flash="success" role="status">{{ success }}</div>
  </div>`,
})

afterEach(() => {
  vi.restoreAllMocks()
  document.body.innerHTML = ''
})

describe('useFlashFocus', () => {
  it('cuon vao giua khung nhin va focus khi co thong bao loi moi', async () => {
    const scroll = vi.fn()
    ;(Element.prototype as unknown as { scrollIntoView: unknown }).scrollIntoView = scroll
    const wrapper = mount(Host, { attachTo: document.body })
    ;(wrapper.vm as unknown as { error: string }).error = 'Không lưu được.'
    await nextTick()
    await nextTick()
    const alert = wrapper.get('[data-flash="error"]').element as HTMLElement
    expect(scroll).toHaveBeenCalledWith({ block: 'center', behavior: expect.any(String) })
    expect(alert.getAttribute('tabindex')).toBe('-1')
    expect(document.activeElement).toBe(alert)
    wrapper.unmount()
  })

  it('ton trong prefers-reduced-motion: khong cuon muot', async () => {
    const scroll = vi.fn()
    ;(Element.prototype as unknown as { scrollIntoView: unknown }).scrollIntoView = scroll
    window.matchMedia = vi.fn().mockReturnValue({ matches: true }) as unknown as typeof window.matchMedia
    const wrapper = mount(Host, { attachTo: document.body })
    ;(wrapper.vm as unknown as { success: string }).success = 'Đã lưu.'
    await nextTick()
    await nextTick()
    expect(scroll).toHaveBeenCalledWith({ block: 'center', behavior: 'auto' })
    expect(document.activeElement).toBe(wrapper.get('[data-flash="success"]').element)
    wrapper.unmount()
  })

  it('revealFlash thu cong dung khi dat lai dung chuoi cu', async () => {
    const scroll = vi.fn()
    ;(Element.prototype as unknown as { scrollIntoView: unknown }).scrollIntoView = scroll
    const wrapper = mount(Host, { attachTo: document.body })
    const vm = wrapper.vm as unknown as { error: string; revealFlash: (kind?: 'error' | 'success') => Promise<void> }
    vm.error = 'Thiếu tên.'
    await nextTick()
    await nextTick()
    scroll.mockClear()
    await vm.revealFlash('error')
    expect(scroll).toHaveBeenCalledTimes(1)
    wrapper.unmount()
  })
})
