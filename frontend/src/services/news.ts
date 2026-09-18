import http from '@/services/http'
import type { NewsDetail, NewsFilters, NewsListResponse } from '@/types/news'

export async function listNews(filters: NewsFilters = {}): Promise<NewsListResponse> {
  return (await http.get<NewsListResponse>('/news', { params: filters })).data
}
export async function getNewsBySlug(slug: string): Promise<NewsDetail> {
  return (await http.get<NewsDetail>(`/news/${encodeURIComponent(slug)}`)).data
}