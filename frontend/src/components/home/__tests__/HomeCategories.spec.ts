// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import HomeCategories from '@/components/home/HomeCategories.vue'
import { getCategories } from '@/services/categories'

vi.mock('@/services/categories', () => ({
  getCategories: vi.fn(),
}))

describe('HomeCategories', () => {
  it('hien thi toi da nam danh muc tu API', async () => {
    vi.mocked(getCategories).mockResolvedValue({
      items: Array.from({ length: 6 }, (_, index) => ({
        id: index + 1,
        name: `Danh mục ${index + 1}`,
        slug: `danh-muc-${index + 1}`,
        description: null,
        icon: null,
      })),
      page: 1,
      page_size: 100,
      total: 6,
    })

    const wrapper = mount(HomeCategories, {
      global: {
        stubs: {
          RouterLink: { props: ['to'], template: '<a><slot /></a>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.findAll('.category-card')).toHaveLength(5)
    expect(wrapper.text()).toContain('Danh mục 1')
    expect(wrapper.text()).not.toContain('Danh mục 6')
  })

  it('hien thi trang thai thu lai khi API loi', async () => {
    vi.mocked(getCategories).mockRejectedValue(new Error('network'))
    const wrapper = mount(HomeCategories, {
      global: {
        stubs: {
          RouterLink: { template: '<a><slot /></a>' },
        },
      },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Chưa thể tải danh mục')
    expect(wrapper.find('button').exists()).toBe(true)
  })
})
