// @vitest-environment jsdom
import { describe, expect, it } from 'vitest'

import router from '@/router'

describe('tham số mã số trong đường dẫn khu chủ thể', () => {
  it.each([
    ['/chu-the/san-pham/12/chinh-sua', 'subject-product-edit'],
    ['/chu-the/yeu-cau/7/chinh-sua', 'subject-product-request-edit'],
  ])('%s mở đúng trang', (path, name) => {
    expect(router.resolve(path).name).toBe(name)
  })

  it.each([
    '/chu-the/san-pham/abc/chinh-sua',
    '/chu-the/san-pham/12abc/chinh-sua',
    '/chu-the/yeu-cau/abc/chinh-sua',
  ])('%s không phải mã số thì về trang không tìm thấy', (path) => {
    expect(router.resolve(path).name).toBe('not-found')
  })

  it('trang thêm sản phẩm không bị nhầm với trang chỉnh sửa', () => {
    expect(router.resolve('/chu-the/san-pham/them').name).toBe('subject-product-create')
  })
})
