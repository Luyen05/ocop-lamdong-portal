<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'

defineProps<{
  title: string
  subtitle: string
}>()
</script>

<template>
  <main class="auth-page">
    <div class="container auth-container">
      <RouterLink class="brand-link d-lg-none" to="/">
        <span class="brand-mark"><img src="/assets/brand/bieu-tuong-128.png" alt="" width="48" height="48" /></span>
        <span>
          <strong>LÂM ĐỒNG OCOP</strong>
          <small>Nông sản OCOP và du lịch nông nghiệp</small>
          <span class="visually-hidden">Về trang chủ</span>
        </span>
      </RouterLink>

      <section class="auth-card ocop-enter">
        <div class="auth-intro d-none d-lg-flex">
          <img class="auth-watermark" src="/assets/brand/bieu-tuong-512.png" alt="" width="512" height="512" aria-hidden="true" />
          <div class="auth-intro__top">
            <RouterLink class="auth-lockup" to="/">
              <span class="auth-lockup__mark"><img src="/assets/brand/bieu-tuong-128.png" alt="" width="52" height="52" /></span>
              <span class="auth-lockup__text">
                <strong>LÂM ĐỒNG OCOP</strong>
                <small>Nông sản OCOP và du lịch nông nghiệp</small>
                <span class="visually-hidden">Về trang chủ</span>
              </span>
            </RouterLink>
            <span class="eyebrow">Đặc sản từ cao nguyên</span>
            <h1>Kết nối sản phẩm OCOP với cộng đồng</h1>
            <p>
              Khám phá sản phẩm địa phương, điểm du lịch nông nghiệp và những câu
              chuyện đặc trưng của Lâm Đồng.
            </p>
          </div>
          <ul class="feature-list">
            <li><AppIcon name="checkCircle" :size="15" /> Thông tin được kiểm duyệt</li>
            <li><AppIcon name="checkCircle" :size="15" /> Trải nghiệm bản đồ trực quan</li>
            <li><AppIcon name="checkCircle" :size="15" /> Kết nối người dùng và chủ thể OCOP</li>
          </ul>
        </div>

        <div class="auth-form-panel">
          <div class="auth-form-copy">
            <span class="eyebrow text-success">Tài khoản OCOP</span>
            <h2>{{ title }}</h2>
            <p>{{ subtitle }}</p>
          </div>
          <slot />
        </div>
      </section>
    </div>
  </main>
</template>

<style scoped>
.auth-container {
  padding-block: clamp(0.75rem, 3vh, 3rem);
}

.auth-page {
  min-height: 100vh;
  background:
    radial-gradient(circle at 8% 8%, color-mix(in srgb, var(--ocop-sage-50) 85%, transparent), transparent 32rem),
    var(--ocop-surface);
}

.brand-link {
  display: inline-flex;
  align-items: center;
  gap: 0.75rem;
  color: var(--ocop-primary-950);
  text-decoration: none;
}

.brand-link span:last-child {
  display: grid;
  line-height: 1.15;
}

.brand-link strong {
  font-size: 1.05rem;
}

.brand-link small {
  margin-top: 0.25rem;
  color: var(--ocop-slate);
  font-size: var(--ocop-font-size-caption);
}

.brand-mark {
  display: grid;
  width: 48px;
  height: 48px;
  flex: 0 0 auto;
  place-items: center;
}

.brand-mark img {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.auth-card {
  display: grid;
  max-width: 1120px;
  min-height: min(620px, calc(100svh - 7rem));
  margin: clamp(0.75rem, 3.5vh, 3rem) auto 0;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--ocop-primary-950) 10%, transparent);
  border-radius: 1.5rem;
  background: var(--ocop-card);
  box-shadow: 0 1.5rem 4rem color-mix(in srgb, var(--ocop-primary-950) 12%, transparent);
}

.auth-intro {
  flex-direction: column;
  justify-content: space-between;
  padding: clamp(1.5rem, 5.5vh, 4rem) clamp(1.5rem, 4vw, 4rem);
  background:
    linear-gradient(160deg, color-mix(in srgb, var(--ocop-primary-950) 97%, transparent), color-mix(in srgb, var(--ocop-primary-700) 91%, transparent)),
    var(--ocop-primary-900);
  color: var(--ocop-white);
}

.auth-intro h1 {
  max-width: 29rem;
  margin: clamp(0.75rem, 2.5vh, 1.25rem) 0;
  font-weight: 750;
  font-size: clamp(1.9rem, min(3.6vw, 6.2vh), 3.5rem);
  line-height: 1.05;
}

.auth-intro p {
  max-width: 30rem;
  margin: 0;
  color: color-mix(in srgb, var(--ocop-white) 78%, transparent);
  line-height: 1.7;
}

.auth-intro {
  position: relative;
  overflow: hidden;
}

.auth-intro > * {
  position: relative;
}

/* Biểu tượng mờ chìm ở góc dưới, cùng tông với nền xanh đậm thay vì thẻ trắng nổi. */
.auth-intro > .auth-watermark {
  position: absolute;
  right: -12%;
  bottom: -14%;
  width: clamp(220px, 46vh, 400px);
  height: auto;
  opacity: 0.06;
  filter: brightness(0) invert(1);
  pointer-events: none;
}

.auth-intro__top {
  display: flex;
  flex-direction: column;
  align-items: flex-start;
}

.auth-intro__top > .eyebrow {
  display: block;
}

.auth-lockup {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: clamp(1rem, 4.5vh, 2.75rem);
  color: var(--ocop-white);
  text-decoration: none;
}

.auth-lockup__mark {
  display: grid;
  width: 52px;
  height: 52px;
  flex: 0 0 auto;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-white);
}

.auth-lockup__mark img {
  width: 44px;
  height: 44px;
  object-fit: contain;
}

.auth-lockup__text {
  display: grid;
  line-height: 1.15;
}

.auth-lockup__text strong {
  font-size: 1.05rem;
  letter-spacing: 0.02em;
}

.auth-lockup__text small {
  margin-top: 0.25rem;
  color: color-mix(in srgb, var(--ocop-white) 72%, transparent);
  font-size: var(--ocop-font-size-caption);
}

.eyebrow {
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

.feature-list {
  display: grid;
  gap: clamp(0.4rem, 1.4vh, 0.8rem);
  margin: clamp(1rem, 3vh, 2rem) 0 0;
  padding: 0;
  list-style: none;
}

.feature-list li {
  display: flex;
  align-items: center;
  gap: 0.65rem;
}

.feature-list .app-icon {
  color: var(--ocop-lime-200);
}

.auth-form-panel {
  align-self: center;
  padding: clamp(1.25rem, 3.5vh, 2rem) clamp(1.25rem, 3vw, 2rem);
}

.auth-form-copy h2 {
  margin: 0.65rem 0 0.5rem;
  color: var(--ocop-navy);
  font-size: clamp(1.6rem, min(3vw, 4.6vh), 2.35rem);
  font-weight: 750;
}

.auth-form-copy p {
  margin-bottom: clamp(0.75rem, 2.6vh, 2rem);
  color: var(--ocop-slate);
}

/* Màn hình thấp (laptop có thang hiển thị 125-150%): thu gọn ô nhập để cả biểu mẫu nằm trong một màn hình. */
@media (max-height: 880px) {
  .auth-form-panel :deep(.d-grid.gap-3) {
    gap: 0.65rem !important;
  }

  .auth-form-panel :deep(.form-control-lg),
  .auth-form-panel :deep(.input-group-lg > .form-control),
  .auth-form-panel :deep(.input-group-lg > .btn) {
    padding-block: 0.45rem;
    font-size: 1rem;
  }

  .auth-form-panel :deep(.btn-lg) {
    padding-block: 0.55rem;
    font-size: 1.05rem;
  }

  .auth-form-panel :deep(.form-label) {
    margin-bottom: 0.25rem;
  }

  .auth-form-panel :deep(.social-note) {
    margin-top: 0.4rem;
    font-size: 0.72rem;
    line-height: 1.3;
  }
}

/* Chỉ khi quá thấp mới bỏ ghi chú quyền riêng tư; chữ ở cột trái luôn giữ vì chiều cao thẻ do biểu mẫu quyết định. */
@media (max-height: 700px) {
  .auth-form-panel :deep(.social-note) {
    display: none;
  }
}

/* Màn hình thấp: cột trái chỉ gọn khoảng cách, không ẩn nội dung. */
@media (max-height: 880px) and (min-width: 992px) {
  .feature-list {
    gap: 0.3rem;
    margin-top: 0.75rem;
    font-size: 0.9rem;
  }
}

@media (max-height: 820px) and (min-width: 992px) {
  .auth-container {
    padding-block: 0.5rem;
  }

  .auth-card {
    margin-top: 0.5rem;
  }

  .auth-form-panel {
    padding-block: 1.25rem;
  }

  .auth-form-panel :deep(.d-grid.gap-3) {
    gap: 0.5rem !important;
  }

  .auth-form-panel :deep(.form-control-lg),
  .auth-form-panel :deep(.input-group-lg > .form-control),
  .auth-form-panel :deep(.input-group-lg > .btn) {
    padding-block: 0.35rem;
  }

  .auth-form-panel :deep(.btn-lg) {
    padding-block: 0.45rem;
  }
}

@media (min-width: 992px) {
  .auth-container {
    display: flex;
    min-height: 100svh;
    align-items: center;
    justify-content: center;
  }

  .auth-card {
    width: 100%;
    min-height: min(620px, calc(100svh - 2rem));
    margin: 0 auto;
    grid-template-columns: 1fr 1fr;
  }

  .auth-form-panel {
    padding: clamp(1.5rem, 5vh, 3.5rem) clamp(1.5rem, 3.5vw, 3.5rem);
  }
}
</style>
