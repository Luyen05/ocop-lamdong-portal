/**
 * Lỗi Vue báo kèm `info` cho biết đang ở giai đoạn nào. Chỉ lỗi khi dựng giao diện
 * (render, setup) mới khiến cả trang không dùng được và đáng thay bằng trang lỗi chung;
 * lỗi trong sự kiện, watcher hay tác vụ nền chỉ được ghi nhật ký, trang vẫn dùng tiếp.
 */
export function isFatalRenderError(info: string): boolean {
  return /^(render function|setup function)$/i.test(info.trim())
}
