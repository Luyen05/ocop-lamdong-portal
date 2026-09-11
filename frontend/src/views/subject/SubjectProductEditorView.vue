<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getCategories } from '@/services/categories'
import { getApiErrorMessage } from '@/services/api-error'
import {
  createProductDraft,
  getProductChangeRequest,
  getMyProduct,
  requestProductUpdate,
  resubmitProductChangeRequest,
  submitProduct,
  updateProductDraft,
} from '@/services/product-management'
import type { Category } from '@/types/category'
import type {
  ManagedProduct,
  ProductChangeRequest,
  ProductWritePayload,
} from '@/types/product-management'

const route = useRoute()
const router = useRouter()
const categories = ref<Category[]>([])
const currentProduct = ref<ManagedProduct | null>(null)
const currentRequest = ref<ProductChangeRequest | null>(null)
const loading = ref(true)
const saving = ref(false)
const errorMessage = ref('')
const updateReason = ref('')

const productId = computed(() => {
  const raw = route.params.id
  return typeof raw === 'string' ? Number(raw) : null
})
const requestId = computed(() => {
  const raw = route.params.requestId
  return typeof raw === 'string' ? Number(raw) : null
})
const isRequestRevision = computed(() => Boolean(currentRequest.value))
const isApprovedUpdate = computed(
  () => !isRequestRevision.value && currentProduct.value?.status === 'approved',
)
const pageTitle = computed(() =>
  isRequestRevision.value
    ? 'Bổ sung yêu cầu cập nhật'
    : isApprovedUpdate.value
      ? 'Đề nghị cập nhật sản phẩm'
      : productId.value
        ? 'Chỉnh sửa sản phẩm'
        : 'Thêm sản phẩm',
)

const today = new Date()
const threeYearsLater = new Date(today)
threeYearsLater.setFullYear(today.getFullYear() + 3)
const isoDate = (value: Date): string => value.toISOString().slice(0, 10)

const form = reactive<ProductWritePayload>({
  category_id: 0,
  name: '',
  star: 3,
  price: '0',
  unit: '',
  cert_code: '',
  cert_issued_at: isoDate(today),
  cert_expires_at: isoDate(threeYearsLater),
  issuing_authority: '',
  certificate_url: '',
  vietgap_code: null,
  description: '',
  story: null,
  ingredients: null,
  usage_instructions: null,
  images: [{ image_url: '', is_primary: true, sort_order: 0 }],
})

function fillForm(product: ManagedProduct | ProductWritePayload): void {
  form.category_id = product.category_id
  form.name = product.name
  form.star = product.star
  form.price = String(product.price)
  form.unit = product.unit
  form.cert_code = product.cert_code || ''
  form.cert_issued_at = product.cert_issued_at || ''
  form.cert_expires_at = product.cert_expires_at || ''
  form.issuing_authority = product.issuing_authority || ''
  form.certificate_url = product.certificate_url || ''
  form.vietgap_code = product.vietgap_code
  form.description = product.description
  form.story = product.story
  form.ingredients = product.ingredients
  form.usage_instructions = product.usage_instructions
  const primaryImage = product.images.find((image) => image.is_primary) || product.images[0]
  form.images = [{ image_url: primaryImage?.image_url || '', is_primary: true, sort_order: 0 }]
}

function normalizedPayload(): ProductWritePayload {
  return {
    ...form,
    vietgap_code: form.vietgap_code || null,
    story: form.story || null,
    ingredients: form.ingredients || null,
    usage_instructions: form.usage_instructions || null,
    images: form.images.map((image, index) => ({ ...image, sort_order: index })),
  }
}

async function load(): Promise<void> {
  loading.value = true
  try {
    const categoryData = await getCategories()
    categories.value = categoryData.items
    if (!form.category_id && categories.value[0]) form.category_id = categories.value[0].id
    if (requestId.value) {
      const request = await getProductChangeRequest('subject', requestId.value)
      if (request.status !== 'needs_revision' || request.request_type !== 'update' || !request.proposed_data) {
        errorMessage.value = 'Chỉ yêu cầu cập nhật cần bổ sung mới có thể chỉnh sửa.'
        return
      }
      currentRequest.value = request
      updateReason.value = request.reason || ''
      fillForm(request.proposed_data)
    } else if (productId.value) {
      const product = await getMyProduct(productId.value)
      if (!['draft', 'needs_revision', 'rejected', 'approved'].includes(product.status)) {
        errorMessage.value = 'Sản phẩm đang chờ xử lý và không thể chỉnh sửa.'
        return
      }
      currentProduct.value = product
      fillForm(product)
    }
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải biểu mẫu sản phẩm.')
  } finally {
    loading.value = false
  }
}

async function save(submitAfterSave = false): Promise<void> {
  saving.value = true
  errorMessage.value = ''
  try {
    const payload = normalizedPayload()
    if (currentRequest.value) {
      await resubmitProductChangeRequest(currentRequest.value.id, {
        proposed_data: payload,
        reason: updateReason.value || null,
      })
    } else if (isApprovedUpdate.value && currentProduct.value) {
      await requestProductUpdate(currentProduct.value.id, payload, updateReason.value)
    } else {
      const saved = currentProduct.value
        ? await updateProductDraft(currentProduct.value.id, payload)
        : await createProductDraft(payload)
      if (submitAfterSave) await submitProduct(saved.id)
    }
    await router.push({
      name: 'subject-products',
      query: {
        saved: isRequestRevision.value
          ? 'resubmitted'
          : isApprovedUpdate.value
            ? 'requested'
            : submitAfterSave
              ? 'submitted'
              : 'draft',
      },
    })
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể lưu thông tin sản phẩm.')
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="editor-page">
    <header>
      <RouterLink to="/chu-the/san-pham">← Danh sách sản phẩm</RouterLink>
      <span>{{ isApprovedUpdate || isRequestRevision ? 'Yêu cầu thay đổi' : 'Hồ sơ sản phẩm OCOP' }}</span>
      <h1>{{ pageTitle }}</h1>
      <p v-if="isRequestRevision">
        Cập nhật nội dung theo phản hồi của quản trị viên rồi gửi lại yêu cầu.
      </p>
      <p v-else-if="isApprovedUpdate">
        Phiên bản hiện tại vẫn công khai. Dữ liệu bên dưới chỉ được áp dụng sau khi quản trị viên duyệt.
      </p>
      <p v-else>
        Khai báo đúng hạng sao ghi trên giấy chứng nhận. Quản trị viên website không cấp hạng sao OCOP.
      </p>
    </header>

    <div v-if="errorMessage" class="alert alert-danger" role="alert">{{ errorMessage }}</div>
    <p v-if="loading" class="loading-card">Đang tải biểu mẫu...</p>

    <form v-else class="product-form" @submit.prevent="save(isApprovedUpdate || isRequestRevision)">
      <section>
        <div class="section-heading">
          <strong>1. Thông tin sản phẩm</strong>
          <small>Các trường có dấu * là bắt buộc</small>
        </div>
        <div class="form-grid">
          <label class="wide">Tên sản phẩm *<input v-model.trim="form.name" required minlength="2" /></label>
          <label>Danh mục *
            <select v-model.number="form.category_id" required>
              <option v-for="category in categories" :key="category.id" :value="category.id">{{ category.name }}</option>
            </select>
          </label>
          <label>Giá tham khảo *<input v-model="form.price" type="number" min="0" step="1000" required /></label>
          <label>Đơn vị tính *<input v-model.trim="form.unit" placeholder="Hộp 500g" required /></label>
          <label class="wide">Mô tả sản phẩm *<textarea v-model.trim="form.description" rows="4" required minlength="10" /></label>
          <label class="wide">Câu chuyện sản phẩm<textarea v-model="form.story" rows="3" /></label>
          <label>Thành phần<textarea v-model="form.ingredients" rows="3" /></label>
          <label>Hướng dẫn sử dụng<textarea v-model="form.usage_instructions" rows="3" /></label>
        </div>
      </section>

      <section>
        <div class="section-heading">
          <strong>2. Chứng nhận OCOP</strong>
          <small>Admin chỉ đối chiếu minh chứng và duyệt hiển thị</small>
        </div>
        <div class="notice">Hạng sao phải khớp giấy chứng nhận hoặc quyết định công nhận của cơ quan có thẩm quyền.</div>
        <div class="form-grid">
          <label>Hạng sao theo chứng nhận *
            <select v-model.number="form.star" required>
              <option :value="3">3 sao</option><option :value="4">4 sao</option><option :value="5">5 sao</option>
            </select>
          </label>
          <label>Mã chứng nhận / số quyết định *<input v-model.trim="form.cert_code" required /></label>
          <label>Ngày cấp *<input v-model="form.cert_issued_at" type="date" required /></label>
          <label>Ngày hết hạn *<input v-model="form.cert_expires_at" type="date" required /></label>
          <label class="wide">Cơ quan công nhận *<input v-model.trim="form.issuing_authority" required /></label>
          <label class="wide">Đường dẫn tài liệu chứng nhận *
            <input v-model.trim="form.certificate_url" type="url" placeholder="https://..." required />
            <small>Tạm dùng URL; upload Firebase sẽ được nối ở module ảnh.</small>
          </label>
          <label class="wide">Mã VietGAP (nếu có)<input v-model="form.vietgap_code" /></label>
        </div>
      </section>

      <section>
        <div class="section-heading"><strong>3. Ảnh đại diện</strong><small>JPEG, PNG hoặc WebP</small></div>
        <label>Đường dẫn ảnh chính *
          <input v-model.trim="form.images[0].image_url" type="url" placeholder="https://..." required />
          <small>Tạm dùng URL; backend upload Firebase sẽ thay thế bước này sau.</small>
        </label>
        <img v-if="form.images[0].image_url" class="image-preview" :src="form.images[0].image_url" alt="Xem trước ảnh sản phẩm" />
      </section>

      <section v-if="isApprovedUpdate || isRequestRevision">
        <div class="section-heading"><strong>4. Lý do cập nhật</strong></div>
        <label>Lý do đề nghị thay đổi
          <textarea v-model.trim="updateReason" rows="3" placeholder="Ví dụ: cập nhật bao bì và giá bán mới" />
        </label>
      </section>

      <footer>
        <RouterLink to="/chu-the/san-pham">Hủy</RouterLink>
        <button
          v-if="!isApprovedUpdate"
          class="secondary-button"
          type="button"
          :disabled="saving"
          @click="save(false)"
        >
          Lưu bản nháp
        </button>
        <button class="primary-button" type="submit" :disabled="saving">
          {{ saving ? 'Đang lưu...' : isRequestRevision ? 'Gửi lại yêu cầu' : isApprovedUpdate ? 'Gửi yêu cầu cập nhật' : 'Lưu và gửi duyệt' }}
        </button>
      </footer>
    </form>
  </main>
</template>

<style scoped>
.editor-page { display: grid; max-width: 960px; margin-inline: auto; gap: 18px; }
header > a { color: var(--ocop-primary-700); font-size: 12px; font-weight: 700; text-decoration: none; }
header > span { display: block; margin-top: 16px; color: var(--ocop-primary-700); font-size: 10px; font-weight: 800; text-transform: uppercase; }
header h1 { margin: 4px 0; font-size: 30px; }
header p { margin: 0; color: var(--ocop-slate); font-size: 13px; }
.loading-card, .product-form section { padding: 22px; border: 1px solid var(--ocop-border); border-radius: 14px; background: #fff; }
.product-form { display: grid; gap: 16px; }
.section-heading { display: flex; margin-bottom: 16px; justify-content: space-between; gap: 12px; }
.section-heading strong { color: var(--ocop-navy); }
.section-heading small, label small { color: var(--ocop-slate); font-size: 10px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
label { display: grid; gap: 6px; color: #526277; font-size: 11px; font-weight: 700; }
label.wide { grid-column: 1 / -1; }
input, select, textarea { width: 100%; padding: 10px 11px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; color: var(--ocop-navy); }
textarea { resize: vertical; }
.notice { margin-bottom: 15px; padding: 10px 12px; border-radius: 8px; background: #eff6ff; color: #1d4f91; font-size: 11px; }
.image-preview { width: 180px; height: 130px; margin-top: 12px; border-radius: 10px; object-fit: cover; }
footer { display: flex; padding: 16px 0 30px; align-items: center; justify-content: flex-end; gap: 9px; }
footer a, footer button { padding: 10px 15px; border: 1px solid var(--ocop-border); border-radius: 9px; background: #fff; color: var(--ocop-navy); font-size: 12px; font-weight: 700; text-decoration: none; }
.primary-button { border-color: var(--ocop-primary-700) !important; background: var(--ocop-primary-700) !important; color: #fff !important; }
.secondary-button { color: var(--ocop-primary-700) !important; }
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  label.wide { grid-column: auto; }
  .section-heading { flex-direction: column; }
  footer { align-items: stretch; flex-direction: column-reverse; }
  footer a, footer button { text-align: center; }
}
</style>
