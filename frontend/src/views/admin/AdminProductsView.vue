<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter, type LocationQuery, type LocationQueryRaw } from 'vue-router'

import ProductEvidenceManager from '@/components/admin/ProductEvidenceManager.vue'
import AppIcon from '@/components/ui/AppIcon.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import StatusPanel from '@/components/ui/StatusPanel.vue'
import { useConfirmDialog } from '@/composables/useConfirmDialog'
import { useDialogFocus } from '@/composables/useDialogFocus'
import { useFlashFocus } from '@/composables/useFlashFocus'
import { getApiErrorMessage } from '@/services/api-error'
import { getCategories } from '@/services/categories'
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
/** Lọc theo hạn giấy chứng nhận: backend chưa có tham số này nên lọc phía trình duyệt trên sản phẩm đã duyệt. */
type ExpiryFilter = '' | 'expired' | 'soon'
type ComparableProductField = Exclude<keyof ProductWritePayload, 'images'>

const comparisonFields: Array<{ key: ComparableProductField; label: string }> = [
  { key: 'name', label: 'Tên sản phẩm' },
  { key: 'category_id', label: 'Nhóm sản phẩm' },
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

const workflowStatuses: ProductWorkflowStatus[] = [
  'pending',
  'needs_revision',
  'approved',
  'draft',
  'rejected',
  'suspended',
  'archived',
]
/** Số ngày coi là "sắp hết hạn", khớp EXPIRING_WINDOW_DAYS của backend (admin_statistics.py). */
const EXPIRING_WINDOW_DAYS = 90
const EXPIRY_PAGE_SIZE = 100
const EXPIRY_MAX_PAGES = 10

const route = useRoute()
const router = useRouter()

const products = ref<ManagedProduct[]>([])
const productTotal = ref(0)
/** Tổng sản phẩm đang chờ duyệt, độc lập với bộ lọc đang chọn (null: chưa đếm được). */
const pendingProductTotal = ref<number | null>(null)
const page = ref(1)
const pageSize = 20
const requests = ref<ProductChangeRequest[]>([])
const loading = ref(true)
const loadError = ref('')
const successMessage = ref('')
/** Lỗi khi duyệt/từ chối: hiện ngay trong hộp thoại duyệt, không nằm sau lớp phủ. */
const moderationError = ref('')
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
const categoryNames = ref(new Map<number, string>())

// Bộ lọc đang gõ/chọn trên form (chỉ áp dụng khi bấm "Áp dụng"). Bộ lọc đã áp dụng nằm trên URL.
const search = ref('')
const workflowStatus = ref<ProductWorkflowStatus | ''>('pending')
const verificationLevel = ref<VerificationLevel | ''>('')
const verificationStatus = ref<ProductVerificationStatus | ''>('')
const evidenceIssue = ref<EvidenceIssueFilter>('')
const expiryFilter = ref<ExpiryFilter>('')

const confirm = useConfirmDialog()
const { revealFlash } = useFlashFocus({ success: successMessage })

const activeTab = computed<'products' | 'changes'>(() => (route.query.tab === 'changes' ? 'changes' : 'products'))
const pendingRequests = computed(() => requests.value.filter((item) => item.status === 'pending'))
const pendingBadgeTotal = computed(() =>
  pendingProductTotal.value === null ? null : pendingProductTotal.value + pendingRequests.value.length,
)
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
const expiryLabel = computed(() =>
  expiryFilter.value === 'expired'
    ? 'Giấy chứng nhận đã hết hạn'
    : expiryFilter.value === 'soon'
      ? `Giấy chứng nhận hết hạn trong ${EXPIRING_WINDOW_DAYS} ngày tới`
      : '',
)

// ---------- Bộ lọc <-> URL ----------
function firstQuery(value: LocationQuery[string] | undefined): string {
  const first = Array.isArray(value) ? value[0] : value
  return typeof first === 'string' ? first : ''
}

/** Đọc bộ lọc đã áp dụng từ URL: thiếu `status` nghĩa là "Chờ duyệt", `status=all` là "Tất cả". */
function readFiltersFromQuery(): void {
  const query = route.query
  const statusParam = firstQuery(query.status)
  workflowStatus.value =
    statusParam === 'all'
      ? ''
      : (workflowStatuses as string[]).includes(statusParam)
        ? (statusParam as ProductWorkflowStatus)
        : 'pending'
  search.value = firstQuery(query.q).slice(0, 150)
  const level = firstQuery(query.level)
  verificationLevel.value = (['A', 'B1', 'B2', 'C'] as string[]).includes(level) ? (level as VerificationLevel) : ''
  const verification = firstQuery(query.verification)
  verificationStatus.value = (
    ['verified_official_decision', 'verified_government_source', 'pending_verification'] as string[]
  ).includes(verification)
    ? (verification as ProductVerificationStatus)
    : ''
  const issue = firstQuery(query.issue)
  evidenceIssue.value = issue === 'missing_decision' || issue === 'missing_issued_at' ? issue : ''
  const expiry = firstQuery(query.expiry)
  expiryFilter.value = expiry === 'expired' || expiry === 'soon' ? expiry : ''
  // Lọc theo hạn chỉ có nghĩa với sản phẩm đã duyệt.
  if (expiryFilter.value) workflowStatus.value = 'approved'
  const pageParam = Number.parseInt(firstQuery(query.page), 10)
  page.value = Number.isFinite(pageParam) && pageParam > 1 ? pageParam : 1
  showAdvancedFilters.value = Boolean(
    verificationLevel.value || verificationStatus.value || evidenceIssue.value,
  )
}

function buildQuery(nextPage = 1): LocationQueryRaw {
  const query: LocationQueryRaw = {}
  if (activeTab.value === 'changes') query.tab = 'changes'
  if (workflowStatus.value === '') query.status = 'all'
  else if (workflowStatus.value !== 'pending') query.status = workflowStatus.value
  const keyword = search.value.trim()
  if (keyword) query.q = keyword
  if (verificationLevel.value) query.level = verificationLevel.value
  if (verificationStatus.value) query.verification = verificationStatus.value
  if (evidenceIssue.value) query.issue = evidenceIssue.value
  if (expiryFilter.value) query.expiry = expiryFilter.value
  if (nextPage > 1) query.page = String(nextPage)
  return query
}

function sameQuery(a: LocationQueryRaw, b: LocationQuery): boolean {
  const left = Object.entries(a).map(([key, value]) => [key, String(value)]).sort()
  const right = Object.entries(b).map(([key, value]) => [key, firstQuery(value)]).sort()
  return JSON.stringify(left) === JSON.stringify(right)
}

/** Ghi bộ lọc vào URL; URL đổi thì watcher bên dưới tải lại, không đổi thì tải lại thủ công. */
async function pushQuery(query: LocationQueryRaw): Promise<void> {
  if (sameQuery(query, route.query)) {
    readFiltersFromQuery()
    await loadData()
    return
  }
  await router.push({ query })
}

const filterKey = computed(() => {
  const { status, q, level, verification, issue, expiry, page: pageParam } = route.query
  return JSON.stringify([status, q, level, verification, issue, expiry, pageParam].map((value) => firstQuery(value)))
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

function isPendingOnlyFilter(filters: AdminProductFilters): boolean {
  return Object.keys(filters).every((key) => ['page', 'page_size', 'status'].includes(key)) && filters.status === 'pending'
}

function matchesExpiry(product: ManagedProduct): boolean {
  if (!product.cert_expires_at) return false
  const today = new Date(new Date().toDateString())
  const expires = new Date(product.cert_expires_at)
  if (expiryFilter.value === 'expired') return expires < today
  const limit = new Date(today)
  limit.setDate(limit.getDate() + EXPIRING_WINDOW_DAYS)
  return expires >= today && expires <= limit
}

/** Lấy lần lượt các trang sản phẩm đã duyệt (theo bộ lọc hiện có) rồi lọc theo hạn chứng nhận. */
async function listByExpiry(): Promise<{ items: ManagedProduct[]; total: number }> {
  const matched: ManagedProduct[] = []
  for (let current = 1; current <= EXPIRY_MAX_PAGES; current += 1) {
    const result = await listAdminProducts({ ...buildProductFilters(), page: current, page_size: EXPIRY_PAGE_SIZE })
    matched.push(...result.items.filter(matchesExpiry))
    if (current * EXPIRY_PAGE_SIZE >= result.total) break
  }
  matched.sort((a, b) => String(a.cert_expires_at).localeCompare(String(b.cert_expires_at)))
  return {
    items: matched.slice((page.value - 1) * pageSize, page.value * pageSize),
    total: matched.length,
  }
}

// Đếm lượt tải: chuyển trang/lọc nhanh thì chỉ kết quả của lượt mới nhất được hiển thị.
let loadSequence = 0

async function loadData(): Promise<void> {
  const sequence = ++loadSequence
  loading.value = true
  loadError.value = ''
  try {
    const filters = buildProductFilters()
    const pendingOnly = isPendingOnlyFilter(filters)
    const [productData, requestData, pendingTotal] = await Promise.all([
      expiryFilter.value ? listByExpiry() : listAdminProducts(filters),
      listProductChangeRequests('admin'),
      pendingOnly
        ? Promise.resolve<number | null>(null)
        : listAdminProducts({ status: 'pending', page: 1, page_size: 1 })
            .then((result) => result.total)
            .catch(() => null),
    ])
    if (sequence !== loadSequence) return
    products.value = productData.items
    productTotal.value = productData.total
    requests.value = requestData.items
    pendingProductTotal.value = pendingOnly ? productData.total : pendingTotal
    for (const product of productData.items) categoryNames.value.set(product.category.id, product.category.name)
  } catch (error) {
    if (sequence !== loadSequence) return
    loadError.value = getApiErrorMessage(error, 'Không thể tải dữ liệu quản lý sản phẩm.')
  } finally {
    if (sequence === loadSequence) loading.value = false
  }
}

async function applyFilters(): Promise<void> {
  successMessage.value = ''
  await pushQuery(buildQuery(1))
}

async function resetFilters(): Promise<void> {
  search.value = ''
  workflowStatus.value = 'pending'
  verificationLevel.value = ''
  verificationStatus.value = ''
  evidenceIssue.value = ''
  expiryFilter.value = ''
  showAdvancedFilters.value = false
  await pushQuery(buildQuery(1))
}

async function clearExpiryFilter(): Promise<void> {
  expiryFilter.value = ''
  workflowStatus.value = 'approved'
  await pushQuery(buildQuery(1))
}

async function changePage(nextPage: number): Promise<void> {
  if (nextPage < 1 || nextPage > totalPages.value || nextPage === page.value) return
  readFiltersFromQuery()
  await pushQuery(buildQuery(nextPage))
}

async function setTab(tab: 'products' | 'changes'): Promise<void> {
  if (tab === activeTab.value) return
  const query: LocationQueryRaw = { ...route.query }
  if (tab === 'changes') query.tab = 'changes'
  else delete query.tab
  await router.push({ query })
}

watch(filterKey, () => {
  readFiltersFromQuery()
  void loadData()
})

// ---------- Hộp thoại duyệt ----------
function showModerationError(message: string): void {
  moderationError.value = message
  void revealFlash('modal-error')
}

async function openProduct(product: ManagedProduct): Promise<void> {
  selectedRequest.value = null
  selectedProduct.value = product
  evidence.value = null
  evidenceError.value = ''
  moderationError.value = ''
  decision.value = 'approved'
  reviewNote.value = ''
  showExceptionalAction.value = false
  evidenceLoading.value = true
  try {
    const result = await getProductEvidence(product.id)
    // Đã mở sản phẩm khác trong lúc chờ thì bỏ kết quả cũ.
    if (selectedProduct.value?.id === product.id) evidence.value = result
  } catch (error) {
    if (selectedProduct.value?.id === product.id) {
      evidenceError.value = getApiErrorMessage(error, 'Không thể tải chứng cứ của sản phẩm.')
    }
  } finally {
    if (selectedProduct.value?.id === product.id || !selectedProduct.value) evidenceLoading.value = false
  }
}

function openRequest(request: ProductChangeRequest): void {
  selectedProduct.value = null
  selectedRequest.value = request
  evidence.value = null
  moderationError.value = ''
  decision.value = 'approved'
  reviewNote.value = ''
  void resolveCategoryNames(request)
}

function closeModal(force = false): void {
  if (submitting.value && !force) return
  selectedProduct.value = null
  selectedRequest.value = null
  evidence.value = null
  evidenceError.value = ''
  moderationError.value = ''
}

/** Đóng hộp thoại; nếu đã gõ phản hồi thì hỏi trước để không mất ghi chú (Esc, nút Hủy, nền). */
async function requestClose(): Promise<void> {
  if (submitting.value) return
  const canModerate = canModerateSelectedProduct.value || canModerateSelectedRequest.value
  if (canModerate && reviewNote.value.trim()) {
    const discard = await confirm.ask({
      title: 'Đóng và bỏ phản hồi đã nhập?',
      message: 'Nội dung phản hồi cho chủ thể chưa được gửi sẽ bị mất.',
      confirmLabel: 'Đóng và bỏ phản hồi',
      cancelLabel: 'Tiếp tục soạn',
      tone: 'danger',
    })
    if (!discard) return
  }
  closeModal()
}

useDialogFocus(isReviewDialogOpen, reviewDialog, () => void requestClose())

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
  if (submitting.value) return
  if (selectedProduct.value && !canModerateSelectedProduct.value) return
  if (selectedRequest.value && !canModerateSelectedRequest.value) return
  if ((decision.value === 'needs_revision' || decision.value === 'rejected') && !reviewNote.value.trim()) {
    showModerationError('Cần nhập nội dung phản hồi khi yêu cầu bổ sung hoặc từ chối.')
    return
  }
  moderationError.value = ''
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
  const confirmed = await confirm.ask({
    title: `Xác nhận ${actionLabel}?`,
    message: `Bạn sắp ${actionLabel} ${targetLabel}.`,
    confirmLabel: `Xác nhận ${actionLabel}`,
    tone: decision.value === 'rejected' ? 'danger' : 'primary',
  })
  if (!confirmed) return
  submitting.value = true
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
    showModerationError(getApiErrorMessage(error, 'Không thể xử lý yêu cầu kiểm duyệt.'))
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

// ---------- Bảng so sánh yêu cầu cập nhật ----------
const priceFormatter = new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND', maximumFractionDigits: 0 })

/** Tên nhóm sản phẩm lấy từ dữ liệu đã tải; chỉ gọi danh mục khi gặp mã chưa biết. */
async function resolveCategoryNames(request: ProductChangeRequest): Promise<void> {
  const ids = [request.current_data?.category_id, request.proposed_data?.category_id].filter(
    (id): id is number => typeof id === 'number',
  )
  if (ids.every((id) => categoryNames.value.has(id))) return
  try {
    const result = await getCategories()
    for (const category of result.items) categoryNames.value.set(category.id, category.name)
  } catch {
    // Không lấy được thì hiển thị "Nhóm số N", không chặn việc duyệt.
  }
}

function shortenUrl(value: string): string {
  try {
    const url = new URL(value)
    const file = decodeURIComponent(url.pathname.split('/').filter(Boolean).pop() ?? '')
    const text = file ? `${url.hostname.replace(/^www\./, '')} › ${file}` : url.hostname.replace(/^www\./, '')
    return text.length > 48 ? `${text.slice(0, 45)}…` : text
  } catch {
    return value.length > 48 ? `${value.slice(0, 45)}…` : value
  }
}

interface ComparisonCell {
  text: string
  href?: string
}

function rawValue(data: ProductWritePayload | ProductSnapshot | null, field: ComparableProductField): string {
  const value = data?.[field]
  return value === null || value === undefined ? '' : String(value)
}

function comparisonCell(data: ProductWritePayload | ProductSnapshot | null, field: ComparableProductField): ComparisonCell {
  const value = rawValue(data, field)
  if (!value) return { text: '—' }
  switch (field) {
    case 'category_id':
      return { text: categoryNames.value.get(Number(value)) ?? `Nhóm số ${value}` }
    case 'price': {
      const amount = Number(value)
      return { text: Number.isFinite(amount) ? priceFormatter.format(amount) : value }
    }
    case 'star':
      return { text: `${value} sao` }
    case 'cert_issued_at':
    case 'cert_expires_at':
      return { text: formatDate(value) }
    case 'certificate_url':
      return { text: shortenUrl(value), href: value }
    default:
      return { text: value }
  }
}

function fieldChanged(request: ProductChangeRequest, field: ComparableProductField): boolean {
  return rawValue(request.current_data, field) !== rawValue(request.proposed_data, field)
}

function workflowLabel(status: ProductWorkflowStatus): string {
  return {
    draft: 'Bản nháp',
    pending: 'Chờ duyệt',
    needs_revision: 'Cần bổ sung',
    approved: 'Đã duyệt',
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

onMounted(() => {
  readFiltersFromQuery()
  void loadData()
})
</script>

<template>
  <div class="admin-products-page">
    <header class="page-heading">
      <div>
        <span>Kiểm duyệt dữ liệu OCOP</span>
        <h1>Quản lý sản phẩm và chứng cứ</h1>
        <p>Quản trị viên đối chiếu nguồn công nhận, hồ sơ chứng nhận và quyết định trước khi công khai.</p>
      </div>
      <div v-if="pendingBadgeTotal !== null" class="summary-badge">{{ pendingBadgeTotal }} yêu cầu chờ xử lý</div>
    </header>

    <Transition name="ocop-rise">
      <div v-if="successMessage" class="alert alert-success" role="status" data-flash="success" tabindex="-1">{{ successMessage }}</div>
    </Transition>

    <nav class="tab-list" aria-label="Loại dữ liệu sản phẩm">
      <button
        :class="{ active: activeTab === 'products' }"
        type="button"
        :aria-current="activeTab === 'products' ? 'page' : undefined"
        @click="setTab('products')"
      >
        Sản phẩm <span>{{ productTotal }}</span>
      </button>
      <button
        :class="{ active: activeTab === 'changes' }"
        type="button"
        :aria-current="activeTab === 'changes' ? 'page' : undefined"
        @click="setTab('changes')"
      >
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
            <option value="approved">Đã duyệt</option>
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
      <p class="filter-hint">
        “Đã duyệt” gồm cả sản phẩm chưa đủ điều kiện hiển thị công khai (như chủ thể không còn hoạt động hoặc hồ sơ thiếu thông tin bắt buộc).
        Số sản phẩm đang công khai xem ở trang Tổng quan.
      </p>
      <p v-if="expiryFilter" class="active-filter">
        <span>Đang lọc: {{ expiryLabel }}, trong số sản phẩm đã duyệt</span>
        <button type="button" @click="clearExpiryFilter">Bỏ lọc này</button>
      </p>
    </form>

    <section class="queue-panel stagger-in">
      <StatusPanel v-if="loading" kind="loading" :rows="4" message="Đang tải dữ liệu sản phẩm…" />
      <StatusPanel v-else-if="loadError" kind="error" :message="loadError" @retry="loadData" />
      <template v-else-if="activeTab === 'products'">
        <StatusPanel v-if="!products.length" kind="empty" title="Không tìm thấy sản phẩm phù hợp bộ lọc" message="Thử bỏ bớt điều kiện lọc hoặc đổi trạng thái." />
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
        <StatusPanel v-if="!requests.length" kind="empty" title="Chưa có yêu cầu thay đổi sản phẩm" />
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

    <Transition name="ocop-fade">
    <div v-if="selectedProduct || selectedRequest" class="modal-backdrop" role="presentation" @click.self="requestClose()">
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
          <button type="button" aria-label="Đóng" @click="requestClose()"><AppIcon name="close" :size="17" /></button>
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
              <span>Dòng nền vàng, có nhãn “Đã đổi”, là dữ liệu chủ thể muốn thay đổi</span>
            </div>
            <div class="comparison-scroll">
              <table class="comparison-table">
                <caption class="visually-hidden">So sánh dữ liệu sản phẩm đang công khai với đề xuất của chủ thể</caption>
                <thead>
                  <tr>
                    <th scope="col">Trường dữ liệu</th>
                    <th scope="col">Đang công khai</th>
                    <th scope="col">Chủ thể đề xuất</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="field in comparisonFields"
                    :key="field.key"
                    :class="{ changed: fieldChanged(selectedRequest, field.key) }"
                  >
                    <th scope="row">
                      {{ field.label }}
                      <span v-if="fieldChanged(selectedRequest, field.key)" class="changed-tag">Đã đổi</span>
                    </th>
                    <td data-label="Đang công khai">
                      <a v-if="comparisonCell(selectedRequest.current_data, field.key).href" :href="comparisonCell(selectedRequest.current_data, field.key).href" target="_blank" rel="noopener">{{ comparisonCell(selectedRequest.current_data, field.key).text }}</a>
                      <template v-else>{{ comparisonCell(selectedRequest.current_data, field.key).text }}</template>
                    </td>
                    <td data-label="Chủ thể đề xuất">
                      <a v-if="comparisonCell(selectedRequest.proposed_data, field.key).href" :href="comparisonCell(selectedRequest.proposed_data, field.key).href" target="_blank" rel="noopener">{{ comparisonCell(selectedRequest.proposed_data, field.key).text }}</a>
                      <template v-else>{{ comparisonCell(selectedRequest.proposed_data, field.key).text }}</template>
                    </td>
                  </tr>
                </tbody>
              </table>
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
        <div v-if="moderationError" class="modal-error" role="alert" data-flash="modal-error" tabindex="-1">
          <AppIcon name="alert" :size="16" /> <span>{{ moderationError }}</span>
        </div>
        <footer>
          <button type="button" @click="requestClose()">{{ canModerateSelectedRequest || canModerateSelectedProduct ? 'Hủy' : 'Đóng' }}</button>
          <button v-if="canModerateSelectedRequest || canModerateSelectedProduct" class="submit-button" type="submit" :disabled="submitting">
            {{ submitting ? 'Đang xử lý...' : 'Xác nhận quyết định' }}
          </button>
        </footer>
      </form>
    </div>
    </Transition>

    <ConfirmDialog v-bind="confirm.props" @confirm="confirm.accept" @cancel="confirm.dismiss" />
  </div>
</template>

<style scoped>
/* ── Page layout ── */
.admin-products-page { display: grid; gap: var(--admin-space-5); font-family: var(--admin-font); }

/* ── Page heading ── */
.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-4); flex-wrap: wrap; }
.page-heading > div > span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em; }
.page-heading h1 { margin: 4px 0 4px; font-size: 1.625rem; font-weight: 800; color: var(--admin-text); }
.page-heading p { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.summary-badge { padding: 6px 14px; border-radius: var(--admin-radius-pill); background: var(--admin-primary-soft); color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; white-space: nowrap; }

/* ── Tabs ── */
.tab-list { display: flex; gap: 6px; }
.tab-list button {
  display: inline-flex;
  min-height: var(--admin-control-height);
  align-items: center;
  gap: 6px;
  padding: 9px 16px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-muted);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--admin-transition);
}
.tab-list button.active {
  border-color: var(--admin-primary);
  background: var(--admin-primary);
  color: var(--ocop-white);
}
.tab-list span {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  min-width: 20px;
  height: 20px;
  padding: 0 5px;
  border-radius: var(--admin-radius-pill);
  background: color-mix(in srgb, var(--ocop-white) 22%, transparent);
  font-size: 11px;
  font-weight: 800;
}
.tab-list button:not(.active) span { background: var(--admin-bg); color: var(--admin-muted); }

/* ── Filter panel ── */
.filter-panel {
  display: grid;
  padding: var(--admin-space-4);
  gap: var(--admin-space-3);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-sm);
}
.basic-filters { display: grid; grid-template-columns: minmax(240px, 2fr) minmax(160px, 1fr) auto; align-items: end; gap: 10px; }
.advanced-filters { display: grid; padding-top: var(--admin-space-3); grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 10px; border-top: 1px solid var(--admin-border-soft); }
.filter-panel label { display: grid; gap: 5px; color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; letter-spacing: 0.03em; }
.filter-panel input, .filter-panel select {
  width: 100%;
  height: var(--admin-control-height);
  padding: 0 10px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  transition: border-color var(--admin-transition);
}
.filter-panel input:focus, .filter-panel select:focus { border-color: var(--admin-primary-dark); }
.filter-hint { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-xs); line-height: 1.5; }
.active-filter { display: flex; flex-wrap: wrap; align-items: center; gap: var(--admin-space-2); margin: 0; padding: var(--admin-space-2) var(--admin-space-3); border-radius: var(--admin-radius-md); background: var(--admin-info-soft); color: var(--admin-info-text); font-size: var(--admin-font-sm); font-weight: 600; }
.active-filter button { min-height: 44px; padding: 0 var(--admin-space-3); border: 1px solid var(--admin-info-border); border-radius: var(--admin-radius-sm); background: var(--admin-card); color: var(--admin-info-text); font-size: var(--admin-font-sm); font-weight: 700; cursor: pointer; }
.filter-actions { display: flex; flex-wrap: wrap; gap: 7px; align-items: flex-end; }
.filter-actions button {
  min-height: var(--admin-control-height);
  padding: 0 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-muted);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  cursor: pointer;
  transition: all var(--admin-transition);
}
.filter-actions button:hover { border-color: var(--admin-primary); color: var(--admin-primary); }
.filter-actions .primary-button {
  border-color: var(--admin-primary);
  background: var(--admin-primary);
  color: var(--ocop-white);
}
.filter-actions .primary-button:hover { background: var(--admin-primary-dark); }

/* ── Alert ── */
.alert {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--admin-space-3);
  padding: var(--admin-space-3) var(--admin-space-4);
  border-radius: var(--admin-radius-md);
  font-size: var(--admin-font-sm);
  font-weight: 500;
}
.alert-danger { background: var(--admin-danger-soft); color: var(--admin-danger-text); border: 1px solid var(--admin-danger-border); }
.alert-success { background: var(--admin-success-soft); color: var(--admin-success-text); border: 1px solid var(--admin-success-border); }

/* ── Queue panel ── */
.queue-panel {
  overflow: hidden;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-sm);
}
.product-summary { display: grid; gap: 3px; min-width: 0; }
.product-summary h2 { margin: 2px 0 0; font-size: var(--admin-font-base); font-weight: 700; color: var(--admin-text); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.product-summary p { margin: 0; font-size: var(--admin-font-sm); color: var(--admin-muted); overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.queue-panel article {
  display: grid;
  padding: 14px 20px;
  align-items: center;
  grid-template-columns: 72px minmax(0, 1fr) auto;
  gap: 14px;
  border-bottom: 1px solid var(--admin-border-soft);
  transition: background var(--admin-transition);
}
.queue-panel article:last-child { border-bottom: 0; }
.queue-panel article:hover { background: var(--admin-bg); }
.queue-panel article > img { width: 72px; height: 64px; border-radius: var(--admin-radius-sm); object-fit: cover; }
.request-symbol {
  display: grid;
  width: 48px;
  height: 48px;
  place-items: center;
  border-radius: var(--admin-radius-md);
  background: var(--admin-primary-soft);
  color: var(--admin-primary);
  font-size: 22px;
}
.queue-panel small { color: var(--admin-muted); font-size: var(--admin-font-xs); }
.queue-panel h2 { margin: 4px 0 3px; font-size: var(--admin-font-base); font-weight: 700; color: var(--admin-text); }
.queue-panel p { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.queue-panel > button, .queue-panel button, .review-modal button {
  min-height: 44px;
  padding: 8px 14px;
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  cursor: pointer;
  white-space: nowrap;
  transition: all var(--admin-transition);
}
.queue-panel button:hover { border-color: var(--admin-primary); color: var(--admin-primary); }

/* ── Pagination ── */
.pagination-bar {
  display: flex;
  padding: 12px 20px;
  align-items: center;
  justify-content: space-between;
  gap: var(--admin-space-3);
  border-top: 1px solid var(--admin-border-soft);
  background: var(--admin-bg);
}
.pagination-bar span { color: var(--admin-muted); font-size: var(--admin-font-sm); font-weight: 600; }
.pagination-bar div { display: flex; gap: 7px; }
.pagination-bar button:disabled { cursor: not-allowed; opacity: 0.4; }

/* ── Status chips (badge pill) ── */
.status-row { display: flex; margin-top: var(--admin-space-2); flex-wrap: wrap; gap: 5px; }
.status-chip, .issue-chip, .level-chip {
  display: inline-flex;
  align-items: center;
  padding: 3px 9px;
  border-radius: var(--admin-radius-pill);
  font-size: var(--admin-font-xs);
  font-weight: 700;
}
.status-chip { background: var(--admin-badge-draft-bg); color: var(--admin-badge-draft-text); }
.status-chip[data-status="pending"] { background: var(--admin-badge-pending-bg); color: var(--admin-badge-pending-text); }
.status-chip[data-status="approved"] { background: var(--admin-badge-approved-bg); color: var(--admin-badge-approved-text); }
.status-chip[data-status="rejected"], .status-chip[data-status="suspended"] { background: var(--admin-badge-rejected-bg); color: var(--admin-badge-rejected-text); }
.status-chip[data-status="needs_revision"] { background: var(--admin-badge-revision-bg); color: var(--admin-badge-revision-text); }
.status-chip[data-status="cancelled"], .status-chip[data-status="archived"] { background: var(--admin-badge-draft-bg); color: var(--admin-badge-draft-text); }
.status-chip.verification { background: var(--admin-info-soft); color: var(--admin-info-text); }
.issue-chip { background: var(--admin-warning-soft); color: var(--admin-warning-text); }
.level-chip { background: var(--admin-primary-soft); color: var(--admin-primary); }

/* ── Empty ── */

/* ══════════ MODAL ══════════ */
.modal-backdrop {
  position: fixed;
  z-index: 80;
  inset: 0;
  display: grid;
  padding: var(--admin-space-5);
  place-items: center;
  overflow-y: auto;
  background: var(--admin-scrim);
  backdrop-filter: blur(4px);
}
.review-modal {
  width: min(100%, 820px);
  max-height: calc(100vh - 40px);
  padding: var(--admin-space-6);
  overflow-y: auto;
  border-radius: var(--admin-radius-lg);
  background: var(--admin-card);
  box-shadow: var(--admin-shadow-modal);
}

/* Modal header */
.review-modal > header, .section-heading {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--admin-space-3);
  padding-bottom: var(--admin-space-4);
  border-bottom: 1px solid var(--admin-border-soft);
  margin-bottom: var(--admin-space-4);
}
.review-modal header > div > span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em; }
.review-modal header h2 { margin: 3px 0 0; font-size: var(--admin-font-2xl); color: var(--admin-text); }
.review-modal header > button { border: 0 !important; background: var(--admin-bg); color: var(--admin-muted); border-radius: var(--admin-radius-sm); width: 44px; height: 44px; display: grid; place-items: center; flex-shrink: 0; }
.review-modal header > button:hover { color: var(--admin-danger); background: var(--admin-danger-soft); }

/* Sections inside modal */
.subject-box, .review-grid, .evidence-overview {
  display: grid;
  margin-top: var(--admin-space-4);
  padding: var(--admin-space-4);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--admin-space-3);
  border-radius: var(--admin-radius-md);
  background: var(--admin-bg);
}
.subject-box div, .review-grid div, .evidence-overview div { display: grid; gap: 3px; }
.subject-box small, .review-grid small, .evidence-overview small { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; text-transform: uppercase; letter-spacing: 0.04em; }
.subject-box strong, .review-grid strong, .evidence-overview strong { font-size: var(--admin-font-sm); overflow-wrap: anywhere; color: var(--admin-text); }
.review-grid .wide { grid-column: 1 / -1; }

.last-review-box {
  display: grid;
  margin-top: var(--admin-space-3);
  padding: var(--admin-space-3) var(--admin-space-4);
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: var(--admin-space-3);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-md);
  background: var(--admin-bg);
}
.last-review-box div { display: grid; gap: 3px; }
.last-review-box small { color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; text-transform: uppercase; }
.last-review-box strong { font-size: var(--admin-font-sm); color: var(--admin-text); }
.last-review-box p { grid-column: 1 / -1; margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }

.document-links { display: flex; margin-top: var(--admin-space-3); gap: var(--admin-space-2); flex-wrap: wrap; }
.document-links a, .document-links button { padding: 8px 12px; border-radius: var(--admin-radius-sm); background: var(--admin-info-soft); color: var(--admin-info-text); font-size: var(--admin-font-sm); font-weight: 700; text-decoration: none; border: 0; cursor: pointer; }
.document-links a:hover, .document-links button:hover { background: var(--admin-info-soft); }

.review-warnings { margin-top: var(--admin-space-3); padding: var(--admin-space-3) var(--admin-space-4); border: 1px solid var(--admin-warning-border); border-radius: var(--admin-radius-md); background: var(--admin-warning-soft); color: var(--admin-warning-text); font-size: var(--admin-font-sm); }
.review-warnings ul { margin: 6px 0 0; padding-left: 18px; }
.workflow-guide { margin: var(--admin-space-4) 0 0; padding: var(--admin-space-3) var(--admin-space-4); border: 1px solid var(--admin-info-soft); border-radius: var(--admin-radius-md); background: var(--admin-info-soft); color: var(--admin-info-text); font-size: var(--admin-font-sm); line-height: 1.55; }

.evidence-disclosure { margin-top: var(--admin-space-4); border: 1px solid var(--admin-border); border-radius: var(--admin-radius-md); background: var(--admin-card); }
.evidence-disclosure summary { display: flex; padding: var(--admin-space-3) var(--admin-space-4); align-items: center; justify-content: space-between; gap: var(--admin-space-3); cursor: pointer; color: var(--admin-text); font-size: var(--admin-font-sm); font-weight: 700; }
.evidence-disclosure summary small { color: var(--admin-muted); font-size: var(--admin-font-sm); font-weight: 500; }
.evidence-content { padding: 0 var(--admin-space-4) var(--admin-space-4); }
.evidence-content :deep(.evidence-section) { margin-top: 0; border-top: 0; padding-top: 6px; }
.evidence-section { display: grid; margin-top: var(--admin-space-5); gap: 11px; border-top: 1px solid var(--admin-border); padding-top: var(--admin-space-4); }
.evidence-section h3 { margin: 3px 0 0; font-size: var(--admin-font-xl); color: var(--admin-text); }
.evidence-overview { margin-top: 0; grid-template-columns: 1fr 2fr; }
.evidence-card { padding: var(--admin-space-3); border: 1px solid var(--admin-border); border-radius: var(--admin-radius-sm); }
.evidence-card > div { display: flex; align-items: center; gap: var(--admin-space-2); }
.evidence-card h4 { margin: 8px 0 4px; font-size: var(--admin-font-sm); font-weight: 700; color: var(--admin-text); }
.evidence-card p { margin: 3px 0; color: var(--admin-muted); font-size: var(--admin-font-xs); }
.evidence-card a { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 700; text-decoration: none; }
.evidence-message { padding: var(--admin-space-4); border-radius: var(--admin-radius-sm); background: var(--admin-bg); color: var(--admin-muted); font-size: var(--admin-font-sm); text-align: center; }
.evidence-message.error { background: var(--admin-danger-soft); color: var(--admin-danger-text); }
.issue-list { display: flex; flex-wrap: wrap; gap: 6px; }
.issue-list span { padding: 5px 10px; border-radius: var(--admin-radius-sm); background: var(--admin-warning-soft); color: var(--admin-warning-text); font-size: var(--admin-font-xs); font-weight: 700; }
.reason-box { padding: var(--admin-space-3); border-radius: var(--admin-radius-sm); background: var(--admin-warning-soft); color: var(--admin-warning-text); font-size: var(--admin-font-sm); }
.warning-box { padding: var(--admin-space-3); border-radius: var(--admin-radius-sm); background: var(--admin-danger-soft); color: var(--admin-danger-text); font-size: var(--admin-font-sm); }

/* Comparison */
.comparison-section { display: grid; margin-top: var(--admin-space-4); gap: var(--admin-space-3); }
.comparison-heading { display: flex; align-items: center; justify-content: space-between; gap: var(--admin-space-3); }
.comparison-heading strong { font-size: var(--admin-font-sm); font-weight: 700; color: var(--admin-text); }
.comparison-heading span { color: var(--admin-muted); font-size: var(--admin-font-sm); }
.comparison-scroll { overflow-x: auto; border: 1px solid var(--admin-border); border-radius: var(--admin-radius-md); }
.comparison-table { width: 100%; border-collapse: collapse; font-size: var(--admin-font-sm); }
.comparison-table th, .comparison-table td { padding: 9px 14px; border-bottom: 1px solid var(--admin-border-soft); text-align: left; vertical-align: top; overflow-wrap: anywhere; color: var(--admin-text); }
.comparison-table tbody tr:last-child th, .comparison-table tbody tr:last-child td { border-bottom: 0; }
.comparison-table thead th { background: var(--admin-bg); color: var(--admin-muted); font-weight: 700; font-size: var(--admin-font-xs); text-transform: uppercase; letter-spacing: 0.04em; }
.comparison-table tbody th { width: 160px; font-weight: 700; }
.comparison-table td a { color: var(--admin-primary-dark); font-weight: 600; text-decoration: underline; text-underline-offset: 2px; }
.comparison-table tr.changed th, .comparison-table tr.changed td { background: var(--admin-highlight); }
.comparison-table tr.changed th { color: var(--admin-warning-text); }
.changed-tag { display: inline-block; margin-left: 6px; padding: 1px 8px; border-radius: var(--admin-radius-pill); background: var(--admin-warning-soft); color: var(--admin-warning-text); font-size: var(--admin-font-xs); font-weight: 800; }

/* Decision box */
.decision-box { display: grid; margin-top: var(--admin-space-4); gap: var(--admin-space-3); }
.decision-options { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--admin-space-2); }
.decision-options button { padding: 11px var(--admin-space-3); }
.decision-options button.active { border-color: var(--admin-primary); background: var(--admin-primary-soft); color: var(--admin-primary); }
.exception-toggle { justify-self: start; border: 0 !important; color: var(--admin-muted) !important; text-decoration: underline; font-size: var(--admin-font-sm) !important; }
.reject-option { justify-self: start; border-color: var(--admin-danger-border) !important; color: var(--admin-danger-text) !important; }
.reject-option.active { background: var(--admin-danger-soft) !important; }
.decision-box label { display: grid; gap: 5px; color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; }
.decision-box select, .decision-box textarea { padding: 9px 12px; border: 1px solid var(--admin-border); border-radius: var(--admin-radius-sm); font-size: var(--admin-font-sm); color: var(--admin-text); }
.decision-box textarea { resize: vertical; }
.modal-error { display: flex; align-items: flex-start; gap: var(--admin-space-2); margin-top: var(--admin-space-4); padding: var(--admin-space-3) var(--admin-space-4); border: 1px solid var(--admin-danger-border); border-radius: var(--admin-radius-md); background: var(--admin-danger-soft); color: var(--admin-danger-text); font-size: var(--admin-font-sm); font-weight: 600; }
.review-modal footer { display: flex; margin-top: var(--admin-space-4); justify-content: flex-end; gap: var(--admin-space-2); padding-top: var(--admin-space-4); border-top: 1px solid var(--admin-border-soft); }
.review-modal .submit-button { border-color: var(--admin-primary) !important; background: var(--admin-primary) !important; color: var(--ocop-white) !important; }
.review-modal .submit-button:hover { background: var(--admin-primary-dark) !important; }

/* ── Responsive ── */
@media (max-width: 1180px) { .basic-filters { grid-template-columns: repeat(2, minmax(0, 1fr)); } .filter-actions { grid-column: 1 / -1; } }
@media (max-width: 640px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
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
  .evidence-disclosure summary { align-items: flex-start; flex-direction: column; }
  .comparison-heading { align-items: flex-start; flex-direction: column; }
  .comparison-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip-path: inset(50%); white-space: nowrap; }
  .comparison-table, .comparison-table tbody, .comparison-table tr, .comparison-table th, .comparison-table td { display: block; width: 100%; }
  .comparison-table tbody th { width: 100%; padding-bottom: 2px; border-bottom: 0; }
  .comparison-table td { padding-top: 2px; padding-bottom: 6px; }
  .comparison-table td::before { content: attr(data-label) ': '; color: var(--admin-muted); font-weight: 700; }
  .comparison-table tbody tr { border-bottom: 1px solid var(--admin-border-soft); }
  .decision-options { grid-template-columns: 1fr; }
}
</style>
