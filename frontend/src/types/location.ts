import type { ProductListItem } from '@/types/product'

export type LocationType =
  | 'tea_coffee_farm'
  | 'fruit_garden'
  | 'flower_garden'
  | 'dairy_farm'
  | 'vegetable_farm'
  | 'craft_village'
  | 'farmstay'
  | 'ocop_store'
  | 'workshop'
  | 'other'

/** Nhóm điểm trên bản đồ: điểm du lịch hoặc cửa hàng (cửa hàng OCOP, cơ sở sản xuất). */
export type LocationKind = 'attraction' | 'shop'
export type LocationKindFilter = LocationKind | 'all'
/** Vai trò của sản phẩm tại điểm. */
export type ProductRole = 'produced_here' | 'sold_here' | 'displayed'

export type LocationSort = 'name' | '-name' | 'newest' | 'rating'

export interface LocationTypeOption {
  value: LocationType
  label: string
}

export interface LocationFilterOptions {
  types: LocationTypeOption[]
  districts: string[]
}

export interface LocationListItem {
  id: number
  name: string
  slug: string
  type: LocationType
  type_label: string
  kind?: LocationKind
  district: string
  address: string
  latitude: number
  longitude: number
  opening_hours: string | null
  ticket_price: number | null
  services: string[]
  description: string | null
  rating_avg: number
  primary_image_url: string | null
}

export interface LocationListResponse {
  items: LocationListItem[]
  page: number
  page_size: number
  total: number
}

export interface LocationFilters {
  kind?: LocationKindFilter
  page?: number
  page_size?: number
  search?: string
  type?: LocationType
  district?: string
  sort?: LocationSort
}

export interface LocationImage {
  source_url?: string | null
  credit?: string | null
  license?: string | null
  id: number
  image_url: string
  is_primary: boolean
  sort_order: number
}

export interface LocationSubject {
  id: number
  name: string
  district: string
}

export interface LocationDetail extends LocationListItem {
  contact_phone: string | null
  website: string | null
  source_url: string | null
  views: number
  images: LocationImage[]
  subject: LocationSubject | null
  products: ProductListItem[]
  updated_at: string
}

export interface MapFeatureProperties {
  id: number
  slug: string
  name: string
  type: LocationType
  type_label: string
  kind?: LocationKind
  district: string
  address: string
  opening_hours: string | null
  ticket_price: number | null
  services?: string[]
  description?: string | null
  contact_phone?: string | null
  website?: string | null
  rating_avg: number
  primary_image_url: string | null
  subject?: MapSubject | null
  products?: MapProduct[]
}

export interface MapSubject {
  id: number
  name: string
  district: string
}

export interface MapProduct {
  id: number
  name: string
  slug: string
  star: number
  primary_image_url: string | null
  role?: ProductRole
}

export interface MapFeature {
  type: 'Feature'
  geometry: { type: 'Point'; coordinates: [number, number] }
  properties: MapFeatureProperties
}

export interface MapFeatureCollection {
  type: 'FeatureCollection'
  features: MapFeature[]
}

export interface MapFilters {
  search?: string
  type?: LocationType
  district?: string
  kind?: LocationKindFilter
  product_id?: number
  category?: string
  subject_id?: number
}

/** Điểm bán hoặc giới thiệu một sản phẩm (GET /products/{slug}/locations). */
export interface ProductLocationItem extends LocationListItem {
  role: ProductRole
}

export interface ProductLocationResponse {
  product_id: number
  product_name: string
  product_slug: string
  items: ProductLocationItem[]
}

/** Chủ thể kèm mọi điểm và sản phẩm công khai (GET /subjects/{id}). */
export interface PublicSubjectDetail {
  id: number
  name: string
  district: string
  address: string
  locations: LocationListItem[]
  products: ProductListItem[]
}

export interface Coordinate {
  latitude: number
  longitude: number
}

export interface NearbyLocation extends LocationListItem {
  distance_m: number
}

export interface NearbyLocationResponse {
  origin: Coordinate
  radius_m: number
  items: NearbyLocation[]
}

export interface RouteResponse {
  provider: 'OSRM'
  profile: 'driving'
  origin: Coordinate
  destination: { slug: string; name: string; latitude: number; longitude: number }
  distance_m: number
  duration_s: number
  geometry: { type: 'LineString'; coordinates: Array<[number, number]> }
}
