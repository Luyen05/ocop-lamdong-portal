// Ảnh chụp thật tại Đà Lạt, Lâm Đồng, dùng theo Giấy phép Unsplash (https://unsplash.com/license):
// được dùng miễn phí, kể cả thương mại, không bắt buộc ghi nguồn; cổng vẫn ghi tên tác giả để minh bạch.
// Đây là ảnh minh họa cảnh quan chung, không phải ảnh của một sản phẩm hay điểm du lịch cụ thể.
export interface SitePhoto {
  src: string
  alt: string
  author: string
  sourceUrl: string
  /** object-position khi cắt ảnh vào khung, mặc định ở giữa */
  position?: string
}

const base = '/assets/images/photos'

export const heroPhoto: SitePhoto = {
  src: `${base}/hero-binh-minh.webp`,
  alt: 'Bình minh trên đồng cỏ và đồi núi Đà Lạt',
  author: 'Pete Walls',
  sourceUrl: 'https://unsplash.com/photos/Fl3bY0hWXv4',
}

export const flowerFarmPhoto: SitePhoto = {
  src: `${base}/trai-hoa.webp`,
  alt: 'Người trồng hoa chăm sóc vườn hoa trong nhà kính ở Đà Lạt',
  author: 'Caitlin James',
  sourceUrl: 'https://unsplash.com/photos/y5_YGwhtIiY',
}

export const teaPhoto: SitePhoto = {
  src: `${base}/doi-che.webp`,
  alt: 'Cánh đồng chè xanh ở Đà Lạt',
  author: 'Tam Mai',
  sourceUrl: 'https://unsplash.com/photos/lNFjknOwqx0',
}

export const strawberryPhoto: SitePhoto = {
  src: `${base}/dau-tay.webp`,
  alt: 'Giỏ dâu tây tươi hái ở Đà Lạt',
  author: 'Yuliia Martsynkevych',
  sourceUrl: 'https://unsplash.com/photos/ejQ44jyhKAY',
}

export const hydrangeaPhoto: SitePhoto = {
  src: `${base}/cam-tu-cau.webp`,
  alt: 'Hoa cẩm tú cầu xanh nở ở Đà Lạt',
  author: 'Tuyen Vo',
  sourceUrl: 'https://unsplash.com/photos/VDblkjZ1mxA',
  position: '12% 45%',
}

export const homePhotos: SitePhoto[] = [heroPhoto, flowerFarmPhoto, teaPhoto, strawberryPhoto, hydrangeaPhoto]
