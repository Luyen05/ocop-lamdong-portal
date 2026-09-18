// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { listNews } from '@/services/news'
import NewsView from '@/views/NewsView.vue'
import type { NewsListResponse } from '@/types/news'

vi.mock('@/services/news', () => ({ listNews: vi.fn() }))
const response: NewsListResponse = {
  items: [{ id: 1, title: 'Tin OCOP', slug: 'tin-ocop', category: 'Hoạt động',
    summary: 'Tóm tắt', primary_image_url: null, published_at: '2026-09-01' }],
  page: 1, page_size: 12, total: 1,
}
const wrappers: ReturnType<typeof mount>[] = []
function mountView() {
  const wrapper = mount(NewsView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  wrappers.push(wrapper)
  return wrapper
}
describe('NewsView', () => {
  beforeEach(() => { vi.resetAllMocks() })
  afterEach(() => { wrappers.splice(0).forEach(wrapper => wrapper.unmount()) })
  it('shows loading then successful list', async () => {
    vi.mocked(listNews).mockResolvedValue(response)
    const wrapper = mountView()
    expect(wrapper.get('[role="status"]').text()).toContain('Đang tải')
    await flushPromises()
    expect(wrapper.get('.news-card').text()).toContain('Tin OCOP')
    expect(listNews).toHaveBeenCalledWith({ page: 1, page_size: 12, search: undefined })
  })
  it('shows empty response', async () => {
    vi.mocked(listNews).mockResolvedValue({ ...response, items: [], total: 0 })
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.empty-state').text()).toContain('Chưa tìm thấy bài viết')
  })
  it.each(['network', 'server'])('shows %s error and retries', async (kind) => {
    const error = kind === 'network' ? new AxiosError('Network Error') :
      new AxiosError('Server error', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 500, statusText: '', headers: {}, config: { headers: new AxiosHeaders() },
        data: { message: 'Máy chủ gặp lỗi.' },
      })
    vi.mocked(listNews).mockRejectedValueOnce(error).mockResolvedValue(response)
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain(kind === 'network' ? 'Không thể kết nối' : 'Máy chủ gặp lỗi.')
    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(listNews).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.news-card').exists()).toBe(true)
  })
  it('paginates using backend metadata and submits search at page 1', async () => {
    vi.mocked(listNews).mockResolvedValueOnce({ ...response, page_size: 2, total: 5 })
      .mockResolvedValueOnce({ ...response, page: 2, page_size: 2, total: 5 })
      .mockResolvedValue(response)
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('#news-search').setValue('  OCOP  ')
    expect(listNews).toHaveBeenCalledTimes(1)
    await wrapper.get('.pagination-wrap button:last-child').trigger('click')
    await flushPromises()
    expect(listNews).toHaveBeenLastCalledWith({ page: 2, page_size: 2, search: undefined })
    expect(wrapper.get('.pagination-wrap span').text()).toBe('Trang 2 / 3')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    expect(listNews).toHaveBeenLastCalledWith({ page: 1, page_size: 2, search: 'OCOP' })
  })
  it('preserves submitted search on pagination and retry', async () => {
    vi.mocked(listNews).mockResolvedValue({ ...response, total: 25 })
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('#news-search').setValue('OCOP')
    await wrapper.get('form').trigger('submit')
    await flushPromises()
    await wrapper.get('#news-search').setValue('draft')
    vi.mocked(listNews).mockRejectedValueOnce(new AxiosError('Network Error'))
    await wrapper.get('.pagination-wrap button:last-child').trigger('click')
    await flushPromises()
    expect(listNews).toHaveBeenLastCalledWith({ page: 2, page_size: 12, search: 'OCOP' })
    await wrapper.get('[role="alert"] button').trigger('click')
    await flushPromises()
    expect(listNews).toHaveBeenLastCalledWith({ page: 2, page_size: 12, search: 'OCOP' })
  })
})