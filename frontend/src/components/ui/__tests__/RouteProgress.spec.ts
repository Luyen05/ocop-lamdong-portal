// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { nextTick } from 'vue'

import { pageStatus } from '@/stores/page-status'

import RouteProgress from '../RouteProgress.vue'

describe('RouteProgress', () => {
  beforeEach(() => {
    vi.useFakeTimers()
  })

  afterEach(() => {
    pageStatus.finishNavigation()
    vi.useRealTimers()
  })

  it('không hiện thanh khi việc xong trong dưới 150 ms', async () => {
    const wrapper = mount(RouteProgress)
    pageStatus.startNavigation()
    await nextTick()
    vi.advanceTimersByTime(100)
    pageStatus.finishNavigation()
    await nextTick()
    vi.advanceTimersByTime(500)
    await nextTick()
    expect(wrapper.find('[data-testid="route-progress"]').exists()).toBe(false)
    wrapper.unmount()
  })

  it('hiện thanh, thông báo cho trình đọc màn hình rồi ẩn khi xong', async () => {
    const wrapper = mount(RouteProgress)
    pageStatus.startNavigation()
    await nextTick()
    vi.advanceTimersByTime(200)
    await nextTick()
    expect(wrapper.find('[data-testid="route-progress"]').exists()).toBe(true)
    expect(wrapper.find('[role="status"]').text()).toBe('Đang tải trang…')

    pageStatus.finishNavigation()
    await nextTick()
    expect(wrapper.find('[data-testid="route-progress"]').classes()).toContain('is-finishing')
    vi.advanceTimersByTime(400)
    await nextTick()
    expect(wrapper.find('[data-testid="route-progress"]').exists()).toBe(false)
    wrapper.unmount()
  })
})
