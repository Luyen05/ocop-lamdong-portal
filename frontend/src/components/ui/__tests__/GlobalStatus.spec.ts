// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { pageStatus } from '@/stores/page-status'

const push = vi.fn()
vi.mock('vue-router', () => ({ useRouter: () => ({ push }) }))

import GlobalStatus from '../GlobalStatus.vue'

describe('GlobalStatus', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    push.mockClear()
  })

  afterEach(() => {
    pageStatus.setOnline(true)
    pageStatus.dismissNavigationFailure()
    vi.useRealTimers()
  })

  it('báo ngoại tuyến rồi báo đã kết nối lại trong 3 giây', async () => {
    const wrapper = mount(GlobalStatus)
    window.dispatchEvent(new Event('offline'))
    await nextTick()
    expect(wrapper.find('[data-testid="offline-notice"]').exists()).toBe(true)

    window.dispatchEvent(new Event('online'))
    await nextTick()
    expect(wrapper.find('[data-testid="offline-notice"]').exists()).toBe(false)
    expect(wrapper.find('[data-testid="online-notice"]').text()).toContain('Đã kết nối lại')

    vi.advanceTimersByTime(3100)
    await nextTick()
    expect(wrapper.find('[data-testid="online-notice"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('hiện lỗi mở trang và thử lại bằng cách điều hướng tới trang đích', async () => {
    const wrapper = mount(GlobalStatus)
    pageStatus.reportNavigationFailure('/ban-do')
    await nextTick()
    const box = wrapper.find('[data-testid="navigation-failure"]')
    expect(box.exists()).toBe(true)
    await box.find('.global-status__action').trigger('click')
    expect(push).toHaveBeenCalledWith('/ban-do')
    expect(wrapper.find('[data-testid="navigation-failure"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('đóng thông báo lỗi mà không điều hướng', async () => {
    const wrapper = mount(GlobalStatus)
    pageStatus.reportNavigationFailure('/ban-do')
    await nextTick()
    await wrapper.find('.global-status__close').trigger('click')
    expect(push).not.toHaveBeenCalled()
    expect(wrapper.find('[data-testid="navigation-failure"]').exists()).toBe(false)
    wrapper.unmount()
  })
})
