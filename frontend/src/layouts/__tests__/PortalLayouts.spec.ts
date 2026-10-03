// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import AdminLayout from '@/layouts/AdminLayout.vue'
import SubjectLayout from '@/layouts/SubjectLayout.vue'
import { getAdminDashboard } from '@/services/admin'
import { checkApiHealth } from '@/services/system'

vi.mock('@/services/admin', () => ({ getAdminDashboard: vi.fn() }))
vi.mock('@/services/system', () => ({ checkApiHealth: vi.fn() }))
vi.mock('@/stores/auth', () => ({
  authStore: {
    currentUser: { value: { full_name: 'Người dùng demo' } },
    logout: vi.fn(),
  },
}))

const page = { template: '<p class="page">Trang</p>' }

async function mountLayout(layout: typeof AdminLayout, path: string) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [
      {
        path: '/quan-tri',
        component: layout,
        children: [
          { path: '', name: 'admin-dashboard', component: page, meta: { title: 'Tổng quan quản trị' } },
          { path: 'san-pham', name: 'admin-products', component: page, meta: { title: 'Duyệt sản phẩm' } },
        ],
      },
      {
        path: '/chu-the',
        component: layout,
        children: [
          { path: 'san-pham', name: 'subject-products', component: page, meta: { title: 'Sản phẩm của chủ thể' } },
          { path: 'san-pham/them', name: 'subject-product-create', component: page },
          { path: 'diem-du-lich', name: 'subject-locations', component: page, meta: { title: 'Điểm du lịch của tôi' } },
          { path: 'ho-so', name: 'subject-profile', component: page, meta: { title: 'Hồ sơ chủ thể' } },
        ],
      },
    ],
  })
  await router.push(path)
  await router.isReady()
  const wrapper = mount({ template: '<RouterView />' }, { global: { plugins: [router] }, attachTo: document.body })
  await flushPromises()
  return wrapper
}

describe('AdminLayout', () => {
  beforeEach(() => {
    vi.mocked(checkApiHealth).mockResolvedValue(true)
    vi.mocked(getAdminDashboard).mockResolvedValue({
      total_products: 10,
      approved_products: 6,
      pending_products: 2,
      pending_subject_applications: 1,
      pending_change_requests: 1,
      products_missing_decision: 0,
      pending_locations: 3,
      pending_location_change_requests: 0,
    })
  })

  it('chi hien cac muc da co trang, khong con muc Sap co', async () => {
    const wrapper = await mountLayout(AdminLayout, '/quan-tri/san-pham')

    expect(wrapper.findAll('.ps-nav__item').map((item) => item.text())).toEqual([
      'Tổng quan',
      'Sản phẩm',
      'Điểm du lịch',
      'Chủ thể / HTX',
    ])
    expect(wrapper.text()).not.toContain('Sắp có')
    expect(wrapper.find('.ps-topbar__name').text()).toBe('Duyệt sản phẩm')
    expect(wrapper.find('.ps-topbar__sub').text()).toBe('Duyệt sản phẩm và yêu cầu chỉnh sửa')
    expect(wrapper.find('.page').exists()).toBe(true)
  })

  it('chuong lay so viec cho xu ly tu API dashboard', async () => {
    const wrapper = await mountLayout(AdminLayout, '/quan-tri')

    expect(getAdminDashboard).toHaveBeenCalled()
    expect(wrapper.find('.ps-bell__badge').text()).toBe('7')
    await wrapper.find('.ps-bell__button').trigger('click')
    expect(wrapper.findAll('.ps-bell__list li').map((row) => row.text())).toEqual([
      'Hồ sơ chủ thể chờ duyệt1',
      'Sản phẩm chờ duyệt2',
      'Yêu cầu chỉnh sửa sản phẩm1',
      'Điểm du lịch chờ duyệt3',
    ])
  })

  it('an chuong khi khong tai duoc du lieu dashboard', async () => {
    vi.mocked(getAdminDashboard).mockRejectedValue(new Error('network'))
    const wrapper = await mountLayout(AdminLayout, '/quan-tri')

    expect(wrapper.find('.ps-bell').exists()).toBe(false)
  })
})

describe('SubjectLayout', () => {
  beforeEach(() => {
    vi.mocked(checkApiHealth).mockResolvedValue(true)
  })

  it('co 3 muc menu cua chu the va khong co chuong thong bao', async () => {
    const wrapper = await mountLayout(SubjectLayout, '/chu-the/diem-du-lich')

    expect(wrapper.findAll('.ps-nav__item').map((item) => item.text())).toEqual([
      'Sản phẩm',
      'Điểm du lịch',
      'Hồ sơ đơn vị',
    ])
    expect(wrapper.find('.ps-bell').exists()).toBe(false)
    expect(wrapper.find('.ps-nav__item.is-active').text()).toBe('Điểm du lịch')
    expect(wrapper.find('.ps-avatar').text()).toContain('Chủ thể')
  })

  it('trang con van sang muc cha va dung tieu de du phong', async () => {
    const wrapper = await mountLayout(SubjectLayout, '/chu-the/san-pham/them')

    expect(wrapper.find('.ps-nav__item.is-active').text()).toBe('Sản phẩm')
    expect(wrapper.find('.ps-topbar__name').text()).toBe('Thêm sản phẩm')
    expect(wrapper.find('.ps-topbar__sub').text()).toBe('Soạn sản phẩm mới và gửi duyệt')
  })
})
