// @vitest-environment jsdom
import { mount, RouterLinkStub } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'
import NewsCard from '@/components/news/NewsCard.vue'
import type { NewsListItem } from '@/types/news'

const news: NewsListItem = {
  id: 1, title: 'Tin OCOP', slug: 'tin-ocop', category: 'Hoạt động',
  summary: 'Tóm tắt bài viết', primary_image_url: 'https://example.com/news.jpg',
  published_at: '2026-09-01T00:00:00Z',
}
function mountCard(url: string | null = news.primary_image_url) {
  return mount(NewsCard, {
    props: { news: { ...news, primary_image_url: url } },
    global: { stubs: { RouterLink: RouterLinkStub } },
  })
}
describe('NewsCard', () => {
  it('renders API text, Vietnamese date and detail link', () => {
    const wrapper = mountCard()
    for (const text of [news.title, news.category, news.summary]) expect(wrapper.text()).toContain(text)
    expect(wrapper.get('time').text()).toBe(new Date(news.published_at).toLocaleDateString('vi-VN'))
    expect(wrapper.findComponent(RouterLinkStub).props('to')).toBe('/tin-tuc/tin-ocop')
  })
  it.each([null, ''])('shows a placeholder for missing image (%s)', (url) => {
    const wrapper = mountCard(url)
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
  })
  it('falls back after image error and resets for a new URL', async () => {
    const wrapper = mountCard()
    await wrapper.get('img').trigger('error')
    expect(wrapper.find('img').exists()).toBe(false)
    expect(wrapper.find('.image-placeholder').exists()).toBe(true)
    await wrapper.setProps({ news: { ...news, primary_image_url: '/new.jpg' } })
    expect(wrapper.get('img').attributes('src')).toBe('/new.jpg')
  })
  it('renders valid image', () => {
    const wrapper = mountCard()
    expect(wrapper.get('img').attributes('src')).toBe(news.primary_image_url)
    expect(wrapper.get('img').attributes('alt')).toBe(news.title)
    expect(wrapper.find('.image-placeholder').exists()).toBe(false)
  })
})