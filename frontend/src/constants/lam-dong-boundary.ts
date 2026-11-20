/**
 * Tọa độ ranh giới hành chính tỉnh Lâm Đồng (đã tối ưu số đỉnh để vẽ mượt trên Leaflet và SVG).
 * Thứ tự mỗi cặp trong mảng là [vĩ độ (lat), kinh độ (lng)] theo chuẩn Leaflet LatLngTuple,
 * nằm hoàn toàn trong khung bao LAM_DONG_BOUNDS (lat 10.2..12.6, lng 106.6..109.0).
 */
export const LAM_DONG_BOUNDARY_LATLNGS: ReadonlyArray<[number, number]> = [
  // Cực Bắc - Đam Rông & Lạc Dương (giáp Đắk Lắk)
  [12.375, 108.165],
  [12.345, 108.285],
  [12.392, 108.415],
  [12.368, 108.535],
  [12.312, 108.625],
  // Phía Đông Bắc & Đông - Lạc Dương & Đơn Dương (giáp Khánh Hòa, Ninh Thuận)
  [12.225, 108.695],
  [12.115, 108.712],
  [12.015, 108.678],
  [11.915, 108.655],
  [11.815, 108.638],
  [11.715, 108.585],
  [11.635, 108.545],
  // Phía Đông Nam & Nam - Đơn Dương, Đức Trọng, Di Linh (giáp Ninh Thuận, Bình Thuận)
  [11.585, 108.455],
  [11.525, 108.355],
  [11.465, 108.265],
  [11.415, 108.175],
  [11.385, 108.065],
  [11.425, 107.965],
  [11.395, 107.855],
  // Phía Tây Nam - Bảo Lâm, Bảo Lộc, Đạ Huoai, Đạ Tẻh, Cát Tiên (giáp Bình Thuận, Đồng Nai, Bình Phước)
  [11.365, 107.735],
  [11.315, 107.615],
  [11.335, 107.495],
  [11.415, 107.395],
  [11.495, 107.315],
  [11.575, 107.245],
  [11.685, 107.235],
  [11.765, 107.325],
  // Phía Tây & Tây Bắc - Cát Tiên, Bảo Lâm, Di Linh, Lâm Hà, Đam Rông (giáp Đắk Nông)
  [11.825, 107.455],
  [11.785, 107.585],
  [11.845, 107.685],
  [11.925, 107.765],
  [11.985, 107.885],
  [12.065, 107.965],
  [12.165, 108.015],
  [12.275, 108.085],
  [12.375, 108.165],
]

/**
 * Khung mặt nạ bao ngoài để tạo hiệu ứng Spotlight (làm dịu vùng ngoài tỉnh Lâm Đồng,
 * tôn nổi bật vùng lãnh thổ Lâm Đồng giống phong cách bản đồ văn hóa cmap.vn).
 */
export const LAM_DONG_OUTER_MASK_LATLNGS: ReadonlyArray<[number, number]> = [
  [25.0, 98.0],
  [25.0, 118.0],
  [2.0, 118.0],
  [2.0, 98.0],
]

/** Các tâm địa bàn tiêu biểu trong tỉnh Lâm Đồng để hiển thị nhãn định hướng trên bản đồ xem trước. */
export interface ProvinceLandmark {
  name: string
  latitude: number
  longitude: number
  isCapital?: boolean
}

export const LAM_DONG_LANDMARKS: ReadonlyArray<ProvinceLandmark> = [
  { name: 'TP. Đà Lạt', latitude: 11.9404, longitude: 108.4583, isCapital: true },
  { name: 'TP. Bảo Lộc', latitude: 11.5479, longitude: 107.8077, isCapital: true },
  { name: 'Lạc Dương', latitude: 12.105, longitude: 108.435 },
  { name: 'Đức Trọng', latitude: 11.735, longitude: 108.375 },
  { name: 'Đơn Dương', latitude: 11.775, longitude: 108.545 },
  { name: 'Lâm Hà', latitude: 11.865, longitude: 108.165 },
  { name: 'Di Linh', latitude: 11.585, longitude: 108.075 },
  { name: 'Bảo Lâm', latitude: 11.685, longitude: 107.755 },
]

/**
 * Chuyển chuỗi tọa độ ranh giới Lâm Đồng sang chuỗi SVG path `d="M ... Z"`
 * trong hệ tọa độ viewBox (width x height) với khoảng đệm padding.
 */
export function buildLamDongSvgPath(width = 560, height = 320, paddingX = 48, paddingY = 24): string {
  const lats = LAM_DONG_BOUNDARY_LATLNGS.map(([lat]) => lat)
  const lngs = LAM_DONG_BOUNDARY_LATLNGS.map(([, lng]) => lng)
  const minLat = Math.min(...lats)
  const maxLat = Math.max(...lats)
  const minLng = Math.min(...lngs)
  const maxLng = Math.max(...lngs)
  const latSpan = maxLat - minLat || 1
  const lngSpan = maxLng - minLng || 1
  const drawW = width - paddingX * 2
  const drawH = height - paddingY * 2

  const points = LAM_DONG_BOUNDARY_LATLNGS.map(([lat, lng]) => {
    const x = paddingX + ((lng - minLng) / lngSpan) * drawW
    const y = paddingY + ((maxLat - lat) / latSpan) * drawH
    return `${x.toFixed(1)},${y.toFixed(1)}`
  })
  return `M ${points.join(' L ')} Z`
}
