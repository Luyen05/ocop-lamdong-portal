// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import ServerErrorView from '../ServerErrorView.vue'

describe('ServerErrorView', () => {
  it('có tiêu đề, nút tải lại và lối về trang chủ', () => {
    const wrapper = mount(ServerErrorView, { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } })
    expect(wrapper.find('h1').text()).toBe('Đã xảy ra sự cố')
    expect(wrapper.text()).toContain('Tải lại trang')
    expect(wrapper.text()).toContain('Về trang chủ')
  })
})
