// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import ScrollToTop from '@/components/ui/ScrollToTop.vue'

describe('ScrollToTop', () => {
  afterEach(() => vi.restoreAllMocks())

  it('chi hien sau khi cuon va dua nguoi dung ve dau trang', async () => {
    Object.defineProperty(window, 'scrollY', { configurable: true, value: 0, writable: true })
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
    const wrapper = mount(ScrollToTop)

    expect(wrapper.find('button').exists()).toBe(false)
    window.scrollY = 500
    window.dispatchEvent(new Event('scroll'))
    await nextTick()

    const button = wrapper.get('button[aria-label="Trở về đầu trang"]')
    await button.trigger('click')
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'smooth' })
    wrapper.unmount()
  })
})
