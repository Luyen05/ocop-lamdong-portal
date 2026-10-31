import { beforeEach, describe, expect, it } from 'vitest'

import { pageStatus } from '../page-status'

describe('pageStatus', () => {
  beforeEach(() => {
    while (pageStatus.pendingRequests.value > 0) pageStatus.requestFinished()
    pageStatus.finishNavigation()
    pageStatus.dismissNavigationFailure()
    pageStatus.setOnline(true)
  })

  it('bận khi đang chuyển trang hoặc còn request chạy', () => {
    expect(pageStatus.isBusy.value).toBe(false)
    pageStatus.startNavigation()
    expect(pageStatus.isBusy.value).toBe(true)
    pageStatus.finishNavigation()
    expect(pageStatus.isBusy.value).toBe(false)
    pageStatus.requestStarted()
    pageStatus.requestStarted()
    expect(pageStatus.isBusy.value).toBe(true)
    pageStatus.requestFinished()
    expect(pageStatus.isBusy.value).toBe(true)
    pageStatus.requestFinished()
    expect(pageStatus.isBusy.value).toBe(false)
  })

  it('bộ đếm request không xuống dưới 0', () => {
    pageStatus.requestFinished()
    pageStatus.requestFinished()
    expect(pageStatus.pendingRequests.value).toBe(0)
  })

  it('ghi nhận và xoá lỗi mở trang khi bắt đầu chuyển trang mới', () => {
    pageStatus.startNavigation()
    pageStatus.reportNavigationFailure('/san-pham')
    expect(pageStatus.navigating.value).toBe(false)
    expect(pageStatus.navigationFailure.value).toEqual({ target: '/san-pham' })
    pageStatus.startNavigation()
    expect(pageStatus.navigationFailure.value).toBeNull()
  })

  it('đánh dấu đã qua lần điều hướng đầu tiên', () => {
    pageStatus.finishNavigation()
    expect(pageStatus.firstNavigationDone.value).toBe(true)
  })
})
