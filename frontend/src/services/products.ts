import http from '@/services/http'
import type {
  ProductDetail,
  ProductFilterOptions,
  ProductFilters,
  ProductListResponse,
  ProductSearchSuggestions,
} from '@/types/product'

export async function getProducts(filters: ProductFilters = {}): Promise<ProductListResponse> {
  const response = await http.get<ProductListResponse>('/products', { params: filters })
  return response.data
}

export async function getProduct(slug: string): Promise<ProductDetail> {
  const response = await http.get<ProductDetail>(`/products/${encodeURIComponent(slug)}`)
  return response.data
}

export async function getProductFilterOptions(): Promise<ProductFilterOptions> {
  const response = await http.get<ProductFilterOptions>('/products/filter-options')
  return response.data
}

export async function getProductSearchSuggestions(query: string): Promise<string[]> {
  const response = await http.get<ProductSearchSuggestions>('/products/suggestions', {
    params: { q: query },
  })
  return response.data.suggestions
}
