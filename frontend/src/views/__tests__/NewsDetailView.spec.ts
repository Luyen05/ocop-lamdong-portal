// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { flushPromises, mount, RouterLinkStub } from '@vue/test-utils'
import { reactive } from 'vue'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { getNewsBySlug } from '@/services/news'
import type { NewsDetail } from '@/types/news'
import NewsDetailView from '@/views/NewsDetailView.vue'

const route = reactive({ params: { slug: 'first-news' } })
vi.mock('vue-router', () => ({ useRoute: () => route }))
vi.mock('@/services/news', () => ({ getNewsBySlug: vi.fn() }))
const news: NewsDetail = {
  id: 1, title: 'Tin OCOP', slug: 'first-news', category: 'Hoạt động',
  summary: 'Tóm tắt', content: 'Nội dung bài viết\nĐoạn tiếp theo',
  primary_image_url: null, published_at: '2026-09-01', views: 10,
  images: [], updated_at: '2026-09-01',
}
const wrappers: ReturnType<typeof mount>[] = []
function mountView() {
  const wrapper = mount(NewsDetailView, { global: { stubs: { RouterLink: RouterLinkStub } } })
  wrappers.push(wrapper)
  return wrapper
}
function httpError(status: number, message: string) {
  return new AxiosError('Request failed', 'ERR_BAD_RESPONSE', undefined, undefined, {
    status, statusText: '', headers: {}, config: { headers: new AxiosHeaders() },
    data: { code: 'NEWS_NOT_FOUND', message, details: { slug: 'first-news' } },
  })
}
describe('NewsDetailView', () => {
  beforeEach(() => { vi.resetAllMocks(); route.params.slug = 'first-news' })
  afterEach(() => { wrappers.splice(0).forEach(wrapper => wrapper.unmount()) })
  it('renders loading then full article and back link', async () => {
    vi.mocked(getNewsBySlug).mockResolvedValue(news)
    const wrapper = mountView()
    expect(wrapper.get('[role="status"]').text()).toContain('Đang tải')
    await flushPromises()
    expect(wrapper.get('.news-detail h1').text()).toBe(news.title)
    expect(wrapper.get('.category-badge').text()).toBe(news.category)
    expect(wrapper.get('.summary').text()).toBe(news.summary)
    expect(wrapper.get('.news-content').text()).toBe(news.content)
    expect(wrapper.text()).toContain('10 lượt xem')
    expect(wrapper.get('time').text()).toBe(new Date(news.published_at).toLocaleDateString('vi-VN'))
    expect(wrapper.findComponent(RouterLinkStub).props('to')).toBe('/tin-tuc')
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
  })
  it('shows 404 message without retry', async () => {
    vi.mocked(getNewsBySlug).mockRejectedValue(httpError(404, 'Không tìm thấy bài viết.'))
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.error-state h1').text()).toBe('Không tìm thấy bài viết')
    expect(wrapper.get('.error-state p').text()).toBe('Không tìm thấy bài viết.')
    expect(wrapper.find('.error-state button').exists()).toBe(false)
  })
  it.each(['network', 'server'])('shows %s error and retries current slug', async (kind) => {
    vi.mocked(getNewsBySlug).mockRejectedValueOnce(kind === 'network' ?
      new AxiosError('Network Error') : httpError(500, 'Máy chủ gặp lỗi.')).mockResolvedValue(news)
    const wrapper = mountView()
    await flushPromises()
    expect(wrapper.get('.error-state h1').text()).toBe('Không thể tải bài viết')
    expect(wrapper.get('.error-state p').text()).toContain(kind === 'network' ? 'Không thể kết nối' : 'Máy chủ gặp lỗi.')
    await wrapper.get('.error-state button').trigger('click')
    await flushPromises()
    expect(getNewsBySlug).toHaveBeenLastCalledWith('first-news')
    expect(getNewsBySlug).toHaveBeenCalledTimes(2)
    expect(wrapper.find('.news-detail').exists()).toBe(true)
  })
  it('falls back after a primary image fails', async () => {
    vi.mocked(getNewsBySlug).mockResolvedValue({ ...news, primary_image_url: '/news.jpg' })
    const wrapper = mountView()
    await flushPromises()
    await wrapper.get('.primary-image img').trigger('error')
    expect(wrapper.find('.primary-image img').exists()).toBe(false)
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
  })
  it('ignores stale success after a newer route load', async () => {
    let resolveFirst!: (value: NewsDetail) => void
    vi.mocked(getNewsBySlug).mockReturnValueOnce(new Promise(resolve => { resolveFirst = resolve }))
      .mockResolvedValueOnce({ ...news, title: 'Bài mới', slug: 'second-news' })
    const wrapper = mountView()
    route.params.slug = 'second-news'
    await flushPromises()
    expect(getNewsBySlug).toHaveBeenLastCalledWith('second-news')
    resolveFirst(news)
    await flushPromises()
    expect(wrapper.get('.news-detail h1').text()).toBe('Bài mới')
  })
  it('ignores stale error while a newer route succeeds', async () => {
    let rejectFirst!: (reason: unknown) => void
    vi.mocked(getNewsBySlug).mockReturnValueOnce(new Promise((_, reject) => { rejectFirst = reject }))
      .mockResolvedValueOnce({ ...news, title: 'Bài mới' })
    const wrapper = mountView()
    route.params.slug = 'second-news'
    await flushPromises()
    rejectFirst(httpError(404, 'Không tìm thấy bài viết.'))
    await flushPromises()
    expect(wrapper.find('.error-state').exists()).toBe(false)
    expect(wrapper.get('.news-detail h1').text()).toBe('Bài mới')
  })
})