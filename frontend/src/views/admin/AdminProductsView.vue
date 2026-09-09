<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { getApiErrorMessage } from '@/services/api-error'
import {
  listAdminProducts,
  listProductChangeRequests,
  moderateProduct,
  moderateProductChangeRequest,
} from '@/services/product-management'
import type {
  ManagedProduct,
  ProductChangeRequest,
  ProductModerationDecision,
} from '@/types/product-management'

const products = ref<ManagedProduct[]>([])
const requests = ref<ProductChangeRequest[]>([])
const loading = ref(true)
const errorMessage = ref('')
const successMessage = ref('')
const activeTab = ref<'new' | 'changes'>('new')
const selectedProduct = ref<ManagedProduct | null>(null)
const selectedRequest = ref<ProductChangeRequest | null>(null)
const decision = ref<ProductModerationDecision>('approved')
const reviewNote = ref('')
const submitting = ref(false)

const pendingProducts = computed(() => products.value.filter((item) => item.status === 'pending'))
const pendingRequests = computed(() => requests.value.filter((item) => item.status === 'pending'))
const modalTitle = computed(() => {
  if (selectedProduct.value) return 'Duyệt hiển thị sản phẩm mới'
  if (selectedRequest.value?.request_type === 'update') return 'Duyệt yêu cầu cập nhật'
  return 'Duyệt yêu cầu ngừng hiển thị'
})

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const [productData, requestData] = await Promise.all([
      listAdminProducts(),
      listProductChangeRequests('admin'),
    ])
    products.value = productData.items
    requests.value = requestData.items
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải hàng đợi kiểm duyệt sản phẩm.')
  } finally {
    loading.value = false
  }
}

function openProduct(product: ManagedProduct): void {
  selectedRequest.value = null
  selectedProduct.value = product
  decision.value = 'approved'
  reviewNote.value = ''
}

function openRequest(request: ProductChangeRequest): void {
  selectedProduct.value = null
  selectedRequest.value = request
  decision.value = 'approved'
  reviewNote.value = ''
}

function closeModal(): void {
  if (submitting.value) return
  selectedProduct.value = null
  selectedRequest.value = null
}

async function submitDecision(): Promise<void> {
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
    selectedProduct.value = null
    selectedRequest.value = null
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể xử lý yêu cầu kiểm duyệt.')
  } finally {
    submitting.value = false
  }
}

function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat('vi-VN').format(new Date(value)) : '—'
}

function fieldValue(request: ProductChangeRequest, field: keyof NonNullable<ProductChangeRequest['proposed_data']>): string {
  const value = request.proposed_data?.[field]
  return value === null || value === undefined ? '—' : String(value)
}

onMounted(loadData)
</script>

<template>
  <main class="admin-products-page">
    <header class="page-heading">
      <div>
        <span>Kiểm duyệt dữ liệu OCOP</span>
        <h1>Duyệt sản phẩm</h1>
        <p>Đối chiếu giấy chứng nhận và duyệt hiển thị; quản trị viên không cấp hoặc tự thay đổi hạng sao.</p>
      </div>
      <div class="summary-badge">{{ pendingProducts.length + pendingRequests.length }} yêu cầu chờ xử lý</div>
    </header>

    <div v-if="errorMessage" class="alert alert-danger" role="alert">{{ errorMessage }}</div>
    <div v-if="successMessage" class="alert alert-success" role="status">{{ successMessage }}</div>

    <nav class="tab-list" aria-label="Loại yêu cầu">
      <button :class="{ active: activeTab === 'new' }" type="button" @click="activeTab = 'new'">
        Sản phẩm mới <span>{{ pendingProducts.length }}</span>
      </button>
      <button :class="{ active: activeTab === 'changes' }" type="button" @click="activeTab = 'changes'">
        Sửa / ngừng hiển thị <span>{{ pendingRequests.length }}</span>
      </button>
    </nav>

    <section class="queue-panel">
      <p v-if="loading" class="empty-state">Đang tải hàng đợi...</p>
      <template v-else-if="activeTab === 'new'">
        <p v-if="!pendingProducts.length" class="empty-state">Không có sản phẩm mới chờ duyệt.</p>
        <article v-for="product in pendingProducts" v-else :key="product.id">
          <img :src="product.images.find((image) => image.is_primary)?.image_url" alt="" />
          <div>
            <small>Hồ sơ #{{ product.id }} · gửi {{ formatDate(product.submitted_at) }}</small>
            <h2>{{ product.name }}</h2>
            <p>{{ product.subject.name }} · {{ product.star }} sao theo chứng nhận · {{ product.cert_code }}</p>
          </div>
          <button type="button" @click="openProduct(product)">Kiểm tra hồ sơ</button>
        </article>
      </template>
      <template v-else>
        <p v-if="!pendingRequests.length" class="empty-state">Không có yêu cầu thay đổi chờ duyệt.</p>
        <article v-for="request in pendingRequests" v-else :key="request.id">
          <span class="request-symbol">{{ request.request_type === 'update' ? '↻' : '×' }}</span>
          <div>
            <small>Yêu cầu #{{ request.id }} · gửi {{ formatDate(request.submitted_at) }}</small>
            <h2>{{ request.product_name }}</h2>
            <p>
              {{ request.subject_name }} ·
              {{ request.request_type === 'update' ? 'Đề nghị cập nhật thông tin' : 'Đề nghị ngừng hiển thị' }}
            </p>
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
            <div><small>Mã chứng nhận</small><strong>{{ selectedProduct.cert_code }}</strong></div>
            <div><small>Ngày cấp</small><strong>{{ formatDate(selectedProduct.cert_issued_at) }}</strong></div>
            <div><small>Ngày hết hạn</small><strong>{{ formatDate(selectedProduct.cert_expires_at) }}</strong></div>
            <div class="wide"><small>Cơ quan công nhận</small><strong>{{ selectedProduct.issuing_authority }}</strong></div>
          </section>
          <div class="document-links">
            <a :href="selectedProduct.certificate_url" target="_blank" rel="noopener">Mở tài liệu chứng nhận ↗</a>
            <a :href="selectedProduct.images[0]?.image_url" target="_blank" rel="noopener">Mở ảnh sản phẩm ↗</a>
          </div>
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

        <section class="decision-box">
          <label>Quyết định
            <select v-model="decision">
              <option value="approved">{{ selectedProduct ? 'Duyệt hiển thị' : 'Chấp thuận yêu cầu' }}</option>
              <option value="needs_revision">Yêu cầu bổ sung</option>
              <option value="rejected">Từ chối</option>
            </select>
          </label>
          <label>Phản hồi cho chủ thể
            <textarea
              v-model="reviewNote"
              rows="3"
              :required="decision !== 'approved'"
              placeholder="Bắt buộc khi yêu cầu bổ sung hoặc từ chối"
            />
          </label>
        </section>
        <footer>
          <button type="button" @click="closeModal">Hủy</button>
          <button class="submit-button" type="submit" :disabled="submitting">
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
.page-heading span, .review-modal header span { color: var(--ocop-primary-700); font-size: 10px; font-weight: 800; text-transform: uppercase; }
.page-heading h1 { margin: 4px 0; font-size: 31px; }
.page-heading p { margin: 0; color: var(--ocop-slate); font-size: 13px; }
.summary-badge { padding: 8px 11px; border-radius: 999px; background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: 11px; font-weight: 800; }
.tab-list { display: flex; gap: 8px; }
.tab-list button { padding: 10px 14px; border: 1px solid var(--ocop-border); border-radius: 9px; background: #fff; color: #56677c; font-size: 12px; font-weight: 700; }
.tab-list button.active { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: #fff; }
.tab-list span { margin-left: 5px; padding: 2px 6px; border-radius: 999px; background: rgb(255 255 255 / 20%); }
.queue-panel { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: 14px; background: #fff; }
.queue-panel article { display: grid; padding: 15px 16px; align-items: center; grid-template-columns: 72px minmax(0, 1fr) auto; gap: 14px; border-bottom: 1px solid #edf1f4; }
.queue-panel article:last-child { border-bottom: 0; }
.queue-panel article > img { width: 72px; height: 64px; border-radius: 9px; object-fit: cover; }
.request-symbol { display: grid; width: 48px; height: 48px; place-items: center; border-radius: 12px; background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: 25px; }
.queue-panel small { color: var(--ocop-slate); font-size: 10px; }
.queue-panel h2 { margin: 4px 0; font-size: 15px; }
.queue-panel p { margin: 0; color: var(--ocop-slate); font-size: 11px; }
.queue-panel button, .review-modal button { padding: 8px 11px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; font-size: 11px; font-weight: 700; }
.empty-state { padding: 50px 20px; color: var(--ocop-slate); text-align: center; }
.modal-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; padding: 20px; place-items: center; overflow-y: auto; background: rgb(15 23 43 / 58%); }
.review-modal { width: min(100%, 760px); max-height: calc(100vh - 40px); padding: 24px; overflow-y: auto; border-radius: 16px; background: #fff; box-shadow: 0 30px 70px rgb(15 23 43 / 28%); }
.review-modal > header { display: flex; align-items: start; justify-content: space-between; }
.review-modal header h2 { margin: 4px 0 0; font-size: 22px; }
.review-modal header > button { border: 0; font-size: 20px; }
.subject-box, .review-grid { display: grid; margin-top: 18px; padding: 15px; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 13px; border-radius: 11px; background: #f7f9fa; }
.subject-box div, .review-grid div { display: grid; gap: 3px; }
.subject-box small, .review-grid small { color: var(--ocop-slate); font-size: 9px; font-weight: 700; text-transform: uppercase; }
.subject-box strong, .review-grid strong { font-size: 12px; overflow-wrap: anywhere; }
.review-grid .wide { grid-column: 1 / -1; }
.document-links { display: flex; margin-top: 12px; gap: 8px; }
.document-links a { padding: 8px 10px; border-radius: 7px; background: #eff6ff; color: #1d4f91; font-size: 11px; font-weight: 700; text-decoration: none; }
.reason-box, .warning-box { padding: 11px; border-radius: 8px; background: #fff7ed; color: #914515; font-size: 12px; }
.warning-box { background: #fef2f2; color: #a72727; }
.decision-box { display: grid; margin-top: 18px; gap: 12px; }
.decision-box label { display: grid; gap: 5px; color: #526277; font-size: 11px; font-weight: 700; }
.decision-box select, .decision-box textarea { padding: 9px; border: 1px solid var(--ocop-border); border-radius: 8px; }
.decision-box textarea { resize: vertical; }
.review-modal footer { display: flex; margin-top: 16px; justify-content: flex-end; gap: 8px; }
.review-modal .submit-button { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: #fff; }
@media (max-width: 640px) {
  .page-heading { align-items: start; flex-direction: column; }
  .tab-list { display: grid; grid-template-columns: 1fr; }
  .queue-panel article { grid-template-columns: 52px minmax(0, 1fr); }
  .queue-panel article > img { width: 52px; height: 52px; }
  .queue-panel article > button { grid-column: 1 / -1; }
  .subject-box, .review-grid { grid-template-columns: 1fr; }
  .review-grid .wide { grid-column: auto; }
  .document-links { flex-direction: column; }
}
</style>
