// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createMemoryHistory, createRouter } from 'vue-router'

import PortalShell, { type PortalNavItem, type PortalNotification } from '@/layouts/PortalShell.vue'
import { checkApiHealth } from '@/services/system'
import pkg from '../../../package.json'

vi.mock('@/services/system', () => ({ checkApiHealth: vi.fn() }))
vi.mock('@/stores/auth', () => ({
  authStore: {
    currentUser: { value: { full_name: 'Nguyễn Văn A' } },
    logout: vi.fn(),
  },
}))

const navItems: PortalNavItem[] = [
  { label: 'Tổng quan', icon: 'dashboard', to: '/quan-tri', exact: true },
  { label: 'Sản phẩm', icon: 'package', to: '/quan-tri/san-pham' },
]

async function mountShell(options: { path?: string; notifications?: PortalNotification[] | null } = {}) {
  const router = createRouter({
    history: createMemoryHistory(),
    routes: [{ path: '/:pathMatch(.*)*', component: { template: '<div />' } }],
  })
  await router.push(options.path ?? '/quan-tri')
  await router.isReady()

  return mount(PortalShell, {
    props: {
      brandTitle: 'LÂM ĐỒNG OCOP',
      brandSubtitle: 'Khu vực quản trị',
      brandTo: '/quan-tri',
      navLabel: 'Điều hướng quản trị',
      navItems,
      roleLabel: 'Quản trị viên',
      profileTo: '/tai-khoan',
      pageTitle: 'Tổng quan quản trị',
      pageSubtitle: 'Việc cần xử lý',
      notifications: options.notifications ?? null,
    },
    slots: { default: '<p class="slot-content">Nội dung trang</p>' },
    global: { plugins: [router] },
    attachTo: document.body,
  })
}

describe('PortalShell', () => {
  beforeEach(() => {
    vi.mocked(checkApiHealth).mockResolvedValue(true)
  })

  it('hien thi menu, tieu de trang, nguoi dung va noi dung', async () => {
    const wrapper = await mountShell()
    await flushPromises()

    expect(wrapper.find('nav').attributes('aria-label')).toBe('Điều hướng quản trị')
    expect(wrapper.findAll('.ps-nav__item').map((item) => item.text())).toEqual(['Tổng quan', 'Sản phẩm'])
    expect(wrapper.find('.ps-topbar__name').text()).toBe('Tổng quan quản trị')
    expect(wrapper.find('.ps-topbar__sub').text()).toBe('Việc cần xử lý')
    expect(wrapper.find('.ps-avatar').text()).toContain('Nguyễn Văn A')
    expect(wrapper.find('.ps-avatar').text()).toContain('Quản trị viên')
    expect(wrapper.find('main .slot-content').exists()).toBe(true)
    expect(wrapper.text()).not.toContain('Sắp có')
  })

  it('hien phien ban lay tu package.json', async () => {
    const wrapper = await mountShell()
    expect(wrapper.find('.ps-version').text()).toContain(pkg.version)
  })

  it('chi sang muc dang xem va muc goc chi sang khi dung duong dan', async () => {
    const wrapper = await mountShell({ path: '/quan-tri/san-pham' })
    const [overview, products] = wrapper.findAll('.ps-nav__item')

    expect(overview.classes()).not.toContain('is-active')
    expect(overview.attributes('aria-current')).toBeUndefined()
    expect(products.classes()).toContain('is-active')
    expect(products.attributes('aria-current')).toBe('page')
  })

  it('an chuong khi khong co du lieu thong bao that', async () => {
    const wrapper = await mountShell({ notifications: null })
    expect(wrapper.find('.ps-bell').exists()).toBe(false)
  })

  it('hien tong so viec cho xu ly va chi liet ke muc co viec', async () => {
    const wrapper = await mountShell({
      notifications: [
        { key: 'a', label: 'Sản phẩm chờ duyệt', count: 3, to: '/quan-tri/san-pham' },
        { key: 'b', label: 'Hồ sơ chủ thể chờ duyệt', count: 0, to: '/quan-tri/ho-so-chu-the' },
        { key: 'c', label: 'Điểm du lịch chờ duyệt', count: 2, to: '/quan-tri/diem-du-lich' },
      ],
    })

    const button = wrapper.find('.ps-bell__button')
    expect(button.attributes('aria-label')).toBe('Thông báo: 5 việc cần xử lý')
    expect(wrapper.find('.ps-bell__badge').text()).toBe('5')
    expect(wrapper.find('.ps-bell__panel').exists()).toBe(false)

    await button.trigger('click')
    expect(button.attributes('aria-expanded')).toBe('true')
    const rows = wrapper.findAll('.ps-bell__list li')
    expect(rows.map((row) => row.text())).toEqual(['Sản phẩm chờ duyệt3', 'Điểm du lịch chờ duyệt2'])
  })

  it('bao khong co viec khi moi so deu bang 0 va dong bang phim Escape', async () => {
    const wrapper = await mountShell({
      notifications: [{ key: 'a', label: 'Sản phẩm chờ duyệt', count: 0, to: '/quan-tri/san-pham' }],
    })

    expect(wrapper.find('.ps-bell__badge').exists()).toBe(false)
    await wrapper.find('.ps-bell__button').trigger('click')
    expect(wrapper.find('.ps-bell__empty').text()).toBe('Không có việc nào đang chờ.')

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('.ps-bell__panel').exists()).toBe(false)
  })

  it('hien trang thai ket noi API theo endpoint suc khoe', async () => {
    const ok = await mountShell()
    await flushPromises()
    expect(ok.find('.ps-api').classes()).toContain('is-ok')
    expect(ok.find('.ps-api').text()).toBe('API kết nối')

    vi.mocked(checkApiHealth).mockResolvedValue(false)
    const down = await mountShell()
    await flushPromises()
    expect(down.find('.ps-api').classes()).toContain('is-down')
    expect(down.find('.ps-api').text()).toBe('Mất kết nối API')
  })

  it('mo va dong ngan keo menu tren dien thoai', async () => {
    const wrapper = await mountShell()
    const toggle = wrapper.find('.ps-topbar__toggle')

    expect(toggle.attributes('aria-expanded')).toBe('false')
    await toggle.trigger('click')
    expect(toggle.attributes('aria-expanded')).toBe('true')
    expect(wrapper.find('#portal-sidebar').classes()).toContain('is-open')

    document.dispatchEvent(new KeyboardEvent('keydown', { key: 'Escape' }))
    await flushPromises()
    expect(wrapper.find('#portal-sidebar').classes()).not.toContain('is-open')
  })
})
