<script setup lang="ts">
import {
  BarController,
  BarElement,
  CategoryScale,
  Chart,
  LinearScale,
  Tooltip,
  type ChartConfiguration,
} from 'chart.js'
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'

import AppIcon from '@/components/ui/AppIcon.vue'

Chart.register(BarController, BarElement, CategoryScale, LinearScale, Tooltip)

export interface StatChartItem {
  label: string
  value: number
  /** Token màu: `--ocop-…` hoặc `var(--ocop-…)`; được đọc từ CSS khi vẽ để biểu đồ dùng đúng bảng màu. */
  color: string
  /** Nhãn đầy đủ trong tooltip và bảng số liệu (mặc định là label). */
  fullLabel?: string
}

const props = withDefaults(
  defineProps<{
    title: string
    description?: string
    /** column: cột đứng; bar: thanh ngang; stacked: một thanh ngang chia theo tỉ lệ. */
    kind?: 'column' | 'bar' | 'stacked'
    items: StatChartItem[]
    /** Câu mô tả số liệu cho trình đọc màn hình. */
    summary: string
    unit?: string
    height?: number
  }>(),
  {
    description: '',
    kind: 'column',
    unit: 'sản phẩm',
    height: 240,
  },
)

const canvasRef = ref<HTMLCanvasElement | null>(null)
const showTable = ref(false)
const tableId = `stat-table-${Math.random().toString(36).slice(2, 9)}`
let chart: Chart | null = null

const total = computed(() => props.items.reduce((sum, item) => sum + item.value, 0))

function cssToken(token: string): string | undefined {
  const name = token.startsWith('var(') ? token.slice(4, -1).trim() : token
  if (!name.startsWith('--') || typeof window === 'undefined') return undefined
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || undefined
}

function tooltipLabel(index: number): string {
  const item = props.items[index]
  return item ? `${item.fullLabel ?? item.label}: ${item.value} ${props.unit}` : ''
}

// Nhãn dài trên trục thanh ngang được ngắt thành nhiều dòng thay vì bị cắt mất chữ.
function wrapLabel(label: string, max = 18): string | string[] {
  if (label.length <= max) return label
  const lines: string[] = []
  let line = ''
  for (const word of label.split(' ')) {
    if (line && `${line} ${word}`.length > max) {
      lines.push(line)
      line = word
    } else {
      line = line ? `${line} ${word}` : word
    }
  }
  if (line) lines.push(line)
  return lines
}

function buildConfig(): ChartConfiguration<'bar'> {
  const textColor = cssToken('--ocop-mist-700')
  const gridColor = cssToken('--ocop-mist-100')
  const fontFamily = cssToken('--ocop-font-family-sans')
  const reduceMotion = typeof window !== 'undefined' && window.matchMedia?.('(prefers-reduced-motion: reduce)').matches
  const common = {
    responsive: true,
    maintainAspectRatio: false,
    animation: reduceMotion ? (false as const) : undefined,
    font: { family: fontFamily },
  }

  if (props.kind === 'stacked') {
    return {
      type: 'bar',
      data: {
        labels: [props.title],
        datasets: props.items.map((item) => ({
          label: item.fullLabel ?? item.label,
          data: [item.value],
          backgroundColor: cssToken(item.color),
          borderRadius: 6,
          borderSkipped: false,
          borderWidth: 2,
          borderColor: cssToken('--ocop-white'),
          barThickness: 28,
        })),
      },
      options: {
        ...common,
        indexAxis: 'y',
        scales: {
          x: { stacked: true, display: false, max: total.value || 1 },
          y: { stacked: true, display: false },
        },
        plugins: {
          legend: { display: false },
          tooltip: { callbacks: { label: (context) => tooltipLabel(context.datasetIndex) } },
        },
      },
    }
  }

  const horizontal = props.kind === 'bar'
  const valueAxis = {
    beginAtZero: true,
    grid: { color: gridColor },
    border: { display: false },
    ticks: { color: textColor, precision: 0, font: { family: fontFamily } },
  }
  const labelAxis = {
    grid: { display: false },
    border: { color: cssToken('--ocop-mist-300') },
    ticks: { color: textColor, font: { family: fontFamily, size: 12 }, autoSkip: !horizontal, maxRotation: 0 },
  }

  return {
    type: 'bar',
    data: {
      labels: props.items.map((item) => (horizontal ? wrapLabel(item.label) : item.label)),
      datasets: [
        {
          data: props.items.map((item) => item.value),
          backgroundColor: props.items.map((item) => cssToken(item.color) ?? ''),
          borderRadius: 6,
          maxBarThickness: horizontal ? 22 : 44,
        },
      ],
    },
    options: {
      ...common,
      indexAxis: horizontal ? 'y' : 'x',
      scales: horizontal ? { x: valueAxis, y: labelAxis } : { x: labelAxis, y: valueAxis },
      plugins: {
        legend: { display: false },
        tooltip: {
          callbacks: {
            title: (contexts) => {
              const item = contexts[0] ? props.items[contexts[0].dataIndex] : undefined
              return item ? item.fullLabel ?? item.label : ''
            },
            label: (context) => tooltipLabel(context.dataIndex),
          },
        },
      },
    },
  }
}

function renderChart(): void {
  if (!canvasRef.value) return
  chart?.destroy()
  chart = null
  try {
    chart = new Chart(canvasRef.value, buildConfig())
  } catch {
    // Không vẽ được (trình duyệt không hỗ trợ canvas): bảng số liệu vẫn dùng được.
    showTable.value = true
  }
}

onMounted(renderChart)
watch(() => [props.items, props.kind], renderChart, { deep: true })
onBeforeUnmount(() => chart?.destroy())
</script>

<template>
  <article class="stat-chart">
    <header class="chart-head">
      <div>
        <h3>{{ title }}</h3>
        <p v-if="description">{{ description }}</p>
      </div>
      <button
        class="table-toggle"
        type="button"
        :aria-pressed="showTable"
        :aria-controls="tableId"
        @click="showTable = !showTable"
      >
        <AppIcon :name="showTable ? 'barChart' : 'table'" :size="16" />
        <span class="toggle-text">{{ showTable ? 'Xem biểu đồ' : 'Bảng số liệu' }}</span>
      </button>
    </header>

    <slot name="lead" />

    <div v-show="!showTable" class="chart-box" :style="{ height: `${height}px` }">
      <canvas ref="canvasRef" role="img" :aria-label="summary" />
    </div>

    <table v-show="showTable" :id="tableId" class="chart-table">
      <caption class="visually-hidden">{{ title }}</caption>
      <thead>
        <tr>
          <th scope="col">Nhóm</th>
          <th scope="col" class="num">Số lượng</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in items" :key="item.fullLabel ?? item.label">
          <th scope="row"><span class="swatch" :style="{ background: item.color.startsWith('--') ? `var(${item.color})` : item.color }" />{{ item.fullLabel ?? item.label }}</th>
          <td class="num">{{ item.value }}</td>
        </tr>
      </tbody>
    </table>

    <slot />
  </article>
</template>

<style scoped>
.stat-chart {
  container-type: inline-size;
  display: flex;
  min-width: 0;
  flex-direction: column;
  gap: var(--ocop-space-4);
  padding: var(--ocop-space-5);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-lg);
  background: var(--ocop-card);
}

.chart-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: var(--ocop-space-3);
}

.chart-head h3 {
  margin: 0;
  color: var(--ocop-mist-950);
  font-size: var(--ocop-font-size-body-lg);
  font-weight: 700;
}

.chart-head p {
  margin: var(--ocop-space-1) 0 0;
  color: var(--ocop-mist-600);
  font-size: var(--ocop-font-size-small);
}

.table-toggle {
  display: inline-flex;
  min-height: var(--ocop-control-md);
  flex-shrink: 0;
  align-items: center;
  gap: var(--ocop-space-2);
  padding: 0 var(--ocop-space-3);
  border: 1px solid var(--ocop-border);
  border-radius: var(--ocop-radius-sm);
  background: var(--ocop-card);
  color: var(--ocop-mist-700);
  font-size: var(--ocop-font-size-small);
  font-weight: 600;
}

.table-toggle:hover {
  border-color: var(--ocop-mist-400);
  color: var(--ocop-mist-950);
}

/* Thẻ hẹp: nút chỉ còn icon (chữ vẫn đọc được bằng trình đọc màn hình) để tiêu đề không bị ép xuống dòng. */
@container (max-width: 400px) {
  .table-toggle {
    width: var(--ocop-control-md);
    justify-content: center;
    padding: 0;
  }

  .toggle-text {
    position: absolute;
    width: 1px;
    height: 1px;
    overflow: hidden;
    clip: rect(0 0 0 0);
    white-space: nowrap;
  }
}

.chart-box {
  position: relative;
  min-width: 0;
}

.chart-table {
  width: 100%;
  border-collapse: collapse;
  font-size: var(--ocop-font-size-small);
}

.chart-table th,
.chart-table td {
  padding: var(--ocop-space-2) var(--ocop-space-1);
  border-bottom: 1px solid var(--ocop-border-soft);
  text-align: left;
}

.chart-table thead th {
  color: var(--ocop-mist-600);
  font-weight: 600;
}

.chart-table tbody th {
  font-weight: 500;
}

.chart-table .num {
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.swatch {
  display: inline-block;
  width: 10px;
  height: 10px;
  margin-right: var(--ocop-space-2);
  border-radius: var(--ocop-radius-xs);
}
</style>
