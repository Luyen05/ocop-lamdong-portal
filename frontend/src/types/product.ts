export interface ProductCategory {
  id: number
  name: string
  slug: string
}

export interface ProductSubject {
  id: number
  name: string
  district: string
}

export interface ProductImage {
  id: number
  image_url: string
  is_primary: boolean
  sort_order: number
}

export interface ProductListItem {
  id: number
  name: string
  slug: string
  star: number
  price: number
  unit: string
  description: string
  rating_avg: number
  primary_image_url: string | null
  category: ProductCategory
  subject: ProductSubject
  created_at: string
}

export interface ProductDetail extends ProductListItem {
  cert_code: string | null
  cert_year: number | null
  vietgap_code: string | null
  story: string | null
  ingredients: string | null
  usage_instructions: string | null
  views: number
  images: ProductImage[]
  updated_at: string
}

export type ProductSort = 'newest' | 'name' | '-name' | 'price' | '-price' | 'rating'

export interface ProductFilters {
  page?: number
  page_size?: number
  search?: string
  category?: string
  star?: number
  district?: string
  min_price?: number
  max_price?: number
  sort?: ProductSort
}

export interface ProductListResponse {
  items: ProductListItem[]
  page: number
  page_size: number
  total: number
}
