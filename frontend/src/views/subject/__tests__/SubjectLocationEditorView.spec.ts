// @vitest-environment jsdom
import { enableAutoUnmount, flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  checkLocationPosition,
  createLocationDraft,
  getMyLocation,
  parseCoordinates,
  requestLocationUpdate,
  submitLocation,
  updateLocationDraft,
  uploadLocationImage,
} from '@/services/location-management'
import { getLocationFilterOptions } from '@/services/locations'
import { listMyProducts } from '@/services/product-management'
import { getMySubjectApplication } from '@/services/subjects'
import { makeLocation, positionCheck } from '@/test/location-fixtures'
import SubjectLocationEditorView from '@/views/subject/SubjectLocationEditorView.vue'

const route = reactive({ params: {} as Record<string, string> })
const router = { push: vi.fn().mockResolvedValue(undefined), replace: vi.fn().mockResolvedValue(undefined) }

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => router,
  onBeforeRouteLeave: vi.fn(),
}))

vi.mock('@/services/location-management', () => ({
  checkLocationPosition: vi.fn(),
  createLocationDraft: vi.fn(),
  deleteTemporaryLocationImage: vi.fn(),
  getMyLocation: vi.fn(),
  getMyLocationChangeRequest: vi.fn(),
  parseCoordinates: vi.fn(),
  requestLocationUpdate: vi.fn(),
  resubmitLocationChangeRequest: vi.fn(),
  submitLocation: vi.fn(),
  updateLocationDraft: vi.fn(),
  uploadLocationImage: vi.fn(),
}))
vi.mock('@/services/locations', () => ({ getLocationFilterOptions: vi.fn() }))
vi.mock('@/services/product-management', () => ({ listMyProducts: vi.fn() }))
vi.mock('@/services/subjects', () => ({ getMySubjectApplication: vi.fn() }))

enableAutoUnmount(afterEach)

const PickerStub = {
  name: 'LocationPicker',
  props: ['latitude', 'longitude', 'accuracy', 'readonly'],
  emits: ['pick'],
  template: '<div class="picker-stub" />',
}

function mountView() {
  return mount(SubjectLocationEditorView, {
    attachTo: document.body,
    global: { stubs: { RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' }, LocationPicker: PickerStub } },
  })
}

function button(wrapper: ReturnType<typeof mountView>, label: string) {
  return wrapper.findAll('button').find((item) => item.text().trim() === label)
}

describe('SubjectLocationEditorView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    route.params = {}
    vi.mocked(getLocationFilterOptions).mockResolvedValue({ types: [], districts: ['Đà Lạt', 'Lạc Dương'] })
    vi.mocked(listMyProducts).mockResolvedValue({
      items: [{ id: 6, name: 'Hồng treo gió Đà Lạt' } as never],
      page: 1,
      page_size: 100,
      total: 1,
    })
    vi.mocked(getMySubjectApplication).mockResolvedValue({
      address: 'Phường Lang Biang - Đà Lạt, tỉnh Lâm Đồng',
      district: 'Đà Lạt',
    } as never)
    vi.mocked(checkLocationPosition).mockResolvedValue(positionCheck)
  })

  it('tao ban nhap chi voi ten va loai hinh roi chuyen sang dia chi cua ban nhap', async () => {
    const created = makeLocation({ latitude: null, longitude: null, location_source: null, images: [], position_check: null })
    vi.mocked(createLocationDraft).mockResolvedValue(created)
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('h1').text()).toBe('Khai báo điểm du lịch')
    await button(wrapper, 'Lưu nháp')?.trigger('click')
    expect(wrapper.text()).toContain('Nhập tên điểm du lịch')
    expect(createLocationDraft).not.toHaveBeenCalled()

    await wrapper.find('input[type="text"]').setValue('Vườn dâu Langbiang Demo')
    await button(wrapper, 'Lưu nháp')?.trigger('click')
    await flushPromises()

    expect(createLocationDraft).toHaveBeenCalledWith(
      expect.objectContaining({ name: 'Vườn dâu Langbiang Demo', type: 'fruit_garden', latitude: null, longitude: null }),
    )
    expect(router.replace).toHaveBeenCalledWith('/chu-the/diem-du-lich/10')
    expect(wrapper.text()).toContain('Đã lưu nháp')
  })

  it('ban nhap thieu thong tin thi khoa nut gui duyet va liet ke muc con thieu', async () => {
    route.params = { id: '10' }
    vi.mocked(getMyLocation).mockResolvedValue(
      makeLocation({ description: 'Quá ngắn', images: [], address: null, district: null }),
    )
    const wrapper = mountView()
    await flushPromises()

    expect(button(wrapper, 'Gửi duyệt')?.attributes('disabled')).toBeDefined()
    const summary = wrapper.find('#missing-summary').text()
    expect(summary).toContain('địa chỉ và xã/phường')
    expect(summary).toContain('mô tả tối thiểu 40 ký tự')
    expect(summary).toContain('ít nhất 1 ảnh')

    await button(wrapper, 'Dùng địa chỉ của đơn vị')?.trigger('click')
    expect((wrapper.find('input[list="district-options"]').element as HTMLInputElement).value).toBe('Đà Lạt')
  })

  it('luu roi gui duyet ban nhap day du', async () => {
    route.params = { id: '10' }
    const draft = makeLocation()
    vi.mocked(getMyLocation).mockResolvedValue(draft)
    vi.mocked(updateLocationDraft).mockResolvedValue(draft)
    vi.mocked(submitLocation).mockResolvedValue(makeLocation({ status: 'pending', submitted_at: '2026-09-27T05:00:00Z' }))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.text()).toContain('Không trùng điểm đã có. Điểm gần nhất: Vườn dâu tây Cô Liên')
    await button(wrapper, 'Gửi duyệt')?.trigger('click')
    await flushPromises()

    expect(updateLocationDraft).toHaveBeenCalledWith(
      10,
      expect.objectContaining({ latitude: 12.047, longitude: 108.441, location_source: 'map_pin', ticket_price: 50000 }),
    )
    expect(submitLocation).toHaveBeenCalledWith(10)
    expect(wrapper.text()).toContain('Đã gửi hồ sơ.')
    expect(wrapper.find('fieldset').attributes('disabled')).toBeDefined()
    expect(button(wrapper, 'Gửi duyệt')).toBeUndefined()
  })

  it('dat ghim tren ban do, dan toa do va lay GPS', async () => {
    vi.useFakeTimers()
    const wrapper = mountView()
    await flushPromises()

    wrapper.findComponent(PickerStub).vm.$emit('pick', { latitude: 11.95, longitude: 108.44 })
    await vi.advanceTimersByTimeAsync(350)
    expect(checkLocationPosition).toHaveBeenCalledWith(11.95, 108.44, undefined)
    expect(wrapper.text()).toContain('11.950000, 108.440000')
    expect(wrapper.text()).toContain('Ghim trên bản đồ')
    vi.useRealTimers()

    vi.mocked(parseCoordinates).mockResolvedValue({
      latitude: 21.0285,
      longitude: 105.8542,
      location_source: 'coordinates',
      position_check: { ...positionCheck, latitude: 21.0285, longitude: 105.8542, inside_lam_dong: false, nearest: null },
    })
    await wrapper.findAll('[role="radio"]')[2]?.trigger('click')
    await wrapper.find('#paste-input').setValue('21.0285, 105.8542')
    await button(wrapper, 'Đặt ghim')?.trigger('click')
    await flushPromises()
    expect(parseCoordinates).toHaveBeenCalledWith('21.0285, 105.8542')
    expect(wrapper.text()).toContain('Vị trí nằm ngoài tỉnh Lâm Đồng')

    const getCurrentPosition = vi.fn((success: PositionCallback) =>
      success({ coords: { latitude: 12.047, longitude: 108.441, accuracy: 14.6 } } as GeolocationPosition),
    )
    Object.defineProperty(navigator, 'geolocation', { configurable: true, value: { getCurrentPosition } })
    await wrapper.findAll('[role="radio"]')[1]?.trigger('click')
    await button(wrapper, 'Lấy vị trí hiện tại')?.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('GPS của thiết bị')
    expect(wrapper.text()).toContain('± 15 m (tốt)')
    expect(wrapper.findComponent(PickerStub).props('accuracy')).toBe(14.6)
  })

  it('tai anh len va chon anh chinh', async () => {
    vi.mocked(uploadLocationImage).mockResolvedValue({
      image_url: 'http://localhost:8000/uploads/locations/2/b.png',
      storage_path: 'locations/2/b.png',
      content_type: 'image/png',
      size_bytes: 100,
    })
    const wrapper = mountView()
    await flushPromises()
    const input = wrapper.find('input[type="file"]')
    const file = new File(['png'], 'vuon.png', { type: 'image/png' })
    Object.defineProperty(input.element, 'files', { value: [file] })
    await input.trigger('change')
    await flushPromises()

    expect(uploadLocationImage).toHaveBeenCalledWith(file)
    expect(wrapper.findAll('.gallery li')).toHaveLength(1)
    expect((wrapper.find('.gallery input[type="radio"]').element as HTMLInputElement).checked).toBe(true)
  })

  it('diem da duyet chuyen sang gui yeu cau cap nhat', async () => {
    route.params = { id: '10' }
    vi.mocked(getMyLocation).mockResolvedValue(makeLocation({ status: 'approved', version: 2 }))
    vi.mocked(requestLocationUpdate).mockResolvedValue({} as never)
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('h1').text()).toBe('Đề nghị cập nhật điểm du lịch')
    expect(button(wrapper, 'Lưu nháp')).toBeUndefined()
    await wrapper.find('textarea[placeholder^="Ví dụ: đổi giờ"]').setValue('Đổi giờ mở cửa.')
    await button(wrapper, 'Gửi yêu cầu cập nhật')?.trigger('click')
    await flushPromises()

    expect(requestLocationUpdate).toHaveBeenCalledWith(
      10,
      expect.objectContaining({ name: 'Vườn dâu Langbiang Demo', latitude: 12.047, images: expect.any(Array) }),
      'Đổi giờ mở cửa.',
    )
    expect(router.push).toHaveBeenCalledWith({ path: '/chu-the/diem-du-lich' })
  })

  it('ho so dang cho duyet chi xem, khong sua', async () => {
    route.params = { id: '10' }
    vi.mocked(getMyLocation).mockResolvedValue(makeLocation({ status: 'pending', submitted_at: '2026-09-27T05:00:00Z' }))
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('fieldset').attributes('disabled')).toBeDefined()
    expect(wrapper.text()).toContain('Hồ sơ đang chờ quản trị viên duyệt nên chưa sửa được.')
    expect(wrapper.findComponent(PickerStub).props('readonly')).toBe(true)
    expect(wrapper.find('a[href="/chu-the/diem-du-lich"]').exists()).toBe(true)
  })

  it('hien ghi chu cua quan tri vien khi can bo sung', async () => {
    route.params = { id: '10' }
    vi.mocked(getMyLocation).mockResolvedValue(
      makeLocation({ status: 'needs_revision', review_note: 'Bổ sung ảnh cổng vào.', reviewed_by_name: 'Quản trị viên' }),
    )
    const wrapper = mountView()
    await flushPromises()

    expect(wrapper.find('h1').text()).toBe('Bổ sung hồ sơ điểm du lịch')
    expect(wrapper.text()).toContain('Bổ sung ảnh cổng vào.')
    expect(wrapper.find('fieldset').attributes('disabled')).toBeUndefined()
  })
})
