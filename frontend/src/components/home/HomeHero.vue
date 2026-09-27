<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import { useRouter } from 'vue-router'

import AppIcon from '@/components/ui/AppIcon.vue'
import { heroPhoto } from '@/constants/photos'

type SearchMode = 'products' | 'locations'

interface SearchModeOption {
  value: SearchMode
  label: string
  icon: string
  placeholder: string
  inputLabel: string
  submitLabel: string
}

const modes: SearchModeOption[] = [
  {
    value: 'products',
    label: 'Sản phẩm',
    icon: 'package',
    placeholder: 'Atiso, cà phê Cầu Đất, dâu tây...',
    inputLabel: 'Tên sản phẩm cần tìm',
    submitLabel: 'Tìm sản phẩm',
  },
  {
    value: 'locations',
    label: 'Điểm du lịch',
    icon: 'map-pin',
    placeholder: 'Đồi chè, vườn dâu, nông trại...',
    inputLabel: 'Tên điểm du lịch cần tìm',
    submitLabel: 'Tìm điểm du lịch',
  },
]

const router = useRouter()
// Ảnh nền thật; nếu chưa có file hoặc tải lỗi thì dùng phong cảnh vẽ SVG bên dưới.
const photoFailed = ref(false)
const search = ref('')
const mode = ref<SearchMode>('products')
const modeButtons = ref<HTMLButtonElement[]>([])
const activeMode = computed(() => modes.find((item) => item.value === mode.value) ?? modes[0])

async function submitSearch(): Promise<void> {
  const keyword = search.value.trim()
  await router.push({ name: mode.value, query: keyword ? { search: keyword } : {} })
}

// Toggle group: phím mũi tên chuyển lựa chọn, focus đi theo (roving focus).
async function onModeKeydown(event: KeyboardEvent, index: number): Promise<void> {
  const step = event.key === 'ArrowRight' || event.key === 'ArrowDown' ? 1
    : event.key === 'ArrowLeft' || event.key === 'ArrowUp' ? -1 : 0
  if (!step) return
  event.preventDefault()
  const next = (index + step + modes.length) % modes.length
  mode.value = modes[next].value
  await nextTick()
  modeButtons.value[next]?.focus()
}
</script>

<template>
  <section class="home-hero" aria-labelledby="home-hero-title">
    <!-- Phong cảnh minh họa Lâm Đồng: núi sương, rừng thông, đồi chè, hoa dã quỳ. Nền cho khung kính mờ. -->
    <svg class="hero-scene" viewBox="0 0 1440 640" preserveAspectRatio="xMidYMax slice" aria-hidden="true" focusable="false">
      <defs>
        <linearGradient id="hero-sky" x1="0" y1="0" x2="0" y2="1">
          <stop class="sky-top" offset="0" />
          <stop class="sky-mid" offset="0.55" />
          <stop class="sky-horizon" offset="1" />
        </linearGradient>
        <radialGradient id="hero-sun-glow">
          <stop class="glow-core" offset="0" />
          <stop class="glow-edge" offset="1" />
        </radialGradient>
        <filter id="hero-mist" x="-10%" y="-50%" width="120%" height="200%">
          <feGaussianBlur stdDeviation="14" />
        </filter>
      </defs>
      <rect width="1440" height="640" fill="url(#hero-sky)" />
      <circle cx="1080" cy="250" r="190" fill="url(#hero-sun-glow)" />
      <circle class="sun" cx="1080" cy="250" r="64" />
      <path class="ridge-far" d="M0 360 L120 300 L220 330 L340 250 L470 320 L600 270 L720 330 L850 240 L980 300 L1100 230 L1230 300 L1340 260 L1440 290 L1440 640 L0 640 Z" />
      <ellipse class="mist" cx="420" cy="360" rx="520" ry="34" filter="url(#hero-mist)" />
      <path class="ridge-mid" d="M0 420 C120 380 200 400 300 360 S520 330 620 380 S840 400 960 350 S1200 330 1300 370 S1400 380 1440 360 L1440 640 L0 640 Z" />
      <g class="pines">
        <path d="M1010 372 l14 -40 l14 40 Z M1036 376 l18 -52 l18 52 Z M1066 370 l12 -34 l12 34 Z M1188 360 l16 -46 l16 46 Z M1214 366 l12 -34 l12 34 Z M1236 364 l18 -50 l18 50 Z" />
        <path d="M150 406 l14 -40 l14 40 Z M176 410 l18 -52 l18 52 Z M206 404 l12 -34 l12 34 Z" />
      </g>
      <ellipse class="mist mist-low" cx="1100" cy="420" rx="480" ry="30" filter="url(#hero-mist)" />
      <path class="tea-hill" d="M0 500 C160 440 320 450 480 470 S820 520 1000 470 S1300 430 1440 460 L1440 640 L0 640 Z" />
      <g class="tea-rows">
        <path d="M40 520 C220 470 400 480 560 500 S880 540 1060 500 S1320 470 1440 490" />
        <path d="M0 552 C200 505 380 515 540 532 S880 572 1060 532 S1320 502 1440 522" />
        <path d="M0 586 C200 540 380 550 540 566 S880 604 1060 566 S1320 536 1440 556" />
      </g>
      <path class="field" d="M0 600 C240 580 520 596 760 588 S1200 578 1440 594 L1440 640 L0 640 Z" />
      <g class="flowers">
        <g transform="translate(1180 560)"><circle class="petal" r="11" /><circle class="core" r="4" /></g>
        <g transform="translate(1216 578)"><circle class="petal" r="8" /><circle class="core" r="3" /></g>
        <g transform="translate(1250 556)"><circle class="petal" r="10" /><circle class="core" r="3.5" /></g>
        <g transform="translate(1292 582)"><circle class="petal" r="12" /><circle class="core" r="4.5" /></g>
        <g transform="translate(1336 560)"><circle class="petal" r="8" /><circle class="core" r="3" /></g>
        <g transform="translate(1380 590)"><circle class="petal" r="10" /><circle class="core" r="3.5" /></g>
        <g transform="translate(920 596)"><circle class="petal" r="7" /><circle class="core" r="2.5" /></g>
        <g transform="translate(956 606)"><circle class="petal" r="9" /><circle class="core" r="3" /></g>
      </g>
    </svg>
    <img
      v-if="!photoFailed"
      class="hero-photo"
      :src="heroPhoto.src"
      :alt="heroPhoto.alt"
      fetchpriority="high"
      @error="photoFailed = true"
    />
    <div v-if="!photoFailed" class="hero-shade" aria-hidden="true" />

    <div class="site-content hero-inner">
      <div class="hero-glass">
        <h1 id="home-hero-title">
          Nông sản OCOP <span class="hero-mark">đạt sao</span> và du lịch nông nghiệp Lâm Đồng
        </h1>
        <p class="hero-lead">
          Tra cứu sản phẩm đã được phê duyệt, tìm nhà vườn, điểm du lịch và chỉ đường trên bản đồ số.
        </p>


        <div class="mode-group" role="radiogroup" aria-label="Chọn loại nội dung cần tìm">
          <button
            v-for="(item, index) in modes"
            :key="item.value"
            ref="modeButtons"
            class="mode-option"
            type="button"
            role="radio"
            :aria-checked="mode === item.value"
            :tabindex="mode === item.value ? 0 : -1"
            @click="mode = item.value"
            @keydown="onModeKeydown($event, index)"
          >
            <AppIcon :name="item.icon" :size="16" />
            {{ item.label }}
          </button>
        </div>

        <form class="hero-search" role="search" @submit.prevent="submitSearch">
          <label class="search-field">
            <span class="visually-hidden">{{ activeMode.inputLabel }}</span>
            <AppIcon name="search" :size="18" />
            <input v-model="search" type="search" :placeholder="activeMode.placeholder" />
          </label>
          <button class="ocop-btn-accent" type="submit">
            <AppIcon name="search" :size="16" />
            {{ activeMode.submitLabel }}
          </button>
        </form>


        <!-- Progressive disclosure: giải thích OCOP cho du khách lần đầu, không chiếm chỗ của người đã biết. -->
        <details class="ocop-explainer">
          <summary>
            <AppIcon name="award" :size="16" />
            OCOP là gì?
          </summary>
          <p>
            OCOP (Mỗi xã một sản phẩm) là chương trình đánh giá, phân hạng sản phẩm đặc trưng của địa phương.
            Sản phẩm được công nhận từ 3 đến 5 sao; số sao càng cao, tiêu chuẩn chất lượng và câu chuyện sản phẩm càng được đánh giá cao.
          </p>
        </details>
      </div>
    </div>
  </section>
</template>

<style scoped>
.home-hero {
  position: relative;
  overflow: hidden;
  background: var(--ocop-mist-200);
}

.hero-scene {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-photo,
.hero-shade {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
}

.hero-photo {
  object-fit: cover;
  object-position: center 60%;
}

/* Lớp tối nhẹ phía trái giúp khung kính mờ nổi rõ trên ảnh sáng. */
.hero-shade {
  background: linear-gradient(90deg, color-mix(in srgb, var(--ocop-mist-950) 45%, transparent) 0%, color-mix(in srgb, var(--ocop-mist-950) 12%, transparent) 60%, transparent 100%);
}

.sky-top { stop-color: var(--ocop-mist-300); }
.sky-mid { stop-color: var(--ocop-mist-100); }
.sky-horizon { stop-color: var(--ocop-daquy-100); }
.glow-core { stop-color: var(--ocop-daquy-200); stop-opacity: 0.9; }
.glow-edge { stop-color: var(--ocop-daquy-100); stop-opacity: 0; }
.sun { fill: var(--ocop-daquy-300); }
.ridge-far { fill: var(--ocop-mist-400); opacity: 0.6; }
.ridge-mid { fill: var(--ocop-mist-600); opacity: 0.85; }
.pines path { fill: var(--ocop-mist-800); }
.mist { fill: var(--ocop-white); opacity: 0.7; }
.mist-low { opacity: 0.55; }
.tea-hill { fill: var(--ocop-tone-leaf); }
.tea-rows path { fill: none; stroke: color-mix(in srgb, var(--ocop-white) 22%, transparent); stroke-width: 6; stroke-linecap: round; }
.field { fill: var(--ocop-mist-900); opacity: 0.35; }
.petal { fill: var(--ocop-daquy-400); }
.core { fill: var(--ocop-daquy-800); }

.hero-inner {
  position: relative;
  z-index: 1;
  display: flex;
  min-height: 600px;
  padding: var(--ocop-space-12) 0 var(--ocop-space-16);
  align-items: center;
}

/* Khung kính mờ (glassmorphism). */
.hero-glass {
  display: flex;
  width: min(100%, 680px);
  padding: var(--ocop-space-8);
  flex-direction: column;
  align-items: flex-start;
  gap: var(--ocop-space-4);
  border: 1px solid var(--ocop-glass-border);
  border-radius: var(--ocop-radius-xl);
  background: var(--ocop-glass-bg);
  box-shadow: var(--ocop-shadow-overlay);
  backdrop-filter: blur(var(--ocop-glass-blur)) saturate(1.2);
}

@supports not ((backdrop-filter: blur(1px)) or (-webkit-backdrop-filter: blur(1px))) {
  .hero-glass {
    background: var(--ocop-glass-bg-solid);
  }
}

@media (prefers-reduced-transparency: reduce) {
  .hero-glass {
    background: var(--ocop-card);
    backdrop-filter: none;
  }
}


h1 {
  margin: 0;
  color: var(--ocop-mist-950);
  font-size: clamp(1.75rem, 3.2vw, 2.5rem);
  font-weight: 800;
  letter-spacing: -0.02em;
  line-height: 1.12;
}

.hero-mark {
  background: linear-gradient(transparent 62%, var(--ocop-daquy-300) 62%, var(--ocop-daquy-300) 92%, transparent 92%);
}

.hero-lead {
  margin: 0;
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-body-lg);
  line-height: 1.6;
}

.ocop-explainer {
  width: 100%;
  border-radius: var(--ocop-radius-md);
  background: color-mix(in srgb, var(--ocop-white) 55%, transparent);
}

.ocop-explainer summary {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-3);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-body);
  font-weight: 700;
  cursor: pointer;
  list-style: none;
}

.ocop-explainer summary::-webkit-details-marker {
  display: none;
}

.ocop-explainer summary::after {
  color: var(--ocop-mist-600);
  content: '+';
  font-size: var(--ocop-font-size-title-sm);
}

.ocop-explainer[open] summary::after {
  content: '−';
}

.ocop-explainer summary :deep(.app-icon) {
  color: var(--ocop-daquy-600);
}

.ocop-explainer p {
  margin: 0;
  padding: 0 var(--ocop-space-3) var(--ocop-space-3);
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-small);
  line-height: 1.6;
}

/* Toggle group (segmented control). */
.mode-group {
  display: inline-flex;
  margin-top: var(--ocop-space-2);
  padding: var(--ocop-space-1);
  gap: var(--ocop-space-1);
  border-radius: var(--ocop-radius-pill);
  background: color-mix(in srgb, var(--ocop-mist-950) 8%, transparent);
}

.mode-option {
  display: inline-flex;
  min-height: 40px;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-4);
  border: 0;
  border-radius: var(--ocop-radius-pill);
  background: transparent;
  color: var(--ocop-mist-800);
  font-size: var(--ocop-font-size-body);
  font-weight: 600;
  transition: background var(--ocop-transition), color var(--ocop-transition), box-shadow var(--ocop-transition);
}

.mode-option:hover {
  color: var(--ocop-mist-950);
}

.mode-option[aria-checked='true'] {
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-sm);
  color: var(--ocop-mist-950);
  font-weight: 700;
}

/* Lựa chọn đang bật có thêm gạch vàng, không chỉ dựa vào màu nền. */
.mode-option[aria-checked='true'] :deep(.app-icon) {
  color: var(--ocop-daquy-600);
}

.hero-search {
  display: flex;
  width: 100%;
  padding: var(--ocop-space-2);
  gap: var(--ocop-space-2);
  border: 1px solid var(--ocop-mist-200);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
  box-shadow: var(--ocop-shadow-card);
}

.search-field {
  position: relative;
  display: flex;
  min-width: 0;
  flex: 1;
  align-items: center;
}

.search-field .app-icon {
  position: absolute;
  left: var(--ocop-space-3);
  color: var(--ocop-mist-600);
  pointer-events: none;
}

.search-field input {
  width: 100%;
  height: var(--ocop-control-lg);
  padding: 0 var(--ocop-space-3) 0 calc(var(--ocop-space-8) + var(--ocop-space-2));
  border: 1px solid transparent;
  border-radius: var(--ocop-radius-md);
  outline: 0;
  background: transparent;
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-body-lg);
}

.search-field input::placeholder {
  color: var(--ocop-mist-600);
}

.search-field input:focus {
  border-color: var(--ocop-primary-500);
  box-shadow: 0 0 0 3px color-mix(in srgb, var(--ocop-primary-500) 18%, transparent);
}

.hero-search button {
  min-height: var(--ocop-control-lg);
}


@media (max-width: 767.98px) {
  .home-hero {
    background: var(--ocop-mist-100);
  }

  .hero-scene,
  .hero-photo,
  .hero-shade {
    height: 240px;
  }

  .hero-inner {
    min-height: 0;
    padding: calc(var(--ocop-space-16) * 2) 0 var(--ocop-space-6);
  }

  .hero-glass {
    padding: var(--ocop-space-5);
    border-radius: var(--ocop-radius-lg);
    background: var(--ocop-glass-bg-solid);
  }

  .hero-lead {
    font-size: var(--ocop-font-size-body);
    line-height: 1.5;
  }

  .mode-group {
    display: flex;
    width: 100%;
  }

  .mode-option {
    flex: 1;
    justify-content: center;
    padding: 0 var(--ocop-space-2);
  }

  .hero-search {
    flex-direction: column;
  }
}
</style>
