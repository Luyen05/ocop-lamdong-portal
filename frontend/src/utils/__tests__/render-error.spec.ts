import { describe, expect, it } from 'vitest'

import { isFatalRenderError } from '../render-error'

describe('isFatalRenderError', () => {
  it('lỗi khi dựng giao diện là nghiêm trọng', () => {
    expect(isFatalRenderError('render function')).toBe(true)
    expect(isFatalRenderError('setup function')).toBe(true)
  })

  it('lỗi sự kiện, watcher, tác vụ nền chỉ ghi nhật ký', () => {
    expect(isFatalRenderError('native event handler')).toBe(false)
    expect(isFatalRenderError('watcher callback')).toBe(false)
    expect(isFatalRenderError('scheduler flush')).toBe(false)
  })
})
