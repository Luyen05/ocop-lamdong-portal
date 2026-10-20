// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'

import { prefersReducedMotion, scrollBehavior, scrollToTop } from '@/utils/motion'

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
})
