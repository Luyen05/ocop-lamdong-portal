// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import ProductCard from '@/components/products/ProductCard.vue'
import type { ProductListItem } from '@/types/product'

enableAutoUnmount(afterEach)

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
  it('hien thi thong tin cot loi trong mot lien ket duy nhat', async () => {
    const wrapper = mount(ProductCard, {
      props: { product },
      global: {
        stubs: {
          RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        },
      },
    })

    expect(wrapper.text()).toContain('Liên hệ')
    expect(wrapper.text()).toContain('Thảo dược')
    expect(wrapper.text()).not.toContain(product.description)
    expect(wrapper.text()).not.toContain('Bản Đồ')
    expect(wrapper.findAll('a')).toHaveLength(1)

    await wrapper.get('img').trigger('error')
    expect(wrapper.find('.product-placeholder').exists()).toBe(true)
  })
})

describe('ProductCard link accessibility', () => {
  it.each([product.primary_image_url, null])(
    'keeps an explicit product name and destination with image %s', async (imageUrl) => {
      const router = createRouter({
        history: createMemoryHistory(),
        routes: [
          { path: '/', component: { template: '<div />' } },
          { path: '/san-pham/:slug', component: { template: '<div />' } },
        ],
      })
      await router.push('/')
      await router.isReady()
      const wrapper = mount(ProductCard, {
        props: { product: { ...product, primary_image_url: imageUrl } },
        global: { plugins: [router] },
      })
      const link = wrapper.get('a')
      expect(wrapper.findAll('a')).toHaveLength(1)
      expect(link.attributes('aria-label')).toBe(product.name)
      expect(link.attributes('href')).toBe(`/san-pham/${product.slug}`)

      if (imageUrl) await wrapper.get('img').trigger('error')
      expect(wrapper.find('.product-placeholder').exists()).toBe(true)
      expect(link.attributes('aria-label')).toBe(product.name)

      const nextProduct = { ...product, id: 2, name: 'Product B', slug: 'product-b' }
      await wrapper.setProps({ product: nextProduct })
      expect(link.attributes('aria-label')).toBe(nextProduct.name)
      expect(wrapper.get('h2').text()).toBe(nextProduct.name)
      expect(link.attributes('href')).toBe(`/san-pham/${nextProduct.slug}`)
      await link.trigger('click')
      await flushPromises()
      expect(router.currentRoute.value.params.slug).toBe(nextProduct.slug)
    },
  )
})
