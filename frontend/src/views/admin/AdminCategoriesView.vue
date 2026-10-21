<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'
import StatusPanel from '@/components/ui/StatusPanel.vue'
import { useDialogFocus } from '@/composables/useDialogFocus'
import {
  createAdminCategory,
  deleteAdminCategory,
  listAdminCategories,
  updateAdminCategory,
} from '@/services/admin-categories'
import { getApiErrorMessage } from '@/services/api-error'
import type { AdminCategory, AdminCategoryPayload } from '@/types/category'
import { categoryTheme } from '@/utils/category'

const categories = ref<AdminCategory[]>([])
const isLoading = ref(true)
const errorMessage = ref('')
const statusMessage = ref('')
const togglingId = ref<number | null>(null)
const rowError = ref<{ id: number; message: string } | null>(null)

// Hộp thoại thêm/sửa
const editing = ref<AdminCategory | null>(null)
const isFormOpen = ref(false)
const isSaving = ref(false)
const formError = ref('')
const formDialog = ref<HTMLElement | null>(null)
const form = reactive({
  name: '',
  slug: '',
  description: '',
  icon: '',
  is_visible: true,
  sort_order: 0,
})

// Hộp thoại xóa
const deleting = ref<AdminCategory | null>(null)
const isDeleting = ref(false)
const deleteError = ref('')
const deleteDialog = ref<HTMLElement | null>(null)

const isDeleteOpen = computed(() => Boolean(deleting.value))
const hiddenCount = computed(() => categories.value.filter((item) => !item.is_visible).length)

function sortCategories(items: AdminCategory[]): AdminCategory[] {
  return [...items].sort(
    (a, b) => a.sort_order - b.sort_order || a.name.localeCompare(b.name, 'vi') || a.id - b.id,
  )
}

async function loadCategories(): Promise<void> {
  isLoading.value = true
  errorMessage.value = ''
  try {
    categories.value = sortCategories((await listAdminCategories()).items)
  } catch (error) {
    errorMessage.value = getApiErrorMessage(error, 'Không thể tải danh sách danh mục.')
  } finally {
    isLoading.value = false
  }
}

function replaceCategory(updated: AdminCategory): void {
  const exists = categories.value.some((item) => item.id === updated.id)
  categories.value = sortCategories(
    exists
      ? categories.value.map((item) => (item.id === updated.id ? updated : item))
      : [...categories.value, updated],
  )
}

function openForm(category: AdminCategory | null): void {
  editing.value = category
  form.name = category?.name ?? ''
  form.slug = category?.slug ?? ''
  form.description = category?.description ?? ''
  form.icon = category?.icon ?? ''
  form.is_visible = category?.is_visible ?? true
  form.sort_order = category?.sort_order ?? 0
  formError.value = ''
  statusMessage.value = ''
  isFormOpen.value = true
}

function closeForm(): void {
  if (isSaving.value) return
  isFormOpen.value = false
}

useDialogFocus(isFormOpen, formDialog, closeForm)

async function submitForm(): Promise<void> {
  if (isSaving.value) return
  const name = form.name.trim()
  const slug = form.slug.trim().toLowerCase()
  formError.value = ''
  if (name.length < 2) {
    formError.value = 'Tên danh mục cần ít nhất 2 ký tự.'
    return
  }
  if (slug && !/^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug)) {
    formError.value = 'Đường dẫn chỉ gồm chữ thường không dấu, số và dấu gạch ngang (ví dụ: nong-san-tuoi).'
    return
  }
  const sortOrder = Number(form.sort_order)
  if (!Number.isInteger(sortOrder) || sortOrder < 0) {
    formError.value = 'Thứ tự là số nguyên từ 0 trở lên.'
    return
  }

  const payload: AdminCategoryPayload = {
    name,
    description: form.description.trim() || null,
    icon: form.icon.trim() || null,
    is_visible: form.is_visible,
    sort_order: sortOrder,
  }
  if (slug) payload.slug = slug
  else if (editing.value) payload.slug = editing.value.slug

  isSaving.value = true
  try {
    const saved = editing.value
      ? await updateAdminCategory(editing.value.id, payload)
      : await createAdminCategory(payload)
    replaceCategory(saved)
    statusMessage.value = editing.value ? `Đã lưu danh mục "${saved.name}".` : `Đã thêm danh mục "${saved.name}".`
    isSaving.value = false
    isFormOpen.value = false
  } catch (error) {
    formError.value = getApiErrorMessage(error, 'Không thể lưu danh mục.')
    isSaving.value = false
  }
}

async function toggleVisibility(category: AdminCategory): Promise<void> {
  if (togglingId.value !== null) return
  togglingId.value = category.id
  rowError.value = null
  statusMessage.value = ''
  try {
    const updated = await updateAdminCategory(category.id, { is_visible: !category.is_visible })
    replaceCategory(updated)
    statusMessage.value = updated.is_visible
      ? `Đã hiện danh mục "${updated.name}".`
      : `Đã ẩn danh mục "${updated.name}" khỏi bộ lọc và ô chọn khi tạo sản phẩm mới.`
  } catch (error) {
    rowError.value = {
      id: category.id,
      message: getApiErrorMessage(error, 'Không thể đổi trạng thái hiển thị.'),
    }
  } finally {
    togglingId.value = null
  }
}

function askDelete(category: AdminCategory): void {
  deleting.value = category
  deleteError.value = ''
  statusMessage.value = ''
}

function closeDelete(): void {
  if (isDeleting.value) return
  deleting.value = null
}

useDialogFocus(isDeleteOpen, deleteDialog, closeDelete)

async function confirmDelete(): Promise<void> {
  const category = deleting.value
  if (!category || isDeleting.value) return
  isDeleting.value = true
  deleteError.value = ''
  try {
    await deleteAdminCategory(category.id)
    categories.value = categories.value.filter((item) => item.id !== category.id)
    statusMessage.value = `Đã xóa danh mục "${category.name}".`
    isDeleting.value = false
    deleting.value = null
  } catch (error) {
    deleteError.value = getApiErrorMessage(error, 'Không thể xóa danh mục.')
    isDeleting.value = false
  }
}

onMounted(loadCategories)
</script>

<template>
  <div class="categories-page">
    <header class="page-heading">
      <div>
        <span>Danh mục sản phẩm</span>
        <h1>Danh mục</h1>
        <p>
          Danh mục ẩn không còn trong bộ lọc công khai và ô chọn khi chủ thể tạo sản phẩm mới;
          sản phẩm đã thuộc danh mục vẫn hiển thị bình thường.
        </p>
      </div>
      <div class="heading-actions">
        <strong>{{ categories.length }} danh mục<template v-if="hiddenCount"> · {{ hiddenCount }} đang ẩn</template></strong>
        <button class="btn btn-primary" type="button" @click="openForm(null)">
          <AppIcon name="plus" :size="16" /> Thêm danh mục
        </button>
      </div>
    </header>

    <div role="status" aria-live="polite">
      <p v-if="statusMessage" class="alert alert-success">
        <AppIcon name="checkCircle" :size="18" /> {{ statusMessage }}
      </p>
    </div>

    <section class="table-card" aria-label="Danh sách danh mục">
      <StatusPanel v-if="isLoading" kind="loading" :rows="4" message="Đang tải danh mục…" />
      <StatusPanel v-else-if="errorMessage" kind="error" :message="errorMessage" @retry="loadCategories" />
      <StatusPanel
        v-else-if="categories.length === 0"
        kind="empty"
        title="Chưa có danh mục nào"
        message="Thêm danh mục đầu tiên để chủ thể chọn khi khai báo sản phẩm."
      />
      <table v-else class="table categories-table">
        <thead>
          <tr>
            <th scope="col">Danh mục</th>
            <th scope="col">Đường dẫn</th>
            <th scope="col" class="text-end">Sản phẩm</th>
            <th scope="col" class="text-end">Thứ tự</th>
            <th scope="col">Hiển thị</th>
            <th scope="col" class="text-end">Thao tác</th>
          </tr>
        </thead>
        <tbody class="stagger-in">
          <tr v-for="category in categories" :key="category.id" :class="{ 'is-hidden': !category.is_visible }">
            <td data-label="Danh mục" class="cell-name">
              <div class="name-cell">
                <span
                  class="category-chip"
                  :style="{
                    background: categoryTheme(category.slug).background,
                    color: categoryTheme(category.slug).foreground,
                  }"
                  aria-hidden="true"
                >
                  <AppIcon :name="categoryTheme(category.slug).icon" :size="18" />
                </span>
                <div>
                  <strong>{{ category.name }}</strong>
                  <small v-if="category.description">{{ category.description }}</small>
                </div>
              </div>
            </td>
            <td data-label="Đường dẫn"><div><code>{{ category.slug }}</code></div></td>
            <td data-label="Sản phẩm" class="text-end"><div>{{ category.product_count }}</div></td>
            <td data-label="Thứ tự" class="text-end"><div>{{ category.sort_order }}</div></td>
            <td data-label="Hiển thị">
              <div class="visibility-cell">
                <button
                  class="switch"
                  type="button"
                  role="switch"
                  :aria-checked="category.is_visible"
                  :aria-label="`Hiển thị danh mục ${category.name}`"
                  :disabled="togglingId !== null"
                  @click="toggleVisibility(category)"
                >
                  <span class="switch-track" aria-hidden="true"><span class="switch-thumb" /></span>
                  <span class="switch-text">{{ category.is_visible ? 'Đang hiện' : 'Đang ẩn' }}</span>
                </button>
                <small v-if="rowError?.id === category.id" class="row-error" role="alert">{{ rowError.message }}</small>
              </div>
            </td>
            <td data-label="Thao tác" class="cell-actions">
              <div class="row-actions">
                <button class="btn btn-light" type="button" :aria-label="`Sửa danh mục ${category.name}`" @click="openForm(category)">
                  <AppIcon name="pencil" :size="15" /> Sửa
                </button>
                <button
                  v-if="category.product_count === 0"
                  class="btn btn-outline-danger"
                  type="button"
                  :aria-label="`Xóa danh mục ${category.name}`"
                  @click="askDelete(category)"
                >
                  <AppIcon name="trash" :size="15" /> Xóa
                </button>
                <small v-else class="delete-note">Còn sản phẩm, chỉ có thể ẩn</small>
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </section>

    <Transition name="ocop-fade">
      <div v-if="isFormOpen" class="modal-layer" role="presentation" @click.self="closeForm">
        <section
          ref="formDialog"
          class="dialog"
          role="dialog"
          aria-modal="true"
          aria-labelledby="category-form-title"
          tabindex="-1"
        >
          <header class="dialog-header">
            <h2 id="category-form-title">{{ editing ? 'Sửa danh mục' : 'Thêm danh mục' }}</h2>
            <button class="icon-button" type="button" aria-label="Đóng" @click="closeForm">
              <AppIcon name="close" :size="17" />
            </button>
          </header>
          <form class="category-form" novalidate @submit.prevent="submitForm">
            <div v-if="formError" class="alert alert-danger" role="alert">{{ formError }}</div>
            <label class="field">
              <span>Tên danh mục *</span>
              <input v-model="form.name" class="form-control" required minlength="2" maxlength="150" autocomplete="off" />
            </label>
            <label class="field">
              <span>Đường dẫn (slug)</span>
              <input
                v-model="form.slug"
                class="form-control"
                maxlength="150"
                autocomplete="off"
                aria-describedby="category-slug-hint"
                placeholder="Để trống để tự tạo từ tên"
              />
              <small id="category-slug-hint">Chữ thường không dấu, số và dấu gạch ngang, ví dụ: nong-san-tuoi.</small>
            </label>
            <label class="field">
              <span>Mô tả</span>
              <textarea v-model="form.description" class="form-control" rows="3" maxlength="2000" />
            </label>
            <div class="field-row">
              <label class="field">
                <span>Biểu tượng</span>
                <input v-model="form.icon" class="form-control" maxlength="100" autocomplete="off" placeholder="Ví dụ: bi-basket" />
              </label>
              <label class="field">
                <span>Thứ tự hiển thị</span>
                <input v-model.number="form.sort_order" class="form-control" type="number" min="0" step="1" inputmode="numeric" />
              </label>
            </div>
            <label class="check-field">
              <input v-model="form.is_visible" type="checkbox" />
              <span>Hiện trong bộ lọc và ô chọn khi tạo sản phẩm mới</span>
            </label>
            <div class="dialog-actions">
              <button class="btn btn-light" type="button" :disabled="isSaving" @click="closeForm">Hủy</button>
              <button class="btn btn-primary" type="submit" :disabled="isSaving">
                {{ isSaving ? 'Đang lưu...' : editing ? 'Lưu thay đổi' : 'Thêm danh mục' }}
              </button>
            </div>
          </form>
        </section>
      </div>
    </Transition>

    <Transition name="ocop-fade">
      <div v-if="deleting" class="modal-layer" role="presentation" @click.self="closeDelete">
        <section
          ref="deleteDialog"
          class="dialog dialog-sm"
          role="alertdialog"
          aria-modal="true"
          aria-labelledby="category-delete-title"
          aria-describedby="category-delete-desc"
          tabindex="-1"
        >
          <h2 id="category-delete-title">Xóa danh mục "{{ deleting.name }}"?</h2>
          <p id="category-delete-desc" class="dialog-text">
            Danh mục chưa có sản phẩm nào. Sau khi xóa sẽ không khôi phục được.
          </p>
          <div v-if="deleteError" class="alert alert-danger" role="alert">{{ deleteError }}</div>
          <div class="dialog-actions">
            <button class="btn btn-light" type="button" :disabled="isDeleting" @click="closeDelete">Hủy</button>
            <button class="btn btn-danger" type="button" :disabled="isDeleting" @click="confirmDelete">
              {{ isDeleting ? 'Đang xóa...' : 'Xác nhận xóa' }}
            </button>
          </div>
        </section>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.categories-page { display: grid; gap: var(--admin-space-5); font-family: var(--admin-font); }

.page-heading { display: flex; align-items: flex-end; justify-content: space-between; gap: var(--admin-space-4); flex-wrap: wrap; }
.page-heading > div:first-child { max-width: 64ch; }
.page-heading > div > span { color: var(--admin-primary); font-size: var(--admin-font-xs); font-weight: 800; text-transform: uppercase; letter-spacing: 0.07em; }
.page-heading h1 { margin: var(--admin-space-1) 0; color: var(--admin-text); font-size: var(--ocop-font-size-title-md); font-weight: 800; }
.page-heading p { margin: 0; color: var(--admin-muted); font-size: var(--admin-font-sm); }
.heading-actions { display: flex; align-items: center; gap: var(--admin-space-3); flex-wrap: wrap; }
.heading-actions > strong { padding: var(--admin-space-1) var(--admin-space-3); border-radius: var(--admin-radius-pill); background: var(--admin-primary-soft); color: var(--admin-primary-dark); font-size: var(--admin-font-xs); font-weight: 800; }

.btn {
  display: inline-flex;
  min-height: var(--admin-control-height);
  align-items: center;
  justify-content: center;
  gap: var(--admin-space-2);
  padding: 0 var(--admin-space-4);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  white-space: nowrap;
  cursor: pointer;
  transition: background var(--admin-transition), border-color var(--admin-transition), color var(--admin-transition);
}
.btn-primary { border-color: var(--admin-primary-dark); background: var(--admin-primary-dark); color: var(--admin-on-primary); }
.btn-primary:hover { background: var(--admin-primary); }
.btn-danger { border-color: var(--admin-danger-text); background: var(--admin-danger-text); color: var(--admin-on-primary); }
.btn-danger:hover { background: var(--admin-danger-hover); }
.btn-light { background: var(--admin-bg); color: var(--admin-text); }
.btn-light:hover { border-color: var(--admin-primary); color: var(--admin-primary-dark); }
.btn-outline-danger { border-color: var(--admin-danger-border); background: transparent; color: var(--admin-danger-text); }
.btn-outline-danger:hover { background: var(--admin-danger-soft); }
.btn:disabled { cursor: not-allowed; opacity: 0.55; }

.alert { display: flex; align-items: center; gap: var(--admin-space-2); margin: 0; padding: var(--admin-space-3) var(--admin-space-4); border-radius: var(--admin-radius-md); font-size: var(--admin-font-sm); }
.alert-success { border: 1px solid var(--admin-success-border); background: var(--admin-success-soft); color: var(--admin-success-text); }
.alert-danger { border: 1px solid var(--admin-danger-border); background: var(--admin-danger-soft); color: var(--admin-danger-text); }

.table-card { overflow: hidden; border: 1px solid var(--admin-border); border-radius: var(--admin-radius-lg); background: var(--admin-card); box-shadow: var(--admin-shadow-sm); }
.table { width: 100%; margin: 0; border-collapse: collapse; }
.table th {
  padding: var(--admin-space-3) var(--admin-space-5);
  border-bottom: 1px solid var(--admin-border);
  background: var(--admin-bg);
  color: var(--admin-muted);
  font-size: var(--admin-font-xs);
  font-weight: 700;
  letter-spacing: 0.05em;
  text-align: left;
  text-transform: uppercase;
  white-space: nowrap;
}
.table th.text-end, .table td.text-end { text-align: right; }
.table td { padding: var(--admin-space-3) var(--admin-space-5); border-bottom: 1px solid var(--admin-border-soft); color: var(--admin-text); font-size: var(--admin-font-sm); vertical-align: middle; }
.table tbody tr:last-child td { border-bottom: 0; }
.table tbody tr:hover td { background: var(--admin-bg); }
.table tbody tr.is-hidden .name-cell strong { color: var(--admin-muted); }
.table td strong { display: block; font-weight: 700; }
.table td small { display: block; margin-top: var(--admin-space-1); color: var(--admin-muted); font-size: var(--admin-font-xs); overflow-wrap: anywhere; }
.table code { color: var(--admin-text); font-size: var(--admin-font-xs); overflow-wrap: anywhere; }

.name-cell { display: flex; align-items: center; gap: var(--admin-space-3); }
.category-chip { display: grid; flex: none; width: 40px; height: 40px; place-items: center; border-radius: var(--admin-radius-md); }

.visibility-cell { display: grid; justify-items: start; gap: var(--admin-space-1); }
.switch {
  display: inline-flex;
  min-height: var(--admin-control-height);
  align-items: center;
  gap: var(--admin-space-2);
  padding: 0 var(--admin-space-2);
  border: 0;
  border-radius: var(--admin-radius-sm);
  background: transparent;
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
  font-weight: 600;
  cursor: pointer;
}
.switch:disabled { cursor: progress; opacity: 0.7; }
.switch-track { position: relative; width: 40px; height: 24px; border-radius: var(--admin-radius-pill); background: var(--ocop-mist-500); transition: background var(--admin-transition); }
.switch-thumb { position: absolute; top: 3px; left: 3px; width: 18px; height: 18px; border-radius: 50%; background: var(--ocop-white); box-shadow: var(--admin-shadow-sm); transition: transform var(--admin-transition); }
.switch[aria-checked='true'] .switch-track { background: var(--admin-success); }
.switch[aria-checked='true'] .switch-thumb { transform: translateX(16px); }
.row-error { color: var(--admin-danger-text) !important; }

.row-actions { display: flex; align-items: center; justify-content: flex-end; gap: var(--admin-space-2); flex-wrap: wrap; }
.delete-note { margin: 0 !important; max-width: 16ch; text-align: right; }

.modal-layer { position: fixed; z-index: 200; inset: 0; display: grid; padding: var(--admin-space-5); place-items: center; overflow-y: auto; background: var(--admin-scrim); }
.dialog { width: min(100%, 560px); max-height: calc(100vh - 2 * var(--admin-space-5)); padding: var(--admin-space-6); overflow-y: auto; border-radius: var(--admin-radius-lg); background: var(--admin-card); box-shadow: var(--admin-shadow-modal); }
.dialog-sm { width: min(100%, 460px); }
.dialog h2 { margin: 0; color: var(--admin-text); font-size: var(--admin-font-xl); font-weight: 800; overflow-wrap: anywhere; }
.dialog-header { display: flex; align-items: flex-start; justify-content: space-between; gap: var(--admin-space-4); margin-bottom: var(--admin-space-4); }
.icon-button { display: grid; width: var(--admin-control-height); height: var(--admin-control-height); flex: none; place-items: center; border: 0; border-radius: var(--admin-radius-sm); background: var(--admin-bg); color: var(--admin-muted); cursor: pointer; }
.icon-button:hover { background: var(--admin-danger-soft); color: var(--admin-danger-text); }
.dialog-text { margin: var(--admin-space-3) 0 0; color: var(--admin-text); font-size: var(--admin-font-sm); }

.category-form { display: grid; gap: var(--admin-space-4); }
.field { display: grid; gap: var(--admin-space-1); margin: 0; }
.field > span { color: var(--admin-text); font-size: var(--admin-font-sm); font-weight: 700; }
.field > small { color: var(--admin-muted); font-size: var(--admin-font-xs); }
.field-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: var(--admin-space-3); }
.form-control {
  width: 100%;
  min-height: var(--admin-control-height);
  padding: var(--admin-space-2) var(--admin-space-3);
  border: 1px solid var(--admin-border);
  border-radius: var(--admin-radius-sm);
  background: var(--admin-card);
  color: var(--admin-text);
  font-size: var(--admin-font-sm);
}
.form-control:focus { border-color: var(--admin-primary); }
textarea.form-control { resize: vertical; }
.check-field { display: flex; min-height: var(--admin-control-height); align-items: center; gap: var(--admin-space-3); margin: 0; color: var(--admin-text); font-size: var(--admin-font-sm); cursor: pointer; }
.check-field input { width: 20px; height: 20px; flex: none; accent-color: var(--admin-primary-dark); }
.dialog-actions { display: flex; justify-content: flex-end; gap: var(--admin-space-2); margin-top: var(--admin-space-4); }

@media (prefers-reduced-motion: reduce) {
  .switch-track, .switch-thumb { transition: none; }
}

@media (max-width: 767.98px) {
  .page-heading { align-items: flex-start; flex-direction: column; }
  .heading-actions { width: 100%; justify-content: space-between; }
  .field-row { grid-template-columns: 1fr; }

  /* Điện thoại: mỗi danh mục là một thẻ, nhãn cột hiện bên trái giá trị. */
  .categories-table thead { position: absolute; width: 1px; height: 1px; overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap; }
  .categories-table tbody { display: grid; gap: var(--admin-space-3); padding: var(--admin-space-3); }
  .categories-table tr { display: grid; gap: var(--admin-space-2); padding: var(--admin-space-4); border: 1px solid var(--admin-border); border-radius: var(--admin-radius-md); background: var(--admin-card); }
  .categories-table tbody tr:hover td { background: transparent; }
  .categories-table td { display: grid; grid-template-columns: minmax(88px, 35%) minmax(0, 1fr); align-items: center; gap: var(--admin-space-2); padding: 0; border: 0; text-align: left !important; }
  .categories-table td::before { content: attr(data-label); color: var(--admin-muted); font-size: var(--admin-font-xs); font-weight: 700; }
  .categories-table td.cell-name, .categories-table td.cell-actions { grid-template-columns: 1fr; }
  .categories-table td.cell-name::before, .categories-table td.cell-actions::before { content: none; }
  .categories-table td.cell-actions { padding-top: var(--admin-space-2); border-top: 1px solid var(--admin-border-soft); }
  .row-actions { justify-content: stretch; }
  .row-actions .btn { flex: 1; }
  .delete-note { max-width: none; text-align: left; }
}
</style>
