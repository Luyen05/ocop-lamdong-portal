import http from '@/services/http'
import type {
  AdminLocationFilters,
  CoordinateParseResult,
  LocationChangeRequest,
  LocationChangeRequestListResponse,
  LocationChangeStatus,
  LocationDraftPayload,
  LocationImageUpload,
  LocationModerationPayload,
  LocationModerationStatus,
  LocationPositionCheck,
  LocationWorkflowStatus,
  LocationWritePayload,
  ManagedLocation,
  ManagedLocationListResponse,
} from '@/types/location-management'

// ---------------------------------------------------------------------------
// Chủ thể
// ---------------------------------------------------------------------------

export async function listMyLocations(status?: LocationWorkflowStatus): Promise<ManagedLocationListResponse> {
  const response = await http.get<ManagedLocationListResponse>('/subject/locations', {
    params: { status, page_size: 100 },
  })
  return response.data
}

export async function getMyLocation(locationId: number): Promise<ManagedLocation> {
  const response = await http.get<ManagedLocation>(`/subject/locations/${locationId}`)
  return response.data
}

export async function createLocationDraft(payload: LocationDraftPayload): Promise<ManagedLocation> {
  const response = await http.post<ManagedLocation>('/subject/locations', payload)
  return response.data
}

export async function updateLocationDraft(
  locationId: number,
  payload: LocationDraftPayload,
): Promise<ManagedLocation> {
  const response = await http.patch<ManagedLocation>(`/subject/locations/${locationId}`, payload)
  return response.data
}

export async function deleteLocationDraft(locationId: number): Promise<void> {
  await http.delete(`/subject/locations/${locationId}`)
}

export async function submitLocation(locationId: number): Promise<ManagedLocation> {
  const response = await http.post<ManagedLocation>(`/subject/locations/${locationId}/submit`)
  return response.data
}

export async function checkLocationPosition(
  latitude: number,
  longitude: number,
  excludeId?: number | null,
): Promise<LocationPositionCheck> {
  const response = await http.get<LocationPositionCheck>('/subject/locations/position-check', {
    params: { latitude, longitude, exclude_id: excludeId ?? undefined },
  })
  return response.data
}

export async function parseCoordinates(text: string): Promise<CoordinateParseResult> {
  const response = await http.post<CoordinateParseResult>('/subject/locations/parse-coordinates', { text })
  return response.data
}

export async function uploadLocationImage(file: File): Promise<LocationImageUpload> {
  const formData = new FormData()
  formData.append('file', file)
  const response = await http.post<LocationImageUpload>('/subject/location-images', formData)
  return response.data
}

export async function deleteTemporaryLocationImage(storagePath: string): Promise<void> {
  const fileName = storagePath.split('/').pop()
  if (!fileName) return
  await http.delete(`/subject/location-images/${encodeURIComponent(fileName)}`)
}

export async function requestLocationUpdate(
  locationId: number,
  proposedData: LocationWritePayload,
  reason: string,
): Promise<LocationChangeRequest> {
  const response = await http.post<LocationChangeRequest>(
    `/subject/locations/${locationId}/change-requests`,
    { proposed_data: proposedData, reason: reason || null },
  )
  return response.data
}

export async function requestLocationDeletion(locationId: number, reason: string): Promise<LocationChangeRequest> {
  const response = await http.post<LocationChangeRequest>(
    `/subject/locations/${locationId}/deletion-requests`,
    { reason },
  )
  return response.data
}

export async function listMyLocationChangeRequests(
  status?: LocationChangeStatus,
): Promise<LocationChangeRequestListResponse> {
  const response = await http.get<LocationChangeRequestListResponse>('/subject/location-change-requests', {
    params: { status, page_size: 100 },
  })
  return response.data
}

export async function getMyLocationChangeRequest(requestId: number): Promise<LocationChangeRequest> {
  const response = await http.get<LocationChangeRequest>(`/subject/location-change-requests/${requestId}`)
  return response.data
}

export async function resubmitLocationChangeRequest(
  requestId: number,
  payload: { proposed_data: LocationWritePayload | null; reason: string | null },
): Promise<LocationChangeRequest> {
  const response = await http.put<LocationChangeRequest>(`/subject/location-change-requests/${requestId}`, payload)
  return response.data
}

export async function cancelLocationChangeRequest(requestId: number): Promise<LocationChangeRequest> {
  const response = await http.post<LocationChangeRequest>(`/subject/location-change-requests/${requestId}/cancel`)
  return response.data
}

// ---------------------------------------------------------------------------
// Quản trị
// ---------------------------------------------------------------------------

export async function listAdminLocations(filters: AdminLocationFilters): Promise<ManagedLocationListResponse> {
  const response = await http.get<ManagedLocationListResponse>('/admin/locations', { params: filters })
  return response.data
}

export async function getAdminLocation(locationId: number): Promise<ManagedLocation> {
  const response = await http.get<ManagedLocation>(`/admin/locations/${locationId}`)
  return response.data
}

export async function moderateLocation(
  locationId: number,
  payload: LocationModerationPayload,
): Promise<ManagedLocation> {
  const response = await http.patch<ManagedLocation>(`/admin/locations/${locationId}/moderation`, payload)
  return response.data
}

export async function listAdminLocationChangeRequests(
  status?: LocationChangeStatus,
): Promise<LocationChangeRequestListResponse> {
  const response = await http.get<LocationChangeRequestListResponse>('/admin/location-change-requests', {
    params: { status, page_size: 100 },
  })
  return response.data
}

export async function getAdminLocationChangeRequest(requestId: number): Promise<LocationChangeRequest> {
  const response = await http.get<LocationChangeRequest>(`/admin/location-change-requests/${requestId}`)
  return response.data
}

export async function moderateLocationChangeRequest(
  requestId: number,
  payload: { status: LocationModerationStatus; note: string | null },
): Promise<LocationChangeRequest> {
  const response = await http.patch<LocationChangeRequest>(
    `/admin/location-change-requests/${requestId}/moderation`,
    payload,
  )
  return response.data
}
