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
          <div class="period-btns">
            <button
              v-for="p in periods"
              :key="p.value"
              :class="{ active: period === p.value }"
              @click="changePeriod(p.value)"
            >
              {{ p.label }}
            </button>
          </div>
        </div>
        <div class="chart-wrap">
          <div ref="chartContainer" class="chart-container" />
          <div v-if="loading" class="chart-overlay">載入中...</div>
          <div v-else-if="error" class="chart-overlay error">{{ error }}</div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { useRoute } from 'vue-router'
import { createChart, CandlestickSeries, HistogramSeries, type IChartApi } from 'lightweight-charts'
import client from '@/api/client'

const route = useRoute()
const ticker = route.params.ticker as string
const chartContainer = ref<HTMLElement | null>(null)
const period = ref('3mo')
const stockName = ref('')
const loading = ref(false)
const error = ref('')
const periods = [
  { label: '1M', value: '1mo' },
  { label: '3M', value: '3mo' },
  { label: '6M', value: '6mo' },
  { label: '1Y', value: '1y' },
]

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
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '載入失敗，請稍後再試'
  } finally {
    loading.value = false
  }
}

async function loadStockName() {
  try {
    const res = await client.get('/stocks/search', { params: { q: ticker.replace('.TW', '') } })
    const match = res.data.find((s: any) => s.ticker === ticker)
    if (match) stockName.value = match.name
  } catch {}
}

function changePeriod(p: string) {
  period.value = p
}

watch(period, loadChart)

onMounted(async () => {
  if (!chartContainer.value) return
  loadStockName()

  chart = createChart(chartContainer.value, {
    autoSize: true,
    height: 420,
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
  padding: 0.75rem 1rem;
  border-bottom: 1px solid #111f35;
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
  font-size: 0.875rem;
  color: #4a7aad;
  background: rgba(13, 24, 41, 0.7);
  pointer-events: none;
}

.chart-overlay.error { color: #ff4d6d; }
</style>
