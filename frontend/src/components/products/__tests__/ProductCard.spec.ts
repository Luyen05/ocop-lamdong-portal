// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ProductCard from '@/components/products/ProductCard.vue'
import type { ProductListItem } from '@/types/product'

const product: ProductListItem = {
  id: 1,
  name: 'Test product',
  slug: 'test-product',
  star: 5,
  price: 100000,
  unit: 'box',
  description: 'Description',
  rating_avg: 4.5,
  primary_image_url: 'https://example.com/product.jpg',
  category: { id: 1, name: 'Food', slug: 'food' },
  subject: { id: 1, name: 'Producer', district: 'Da Lat' },
  created_at: '2026-01-01T00:00:00Z',
}

function mountCard(primary_image_url: string | null = product.primary_image_url) {
  return mount(ProductCard, {
    props: { product: { ...product, primary_image_url } },
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
  })
}

describe('ProductCard', () => {
  it('does not infer VietGAP certification from five OCOP stars', () => {
    expect(mountCard().text()).not.toContain('VietGAP')
  })

  it.each([null, ''])('shows the OCOP placeholder for a missing image URL (%s)', (url) => {
    const wrapper = mountCard(url)
    expect(wrapper.find('.product-media img').exists()).toBe(false)
    expect(wrapper.find('.product-placeholder').text()).toContain('OCOP')
  })

  it('shows the same placeholder after an image load error', async () => {
    const wrapper = mountCard()
    await wrapper.find('.product-media img').trigger('error')
    expect(wrapper.find('.product-media img').exists()).toBe(false)
    expect(wrapper.find('.product-placeholder').text()).toContain('OCOP')
  })

  it('renders a valid image with the product name as alt text', () => {
    const wrapper = mountCard()
    const image = wrapper.find('.product-media img')
    expect(image.attributes('src')).toBe(product.primary_image_url)
    expect(image.attributes('alt')).toBe(product.name)
    expect(wrapper.find('.product-placeholder').exists()).toBe(false)
  })
})
