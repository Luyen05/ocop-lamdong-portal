import http from '@/services/http'
import type {
  Coordinate,
  LocationDetail,
  LocationFilterOptions,
  LocationFilters,
  LocationListResponse,
  LocationKindFilter,
  LocationType,
  MapFeatureCollection,
  MapFilters,
  NearbyLocationResponse,
  ProductLocationResponse,
  PublicSubjectDetail,
  RouteResponse,
} from '@/types/location'

export async function getLocations(filters: LocationFilters = {}): Promise<LocationListResponse> {
  const response = await http.get<LocationListResponse>('/locations', { params: filters })
  return response.data
}

export async function getLocation(slug: string): Promise<LocationDetail> {
  const response = await http.get<LocationDetail>(`/locations/${encodeURIComponent(slug)}`)
  return response.data
}

export async function getLocationFilterOptions(
  kind: LocationKindFilter = 'attraction',
): Promise<LocationFilterOptions> {
  const response = await http.get<LocationFilterOptions>('/locations/filter-options', { params: { kind } })
  return response.data
}

export async function getMapLocations(filters: MapFilters = {}): Promise<MapFeatureCollection> {
  const response = await http.get<MapFeatureCollection>('/map/locations', { params: filters })
  return response.data
}

export async function getNearbyLocations(
  origin: Coordinate,
  options: { radiusKm?: number; limit?: number; type?: LocationType; kind?: LocationKindFilter } = {},
): Promise<NearbyLocationResponse> {
  const response = await http.get<NearbyLocationResponse>('/map/nearby', {
    params: {
      latitude: origin.latitude,
      longitude: origin.longitude,
      radius_km: options.radiusKm,
      limit: options.limit,
      type: options.type,
      kind: options.kind,
    },
  })
  return response.data
}

export async function getRoute(destinationSlug: string, origin: Coordinate): Promise<RouteResponse> {
  const response = await http.get<RouteResponse>('/map/route', {
    params: {
      destination: destinationSlug,
      from_latitude: origin.latitude,
      from_longitude: origin.longitude,
    },
    // Dịch vụ OSRM bên ngoài có thể chậm hơn các API nội bộ.
    timeout: 20_000,
  })
  return response.data
}

/** Nơi mua, xem hoặc sản xuất một sản phẩm (cửa hàng và điểm du lịch đã duyệt). */
export async function getProductLocations(slug: string): Promise<ProductLocationResponse> {
  const response = await http.get<ProductLocationResponse>(
    `/products/${encodeURIComponent(slug)}/locations`,
  )
  return response.data
}

/** Chủ thể đã duyệt cùng mọi điểm và sản phẩm công khai của chủ thể. */
export async function getPublicSubject(id: number): Promise<PublicSubjectDetail> {
  const response = await http.get<PublicSubjectDetail>(`/subjects/${id}`)
  return response.data
}
