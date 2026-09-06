import http from '@/services/http'
import type {
  ProductDetail,
  ProductFilters,
  ProductListResponse,
} from '@/types/product'

export async function getProducts(filters: ProductFilters = {}): Promise<ProductListResponse> {
  const response = await http.get<ProductListResponse>('/products', { params: filters })
  return response.data
}

export async function getProduct(slug: string): Promise<ProductDetail> {
  const response = await http.get<ProductDetail>(`/products/${encodeURIComponent(slug)}`)
  return response.data
}
