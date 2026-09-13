<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { getCategories } from '@/services/categories'
import { getApiErrorMessage } from '@/services/api-error'
import {
  createProductDraft,
  deleteTemporaryProductCertificate,
  deleteTemporaryProductImage,
  getProductChangeRequest,
  getMyProduct,
  requestProductUpdate,
  resubmitProductChangeRequest,
  submitProduct,
  uploadProductCertificate,
  uploadProductImage,
  updateProductDraft,
} from '@/services/product-management'
import type { Category } from '@/types/category'
import type {
  ManagedProduct,
  ProductDraftPayload,
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
const uploadingImage = ref(false)
const uploadingCertificate = ref(false)
const errorMessage = ref('')
const imageErrorMessage = ref('')
const certificateErrorMessage = ref('')
const certificateFileName = ref('')
const imageLoadFailed = ref(false)
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

const form = reactive<ProductDraftPayload>({
  category_id: 0,
  name: '',
  star: null,
  price: null,
  unit: null,
  cert_code: null,
  cert_issued_at: null,
  cert_expires_at: null,
  issuing_authority: null,
  certificate_url: null,
  certificate_storage_path: null,
  vietgap_code: null,
  description: null,
  story: null,
  ingredients: null,
  usage_instructions: null,
  images: [],
})

const completionItems = computed(() => [
  {
    label: 'Thông tin cơ bản',
    complete: Boolean(form.name.trim().length >= 2 && form.category_id && (form.description?.trim().length || 0) >= 10),
  },
  {
    label: 'Thông tin chứng nhận',
    complete: Boolean(
      form.star
      && form.cert_code?.trim()
      && form.cert_issued_at
      && form.cert_expires_at
      && form.issuing_authority?.trim()
      && (form.certificate_storage_path || form.certificate_url)
    ),
  },
  { label: 'Ảnh đại diện', complete: Boolean(form.images[0]?.image_url) },
])
const isSubmissionReady = computed(() => completionItems.value.every((item) => item.complete))

function fillForm(product: ManagedProduct | ProductWritePayload): void {
  form.category_id = product.category_id
  form.name = product.name
  form.star = product.star
  form.price = product.price === null ? null : String(product.price)
  form.unit = product.unit
  form.cert_code = product.cert_code || ''
  form.cert_issued_at = product.cert_issued_at || ''
  form.cert_expires_at = product.cert_expires_at || ''
  form.issuing_authority = product.issuing_authority || ''
  form.certificate_url = product.certificate_url || ''
  form.certificate_storage_path = product.certificate_storage_path || null
  certificateFileName.value = product.certificate_storage_path?.split('/').pop() || ''
  form.vietgap_code = product.vietgap_code
  form.description = product.description
  form.story = product.story
  form.ingredients = product.ingredients
  form.usage_instructions = product.usage_instructions
  const primaryImage = product.images.find((image) => image.is_primary) || product.images[0]
  form.images = primaryImage ? [{
    image_url: primaryImage.image_url,
    storage_path: primaryImage?.storage_path?.startsWith('products/')
      ? primaryImage.storage_path
      : null,
    is_primary: true,
    sort_order: 0,
  }] : []
  imageLoadFailed.value = false
}

async function handleImageSelection(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return

  imageErrorMessage.value = ''
  if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
    imageErrorMessage.value = 'Chỉ chấp nhận ảnh JPEG, PNG hoặc WebP.'
    return
  }
  if (file.size > 5 * 1024 * 1024) {
    imageErrorMessage.value = 'Ảnh không được vượt quá 5 MB.'
    return
  }

  const previousStoragePath = form.images[0]?.storage_path
  uploadingImage.value = true
  try {
    const uploaded = await uploadProductImage(file)
    form.images = [{
      image_url: uploaded.image_url,
      storage_path: uploaded.storage_path,
      is_primary: true,
      sort_order: 0,
    }]
    imageLoadFailed.value = false
    if (previousStoragePath && previousStoragePath !== uploaded.storage_path) {
      await deleteTemporaryProductImage(previousStoragePath).catch(() => undefined)
    }
  } catch (error) {
    imageErrorMessage.value = getApiErrorMessage(error, 'Không thể tải ảnh lên máy chủ.')
  } finally {
    uploadingImage.value = false
  }
}

async function handleCertificateSelection(event: Event): Promise<void> {
  const input = event.target as HTMLInputElement
  const file = input.files?.[0]
  input.value = ''
  if (!file) return
  certificateErrorMessage.value = ''
  if (!['application/pdf', 'image/jpeg', 'image/png'].includes(file.type)) {
    certificateErrorMessage.value = 'Chỉ chấp nhận chứng nhận PDF, JPEG hoặc PNG.'
    return
  }
  if (file.size > 10 * 1024 * 1024) {
    certificateErrorMessage.value = 'File chứng nhận không được vượt quá 10 MB.'
    return
  }
  const previousStoragePath = form.certificate_storage_path
  uploadingCertificate.value = true
  try {
    const uploaded = await uploadProductCertificate(file)
    form.certificate_storage_path = uploaded.storage_path
    form.certificate_url = null
    certificateFileName.value = uploaded.original_filename
    if (previousStoragePath && previousStoragePath !== uploaded.storage_path) {
      await deleteTemporaryProductCertificate(previousStoragePath).catch(() => undefined)
    }
  } catch (error) {
    certificateErrorMessage.value = getApiErrorMessage(error, 'Không thể tải giấy chứng nhận lên máy chủ.')
  } finally {
    uploadingCertificate.value = false
  }
}

function handleImageError(): void {
  imageLoadFailed.value = true
}

function normalizedDraftPayload(): ProductDraftPayload {
  return {
    category_id: form.category_id,
    name: form.name.trim(),
    star: form.star || null,
    price: form.price === '' ? null : form.price,
    unit: form.unit?.trim() || null,
    cert_code: form.cert_code?.trim() || null,
    cert_issued_at: form.cert_issued_at || null,
    cert_expires_at: form.cert_expires_at || null,
    issuing_authority: form.issuing_authority?.trim() || null,
    certificate_url: form.certificate_url?.trim() || null,
    certificate_storage_path: form.certificate_storage_path,
    vietgap_code: form.vietgap_code || null,
    description: form.description?.trim() || null,
    story: form.story || null,
    ingredients: form.ingredients || null,
    usage_instructions: form.usage_instructions || null,
    images: form.images.map((image, index) => ({ ...image, sort_order: index })),
  }
}

function submissionPayload(): ProductWritePayload {
  return normalizedDraftPayload() as ProductWritePayload
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
  if (form.name.trim().length < 2 || !form.category_id) {
    errorMessage.value = 'Cần nhập tên và chọn danh mục trước khi lưu bản nháp.'
    return
  }
  if (submitAfterSave && !isSubmissionReady.value) {
    errorMessage.value = 'Hồ sơ chưa đủ điều kiện gửi duyệt. Vui lòng hoàn thành các mục còn thiếu.'
    return
  }
  saving.value = true
  errorMessage.value = ''
  try {
    const draftPayload = normalizedDraftPayload()
    if (currentRequest.value) {
      await resubmitProductChangeRequest(currentRequest.value.id, {
        proposed_data: submissionPayload(),
        reason: updateReason.value || null,
      })
    } else if (isApprovedUpdate.value && currentProduct.value) {
      await requestProductUpdate(currentProduct.value.id, submissionPayload(), updateReason.value)
    } else {
      const saved = currentProduct.value
        ? await updateProductDraft(currentProduct.value.id, draftPayload)
        : await createProductDraft(draftPayload)
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
      <RouterLink to="/chu-the/san-pham"><AppIcon name="arrowLeft" :size="14" /> Danh sách sản phẩm</RouterLink>
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

    <form v-else class="product-form" @submit.prevent="save(true)">
      <aside class="completion-card" aria-label="Mức độ hoàn thiện hồ sơ">
        <div><strong>Tiến độ hồ sơ</strong><span>{{ completionItems.filter((item) => item.complete).length }}/{{ completionItems.length }} mục</span></div>
        <ul>
          <li v-for="item in completionItems" :key="item.label" :class="{ complete: item.complete }">
            <span><AppIcon :name="item.complete ? 'checkCircle' : 'circle'" :size="14" /></span>{{ item.label }}
          </li>
        </ul>
      </aside>
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
          <label>Giá tham khảo<input v-model="form.price" type="number" min="0" step="1000" placeholder="Để trống nếu cần liên hệ" /></label>
          <label>Đơn vị tính<input v-model.trim="form.unit" placeholder="Hộp 500g" /></label>
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
              <option :value="null" disabled>Chọn hạng sao</option>
              <option :value="3">3 sao</option><option :value="4">4 sao</option><option :value="5">5 sao</option>
            </select>
          </label>
          <label>Mã chứng nhận / số quyết định *<input v-model.trim="form.cert_code" required /></label>
          <label>Ngày cấp *<input v-model="form.cert_issued_at" type="date" required /></label>
          <label>Ngày hết hạn *<input v-model="form.cert_expires_at" type="date" required /></label>
          <label class="wide">Cơ quan công nhận *<input v-model.trim="form.issuing_authority" required /></label>
          <label class="wide certificate-upload">Bản chụp giấy chứng nhận *
            <input
              type="file"
              accept="application/pdf,image/jpeg,image/png"
              :disabled="uploadingCertificate || saving"
              @change="handleCertificateSelection"
            />
            <small>PDF, JPEG hoặc PNG · tối đa 10 MB · chỉ chủ thể và quản trị viên được xem.</small>
          </label>
          <p v-if="uploadingCertificate" class="upload-status wide" role="status">Đang tải giấy chứng nhận...</p>
          <div v-if="certificateErrorMessage" class="alert alert-danger image-alert wide" role="alert">{{ certificateErrorMessage }}</div>
          <div v-if="form.certificate_storage_path || form.certificate_url" class="certificate-file wide">
            <span><AppIcon name="checkCircle" :size="16" /></span>
            <div><strong>{{ certificateFileName || 'Tài liệu chứng nhận đã liên kết' }}</strong><small>{{ form.certificate_storage_path ? 'File riêng tư trên hệ thống' : 'Tài liệu từ dữ liệu cũ' }}</small></div>
          </div>
          <label class="wide">Mã VietGAP (nếu có)<input v-model="form.vietgap_code" /></label>
        </div>
      </section>

      <section>
        <div class="section-heading"><strong>3. Ảnh đại diện</strong><small>JPEG, PNG hoặc WebP · tối đa 5 MB</small></div>
        <label class="upload-field">Chọn ảnh sản phẩm *
          <input
            type="file"
            accept="image/jpeg,image/png,image/webp"
            :disabled="uploadingImage || saving"
            @change="handleImageSelection"
          />
          <small>Ảnh được lưu trên máy chủ của hệ thống. Mỗi sản phẩm dùng một ảnh đại diện.</small>
        </label>
        <p v-if="uploadingImage" class="upload-status" role="status">Đang tải ảnh lên...</p>
        <div v-if="imageErrorMessage" class="alert alert-danger image-alert" role="alert">{{ imageErrorMessage }}</div>
        <div v-if="form.images[0]?.image_url" class="preview-card">
          <img
            v-if="!imageLoadFailed"
            class="image-preview"
            :src="form.images[0]?.image_url"
            alt="Xem trước ảnh sản phẩm"
            @error="handleImageError"
          />
          <div v-else class="image-placeholder" role="img" aria-label="Ảnh sản phẩm không tải được">OCOP</div>
          <div>
            <strong>Ảnh đại diện đã chọn</strong>
            <small v-if="form.images[0]?.storage_path">Ảnh tải lên hệ thống</small>
            <small v-else>Ảnh từ dữ liệu cũ</small>
          </div>
        </div>
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
          :disabled="saving || uploadingImage || uploadingCertificate"
          @click="save(false)"
        >
          Lưu bản nháp
        </button>
        <button class="primary-button" type="submit" :disabled="saving || uploadingImage || uploadingCertificate || !isSubmissionReady">
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
.completion-card { padding: 16px 20px; border: 1px solid #b8ddcf; border-radius: 14px; background: #f3fbf7; }
.completion-card > div { display: flex; align-items: center; justify-content: space-between; gap: 12px; }
.completion-card > div span { color: var(--ocop-primary-700); font-size: 12px; font-weight: 800; }
.completion-card ul { display: flex; margin: 12px 0 0; padding: 0; flex-wrap: wrap; gap: 8px; list-style: none; }
.completion-card li { display: flex; padding: 6px 9px; align-items: center; gap: 5px; border-radius: 999px; background: #fff; color: #7b8797; font-size: 10px; font-weight: 700; }
.completion-card li.complete { background: #daf5e8; color: #08745a; }
.section-heading { display: flex; margin-bottom: 16px; justify-content: space-between; gap: 12px; }
.section-heading strong { color: var(--ocop-navy); }
.section-heading small, label small { color: var(--ocop-slate); font-size: 10px; }
.form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
label { display: grid; gap: 6px; color: #526277; font-size: 11px; font-weight: 700; }
label.wide { grid-column: 1 / -1; }
input, select, textarea { width: 100%; padding: 10px 11px; border: 1px solid var(--ocop-border); border-radius: 8px; background: #fff; color: var(--ocop-navy); }
textarea { resize: vertical; }
.notice { margin-bottom: 15px; padding: 10px 12px; border-radius: 8px; background: #eff6ff; color: #1d4f91; font-size: 11px; }
.upload-field input[type='file'] { padding: 8px; cursor: pointer; }
.certificate-upload input[type='file'] { padding: 8px; cursor: pointer; }
.wide { grid-column: 1 / -1; }
.certificate-file { display: flex; padding: 11px 12px; align-items: center; gap: 10px; border: 1px solid #b8ddcf; border-radius: 9px; background: #f3fbf7; color: var(--ocop-primary-700); }
.certificate-file > span { font-size: 18px; font-weight: 800; }
.certificate-file > div { display: grid; gap: 2px; }
.certificate-file strong { color: var(--ocop-navy); font-size: 11px; overflow-wrap: anywhere; }
.certificate-file small { color: var(--ocop-slate); font-size: 9px; }
.upload-status { margin: 12px 0 0; color: var(--ocop-primary-700); font-size: 12px; font-weight: 700; }
.image-alert { margin: 12px 0 0; font-size: 12px; }
.preview-card { display: flex; width: fit-content; max-width: 100%; margin-top: 14px; padding: 8px; align-items: center; gap: 12px; border: 1px solid var(--ocop-border); border-radius: 12px; background: var(--ocop-surface); }
.preview-card > div:last-child { display: grid; gap: 3px; }
.preview-card strong { font-size: 12px; }
.preview-card small { color: var(--ocop-slate); font-size: 10px; }
.image-preview, .image-placeholder { width: 180px; height: 130px; border-radius: 10px; object-fit: cover; }
.image-placeholder { display: grid; place-items: center; background: linear-gradient(135deg, #e8f5ef, #d7eee5); color: var(--ocop-primary-700); font-size: 22px; font-weight: 800; }
footer { display: flex; padding: 16px 0 30px; align-items: center; justify-content: flex-end; gap: 9px; }
footer a, footer button { padding: 10px 15px; border: 1px solid var(--ocop-border); border-radius: 9px; background: #fff; color: var(--ocop-navy); font-size: 12px; font-weight: 700; text-decoration: none; }
.primary-button { border-color: var(--ocop-primary-700) !important; background: var(--ocop-primary-700) !important; color: #fff !important; }
.secondary-button { color: var(--ocop-primary-700) !important; }
@media (max-width: 640px) {
  .form-grid { grid-template-columns: 1fr; }
  label.wide { grid-column: auto; }
  .section-heading { flex-direction: column; }
  .completion-card ul { display: grid; }
  footer { align-items: stretch; flex-direction: column-reverse; }
  footer a, footer button { text-align: center; }
  .preview-card { width: 100%; align-items: stretch; flex-direction: column; }
  .image-preview, .image-placeholder { width: 100%; height: 190px; }
}
</style>
