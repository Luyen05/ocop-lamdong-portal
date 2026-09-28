// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  getAdminLocation,
  getAdminLocationChangeRequest,
  listAdminLocationChangeRequests,
  listAdminLocations,
  moderateLocation,
  moderateLocationChangeRequest,
} from '@/services/location-management'
import { makeChangeRequest, makeLocation, positionCheck } from '@/test/location-fixtures'
import AdminLocationsView from '@/views/admin/AdminLocationsView.vue'

const route = reactive({ query: {} as Record<string, string> })
vi.mock('vue-router', () => ({ useRoute: () => route }))

vi.mock('@/services/location-management', () => ({
  getAdminLocation: vi.fn(),
  getAdminLocationChangeRequest: vi.fn(),
  listAdminLocationChangeRequests: vi.fn(),
  listAdminLocations: vi.fn(),
  moderateLocation: vi.fn(),
  moderateLocationChangeRequest: vi.fn(),
}))

enableAutoUnmount(afterEach)

const PickerStub = {
  name: 'LocationPicker',
  props: ['latitude', 'longitude', 'accuracy', 'readonly', 'label'],
  emits: ['pick'],
  template: '<div class="picker-stub" />',
}

const pending = makeLocation({ status: 'pending', submitted_at: '2026-09-27T04:00:00Z' })

function mountView() {
  return mount(AdminLocationsView, {
    attachTo: document.body,
    global: { stubs: { LocationPicker: PickerStub, RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } } },
  })
}

function button(wrapper: ReturnType<typeof mountView>, label: string) {
  return wrapper.findAll('button').find((item) => item.text().trim().startsWith(label))
}

describe('AdminLocationsView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    route.query = {}
    vi.mocked(listAdminLocations).mockResolvedValue({
      items: [pending],
      page: 1,
      page_size: 100,
      total: 1,
      status_counts: { pending: 1, approved: 9 },
    })
    vi.mocked(listAdminLocationChangeRequests).mockResolvedValue({ items: [makeChangeRequest()], page: 1, page_size: 100, total: 1 })
    vi.mocked(getAdminLocation).mockResolvedValue(pending)
    vi.mocked(getAdminLocationChangeRequest).mockResolvedValue(makeChangeRequest())
  })

  it('tai hang doi cho duyet, dem theo muc va mo chi tiet diem dau tien', async () => {
    const wrapper = mountView()
    await flushPromises()

    expect(listAdminLocations).toHaveBeenCalledWith(expect.objectContaining({ status: 'pending' }))
    expect(button(wrapper, 'Chờ duyệt')?.text()).toContain('1')
    expect(button(wrapper, 'Đã duyệt')?.text()).toContain('9')
    expect(button(wrapper, 'Yêu cầu cập nhật')?.text()).toContain('1')
    expect(wrapper.find('.detail h2').text()).toBe('Vườn dâu Langbiang Demo')
    expect(wrapper.text()).toContain('Không trùng điểm đã duyệt (gần nhất khoảng 9,9 km: Vườn dâu tây Cô Liên)')
    expect(wrapper.find('a[href*="google.com/maps"]').attributes('href')).toContain('12.047000,108.441000')
  })

  it('bat buoc ghi chu khi tra lai va gui quyet dinh', async () => {
    vi.mocked(moderateLocation).mockResolvedValue(makeLocation({ status: 'needs_revision' }))
    const wrapper = mountView()
    await flushPromises()

    await wrapper.findAll('[role="radio"]')[1]?.trigger('click')
    await button(wrapper, 'Gửi yêu cầu bổ sung')?.trigger('click')
    expect(moderateLocation).not.toHaveBeenCalled()
    expect(wrapper.text()).toContain('Cần nhập ghi chú')

    await wrapper.find('.decision textarea').setValue('Đặt lại ghim đúng cổng vào.')
    await button(wrapper, 'Gửi yêu cầu bổ sung')?.trigger('click')
    await flushPromises()
    expect(moderateLocation).toHaveBeenCalledWith(10, { status: 'needs_revision', note: 'Đặt lại ghim đúng cổng vào.' })
    expect(wrapper.text()).toContain('Đã trả lại để bổ sung: Vườn dâu Langbiang Demo.')
  })

  it('chinh vi tri roi duyet gui kem toa do moi', async () => {
    vi.mocked(moderateLocation).mockResolvedValue(makeLocation({ status: 'approved' }))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.findComponent(PickerStub).props('readonly')).toBe(true)
    await button(wrapper, 'Chỉnh vị trí')?.trigger('click')
    expect(wrapper.findComponent(PickerStub).props('readonly')).toBe(false)
    wrapper.findComponent(PickerStub).vm.$emit('pick', { latitude: 12.0468, longitude: 108.4415 })
    await flushPromises()
    expect(wrapper.text()).toContain('12.046800, 108.441500')

    await button(wrapper, 'Duyệt và hiện trên bản đồ')?.trigger('click')
    await flushPromises()
    expect(moderateLocation).toHaveBeenCalledWith(10, {
      status: 'approved',
      note: null,
      latitude: 12.0468,
      longitude: 108.4415,
    })
  })

  it('canh bao trung diem va ngoai tinh trong hang doi', async () => {
    const risky = makeLocation({
      status: 'pending',
      position_check: { ...positionCheck, inside_lam_dong: false, duplicate_warning: true, nearest: { ...positionCheck.nearest!, distance_m: 85 } },
    })
    vi.mocked(listAdminLocations).mockResolvedValue({ items: [risky], page: 1, page_size: 100, total: 1, status_counts: { pending: 1 } })
    vi.mocked(getAdminLocation).mockResolvedValue(risky)
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('.queue-item').text()).toContain('Có thể trùng')
    expect(wrapper.find('.queue-item').text()).toContain('Ngoài tỉnh')
    expect(wrapper.text()).toContain('Có thể trùng “Vườn dâu tây Cô Liên” (cách 85 m)')
  })

  it('duyet yeu cau cap nhat va hien bang so sanh', async () => {
    vi.mocked(moderateLocationChangeRequest).mockResolvedValue(makeChangeRequest({ status: 'approved' }))
    route.query = { tab: 'requests' }
    const wrapper = mountView()
    await flushPromises()

    expect(getAdminLocationChangeRequest).toHaveBeenCalledWith(5)
    const changed = wrapper.findAll('.compare tr.changed')
    expect(changed.map((row) => row.find('th').text())).toContain('Giờ mở cửa (có thay đổi)')
    expect(wrapper.text()).toContain('Đổi giờ mở cửa mùa cao điểm.')

    await button(wrapper, 'Duyệt và áp dụng thay đổi')?.trigger('click')
    await flushPromises()
    expect(moderateLocationChangeRequest).toHaveBeenCalledWith(5, { status: 'approved', note: null })
  })

  it('hien loi va thu lai khi khong tai duoc hang doi', async () => {
    vi.mocked(listAdminLocations).mockRejectedValueOnce(new Error('network'))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.text()).toContain('Không tải được hàng đợi điểm du lịch.')

    await wrapper.find('.queue .state button').trigger('click')
    await flushPromises()
    expect(wrapper.find('.queue-item').exists()).toBe(true)
  })
})
