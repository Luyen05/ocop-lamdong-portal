// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import MobileTabBar from '@/components/MobileTabBar.vue'

vi.mock('vue-router', () => ({ useRoute: () => ({ path: '/san-pham/tra-atiso' }) }))

describe('MobileTabBar', () => {
  it('hien thi nam diem den va danh dau body de chua cho', () => {
    const wrapper = mount(MobileTabBar, {
      global: { stubs: { RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } } },
    })
    const links = wrapper.findAll('a')
    expect(links.map((link) => link.attributes('href'))).toEqual(['/', '/san-pham', '/diem-du-lich', '/ban-do', '/tin-tuc'])
    expect(document.body.classList.contains('has-tabbar')).toBe(true)
    expect(wrapper.findAll('.is-active').map((link) => link.attributes('href'))).toEqual(['/san-pham'])
    wrapper.unmount()
    expect(document.body.classList.contains('has-tabbar')).toBe(false)
  })
})
