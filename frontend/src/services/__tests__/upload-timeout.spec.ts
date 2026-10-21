import { beforeEach, describe, expect, it, vi } from 'vitest'

const http = vi.hoisted(() => ({
  post: vi.fn(),
  get: vi.fn(),
}))

vi.mock('@/services/http', () => ({ default: http, UPLOAD_TIMEOUT_MS: 120_000 }))

import { uploadLocationImage } from '@/services/location-management'
import {
  downloadProductCertificate,
  uploadProductCertificate,
  uploadProductImage,
} from '@/services/product-management'

describe('tải file dùng thời gian chờ riêng 120 giây', () => {
  beforeEach(() => {
    http.post.mockReset().mockResolvedValue({ data: {} })
    http.get.mockReset().mockResolvedValue({ data: new Blob() })
  })

  it.each([
    ['ảnh sản phẩm', uploadProductImage, '/subject/product-images'],
    ['chứng nhận', uploadProductCertificate, '/subject/product-certificates'],
    ['ảnh điểm du lịch', uploadLocationImage, '/subject/location-images'],
  ])('%s', async (_label, upload, url) => {
    await upload(new File(['x'], 'a.png', { type: 'image/png' }))

    expect(http.post).toHaveBeenCalledWith(url, expect.any(FormData), { timeout: 120_000 })
  })

  it('tải chứng nhận về', async () => {
    await downloadProductCertificate('admin', 5)

    expect(http.get).toHaveBeenCalledWith('/admin/products/5/certificate', {
      responseType: 'blob',
      timeout: 120_000,
    })
  })
})
