/**
 * Thẻ SEO theo từng trang: tiêu đề, mô tả, canonical, Open Graph, Twitter Card, robots, JSON-LD.
 * Trình tìm kiếm hiện đại (Google) chạy JavaScript nên đọc được các thẻ này. Bot chia sẻ không chạy
 * JavaScript (Facebook, Zalo) nhận HTML tĩnh từ backend (`backend/app/api/routes/seo.py`) qua Nginx.
 */
import { SITE_NAME } from '@/router/titles'

export const DEFAULT_DESCRIPTION =
  'Cổng thông tin nông sản OCOP và bản đồ số du lịch nông nghiệp tỉnh Lâm Đồng: tra cứu sản phẩm đạt sao, điểm tham quan và đường đi.'
export const DEFAULT_OG_IMAGE = '/assets/images/og-default.jpg'

export interface PageSeo {
  /** Tên trang, chưa kèm tên website. */
  title?: string
  /** Tiêu đề đầy đủ dùng nguyên văn (ví dụ trang chủ); ưu tiên hơn `title`. */
  fullTitle?: string
  description?: string
  /** Ảnh chia sẻ: đường dẫn tuyệt đối hoặc bắt đầu bằng `/`. */
  image?: string | null
  /** Đường dẫn chuẩn (canonical), mặc định là đường dẫn hiện tại không kèm query. */
  path?: string
  /** Trang riêng tư hoặc không có nội dung cho tìm kiếm. */
  noindex?: boolean
  jsonLd?: Record<string, unknown> | null
}

const JSON_LD_ID = 'seo-json-ld'

/** Rút gọn mô tả cho thẻ meta: gộp khoảng trắng, cắt tại ranh giới từ. */
export function clipDescription(text: string | null | undefined, limit = 160): string {
  const cleaned = (text ?? '').replace(/\s+/g, ' ').trim()
  if (cleaned.length <= limit) return cleaned
  return `${cleaned.slice(0, limit - 1).replace(/\s+\S*$/, '').replace(/[\s,.;:-]+$/, '')}…`
}

export function absoluteUrl(pathOrUrl: string): string {
  if (/^https?:\/\//i.test(pathOrUrl)) return pathOrUrl
  return `${window.location.origin}${pathOrUrl.startsWith('/') ? '' : '/'}${pathOrUrl}`
}

function setMeta(attribute: 'name' | 'property', key: string, content: string | null): void {
  const selector = `meta[${attribute}="${key}"]`
  let element = document.head.querySelector<HTMLMetaElement>(selector)
  if (content === null) {
    element?.remove()
    return
  }
  if (!element) {
    element = document.createElement('meta')
    element.setAttribute(attribute, key)
    document.head.appendChild(element)
  }
  element.setAttribute('content', content)
}

function setCanonical(href: string): void {
  let element = document.head.querySelector<HTMLLinkElement>('link[rel="canonical"]')
  if (!element) {
    element = document.createElement('link')
    element.setAttribute('rel', 'canonical')
    document.head.appendChild(element)
  }
  element.setAttribute('href', href)
}

function setJsonLd(data: Record<string, unknown> | null | undefined): void {
  const existing = document.getElementById(JSON_LD_ID)
  if (!data) {
    existing?.remove()
    return
  }
  const element = existing ?? document.createElement('script')
  element.id = JSON_LD_ID
  element.setAttribute('type', 'application/ld+json')
  // textContent không thực thi mã; "<" được thoát để dữ liệu không thể đóng thẻ script sớm.
  element.textContent = JSON.stringify(data).replace(/</g, '\\u003c')
  if (!existing) document.head.appendChild(element)
}

export function applyPageSeo(seo: PageSeo): void {
  const fullTitle = seo.fullTitle || (seo.title ? `${seo.title} | ${SITE_NAME}` : SITE_NAME)
  const description = seo.description || DEFAULT_DESCRIPTION
  const path = seo.path ?? window.location.pathname
  const canonical = absoluteUrl(path)
  const image = absoluteUrl(seo.image || DEFAULT_OG_IMAGE)

  document.title = fullTitle
  setMeta('name', 'description', description)
  setMeta('name', 'robots', seo.noindex ? 'noindex, nofollow' : null)
  setCanonical(canonical)

  setMeta('property', 'og:type', 'website')
  setMeta('property', 'og:site_name', SITE_NAME)
  setMeta('property', 'og:locale', 'vi_VN')
  setMeta('property', 'og:title', fullTitle)
  setMeta('property', 'og:description', description)
  setMeta('property', 'og:url', canonical)
  setMeta('property', 'og:image', image)
  setMeta('name', 'twitter:card', 'summary_large_image')
  setMeta('name', 'twitter:title', fullTitle)
  setMeta('name', 'twitter:description', description)
  setMeta('name', 'twitter:image', image)

  setJsonLd(seo.jsonLd)
}

/** Mô tả riêng cho các trang tĩnh; trang không có ở đây dùng mô tả mặc định. */
export const ROUTE_DESCRIPTIONS: Record<string, string> = {
  home: DEFAULT_DESCRIPTION,
  products:
    'Danh sách sản phẩm OCOP Lâm Đồng đạt 3 đến 5 sao: lọc theo nhóm, hạng sao, huyện và giá; xem đơn vị sản xuất và nơi mua.',
  locations:
    'Điểm du lịch nông nghiệp Lâm Đồng: đồi chè, vườn trái cây, vườn hoa, nông trại và farmstay kèm giờ mở cửa, giá vé và địa chỉ.',
  map: 'Bản đồ số du lịch nông nghiệp Lâm Đồng: tìm điểm tham quan gần bạn, xem sản phẩm OCOP tại điểm và chỉ đường.',
  news: 'Tin tức, sự kiện về chương trình OCOP và nông sản tỉnh Lâm Đồng từ cổng thông tin OCOP tỉnh.',
}

export function productJsonLd(product: {
  name: string
  description: string | null
  star: number | null
  price: number | null
  category: { name: string }
  subject: { name: string }
  images?: { image_url: string }[]
  primary_image_url: string | null
}, canonical: string): Record<string, unknown> {
  const image = product.primary_image_url ?? product.images?.[0]?.image_url
  const data: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'Product',
    name: product.name,
    description: clipDescription(product.description, 500),
    url: canonical,
    category: product.category.name,
    brand: { '@type': 'Brand', name: product.subject.name },
  }
  if (product.star) {
    data.additionalProperty = {
      '@type': 'PropertyValue',
      name: 'Xếp hạng OCOP',
      value: `${product.star} sao`,
    }
  }
  if (image) data.image = absoluteUrl(image)
  if (product.price && product.price > 0) {
    data.offers = {
      '@type': 'Offer',
      price: String(Math.round(product.price)),
      priceCurrency: 'VND',
      url: canonical,
    }
  }
  return data
}

export function locationJsonLd(location: {
  name: string
  description: string | null
  type_label: string
  address: string
  latitude: number
  longitude: number
  opening_hours: string | null
  primary_image_url: string | null
}, canonical: string): Record<string, unknown> {
  const data: Record<string, unknown> = {
    '@context': 'https://schema.org',
    '@type': 'TouristAttraction',
    name: location.name,
    description: clipDescription(location.description, 500),
    url: canonical,
    touristType: location.type_label,
    address: {
      '@type': 'PostalAddress',
      streetAddress: location.address,
      addressRegion: 'Lâm Đồng',
      addressCountry: 'VN',
    },
    geo: {
      '@type': 'GeoCoordinates',
      latitude: location.latitude,
      longitude: location.longitude,
    },
  }
  if (location.opening_hours) data.openingHours = location.opening_hours
  if (location.primary_image_url) data.image = absoluteUrl(location.primary_image_url)
  return data
}
