<script setup lang="ts">
import { reactive, ref } from 'vue'

import { getApiErrorMessage } from '@/services/api-error'
import {
  createDataSource,
  getProductEvidence,
  linkProductEvidence,
  listDataSources,
  unlinkProductEvidence,
  updateDataSource,
  updateProductEvidenceLink,
} from '@/services/product-management'
import type {
  DataSourceType,
  DataSourceWritePayload,
  EvidenceRole,
  ProductDataSource,
  ProductEvidenceIssue,
  ProductEvidenceLinkPayload,
  ProductEvidenceResponse,
  ProductEvidenceSource,
  ProductVerificationStatus,
  VerificationLevel,
} from '@/types/product-management'

const props = defineProps<{
  productId: number
  evidence: ProductEvidenceResponse
}>()

const emit = defineEmits<{
  updated: [evidence: ProductEvidenceResponse]
}>()

const catalog = ref<ProductDataSource[]>([])
const panel = ref<'link' | 'source' | ''>('')
const editingSourceId = ref<number | null>(null)
const editingLink = ref<ProductEvidenceSource | null>(null)
const loadingCatalog = ref(false)
const saving = ref(false)
const actionError = ref('')
const actionSuccess = ref('')

const today = new Date().toISOString().slice(0, 10)
const sourceForm = reactive<DataSourceWritePayload>({
  title: '',
  document_number: null,
  issuing_body: null,
  source_type: 'recognition_decision',
  published_at: null,
  source_url: '',
  retrieved_at: today,
})
const linkForm = reactive<ProductEvidenceLinkPayload>({
  source_id: 0,
  evidence_role: 'recognition',
  verification_level: 'A',
  original_address: null,
  verified_at: today,
  notes: null,
})

const sourceTypeLabels: Record<DataSourceType, string> = {
  legal_document: 'Văn bản pháp lý',
  recognition_decision: 'Quyết định công nhận',
  government_portal: 'Cổng cơ quan nhà nước',
  government_news: 'Báo/cổng thông tin nhà nước',
  subject_website: 'Website chủ thể',
  academic_reference: 'Tài liệu tham khảo',
  other: 'Nguồn khác',
}

const evidenceRoleLabels: Record<EvidenceRole, string> = {
  recognition: 'Công nhận sản phẩm',
  identity: 'Xác nhận tên/chủ thể',
  address: 'Xác nhận địa chỉ',
  enrichment: 'Bổ sung mô tả',
}

function verificationLabel(status: ProductVerificationStatus): string {
  return {
    verified_official_decision: 'Đã đối chiếu quyết định',
    verified_government_source: 'Đã có nguồn cơ quan nhà nước',
    pending_verification: 'Chờ xác minh nguồn',
  }[status]
}

function issueLabel(issue: ProductEvidenceIssue): string {
  return {
    no_recognition_source: 'Chưa có nguồn công nhận',
    missing_decision: 'Thiếu số quyết định',
    missing_issued_at: 'Thiếu ngày cấp',
    missing_expires_at: 'Thiếu ngày hết hạn',
  }[issue]
}

function resetMessages(): void {
  actionError.value = ''
  actionSuccess.value = ''
}

async function loadCatalog(): Promise<void> {
  loadingCatalog.value = true
  try {
    catalog.value = (await listDataSources()).items
    if (!linkForm.source_id && catalog.value[0]) linkForm.source_id = catalog.value[0].id
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không thể tải danh mục nguồn dữ liệu.')
  } finally {
    loadingCatalog.value = false
  }
}

async function openLinkForm(): Promise<void> {
  resetMessages()
  panel.value = 'link'
  editingLink.value = null
  Object.assign(linkForm, {
    source_id: 0,
    evidence_role: 'recognition' as EvidenceRole,
    verification_level: 'A' as VerificationLevel,
    original_address: null,
    verified_at: today,
    notes: null,
  })
  await loadCatalog()
}

function openLinkEdit(link: ProductEvidenceSource): void {
  resetMessages()
  editingLink.value = link
  panel.value = 'link'
  Object.assign(linkForm, {
    source_id: link.source.id,
    evidence_role: link.evidence_role,
    verification_level: link.verification_level,
    original_address: link.original_address,
    verified_at: link.verified_at,
    notes: link.notes,
  })
}

function resetSourceForm(): void {
  Object.assign(sourceForm, {
    title: '',
    document_number: null,
    issuing_body: null,
    source_type: 'recognition_decision' as DataSourceType,
    published_at: null,
    source_url: '',
    retrieved_at: today,
  })
}

function openSourceCreate(): void {
  resetMessages()
  resetSourceForm()
  editingSourceId.value = null
  panel.value = 'source'
}

function openSourceEdit(source: ProductDataSource): void {
  resetMessages()
  editingSourceId.value = source.id
  Object.assign(sourceForm, {
    title: source.title,
    document_number: source.document_number,
    issuing_body: source.issuing_body,
    source_type: source.source_type as DataSourceType,
    published_at: source.published_at,
    source_url: source.source_url,
    retrieved_at: source.retrieved_at,
  })
  panel.value = 'source'
}

async function refreshEvidence(message: string): Promise<void> {
  emit('updated', await getProductEvidence(props.productId))
  actionSuccess.value = message
}

async function saveSource(): Promise<void> {
  saving.value = true
  resetMessages()
  try {
    const payload: DataSourceWritePayload = {
      ...sourceForm,
      document_number: sourceForm.document_number || null,
      issuing_body: sourceForm.issuing_body || null,
      published_at: sourceForm.published_at || null,
    }
    if (editingSourceId.value) {
      await updateDataSource(editingSourceId.value, payload)
      await refreshEvidence('Đã cập nhật thông tin nguồn.')
    } else {
      const source = await createDataSource(payload)
      catalog.value.unshift(source)
      linkForm.source_id = source.id
      panel.value = 'link'
      actionSuccess.value = 'Đã tạo nguồn. Hãy xác nhận thông tin liên kết với sản phẩm.'
      return
    }
    panel.value = ''
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không thể lưu nguồn dữ liệu.')
  } finally {
    saving.value = false
  }
}

async function saveLink(): Promise<void> {
  if (!linkForm.source_id) {
    actionError.value = 'Vui lòng chọn một nguồn dữ liệu.'
    return
  }
  saving.value = true
  resetMessages()
  try {
    const nextEvidence = editingLink.value
      ? await updateProductEvidenceLink(
          props.productId,
          editingLink.value.source.id,
          editingLink.value.evidence_role,
          {
            verification_level: linkForm.verification_level,
            original_address: linkForm.original_address || null,
            verified_at: linkForm.verified_at,
            notes: linkForm.notes || null,
          },
        )
      : await linkProductEvidence(props.productId, {
          ...linkForm,
          original_address: linkForm.original_address || null,
          notes: linkForm.notes || null,
        })
    emit('updated', nextEvidence)
    panel.value = ''
    actionSuccess.value = editingLink.value ? 'Đã cập nhật liên kết chứng cứ.' : 'Đã liên kết nguồn với sản phẩm.'
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không thể lưu liên kết chứng cứ.')
  } finally {
    saving.value = false
  }
}

async function removeLink(link: ProductEvidenceSource): Promise<void> {
  if (!window.confirm(`Gỡ nguồn “${link.source.title}” khỏi sản phẩm?`)) return
  saving.value = true
  resetMessages()
  try {
    await unlinkProductEvidence(props.productId, link.source.id, link.evidence_role)
    await refreshEvidence('Đã gỡ liên kết chứng cứ.')
  } catch (error) {
    actionError.value = getApiErrorMessage(error, 'Không thể gỡ liên kết chứng cứ.')
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <section class="evidence-manager">
    <header>
      <div>
        <small>Đối chiếu nguồn</small>
        <h3>Chứng cứ dữ liệu</h3>
      </div>
      <div class="header-actions">
        <span class="count-chip">{{ evidence.evidence_count }} nguồn</span>
        <button type="button" @click="openSourceCreate">Tạo nguồn</button>
        <button class="primary-action" type="button" @click="openLinkForm">+ Liên kết nguồn</button>
      </div>
    </header>

    <div v-if="actionError" class="action-message error" role="alert">{{ actionError }}</div>
    <div v-if="actionSuccess" class="action-message success" role="status">{{ actionSuccess }}</div>

    <div class="evidence-overview">
      <div><small>Cấp nguồn cao nhất</small><strong>{{ evidence.verification_level || 'Chưa xếp cấp' }}</strong></div>
      <div><small>Trạng thái xác minh</small><strong>{{ verificationLabel(evidence.verification_status) }}</strong></div>
    </div>
    <div v-if="evidence.issues.length" class="issue-list">
      <span v-for="issue in evidence.issues" :key="issue">{{ issueLabel(issue) }}</span>
    </div>

    <form v-if="panel === 'source'" class="manager-form" @submit.prevent="saveSource">
      <div class="form-heading">
        <strong>{{ editingSourceId ? 'Sửa nguồn dữ liệu' : 'Tạo nguồn dữ liệu' }}</strong>
        <button type="button" @click="panel = ''">Đóng</button>
      </div>
      <div class="form-grid">
        <label class="wide">Tên tài liệu *<input v-model.trim="sourceForm.title" required minlength="3" /></label>
        <label>Loại nguồn *
          <select v-model="sourceForm.source_type" required>
            <option v-for="(label, value) in sourceTypeLabels" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>Số văn bản<input v-model.trim="sourceForm.document_number" placeholder="3981/QĐ-UBND" /></label>
        <label>Cơ quan ban hành<input v-model.trim="sourceForm.issuing_body" /></label>
        <label>Ngày công bố<input v-model="sourceForm.published_at" type="date" /></label>
        <label class="wide">Đường dẫn nguồn *<input v-model.trim="sourceForm.source_url" type="url" required placeholder="https://..." /></label>
        <label>Ngày truy cập *<input v-model="sourceForm.retrieved_at" type="date" required /></label>
      </div>
      <footer><button class="save-button" type="submit" :disabled="saving">{{ saving ? 'Đang lưu...' : 'Lưu nguồn' }}</button></footer>
    </form>

    <form v-if="panel === 'link'" class="manager-form" @submit.prevent="saveLink">
      <div class="form-heading">
        <strong>{{ editingLink ? 'Sửa liên kết chứng cứ' : 'Liên kết nguồn với sản phẩm' }}</strong>
        <button type="button" @click="panel = ''">Đóng</button>
      </div>
      <p v-if="loadingCatalog">Đang tải danh mục nguồn...</p>
      <div class="form-grid">
        <label class="wide">Nguồn dữ liệu *
          <select v-model.number="linkForm.source_id" required :disabled="Boolean(editingLink)">
            <option :value="0" disabled>Chọn nguồn</option>
            <option v-for="source in catalog" :key="source.id" :value="source.id">{{ source.document_number || 'Không số' }} — {{ source.title }}</option>
          </select>
        </label>
        <label>Vai trò chứng cứ *
          <select v-model="linkForm.evidence_role" required :disabled="Boolean(editingLink)">
            <option v-for="(label, value) in evidenceRoleLabels" :key="value" :value="value">{{ label }}</option>
          </select>
        </label>
        <label>Cấp tin cậy *
          <select v-model="linkForm.verification_level" required>
            <option value="A">A — Quyết định chính thức</option>
            <option value="B1">B1 — Cơ quan nhà nước</option>
            <option value="B2">B2 — Đề xuất/chấm điểm</option>
            <option value="C">C — Nguồn chủ thể</option>
          </select>
        </label>
        <label>Ngày xác minh *<input v-model="linkForm.verified_at" type="date" required /></label>
        <label class="wide">Địa chỉ gốc<textarea v-model="linkForm.original_address" rows="2" /></label>
        <label class="wide">Ghi chú<textarea v-model="linkForm.notes" rows="2" /></label>
      </div>
      <footer><button class="save-button" type="submit" :disabled="saving || loadingCatalog">{{ saving ? 'Đang lưu...' : 'Lưu liên kết' }}</button></footer>
    </form>

    <p v-if="!evidence.sources.length" class="empty-message">Sản phẩm chưa được liên kết với nguồn chứng cứ.</p>
    <article v-for="link in evidence.sources" v-else :key="`${link.source.id}-${link.evidence_role}`" class="evidence-card">
      <div class="card-meta">
        <span class="count-chip">Nguồn {{ link.verification_level }}</span>
        <small>{{ evidenceRoleLabels[link.evidence_role] }}</small>
      </div>
      <h4>{{ link.source.title }}</h4>
      <p>{{ link.source.document_number || 'Chưa có số văn bản' }} · {{ link.source.issuing_body || 'Chưa rõ cơ quan ban hành' }}</p>
      <p v-if="link.notes" class="source-note">{{ link.notes }}</p>
      <div class="card-actions">
        <a :href="link.source.source_url" target="_blank" rel="noopener">Xem nguồn gốc ↗</a>
        <button type="button" @click="openSourceEdit(link.source)">Sửa nguồn</button>
        <button type="button" @click="openLinkEdit(link)">Sửa liên kết</button>
        <button class="danger" type="button" :disabled="saving" @click="removeLink(link)">Gỡ</button>
      </div>
    </article>
  </section>
</template>

<style scoped>
.evidence-manager { display: grid; margin-top: 22px; padding-top: 18px; gap: 11px; border-top: 1px solid var(--ocop-border); }
.evidence-manager > header, .header-actions, .form-heading, .card-meta, .card-actions { display: flex; align-items: center; gap: var(--ocop-space-2); }
.evidence-manager > header, .form-heading { justify-content: space-between; }
.evidence-manager header small { color: var(--ocop-primary-700); font-size: var(--ocop-font-size-2xs); font-weight: 800; text-transform: uppercase; }
.evidence-manager h3 { margin: 3px 0 0; font-size: 17px; }
.evidence-manager button { padding: 7px 9px; border: 1px solid var(--ocop-border); border-radius: 7px; background: var(--ocop-card); font-size: var(--ocop-font-size-2xs); font-weight: 700; }
.evidence-manager .primary-action, .evidence-manager .save-button { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: var(--ocop-white); }
.count-chip { padding: 5px var(--ocop-space-2); border-radius: var(--ocop-radius-pill); background: var(--ocop-mint-soft); color: var(--ocop-primary-700); font-size: 9px; font-weight: 800; white-space: nowrap; }
.action-message { padding: 9px 11px; border-radius: var(--ocop-radius-sm); font-size: var(--ocop-font-size-2xs); }
.action-message.error { background: var(--ocop-danger-soft); color: var(--ocop-danger-strong); }
.action-message.success { background: var(--ocop-success-soft); color: var(--ocop-primary-700); }
.evidence-overview { display: grid; padding: 13px; grid-template-columns: 1fr 2fr; gap: var(--ocop-space-3); border-radius: 10px; background: var(--ocop-surface-subtle); }
.evidence-overview div { display: grid; gap: 3px; }
.evidence-overview small { color: var(--ocop-slate); font-size: 9px; font-weight: 700; text-transform: uppercase; }
.evidence-overview strong { font-size: var(--ocop-font-size-caption); }
.issue-list { display: flex; flex-wrap: wrap; gap: 6px; }
.issue-list span { padding: 6px var(--ocop-space-2); border-radius: 7px; background: var(--ocop-notice-soft); color: var(--ocop-notice); font-size: var(--ocop-font-size-2xs); font-weight: 700; }
.manager-form { display: grid; padding: 14px; gap: var(--ocop-space-3); border: 1px solid var(--ocop-mint-border); border-radius: 11px; background: var(--ocop-mint-soft); }
.manager-form .form-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 10px; }
.manager-form label { display: grid; gap: var(--ocop-space-1); color: var(--ocop-neutral-600); font-size: var(--ocop-font-size-2xs); font-weight: 700; }
.manager-form .wide { grid-column: 1 / -1; }
.manager-form input, .manager-form select, .manager-form textarea { width: 100%; padding: var(--ocop-space-2); border: 1px solid var(--ocop-border); border-radius: 7px; background: var(--ocop-card); font-size: var(--ocop-font-size-xs); }
.manager-form textarea { resize: vertical; }
.manager-form footer { display: flex; justify-content: flex-end; }
.empty-message { padding: 14px; border-radius: var(--ocop-radius-sm); background: var(--ocop-surface-subtle); color: var(--ocop-slate); font-size: var(--ocop-font-size-xs); text-align: center; }
.evidence-card { padding: var(--ocop-space-3); border: 1px solid var(--ocop-border); border-radius: 10px; }
.evidence-card h4 { margin: 9px 0 var(--ocop-space-1); font-size: var(--ocop-font-size-small); }
.evidence-card p { margin: 3px 0; color: var(--ocop-slate); font-size: var(--ocop-font-size-2xs); }
.evidence-card .source-note { color: var(--ocop-notice-deep); }
.card-actions { margin-top: 10px; flex-wrap: wrap; }
.card-actions a { margin-right: auto; color: var(--ocop-info-strong); font-size: var(--ocop-font-size-2xs); font-weight: 700; text-decoration: none; }
.card-actions .danger { border-color: var(--ocop-danger-border); color: var(--ocop-danger-strong); }
@media (max-width: 640px) {
  .evidence-manager > header { align-items: flex-start; flex-direction: column; }
  .header-actions { width: 100%; flex-wrap: wrap; }
  .evidence-overview, .manager-form .form-grid { grid-template-columns: 1fr; }
  .manager-form .wide { grid-column: auto; }
}
</style>
