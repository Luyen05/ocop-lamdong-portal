// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import { heroPhoto } from '@/constants/photos'

import PhotoBanner from '../PhotoBanner.vue'

describe('PhotoBanner', () => {
  it('hiện ảnh trang trí và nội dung truyền vào', () => {
    const wrapper = mount(PhotoBanner, { props: { photo: heroPhoto }, slots: { default: '<h1>Tiêu đề</h1>' } })
    const image = wrapper.get('img.banner-photo')
    expect(image.attributes('src')).toBe(heroPhoto.src)
    expect(image.attributes('alt')).toBe('')
    expect(wrapper.get('h1').text()).toBe('Tiêu đề')
  })

  it('ảnh lỗi thì bỏ ảnh nhưng vẫn giữ nội dung', async () => {
    const wrapper = mount(PhotoBanner, { props: { photo: heroPhoto }, slots: { default: '<h1>Tiêu đề</h1>' } })
    await wrapper.get('img').trigger('error')
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.get('h1').text()).toBe('Tiêu đề')
  })
})
