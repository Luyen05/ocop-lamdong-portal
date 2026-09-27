<script setup lang="ts">
import AppIcon from '@/components/ui/AppIcon.vue'

defineProps<{
  title: string
  subtitle: string
}>()
</script>

<template>
  <main class="auth-page">
    <div class="container py-4 py-lg-5">
      <RouterLink class="brand-link" to="/" aria-label="Về trang chủ">
        <span class="brand-mark">O</span>
        <span>
          <strong>OCOP Lâm Đồng</strong>
          <small>Cổng thông tin và bản đồ số</small>
        </span>
      </RouterLink>

      <section class="auth-card mt-4 mt-lg-5">
        <div class="auth-intro d-none d-lg-flex">
          <div>
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
  width: 2.75rem;
  height: 2.75rem;
  place-items: center;
  border-radius: 50%;
  background: var(--ocop-primary-700);
  color: var(--ocop-white);
  font-size: 1.55rem;
}

.auth-card {
  display: grid;
  max-width: 1040px;
  min-height: 620px;
  margin-inline: auto;
  overflow: hidden;
  border: 1px solid color-mix(in srgb, var(--ocop-primary-950) 10%, transparent);
  border-radius: 1.5rem;
  background: var(--ocop-card);
  box-shadow: 0 1.5rem 4rem color-mix(in srgb, var(--ocop-primary-950) 12%, transparent);
}

.auth-intro {
  flex-direction: column;
  justify-content: space-between;
  padding: 4rem;
  background:
    linear-gradient(160deg, color-mix(in srgb, var(--ocop-primary-950) 97%, transparent), color-mix(in srgb, var(--ocop-primary-700) 91%, transparent)),
    var(--ocop-primary-900);
  color: var(--ocop-white);
}

.auth-intro h1 {
  max-width: 29rem;
  margin: 1.25rem 0;
  font-weight: 750;
  font-size: clamp(2.2rem, 4vw, 3.5rem);
  line-height: 1.05;
}

.auth-intro p {
  max-width: 30rem;
  margin: 0;
  color: color-mix(in srgb, var(--ocop-white) 78%, transparent);
  line-height: 1.7;
}

.eyebrow {
  font-size: 0.76rem;
  font-weight: 700;
  letter-spacing: 0.13em;
  text-transform: uppercase;
}

.feature-list {
  display: grid;
  gap: 0.8rem;
  margin: 2rem 0 0;
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
  padding: 2rem;
}

.auth-form-copy h2 {
  margin: 0.65rem 0 0.5rem;
  color: var(--ocop-navy);
  font-size: clamp(1.8rem, 3vw, 2.35rem);
  font-weight: 750;
}

.auth-form-copy p {
  margin-bottom: 2rem;
  color: var(--ocop-slate);
}

@media (min-width: 992px) {
  .auth-card {
    grid-template-columns: 1.08fr 0.92fr;
  }

  .auth-form-panel {
    padding: 3.5rem;
  }
}
</style>
