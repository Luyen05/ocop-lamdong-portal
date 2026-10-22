// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

const push = vi.fn()
const back = vi.fn()
const route = { path: '/trang-khong-co', fullPath: '/trang-khong-co?x=1' }

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => ({ push, back }),
}))

import NotFoundView from '@/views/NotFoundView.vue'

const stubs = { RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } }

describe('NotFoundView', () => {
  it('huong nguoi dung ve cac trang cong khai hop le va hien lai dia chi da go', () => {
    const wrapper = mount(NotFoundView, { global: { stubs } })

    expect(wrapper.get('h1').text()).toBe('Không tìm thấy trang')
    expect(wrapper.findAll('a').map((link) => link.attributes('href'))).toEqual(['/', '/san-pham'])
    expect(wrapper.get('[data-testid="requested-path"]').text()).toBe('/trang-khong-co?x=1')
  })

  it('tim san pham tu o tim kiem va quay lai trang truoc', async () => {
    const wrapper = mount(NotFoundView, { global: { stubs } })

    await wrapper.get('input[type="search"]').setValue('  atiso ')
    await wrapper.get('form').trigger('submit')
    expect(push).toHaveBeenCalledWith({ name: 'products', query: { search: 'atiso' } })

    push.mockClear()
    await wrapper.get('input[type="search"]').setValue('   ')
    await wrapper.get('form').trigger('submit')
    expect(push).not.toHaveBeenCalled()

    window.history.pushState({}, '', '/a')
    window.history.pushState({}, '', '/b')
    const remounted = mount(NotFoundView, { global: { stubs } })
    await remounted.findAll('button').find((b) => b.text().includes('Quay lại'))?.trigger('click')
    expect(back).toHaveBeenCalled()
  })
})
