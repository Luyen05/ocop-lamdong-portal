// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import HomeHero from '@/components/home/HomeHero.vue'

const { push } = vi.hoisted(() => ({ push: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

describe('HomeHero', () => {
  it('chuyen tu khoa tim kiem sang trang san pham', async () => {
    const wrapper = mount(HomeHero)
    await wrapper.get('input[type="search"]').setValue('  cà phê Cầu Đất  ')
    await wrapper.get('form').trigger('submit')

    expect(push).toHaveBeenCalledWith({
      name: 'products',
      query: { search: 'cà phê Cầu Đất' },
    })
  })
})
