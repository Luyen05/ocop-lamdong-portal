import type { ProductSort } from '@/types/product'

/** Giới hạn độ dài khớp backend (`routes/products.py`: search 150, category 150, district 100). */
export const SEARCH_MAX_LENGTH = 150
export const CATEGORY_MAX_LENGTH = 150
export const DISTRICT_MAX_LENGTH = 100

/** Backend chỉ nhận star 3 đến 5 (`Query(ge=3, le=5)`). */
export const VALID_STARS = ['3', '4', '5'] as const

export const PRODUCT_SORTS: ProductSort[] = ['newest', 'name', '-name', 'price', '-price', 'rating']

const MAX_PRICE = 1_000_000_000_000

export interface ProductFilterValues {
  search: string
  category: string
  star: string
  district: string
  minPrice: string
  maxPrice: string
  sort: ProductSort
}

export const PRICE_CONFLICT_MESSAGE = 'Giá tối thiểu không được lớn hơn giá tối đa.'

function text(value: unknown, max: number): string {
  return typeof value === 'string' ? value.trim().slice(0, max) : ''
}

/** Giá hợp lệ: số không âm (tối đa 2 chữ số thập phân). Trả chuỗi chuẩn hóa hoặc '' nếu sai. */
export function normalizePrice(value: unknown): string {
  const raw = typeof value === 'number' ? String(value) : typeof value === 'string' ? value.trim() : ''
  if (!/^\d+(\.\d{1,2})?$/.test(raw)) return ''
  const parsed = Number(raw)
  return Number.isFinite(parsed) && parsed <= MAX_PRICE ? String(parsed) : ''
}

export function priceNumber(value: string): number | undefined {
  const normalized = normalizePrice(value)
  return normalized ? Number(normalized) : undefined
}

export function hasPriceConflict(values: Pick<ProductFilterValues, 'minPrice' | 'maxPrice'>): boolean {
  const min = priceNumber(values.minPrice)
  const max = priceNumber(values.maxPrice)
  return min !== undefined && max !== undefined && min > max
}

/**
 * Chuẩn hóa mọi giá trị lọc (từ URL hoặc từ form) về dạng backend chấp nhận: bỏ giá trị sai kiểu,
 * cắt theo độ dài tối đa, chỉ nhận star 3/4/5, giá là số không âm, sắp xếp thuộc danh sách.
 * Không xử lý min > max: người gọi dùng `hasPriceConflict`.
 */
export function normalizeProductFilters(raw: Partial<Record<keyof ProductFilterValues, unknown>>): ProductFilterValues {
  const star = text(raw.star, 10)
  const sort = typeof raw.sort === 'string' ? raw.sort : ''
  return {
    search: text(raw.search, SEARCH_MAX_LENGTH),
    category: text(raw.category, CATEGORY_MAX_LENGTH),
    star: (VALID_STARS as readonly string[]).includes(star) ? star : '',
    district: text(raw.district, DISTRICT_MAX_LENGTH),
    minPrice: normalizePrice(raw.minPrice),
    maxPrice: normalizePrice(raw.maxPrice),
    sort: (PRODUCT_SORTS as string[]).includes(sort) ? (sort as ProductSort) : 'newest',
  }
}
