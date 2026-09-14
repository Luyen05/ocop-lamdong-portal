import http from '@/services/http'
import type { NewsFilters, NewsListResponse } from '@/types/news'

export async function getNews(filters: NewsFilters = {}): Promise<NewsListResponse> {
  const response = await http.get<NewsListResponse>('/news', { params: filters })
  return response.data
}
