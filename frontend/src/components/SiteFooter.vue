<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'

const stats = [
  { icon: 'award', value: '3–5 sao', label: 'Sản phẩm OCOP được kiểm duyệt', tone: 'green' },
  { icon: 'map', value: 'GIS', label: 'Bản đồ điểm đến nông nghiệp', tone: 'gold' },
  { icon: 'building', value: 'HTX', label: 'Không gian dành cho chủ thể', tone: 'blue' },
  { icon: 'map-pin', value: '124', label: 'Xã, phường & đặc khu Lâm Đồng', tone: 'purple' },
]
</script>

<template>
  <footer class="site-footer">
    <div class="site-content footer-inner">
      <div class="stat-grid" aria-label="Số liệu tổng quan">
        <div v-for="stat in stats" :key="stat.label" class="stat-card" :class="`tone-${stat.tone}`">
          <span class="stat-icon" aria-hidden="true"><AppIcon :name="stat.icon" :size="19" /></span>
          <span>
            <strong>{{ stat.value }}</strong>
            <small>{{ stat.label }}</small>
          </span>
        </div>
      </div>

      <div class="footer-grid">
        <section class="footer-brand" aria-labelledby="footer-brand-title">
          <h2 id="footer-brand-title">
            <span><img src="/assets/figma/home/icon-brand.svg" alt="" /></span>
            CỔNG OCOP LÂM ĐỒNG
          </h2>
          <p>Hệ thống Cổng thông tin trực tuyến quảng bá sản phẩm OCOP và Bản đồ số Du lịch Nông nghiệp tỉnh Lâm Đồng.</p>
          <address>
            <span><AppIcon name="map-pin" :size="14" /> Trung tâm Hành chính Tỉnh Lâm Đồng, 36 Trần Phú, TP. Đà Lạt</span>
            <span><AppIcon name="phone" :size="14" /> 0263.3822000 - 0263.3831200</span>
            <span><AppIcon name="mail" :size="14" /> sonnptnt@lamdong.gov.vn</span>
          </address>
        </section>

        <nav aria-labelledby="footer-system-title">
          <h2 id="footer-system-title">Danh Mục Hệ Thống</h2>
          <RouterLink to="/">Trang chủ</RouterLink>
          <RouterLink to="/san-pham">Tra cứu sản phẩm OCOP 3-5 sao</RouterLink>
          <RouterLink to="/diem-du-lich">Khám phá điểm du lịch nông nghiệp</RouterLink>
          <RouterLink to="/ban-do">Bản đồ số GIS &amp; Chỉ đường</RouterLink>
          <RouterLink to="/tin-tuc">Tin tức &amp; Sự kiện OCOP</RouterLink>
        </nav>

        <section aria-labelledby="footer-product-title">
          <h2 id="footer-product-title">Nhóm Sản Phẩm OCOP</h2>
          <p>• Nông sản tươi Đà Lạt - Lâm Đồng</p>
          <p>• Thực phẩm chế biến &amp; Mứt đặc sản</p>
          <p>• Đồ uống, Trà &amp; Cà phê Arabica Cầu Đất</p>
          <p>• Thảo dược, Atisô &amp; Đông trùng hạ thảo</p>
          <p>• Làng nghề &amp; Thủ công mỹ nghệ</p>
        </section>

        <aside class="info-card">
          <strong><AppIcon name="shieldCheck" :size="15" /> THÔNG TIN MINH BẠCH</strong>
          <p>Nội dung sản phẩm, chủ thể và điểm đến chỉ được công khai sau khi hoàn thành quy trình kiểm duyệt.</p>
          <span>Dữ liệu cập nhật theo phê duyệt</span>
        </aside>
      </div>

      <div class="footer-bottom">
        <span>© 2026 Cổng Thông Tin Quảng Bá OCOP &amp; Bản Đồ Số Du Lịch Nông Nghiệp Lâm Đồng.</span>
        <span>Phát triển với Vue 3 / FastAPI / PostGIS</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  padding: var(--ocop-space-12) 0 28px;
  background: var(--ocop-sidebar);
  color: var(--ocop-sidebar-muted);
}

.stat-grid {
  display: grid;
  padding-bottom: var(--ocop-space-8);
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: var(--ocop-space-4);
  border-bottom: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 12%, transparent);
}

.stat-card {
  display: flex;
  min-height: 82px;
  padding: var(--ocop-space-4);
  align-items: center;
  gap: var(--ocop-space-3);
  border: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 10%, transparent);
  border-radius: var(--ocop-radius-md);
  background: var(--ocop-sidebar-card);
}

.stat-icon {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--ocop-radius-sm);
  font-size: var(--ocop-font-size-title-sm);
}

.tone-green .stat-icon { background: color-mix(in srgb, var(--ocop-mint) 14%, transparent); color: var(--ocop-mint-300); }
.tone-gold .stat-icon { background: color-mix(in srgb, var(--ocop-gold) 14%, transparent); color: var(--ocop-gold-300); }
.tone-blue .stat-icon { background: color-mix(in srgb, var(--ocop-blue) 18%, transparent); color: var(--ocop-blue-300); }
.tone-purple .stat-icon { background: color-mix(in srgb, var(--ocop-tone-purple) 16%, transparent); color: var(--ocop-tone-purple-light); }

.stat-card strong,
.stat-card small {
  display: block;
}

.stat-card strong {
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-title-sm);
  line-height: 22px;
}

.stat-card small {
  margin-top: 2px;
  color: var(--ocop-text-on-dark-muted);
  font-size: var(--ocop-font-size-caption);
}

.footer-grid {
  display: grid;
  padding: 36px 0 var(--ocop-space-8);
  grid-template-columns: 1.15fr 1fr 1.1fr 1fr;
  gap: var(--ocop-space-12);
  border-bottom: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 12%, transparent);
}

.footer-grid h2 {
  margin: 0 0 var(--ocop-space-3);
  color: var(--ocop-surface-subtle);
  font-size: var(--ocop-font-size-caption);
  font-weight: 750;
  line-height: 18px;
}

.footer-brand h2 {
  display: flex;
  align-items: center;
  gap: 9px;
}

.footer-brand h2 > span {
  display: grid;
  width: 28px;
  height: 28px;
  place-items: center;
  border-radius: 7px;
  background: var(--ocop-primary-700);
}

.footer-brand h2 img {
  width: 16px;
  height: 16px;
}

.footer-grid p,
.footer-grid a,
.footer-grid address {
  margin: 0;
  color: var(--ocop-text-on-dark-muted);
  font-size: var(--ocop-font-size-caption);
  font-style: normal;
  line-height: 18px;
  text-decoration: none;
}

.footer-grid nav,
.footer-grid section {
  display: flex;
  flex-direction: column;
}

.footer-grid nav a {
  display: flex;
  min-height: 24px;
  align-items: center;
}

@media (pointer: coarse) {
  .footer-grid nav a {
    min-height: var(--ocop-control-md);
  }
}

.footer-grid a:hover {
  color: var(--ocop-mint-100);
}

.footer-brand > p {
  margin-bottom: var(--ocop-space-3);
}

.footer-brand address {
  display: grid;
  gap: 5px;
}

.footer-brand address span {
  display: flex;
  align-items: flex-start;
  gap: 7px;
}

.footer-brand address :deep(.app-icon) {
  margin-top: 2px;
  color: var(--ocop-mint-300);
}

.info-card {
  align-self: start;
  padding: var(--ocop-space-4);
  border: 1px solid color-mix(in srgb, var(--ocop-neutral-400) 14%, transparent);
  border-radius: var(--ocop-radius-md);
  background: color-mix(in srgb, var(--ocop-sidebar-card) 88%, var(--ocop-white));
}

.info-card strong {
  display: flex;
  align-items: center;
  gap: 6px;
  color: var(--ocop-mint-400);
  font-size: var(--ocop-font-size-caption);
}

.info-card p {
  margin: 10px 0;
}

.info-card span {
  display: block;
  padding: 7px 10px;
  border-radius: 6px;
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
  font-size: var(--ocop-font-size-caption);
  font-weight: 700;
  text-align: center;
}

.footer-bottom {
  display: flex;
  padding-top: var(--ocop-space-6);
  justify-content: space-between;
  gap: var(--ocop-space-5);
  color: var(--ocop-text-on-dark-muted);
  font-size: var(--ocop-font-size-caption);
}

@media (max-width: 991.98px) {
  .stat-grid,
  .footer-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .footer-grid {
    gap: var(--ocop-space-8);
  }
}

@media (max-width: 575.98px) {
  .site-footer {
    padding-top: var(--ocop-space-8);
  }

  .stat-grid,
  .footer-grid {
    grid-template-columns: 1fr;
  }

  .stat-grid {
    gap: 10px;
  }

  .footer-grid {
    gap: 28px;
  }

  .footer-bottom {
    flex-direction: column;
  }
}
</style>
