// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import AppHeader from '@/components/AppHeader.vue'

const pushMock = vi.hoisted(() => vi.fn())

vi.mock('vue-router', () => ({
  useRoute: () => ({ fullPath: '/' }),
  useRouter: () => ({ push: pushMock }),
}))

describe('AppHeader', () => {
  beforeEach(() => pushMock.mockReset())

  it('mo o tim kiem responsive va chuyen den trang san pham', async () => {
    const wrapper = mount(AppHeader, {
      global: {
        stubs: {
          RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        },
      },
    })

    const toggle = wrapper.get('button[aria-controls="responsive-header-search"]')
    expect(toggle.attributes('aria-expanded')).toBe('false')

    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')

    await wrapper.get('.responsive-search input').setValue('  cà phê  ')
    await wrapper.get('.responsive-search').trigger('submit')
    await flushPromises()

    expect(pushMock).toHaveBeenCalledWith({ name: 'products', query: { search: 'cà phê' } })
    wrapper.unmount()
  })
})
