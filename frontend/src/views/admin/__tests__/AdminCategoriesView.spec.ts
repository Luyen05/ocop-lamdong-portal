// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import {
  createAdminCategory,
  deleteAdminCategory,
  listAdminCategories,
  updateAdminCategory,
} from '@/services/admin-categories'
import type { AdminCategory } from '@/types/category'
import AdminCategoriesView from '@/views/admin/AdminCategoriesView.vue'

vi.mock('@/services/admin-categories', () => ({
  listAdminCategories: vi.fn(),
  createAdminCategory: vi.fn(),
  updateAdminCategory: vi.fn(),
  deleteAdminCategory: vi.fn(),
}))

const drinks: AdminCategory = {
  id: 2,
  name: 'Đồ uống',
  slug: 'do-uong',
  description: 'Trà, cà phê',
  icon: null,
  is_visible: true,
  sort_order: 1,
  product_count: 4,
}

const herbs: AdminCategory = {
  id: 3,
  name: 'Thảo dược',
  slug: 'thao-duoc',
  description: null,
  icon: null,
  is_visible: false,
  sort_order: 2,
  product_count: 0,
}

function apiError(status: number, message: string): AxiosError {
  const headers = new AxiosHeaders()
  return new AxiosError('Request failed', 'ERR_BAD_REQUEST', { headers }, null, {
    status,
    statusText: 'Error',
    headers: {},
    config: { headers },
    data: { code: 'CATEGORY_NAME_EXISTS', message, details: null },
  })
}

async function mountView() {
  const wrapper = mount(AdminCategoriesView)
  await flushPromises()
  return wrapper
}

describe('AdminCategoriesView', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    vi.mocked(listAdminCategories).mockResolvedValue({ items: [herbs, drinks], total: 2 })
  })

  it('liệt kê danh mục theo thứ tự, số sản phẩm và trạng thái hiển thị', async () => {
    const wrapper = await mountView()

    const rows = wrapper.findAll('tbody tr')
    expect(rows.map((row) => row.find('strong').text())).toEqual(['Đồ uống', 'Thảo dược'])
    expect(rows[0].text()).toContain('do-uong')
    expect(rows[0].get('td[data-label="Sản phẩm"]').text()).toBe('4')
    expect(wrapper.get('[aria-label="Hiển thị danh mục Đồ uống"]').attributes('aria-checked')).toBe('true')
    expect(wrapper.get('[aria-label="Hiển thị danh mục Thảo dược"]').attributes('aria-checked')).toBe('false')
    expect(wrapper.text()).toContain('2 danh mục · 1 đang ẩn')
    // Danh mục còn sản phẩm không có nút xóa.
    expect(wrapper.find('[aria-label="Xóa danh mục Đồ uống"]').exists()).toBe(false)
    expect(rows[0].text()).toContain('Còn sản phẩm, chỉ có thể ẩn')
    expect(wrapper.find('[aria-label="Xóa danh mục Thảo dược"]').exists()).toBe(true)
  })

  it('bật/tắt hiển thị gọi API và cập nhật dòng', async () => {
    vi.mocked(updateAdminCategory).mockResolvedValue({ ...drinks, is_visible: false })
    const wrapper = await mountView()

    await wrapper.get('[aria-label="Hiển thị danh mục Đồ uống"]').trigger('click')
    await flushPromises()

    expect(updateAdminCategory).toHaveBeenCalledWith(2, { is_visible: false })
    expect(wrapper.get('[aria-label="Hiển thị danh mục Đồ uống"]').attributes('aria-checked')).toBe('false')
    expect(wrapper.text()).toContain('Đã ẩn danh mục "Đồ uống"')
  })

  it('thêm danh mục mới, slug để trống thì không gửi', async () => {
    vi.mocked(createAdminCategory).mockResolvedValue({
      id: 9,
      name: 'Nông sản tươi',
      slug: 'nong-san-tuoi',
      description: null,
      icon: null,
      is_visible: true,
      sort_order: 0,
      product_count: 0,
    })
    const wrapper = await mountView()

    await wrapper.findAll('button').find((button) => button.text().includes('Thêm danh mục'))!.trigger('click')
    const dialog = wrapper.get('[role="dialog"]')
    await dialog.get('input.form-control').setValue('  Nông sản tươi ')
    await dialog.get('form').trigger('submit')
    await flushPromises()

    expect(createAdminCategory).toHaveBeenCalledWith({
      name: 'Nông sản tươi',
      description: null,
      icon: null,
      is_visible: true,
      sort_order: 0,
    })
    expect(wrapper.find('[role="dialog"]').exists()).toBe(false)
    expect(wrapper.findAll('tbody tr').map((row) => row.find('strong').text())).toEqual([
      'Nông sản tươi',
      'Đồ uống',
      'Thảo dược',
    ])
  })

  it('sửa danh mục và hiện lỗi trùng tên từ máy chủ', async () => {
    vi.mocked(updateAdminCategory).mockRejectedValue(apiError(409, 'Tên danh mục đã tồn tại.'))
    const wrapper = await mountView()

    await wrapper.get('[aria-label="Sửa danh mục Đồ uống"]').trigger('click')
    const dialog = wrapper.get('[role="dialog"]')
    expect((dialog.get('input.form-control').element as HTMLInputElement).value).toBe('Đồ uống')
    await dialog.get('input.form-control').setValue('Thảo dược')
    await dialog.get('form').trigger('submit')
    await flushPromises()

    expect(updateAdminCategory).toHaveBeenCalledWith(2, expect.objectContaining({ name: 'Thảo dược', slug: 'do-uong' }))
    expect(wrapper.get('[role="dialog"] [role="alert"]').text()).toBe('Tên danh mục đã tồn tại.')
  })

  it('chặn slug sai định dạng trước khi gửi', async () => {
    const wrapper = await mountView()

    await wrapper.findAll('button').find((button) => button.text().includes('Thêm danh mục'))!.trigger('click')
    const inputs = wrapper.findAll('[role="dialog"] input.form-control')
    await inputs[0].setValue('Rau củ')
    await inputs[1].setValue('rau củ')
    await wrapper.get('[role="dialog"] form').trigger('submit')

    expect(createAdminCategory).not.toHaveBeenCalled()
    expect(wrapper.get('[role="dialog"] [role="alert"]').text()).toContain('Đường dẫn chỉ gồm chữ thường')
  })

  it('xóa danh mục trống sau khi xác nhận', async () => {
    vi.mocked(deleteAdminCategory).mockResolvedValue()
    const wrapper = await mountView()

    await wrapper.get('[aria-label="Xóa danh mục Thảo dược"]').trigger('click')
    const dialog = wrapper.get('[role="alertdialog"]')
    expect(dialog.text()).toContain('Xóa danh mục "Thảo dược"?')
    expect(deleteAdminCategory).not.toHaveBeenCalled()
    await dialog.findAll('button').find((button) => button.text() === 'Xác nhận xóa')!.trigger('click')
    await flushPromises()

    expect(deleteAdminCategory).toHaveBeenCalledWith(3)
    expect(wrapper.findAll('tbody tr')).toHaveLength(1)
    expect(wrapper.text()).toContain('Đã xóa danh mục "Thảo dược".')
  })

  it('có trạng thái lỗi với nút Thử lại và trạng thái rỗng', async () => {
    vi.mocked(listAdminCategories).mockRejectedValueOnce(new Error('offline'))
    const wrapper = await mountView()
    expect(wrapper.text()).toContain('Không thể tải danh sách danh mục.')

    vi.mocked(listAdminCategories).mockResolvedValueOnce({ items: [], total: 0 })
    await wrapper.findAll('button').find((button) => button.text().includes('Thử lại'))!.trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain('Chưa có danh mục nào')
  })
})
