import axios from 'axios'

interface ApiValidationDetail {
  loc?: Array<string | number>
  msg?: string
  type?: string
  ctx?: Record<string, unknown>
}

interface ApiErrorBody {
  code?: string
  message?: string
  details?: unknown
}

/** Tên trường (khóa của API) → tên hiển thị tiếng Việt cho người dùng. */
const FIELD_LABELS: Record<string, string> = {
  name: 'Tên sản phẩm',
  price: 'Giá',
  unit: 'Đơn vị tính',
  star: 'Hạng sao',
  category_id: 'Nhóm sản phẩm',
  description: 'Mô tả',
  story: 'Câu chuyện sản phẩm',
  ingredients: 'Thành phần',
  usage_instructions: 'Hướng dẫn sử dụng',
  cert_code: 'Mã chứng nhận',
  cert_issued_at: 'Ngày cấp chứng nhận',
  cert_expires_at: 'Ngày hết hạn chứng nhận',
  issuing_authority: 'Cơ quan công nhận',
  certificate_url: 'Đường dẫn tài liệu chứng nhận',
  certificate_storage_path: 'Tệp chứng nhận',
  vietgap_code: 'Mã VietGAP',
  images: 'Ảnh sản phẩm',
  image_url: 'Đường dẫn ảnh',
  email: 'Email',
  password: 'Mật khẩu',
  current_password: 'Mật khẩu hiện tại',
  new_password: 'Mật khẩu mới',
  full_name: 'Họ và tên',
  phone: 'Số điện thoại',
  contact_phone: 'Số điện thoại liên hệ',
  avatar_url: 'Đường dẫn ảnh đại diện',
  tax_code: 'Mã số thuế',
  representative: 'Người đại diện',
  address: 'Địa chỉ',
  district: 'Xã, phường',
  note: 'Ghi chú',
  reason: 'Lý do',
  review_note: 'Phản hồi',
  moderation_note: 'Phản hồi',
  rejection_reason: 'Lý do từ chối',
  comment: 'Nhận xét',
  rating: 'Số sao đánh giá',
  title: 'Tiêu đề',
  content: 'Nội dung',
  search: 'Từ khóa tìm kiếm',
  slug: 'Đường dẫn rút gọn',
  website: 'Trang web',
  opening_hours: 'Giờ mở cửa',
  ticket_price: 'Giá vé',
  services: 'Dịch vụ',
  latitude: 'Vĩ độ',
  longitude: 'Kinh độ',
  location_type: 'Loại hình điểm du lịch',
  status: 'Trạng thái',
  page: 'Trang',
  page_size: 'Số dòng mỗi trang',
  alt_text: 'Mô tả ảnh',
  sort_order: 'Thứ tự',
}

/** Phần đầu của loc chỉ cho biết nơi dữ liệu nằm trong yêu cầu, không phải tên trường. */
const LOCATION_SCOPES = new Set(['body', 'query', 'path', 'header', 'cookie'])

function numberText(value: unknown): string {
  return typeof value === 'number' ? value.toLocaleString('vi-VN') : String(value)
}

/** Chuyển câu lỗi pydantic (tiếng Anh) thành cụm tiếng Việt đứng sau tên trường. */
export function translateValidationMessage(detail: ApiValidationDetail): string {
  const raw = (detail.msg ?? '').trim()
  const type = detail.type ?? ''
  const ctx = detail.ctx ?? {}

  if (raw.startsWith('Value error, ')) return raw.slice('Value error, '.length).trim()

  if (type === 'missing' || /^field required$/i.test(raw)) return 'là bắt buộc'

  const atMost = raw.match(/at most (\d+) character/i)
  if (type === 'string_too_long' || atMost) {
    const n = atMost?.[1] ?? ctx.max_length
    return `tối đa ${numberText(Number(n))} ký tự`
  }
  const atLeast = raw.match(/at least (\d+) character/i)
  if (type === 'string_too_short' || atLeast) {
    const n = atLeast?.[1] ?? ctx.min_length
    return `tối thiểu ${numberText(Number(n))} ký tự`
  }
  const listMost = raw.match(/at most (\d+) item/i)
  if (type === 'too_long' || listMost) {
    const n = listMost?.[1] ?? ctx.max_length
    return `tối đa ${n} mục`
  }
  const listLeast = raw.match(/at least (\d+) item/i)
  if (type === 'too_short' || listLeast) {
    const n = listLeast?.[1] ?? ctx.min_length
    return `cần ít nhất ${n} mục`
  }

  const gte = raw.match(/greater than or equal to (-?[\d.]+)/i)
  if (gte) return `phải từ ${numberText(Number(gte[1]))} trở lên`
  const gt = raw.match(/greater than (-?[\d.]+)/i)
  if (gt) return `phải lớn hơn ${numberText(Number(gt[1]))}`
  const lte = raw.match(/less than or equal to (-?[\d.]+)/i)
  if (lte) return `không được vượt quá ${numberText(Number(lte[1]))}`
  const lt = raw.match(/less than (-?[\d.]+)/i)
  if (lt) return `phải nhỏ hơn ${numberText(Number(lt[1]))}`

  if (type === 'string_pattern_mismatch' || /should match pattern/i.test(raw)) return 'chưa đúng định dạng'
  if (/email/i.test(raw)) return 'chưa phải địa chỉ email hợp lệ'
  if (/valid (url|http)|url/i.test(raw)) return 'chưa phải đường dẫn hợp lệ'
  if (/valid date|valid datetime/i.test(raw)) return 'chưa phải ngày hợp lệ'
  if (/valid (integer|number|decimal)|decimal input|should be a valid/i.test(raw)) {
    return /no more than \d+ digits|decimal places/i.test(raw) ? 'có quá nhiều chữ số' : 'chưa phải số hợp lệ'
  }
  if (type === 'literal_error' || type === 'enum' || /^input should be '/i.test(raw)) return 'có giá trị chưa được chấp nhận'
  if (type === 'extra_forbidden') return 'không được phép gửi'

  return 'chưa hợp lệ'
}

function fieldKey(loc: ApiValidationDetail['loc']): string | null {
  if (!Array.isArray(loc)) return null
  for (let index = loc.length - 1; index >= 0; index -= 1) {
    const part = loc[index]
    if (typeof part === 'string' && !LOCATION_SCOPES.has(part)) return part
  }
  return null
}

function fieldLabel(detail: ApiValidationDetail, key: string): string {
  const base = FIELD_LABELS[key] ?? `(${key})`
  const imageIndex = Array.isArray(detail.loc) ? detail.loc.findIndex((part) => part === 'images') : -1
  const position = imageIndex >= 0 ? detail.loc?.[imageIndex + 1] : undefined
  if (key !== 'images' && typeof position === 'number') return `Ảnh số ${position + 1}: ${base.toLowerCase()}`
  return base
}

function validationDetails(body: ApiErrorBody | undefined): ApiValidationDetail[] {
  if (!body || !Array.isArray(body.details)) return []
  return body.details.filter(
    (item): item is ApiValidationDetail => typeof item === 'object' && item !== null && 'msg' in item,
  )
}

function validationSentence(detail: ApiValidationDetail): string {
  const key = fieldKey(detail.loc)
  const phrase = translateValidationMessage(detail)
  if (!key) {
    const text = phrase.charAt(0).toUpperCase() + phrase.slice(1)
    return text.endsWith('.') ? text : `${text}.`
  }
  return `${fieldLabel(detail, key)} ${phrase}.`
}

const MAX_LISTED_ERRORS = 4

/**
 * Với lỗi 422 (VALIDATION_ERROR) trả về map `tên trường → thông điệp tiếng Việt`.
 * Trường nào có nhiều lỗi thì lấy lỗi đầu tiên. Lỗi không gắn với trường nào được đặt ở khóa `_form`.
 * Không phải lỗi kiểm tra dữ liệu thì trả về `{}`.
 */
export function getApiFieldErrors(error: unknown): Record<string, string> {
  if (!axios.isAxiosError<ApiErrorBody>(error) || !error.response) return {}
  const result: Record<string, string> = {}
  for (const detail of validationDetails(error.response.data)) {
    const key = fieldKey(detail.loc) ?? '_form'
    if (!(key in result)) result[key] = validationSentence(detail)
  }
  return result
}

export function getApiErrorMessage(error: unknown, fallback?: string): string {
  const defaultMessage = fallback ?? 'Có lỗi xảy ra. Vui lòng thử lại.'
  if (!axios.isAxiosError<ApiErrorBody>(error)) {
    return defaultMessage
  }

  if (!error.response) {
    return 'Không thể kết nối đến máy chủ. Vui lòng thử lại.'
  }

  const body = error.response.data
  const details = validationDetails(body)
  if ((error.response.status === 422 || body?.code === 'VALIDATION_ERROR') && details.length) {
    const sentences = details.map(validationSentence)
    const unique = [...new Set(sentences)]
    if (unique.length === 1) return unique[0]
    const shown = unique.slice(0, MAX_LISTED_ERRORS)
    const rest = unique.length - shown.length
    const tail = rest > 0 ? ` Và ${rest} mục khác.` : ''
    return `Cần sửa ${unique.length} mục: ${shown.join(' ')}${tail}`
  }

  return body?.message || defaultMessage
}
