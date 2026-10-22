// @vitest-environment jsdom
import { enableAutoUnmount, mount } from '@vue/test-utils'
import { afterEach, describe, expect, it } from 'vitest'

import PresentationGallery from '@/components/products/PresentationGallery.vue'

enableAutoUnmount(afterEach)

const images = [
  { id: 1, image_url: 'https://example.com/a.jpg', is_primary: true, sort_order: 0 },
  { id: 2, image_url: 'https://example.com/b.jpg', is_primary: false, sort_order: 1 },
  { id: 3, image_url: 'https://example.com/c.jpg', is_primary: false, sort_order: 2 },
]

function mainSrc(wrapper: ReturnType<typeof mount>): string | undefined {
  return wrapper.find('.main-image img').attributes('src')
}

describe('PresentationGallery', () => {
  it('anh chinh loi thi chuyen sang anh hop le ke tiep', async () => {
    const wrapper = mount(PresentationGallery, { props: { images, name: 'Trà' } })
    expect(mainSrc(wrapper)).toBe('https://example.com/a.jpg')
    await wrapper.get('.main-image img').trigger('error')
    expect(mainSrc(wrapper)).toBe('https://example.com/b.jpg')
    await wrapper.get('.main-image img').trigger('error')
    expect(mainSrc(wrapper)).toBe('https://example.com/c.jpg')
    expect(wrapper.find('.image-placeholder').exists()).toBe(false)
  })

  it('chi hien khung giu cho khi tat ca anh deu loi', async () => {
    const wrapper = mount(PresentationGallery, { props: { images: images.slice(0, 2), name: 'Trà' } })
    await wrapper.get('.main-image img').trigger('error')
    await wrapper.get('.main-image img').trigger('error')
    expect(wrapper.find('.main-image img').exists()).toBe(false)
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
  })

  it('anh dang chon bi loi thi chuyen sang anh khac, anh nho loi bi an', async () => {
    const wrapper = mount(PresentationGallery, { props: { images, name: 'Trà' } })
    await wrapper.findAll('.thumbnail')[1].trigger('click')
    expect(mainSrc(wrapper)).toBe('https://example.com/b.jpg')
    await wrapper.get('.main-image img').trigger('error')
    expect(mainSrc(wrapper)).toBe('https://example.com/a.jpg')
    expect(wrapper.findAll('.thumbnail')[1].isVisible()).toBe(false)
  })

  it('dat lai trang thai loi khi doi danh sach anh', async () => {
    const wrapper = mount(PresentationGallery, { props: { images: images.slice(0, 1), name: 'Trà' } })
    await wrapper.get('.main-image img').trigger('error')
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
    await wrapper.setProps({ images: [images[1]], name: 'Cà phê' })
    expect(mainSrc(wrapper)).toBe('https://example.com/b.jpg')
  })
})
