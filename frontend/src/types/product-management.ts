export type ProductWorkflowStatus =
  | 'draft'
  | 'pending'
  | 'needs_revision'
  | 'approved'
  | 'rejected'
  | 'suspended'
  | 'archived'

export type ProductModerationDecision = 'approved' | 'needs_revision' | 'rejected'
export type ProductChangeType = 'update' | 'delete'
export type ProductChangeStatus =
  | 'pending'
  | 'needs_revision'
  | 'approved'
  | 'rejected'
  | 'cancelled'

export interface ProductImagePayload {
  image_url: string
  is_primary: boolean
  sort_order: number
}

export interface ProductWritePayload {
  category_id: number
  name: string
  star: number
  price: string
  unit: string
  cert_code: string
  cert_issued_at: string
  cert_expires_at: string
  issuing_authority: string
  certificate_url: string
  vietgap_code: string | null
  description: string
  story: string | null
  ingredients: string | null
  usage_instructions: string | null
  images: ProductImagePayload[]
}

export interface ManagedProduct extends Omit<ProductWritePayload, 'images'> {
  id: number
  subject_id: number
  slug: string
  status: ProductWorkflowStatus
  submitted_at: string | null
  reviewed_at: string | null
  moderation_note: string | null
  version: number
  category: { id: number; name: string; slug: string }
  subject: { id: number; name: string; representative: string; tax_code: string | null }
  images: Array<ProductImagePayload & { id: number }>
  created_at: string
  updated_at: string
}

export interface ManagedProductListResponse {
  items: ManagedProduct[]
  page: number
  page_size: number
  total: number
}

export interface ProductChangeRequest {
  id: number
  product_id: number
  subject_id: number
  request_type: ProductChangeType
  proposed_data: ProductWritePayload | null
  reason: string | null
  status: ProductChangeStatus
  base_version: number
  submitted_at: string
  reviewed_at: string | null
  review_note: string | null
  product_name: string
  subject_name: string
  created_at: string
  updated_at: string
}

export interface ProductChangeRequestListResponse {
  items: ProductChangeRequest[]
  page: number
  page_size: number
  total: number
}

export interface ProductModerationPayload {
  status: ProductModerationDecision
  note?: string | null
}
