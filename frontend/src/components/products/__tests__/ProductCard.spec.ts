// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ProductCard from '@/components/products/ProductCard.vue'
import type { ProductListItem } from '@/types/product'

const product: ProductListItem = {
  id: 1,
  name: 'Trà atiso Đà Lạt',
  slug: 'tra-atiso-da-lat',
  star: 3,
  price: 0,
  unit: 'hộp',
  description: 'Sản phẩm OCOP từ vùng nguyên liệu Lâm Đồng.',
  rating_avg: 0,
  vietgap_code: null,
  primary_image_url: 'https://example.com/broken.jpg',
  category: { id: 1, name: 'Thảo dược', slug: 'thao-duoc' },
  subject: { id: 1, name: 'Hợp tác xã Đà Lạt', district: 'phường Xuân Hương' },
  created_at: '2026-09-13T00:00:00Z',
}

describe('ProductCard', () => {
  it('hien thi gia lien he va khong con lien ket ban do minh hoa', async () => {
    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        },
      },
    })

    expect(wrapper.text()).toContain('Liên hệ')
    expect(wrapper.text()).toContain('Xem chi tiết')
    expect(wrapper.text()).not.toContain('Bản Đồ')

    await wrapper.get('img').trigger('error')
    expect(wrapper.find('.product-placeholder').exists()).toBe(true)
  })
})
