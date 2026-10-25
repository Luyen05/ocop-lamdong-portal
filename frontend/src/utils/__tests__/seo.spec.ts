// @vitest-environment jsdom
import { beforeEach, describe, expect, it } from 'vitest'

import {
  absoluteUrl,
  applyPageSeo,
  clipDescription,
  DEFAULT_DESCRIPTION,
  locationJsonLd,
  productJsonLd,
} from '@/utils/seo'

function meta(attribute: 'name' | 'property', key: string): string | null {
  return document.head.querySelector(`meta[${attribute}="${key}"]`)?.getAttribute('content') ?? null
}

describe('applyPageSeo', () => {
  beforeEach(() => {
    document.head.innerHTML = ''
    document.title = ''
  })

  it('đặt tiêu đề, mô tả, canonical, Open Graph và Twitter Card', () => {
    applyPageSeo({ title: 'Trà xanh', description: 'Trà Cầu Đất', path: '/san-pham/tra-xanh', image: '/a.jpg' })

    expect(document.title).toBe('Trà xanh | OCOP Lâm Đồng')
    expect(meta('name', 'description')).toBe('Trà Cầu Đất')
    expect(document.head.querySelector('link[rel="canonical"]')?.getAttribute('href')).toBe(
      `${window.location.origin}/san-pham/tra-xanh`,
    )
    expect(meta('property', 'og:title')).toBe('Trà xanh | OCOP Lâm Đồng')
    expect(meta('property', 'og:image')).toBe(`${window.location.origin}/a.jpg`)
    expect(meta('property', 'og:locale')).toBe('vi_VN')
    expect(meta('name', 'twitter:card')).toBe('summary_large_image')
  })

  it('không nhân đôi thẻ khi gọi lại và dùng mô tả mặc định khi thiếu', () => {
    applyPageSeo({ title: 'A' })
    applyPageSeo({ title: 'B' })

    expect(document.head.querySelectorAll('meta[name="description"]')).toHaveLength(1)
    expect(document.head.querySelectorAll('link[rel="canonical"]')).toHaveLength(1)
    expect(meta('name', 'description')).toBe(DEFAULT_DESCRIPTION)
    expect(document.title).toBe('B | OCOP Lâm Đồng')
  })

  it('noindex chỉ có khi được yêu cầu và bị gỡ ở trang kế tiếp', () => {
    applyPageSeo({ title: 'Tài khoản', noindex: true })
    expect(meta('name', 'robots')).toBe('noindex, nofollow')

    applyPageSeo({ title: 'Sản phẩm' })
    expect(meta('name', 'robots')).toBeNull()
  })

  it('fullTitle được dùng nguyên văn', () => {
    applyPageSeo({ fullTitle: 'OCOP Lâm Đồng | Nông sản OCOP' })
    expect(document.title).toBe('OCOP Lâm Đồng | Nông sản OCOP')
  })

  it('JSON-LD được thay thế, gỡ khi trang sau không có và không thể đóng thẻ script sớm', () => {
    applyPageSeo({ title: 'A', jsonLd: { '@type': 'Product', name: '</script><b>x' } })
    const script = document.getElementById('seo-json-ld')!
    expect(script.textContent).not.toContain('</script>')
    expect(JSON.parse(script.textContent!).name).toBe('</script><b>x')

    applyPageSeo({ title: 'B', jsonLd: { '@type': 'TouristAttraction' } })
    expect(document.querySelectorAll('#seo-json-ld')).toHaveLength(1)
    expect(JSON.parse(document.getElementById('seo-json-ld')!.textContent!)['@type']).toBe('TouristAttraction')

    applyPageSeo({ title: 'C' })
    expect(document.getElementById('seo-json-ld')).toBeNull()
  })
})

describe('clipDescription và absoluteUrl', () => {
  it('rút gọn tại ranh giới từ và gộp khoảng trắng', () => {
    const text = 'Trà   xanh '.repeat(40)
    const clipped = clipDescription(text, 50)
    expect(clipped.length).toBeLessThanOrEqual(50)
    expect(clipped.endsWith('…')).toBe(true)
    expect(clipDescription('  ngắn  ')).toBe('ngắn')
    expect(clipDescription(null)).toBe('')
  })

  it('giữ nguyên địa chỉ tuyệt đối, ghép origin cho đường dẫn tương đối', () => {
    expect(absoluteUrl('https://res.cloudinary.com/x.jpg')).toBe('https://res.cloudinary.com/x.jpg')
    expect(absoluteUrl('/a.jpg')).toBe(`${window.location.origin}/a.jpg`)
  })
})

describe('dữ liệu có cấu trúc', () => {
  it('Product có thương hiệu, hạng sao, ảnh và giá chỉ khi giá > 0', () => {
    const base = {
      name: 'Trà',
      description: 'Ngon',
      star: 4,
      price: 120000,
      category: { name: 'Đồ uống' },
      subject: { name: 'HTX' },
      primary_image_url: 'https://x/y.jpg',
    }
    const data = productJsonLd(base, 'https://s/san-pham/tra')
    expect(data['@type']).toBe('Product')
    expect(data.brand).toEqual({ '@type': 'Brand', name: 'HTX' })
    expect(data.offers).toMatchObject({ price: '120000', priceCurrency: 'VND' })
    expect(productJsonLd({ ...base, price: null }, 'u').offers).toBeUndefined()
  })

  it('TouristAttraction có tọa độ và giờ mở cửa', () => {
    const data = locationJsonLd(
      {
        name: 'Đồi chè',
        description: null,
        type_label: 'Đồi chè & cà phê',
        address: 'Cầu Đất',
        latitude: 11.88,
        longitude: 108.54,
        opening_hours: '07:00 - 19:00',
        primary_image_url: null,
      },
      'u',
    )
    expect(data.geo).toEqual({ '@type': 'GeoCoordinates', latitude: 11.88, longitude: 108.54 })
    expect(data.openingHours).toBe('07:00 - 19:00')
    expect(data.image).toBeUndefined()
  })
})
