/**
 * Lỗi tải mã của một trang (import động). Hai nguyên nhân thường gặp:
 * - mất mạng giữa chừng;
 * - vừa triển khai bản mới nên tên tệp cũ không còn (tab mở từ trước).
 */
const CHUNK_ERROR_PATTERNS = [
  /Failed to fetch dynamically imported module/i,
  /error loading dynamically imported module/i,
  /Importing a module script failed/i,
  /Unable to preload CSS/i,
  /Loading (CSS )?chunk [\w-]+ failed/i,
]

export function isChunkLoadError(error: unknown): boolean {
  const message = error instanceof Error ? error.message : typeof error === 'string' ? error : ''
  return CHUNK_ERROR_PATTERNS.some((pattern) => pattern.test(message))
}

const RELOAD_KEY = 'ocop_chunk_reload_at'
const RELOAD_COOLDOWN_MS = 60_000

/**
 * Quyết định xử lý khi tải mã trang thất bại:
 * - `reload`: đang có mạng và chưa tải lại trong 60 giây gần nhất, nhiều khả năng do bản mới → tải lại trang đích;
 * - `notify`: ngoại tuyến, đã tải lại mà vẫn lỗi, hoặc không ghi nhớ được lần tải lại → báo người dùng và cho thử lại.
 */
export function decideChunkRecovery(
  online: boolean,
  now = Date.now(),
  storage: Pick<Storage, 'getItem' | 'setItem'> | null = safeSessionStorage(),
): 'reload' | 'notify' {
  if (!online || !storage) return 'notify'
  let last = 0
  try {
    last = Number(storage.getItem(RELOAD_KEY) ?? 0) || 0
    if (now - last < RELOAD_COOLDOWN_MS) return 'notify'
    storage.setItem(RELOAD_KEY, String(now))
  } catch {
    // Không ghi nhớ được lần tải lại thì không tải lại, tránh vòng lặp vô hạn.
    return 'notify'
  }
  return 'reload'
}

function safeSessionStorage(): Storage | null {
  try {
    return typeof window === 'undefined' ? null : window.sessionStorage
  } catch {
    return null
  }
}
