// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import HomeNews from '@/components/home/HomeNews.vue'
import { getNews } from '@/services/news'

vi.mock('@/services/news', () => ({
  getNews: vi.fn(),
}))

const sampleNews = {
  id: 'tin-ocop',
  title: 'Hoạt động OCOP Lâm Đồng',
  summary: 'Thông tin từ nguồn chính thức.',
  published_at: '2026-08-12T14:55:37+07:00',
  source_name: 'Cổng TTĐT OCOP Lâm Đồng',
  source_url: 'https://ocoplamdong.gov.vn/tin-tuc/tin-ocop.html',
  image_url: null,
  category: 'Tin tức - Sự kiện',
}

describe('HomeNews', () => {
  beforeEach(() => vi.clearAllMocks())

  it('hien thi tin moi tu api va lien ket den nguon goc', async () => {
    vi.mocked(getNews).mockResolvedValue({
      items: [sampleNews],
      page: 1,
      page_size: 4,
      total: 1,
    })
    const wrapper = mount(HomeNews, {
      global: {
        stubs: { RouterLink: { props: ['to'], template: '<a><slot /></a>' } },
      },
    })
    await flushPromises()

    expect(getNews).toHaveBeenCalledWith({ page: 1, page_size: 4 })
    expect(wrapper.text()).toContain('Hoạt động OCOP Lâm Đồng')
    expect(wrapper.get('.news-body a').attributes('href')).toBe(sampleNews.source_url)
    wrapper.unmount()
  })

  it('hien thi loi va cho phep thu lai', async () => {
    vi.mocked(getNews).mockRejectedValueOnce(new Error('network'))
    vi.mocked(getNews).mockResolvedValueOnce({ items: [sampleNews], page: 1, page_size: 4, total: 1 })
    const wrapper = mount(HomeNews, {
      global: { stubs: { RouterLink: { template: '<a><slot /></a>' } } },
    })
    await flushPromises()

    expect(wrapper.text()).toContain('Chưa thể tải tin tức mới')
    await wrapper.get('.state-card button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain(sampleNews.title)
    wrapper.unmount()
  })
})
