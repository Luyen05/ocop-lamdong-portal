// @vitest-environment jsdom
import { AxiosError, AxiosHeaders } from 'axios'
import { flushPromises, mount } from '@vue/test-utils'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import HomeNews from '@/components/home/HomeNews.vue'
import { listNews } from '@/services/news'
import type { NewsListItem, NewsListResponse } from '@/types/news'

vi.mock('@/services/news', () => ({ listNews: vi.fn() }))

function article(id: number): NewsListItem {
  return {
    id, title: `Tin OCOP ${id}`, slug: `tin-ocop-${id}`, category: 'Hoạt động',
    summary: `Tóm tắt bài viết ${id}`, primary_image_url: `/news-${id}.jpg`,
    published_at: `2026-09-0${id}T00:00:00Z`,
  }
}
const response: NewsListResponse = {
  items: [article(3), article(1), article(2)], page: 1, page_size: 3, total: 4,
}
const wrappers: ReturnType<typeof mount>[] = []
function mountNews() {
  const wrapper = mount(HomeNews, {
    global: {
      stubs: { RouterLink: { props: ['to'], template: '<a :href="to"><slot /></a>' } },
    },
  })
  wrappers.push(wrapper)
  return wrapper
}

describe('HomeNews', () => {
  beforeEach(() => { vi.resetAllMocks() })
  afterEach(() => { wrappers.splice(0).forEach(wrapper => wrapper.unmount()) })

  it('shows loading then API fields in backend order, capped at three cards', async () => {
    vi.mocked(listNews).mockResolvedValue({ ...response, items: [...response.items, article(4)] })
    const wrapper = mountNews()
    expect(wrapper.get('[role="status"]').text()).toContain('Đang tải tin tức')
    expect(wrapper.find('.news-card').exists()).toBe(false)
    await flushPromises()

    expect(listNews).toHaveBeenCalledWith({ page: 1, page_size: 3 })
    const cards = wrapper.findAll('.news-card')
    expect(cards).toHaveLength(3)
    response.items.forEach((item, index) => {
      const card = cards[index]!
      for (const text of [item.title, item.category, item.summary]) expect(card.text()).toContain(text)
      expect(card.get('img').attributes('src')).toBe(item.primary_image_url)
      expect(card.get('time').attributes('datetime')).toBe(item.published_at)
      expect(card.get('time').text()).toBe(new Date(item.published_at).toLocaleDateString('vi-VN'))
    })
    expect(wrapper.text()).not.toContain('Dữ liệu minh họa')
    expect(wrapper.find('button[disabled]').exists()).toBe(false)
    expect(wrapper.find('[role="status"]').exists()).toBe(false)
  })

  it('links every article to its slug and provides a view-all link', async () => {
    vi.mocked(listNews).mockResolvedValue(response)
    const wrapper = mountNews()
    await flushPromises()
    wrapper.findAll('.news-card').forEach((card, index) => {
      const links = card.findAll('a')
      expect(links).toHaveLength(3)
      links.forEach(link => expect(link.attributes('href')).toBe(`/tin-tuc/${response.items[index]!.slug}`))
    })
    expect(wrapper.get('.section-heading a').attributes('href')).toBe('/tin-tuc')
    expect(wrapper.get('.section-heading a').text()).toContain('Xem tất cả tin tức')
  })

  it('shows an empty state without mock articles or retry', async () => {
    vi.mocked(listNews).mockResolvedValue({ ...response, items: [], total: 0 })
    const wrapper = mountNews()
    await flushPromises()
    expect(wrapper.get('[role="status"]').text()).toBe('Chưa có tin tức được xuất bản.')
    expect(wrapper.find('.news-card').exists()).toBe(false)
    expect(wrapper.find('button').exists()).toBe(false)
    expect(wrapper.get('.section-heading a').attributes('href')).toBe('/tin-tuc')
  })

  it.each(['network', 'server'])('shows %s error without mock fallback and retries successfully', async (kind) => {
    const error = kind === 'network' ? new AxiosError('Network Error') :
      new AxiosError('Server error', 'ERR_BAD_RESPONSE', undefined, undefined, {
        status: 500, statusText: '', headers: {}, config: { headers: new AxiosHeaders() },
        data: { message: 'Máy chủ gặp lỗi.' },
      })
    let resolveRetry!: (value: NewsListResponse) => void
    const retryResponse = new Promise<NewsListResponse>(resolve => { resolveRetry = resolve })
    vi.mocked(listNews).mockRejectedValueOnce(error).mockReturnValueOnce(retryResponse)
    const wrapper = mountNews()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain(kind === 'network' ? 'Không thể kết nối' : 'Máy chủ gặp lỗi.')
    expect(wrapper.find('.news-card').exists()).toBe(false)
    expect(wrapper.find('[role="status"]').exists()).toBe(false)
    await wrapper.get('[role="alert"] button').trigger('click')
    expect(wrapper.get('[role="status"]').text()).toContain('Đang tải tin tức')
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
    resolveRetry(response)
    await flushPromises()
    expect(listNews).toHaveBeenCalledTimes(2)
    expect(listNews).toHaveBeenLastCalledWith({ page: 1, page_size: 3 })
    expect(wrapper.findAll('.news-card')).toHaveLength(3)
    expect(wrapper.find('[role="alert"]').exists()).toBe(false)
  })

  it('uses the fallback message for unexpected errors', async () => {
    vi.mocked(listNews).mockRejectedValue(new Error('unexpected'))
    const wrapper = mountNews()
    await flushPromises()
    expect(wrapper.get('[role="alert"]').text()).toContain('Chưa thể tải tin tức.')
  })

  it('reuses placeholders for null, empty and broken images', async () => {
    vi.mocked(listNews).mockResolvedValue({ ...response, items: [
      { ...article(1), primary_image_url: null },
      { ...article(2), primary_image_url: '' },
      article(3),
    ] })
    const wrapper = mountNews()
    await flushPromises()
    expect(wrapper.findAll('.image-placeholder')).toHaveLength(2)
    expect(wrapper.findAll('img')).toHaveLength(1)
    await wrapper.get('img').trigger('error')
    expect(wrapper.findAll('.image-placeholder')).toHaveLength(3)
    expect(wrapper.find('img').exists()).toBe(false)
  })
})
