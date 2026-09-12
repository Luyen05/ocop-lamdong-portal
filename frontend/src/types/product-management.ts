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
export type VerificationLevel = 'A' | 'B1' | 'B2' | 'C'
export type ProductVerificationStatus =
  | 'verified_official_decision'
  | 'verified_government_source'
  | 'pending_verification'
export type ProductEvidenceIssue =
  | 'no_recognition_source'
  | 'missing_decision'
  | 'missing_issued_at'
  | 'missing_expires_at'
export type EvidenceRole = 'recognition' | 'identity' | 'address' | 'enrichment'
export type DataSourceType =
  | 'legal_document'
  | 'recognition_decision'
  | 'government_portal'
  | 'government_news'
  | 'subject_website'
  | 'academic_reference'
  | 'other'

export interface ProductImagePayload {
  image_url: string
  storage_path?: string | null
  is_primary: boolean
  sort_order: number
}

export interface ProductImageUpload {
  image_url: string
  storage_path: string
  content_type: 'image/jpeg' | 'image/png' | 'image/webp'
  size_bytes: number
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

export interface ManagedProduct
  extends Omit<
    ProductWritePayload,
    'images' | 'cert_code' | 'cert_issued_at' | 'cert_expires_at' | 'issuing_authority' | 'certificate_url'
  > {
  id: number
  subject_id: number
  slug: string
  cert_code: string | null
  cert_issued_at: string | null
  cert_expires_at: string | null
  issuing_authority: string | null
  certificate_url: string | null
  status: ProductWorkflowStatus
  submitted_at: string | null
  reviewed_at: string | null
  moderation_note: string | null
  version: number
  category: { id: number; name: string; slug: string }
  subject: { id: number; name: string; representative: string; tax_code: string | null }
  images: Array<ProductImagePayload & { id: number }>
  verification_level: VerificationLevel | null
  verification_status: ProductVerificationStatus
  evidence_count: number
  missing_decision: boolean
  missing_issued_at: boolean
  created_at: string
  updated_at: string
}

export interface ManagedProductListResponse {
  items: ManagedProduct[]
  page: number
  page_size: number
  total: number
}

export interface ProductSnapshot
  extends Omit<
    ProductWritePayload,
    'cert_code' | 'cert_issued_at' | 'cert_expires_at' | 'issuing_authority' | 'certificate_url'
  > {
  cert_code: string | null
  cert_issued_at: string | null
  cert_expires_at: string | null
  issuing_authority: string | null
  certificate_url: string | null
}

export interface ProductChangeRequest {
  id: number
  product_id: number
  subject_id: number
  request_type: ProductChangeType
  current_data: ProductSnapshot
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

export interface ProductChangeRevisionPayload {
  proposed_data?: ProductWritePayload | null
  reason?: string | null
}

export interface ProductModerationPayload {
  status: ProductModerationDecision
  note?: string | null
}

export interface ProductDataSource {
  id: number
  title: string
  document_number: string | null
  issuing_body: string | null
  source_type: string
  published_at: string | null
  source_url: string
  local_path: string | null
  sha256: string | null
  retrieved_at: string
}

export interface DataSourceWritePayload {
  title: string
  document_number: string | null
  issuing_body: string | null
  source_type: DataSourceType
  published_at: string | null
  source_url: string
  retrieved_at: string
}

export interface DataSourceListResponse {
  items: ProductDataSource[]
  page: number
  page_size: number
  total: number
}

export interface ProductEvidenceSource {
  evidence_role: EvidenceRole
  verification_level: VerificationLevel
  original_address: string | null
  verified_at: string
  notes: string | null
  source: ProductDataSource
}

export interface ProductEvidenceLinkPayload {
  source_id: number
  evidence_role: EvidenceRole
  verification_level: VerificationLevel
  original_address: string | null
  verified_at: string
  notes: string | null
}

export type ProductEvidenceLinkUpdatePayload = Omit<
  ProductEvidenceLinkPayload,
  'source_id' | 'evidence_role'
>

export interface ProductEvidenceResponse {
  product_id: number
  product_name: string
  verification_level: VerificationLevel | null
  verification_status: ProductVerificationStatus
  evidence_count: number
  issues: ProductEvidenceIssue[]
  sources: ProductEvidenceSource[]
}

export interface AdminProductFilters {
  status?: ProductWorkflowStatus
  search?: string
  verification_level?: VerificationLevel
  verification_status?: ProductVerificationStatus
  missing_decision?: boolean
  missing_issued_at?: boolean
}
