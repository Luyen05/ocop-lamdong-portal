<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import ProductEvidenceManager from '@/components/admin/ProductEvidenceManager.vue'
import { getApiErrorMessage } from '@/services/api-error'
import {
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
  ProductVerificationStatus,
  ProductWorkflowStatus,
  VerificationLevel,
} from '@/types/product-management'

type EvidenceIssueFilter = '' | 'missing_decision' | 'missing_issued_at'

const products = ref<ManagedProduct[]>([])
const productTotal = ref(0)
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

const search = ref('')
const workflowStatus = ref<ProductWorkflowStatus | ''>('')
const verificationLevel = ref<VerificationLevel | ''>('')
const verificationStatus = ref<ProductVerificationStatus | ''>('')
const evidenceIssue = ref<EvidenceIssueFilter>('')

const pendingProducts = computed(() => products.value.filter((item) => item.status === 'pending'))
const pendingRequests = computed(() => requests.value.filter((item) => item.status === 'pending'))
const canModerateSelectedProduct = computed(() => selectedProduct.value?.status === 'pending')
const modalTitle = computed(() => {
  if (selectedProduct.value) {
    return canModerateSelectedProduct.value ? 'Kiểm tra và duyệt sản phẩm' : 'Hồ sơ và chứng cứ sản phẩm'
  }
  if (selectedRequest.value?.request_type === 'update') return 'Duyệt yêu cầu cập nhật'
  return 'Duyệt yêu cầu ngừng hiển thị'
})

function buildProductFilters(): AdminProductFilters {
  const filters: AdminProductFilters = {}
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
  await loadData()
}

async function resetFilters(): Promise<void> {
  search.value = ''
  workflowStatus.value = ''
  verificationLevel.value = ''
  verificationStatus.value = ''
  evidenceIssue.value = ''
  await loadData()
}

async function openProduct(product: ManagedProduct): Promise<void> {
  selectedRequest.value = null
  selectedProduct.value = product
  evidence.value = null
  evidenceError.value = ''
  decision.value = 'approved'
  reviewNote.value = ''
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

function closeModal(): void {
  if (submitting.value) return
  selectedProduct.value = null
  selectedRequest.value = null
  evidence.value = null
  evidenceError.value = ''
}

async function submitDecision(): Promise<void> {
  if (selectedProduct.value && !canModerateSelectedProduct.value) return
  if ((decision.value === 'needs_revision' || decision.value === 'rejected') && !reviewNote.value.trim()) {
    errorMessage.value = 'Cần nhập nội dung phản hồi khi yêu cầu bổ sung hoặc từ chối.'
    return
  }
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
    closeModal()
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể xử lý yêu cầu kiểm duyệt.')
  } finally {
    submitting.value = false
  }
}

function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat('vi-VN').format(new Date(value)) : 'Chưa có'
}

function fieldValue(request: ProductChangeRequest, field: keyof NonNullable<ProductChangeRequest['proposed_data']>): string {
  const value = request.proposed_data?.[field]
  return value === null || value === undefined ? '—' : String(value)
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
        Sửa / ngừng hiển thị <span>{{ pendingRequests.length }}</span>
      </button>
    </nav>

    <form v-if="activeTab === 'products'" class="filter-panel" @submit.prevent="applyFilters">
      <label class="search-field">Tìm sản phẩm hoặc chủ thể
        <input v-model="search" type="search" placeholder="Tên, mã chứng nhận, chủ thể..." />
      </label>
      <label>Trạng thái nghiệp vụ
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
      <div class="filter-actions">
        <button type="button" @click="resetFilters">Đặt lại</button>
        <button class="primary-button" type="submit">Áp dụng</button>
      </div>
    </form>

    <section class="queue-panel">
      <p v-if="loading" class="empty-state">Đang tải dữ liệu...</p>
      <template v-else-if="activeTab === 'products'">
        <p v-if="!products.length" class="empty-state">Không tìm thấy sản phẩm phù hợp bộ lọc.</p>
        <article v-for="product in products" v-else :key="product.id">
          <img v-if="product.images.find((image) => image.is_primary)?.image_url" :src="product.images.find((image) => image.is_primary)?.image_url" alt="" />
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
      </template>
      <template v-else>
        <p v-if="!pendingRequests.length" class="empty-state">Không có yêu cầu thay đổi chờ duyệt.</p>
        <article v-for="request in pendingRequests" v-else :key="request.id">
          <span class="request-symbol">{{ request.request_type === 'update' ? '↻' : '×' }}</span>
          <div>
            <small>Yêu cầu #{{ request.id }} · gửi {{ formatDate(request.submitted_at) }}</small>
            <h2>{{ request.product_name }}</h2>
            <p>{{ request.subject_name }} · {{ request.request_type === 'update' ? 'Đề nghị cập nhật thông tin' : 'Đề nghị ngừng hiển thị' }}</p>
          </div>
          <button type="button" @click="openRequest(request)">Kiểm tra yêu cầu</button>
        </article>
      </template>
    </section>

    <div v-if="selectedProduct || selectedRequest" class="modal-backdrop" @click.self="closeModal">
      <form class="review-modal" @submit.prevent="submitDecision">
        <header>
          <div>
            <span>Kiểm duyệt sản phẩm</span>
            <h2>{{ modalTitle }}</h2>
          </div>
          <button type="button" aria-label="Đóng" @click="closeModal">×</button>
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
          <div class="document-links">
            <a v-if="selectedProduct.certificate_url" :href="selectedProduct.certificate_url" target="_blank" rel="noopener">Mở tài liệu chứng nhận ↗</a>
            <a v-if="selectedProduct.images[0]?.image_url" :href="selectedProduct.images[0].image_url" target="_blank" rel="noopener">Mở ảnh sản phẩm ↗</a>
          </div>

          <p v-if="evidenceLoading" class="evidence-message">Đang tải chứng cứ...</p>
          <p v-else-if="evidenceError" class="evidence-message error">{{ evidenceError }}</p>
          <ProductEvidenceManager
            v-else-if="evidence"
            :product-id="selectedProduct.id"
            :evidence="evidence"
            @updated="evidence = $event"
          />
        </template>

        <template v-else-if="selectedRequest">
          <section class="subject-box">
            <div><small>Sản phẩm</small><strong>{{ selectedRequest.product_name }}</strong></div>
            <div><small>Chủ thể</small><strong>{{ selectedRequest.subject_name }}</strong></div>
            <div><small>Loại yêu cầu</small><strong>{{ selectedRequest.request_type === 'update' ? 'Cập nhật' : 'Ngừng hiển thị' }}</strong></div>
          </section>
          <p v-if="selectedRequest.reason" class="reason-box"><strong>Lý do:</strong> {{ selectedRequest.reason }}</p>
          <section v-if="selectedRequest.request_type === 'update'" class="review-grid">
            <div><small>Tên đề xuất</small><strong>{{ fieldValue(selectedRequest, 'name') }}</strong></div>
            <div><small>Hạng sao theo chứng nhận</small><strong>{{ fieldValue(selectedRequest, 'star') }} sao</strong></div>
            <div><small>Mã chứng nhận</small><strong>{{ fieldValue(selectedRequest, 'cert_code') }}</strong></div>
            <div><small>Ngày hết hạn</small><strong>{{ formatDate(fieldValue(selectedRequest, 'cert_expires_at')) }}</strong></div>
            <div class="wide"><small>Cơ quan công nhận</small><strong>{{ fieldValue(selectedRequest, 'issuing_authority') }}</strong></div>
          </section>
          <p v-else class="warning-box">Nếu chấp thuận, sản phẩm sẽ bị ẩn khỏi API công khai và chuyển vào trạng thái lưu trữ. Dữ liệu không bị xóa cứng.</p>
        </template>

        <section v-if="selectedRequest || canModerateSelectedProduct" class="decision-box">
          <label>Quyết định
            <select v-model="decision">
              <option value="approved">{{ selectedProduct ? 'Duyệt hiển thị' : 'Chấp thuận yêu cầu' }}</option>
              <option value="needs_revision">Yêu cầu bổ sung</option>
              <option value="rejected">Từ chối</option>
            </select>
          </label>
          <label>Phản hồi cho chủ thể
            <textarea v-model="reviewNote" rows="3" :required="decision !== 'approved'" placeholder="Bắt buộc khi yêu cầu bổ sung hoặc từ chối" />
          </label>
        </section>
        <footer>
          <button type="button" @click="closeModal">{{ selectedRequest || canModerateSelectedProduct ? 'Hủy' : 'Đóng' }}</button>
          <button v-if="selectedRequest || canModerateSelectedProduct" class="submit-button" type="submit" :disabled="submitting">
            {{ submitting ? 'Đang xử lý...' : 'Xác nhận quyết định' }}
          </button>
        </footer>
      </form>
    </div>
  </main>
</template>

<style scoped>
.admin-products-page { display: grid; gap: 20px; }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }
.page-heading span, .review-modal header span, .evidence-section .section-heading small { color: var(--ocop-primary-700); font-size: 10px; font-weight: 800; text-transform: uppercase; }
.page-heading h1 { margin: 4px 0; font-size: 31px; }
.page-heading p { margin: 0; color: var(--ocop-slate); font-size: 13px; }
.summary-badge, .level-chip { padding: 6px 10px; border-radius: 999px; background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: 10px; font-weight: 800; white-space: nowrap; }
.tab-list { display: flex; gap: 8px; }
.tab-list button, .filter-actions button { padding: 10px 14px; border: 1px solid var(--ocop-border); border-radius: 9px; background: #fff; color: #56677c; font-size: 12px; font-weight: 700; }
.tab-list button.active, .filter-actions .primary-button { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: #fff; }
.tab-list span { margin-left: 5px; padding: 2px 6px; border-radius: 999px; background: rgb(255 255 255 / 20%); }
.filter-panel { display: grid; padding: 16px; grid-template-columns: minmax(220px, 1.5fr) repeat(4, minmax(145px, 1fr)) auto; align-items: end; gap: 10px; border: 1px solid var(--ocop-border); border-radius: 14px; background: #fff; }
.filter-panel label { display: grid; gap: 5px; color: #526277; font-size: 10px; font-weight: 700; }
.filter-panel input, .filter-panel select { width: 100%; min-height: 38px; padding: 8px 10px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; font-size: 11px; }
.filter-actions { display: flex; gap: 7px; }
.queue-panel { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: 14px; background: #fff; }
.queue-panel article { display: grid; padding: 15px 16px; align-items: center; grid-template-columns: 72px minmax(0, 1fr) auto; gap: 14px; border-bottom: 1px solid #edf1f4; }
.queue-panel article:last-child { border-bottom: 0; }
.queue-panel article > img { width: 72px; height: 64px; border-radius: 9px; object-fit: cover; }
.request-symbol { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 12px; background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: 25px; }
.queue-panel small { color: var(--ocop-slate); font-size: 10px; }
.queue-panel h2 { margin: 4px 0; font-size: 15px; }
.queue-panel p { margin: 0; color: var(--ocop-slate); font-size: 11px; }
.queue-panel button, .review-modal button { padding: 8px 11px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; font-size: 11px; font-weight: 700; }
.status-row { display: flex; margin-top: 8px; flex-wrap: wrap; gap: 6px; }
.status-chip, .issue-chip { padding: 4px 7px; border-radius: 999px; background: #f1f5f9; color: #475569; font-size: 9px; font-weight: 800; }
.status-chip[data-status="pending"], .issue-chip { background: #fff7ed; color: #9a4d12; }
.status-chip[data-status="approved"] { background: #ecfdf5; color: #08745a; }
.status-chip[data-status="rejected"], .status-chip[data-status="suspended"] { background: #fef2f2; color: #b42323; }
.status-chip.verification { background: #eff6ff; color: #1d4f91; }
.empty-state { padding: 50px 20px; color: var(--ocop-slate); text-align: center; }
.modal-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; padding: 20px; place-items: center; overflow-y: auto; background: rgb(15 23 43 / 58%); }
.review-modal { width: min(100%, 800px); max-height: calc(100vh - 40px); padding: 24px; overflow-y: auto; border-radius: 16px; background: #fff; box-shadow: 0 30px 70px rgb(15 23 43 / 28%); }
.review-modal > header, .section-heading { display: flex; align-items: start; justify-content: space-between; gap: 12px; }
.review-modal header h2 { margin: 4px 0 0; font-size: 22px; }
.review-modal header > button { border: 0; font-size: 20px; }
.subject-box, .review-grid, .evidence-overview { display: grid; margin-top: 18px; padding: 15px; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 13px; border-radius: 11px; background: #f7f9fa; }
.subject-box div, .review-grid div, .evidence-overview div { display: grid; gap: 3px; }
.subject-box small, .review-grid small, .evidence-overview small { color: var(--ocop-slate); font-size: 9px; font-weight: 700; text-transform: uppercase; }
.subject-box strong, .review-grid strong, .evidence-overview strong { font-size: 12px; overflow-wrap: anywhere; }
.review-grid .wide { grid-column: 1 / -1; }
.document-links { display: flex; margin-top: 12px; gap: 8px; }
.document-links a, .evidence-card a { color: #1d4f91; font-size: 11px; font-weight: 700; text-decoration: none; }
.document-links a { padding: 8px 10px; border-radius: 7px; background: #eff6ff; }
.evidence-section { display: grid; margin-top: 22px; gap: 11px; border-top: 1px solid var(--ocop-border); padding-top: 18px; }
.evidence-section h3 { margin: 3px 0 0; font-size: 17px; }
.evidence-overview { margin-top: 0; grid-template-columns: 1fr 2fr; }
.issue-list { display: flex; flex-wrap: wrap; gap: 6px; }
.issue-list span { padding: 6px 8px; border-radius: 7px; background: #fff7ed; color: #9a4d12; font-size: 10px; font-weight: 700; }
.evidence-card { padding: 12px; border: 1px solid var(--ocop-border); border-radius: 10px; }
.evidence-card > div { display: flex; align-items: center; gap: 8px; }
.evidence-card h4 { margin: 9px 0 4px; font-size: 13px; }
.evidence-card p { margin: 3px 0; color: var(--ocop-slate); font-size: 10px; }
.evidence-card .source-note { color: #7c4a11; }
.evidence-message { padding: 14px; border-radius: 8px; background: #f8fafc; color: var(--ocop-slate); font-size: 11px; text-align: center; }
.evidence-message.error { background: #fef2f2; color: #b42323; }
.reason-box, .warning-box { padding: 11px; border-radius: 8px; background: #fff7ed; color: #914515; font-size: 12px; }
.warning-box { background: #fef2f2; color: #a72727; }
.decision-box { display: grid; margin-top: 18px; gap: 12px; }
.decision-box label { display: grid; gap: 5px; color: #526277; font-size: 11px; font-weight: 700; }
.decision-box select, .decision-box textarea { padding: 9px; border: 1px solid var(--ocop-border); border-radius: 8px; }
.decision-box textarea { resize: vertical; }
.review-modal footer { display: flex; margin-top: 16px; justify-content: flex-end; gap: 8px; }
.review-modal .submit-button { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: #fff; }
@media (max-width: 1180px) {
  .filter-panel { grid-template-columns: repeat(3, minmax(0, 1fr)); }
  .search-field { grid-column: span 2; }
}
@media (max-width: 640px) {
  .page-heading { align-items: start; flex-direction: column; }
  .tab-list, .filter-panel { grid-template-columns: 1fr; }
  .tab-list { display: grid; }
  .search-field { grid-column: auto; }
  .filter-actions button { flex: 1; }
  .queue-panel article { grid-template-columns: 52px minmax(0, 1fr); }
  .queue-panel article > img { width: 52px; height: 52px; }
  .queue-panel article > button { grid-column: 1 / -1; }
  .subject-box, .review-grid, .evidence-overview { grid-template-columns: 1fr; }
  .review-grid .wide { grid-column: auto; }
  .document-links { flex-direction: column; }
}
</style>
