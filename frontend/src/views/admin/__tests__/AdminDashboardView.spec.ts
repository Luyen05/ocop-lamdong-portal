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
    // Hàng đợi việc cần làm: 5 sản phẩm + 2 yêu cầu sửa + 3 hồ sơ chủ thể.
    expect(wrapper.text()).toContain('Có 10 việc đang chờ bạn xử lý')
    expect(wrapper.text()).toContain('Sản phẩm mới chờ duyệt')
    expect(wrapper.text()).toContain('75% tổng số sản phẩm')
    // Sản phẩm thiếu số quyết định vẫn được hiển thị.
    expect(wrapper.text()).toContain('Thiếu số quyết định công nhận8')
  })
})
