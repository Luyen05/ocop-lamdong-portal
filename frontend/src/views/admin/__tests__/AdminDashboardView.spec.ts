// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { describe, expect, it, vi } from 'vitest'

import { getAdminDashboard } from '@/services/admin'
import AdminDashboardView from '@/views/admin/AdminDashboardView.vue'

vi.mock('@/services/admin', () => ({ getAdminDashboard: vi.fn() }))

describe('AdminDashboardView', () => {
  it('hien thi thong ke lay tu API', async () => {
    vi.mocked(getAdminDashboard).mockResolvedValue({
      total_products: 60,
      approved_products: 45,
      pending_products: 5,
      pending_subject_applications: 3,
      pending_change_requests: 2,
      products_missing_decision: 8,
    })

    const wrapper = mount(AdminDashboardView, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('60')
    expect(wrapper.text()).toContain('45')
    expect(wrapper.text()).toContain('5 hồ sơ')
    expect(wrapper.text()).toContain('8 hồ sơ')
    expect(wrapper.text()).toContain('Số liệu trực tiếp từ database')
  })
})
