import { describe, expect, it } from 'vitest'

import { documentTitleFor, SITE_NAME } from '@/router/titles'

describe('documentTitleFor', () => {
  it('đặt tên trang trước tên cổng thông tin', () => {
    expect(documentTitleFor('login')).toBe(`Đăng nhập | ${SITE_NAME}`)
    expect(documentTitleFor('admin-products', 'Duyệt sản phẩm')).toBe(`Duyệt sản phẩm | ${SITE_NAME}`)
  })

  it('trang chủ có mô tả, trang lạ chỉ có tên cổng', () => {
    expect(documentTitleFor('home')).toContain('Nông sản OCOP')
    expect(documentTitleFor(undefined)).toBe(SITE_NAME)
  })
})
