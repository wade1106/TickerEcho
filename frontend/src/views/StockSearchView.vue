<template>
  <div class="search-page">
    <header>
      <router-link to="/" class="back">← 返回</router-link>
      <div class="title-block">
        <span class="page-title">股票查詢</span>
      </div>
    </header>

    <main>
      <!-- 搜尋列 -->
      <div class="search-bar-wrap">
        <div class="search-bar">
          <input
            ref="inputEl"
            v-model="query"
            class="search-input"
            placeholder="輸入股票名稱或代碼..."
            @input="onInput"
            @keydown.down.prevent="moveSuggestion(1)"
            @keydown.up.prevent="moveSuggestion(-1)"
            @keydown.enter="selectSuggestion(activeSuggestion)"
            @keydown.esc="suggestions = []"
            autocomplete="off"
          />
          <span v-if="searching" class="search-spinner" />
        </div>

        <!-- 自動補全下拉 -->
        <ul v-if="suggestions.length" class="suggestions">
          <li
            v-for="(s, i) in suggestions"
            :key="s.ticker"
            :class="{ active: i === activeSuggestion }"
            @mousedown.prevent="selectSuggestion(i)"
          >
            <span class="s-code">{{ s.code }}</span>
            <span class="s-name">{{ s.name }}</span>
            <span class="s-ticker">{{ s.ticker }}</span>
          </li>
        </ul>
      </div>

      <!-- 結果卡片 -->
      <Transition name="fade">
        <div v-if="loading" class="status-msg">
          <span class="spinner" />載入中...
        </div>
        <div v-else-if="error" class="status-msg error">{{ error }}</div>
        <div v-else-if="stockInfo" class="info-layout">

          <!-- 左：價格 & 基本資訊 -->
          <div class="info-card">
            <div class="stock-header">
              <div class="stock-title">
                <span class="stock-name">{{ stockInfo.name }}</span>
                <span class="stock-ticker">{{ stockInfo.ticker }}</span>
              </div>
              <div class="price-block">
                <span class="price">{{ priceInfo?.price?.toLocaleString() ?? '—' }}</span>
                <span
                  class="change"
                  :class="(priceInfo?.change_percent ?? 0) >= 0 ? 'pos' : 'neg'"
                >
                  {{ (priceInfo?.change_percent ?? 0) >= 0 ? '+' : '' }}{{ priceInfo?.change_percent?.toFixed(2) ?? '—' }}%
                </span>
              </div>
            </div>

            <div class="meta-grid">
              <div class="meta-item" v-if="stockInfo.sector">
                <span class="meta-label">產業別</span>
                <span class="meta-val">{{ stockInfo.sector }}</span>
              </div>
              <div class="meta-item" v-if="stockInfo.industry">
                <span class="meta-label">細分產業</span>
                <span class="meta-val">{{ stockInfo.industry }}</span>
              </div>
              <div class="meta-item" v-if="stockInfo.country">
                <span class="meta-label">國家</span>
                <span class="meta-val">{{ stockInfo.country }}</span>
              </div>
              <div class="meta-item" v-if="stockInfo.employees">
                <span class="meta-label">員工人數</span>
                <span class="meta-val">{{ stockInfo.employees.toLocaleString() }}</span>
              </div>
              <div class="meta-item" v-if="stockInfo.market_cap">
                <span class="meta-label">市值</span>
                <span class="meta-val">{{ formatMarketCap(stockInfo.market_cap) }} {{ stockInfo.currency }}</span>
              </div>
              <div class="meta-item" v-if="stockInfo.website">
                <span class="meta-label">官方網站</span>
                <a :href="stockInfo.website" target="_blank" rel="noopener" class="meta-link">{{ stockInfo.website }}</a>
              </div>
            </div>

            <div class="action-row">
              <router-link :to="`/chart/${stockInfo.ticker}`" class="chart-btn">查看K線圖 →</router-link>
            </div>
          </div>

          <!-- 右：公司描述 -->
          <div class="desc-card" v-if="stockInfo.summary">
            <div class="desc-title">公司簡介</div>
            <p class="desc-text">{{ stockInfo.summary }}</p>
          </div>
          <div class="desc-card empty-desc" v-else>
            <span>查無公司描述</span>
          </div>

        </div>
      </Transition>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import client from '@/api/client'

const query = ref('')
const inputEl = ref<HTMLInputElement | null>(null)
const suggestions = ref<{ ticker: string; code: string; name: string }[]>([])
const activeSuggestion = ref(-1)
const searching = ref(false)
const loading = ref(false)
const error = ref('')
const stockInfo = ref<any>(null)
const priceInfo = ref<any>(null)

let searchTimer: ReturnType<typeof setTimeout> | null = null

function onInput() {
  activeSuggestion.value = -1
  if (searchTimer) clearTimeout(searchTimer)
  const q = query.value.trim()
  if (q.length < 1) {
    suggestions.value = []
    return
  }
  searchTimer = setTimeout(async () => {
    if (q.length < 2) return
    searching.value = true
    try {
      const res = await client.get('/stocks/search', { params: { q } })
      suggestions.value = res.data
    } catch {
      suggestions.value = []
    } finally {
      searching.value = false
    }
  }, 300)
}

function moveSuggestion(dir: number) {
  const len = suggestions.value.length
  if (!len) return
  activeSuggestion.value = (activeSuggestion.value + dir + len) % len
}

async function selectSuggestion(idx: number) {
  const s = idx >= 0 ? suggestions.value[idx] : suggestions.value[0]
  if (!s) return
  suggestions.value = []
  query.value = `${s.code} ${s.name}`
  await loadStock(s.ticker)
}

async function loadStock(ticker: string) {
  loading.value = true
  error.value = ''
  stockInfo.value = null
  priceInfo.value = null
  try {
    const [infoRes, priceRes] = await Promise.all([
      client.get(`/stocks/${ticker}/info`),
      client.get(`/stocks/${ticker}/price`),
    ])
    stockInfo.value = infoRes.data
    priceInfo.value = priceRes.data
  } catch (e: any) {
    error.value = e?.response?.data?.detail ?? '載入失敗，請稍後再試'
  } finally {
    loading.value = false
  }
}

function formatMarketCap(val: number): string {
  if (val >= 1e12) return (val / 1e12).toFixed(2) + ' 兆'
  if (val >= 1e8) return (val / 1e8).toFixed(2) + ' 億'
  if (val >= 1e4) return (val / 1e4).toFixed(2) + ' 萬'
  return val.toLocaleString()
}
</script>

<style scoped>
.search-page {
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

.page-title {
  font-size: 1rem;
  font-weight: 700;
  letter-spacing: 1px;
  color: #00c8ff;
}

main {
  max-width: 1200px;
  margin: 0 auto;
  padding: 2rem 1.5rem;
}

/* 搜尋列 */
.search-bar-wrap {
  position: relative;
  max-width: 560px;
  margin: 0 auto 2rem;
}

.search-bar {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  padding: 0 1rem;
  transition: border-color 0.2s;
}
.search-bar:focus-within { border-color: #00c8ff; }

.search-input {
  flex: 1;
  background: transparent;
  border: none;
  outline: none;
  color: #c9d6e8;
  font-size: 1rem;
  padding: 0.85rem 0;
}
.search-input::placeholder { color: #2d4a6e; }

.search-spinner {
  width: 16px;
  height: 16px;
  border: 2px solid #1e3a5f;
  border-top-color: #00c8ff;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
  flex-shrink: 0;
}

.suggestions {
  position: absolute;
  top: calc(100% + 4px);
  left: 0; right: 0;
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  list-style: none;
  margin: 0; padding: 0.4rem 0;
  z-index: 100;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
  max-height: 280px;
  overflow-y: auto;
}

.suggestions li {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  padding: 0.55rem 1rem;
  cursor: pointer;
  transition: background 0.15s;
}
.suggestions li:hover,
.suggestions li.active { background: rgba(0, 200, 255, 0.08); }

.s-code { font-size: 0.85rem; color: #00c8ff; font-weight: 600; min-width: 44px; }
.s-name { flex: 1; font-size: 0.875rem; color: #c9d6e8; }
.s-ticker { font-size: 0.75rem; color: #2d4a6e; }

/* 狀態訊息 */
.status-msg {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  padding: 3rem;
  color: #4a7aad;
  font-size: 0.875rem;
}
.status-msg.error { color: #ff4d6d; }

.spinner {
  display: inline-block;
  width: 18px; height: 18px;
  border: 2px solid #1e3a5f;
  border-top-color: #00c8ff;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
  flex-shrink: 0;
}

@keyframes spin { to { transform: rotate(360deg); } }

/* 結果卡片 */
.info-layout {
  display: grid;
  grid-template-columns: 1fr 1.4fr;
  gap: 1.25rem;
  align-items: start;
}

.info-card, .desc-card {
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 1.5rem;
}

.stock-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  margin-bottom: 1.25rem;
  gap: 1rem;
  flex-wrap: wrap;
}

.stock-title {
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.stock-name { font-size: 1.15rem; font-weight: 700; color: #e2eeff; }
.stock-ticker { font-size: 0.8rem; color: #00c8ff; letter-spacing: 0.5px; }

.price-block {
  text-align: right;
}
.price { display: block; font-size: 1.5rem; font-weight: 700; color: #e2eeff; font-variant-numeric: tabular-nums; }
.change { font-size: 0.9rem; font-weight: 600; }
.pos { color: #26a69a; }
.neg { color: #ef5350; }

.meta-grid {
  display: flex;
  flex-direction: column;
  gap: 0.6rem;
  border-top: 1px solid #111f35;
  padding-top: 1rem;
  margin-bottom: 1.25rem;
}

.meta-item {
  display: flex;
  justify-content: space-between;
  align-items: baseline;
  gap: 0.5rem;
  font-size: 0.84rem;
}
.meta-label { color: #4a7aad; flex-shrink: 0; }
.meta-val { color: #c9d6e8; text-align: right; }
.meta-link {
  color: #00c8ff;
  text-decoration: none;
  font-size: 0.8rem;
  text-align: right;
  word-break: break-all;
}
.meta-link:hover { text-decoration: underline; }

.action-row {
  border-top: 1px solid #111f35;
  padding-top: 1rem;
}

.chart-btn {
  display: inline-block;
  padding: 0.45rem 1.1rem;
  border: 1px solid rgba(0, 200, 255, 0.35);
  border-radius: 6px;
  color: #00c8ff;
  font-size: 0.85rem;
  text-decoration: none;
  transition: background 0.2s, border-color 0.2s;
}
.chart-btn:hover { background: rgba(0, 200, 255, 0.1); border-color: #00c8ff; }

/* 公司描述 */
.desc-title {
  font-size: 0.8rem;
  font-weight: 600;
  color: #4a7aad;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 0.9rem;
}

.desc-text {
  font-size: 0.875rem;
  line-height: 1.8;
  color: #c9d6e8;
  margin: 0;
  white-space: pre-line;
}

.empty-desc {
  display: flex;
  align-items: center;
  justify-content: center;
  color: #2d4a6e;
  font-size: 0.875rem;
  min-height: 120px;
}

/* Fade transition */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease; }
.fade-enter-from, .fade-leave-to { opacity: 0; }

/* RWD */
@media (max-width: 860px) {
  .info-layout { grid-template-columns: 1fr; }
}

@media (max-width: 640px) {
  header { padding: 0.6rem 0.75rem; }
  main { padding: 1rem 0.75rem; }
  .price { font-size: 1.25rem; }
  .search-input { font-size: 0.9rem; }
}
</style>
