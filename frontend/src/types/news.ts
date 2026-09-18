export interface NewsListItem {
  id: number
  title: string
  slug: string
  category: string
  summary: string
  primary_image_url: string | null
  published_at: string
}
export interface NewsImage {
  id: number
  image_url: string
  is_primary: boolean
  sort_order: number
}
export interface NewsDetail extends NewsListItem {
  content: string
  views: number
  images: NewsImage[]
  updated_at: string
}
export interface NewsListResponse {
  items: NewsListItem[]
  page: number
  page_size: number
  total: number
}
export interface NewsFilters {
  page?: number
  page_size?: number
  search?: string
  category?: string
}