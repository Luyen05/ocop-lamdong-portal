// @vitest-environment jsdom
import { mount } from '@vue/test-utils'
import { describe, expect, it } from 'vitest'

import type { NewsItem } from '@/types/news'

import NewsCard from '../NewsCard.vue'

const article: NewsItem = {
  id: 'tin-1',
  title: 'Hội chợ OCOP',
  summary: 'Tóm tắt',
  category: 'Tin OCOP',
  image_url: null,
  published_at: '2026-09-01T00:00:00Z',
  source_url: 'https://example.com/tin-1',
} as NewsItem

describe('NewsCard', () => {
  it('bài chưa có ảnh dùng ảnh cảnh quan trang trí, ổn định giữa các lần hiển thị', () => {
    const first = mount(NewsCard, { props: { article } }).get('.news-placeholder-photo').attributes('src')
    const second = mount(NewsCard, { props: { article } }).get('.news-placeholder-photo').attributes('src')
    expect(first).toMatch(/^\/assets\/images\/photos\//)
    expect(second).toBe(first)
  })

  it('có ảnh thì hiện ảnh của bài', () => {
    const wrapper = mount(NewsCard, { props: { article: { ...article, image_url: 'https://example.com/a.jpg' } } })
    expect(wrapper.find('.news-placeholder').exists()).toBe(false)
    expect(wrapper.get('img').attributes('src')).toBe('https://example.com/a.jpg')
  })
})
