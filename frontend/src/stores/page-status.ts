import { computed, readonly, ref } from 'vue'

/**
 * Trạng thái chờ chung của cả ứng dụng: đang chuyển trang, đang có request chạy, mất mạng,
 * và lỗi không mở được trang (mã trang tải thất bại). Các thành phần giao diện
 * (thanh tiến trình, thông báo ngoại tuyến, khung xương trang) chỉ đọc từ đây.
 */
const navigating = ref(false)
const pendingRequests = ref(0)
const online = ref(typeof navigator === 'undefined' ? true : navigator.onLine !== false)
const navigationFailure = ref<{ target: string } | null>(null)
const firstNavigationDone = ref(false)

/** Có việc đang chờ: chuyển trang hoặc ít nhất một request API chưa xong. */
const isBusy = computed(() => navigating.value || pendingRequests.value > 0)

function startNavigation(): void {
  navigating.value = true
  navigationFailure.value = null
}

function finishNavigation(): void {
  navigating.value = false
  firstNavigationDone.value = true
}

function requestStarted(): void {
  pendingRequests.value += 1
}

function requestFinished(): void {
  pendingRequests.value = Math.max(0, pendingRequests.value - 1)
}

function setOnline(value: boolean): void {
  online.value = value
}

function reportNavigationFailure(target: string): void {
  navigating.value = false
  firstNavigationDone.value = true
  navigationFailure.value = { target }
}

function dismissNavigationFailure(): void {
  navigationFailure.value = null
}

export const pageStatus = {
  navigating: readonly(navigating),
  pendingRequests: readonly(pendingRequests),
  online: readonly(online),
  navigationFailure: readonly(navigationFailure),
  firstNavigationDone: readonly(firstNavigationDone),
  isBusy,
  startNavigation,
  finishNavigation,
  requestStarted,
  requestFinished,
  setOnline,
  reportNavigationFailure,
  dismissNavigationFailure,
}
