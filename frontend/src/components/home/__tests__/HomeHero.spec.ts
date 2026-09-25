// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import HomeHero from '@/components/home/HomeHero.vue'

const { push } = vi.hoisted(() => ({ push: vi.fn() }))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push }),
}))

const stubs = { global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } } }

describe('HomeHero', () => {
  it('chuyen tu khoa tim kiem sang trang san pham', async () => {
    push.mockClear()
    const wrapper = mount(HomeHero, stubs)
    await wrapper.get('input[type="search"]').setValue('  cà phê Cầu Đất  ')
    await wrapper.get('form').trigger('submit')

    expect(push).toHaveBeenCalledWith({
      name: 'products',
      query: { search: 'cà phê Cầu Đất' },
    })
  })

  it('che do diem du lich chuyen tu khoa sang trang diem du lich', async () => {
    push.mockClear()
    const wrapper = mount(HomeHero, stubs)
    const options = wrapper.findAll('[role="radio"]')
    expect(options).toHaveLength(2)
    expect(options[0].attributes('aria-checked')).toBe('true')

    await options[1].trigger('click')
    expect(options[1].attributes('aria-checked')).toBe('true')
    expect(wrapper.get('input[type="search"]').attributes('placeholder')).toContain('Đồi chè')

    await wrapper.get('input[type="search"]').setValue(' vườn dâu ')
    await wrapper.get('form').trigger('submit')
    expect(push).toHaveBeenCalledWith({ name: 'locations', query: { search: 'vườn dâu' } })
  })

  it('phim mui ten chuyen lua chon trong nhom che do tim', async () => {
    const wrapper = mount(HomeHero, { ...stubs, attachTo: document.body })
    const options = wrapper.findAll('[role="radio"]')
    await options[0].trigger('keydown', { key: 'ArrowRight' })
    expect(options[1].attributes('aria-checked')).toBe('true')
    expect(options[1].attributes('tabindex')).toBe('0')
    expect(options[0].attributes('tabindex')).toBe('-1')
    wrapper.unmount()
  })
})
