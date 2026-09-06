<script setup lang="ts">
import { mapMarkerFixtures } from '@/data/home-fixtures'

const markerIcons = {
  'ocop-5': '✨',
  'ocop-4': '⭐',
  tourism: '🏡',
}
</script>

<template>
  <section id="ban-do" class="map-section" aria-labelledby="map-title">
    <div class="section-heading">
      <div>
        <span class="eyebrow">Hệ Thống Bản Đồ Tọa Độ PostGIS</span>
        <h2 id="map-title">Xem Nhanh Bản Đồ Số Nông Sản Lâm Đồng</h2>
        <p>Bản đồ định vị GPS các chủ thể OCOP, đồi chè và trang trại tại Lâm Đồng</p>
      </div>
      <span class="demo-label">Dữ liệu minh họa</span>
    </div>

    <div class="map-preview" role="img" aria-label="Bản đồ minh họa các điểm OCOP và du lịch Lâm Đồng">
      <div class="map-grid" aria-hidden="true" />
      <span class="region-label label-da-lat">Đà Lạt</span>
      <span class="region-label label-bao-loc">Bảo Lộc</span>
      <span class="region-label label-duc-trong">Đức Trọng</span>

      <span
        v-for="marker in mapMarkerFixtures"
        :key="marker.id"
        class="map-marker"
        :class="`marker-${marker.type}`"
        :style="{ left: `${marker.x}%`, top: `${marker.y}%` }"
        :title="marker.label"
      >
        {{ markerIcons[marker.type] }}
        <span>{{ marker.label }}</span>
      </span>

      <div class="map-controls" aria-hidden="true">
        <span>+</span>
        <span>−</span>
      </div>

      <div class="map-legend">
        <strong>Chú giải bản đồ OCOP:</strong>
        <span>✨ OCOP 5 Sao</span>
        <span>⭐ OCOP 4 Sao</span>
        <span>🏡 Điểm Du Lịch Canh Nông</span>
      </div>
    </div>

    <button class="map-button" type="button" disabled title="Bản đồ tương tác sẽ được triển khai ở module GIS">
      Mở Bản Đồ Toàn Màn Hình →
    </button>
  </section>
</template>

<style scoped>
.map-section {
  padding-top: 48px;
}

.section-heading {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 16px;
}

.eyebrow {
  color: var(--ocop-blue);
  font-size: 11px;
  font-weight: 800;
  line-height: 16px;
  text-transform: uppercase;
}

h2 {
  margin: 4px 0 0;
  color: var(--ocop-navy);
  font-size: 20px;
  font-weight: 800;
  letter-spacing: -0.5px;
  line-height: 28px;
}

.section-heading p {
  margin: 2px 0 0;
  color: var(--ocop-slate);
  font-size: 12px;
}

.demo-label {
  flex: 0 0 auto;
  padding: 5px 9px;
  border: 1px solid #bfdbfe;
  border-radius: 999px;
  background: #eff6ff;
  color: #1d4ed8;
  font-size: 10px;
  font-weight: 700;
}

.map-preview {
  position: relative;
  min-height: 430px;
  margin-top: 16px;
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: var(--ocop-radius-lg);
  background:
    radial-gradient(circle at 70% 18%, rgb(153 215 190 / 65%), transparent 20%),
    radial-gradient(circle at 27% 68%, rgb(186 216 154 / 70%), transparent 28%),
    #e9f2e7;
  box-shadow: inset 0 0 50px rgb(71 101 77 / 8%);
}

.map-grid {
  position: absolute;
  inset: -40px;
  opacity: 0.55;
  background-image:
    linear-gradient(28deg, transparent 45%, #fff 46%, #fff 49%, transparent 50%),
    linear-gradient(105deg, transparent 47%, #c7d9ee 48%, #c7d9ee 51%, transparent 52%),
    linear-gradient(0deg, rgb(100 116 139 / 12%) 1px, transparent 1px),
    linear-gradient(90deg, rgb(100 116 139 / 12%) 1px, transparent 1px);
  background-size: 210px 160px, 240px 190px, 42px 42px, 42px 42px;
  transform: rotate(-4deg) scale(1.08);
}

.region-label {
  position: absolute;
  color: #64748b;
  font-size: 12px;
  font-weight: 700;
  letter-spacing: 0.06em;
  text-transform: uppercase;
}

.label-da-lat { top: 42%; left: 48%; }
.label-bao-loc { top: 82%; left: 20%; }
.label-duc-trong { top: 69%; left: 54%; }

.map-marker {
  position: absolute;
  z-index: 2;
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  border: 3px solid #fff;
  border-radius: 50% 50% 50% 8px;
  box-shadow: 0 5px 10px rgb(15 23 43 / 24%);
  color: #fff;
  transform: translate(-50%, -50%) rotate(-45deg);
}

.map-marker > span {
  position: absolute;
  left: 31px;
  display: none;
  width: max-content;
  max-width: 160px;
  padding: 5px 8px;
  border-radius: 6px;
  background: rgb(15 23 43 / 88%);
  color: #fff;
  font-size: 10px;
  transform: rotate(45deg);
}

.map-marker:hover > span {
  display: block;
}

.marker-ocop-5 { background: #e11d48; }
.marker-ocop-4 { background: #f59e0b; }
.marker-tourism { background: var(--ocop-primary-700); }

.map-marker:not(:hover) {
  font-size: 13px;
}

.map-controls {
  position: absolute;
  z-index: 2;
  top: 16px;
  left: 16px;
  display: grid;
  overflow: hidden;
  border: 1px solid #cbd5e1;
  border-radius: var(--ocop-radius-sm);
  background: #fff;
  box-shadow: 0 4px 10px rgb(15 23 43 / 10%);
}

.map-controls span {
  display: grid;
  width: 34px;
  height: 34px;
  place-items: center;
  color: var(--ocop-navy);
  font-size: 20px;
  font-weight: 600;
}

.map-controls span + span {
  border-top: 1px solid var(--ocop-border);
}

.map-legend {
  position: absolute;
  z-index: 2;
  right: 16px;
  bottom: 16px;
  display: flex;
  padding: 10px 12px;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  border: 1px solid rgb(226 232 240 / 90%);
  border-radius: var(--ocop-radius-sm);
  background: rgb(255 255 255 / 92%);
  box-shadow: 0 5px 12px rgb(15 23 43 / 10%);
  color: #45556c;
  font-size: 10px;
}

.map-legend strong {
  color: var(--ocop-navy);
}

.map-button {
  display: block;
  margin: 12px 0 0 auto;
  padding: 9px 14px;
  border: 1px solid var(--ocop-primary-700);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-primary-700);
  color: #fff;
  font-size: 11px;
  font-weight: 700;
  opacity: 0.72;
}

@media (max-width: 767.98px) {
  .section-heading {
    align-items: flex-start;
  }

  .section-heading p {
    max-width: 250px;
  }

  .map-preview {
    min-height: 390px;
  }

  .map-legend {
    right: 10px;
    bottom: 10px;
    left: 10px;
  }

  .map-marker > span {
    display: none !important;
  }
}
</style>
