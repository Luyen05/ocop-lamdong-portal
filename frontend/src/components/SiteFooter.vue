<script setup lang="ts">
const stats = [
  { icon: '♕', value: '185+', label: 'Sản phẩm OCOP 3 - 5 sao', tone: 'green' },
  { icon: '⌖', value: '68+', label: 'Điểm du lịch nông nghiệp', tone: 'gold' },
  { icon: '♢', value: '120+', label: 'Chủ thể & HTX đăng ký', tone: 'blue' },
  { icon: '◎', value: '12', label: 'Huyện & Thành phố tích hợp', tone: 'purple' },
]
</script>

<template>
  <footer class="site-footer">
    <div class="site-content footer-inner">
      <div class="stat-grid" aria-label="Số liệu tổng quan">
        <div v-for="stat in stats" :key="stat.label" class="stat-card" :class="`tone-${stat.tone}`">
          <span class="stat-icon" aria-hidden="true">{{ stat.icon }}</span>
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
            <span>⌖ Trung tâm Hành chính Tỉnh Lâm Đồng, 36 Trần Phú, TP. Đà Lạt</span>
            <span>☎ 0263.3822000 - 0263.3831200</span>
            <span>✉ sonnptnt@lamdong.gov.vn</span>
          </address>
        </section>

        <nav aria-labelledby="footer-system-title">
          <h2 id="footer-system-title">Danh Mục Hệ Thống</h2>
          <RouterLink to="/">Trang chủ</RouterLink>
          <RouterLink to="/san-pham">Tra cứu sản phẩm OCOP 3-5 sao</RouterLink>
          <a href="/#diem-du-lich">Khám phá điểm du lịch nông nghiệp</a>
          <a href="/#ban-do">Bản đồ số GIS &amp; Chỉ đường</a>
          <a href="/#tin-tuc">Tin tức &amp; Sự kiện OCOP</a>
        </nav>

        <section aria-labelledby="footer-product-title">
          <h2 id="footer-product-title">Nhóm Sản Phẩm OCOP</h2>
          <p>• Nông sản tươi Đà Lạt - Lâm Đồng</p>
          <p>• Thực phẩm chế biến &amp; Mứt đặc sản</p>
          <p>• Đồ uống, Trà &amp; Cà phê Arabica Cầu Đất</p>
          <p>• Thảo dược, Atisô &amp; Đông trùng hạ thảo</p>
          <p>• Làng nghề &amp; Thủ công mỹ nghệ</p>
        </section>

        <aside class="capstone-card">
          <strong>♙ ĐỒ ÁN TỐT NGHIỆP ĐẠI HỌC</strong>
          <p>Thiết kế giao diện UI/UX &amp; Frontend Architecture chuẩn Material Design 3 tích hợp bản đồ số GIS.</p>
          <span>Mô Tả Liệu Đồ Án (12 Mục)</span>
        </aside>
      </div>

      <div class="footer-bottom">
        <span>© 2026 Cổng Thông Tin Quảng Bá OCOP &amp; Bản Đồ Số Du Lịch Nông Nghiệp Lâm Đồng.</span>
        <span>Đồ án tốt nghiệp CNTT ♥ Vue 3 / FastAPI - PostGIS</span>
      </div>
    </div>
  </footer>
</template>

<style scoped>
.site-footer {
  padding: 48px 0 28px;
  background: #101a30;
  color: #91a0b6;
}

.stat-grid {
  display: grid;
  padding-bottom: 32px;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 16px;
  border-bottom: 1px solid rgb(148 163 184 / 12%);
}

.stat-card {
  display: flex;
  min-height: 82px;
  padding: 16px;
  align-items: center;
  gap: 12px;
  border: 1px solid rgb(148 163 184 / 10%);
  border-radius: var(--ocop-radius-md);
  background: #1a263c;
}

.stat-icon {
  display: grid;
  width: 40px;
  height: 40px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: var(--ocop-radius-sm);
  font-size: 18px;
}

.tone-green .stat-icon { background: rgb(0 212 146 / 12%); color: #34d399; }
.tone-gold .stat-icon { background: rgb(255 185 0 / 12%); color: #fbbf24; }
.tone-blue .stat-icon { background: rgb(0 132 209 / 14%); color: #38bdf8; }
.tone-purple .stat-icon { background: rgb(147 51 234 / 14%); color: #c084fc; }

.stat-card strong,
.stat-card small {
  display: block;
}

.stat-card strong {
  color: #fff;
  font-size: 18px;
  line-height: 22px;
}

.stat-card small {
  margin-top: 2px;
  color: #7f8da4;
  font-size: 10px;
}

.footer-grid {
  display: grid;
  padding: 36px 0 32px;
  grid-template-columns: 1.15fr 1fr 1.1fr 1fr;
  gap: 48px;
  border-bottom: 1px solid rgb(148 163 184 / 12%);
}

.footer-grid h2 {
  margin: 0 0 12px;
  color: #f8fafc;
  font-size: 12px;
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
  color: #8290a6;
  font-size: 10px;
  font-style: normal;
  line-height: 18px;
  text-decoration: none;
}

.footer-grid nav,
.footer-grid section {
  display: flex;
  flex-direction: column;
}

.footer-grid a:hover {
  color: #d0fae5;
}

.footer-brand > p {
  margin-bottom: 12px;
}

.footer-brand address {
  display: grid;
  gap: 2px;
}

.capstone-card {
  align-self: start;
  padding: 16px;
  border: 1px solid rgb(148 163 184 / 14%);
  border-radius: var(--ocop-radius-md);
  background: #1b2940;
}

.capstone-card strong {
  color: #fbbf24;
  font-size: 10px;
}

.capstone-card p {
  margin: 10px 0;
}

.capstone-card span {
  display: block;
  padding: 7px 10px;
  border-radius: 6px;
  background: var(--ocop-primary-700);
  color: #fff;
  font-size: 10px;
  font-weight: 700;
  text-align: center;
}

.footer-bottom {
  display: flex;
  padding-top: 24px;
  justify-content: space-between;
  gap: 20px;
  color: #65748b;
  font-size: 9px;
}

@media (max-width: 991.98px) {
  .stat-grid,
  .footer-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }

  .footer-grid {
    gap: 32px;
  }
}

@media (max-width: 575.98px) {
  .site-footer {
    padding-top: 32px;
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
