import http from '@/services/http'
import type {
  AdminProductFilters,
  ManagedProduct,
  ManagedProductListResponse,
  ProductChangeRequest,
  ProductChangeRequestListResponse,
  ProductChangeStatus,
  ProductChangeType,
  ProductModerationPayload,
  ProductEvidenceResponse,
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
