// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'

import { decideChunkRecovery, isChunkLoadError } from '../chunk-error'

function memoryStorage(initial: Record<string, string> = {}) {
  const data = { ...initial }
  return {
    data,
    getItem: (key: string) => data[key] ?? null,
    setItem: (key: string, value: string) => {
      data[key] = value
    },
  }
}

describe('isChunkLoadError', () => {
  it('nhận diện lỗi tải mã trang của Chrome, Firefox, Safari', () => {
    expect(isChunkLoadError(new TypeError('Failed to fetch dynamically imported module: /a.js'))).toBe(true)
    expect(isChunkLoadError(new Error('error loading dynamically imported module'))).toBe(true)
    expect(isChunkLoadError(new Error('Importing a module script failed.'))).toBe(true)
    expect(isChunkLoadError('Loading chunk 12 failed.')).toBe(true)
  })

  it('không nhầm với lỗi khác', () => {
    expect(isChunkLoadError(new Error('Network Error'))).toBe(false)
    expect(isChunkLoadError(null)).toBe(false)
    expect(isChunkLoadError(undefined)).toBe(false)
  })
})

describe('decideChunkRecovery', () => {
  it('tải lại một lần khi có mạng', () => {
    const storage = memoryStorage()
    expect(decideChunkRecovery(true, 100_000, storage)).toBe('reload')
    expect(storage.data.ocop_chunk_reload_at).toBe('100000')
  })

  it('chỉ báo người dùng khi vừa tải lại trong 60 giây (tránh vòng lặp)', () => {
    const storage = memoryStorage({ ocop_chunk_reload_at: '100000' })
    expect(decideChunkRecovery(true, 130_000, storage)).toBe('notify')
    expect(decideChunkRecovery(true, 161_000, storage)).toBe('reload')
  })

  it('chỉ báo người dùng khi ngoại tuyến', () => {
    expect(decideChunkRecovery(false, 1, memoryStorage())).toBe('notify')
  })

  it('chỉ báo người dùng khi không có hoặc không ghi được sessionStorage', () => {
    expect(decideChunkRecovery(true, 1, null)).toBe('notify')
    const broken = {
      getItem: () => null,
      setItem: () => {
        throw new Error('QuotaExceeded')
      },
    }
    expect(decideChunkRecovery(true, 1, broken)).toBe('notify')
  })
})
