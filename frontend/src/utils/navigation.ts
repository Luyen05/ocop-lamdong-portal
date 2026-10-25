/** Chuyển sang trang ngoài (Google/Facebook). Tách riêng để test thay thế được: jsdom không cho đổi trang. */
export function navigateToExternal(url: string): void {
  window.location.assign(url)
}
