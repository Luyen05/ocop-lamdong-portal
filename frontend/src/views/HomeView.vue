<template>
  <main>
    <section class="hero-section">
      <div class="container hero-grid">
        <div>
          <span class="hero-eyebrow">Tinh hoa bản địa · Giá trị bền vững</span>
          <h1>Khám phá sản phẩm OCOP Lâm Đồng</h1>
          <p>
            Cổng thông tin kết nối người dân, du khách và các chủ thể OCOP qua sản
            phẩm đặc trưng, điểm đến nông nghiệp và bản đồ số trực quan.
          </p>
          <div class="d-flex flex-wrap gap-2 mt-4">
            <a class="btn btn-success btn-lg px-4" href="#san-pham">Khám phá ngay</a>
            <RouterLink class="btn btn-outline-success btn-lg px-4" to="/dang-ky">
              Tạo tài khoản
            </RouterLink>
          </div>
        </div>

        <div class="hero-panel" aria-label="Thông tin nổi bật">
          <span class="panel-badge">OCOP Lâm Đồng</span>
          <strong>Nông sản chất lượng từ miền đất cao nguyên</strong>
          <p>Dữ liệu sẽ được kết nối từ API sản phẩm trong module tiếp theo.</p>
        </div>
      </div>
    </section>

    <section id="san-pham" class="container py-5 text-center">
      <span class="section-label">Sắp triển khai</span>
      <h2 class="mt-2">Sản phẩm OCOP nổi bật</h2>
      <p class="mx-auto text-secondary section-copy">
        Khu vực này sẽ hiển thị dữ liệu sản phẩm đã được duyệt từ backend, có tìm
        kiếm, bộ lọc và phân trang.
      </p>
    </section>

    <section id="dia-diem" class="placeholder-band py-5 text-center">
      <div class="container">
        <span class="section-label">Bản đồ số</span>
        <h2 class="mt-2">Điểm đến nông nghiệp Lâm Đồng</h2>
      </div>
    </section>
  </main>
</template>

<style scoped>
.hero-section {
  padding: clamp(4.5rem, 10vw, 8rem) 0;
  background:
    radial-gradient(circle at 78% 30%, rgb(197 222 159 / 70%), transparent 27rem),
    linear-gradient(145deg, #f8faf2, #edf4e5);
}

.hero-grid {
  display: grid;
  align-items: center;
  gap: 3rem;
}

.hero-eyebrow,
.section-label {
  color: #2f6f3e;
  font-size: 0.78rem;
  font-weight: 750;
  letter-spacing: 0.11em;
  text-transform: uppercase;
}

.hero-section h1 {
  max-width: 47rem;
  margin: 1rem 0 1.25rem;
  color: #18351f;
  font-family: "Segoe UI", Arial, sans-serif;
  font-weight: 800;
  font-size: clamp(2.6rem, 7vw, 5.2rem);
  line-height: 1.02;
}

.hero-section > .container > div > p {
  max-width: 42rem;
  color: #5f6f63;
  font-size: 1.08rem;
  line-height: 1.75;
}

.hero-panel {
  display: grid;
  min-height: 24rem;
  align-content: end;
  padding: 2rem;
  border-radius: 1.5rem;
  background: linear-gradient(160deg, #173a22, #3d7a49);
  color: #fff;
  box-shadow: 0 1.5rem 3.5rem rgb(31 76 40 / 18%);
}

.hero-panel strong {
  max-width: 25rem;
  margin: 1rem 0;
  font-family: "Segoe UI", Arial, sans-serif;
  font-size: clamp(1.8rem, 4vw, 2.6rem);
  line-height: 1.15;
}

.hero-panel p {
  margin: 0;
  color: rgb(255 255 255 / 72%);
}

.panel-badge {
  width: max-content;
  padding: 0.4rem 0.8rem;
  border: 1px solid rgb(255 255 255 / 35%);
  border-radius: 999px;
  font-size: 0.75rem;
  font-weight: 700;
}

.section-copy {
  max-width: 42rem;
}

.placeholder-band {
  background: #173a22;
  color: #fff;
}

@media (min-width: 992px) {
  .hero-grid {
    grid-template-columns: 1.2fr 0.8fr;
  }
}
</style>
