import { safeExternalUrl } from '@/utils/location'

/**
 * Câu chuyện sản phẩm có thể kết thúc bằng "Nguồn: https://…" hoặc "Nguồn sản phẩm: https://…".
 * Tách phần nguồn khỏi văn bản; chỉ trả về liên kết khi là http/https hợp lệ (không đổi dữ liệu gốc).
 */
const STORY_SOURCE_PATTERN = /\s*Nguồn(?:\s+sản\s+phẩm)?\s*:\s*([a-z][a-z0-9+.-]*:\S*)\s*$/iu

export function parseStorySource(story: string | null | undefined): { text: string; sourceUrl: string | null } {
  const value = story ?? ''
  const match = STORY_SOURCE_PATTERN.exec(value)
  if (!match) return { text: value, sourceUrl: null }
  return {
    text: value.slice(0, match.index).trim(),
    sourceUrl: safeExternalUrl(match[1]),
  }
}
