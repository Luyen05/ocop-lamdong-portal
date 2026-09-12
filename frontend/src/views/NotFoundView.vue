<template>
  <main class="not-found-page">
    <section class="not-found-card" aria-labelledby="not-found-title">
      <span class="error-code">404</span>
      <h1 id="not-found-title">Không tìm thấy trang</h1>
      <p>Địa chỉ bạn mở không tồn tại hoặc nội dung đã được chuyển sang vị trí khác.</p>
      <div class="not-found-actions">
        <RouterLink class="primary-action" to="/">Về trang chủ</RouterLink>
        <RouterLink to="/san-pham">Xem sản phẩm OCOP</RouterLink>
      </div>
    </section>
  </main>
</template>

<style scoped>
.not-found-page {
  display: grid;
  min-height: 65vh;
  padding: 48px 16px;
  place-items: center;
  background: radial-gradient(circle at 50% 10%, rgb(164 244 207 / 40%), transparent 24rem), var(--ocop-surface);
}

.not-found-card {
  width: min(100%, 560px);
  padding: clamp(32px, 6vw, 56px);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-xl);
  background: #fff;
  box-shadow: 0 24px 50px rgb(15 23 43 / 10%);
  text-align: center;
}

.error-code { color: var(--ocop-primary-700); font-size: 13px; font-weight: 900; letter-spacing: .18em; }
h1 { margin: 12px 0 0; color: var(--ocop-navy); font-size: clamp(28px, 5vw, 38px); }
p { margin: 16px auto 0; color: var(--ocop-slate); line-height: 1.7; }
.not-found-actions { display: flex; margin-top: 28px; flex-wrap: wrap; justify-content: center; gap: 10px; }
.not-found-actions a { padding: 10px 18px; border: 1px solid var(--ocop-border); border-radius: var(--ocop-radius-md); color: var(--ocop-primary-900); font-size: 13px; font-weight: 700; text-decoration: none; }
.not-found-actions .primary-action { border-color: var(--ocop-primary-700); background: var(--ocop-primary-700); color: #fff; }
</style>
