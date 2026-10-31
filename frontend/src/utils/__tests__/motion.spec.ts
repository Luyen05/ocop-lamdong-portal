// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'

import { prefersReducedMotion, scheduleWhenIdle, scrollBehavior, scrollToTop } from '@/utils/motion'

function mockReducedMotion(reduce: boolean): void {
  vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: reduce }))
}

describe('motion utils', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
    vi.restoreAllMocks()
  })

  it('cuộn mượt khi người dùng không bật giảm chuyển động', () => {
    mockReducedMotion(false)
    expect(prefersReducedMotion()).toBe(false)
    expect(scrollBehavior()).toBe('smooth')
  })

  it('cuộn tức thì khi người dùng bật giảm chuyển động', () => {
    mockReducedMotion(true)
    const scrollTo = vi.spyOn(window, 'scrollTo').mockImplementation(() => undefined)
    scrollToTop()
    expect(scrollTo).toHaveBeenCalledWith({ top: 0, behavior: 'auto' })
  })

  it('lên lịch việc không gấp khi trình duyệt hỗ trợ idle callback', () => {
    const requestIdleCallback = vi.fn().mockReturnValue(7)
    const cancelIdleCallback = vi.fn()
    vi.stubGlobal('requestIdleCallback', requestIdleCallback)
    vi.stubGlobal('cancelIdleCallback', cancelIdleCallback)
    const callback = vi.fn()

    const cancel = scheduleWhenIdle(callback, 900)
    cancel()

    expect(requestIdleCallback).toHaveBeenCalledWith(callback, { timeout: 900 })
    expect(cancelIdleCallback).toHaveBeenCalledWith(7)
    expect(callback).not.toHaveBeenCalled()
  })
})
