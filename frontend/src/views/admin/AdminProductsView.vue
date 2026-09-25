<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ProductEvidenceManager from '@/components/admin/ProductEvidenceManager.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import { getApiErrorMessage } from '@/services/api-error'
import {
  downloadProductCertificate,
  getProductEvidence,
  listAdminProducts,
  listProductChangeRequests,
  moderateProduct,
  moderateProductChangeRequest,
} from '@/services/product-management'
import type {
  AdminProductFilters,
  ManagedProduct,
  ProductChangeRequest,
  ProductEvidenceResponse,
  ProductModerationDecision,
  ProductSnapshot,
  ProductVerificationStatus,
  ProductWorkflowStatus,
  ProductWritePayload,
  VerificationLevel,
} from '@/types/product-management'

type EvidenceIssueFilter = '' | 'missing_decision' | 'missing_issued_at'
type ComparableProductField = Exclude<keyof ProductWritePayload, 'images'>

const comparisonFields: Array<{ key: ComparableProductField; label: string }> = [
  { key: 'name', label: 'Tên sản phẩm' },
  { key: 'category_id', label: 'Mã danh mục' },
  { key: 'star', label: 'Hạng sao' },
  { key: 'price', label: 'Giá tham khảo' },
  { key: 'unit', label: 'Đơn vị tính' },
  { key: 'cert_code', label: 'Mã chứng nhận' },
  { key: 'cert_issued_at', label: 'Ngày cấp' },
  { key: 'cert_expires_at', label: 'Ngày hết hạn' },
  { key: 'issuing_authority', label: 'Cơ quan công nhận' },
  { key: 'certificate_url', label: 'Tài liệu chứng nhận' },
  { key: 'description', label: 'Mô tả' },
]

const products = ref<ManagedProduct[]>([])
const productTotal = ref(0)
const page = ref(1)
const pageSize = 20
const requests = ref<ProductChangeRequest[]>([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const activeTab = ref<'products' | 'changes'>('products')
const selectedProduct = ref<ManagedProduct | null>(null)
const selectedRequest = ref<ProductChangeRequest | null>(null)
const evidence = ref<ProductEvidenceResponse | null>(null)
const evidenceLoading = ref(false)
const evidenceError = ref('')
const decision = ref<ProductModerationDecision>('approved')
const reviewNote = ref('')
const submitting = ref(false)
const brokenProductImages = ref(new Set<number>())
const showAdvancedFilters = ref(false)
const showExceptionalAction = ref(false)
const downloadingCertificate = ref(false)
const reviewDialog = ref<HTMLElement | null>(null)

const search = ref('')
const workflowStatus = ref<ProductWorkflowStatus | ''>('pending')
const verificationLevel = ref<VerificationLevel | ''>('')
const verificationStatus = ref<ProductVerificationStatus | ''>('')
const evidenceIssue = ref<EvidenceIssueFilter>('')

const pendingProducts = computed(() => products.value.filter((item) => item.status === 'pending'))
const pendingRequests = computed(() => requests.value.filter((item) => item.status === 'pending'))
const canModerateSelectedProduct = computed(() => selectedProduct.value?.status === 'pending')
const canModerateSelectedRequest = computed(() => selectedRequest.value?.status === 'pending')
const totalPages = computed(() => Math.max(1, Math.ceil(productTotal.value / pageSize)))
const isReviewDialogOpen = computed(() => Boolean(selectedProduct.value || selectedRequest.value))
const modalTitle = computed(() => {
  if (selectedProduct.value) {
    return canModerateSelectedProduct.value ? 'Kiểm tra và duyệt sản phẩm' : 'Hồ sơ và chứng cứ sản phẩm'
  }
  if (selectedRequest.value?.request_type === 'update') return 'Duyệt yêu cầu cập nhật'
  return 'Duyệt yêu cầu ngừng hiển thị'
})
const selectedProductWarnings = computed(() => {
  const product = selectedProduct.value
  if (!product) return []
  const warnings: string[] = []
  if (!product.description || !product.star || !product.cert_code || !product.cert_issued_at || !product.cert_expires_at || !product.issuing_authority) {
    warnings.push('Hồ sơ còn thiếu thông tin bắt buộc.')
  }
  if (!product.certificate_storage_path && !product.certificate_url) warnings.push('Chưa có tài liệu chứng nhận.')
  if (!product.images.some((image) => image.is_primary)) warnings.push('Chưa có ảnh đại diện.')
  if (product.cert_expires_at && new Date(product.cert_expires_at) < new Date(new Date().toDateString())) warnings.push('Giấy chứng nhận đã hết hạn.')
  if (product.subject.status && product.subject.status !== 'approved') warnings.push('Hồ sơ chủ thể không còn ở trạng thái đã duyệt.')
  if (product.subject.is_active === false) warnings.push('Tài khoản chủ thể đang bị khóa.')
  return warnings
})

function buildProductFilters(): AdminProductFilters {
  const filters: AdminProductFilters = { page: page.value, page_size: pageSize }
  const normalizedSearch = search.value.trim()
  if (normalizedSearch) filters.search = normalizedSearch
  if (workflowStatus.value) filters.status = workflowStatus.value
  if (verificationLevel.value) filters.verification_level = verificationLevel.value
  if (verificationStatus.value) filters.verification_status = verificationStatus.value
  if (evidenceIssue.value === 'missing_decision') filters.missing_decision = true
  if (evidenceIssue.value === 'missing_issued_at') filters.missing_issued_at = true
  return filters
}

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const [productData, requestData] = await Promise.all([
      listAdminProducts(buildProductFilters()),
      listProductChangeRequests('admin'),
    ])
    products.value = productData.items
    productTotal.value = productData.total
    requests.value = requestData.items
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải dữ liệu quản lý sản phẩm.')
  } finally {
    loading.value = false
  }
}

async function applyFilters(): Promise<void> {
  successMessage.value = ''
  page.value = 1
  await loadData()
}

async function resetFilters(): Promise<void> {
  search.value = ''
  workflowStatus.value = 'pending'
  verificationLevel.value = ''
  verificationStatus.value = ''
  evidenceIssue.value = ''
  showAdvancedFilters.value = false
  page.value = 1
  await loadData()
}

async function changePage(nextPage: number): Promise<void> {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
  page.value = nextPage
  await loadData()
}

async function openProduct(product: ManagedProduct): Promise<void> {
  selectedRequest.value = null
  selectedProduct.value = product
  evidence.value = null
  evidenceError.value = ''
  decision.value = 'approved'
  reviewNote.value = ''
  showExceptionalAction.value = false
  evidenceLoading.value = true
  try {
    evidence.value = await getProductEvidence(product.id)
  } catch (error) {
    evidenceError.value = getApiErrorMessage(error, 'Không thể tải chứng cứ của sản phẩm.')
  } finally {
    evidenceLoading.value = false
  }
}

function openRequest(request: ProductChangeRequest): void {
  selectedProduct.value = null
  selectedRequest.value = request
  evidence.value = null
  decision.value = 'approved'
  reviewNote.value = ''
}

function closeModal(force = false): void {
  if (submitting.value && !force) return
  selectedProduct.value = null
  selectedRequest.value = null
  evidence.value = null
  evidenceError.value = ''
}

useDialogFocus(isReviewDialogOpen, reviewDialog, () => closeModal())

async function openCertificate(scope: 'subject' | 'admin', productId: number): Promise<void> {
  downloadingCertificate.value = true
  evidenceError.value = ''
  try {
    const blob = await downloadProductCertificate(scope, productId)
    const url = URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.target = '_blank'
    link.rel = 'noopener'
    link.click()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  } catch (error) {
    evidenceError.value = getApiErrorMessage(error, 'Không thể mở file chứng nhận.')
  } finally {
    downloadingCertificate.value = false
  }
}

async function submitDecision(): Promise<void> {
  if (selectedProduct.value && !canModerateSelectedProduct.value) return
  if (selectedRequest.value && !canModerateSelectedRequest.value) return
  if ((decision.value === 'needs_revision' || decision.value === 'rejected') && !reviewNote.value.trim()) {
    errorMessage.value = 'Cần nhập nội dung phản hồi khi yêu cầu bổ sung hoặc từ chối.'
    return
  }
  const targetLabel = selectedProduct.value
    ? `sản phẩm “${selectedProduct.value.name}”`
    : selectedRequest.value?.request_type === 'delete'
      ? `yêu cầu ngừng hiển thị “${selectedRequest.value.product_name}”`
      : `yêu cầu cập nhật “${selectedRequest.value?.product_name || ''}”`
  const actionLabel = {
    approved: 'chấp thuận',
    needs_revision: 'yêu cầu bổ sung',
    rejected: 'từ chối',
  }[decision.value]
  if (!window.confirm(`Xác nhận ${actionLabel} ${targetLabel}?`)) return
  submitting.value = true
  errorMessage.value = ''
  try {
    const payload = { status: decision.value, note: reviewNote.value.trim() || null }
    if (selectedProduct.value) {
      await moderateProduct(selectedProduct.value.id, payload)
    } else if (selectedRequest.value) {
      await moderateProductChangeRequest(selectedRequest.value.id, payload)
    }
    successMessage.value =
      decision.value === 'approved'
        ? 'Đã chấp thuận yêu cầu kiểm duyệt.'
        : decision.value === 'needs_revision'
          ? 'Đã gửi yêu cầu bổ sung cho chủ thể.'
          : 'Đã từ chối yêu cầu và lưu lý do.'
    closeModal(true)
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể xử lý yêu cầu kiểm duyệt.')
  } finally {
    submitting.value = false
  }
}

function updateEvidenceSummary(nextEvidence: ProductEvidenceResponse): void {
  evidence.value = nextEvidence
  const product = products.value.find((item) => item.id === nextEvidence.product_id)
  if (!product) return
  product.verification_level = nextEvidence.verification_level
  product.verification_status = nextEvidence.verification_status
  product.evidence_count = nextEvidence.evidence_count
  product.missing_decision = nextEvidence.issues.includes('missing_decision')
  product.missing_issued_at = nextEvidence.issues.includes('missing_issued_at')
}

function markImageBroken(productId: number): void {
  brokenProductImages.value = new Set([...brokenProductImages.value, productId])
}

function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat('vi-VN').format(new Date(value)) : 'Chưa có'
}

function formatDateTime(value: string | null): string {
  return value
    ? new Intl.DateTimeFormat('vi-VN', { dateStyle: 'short', timeStyle: 'short' }).format(new Date(value))
    : 'Chưa có'
}

function comparisonValue(
  data: ProductWritePayload | ProductSnapshot | null,
  field: ComparableProductField,
): string {
  const value = data?.[field]
  return value === null || value === undefined ? '—' : String(value)
}

function fieldChanged(request: ProductChangeRequest, field: ComparableProductField): boolean {
  return comparisonValue(request.current_data, field) !== comparisonValue(request.proposed_data, field)
}

function workflowLabel(status: ProductWorkflowStatus): string {
  return {
    draft: 'Bản nháp',
    pending: 'Chờ duyệt',
    needs_revision: 'Cần bổ sung',
    approved: 'Đã công khai',
    rejected: 'Bị từ chối',
    suspended: 'Tạm ẩn',
    archived: 'Đã lưu trữ',
  }[status]
}

function verificationLabel(status: ProductVerificationStatus): string {
  return {
    verified_official_decision: 'Đã đối chiếu quyết định',
    verified_government_source: 'Đã có nguồn cơ quan nhà nước',
    pending_verification: 'Chờ xác minh nguồn',
  }[status]
}

onMounted(loadData)
</script>

<template>
  <main class="admin-products-page">
    <header class="page-heading">
      <div>
        <span>Kiểm duyệt dữ liệu OCOP</span>
        <h1>Quản lý sản phẩm và chứng cứ</h1>
        <p>Quản trị viên đối chiếu nguồn công nhận, hồ sơ chứng nhận và quyết định trước khi công khai.</p>
      </div>
      <div class="summary-badge">{{ pendingProducts.length + pendingRequests.length }} yêu cầu chờ xử lý</div>
    </header>

    <div v-if="errorMessage" class="alert alert-danger" role="alert">{{ errorMessage }}</div>
    <div v-if="successMessage" class="alert alert-success" role="status">{{ successMessage }}</div>

    <nav class="tab-list" aria-label="Loại dữ liệu sản phẩm">
      <button :class="{ active: activeTab === 'products' }" type="button" @click="activeTab = 'products'">
        Sản phẩm <span>{{ productTotal }}</span>
      </button>
      <button :class="{ active: activeTab === 'changes' }" type="button" @click="activeTab = 'changes'">
        Sửa / ngừng hiển thị <span>{{ requests.length }}</span>
      </button>
    </nav>

    <form v-if="activeTab === 'products'" class="filter-panel" @submit.prevent="applyFilters">
      <div class="basic-filters">
        <label class="search-field">Tìm sản phẩm hoặc chủ thể
          <input v-model="search" type="search" placeholder="Tên, mã chứng nhận, chủ thể..." />
        </label>
        <label>Trạng thái
          <select v-model="workflowStatus">
            <option value="">Tất cả</option>
            <option value="pending">Chờ duyệt</option>
            <option value="needs_revision">Cần bổ sung</option>
            <option value="approved">Đã công khai</option>
            <option value="draft">Bản nháp</option>
            <option value="rejected">Bị từ chối</option>
            <option value="suspended">Tạm ẩn</option>
            <option value="archived">Đã lưu trữ</option>
          </select>
        </label>
        <div class="filter-actions">
          <button type="button" :aria-expanded="showAdvancedFilters" @click="showAdvancedFilters = !showAdvancedFilters">
            {{ showAdvancedFilters ? 'Ẩn nâng cao' : 'Bộ lọc nâng cao' }}
          </button>
          <button type="button" @click="resetFilters">Đặt lại</button>
          <button class="primary-button" type="submit">Áp dụng</button>
        </div>
      </div>
      <div v-if="showAdvancedFilters" class="advanced-filters">
        <label>Cấp nguồn cao nhất
          <select v-model="verificationLevel">
            <option value="">Tất cả</option>
            <option value="A">A — Quyết định chính thức</option>
            <option value="B1">B1 — Cơ quan nhà nước</option>
            <option value="B2">B2 — Đề xuất/chấm điểm</option>
            <option value="C">C — Nguồn chủ thể</option>
          </select>
        </label>
        <label>Trạng thái xác minh
          <select v-model="verificationStatus">
            <option value="">Tất cả</option>
            <option value="verified_official_decision">Có quyết định chính thức</option>
            <option value="verified_government_source">Có nguồn cơ quan nhà nước</option>
            <option value="pending_verification">Chờ xác minh</option>
          </select>
        </label>
        <label>Vấn đề hồ sơ
          <select v-model="evidenceIssue">
            <option value="">Tất cả</option>
            <option value="missing_decision">Thiếu số quyết định</option>
            <option value="missing_issued_at">Thiếu ngày cấp</option>
          </select>
        </label>
      </div>
    </form>

    <section class="queue-panel">
      <p v-if="loading" class="empty-state">Đang tải dữ liệu...</p>
      <template v-else-if="activeTab === 'products'">
        <p v-if="!products.length" class="empty-state">Không tìm thấy sản phẩm phù hợp bộ lọc.</p>
        <article v-for="product in products" v-else :key="product.id">
          <img
            v-if="product.images.find((image) => image.is_primary)?.image_url && !brokenProductImages.has(product.id)"
            :src="product.images.find((image) => image.is_primary)?.image_url"
            :alt="`Ảnh ${product.name}`"
            @error="markImageBroken(product.id)"
          />
          <span v-else class="request-symbol">◇</span>
          <div class="product-summary">
            <small>Hồ sơ #{{ product.id }} · cập nhật {{ formatDate(product.updated_at) }}</small>
            <h2>{{ product.name }}</h2>
            <p>{{ product.subject.name }} · {{ product.star }} sao · {{ product.cert_code || 'Chưa có mã chứng nhận' }}</p>
            <div class="status-row">
              <span class="status-chip" :data-status="product.status">{{ workflowLabel(product.status) }}</span>
              <span class="status-chip verification">{{ verificationLabel(product.verification_status) }}</span>
              <span v-if="product.verification_level" class="level-chip">Nguồn {{ product.verification_level }}</span>
              <span v-if="product.missing_decision" class="issue-chip">Thiếu quyết định</span>
              <span v-if="product.missing_issued_at" class="issue-chip">Thiếu ngày cấp</span>
            </div>
          </div>
          <button type="button" @click="openProduct(product)">
            {{ product.status === 'pending' ? 'Kiểm tra hồ sơ' : 'Xem hồ sơ' }}
          </button>
        </article>
        <nav v-if="productTotal > pageSize" class="pagination-bar" aria-label="Phân trang sản phẩm">
          <span>Trang {{ page }} / {{ totalPages }} · {{ productTotal }} sản phẩm</span>
          <div>
            <button type="button" :disabled="page <= 1 || loading" @click="changePage(page - 1)"><AppIcon name="chevronLeft" :size="13" /> Trước</button>
            <button type="button" :disabled="page >= totalPages || loading" @click="changePage(page + 1)">Sau <AppIcon name="chevronRight" :size="13" /></button>
          </div>
        </nav>
      </template>
      <template v-else>
        <p v-if="!requests.length" class="empty-state">Chưa có yêu cầu thay đổi sản phẩm.</p>
        <article v-for="request in requests" v-else :key="request.id">
          <span class="request-symbol"><AppIcon :name="request.request_type === 'update' ? 'refresh' : 'close'" :size="16" /></span>
          <div>
            <small>Yêu cầu #{{ request.id }} · gửi {{ formatDate(request.submitted_at) }}</small>
            <h2>{{ request.product_name }}</h2>
            <p>{{ request.subject_name }} · {{ request.request_type === 'update' ? 'Đề nghị cập nhật thông tin' : 'Đề nghị ngừng hiển thị' }}</p>
            <div class="status-row">
              <span class="status-chip" :data-status="request.status">{{ request.status === 'pending' ? 'Chờ duyệt' : request.status === 'approved' ? 'Đã duyệt' : request.status === 'needs_revision' ? 'Cần bổ sung' : request.status === 'cancelled' ? 'Đã hủy' : 'Bị từ chối' }}</span>
            </div>
          </div>
          <button type="button" @click="openRequest(request)">{{ request.status === 'pending' ? 'Kiểm tra yêu cầu' : 'Xem lần xử lý' }}</button>
        </article>
      </template>
    </section>

    <div v-if="selectedProduct || selectedRequest" class="modal-backdrop" role="presentation" @click.self="closeModal()">
      <form
        ref="reviewDialog"
        class="review-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="product-review-title"
        tabindex="-1"
        @submit.prevent="submitDecision"
      >
        <header>
          <div>
            <span>Kiểm duyệt sản phẩm</span>
            <h2 id="product-review-title">{{ modalTitle }}</h2>
          </div>
          <button type="button" aria-label="Đóng" @click="closeModal()"><AppIcon name="close" :size="17" /></button>
        </header>

        <template v-if="selectedProduct">
          <section class="subject-box">
            <div><small>Chủ thể</small><strong>{{ selectedProduct.subject.name }}</strong></div>
            <div><small>Người đại diện</small><strong>{{ selectedProduct.subject.representative }}</strong></div>
            <div><small>Mã số thuế</small><strong>{{ selectedProduct.subject.tax_code || '—' }}</strong></div>
          </section>
          <section class="review-grid">
            <div><small>Tên sản phẩm</small><strong>{{ selectedProduct.name }}</strong></div>
            <div><small>Danh mục</small><strong>{{ selectedProduct.category.name }}</strong></div>
            <div><small>Hạng sao khai báo</small><strong>{{ selectedProduct.star }} sao</strong></div>
            <div><small>Mã chứng nhận</small><strong>{{ selectedProduct.cert_code || 'Chưa có' }}</strong></div>
            <div><small>Ngày cấp</small><strong>{{ formatDate(selectedProduct.cert_issued_at) }}</strong></div>
            <div><small>Ngày hết hạn</small><strong>{{ formatDate(selectedProduct.cert_expires_at) }}</strong></div>
            <div class="wide"><small>Cơ quan công nhận</small><strong>{{ selectedProduct.issuing_authority || 'Chưa có' }}</strong></div>
          </section>
          <section v-if="selectedProduct.reviewed_at" class="last-review-box">
            <div><small>Lần xử lý gần nhất</small><strong>{{ workflowLabel(selectedProduct.status) }}</strong></div>
            <div><small>Người xử lý</small><strong>{{ selectedProduct.reviewed_by_name || 'Quản trị viên' }}</strong></div>
            <div><small>Thời điểm</small><strong>{{ formatDateTime(selectedProduct.reviewed_at) }}</strong></div>
            <p v-if="selectedProduct.moderation_note"><strong>Ghi chú:</strong> {{ selectedProduct.moderation_note }}</p>
          </section>
          <div class="document-links">
            <button
              v-if="selectedProduct.certificate_storage_path"
              type="button"
              :disabled="downloadingCertificate"
              @click="openCertificate('admin', selectedProduct.id)"
            >{{ downloadingCertificate ? 'Đang mở...' : 'Mở file chứng nhận ↗' }}</button>
            <a v-else-if="selectedProduct.certificate_url" :href="selectedProduct.certificate_url" target="_blank" rel="noopener">Mở tài liệu chứng nhận ↗</a>
            <a v-if="selectedProduct.images[0]?.image_url" :href="selectedProduct.images[0].image_url" target="_blank" rel="noopener">Mở ảnh sản phẩm ↗</a>
          </div>

          <div v-if="selectedProductWarnings.length" class="review-warnings" role="alert">
            <strong>Cần kiểm tra trước khi duyệt</strong>
            <ul><li v-for="warning in selectedProductWarnings" :key="warning">{{ warning }}</li></ul>
          </div>

          <p v-if="canModerateSelectedProduct" class="workflow-guide">
            Kiểm tra thông tin chính, chọn <strong>Duyệt hiển thị</strong> rồi xác nhận để công khai sản phẩm.
            Việc thêm chứng cứ chỉ hỗ trợ đối chiếu và không tự động đổi trạng thái.
          </p>

          <details class="evidence-disclosure">
            <summary>
              <span>Chứng cứ nguồn</span>
              <small>Tùy chọn đối chiếu · không tự đổi trạng thái</small>
            </summary>
            <div class="evidence-content">
              <p v-if="evidenceLoading" class="evidence-message">Đang tải chứng cứ...</p>
              <p v-else-if="evidenceError" class="evidence-message error">{{ evidenceError }}</p>
              <ProductEvidenceManager
                v-else-if="evidence"
                :product-id="selectedProduct.id"
                :evidence="evidence"
                @updated="updateEvidenceSummary"
              />
            </div>
          </details>
        </template>

        <template v-else-if="selectedRequest">
          <section class="subject-box">
            <div><small>Sản phẩm</small><strong>{{ selectedRequest.product_name }}</strong></div>
            <div><small>Chủ thể</small><strong>{{ selectedRequest.subject_name }}</strong></div>
            <div><small>Loại yêu cầu</small><strong>{{ selectedRequest.request_type === 'update' ? 'Cập nhật' : 'Ngừng hiển thị' }}</strong></div>
          </section>
          <p v-if="selectedRequest.reason" class="reason-box"><strong>Lý do:</strong> {{ selectedRequest.reason }}</p>
          <section v-if="selectedRequest.reviewed_at" class="last-review-box">
            <div><small>Lần xử lý gần nhất</small><strong>{{ selectedRequest.status === 'approved' ? 'Đã duyệt' : selectedRequest.status === 'needs_revision' ? 'Cần bổ sung' : selectedRequest.status === 'cancelled' ? 'Đã hủy' : 'Bị từ chối' }}</strong></div>
            <div><small>Người xử lý</small><strong>{{ selectedRequest.reviewed_by_name || 'Quản trị viên' }}</strong></div>
            <div><small>Thời điểm</small><strong>{{ formatDateTime(selectedRequest.reviewed_at) }}</strong></div>
            <p v-if="selectedRequest.review_note"><strong>Ghi chú:</strong> {{ selectedRequest.review_note }}</p>
          </section>
          <section v-if="selectedRequest.request_type === 'update'" class="comparison-section">
            <div class="comparison-heading">
              <strong>So sánh nội dung thay đổi</strong>
              <span>Ô màu vàng là dữ liệu đã thay đổi</span>
            </div>
            <div class="comparison-table" role="table" aria-label="So sánh dữ liệu sản phẩm">
              <div class="comparison-row comparison-header" role="row">
                <span>Trường dữ liệu</span><span>Đang công khai</span><span>Chủ thể đề xuất</span>
              </div>
              <div
                v-for="field in comparisonFields"
                :key="field.key"
                class="comparison-row"
                :class="{ changed: fieldChanged(selectedRequest, field.key) }"
                role="row"
              >
                <strong>{{ field.label }}</strong>
                <span>{{ comparisonValue(selectedRequest.current_data, field.key) }}</span>
                <span>{{ comparisonValue(selectedRequest.proposed_data, field.key) }}</span>
              </div>
            </div>
          </section>
          <p v-else class="warning-box">Nếu chấp thuận, sản phẩm sẽ bị ẩn khỏi API công khai và chuyển vào trạng thái lưu trữ. Dữ liệu không bị xóa cứng.</p>
        </template>

        <section v-if="canModerateSelectedRequest || canModerateSelectedProduct" class="decision-box">
          <div class="decision-options" aria-label="Quyết định kiểm duyệt">
            <button type="button" :class="{ active: decision === 'approved' }" @click="decision = 'approved'">
              <AppIcon name="checkCircle" :size="15" /> {{ selectedProduct ? 'Duyệt hiển thị' : 'Chấp thuận yêu cầu' }}
            </button>
            <button type="button" :class="{ active: decision === 'needs_revision' }" @click="decision = 'needs_revision'">
              <AppIcon name="refresh" :size="15" /> Yêu cầu bổ sung
            </button>
          </div>
          <button class="exception-toggle" type="button" @click="showExceptionalAction = !showExceptionalAction">
            {{ showExceptionalAction ? 'Ẩn thao tác đặc biệt' : 'Hồ sơ không hợp lệ?' }}
          </button>
          <button v-if="showExceptionalAction" class="reject-option" :class="{ active: decision === 'rejected' }" type="button" @click="decision = 'rejected'">
            Từ chối hồ sơ
          </button>
          <label>Phản hồi cho chủ thể
            <textarea v-model="reviewNote" rows="3" :required="decision !== 'approved'" placeholder="Bắt buộc khi yêu cầu bổ sung hoặc từ chối" />
          </label>
        </section>
        <footer>
          <button type="button" @click="closeModal()">{{ canModerateSelectedRequest || canModerateSelectedProduct ? 'Hủy' : 'Đóng' }}</button>
          <button v-if="canModerateSelectedRequest || canModerateSelectedProduct" class="submit-button" type="submit" :disabled="submitting">
            {{ submitting ? 'Đang xử lý...' : 'Xác nhận quyết định' }}
          </button>
        </footer>
      </form>
    </div>
  </main>
</template>

<style scoped>
.admin-products-page { display: grid; gap: var(--ocop-space-5); }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--ocop-space-5); }
.page-heading span, .review-modal header span, .evidence-section .section-heading small { color: var(--ocop-primary-700); font-size: var(--ocop-font-size-caption); font-weight: 800; text-transform: uppercase; }
.page-heading h1 { margin: var(--ocop-space-1) 0; font-size: 31px; }
.page-heading p { margin: 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-small); }
.summary-badge, .level-chip { padding: 6px 10px; border-radius: var(--ocop-radius-pill); background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: var(--ocop-font-size-caption); font-weight: 800; white-space: nowrap; }
.tab-list { display: flex; gap: var(--ocop-space-2); }
.tab-list button, .filter-actions button { padding: 10px 14px; border: 1px solid var(--ocop-border); border-radius: 9px; background: var(--ocop-card); color: var(--ocop-neutral-600); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.tab-list button.active, .filter-actions .primary-button { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: var(--ocop-white); }
.tab-list span { margin-left: 5px; padding: 2px 6px; border-radius: var(--ocop-radius-pill); background: color-mix(in srgb, var(--ocop-white) 20%, transparent); }
.filter-panel { display: grid; padding: var(--ocop-space-4); gap: var(--ocop-space-3); border: 1px solid var(--ocop-border); border-radius: 14px; background: var(--ocop-card); }
.basic-filters { display: grid; grid-template-columns: minmax(240px, 2fr) minmax(180px, 1fr) auto; align-items: end; gap: 10px; }
.advanced-filters { display: grid; padding-top: var(--ocop-space-3); grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; border-top: 1px solid var(--ocop-border); }
.filter-panel label { display: grid; gap: 5px; color: var(--ocop-neutral-600); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.filter-panel input, .filter-panel select { width: 100%; min-height: 38px; padding: var(--ocop-space-2) 10px; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); background: var(--ocop-card); font-size: var(--ocop-font-size-caption); }
.filter-actions { display: flex; flex-wrap: wrap; gap: 7px; }
.queue-panel { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: 14px; background: var(--ocop-card); }
.queue-panel article { display: grid; padding: 15px var(--ocop-space-4); align-items: center; grid-template-columns: 72px minmax(0, 1fr) auto; gap: 14px; border-bottom: 1px solid var(--ocop-border-soft); }
.queue-panel article:last-child { border-bottom: 0; }
.queue-panel article > img { width: 72px; height: 64px; border-radius: 9px; object-fit: cover; }
.request-symbol { display: grid; width: 48px; height: 48px; place-items: center; border-radius: var(--ocop-radius-md); background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: 25px; }
.queue-panel small { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.queue-panel h2 { margin: var(--ocop-space-1) 0; font-size: var(--ocop-font-size-body); }
.queue-panel p { margin: 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.queue-panel button, .review-modal button { padding: var(--ocop-space-2) 11px; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); background: var(--ocop-card); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.pagination-bar { display: flex; padding: 13px var(--ocop-space-4); align-items: center; justify-content: space-between; gap: var(--ocop-space-3); border-top: 1px solid var(--ocop-border); background: var(--ocop-surface-subtle); }
.pagination-bar span { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.pagination-bar div { display: flex; gap: 7px; }
.pagination-bar button:disabled { cursor: not-allowed; opacity: .45; }
.status-row { display: flex; margin-top: var(--ocop-space-2); flex-wrap: wrap; gap: 6px; }
.status-chip, .issue-chip { padding: var(--ocop-space-1) 7px; border-radius: var(--ocop-radius-pill); background: var(--ocop-neutral-100); color: var(--ocop-text-muted); font-size: var(--ocop-font-size-caption); font-weight: 800; }
.status-chip[data-status="pending"], .issue-chip { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.status-chip[data-status="approved"] { background: var(--ocop-success-soft); color: var(--ocop-success); }
.status-chip[data-status="rejected"], .status-chip[data-status="suspended"] { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.status-chip[data-status="needs_revision"] { background: var(--ocop-warning-soft); color: var(--ocop-warning); }
.status-chip[data-status="cancelled"], .status-chip[data-status="archived"] { background: var(--ocop-neutral-100); color: var(--ocop-text-muted); }
.status-chip.verification { background: var(--ocop-info-soft); color: var(--ocop-info); }
.empty-state { padding: 50px var(--ocop-space-5); color: var(--ocop-slate); text-align: center; }
.modal-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; padding: var(--ocop-space-5); place-items: center; overflow-y: auto; background: color-mix(in srgb, var(--ocop-neutral-900) 58%, transparent); }
.review-modal { width: min(100%, 800px); max-height: calc(100vh - 40px); padding: var(--ocop-space-6); overflow-y: auto; border-radius: var(--ocop-radius-lg); background: var(--ocop-card); box-shadow: var(--ocop-shadow-overlay); }
.review-modal > header, .section-heading { display: flex; align-items: start; justify-content: space-between; gap: var(--ocop-space-3); }
.review-modal header h2 { margin: var(--ocop-space-1) 0 0; font-size: 22px; }
.review-modal header > button { border: 0; font-size: 20px; }
.subject-box, .review-grid, .evidence-overview { display: grid; margin-top: 18px; padding: 15px; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 13px; border-radius: 11px; background: var(--ocop-surface-subtle); }
.subject-box div, .review-grid div, .evidence-overview div { display: grid; gap: 3px; }
.subject-box small, .review-grid small, .evidence-overview small { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); font-weight: 700; text-transform: uppercase; }
.subject-box strong, .review-grid strong, .evidence-overview strong { font-size: var(--ocop-font-size-caption); overflow-wrap: anywhere; }
.review-grid .wide { grid-column: 1 / -1; }
.last-review-box { display: grid; margin-top: 13px; padding: 13px 15px; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: var(--ocop-space-3); border: 1px solid var(--ocop-mint-border); border-radius: 10px; background: var(--ocop-surface-muted); }
.last-review-box div { display: grid; gap: 3px; }
.last-review-box small { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); font-weight: 700; text-transform: uppercase; }
.last-review-box strong { font-size: var(--ocop-font-size-caption); }
.last-review-box p { grid-column: 1 / -1; margin: 0; color: var(--ocop-text-muted); font-size: var(--ocop-font-size-caption); }
.document-links { display: flex; margin-top: var(--ocop-space-3); gap: var(--ocop-space-2); }
.document-links a, .document-links button, .evidence-card a { color: var(--ocop-info-strong); font-size: var(--ocop-font-size-caption); font-weight: 700; text-decoration: none; }
.document-links a, .document-links button { padding: var(--ocop-space-2) 10px; border: 0; border-radius: 7px; background: var(--ocop-info-soft); }
.review-warnings { margin-top: 13px; padding: 11px 13px; border: 1px solid var(--ocop-notice-border); border-radius: 9px; background: var(--ocop-notice-soft); color: var(--ocop-notice); font-size: var(--ocop-font-size-caption); }
.review-warnings ul { margin: 6px 0 0; padding-left: 18px; }
.workflow-guide { margin: 14px 0 0; padding: var(--ocop-space-3) 14px; border: 1px solid var(--ocop-mint-border); border-radius: 9px; background: var(--ocop-mint-soft); color: var(--ocop-primary-900); font-size: var(--ocop-font-size-caption); line-height: 1.55; }
.evidence-disclosure { margin-top: 14px; border: 1px solid var(--ocop-border); border-radius: 10px; background: var(--ocop-card); }
.evidence-disclosure summary { display: flex; padding: var(--ocop-space-3) 14px; align-items: center; justify-content: space-between; gap: var(--ocop-space-3); cursor: pointer; color: var(--ocop-neutral-700); font-size: var(--ocop-font-size-caption); font-weight: 800; }
.evidence-disclosure summary small { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); font-weight: 600; }
.evidence-content { padding: 0 14px 14px; }
.evidence-content :deep(.evidence-section) { margin-top: 0; border-top: 0; padding-top: 6px; }
.evidence-section { display: grid; margin-top: 22px; gap: 11px; border-top: 1px solid var(--ocop-border); padding-top: 18px; }
.evidence-section h3 { margin: 3px 0 0; font-size: 17px; }
.evidence-overview { margin-top: 0; grid-template-columns: 1fr 2fr; }
.issue-list { display: flex; flex-wrap: wrap; gap: 6px; }
.issue-list span { padding: 6px var(--ocop-space-2); border-radius: 7px; background: var(--ocop-notice-soft); color: var(--ocop-notice); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.evidence-card { padding: var(--ocop-space-3); border: 1px solid var(--ocop-border); border-radius: 10px; }
.evidence-card > div { display: flex; align-items: center; gap: var(--ocop-space-2); }
.evidence-card h4 { margin: 9px 0 var(--ocop-space-1); font-size: var(--ocop-font-size-small); }
.evidence-card p { margin: 3px 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.evidence-card .source-note { color: var(--ocop-notice-deep); }
.evidence-message { padding: 14px; border-radius: var(--ocop-radius-sm); background: var(--ocop-surface-subtle); color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); text-align: center; }
.evidence-message.error { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.reason-box, .warning-box { padding: 11px; border-radius: var(--ocop-radius-sm); background: var(--ocop-warning-soft); color: var(--ocop-warning); font-size: var(--ocop-font-size-caption); }
.warning-box { background: var(--ocop-danger-soft); color: var(--ocop-danger); }
.comparison-section { display: grid; margin-top: 18px; gap: 10px; }
.comparison-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--ocop-space-3); }
.comparison-heading strong { font-size: var(--ocop-font-size-small); }
.comparison-heading span { color: var(--ocop-slate); font-size: var(--ocop-font-size-caption); }
.comparison-table { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: 10px; }
.comparison-row { display: grid; padding: 9px 11px; grid-template-columns: 140px repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-3); border-bottom: 1px solid var(--ocop-border); font-size: var(--ocop-font-size-caption); }
.comparison-row:last-child { border-bottom: 0; }
.comparison-row > span { overflow-wrap: anywhere; }
.comparison-header { background: var(--ocop-neutral-100); color: var(--ocop-neutral-600); font-weight: 800; }
.comparison-row.changed { background: var(--ocop-notice-soft); }
.comparison-row.changed > strong { color: var(--ocop-notice); }
.decision-box { display: grid; margin-top: 18px; gap: var(--ocop-space-3); }
.decision-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--ocop-space-2); }
.decision-options button { padding: 11px; }
.decision-options button.active { border-color: var(--ocop-primary-700); background: var(--ocop-mint-soft); color: var(--ocop-primary-700); }
.exception-toggle { justify-self: start; border: 0 !important; color: var(--ocop-slate); text-decoration: underline; }
.reject-option { justify-self: start; border-color: var(--ocop-danger-border) !important; color: var(--ocop-danger-strong); }
.reject-option.active { background: var(--ocop-danger-soft); }
.decision-box label { display: grid; gap: 5px; color: var(--ocop-neutral-600); font-size: var(--ocop-font-size-caption); font-weight: 700; }
.decision-box select, .decision-box textarea { padding: 9px; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-sm); }
.decision-box textarea { resize: vertical; }
.review-modal footer { display: flex; margin-top: var(--ocop-space-4); justify-content: flex-end; gap: var(--ocop-space-2); }
.review-modal .submit-button { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: var(--ocop-white); }
@media (max-width: 1180px) {
  .basic-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .filter-actions { grid-column: 1 / -1; }
}
@media (max-width: 640px) {
  .page-heading { align-items: start; flex-direction: column; }
  .tab-list, .basic-filters, .advanced-filters { grid-template-columns: 1fr; }
  .tab-list { display: grid; }
  .filter-actions { grid-column: auto; }
  .filter-actions button { flex: 1; }
  .pagination-bar { align-items: stretch; flex-direction: column; }
  .pagination-bar div, .pagination-bar button { flex: 1; }
  .queue-panel article { grid-template-columns: 52px minmax(0, 1fr); }
  .queue-panel article > img { width: 52px; height: 52px; }
  .queue-panel article > button { grid-column: 1 / -1; }
  .subject-box, .review-grid, .evidence-overview, .last-review-box { grid-template-columns: 1fr; }
  .last-review-box p { grid-column: auto; }
  .review-grid .wide { grid-column: auto; }
  .document-links { flex-direction: column; }
  .evidence-disclosure summary { align-items: start; flex-direction: column; }
  .comparison-heading { align-items: start; flex-direction: column; }
  .comparison-header { display: none; }
  .comparison-row { grid-template-columns: 1fr; gap: var(--ocop-space-1); }
  .decision-options { grid-template-columns: 1fr; }
}
</style>
