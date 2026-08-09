<template>
  <div class="chart-page">
    <header>
      <router-link to="/" class="back">← 返回</router-link>
      <div class="title-block">
        <span class="ticker-label">{{ ticker }}</span>
        <span class="stock-name-label" v-if="stockName">{{ stockName }}</span>
      </div>
    </header>
    <main>
      <div class="chart-card">
        <div class="chart-toolbar">
          <div class="chart-type-tabs">
            <button
              :class="{ active: chartType === 'candle' }"
              @click="switchChartType('candle')"
            >K線圖</button>
            <button
              :class="{ active: chartType === 'profile' }"
              @click="switchChartType('profile')"
            >壓力支撐</button>
          </div>
          <div class="divider" />
          <div class="period-btns" v-if="chartType === 'candle'">
            <button
              v-for="p in periods"
              :key="p.value"
              :class="{ active: period === p.value }"
              @click="changePeriod(p.value)"
            >{{ p.label }}</button>
          </div>
          <div class="period-btns" v-else>
            <button
              v-for="p in profilePeriods"
              :key="p.value"
              :class="{ active: profilePeriod === p.value }"
              @click="changeProfilePeriod(p.value)"
            >{{ p.label }}</button>
          </div>
        </div>

        <!-- K線圖 -->
        <div class="chart-wrap" v-show="chartType === 'candle'">
          <div ref="chartContainer" class="chart-container" />
          <Transition name="fade">
            <div v-if="loading" class="chart-overlay">
              <span class="chart-spinner" />
              <span>載入中...</span>
            </div>
            <div v-else-if="error" class="chart-overlay error">{{ error }}</div>
          </Transition>
        </div>

        <!-- 壓力支撐圖 -->
        <div class="profile-wrap" v-show="chartType === 'profile'">
          <div v-if="profileLoading" class="profile-status">
            <span class="chart-spinner" />
            <span>載入中...</span>
          </div>
          <div v-else-if="profileError" class="profile-status error">{{ profileError }}</div>
          <div v-else-if="profileData.length === 0" class="profile-status">查無資料</div>
          <div v-else class="profile-rows">
            <div
              v-for="row in profileData"
              :key="row.label"
              class="profile-row"
              :class="row.type"
            >
              <span class="price-label">{{ row.label }}</span>
              <div class="bar-wrap">
                <div
                  class="bar"
                  :style="{ width: (row.volume / profileMaxVolume * 100) + '%' }"
                />
              </div>
              <span class="vol-label">{{ formatVol(row.volume) }}</span>
            </div>
          </div>
          <div class="profile-legend">
            <span class="legend-item 壓力"><span class="dot" />壓力</span>
            <span class="legend-item 價"><span class="dot" />價</span>
            <span class="legend-item 支撐"><span class="dot" />支撐</span>
          </div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { createChart, CandlestickSeries, HistogramSeries, type IChartApi } from 'lightweight-charts'
import client from '@/api/client'

const route = useRoute()
const ticker = route.params.ticker as string
const chartContainer = ref<HTMLElement | null>(null)
const stockName = ref('')

// --- K線圖 ---
const period = ref('3mo')
const loading = ref(false)
const error = ref('')
const periods = [
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
]

// --- 壓力支撐 ---
const chartType = ref<'candle' | 'profile'>('candle')
const profilePeriod = ref('3mo')
const profileLoading = ref(false)
const profileError = ref('')
const profileData = ref<{ label: string; price_low: number; price_high: number; volume: number; type: string }[]>([])
const profilePeriods = [
  { label: '近季', value: '3mo' },
  { label: '近月', value: '1mo' },
  { label: '近周', value: '5d' },
]
const profileMaxVolume = computed(() =>
  profileData.value.reduce((max, r) => Math.max(max, r.volume), 1),
)

function formatVol(v: number): string {
  if (v >= 1_000_000) return (v / 1_000_000).toFixed(1) + 'M'
  if (v >= 1_000) return (v / 1_000).toFixed(0) + 'K'
  return String(v)
}

// --- Lightweight chart ---
let chart: IChartApi | null = null
let candleSeries: any = null
let volumeSeries: any = null

async function loadChart() {
  loading.value = true
  error.value = ''
  try {
    const res = await client.get(`/stocks/${ticker}/chart`, { params: { period: period.value } })
    const data = res.data
    if (!data || data.length === 0) {
      error.value = '查無資料'
      return
    }
    if (candleSeries) candleSeries.setData(data)
    if (volumeSeries) {
      volumeSeries.setData(
        data.map((d: any) => ({
          time: d.time,
          value: d.volume,
          color: d.close >= d.open ? 'rgba(38, 166, 154, 0.5)' : 'rgba(239, 83, 80, 0.5)',
        })),
      )
    }
    chart?.timeScale().fitContent()
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '載入失敗，請稍後再試'
  } finally {
    loading.value = false
  }
}

async function loadProfile() {
  profileLoading.value = true
  profileError.value = ''
  try {
    const res = await client.get(`/stocks/${ticker}/volume-profile`, {
      params: { period: profilePeriod.value },
    })
    profileData.value = res.data
  } catch (e: any) {
    profileError.value = e?.response?.data?.detail ?? '載入失敗，請稍後再試'
  } finally {
    profileLoading.value = false
  }
}

async function loadStockName() {
  try {
    const res = await client.get('/stocks/search', { params: { q: ticker.replace('.TW', '').replace('.TWO', '') } })
    const match = res.data.find((s: any) => s.ticker === ticker)
    if (match) stockName.value = match.name
  } catch {}
}

function changePeriod(p: string) {
  period.value = p
}

function changeProfilePeriod(p: string) {
  profilePeriod.value = p
}

function chartHeight() {
  return window.innerWidth <= 640 ? 300 : 420
}

function switchChartType(type: 'candle' | 'profile') {
  chartType.value = type
  if (type === 'profile' && profileData.value.length === 0) {
    loadProfile()
  }
  if (type === 'candle') {
    nextTick(() => {
      if (chartContainer.value) {
        chart?.resize(chartContainer.value.clientWidth, chartHeight())
      }
      chart?.timeScale().fitContent()
    })
  }
}

watch(period, loadChart)
watch(profilePeriod, () => {
  if (chartType.value === 'profile') loadProfile()
})

onMounted(async () => {
  if (!chartContainer.value) return
  loadStockName()

  chart = createChart(chartContainer.value, {
    height: chartHeight(),
    layout: {
      background: { color: '#0d1829' },
      textColor: '#4a7aad',
    },
    grid: {
      vertLines: { color: '#111f35' },
      horzLines: { color: '#111f35' },
    },
    crosshair: {
      vertLine: { color: '#1e3a5f', labelBackgroundColor: '#1e3a5f' },
      horzLine: { color: '#1e3a5f', labelBackgroundColor: '#1e3a5f' },
    },
    timeScale: {
      borderColor: '#1e3a5f',
      timeVisible: true,
    },
    rightPriceScale: {
      borderColor: '#1e3a5f',
    },
  })

  candleSeries = chart.addSeries(CandlestickSeries, {
    upColor: '#26a69a',
    downColor: '#ef5350',
    borderVisible: false,
    wickUpColor: '#26a69a',
    wickDownColor: '#ef5350',
  })

  volumeSeries = chart.addSeries(HistogramSeries, {
    priceFormat: { type: 'volume' },
    priceScaleId: 'volume',
  })
  chart.priceScale('volume').applyOptions({ scaleMargins: { top: 0.8, bottom: 0 } })

  const handleResize = () => {
    if (chartContainer.value) {
      chart?.resize(chartContainer.value.clientWidth, chartHeight())
    }
  }
  window.addEventListener('resize', handleResize)
  onUnmounted(() => window.removeEventListener('resize', handleResize))

  await loadChart()
})

onUnmounted(() => {
  chart?.remove()
})
</script>

<style scoped>
.chart-page {
  min-height: 100vh;
  background: #080c14;
}

header {
  background: #0d1829;
  border-bottom: 1px solid #1e3a5f;
  padding: 0.75rem 2rem;
  display: flex;
  align-items: center;
  gap: 1.25rem;
  position: sticky;
  top: 0;
  z-index: 10;
}

.back {
  color: #4a7aad;
  text-decoration: none;
  font-size: 0.85rem;
  transition: color 0.2s;
  white-space: nowrap;
}

.back:hover { color: #00c8ff; }

.title-block {
  display: flex;
  align-items: baseline;
  gap: 0.75rem;
}

.ticker-label {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #00c8ff;
}

.stock-name-label {
  font-size: 0.85rem;
  color: #4a7aad;
}

main {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem;
}

.chart-card {
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
}

.chart-toolbar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #111f35;
}

.chart-type-tabs {
  display: flex;
  gap: 0;
}

.chart-type-tabs button {
  padding: 0.3rem 0.9rem;
  border: 1px solid #1e3a5f;
  background: transparent;
  color: #4a7aad;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.chart-type-tabs button:first-child {
  border-radius: 4px 0 0 4px;
}

.chart-type-tabs button:last-child {
  border-radius: 0 4px 4px 0;
  border-left: none;
}

.chart-type-tabs button:hover {
  border-color: #00c8ff;
  color: #00c8ff;
}

.chart-type-tabs button.active {
  background: rgba(0, 200, 255, 0.12);
  border-color: #00c8ff;
  color: #00c8ff;
}

.divider {
  width: 1px;
  height: 1.4rem;
  background: #1e3a5f;
}

.period-btns {
  display: flex;
  gap: 0.35rem;
}

.period-btns button {
  padding: 0.3rem 0.75rem;
  border: 1px solid #1e3a5f;
  background: transparent;
  color: #4a7aad;
  border-radius: 4px;
  cursor: pointer;
  font-size: 0.8rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}

.period-btns button:hover {
  border-color: #00c8ff;
  color: #00c8ff;
}

.period-btns button.active {
  background: rgba(0, 200, 255, 0.12);
  border-color: #00c8ff;
  color: #00c8ff;
}

.chart-wrap {
  position: relative;
}

.chart-container {
  width: 100%;
}

/* 隱藏 Lightweight Charts 內建的 TradingView 品牌標誌 */
.chart-container :deep(a) {
  display: none !important;
}

.chart-overlay {
  position: absolute;
  inset: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  font-size: 0.875rem;
  color: #4a7aad;
  background: rgba(13, 24, 41, 0.75);
  pointer-events: none;
  backdrop-filter: blur(2px);
}

.chart-overlay.error { color: #ff4d6d; }

.chart-spinner {
  display: inline-block;
  width: 18px;
  height: 18px;
  border: 2px solid #1e3a5f;
  border-top-color: #00c8ff;
  border-radius: 50%;
  animation: chart-spin 0.65s linear infinite;
  flex-shrink: 0;
}

@keyframes chart-spin { to { transform: rotate(360deg); } }

/* Fade transition for loading overlay */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* 壓力支撐 */
.profile-wrap {
  display: flex;
  flex-direction: column;
  min-height: 420px;
}

.profile-status {
  flex: 1;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  font-size: 0.875rem;
  color: #4a7aad;
  padding: 2rem;
}

.profile-status.error { color: #ff4d6d; }

.profile-rows {
  flex: 1;
  overflow-y: auto;
  padding: 0.75rem 1rem;
  display: flex;
  flex-direction: column;
  gap: 3px;
}

.profile-row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  min-height: 22px;
}

.price-label {
  width: 130px;
  flex-shrink: 0;
  font-size: 0.72rem;
  color: #7a9bbf;
  text-align: right;
  font-variant-numeric: tabular-nums;
}

.bar-wrap {
  flex: 1;
  background: #111f35;
  border-radius: 2px;
  height: 16px;
  overflow: hidden;
}

.bar {
  height: 100%;
  border-radius: 2px;
  transition: width 0.3s ease;
  min-width: 2px;
}

.profile-row.壓力 .bar { background: #ef5350; }
.profile-row.支撐 .bar { background: #1565c0; }
.profile-row.價 .bar   { background: #f9a825; }

.vol-label {
  width: 56px;
  flex-shrink: 0;
  font-size: 0.72rem;
  color: #7a9bbf;
  font-variant-numeric: tabular-nums;
}

.profile-legend {
  display: flex;
  gap: 1.25rem;
  padding: 0.6rem 1rem;
  border-top: 1px solid #111f35;
  justify-content: center;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 0.35rem;
  font-size: 0.75rem;
  color: #7a9bbf;
}

.legend-item .dot {
  width: 10px;
  height: 10px;
  border-radius: 2px;
  display: inline-block;
}

.legend-item.壓力 .dot { background: #ef5350; }
.legend-item.價 .dot   { background: #f9a825; }
.legend-item.支撐 .dot { background: #1565c0; }

@media (max-width: 640px) {
  header { padding: 0.6rem 0.75rem; gap: 0.75rem; }
  main { padding: 0.75rem; }
  .chart-toolbar { flex-wrap: wrap; gap: 0.5rem; padding: 0.6rem 0.75rem; }
  .divider { display: none; }
  .period-btns { flex-wrap: wrap; }
  .price-label { width: 90px; font-size: 0.65rem; }
  .profile-wrap { min-height: 300px; }
}
</style>
