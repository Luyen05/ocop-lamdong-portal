// @vitest-environment jsdom
import { flushPromises, mount } from '@vue/test-utils'
import { reactive } from 'vue'
import { beforeEach, describe, expect, it, vi } from 'vitest'

import { getNews } from '@/services/news'
import NewsView from '@/views/NewsView.vue'

const route = reactive({ query: {} as Record<string, string> })
const router = {
  push: vi.fn().mockResolvedValue(undefined),
  replace: vi.fn().mockResolvedValue(undefined),
}

vi.mock('vue-router', () => ({
  useRoute: () => route,
  useRouter: () => router,
}))

vi.mock('@/services/news', () => ({
  getNews: vi.fn(),
}))

const sampleNews = {
  id: 'tin-ocop',
  title: 'Tin OCOP cần tìm',
  summary: 'Nội dung bài viết.',
  published_at: '2026-08-12T14:55:37+07:00',
  source_name: 'Cổng TTĐT OCOP Lâm Đồng',
  source_url: 'https://ocoplamdong.gov.vn/tin-tuc/tin-ocop.html',
  image_url: null,
  category: 'Tin tức - Sự kiện',
}

describe('NewsView', () => {
  beforeEach(() => {
    route.query = {}
    vi.clearAllMocks()
    vi.mocked(getNews).mockResolvedValue({
      items: [sampleNews],
      page: 1,
      page_size: 9,
      total: 10,
    })
  })

  it('tai danh sach va chuyen tu khoa tim kiem vao url', async () => {
    const wrapper = mount(NewsView)
    await flushPromises()

    expect(wrapper.text()).toContain(sampleNews.title)
    expect(wrapper.text()).toContain('10 bài viết')
    await wrapper.get('#news-search-input').setValue('  xúc tiến  ')
    await wrapper.get('.news-search').trigger('submit')
    await flushPromises()

    expect(router.push).toHaveBeenCalledWith({ name: 'news', query: { search: 'xúc tiến' } })
    wrapper.unmount()
  })

  it('hien thi loi than thien va tai lai duoc', async () => {
    vi.mocked(getNews).mockRejectedValueOnce(new Error('network'))
    const wrapper = mount(NewsView)
    await flushPromises()

    expect(wrapper.text()).toContain('Chưa thể tải tin tức')
    await wrapper.get('.error-state button').trigger('click')
    await flushPromises()
    expect(wrapper.text()).toContain(sampleNews.title)
    wrapper.unmount()
  })
})
