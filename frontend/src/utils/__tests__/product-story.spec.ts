import { describe, expect, it } from 'vitest'

import { parseStorySource } from '@/utils/product-story'

describe('parseStorySource', () => {
  const url = 'https://ocoplamdong.gov.vn/Media/admin/files/225%20Quye%CC%82%CC%81t.pdf'

  it.each(['Nguồn', 'Nguồn sản phẩm'])('tach "%s: URL" cuoi cau chuyen', (label) => {
    const result = parseStorySource(`Đạt 69,00 điểm theo Quyết định 3981/QĐ-UBND. ${label}: ${url}`)
    expect(result.text).toBe('Đạt 69,00 điểm theo Quyết định 3981/QĐ-UBND.')
    expect(result.sourceUrl).toBe(url)
  })

  it('khong tao lien ket cho giao thuc nguy hiem nhung van bo khoi van ban', () => {
    const result = parseStorySource('Câu chuyện. Nguồn: javascript:alert(1)')
    expect(result.sourceUrl).toBeNull()
    expect(result.text).toBe('Câu chuyện.')
  })

  it('giu nguyen van ban khi khong co URL o cuoi', () => {
    expect(parseStorySource('Nguồn: Cổng OCOP tỉnh').text).toBe('Nguồn: Cổng OCOP tỉnh')
    expect(parseStorySource('Nguồn gốc từ Đà Lạt.').sourceUrl).toBeNull()
    expect(parseStorySource(null)).toEqual({ text: '', sourceUrl: null })
  })
})
