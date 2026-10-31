// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import ForbiddenView from '@/views/ForbiddenView.vue'

const { currentUser } = vi.hoisted(() => ({
  currentUser: { value: null as { role: 'admin' | 'subject' | 'user' } | null },
}))

vi.mock('@/stores/auth', () => ({
  authStore: {
    currentUser,
    isAuthenticated: { get value() { return currentUser.value !== null } },
  },
}))

const RouterLinkStub = { props: ['to'], template: '<a :href="to"><slot /></a>' }

function mountView() {
  return mount(ForbiddenView, { global: { stubs: { RouterLink: RouterLinkStub } } })
}

describe('ForbiddenView', () => {
  beforeEach(() => {
    currentUser.value = null
  })

  it('nguoi dung thuong co loi Dang ky lam chu the toi /dang-ky-chu-the', () => {
    currentUser.value = { role: 'user' }
    const wrapper = mountView()
    const register = wrapper.findAll('a').find((link) => link.text() === 'Đăng ký làm chủ thể')
    expect(register?.attributes('href')).toBe('/dang-ky-chu-the')
    expect(wrapper.text()).toContain('hợp tác xã, doanh nghiệp')
    expect(wrapper.text()).toContain('Về trang chủ')
  })

  it('chu the va quan tri vien khong thay loi dang ky', () => {
    for (const role of ['subject', 'admin'] as const) {
      currentUser.value = { role }
      expect(mountView().text()).not.toContain('Đăng ký làm chủ thể')
    }
  })

  it('khach chi thay Ve trang chu va Dang nhap', () => {
    const wrapper = mountView()
    expect(wrapper.text()).not.toContain('Đăng ký làm chủ thể')
    expect(wrapper.findAll('a').map((link) => link.text())).toEqual(['Về trang chủ', 'Đăng nhập'])
  })
})
