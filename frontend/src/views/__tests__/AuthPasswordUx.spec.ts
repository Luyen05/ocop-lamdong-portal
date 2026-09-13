// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import LoginView from '@/views/LoginView.vue'
import RegisterView from '@/views/RegisterView.vue'

vi.mock('vue-router', () => ({
  useRoute: () => ({ query: {} }),
  useRouter: () => ({ push: vi.fn() }),
}))

const globalOptions = {
  stubs: {
    AuthLayout: { template: '<div><slot /></div>' },
    RouterLink: { template: '<a><slot /></a>' },
  },
}

describe('trai nghiem mat khau', () => {
  it('cho phep hien va an mat khau dang nhap', async () => {
    const wrapper = mount(LoginView, { global: globalOptions })
    const input = wrapper.get('#login-password')

    expect(input.attributes('type')).toBe('password')
    await wrapper.get('button[aria-label="Hiện mật khẩu"]').trigger('click')
    expect(input.attributes('type')).toBe('text')
    expect(wrapper.get('button[aria-label="Ẩn mật khẩu"]').attributes('aria-pressed')).toBe('true')
  })

  it('hien thi do manh va loi xac nhan ngay khi dang ky', async () => {
    const wrapper = mount(RegisterView, { global: globalOptions })

    await wrapper.get('#register-password').setValue('Matkhau1!')
    expect(wrapper.get('#password-strength').text()).toContain('Tốt')

    await wrapper.get('#register-confirmation').setValue('Khongkhop1!')
    expect(wrapper.get('#confirmation-feedback').text()).toContain('chưa khớp')
    expect(wrapper.get('#register-confirmation').attributes('aria-invalid')).toBe('true')
  })
})
