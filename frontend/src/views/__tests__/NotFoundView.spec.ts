// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import NotFoundView from '@/views/NotFoundView.vue'

describe('NotFoundView', () => {
  it('huong nguoi dung ve cac trang cong khai hop le', () => {
    const wrapper = mount(NotFoundView, {
      global: {
        stubs: {
          RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' },
        },
      },
    })

    expect(wrapper.get('h1').text()).toBe('Không tìm thấy trang')
    expect(wrapper.findAll('a').map((link) => link.attributes('href'))).toEqual([
      '/',
      '/san-pham',
    ])
  })
})
