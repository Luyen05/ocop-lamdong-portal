// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest'
import type { RouteLocationNormalized } from 'vue-router'

import { resolveScroll } from '@/router/scroll'

function location(name: string, path: string, hash = ''): RouteLocationNormalized {
  return { name, path, hash, query: {}, params: {}, fullPath: path + hash, matched: [], meta: {}, redirectedFrom: undefined } as RouteLocationNormalized
}

const run = (to: RouteLocationNormalized, from: RouteLocationNormalized, saved: { left: number; top: number } | null = null) =>
  resolveScroll(to, from, saved) as unknown

describe('router scroll', () => {
  afterEach(() => vi.unstubAllGlobals())

  it('Back/Forward khoi phuc vi tri cu, ke ca tren trang ban do', () => {
    const saved = { left: 0, top: 640 }
    expect(run(location('products', '/san-pham'), location('home', '/'), saved)).toEqual(saved)
    expect(run(location('map', '/ban-do'), location('map', '/ban-do'), saved)).toEqual(saved)
  })

  it('doi trang thi len dau trang', () => {
    expect(run(location('map', '/ban-do'), location('home', '/'))).toEqual({ top: 0 })
    expect(run(location('products', '/san-pham'), location('product-detail', '/san-pham/a'))).toEqual({ top: 0 })
  })

  it('trang ban do chi doi query (chon diem, loc) thi khong dat lai cuon', () => {
    expect(run(location('map', '/ban-do'), location('map', '/ban-do'))).toBe(false)
  })

  it('cac trang khac doi bo loc van len dau trang (danh sach san pham, tin tuc...)', () => {
    expect(run(location('products', '/san-pham'), location('products', '/san-pham'))).toEqual({ top: 0 })
    expect(run(location('news', '/tin-tuc'), location('news', '/tin-tuc'))).toEqual({ top: 0 })
  })

  it('co #neo thi cuon toi neo, mem tru khi giam chuyen dong', () => {
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: false }))
    expect(run(location('map', '/ban-do', '#a'), location('map', '/ban-do'))).toEqual({ el: '#a', behavior: 'smooth' })
    vi.stubGlobal('matchMedia', vi.fn().mockReturnValue({ matches: true }))
    expect(run(location('home', '/', '#a'), location('home', '/'))).toEqual({ el: '#a', behavior: 'auto' })
  })
})
