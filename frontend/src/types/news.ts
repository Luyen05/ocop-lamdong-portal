export interface NewsItem {
  id: string
  title: string
  summary: string
  published_at: string | null
  source_name: string
  source_url: string
  image_url: string | null
  category: string
}

export interface NewsListResponse {
  items: NewsItem[]
  page: number
  page_size: number
  total: number
}

export interface NewsFilters {
  page?: number
  page_size?: number
  search?: string
}
