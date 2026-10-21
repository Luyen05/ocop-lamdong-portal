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

/** Danh mục trong trang quản trị: gồm cả danh mục ẩn và số sản phẩm đang thuộc danh mục. */
export interface AdminCategory extends Category {
  is_visible: boolean
  sort_order: number
  product_count: number
}

export interface AdminCategoryListResponse {
  items: AdminCategory[]
  total: number
}

export interface AdminCategoryPayload {
  name: string
  /** Để trống khi tạo mới thì máy chủ tự sinh từ tên không dấu. */
  slug?: string
  description: string | null
  icon: string | null
  is_visible: boolean
  sort_order: number
}
