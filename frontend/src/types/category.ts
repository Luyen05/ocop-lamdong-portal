export interface Category {
  id: number
  name: string
  slug: string
  description: string | null
  icon: string | null
}

export interface CategoryListResponse {
  items: Category[]
  page: number
  page_size: number
  total: number
}
