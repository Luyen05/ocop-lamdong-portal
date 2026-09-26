// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getAdminDashboard, getAdminStatistics, type AdminStatistics } from '@/services/admin'
import AdminDashboardView from '@/views/admin/AdminDashboardView.vue'

vi.mock('@/services/admin', () => ({ getAdminDashboard: vi.fn(), getAdminStatistics: vi.fn() }))

// Biểu đồ được kiểm thử riêng trong StatChart.spec; ở đây chỉ cần tiêu đề và số liệu truyền vào.
const StatChartStub = {
  props: ['title', 'description', 'items', 'summary'],
  template: '<article class="stat-chart-stub"><h3>{{ title }}</h3><p>{{ description }}</p><span class="summary">{{ summary }}</span><slot name="lead" /><slot /></article>',
}

const statistics: AdminStatistics = {
  generated_at: '2026-09-26T10:00:00+07:00',
  products_by_status: [
    { key: 'draft', count: 1 },
    { key: 'approved', count: 73 },
    { key: 'pending', count: 1 },
    { key: 'needs_revision', count: 1 },
    { key: 'rejected', count: 1 },
  ],
  approved_by_star: [
    { star: 3, count: 46 },
    { star: 4, count: 26 },
    { star: 5, count: 1 },
  ],
  approved_by_category: [
    { id: 1, name: 'Thực phẩm', slug: 'thuc-pham', count: 42 },
    { id: 2, name: 'Đồ uống', slug: 'do-uong', count: 20 },
    { id: 5, name: 'Sinh vật cảnh', slug: 'sinh-vat-canh', count: 0 },
  ],
  approved_by_district: [
    { district: 'xã Đức Trọng', count: 13 },
    { district: 'Đà Lạt', count: 10 },
  ],
  approved_by_month: [
    { month: '2026-08', count: 9 },
    { month: '2026-09', count: 11 },
  ],
  approved_without_review_date: 4,
  certificates: { expired: 1, expiring_soon: 0, expiring_window_days: 90, by_year: [{ year: 2025, count: 50 }] },
  top_viewed_products: [],
  subjects_by_status: [
    { key: 'approved', count: 35 },
    { key: 'pending', count: 1 },
  ],
  locations_by_type: [
    { key: 'tea_coffee_farm', count: 3 },
    { key: 'dairy_farm', count: 1 },
  ],
}

function mountView() {
  return mount(AdminDashboardView, {
    global: { stubs: { RouterLink: { template: '<a><slot /></a>' }, StatChart: StatChartStub } },
  })
}

describe('AdminDashboardView', () => {
  beforeEach(() => {
    vi.mocked(getAdminDashboard).mockResolvedValue({
      total_products: 60,
      approved_products: 45,
      pending_products: 5,
      pending_subject_applications: 3,
      pending_change_requests: 2,
      products_missing_decision: 8,
    })
    vi.mocked(getAdminStatistics).mockResolvedValue(statistics)
  })

  it('hien thi hang doi viec va so lieu chinh', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('60')
    // Hàng đợi việc cần làm: 5 sản phẩm + 2 yêu cầu sửa + 3 hồ sơ chủ thể.
    expect(wrapper.text()).toContain('Có 10 việc đang chờ bạn xử lý')
    expect(wrapper.text()).toContain('Sản phẩm mới chờ duyệt')
    expect(wrapper.text()).toContain('45 đang công khai, 75% tổng số sản phẩm')
    expect(wrapper.text()).toContain('Thiếu số quyết định công nhận8')
    // Số chủ thể và điểm du lịch lấy từ API thống kê.
    expect(wrapper.text()).toContain('Chủ thể / HTX đã duyệt35')
    expect(wrapper.text()).toContain('Điểm du lịch nông nghiệp4')
  })

  it('hien thi cac bieu do thong ke voi nhan tieng Viet', async () => {
    const wrapper = mountView()
    await flushPromises()

    const titles = wrapper.findAll('.stat-chart-stub h3').map((node) => node.text())
    expect(titles).toEqual([
      'Trạng thái hồ sơ sản phẩm',
      'Hạng sao OCOP',
      'Theo nhóm sản phẩm',
      '2 xã, phường có nhiều sản phẩm nhất',
      'Sản phẩm được duyệt theo tháng',
      'Giấy chứng nhận OCOP',
      'Điểm du lịch theo loại hình',
    ])
    const text = wrapper.text()
    // Trạng thái sắp theo thứ tự cố định, đã duyệt đứng đầu, kèm tỉ lệ.
    expect(text).toContain('94,8%')
    expect(text).toContain('Đã duyệt: 73 hồ sơ; Chờ duyệt: 1 hồ sơ; Cần bổ sung: 1 hồ sơ')
    expect(text).toContain('1 nhóm chưa có sản phẩm được duyệt.')
    expect(text).toContain('Xã Đức Trọng: 13 sản phẩm')
    expect(text).toContain('Tháng 8/2026: 9 sản phẩm; Tháng 9/2026: 11 sản phẩm')
    expect(text).toContain('4 sản phẩm nhập sẵn không có ngày duyệt')
    expect(text).toContain('Đồi chè, cà phê: 3 điểm')
    // Chưa có lượt xem: trạng thái rỗng có giải thích, không vẽ biểu đồ toàn số 0.
    expect(text).toContain('Chưa ghi nhận lượt xem nào')
  })

  it('bao loi rieng cho phan thong ke va cho thu lai', async () => {
    vi.mocked(getAdminStatistics).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('[role="alert"]').text()).toContain('Chưa tải được số liệu thống kê.')
    // Hàng đợi việc vẫn hiển thị bình thường.
    expect(wrapper.text()).toContain('Có 10 việc đang chờ bạn xử lý')

    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(getAdminStatistics).toHaveBeenCalledTimes(2)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })
})
