// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import AppIcon from '@/components/ui/AppIcon.vue'

describe('AppIcon', () => {
  it('hien thi icon trang tri an voi trinh doc man hinh', () => {
    const wrapper = mount(AppIcon, { props: { name: 'package', size: 18 } })

    expect(wrapper.attributes('aria-hidden')).toBe('true')
    expect(wrapper.attributes('width')).toBe('18')
    expect(wrapper.findAll('path').length).toBeGreaterThan(0)
  })

  it('hien thi nhan khi icon mang y nghia doc lap', () => {
    const wrapper = mount(AppIcon, { props: { name: 'user', label: 'Tài khoản' } })

    expect(wrapper.attributes('role')).toBe('img')
    expect(wrapper.attributes('aria-label')).toBe('Tài khoản')
  })
})
