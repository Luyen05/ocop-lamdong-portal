<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'

import { getApiErrorMessage } from '@/services/api-error'
import {
  cancelProductChangeRequest,
  deleteProductDraft,
  listMyProducts,
  listProductChangeRequests,
  requestProductDeletion,
  resubmitProductChangeRequest,
  submitProduct,
} from '@/services/product-management'
import type {
  ManagedProduct,
  ProductChangeRequest,
  ProductWorkflowStatus,
} from '@/types/product-management'

const products = ref<ManagedProduct[]>([])
const changeRequests = ref<ProductChangeRequest[]>([])
const filter = ref<ProductWorkflowStatus | ''>('')
const loading = ref(true)
const actionId = ref<number | null>(null)
const errorMessage = ref('')
const successMessage = ref('')
const deletingProduct = ref<ManagedProduct | null>(null)
const revisingDeletionRequest = ref<ProductChangeRequest | null>(null)
const deletionReason = ref('')

const statusLabels: Record<ProductWorkflowStatus, string> = {
  draft: 'Bản nháp',
  pending: 'Chờ duyệt',
  needs_revision: 'Cần bổ sung',
  approved: 'Đang công khai',
  rejected: 'Bị từ chối',
  suspended: 'Tạm ngừng',
  archived: 'Đã lưu trữ',
}

const filteredProducts = computed(() =>
  filter.value ? products.value.filter((item) => item.status === filter.value) : products.value,
)

async function loadData(): Promise<void> {
  loading.value = true
  errorMessage.value = ''
  try {
    const [productData, requestData] = await Promise.all([
      listMyProducts(),
      listProductChangeRequests('subject'),
    ])
    products.value = productData.items
    changeRequests.value = requestData.items
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách sản phẩm.')
  } finally {
    loading.value = false
  }
}

function activeRequest(productId: number): ProductChangeRequest | undefined {
  return changeRequests.value.find(
    (item) => item.product_id === productId && ['pending', 'needs_revision'].includes(item.status),
  )
}

async function submit(product: ManagedProduct): Promise<void> {
  actionId.value = product.id
  errorMessage.value = ''
  try {
    await submitProduct(product.id)
    successMessage.value = 'Sản phẩm đã được gửi để quản trị viên duyệt hiển thị.'
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể gửi duyệt sản phẩm.')
  } finally {
    actionId.value = null
  }
}

async function removeDraft(product: ManagedProduct): Promise<void> {
  if (!window.confirm('Xóa bản nháp “' + product.name + '”?')) return
  actionId.value = product.id
  try {
    await deleteProductDraft(product.id)
    successMessage.value = 'Đã xóa bản nháp.'
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể xóa bản nháp.')
  } finally {
    actionId.value = null
  }
}

async function sendDeletionRequest(): Promise<void> {
  if (!deletingProduct.value) return
  actionId.value = deletingProduct.value.id
  errorMessage.value = ''
  try {
    if (revisingDeletionRequest.value) {
      await resubmitProductChangeRequest(revisingDeletionRequest.value.id, {
        proposed_data: null,
        reason: deletionReason.value,
      })
      successMessage.value = 'Đã bổ sung lý do và gửi lại yêu cầu ngừng hiển thị.'
    } else {
      await requestProductDeletion(deletingProduct.value.id, deletionReason.value)
      successMessage.value = 'Đã gửi yêu cầu ngừng hiển thị. Sản phẩm vẫn công khai cho đến khi được duyệt.'
    }
    deletingProduct.value = null
    revisingDeletionRequest.value = null
    deletionReason.value = ''
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể gửi yêu cầu ngừng hiển thị.')
  } finally {
    actionId.value = null
  }
}

function openDeletionRevision(product: ManagedProduct, request?: ProductChangeRequest): void {
  if (!request) return
  deletingProduct.value = product
  revisingDeletionRequest.value = request
  deletionReason.value = request.reason || ''
}

function closeDeletionDialog(): void {
  deletingProduct.value = null
  revisingDeletionRequest.value = null
  deletionReason.value = ''
}

async function cancelRequest(request?: ProductChangeRequest): Promise<void> {
  if (!request) return
  if (!window.confirm('Hủy yêu cầu đang chờ xử lý?')) return
  actionId.value = request.product_id
  errorMessage.value = ''
  try {
    await cancelProductChangeRequest(request.id)
    successMessage.value = 'Đã hủy yêu cầu thay đổi sản phẩm.'
    await loadData()
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể hủy yêu cầu.')
  } finally {
    actionId.value = null
  }
}

function formatDate(value: string | null): string {
  return value ? new Intl.DateTimeFormat('vi-VN').format(new Date(value)) : '—'
}

onMounted(loadData)
</script>

<template>
  <main class="subject-products-page">
    <header class="page-heading">
      <div>
        <span>Quản lý sản phẩm OCOP</span>
        <h1>Sản phẩm của tôi</h1>
        <p>Hạng sao được khai báo theo giấy chứng nhận; quản trị viên chỉ duyệt cho phép hiển thị.</p>
      </div>
      <RouterLink class="primary-button" to="/chu-the/san-pham/them">+ Thêm sản phẩm</RouterLink>
    </header>

    <div v-if="errorMessage" class="alert alert-danger" role="alert">{{ errorMessage }}</div>
    <div v-if="successMessage" class="alert alert-success" role="status">{{ successMessage }}</div>

    <section class="filter-bar">
      <label>
        Trạng thái
        <select v-model="filter">
          <option value="">Tất cả</option>
          <option v-for="(label, value) in statusLabels" :key="value" :value="value">{{ label }}</option>
        </select>
      </label>
      <strong>{{ filteredProducts.length }} sản phẩm</strong>
    </section>

    <section class="product-panel">
      <p v-if="loading" class="state-message">Đang tải sản phẩm...</p>
      <p v-else-if="!filteredProducts.length" class="state-message">Chưa có sản phẩm phù hợp.</p>
      <div v-else class="product-list">
        <article v-for="product in filteredProducts" :key="product.id">
          <img :src="product.images.find((image) => image.is_primary)?.image_url" alt="" />
          <div class="product-copy">
            <div>
              <span :class="['status', 'status-' + product.status]">{{ statusLabels[product.status] }}</span>
              <span class="stars">{{ product.star }} sao theo chứng nhận</span>
            </div>
            <h2>{{ product.name }}</h2>
            <p>{{ product.category.name }} · {{ product.cert_code }}</p>
            <small>Cập nhật {{ formatDate(product.updated_at) }}</small>
            <p v-if="product.moderation_note" class="moderation-note">
              Phản hồi: {{ product.moderation_note }}
            </p>
            <p v-if="activeRequest(product.id)" class="request-note">
              Có yêu cầu {{ activeRequest(product.id)?.request_type === 'update' ? 'cập nhật' : 'ngừng hiển thị' }}
              — {{ activeRequest(product.id)?.status === 'pending' ? 'đang chờ duyệt' : 'cần bổ sung' }}.
            </p>
          </div>
          <div class="product-actions">
            <RouterLink
              v-if="['draft', 'needs_revision', 'rejected'].includes(product.status) || (product.status === 'approved' && !activeRequest(product.id))"
              :to="'/chu-the/san-pham/' + product.id + '/chinh-sua'"
            >
              {{ product.status === 'approved' ? 'Đề nghị cập nhật' : 'Chỉnh sửa' }}
            </RouterLink>
            <RouterLink
              v-if="activeRequest(product.id)?.status === 'needs_revision' && activeRequest(product.id)?.request_type === 'update'"
              :to="'/chu-the/yeu-cau/' + activeRequest(product.id)?.id + '/chinh-sua'"
            >
              Bổ sung yêu cầu
            </RouterLink>
            <button
              v-if="activeRequest(product.id)?.status === 'needs_revision' && activeRequest(product.id)?.request_type === 'delete'"
              class="approve-button"
              type="button"
              @click="openDeletionRevision(product, activeRequest(product.id))"
            >
              Bổ sung lý do
            </button>
            <button
              v-if="['draft', 'needs_revision', 'rejected'].includes(product.status)"
              class="approve-button"
              type="button"
              :disabled="actionId === product.id"
              @click="submit(product)"
            >
              Gửi duyệt
            </button>
            <button
              v-if="['draft', 'needs_revision', 'rejected'].includes(product.status)"
              class="danger-button"
              type="button"
              @click="removeDraft(product)"
            >
              Xóa bản nháp
            </button>
            <button
              v-if="product.status === 'approved' && !activeRequest(product.id)"
              class="danger-button"
              type="button"
              @click="deletingProduct = product; revisingDeletionRequest = null; deletionReason = ''"
            >
              Đề nghị ngừng
            </button>
            <button
              v-if="activeRequest(product.id)"
              class="danger-button"
              type="button"
              :disabled="actionId === product.id"
              @click="cancelRequest(activeRequest(product.id))"
            >
              Hủy yêu cầu
            </button>
          </div>
        </article>
      </div>
    </section>

    <div v-if="deletingProduct" class="dialog-backdrop" @click.self="closeDeletionDialog">
      <form class="dialog-card" @submit.prevent="sendDeletionRequest">
        <h2>{{ revisingDeletionRequest ? 'Bổ sung yêu cầu ngừng hiển thị' : 'Đề nghị ngừng hiển thị' }}</h2>
        <p>“{{ deletingProduct.name }}” vẫn công khai cho đến khi quản trị viên chấp thuận.</p>
        <label>
          Lý do
          <textarea v-model="deletionReason" required minlength="5" rows="4" />
        </label>
        <div>
          <button type="button" @click="closeDeletionDialog">Đóng</button>
          <button class="danger-fill" type="submit">{{ revisingDeletionRequest ? 'Gửi lại yêu cầu' : 'Gửi yêu cầu' }}</button>
        </div>
      </form>
    </div>
  </main>
</template>

<style scoped>
.subject-products-page { display: grid; gap: 20px; }
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: 20px; }
.page-heading span { color: var(--ocop-primary-700); font-size: 11px; font-weight: 800; text-transform: uppercase; }
.page-heading h1 { margin: 4px 0; color: var(--ocop-navy); font-size: 30px; }
.page-heading p { margin: 0; color: var(--ocop-slate); font-size: 13px; }
.primary-button, .product-actions a { padding: 10px 14px; border-radius: 9px; background: var(--ocop-primary-700); color: #fff; font-size: 12px; font-weight: 700; text-align: center; text-decoration: none; }
.filter-bar { display: flex; padding: 14px 16px; align-items: end; justify-content: space-between; border: 1px solid var(--ocop-border); border-radius: 12px; background: #fff; }
.filter-bar label, .dialog-card label { display: grid; gap: 5px; color: #56677c; font-size: 11px; font-weight: 700; }
.filter-bar select { min-width: 190px; padding: 8px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; }
.filter-bar strong { color: var(--ocop-primary-700); font-size: 12px; }
.product-panel { overflow: hidden; border: 1px solid var(--ocop-border); border-radius: 14px; background: #fff; }
.product-list article { display: grid; padding: 16px; align-items: center; grid-template-columns: 88px minmax(0, 1fr) auto; gap: 16px; border-bottom: 1px solid #edf1f4; }
.product-list article:last-child { border-bottom: 0; }
.product-list article > img { width: 88px; height: 76px; border-radius: 10px; background: #edf2f0; object-fit: cover; }
.product-copy h2 { margin: 7px 0 3px; font-size: 16px; }
.product-copy p, .product-copy small { margin: 0; color: var(--ocop-slate); font-size: 11px; }
.product-copy > div { display: flex; gap: 7px; }
.status, .stars { padding: 3px 7px; border-radius: 999px; background: #eef2f6; color: #526277; font-size: 9px; font-weight: 800; }
.status-approved { background: #dcfce7; color: #167044; }
.status-pending { background: #fff7d6; color: #8d6200; }
.status-needs_revision, .status-rejected { background: #fee2e2; color: #b42318; }
.moderation-note, .request-note { margin-top: 7px !important; padding: 6px 8px; border-radius: 6px; background: #fff7ed; color: #9a4f10 !important; }
.request-note { background: #eff6ff; color: #1d4f91 !important; }
.product-actions { display: grid; min-width: 140px; gap: 7px; }
.product-actions button, .dialog-card button { padding: 8px 10px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; font-size: 11px; font-weight: 700; }
.approve-button { border-color: var(--ocop-primary-700) !important; color: var(--ocop-primary-700); }
.danger-button { border-color: #fecaca !important; color: #b42318; }
.state-message { padding: 50px 20px; color: var(--ocop-slate); text-align: center; }
.dialog-backdrop { position: fixed; z-index: 80; inset: 0; display: grid; padding: 20px; place-items: center; background: rgb(15 23 43 / 55%); }
.dialog-card { width: min(100%, 500px); padding: 24px; border-radius: 15px; background: #fff; box-shadow: 0 25px 60px rgb(15 23 43 / 25%); }
.dialog-card h2 { margin-top: 0; }
.dialog-card textarea { padding: 10px; border: 1px solid var(--ocop-border); border-radius: 8px; resize: vertical; }
.dialog-card > div { display: flex; margin-top: 16px; justify-content: flex-end; gap: 8px; }
.danger-fill { border-color: #b42318 !important; background: #b42318 !important; color: #fff; }
@media (max-width: 767.98px) {
  .page-heading { align-items: stretch; flex-direction: column; }
  .primary-button { text-align: center; }
  .product-list article { grid-template-columns: 64px minmax(0, 1fr); }
  .product-list article > img { width: 64px; height: 64px; }
  .product-actions { grid-column: 1 / -1; grid-template-columns: repeat(2, minmax(0, 1fr)); }
}
</style>
