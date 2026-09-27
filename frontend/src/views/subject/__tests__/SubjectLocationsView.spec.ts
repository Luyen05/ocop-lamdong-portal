// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  cancelLocationChangeRequest,
  deleteLocationDraft,
  listMyLocationChangeRequests,
  listMyLocations,
  requestLocationDeletion,
} from '@/services/location-management'
import { makeChangeRequest, makeLocation } from '@/test/location-fixtures'
import SubjectLocationsView from '@/views/subject/SubjectLocationsView.vue'

vi.mock('@/services/location-management', () => ({
  cancelLocationChangeRequest: vi.fn(),
  deleteLocationDraft: vi.fn(),
  listMyLocationChangeRequests: vi.fn(),
  listMyLocations: vi.fn(),
  requestLocationDeletion: vi.fn(),
  resubmitLocationChangeRequest: vi.fn(),
}))

enableAutoUnmount(afterEach)

const RouterLinkStub = { props: ['to'], template: '<a :href="to"><slot /></a>' }

function mountView() {
  return mount(SubjectLocationsView, {
    attachTo: document.body,
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}

function mockList(items = [makeLocation()], requests = [] as ReturnType<typeof makeChangeRequest>[]) {
  vi.mocked(listMyLocations).mockResolvedValue({ items, page: 1, page_size: 100, total: items.length, status_counts: {} })
  vi.mocked(listMyLocationChangeRequests).mockResolvedValue({ items: requests, page: 1, page_size: 100, total: requests.length })
}

describe('SubjectLocationsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.spyOn(window, 'confirm').mockReturnValue(true)
  })

  it('hien danh sach, dem theo trang thai va loc bang tab', async () => {
    mockList([
      makeLocation({ id: 1, name: 'Vườn nháp', images: [] }),
      makeLocation({ id: 2, name: 'Vườn chờ duyệt', status: 'pending' }),
      makeLocation({ id: 3, name: 'Vườn bị trả lại', status: 'needs_revision', review_note: 'Bổ sung ảnh cổng vào.' }),
    ])
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findAll('tbody tr')).toHaveLength(3)
    expect(wrapper.text()).toContain('Phường Lang Biang - Đà Lạt · chưa có ảnh')
    expect(wrapper.text()).toContain('Quản trị viên: Bổ sung ảnh cổng vào.')
    expect(wrapper.find('a[href="/chu-the/diem-du-lich/1"]').text()).toBe('Tiếp tục khai báo')
    expect(wrapper.find('a[href="/chu-the/diem-du-lich/2"]').text()).toBe('Xem hồ sơ')
    expect(wrapper.find('a[href="/chu-the/diem-du-lich/3"]').text()).toBe('Bổ sung hồ sơ')

    const pendingTab = wrapper.findAll('.tabs button').find((button) => button.text().startsWith('Chờ duyệt'))
    expect(pendingTab?.text()).toContain('1')
    await pendingTab?.trigger('click')
    expect(pendingTab?.attributes('aria-pressed')).toBe('true')
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
  })

  it('hien trang thai rong va trang thai loi co nut thu lai', async () => {
    mockList([])
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Đơn vị chưa khai báo điểm du lịch nào.')

    vi.mocked(listMyLocations).mockRejectedValueOnce(new Error('network'))
    const failing = mountView()
    await flushPromises()
    expect(failing.text()).toContain('Không tải được danh sách điểm du lịch.')
    mockList()
    await failing.find('.state.is-error button').trigger('click')
    await flushPromises()
    expect(failing.findAll('tbody tr')).toHaveLength(1)
  })

  it('diem da duyet co yeu cau dang mo thi hien nhan va cho huy', async () => {
    const approved = makeLocation({ status: 'approved' })
    mockList([approved], [makeChangeRequest({ id: 7, location_id: approved.id })])
    vi.mocked(cancelLocationChangeRequest).mockResolvedValue(makeChangeRequest({ status: 'cancelled' }))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.status').text()).toBe('Đã duyệt · có yêu cầu cập nhật')
    expect(wrapper.text()).not.toContain('Đề nghị cập nhật')
    const cancel = wrapper.findAll('button').find((button) => button.text() === 'Hủy yêu cầu')
    await cancel?.trigger('click')
    await flushPromises()
    expect(cancelLocationChangeRequest).toHaveBeenCalledWith(7)
    expect(wrapper.text()).toContain('Đã hủy yêu cầu.')
  })

  it('gui de nghi ngung hien thi voi ly do', async () => {
    mockList([makeLocation({ status: 'approved' })])
    vi.mocked(requestLocationDeletion).mockResolvedValue(makeChangeRequest({ request_type: 'delete' }))
    const wrapper = mountView()
    await flushPromises()

    await wrapper.findAll('button').find((button) => button.text() === 'Đề nghị ngừng hiển thị')?.trigger('click')
    const dialog = wrapper.find('[role="dialog"]')
    expect(dialog.exists()).toBe(true)
    await dialog.find('textarea').setValue('Tạm dừng đón khách.')
    await dialog.trigger('submit')
    await flushPromises()

    expect(requestLocationDeletion).toHaveBeenCalledWith(10, 'Tạm dừng đón khách.')
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
    expect(wrapper.text()).toContain('Điểm vẫn hiện trên bản đồ tới khi được duyệt.')
  })

  it('xoa ban nhap sau khi xac nhan', async () => {
    mockList([makeLocation()])
    vi.mocked(deleteLocationDraft).mockResolvedValue()
    const wrapper = mountView()
    await flushPromises()
    mockList([])

    await wrapper.findAll('button').find((button) => button.text() === 'Xóa')?.trigger('click')
    await flushPromises()

    expect(deleteLocationDraft).toHaveBeenCalledWith(10)
    expect(wrapper.text()).toContain('Đã xóa “Vườn dâu Langbiang Demo”.')
  })
})
