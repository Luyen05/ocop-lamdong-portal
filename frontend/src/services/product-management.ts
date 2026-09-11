import http from '@/services/http'
import type {
  AdminProductFilters,
  DataSourceListResponse,
  DataSourceWritePayload,
  EvidenceRole,
  ManagedProduct,
  ManagedProductListResponse,
  ProductChangeRequest,
  ProductChangeRequestListResponse,
  ProductChangeStatus,
  ProductChangeType,
  ProductModerationPayload,
  ProductEvidenceResponse,
  ProductEvidenceLinkPayload,
  ProductEvidenceLinkUpdatePayload,
  ProductDataSource,
  ProductWorkflowStatus,
  ProductWritePayload,
} from '@/types/product-management'

export async function listMyProducts(
  status?: ProductWorkflowStatus,
): Promise<ManagedProductListResponse> {
  const response = await http.get<ManagedProductListResponse>('/subject/products', {
    params: { status, page_size: 100 },
  })
  return response.data
}

export async function getMyProduct(productId: number): Promise<ManagedProduct> {
  const response = await http.get<ManagedProduct>(`/subject/products/${productId}`)
  return response.data
}

export async function createProductDraft(payload: ProductWritePayload): Promise<ManagedProduct> {
  const response = await http.post<ManagedProduct>('/subject/products', payload)
  return response.data
}

export async function updateProductDraft(
  productId: number,
  payload: ProductWritePayload,
): Promise<ManagedProduct> {
  const response = await http.put<ManagedProduct>(`/subject/products/${productId}`, payload)
  return response.data
}

export async function deleteProductDraft(productId: number): Promise<void> {
  await http.delete(`/subject/products/${productId}`)
}

export async function submitProduct(productId: number): Promise<ManagedProduct> {
  const response = await http.post<ManagedProduct>(`/subject/products/${productId}/submit`)
  return response.data
}

export async function requestProductUpdate(
  productId: number,
  proposedData: ProductWritePayload,
  reason: string,
): Promise<ProductChangeRequest> {
  const response = await http.post<ProductChangeRequest>(
    `/subject/products/${productId}/change-requests`,
    { proposed_data: proposedData, reason: reason || null },
  )
  return response.data
}

export async function requestProductDeletion(
  productId: number,
  reason: string,
): Promise<ProductChangeRequest> {
  const response = await http.post<ProductChangeRequest>(
    `/subject/products/${productId}/deletion-requests`,
    { reason },
  )
  return response.data
}

export async function listProductChangeRequests(
  scope: 'subject' | 'admin',
  filters: { status?: ProductChangeStatus; request_type?: ProductChangeType; search?: string } = {},
): Promise<ProductChangeRequestListResponse> {
  const prefix = scope === 'subject' ? '/subject' : '/admin'
  const response = await http.get<ProductChangeRequestListResponse>(
    `${prefix}/product-change-requests`,
    { params: { ...filters, page_size: 100 } },
  )
  return response.data
}

export async function listAdminProducts(
  filters: AdminProductFilters = {},
): Promise<ManagedProductListResponse> {
  const response = await http.get<ManagedProductListResponse>('/admin/products', {
    params: { ...filters, page_size: 100 },
  })
  return response.data
}

export async function getProductEvidence(productId: number): Promise<ProductEvidenceResponse> {
  const response = await http.get<ProductEvidenceResponse>(
    `/admin/products/${productId}/evidence`,
  )
  return response.data
}

export async function listDataSources(search?: string): Promise<DataSourceListResponse> {
  const response = await http.get<DataSourceListResponse>('/admin/data-sources', {
    params: { search: search || undefined, page_size: 100 },
  })
  return response.data
}

export async function createDataSource(
  payload: DataSourceWritePayload,
): Promise<ProductDataSource> {
  const response = await http.post<ProductDataSource>('/admin/data-sources', payload)
  return response.data
}

export async function updateDataSource(
  sourceId: number,
  payload: DataSourceWritePayload,
): Promise<ProductDataSource> {
  const response = await http.patch<ProductDataSource>(`/admin/data-sources/${sourceId}`, payload)
  return response.data
}

export async function linkProductEvidence(
  productId: number,
  payload: ProductEvidenceLinkPayload,
): Promise<ProductEvidenceResponse> {
  const response = await http.post<ProductEvidenceResponse>(
    `/admin/products/${productId}/evidence`,
    payload,
  )
  return response.data
}

export async function updateProductEvidenceLink(
  productId: number,
  sourceId: number,
  evidenceRole: EvidenceRole,
  payload: ProductEvidenceLinkUpdatePayload,
): Promise<ProductEvidenceResponse> {
  const response = await http.patch<ProductEvidenceResponse>(
    `/admin/products/${productId}/evidence/${sourceId}/${evidenceRole}`,
    payload,
  )
  return response.data
}

export async function unlinkProductEvidence(
  productId: number,
  sourceId: number,
  evidenceRole: EvidenceRole,
): Promise<void> {
  await http.delete(`/admin/products/${productId}/evidence/${sourceId}/${evidenceRole}`)
}

export async function moderateProduct(
  productId: number,
  payload: ProductModerationPayload,
): Promise<ManagedProduct> {
  const response = await http.patch<ManagedProduct>(
    `/admin/products/${productId}/moderation`,
    payload,
  )
  return response.data
}

export async function moderateProductChangeRequest(
  requestId: number,
  payload: ProductModerationPayload,
): Promise<ProductChangeRequest> {
  const response = await http.patch<ProductChangeRequest>(
    `/admin/product-change-requests/${requestId}/moderation`,
    payload,
  )
  return response.data
}
