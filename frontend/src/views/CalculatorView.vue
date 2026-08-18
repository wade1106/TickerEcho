<template>
  <div class="calc-page">
    <header>
      <div class="brand">
        <span class="brand-icon">◈</span>
        <span class="brand-name">TickerEcho</span>
      </div>
      <div class="header-right">
        <span class="status-dot"></span>
        <span class="status-text">系統運行中</span>
        <router-link to="/" class="nav-link">警報首頁</router-link>
        <router-link to="/stock-search" class="nav-link">股票查詢</router-link>
        <router-link to="/calculator" class="nav-link">股市計算機</router-link>
        <router-link to="/investment-plans" class="nav-link">投資計畫</router-link>
        <button class="logout-btn" @click="logout">登出</button>
      </div>
    </header>

    <main>
      <div class="calc-layout">
        <!-- 左側：交易參數 -->
        <div class="params-card">
          <div class="card-title">交易參數</div>

          <div class="param-group">
            <label>交易類別</label>
            <select v-model="stockType" class="type-select">
              <option value="stock">股票</option>
              <option value="daytrade">股票當沖</option>
              <option value="etf">ETF</option>
            </select>
          </div>

          <div class="param-group">
            <label>買入價格</label>
            <div class="num-input" :class="{ 'input-invalid': buyPriceError }">
              <button class="adj-btn" @click="adjustPrice('buy', -1)">−</button>
              <input
                v-model="buyPriceStr"
                type="text"
                inputmode="decimal"
                class="num-field"
                placeholder="0"
              />
              <button v-if="buyPriceStr" class="clear-btn" @click="buyPriceStr = ''">×</button>
              <button class="adj-btn" @click="adjustPrice('buy', 1)">+</button>
              <span class="unit-label">元</span>
            </div>
            <div v-if="buyPriceError" class="field-error">{{ buyPriceError }}</div>
          </div>

          <div class="param-group">
            <label>賣出價格</label>
            <div class="num-input" :class="{ 'input-invalid': sellPriceError }">
              <button class="adj-btn" @click="adjustPrice('sell', -1)">−</button>
              <input
                v-model="sellPriceStr"
                type="text"
                inputmode="decimal"
                class="num-field"
                placeholder="0"
              />
              <button v-if="sellPriceStr" class="clear-btn" @click="sellPriceStr = ''">×</button>
              <button class="adj-btn" @click="adjustPrice('sell', 1)">+</button>
              <span class="unit-label">元</span>
            </div>
            <div v-if="sellPriceError" class="field-error">{{ sellPriceError }}</div>
          </div>

          <div class="param-group">
            <label>交易數量</label>
            <div class="num-input">
              <button class="adj-btn" @click="adjustShares(-1)">−</button>
              <input v-model.number="sharesInput" type="number" min="1" class="num-field" />
              <button class="adj-btn" @click="adjustShares(1)">+</button>
              <div class="unit-toggle">
                <button :class="{ active: sharesUnit === '股' }" @click="sharesUnit = '股'">股</button>
                <button :class="{ active: sharesUnit === '張' }" @click="sharesUnit = '張'">張</button>
              </div>
            </div>
          </div>

          <div class="param-note">
            實際股數：{{ actualShares.toLocaleString() }} 股
          </div>
        </div>

        <!-- 右側：試算結果 -->
        <div class="result-card">
          <div class="card-title">試算結果</div>
          <div v-if="buyPrice <= 0" class="empty-hint">請輸入買入價格開始試算</div>

          <template v-else>
          <div class="result-summary">
            <span>買入價格 <span class="sum-val">{{ formatPrice(buyPrice) }}元</span></span>
            <span>賣出價格 <span class="sum-val">{{ formatPrice(sellPrice) }}元</span></span>
            <span>損益兩平價格 <span class="sum-val breakeven">{{ formatPrice(breakevenPrice) }}元</span></span>
          </div>

          <div class="table-wrap">
            <table>
              <thead>
                <tr>
                  <th>賣出價格</th>
                  <th>損益金額</th>
                  <th>報酬率</th>
                  <th class="col-buy-fee">買入手續費</th>
                  <th class="col-sell-fee">賣出手續費</th>
                  <th class="col-tax">證券交易稅</th>
                  <th>固投資成本</th>
                </tr>
              </thead>
              <tbody>
                <tr
                  v-for="row in tableRows"
                  :key="row.sellPrice"
                  :class="{ 'row-target': row.isTarget }"
                >
                  <td>{{ formatPrice(row.sellPrice) }}</td>
                  <td :class="row.profit >= 0 ? 'pos' : 'neg'">
                    <span :class="{ 'profit-box': row.isTarget }">{{ row.profit.toLocaleString() }}</span>
                  </td>
                  <td :class="row.profit >= 0 ? 'pos' : 'neg'">{{ row.returnRate }}</td>
                  <td class="fee-cell col-buy-fee">
                    {{ row.buyFee }}
                    <span class="actual-fee">({{ row.buyFeeActual }})</span>
                  </td>
                  <td class="fee-cell col-sell-fee">
                    {{ row.sellFee }}
                    <span class="actual-fee">({{ row.sellFeeActual }})</span>
                  </td>
                  <td class="col-tax">{{ row.tax }}</td>
                  <td>{{ row.totalCost.toLocaleString() }}</td>
                </tr>
              </tbody>
            </table>
          </div>
          </template>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()
function logout() { auth.logout(); router.push('/login') }

const stockType = ref<'stock' | 'daytrade' | 'etf'>('stock')
const buyPriceStr = ref('')
const sellPriceStr = ref('')
const sharesInput = ref(10)
const sharesUnit = ref<'股' | '張'>('股')

// 將字串解析為數字，空字串視為 0
const buyPrice = computed(() => {
  const n = parseFloat(buyPriceStr.value)
  return isNaN(n) ? 0 : n
})
const sellPrice = computed(() => {
  const n = parseFloat(sellPriceStr.value)
  return isNaN(n) ? 0 : n
})

// 驗證：只有輸入了內容且是負數才顯示錯誤
const buyPriceError = computed(() => {
  if (!buyPriceStr.value) return ''
  const n = parseFloat(buyPriceStr.value)
  if (isNaN(n)) return '請輸入有效數字'
  if (n < 0) return '價格不能為負數'
  return ''
})
const sellPriceError = computed(() => {
  if (!sellPriceStr.value) return ''
  const n = parseFloat(sellPriceStr.value)
  if (isNaN(n)) return '請輸入有效數字'
  if (n < 0) return '價格不能為負數'
  return ''
})

const actualShares = computed(() =>
  sharesUnit.value === '張' ? sharesInput.value * 1000 : sharesInput.value,
)

const taxRate = computed(() => {
  if (stockType.value === 'etf') return 0.001
  if (stockType.value === 'daytrade') return 0.0015
  return 0.003
})

function getTickSize(price: number): number {
  if (price < 10) return 0.01
  if (price < 50) return 0.05
  if (price < 100) return 0.1
  if (price < 500) return 0.5
  if (price < 1000) return 1
  return 5
}

function roundToTick(price: number, tick: number): number {
  return Math.round(price / tick) * tick
}

function formatPrice(p: number): string {
  const tick = getTickSize(p)
  if (tick < 0.1) return p.toFixed(2)
  if (tick < 1) return p.toFixed(1)
  return p.toFixed(0)
}

function calcFeeInfo(price: number, shares: number) {
  const actual = Math.round(price * shares * 0.001425)
  return { fee: Math.max(20, actual), actual }
}

const buyFeeInfo = computed(() => calcFeeInfo(buyPrice.value, actualShares.value))

const buyCost = computed(() => buyPrice.value * actualShares.value + buyFeeInfo.value.fee)

function calcRow(sp: number) {
  const shares = actualShares.value
  const { fee: sellFee, actual: sellFeeActual } = calcFeeInfo(sp, shares)
  const tax = Math.round(sp * shares * taxRate.value)
  const profit = Math.round(sp * shares - sellFee - tax - buyCost.value)
  const totalCost = Math.round(buyCost.value + sellFee + tax)
  const returnRate = totalCost > 0 ? (profit / totalCost * 100).toFixed(1) + '%' : '—'
  return {
    sellPrice: sp,
    profit,
    returnRate,
    buyFee: buyFeeInfo.value.fee,
    buyFeeActual: buyFeeInfo.value.actual,
    sellFee,
    sellFeeActual,
    tax,
    totalCost,
    isTarget: Math.abs(sp - sellPrice.value) < 0.0001,
  }
}

const tableRows = computed(() => {
  const sp = sellPrice.value
  const tick = getTickSize(sp)
  const rows = []
  for (let i = -10; i <= 10; i++) {
    const p = Math.round((sp + i * tick) / tick) * tick
    if (p > 0) rows.push(calcRow(p))
  }
  return rows
})

const breakevenPrice = computed(() => {
  const buy = buyPrice.value
  const tick = getTickSize(buy)
  for (let i = 0; i <= 5000; i++) {
    const p = roundToTick(buy + i * tick, tick)
    const { fee: sf } = calcFeeInfo(p, actualShares.value)
    const tax = Math.round(p * actualShares.value * taxRate.value)
    const profit = p * actualShares.value - sf - tax - buyCost.value
    if (profit >= 0) return p
  }
  return buy
})

function adjustPrice(field: 'buy' | 'sell', dir: number) {
  const cur = field === 'buy' ? buyPrice.value : sellPrice.value
  const tick = getTickSize(cur > 0 ? cur : 1)
  const next = Math.max(0, roundToTick(cur + dir * tick, tick))
  const str = formatPrice(next)
  if (field === 'buy') buyPriceStr.value = str
  else sellPriceStr.value = str
}

function adjustShares(dir: number) {
  sharesInput.value = Math.max(1, sharesInput.value + dir)
}
</script>

<style scoped>
.calc-page {
  min-height: 100vh;
  background: #080c14;
}

header {
  background: #0d1829;
  border-bottom: 1px solid #1e3a5f;
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky;
  top: 0;
  z-index: 10;
}

.brand { display: flex; align-items: center; gap: 0.5rem; }
.brand-icon { color: #00c8ff; font-size: 1.2rem; text-shadow: 0 0 10px rgba(0,200,255,0.6); }
.brand-name { font-size: 1rem; font-weight: 700; letter-spacing: 2px; color: #e2eeff; }
.header-right { display: flex; align-items: center; gap: 0.75rem; }
.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 6px rgba(74,222,128,0.7); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
.status-text { font-size: 0.75rem; color: #4a7aad; letter-spacing: 0.5px; }

.nav-link {
  background: transparent;
  border: 1px solid #1e3a5f;
  color: #4a7aad;
  padding: 0.35rem 0.9rem;
  border-radius: 4px;
  font-size: 0.8rem;
  text-decoration: none;
  transition: border-color 0.2s, color 0.2s, background 0.2s;
}
.nav-link:hover { border-color: #00c8ff; color: #00c8ff; }
.nav-link.router-link-exact-active { border-color: #00c8ff; color: #00c8ff; background: rgba(0,200,255,0.12); }

.logout-btn { background: transparent; border: 1px solid #1e3a5f; color: #4a7aad; padding: 0.35rem 0.9rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem; transition: border-color 0.2s, color 0.2s; }
.logout-btn:hover { border-color: #00c8ff; color: #00c8ff; }

main {
  max-width: 1600px;
  margin: 0 auto;
  padding: 1.5rem;
}

.calc-layout {
  display: flex;
  gap: 1.25rem;
  align-items: flex-start;
}

/* --- 左側 --- */
.params-card {
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  padding: 1.25rem 1.5rem;
  width: 280px;
  flex-shrink: 0;
}

.card-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #4a7aad;
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 1.25rem;
}

.param-group {
  margin-bottom: 1.25rem;
}

.param-group label {
  display: block;
  font-size: 0.75rem;
  color: #4a7aad;
  margin-bottom: 0.45rem;
  letter-spacing: 0.5px;
  text-decoration: underline;
  text-underline-offset: 3px;
  text-decoration-color: #1e3a5f;
}

.type-select {
  width: 100%;
  padding: 0.5rem 0.75rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  color: #c9d6e8;
  font-size: 0.875rem;
  outline: none;
  cursor: pointer;
  transition: border-color 0.2s;
}
.type-select:focus { border-color: #00c8ff; }
.type-select option { background: #0d1829; }

.num-input {
  display: flex;
  align-items: center;
  gap: 0;
}

.adj-btn {
  width: 34px;
  height: 36px;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  color: #4a7aad;
  font-size: 1.1rem;
  cursor: pointer;
  transition: border-color 0.2s, color 0.2s;
  flex-shrink: 0;
  line-height: 1;
}
.adj-btn:first-child { border-radius: 6px 0 0 6px; }
.adj-btn:hover { border-color: #00c8ff; color: #00c8ff; }

.num-field {
  flex: 1;
  min-width: 0;
  height: 36px;
  padding: 0 0.5rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-left: none;
  border-right: none;
  color: #c9d6e8;
  font-size: 0.875rem;
  text-align: center;
  outline: none;
  -moz-appearance: textfield;
}
.num-field::-webkit-inner-spin-button,
.num-field::-webkit-outer-spin-button { display: none; }
.num-field:focus { border-color: #00c8ff; }

.unit-label {
  height: 36px;
  padding: 0 0.6rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-left: none;
  border-radius: 0 6px 6px 0;
  color: #4a7aad;
  font-size: 0.8rem;
  display: flex;
  align-items: center;
  flex-shrink: 0;
}

.input-invalid .adj-btn,
.input-invalid .num-field,
.input-invalid .unit-label,
.input-invalid .clear-btn {
  border-color: #ef5350 !important;
}

.field-error {
  margin-top: 4px;
  font-size: 0.72rem;
  color: #ef5350;
  padding-left: 2px;
}

.clear-btn {
  height: 36px;
  padding: 0 0.45rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-left: none;
  color: #4a7aad;
  font-size: 0.9rem;
  cursor: pointer;
  line-height: 1;
  transition: color 0.2s;
  flex-shrink: 0;
}
.clear-btn:hover { color: #ff4d6d; }

.unit-toggle {
  display: flex;
  flex-shrink: 0;
}
.unit-toggle button {
  height: 36px;
  padding: 0 0.7rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-left: none;
  color: #4a7aad;
  font-size: 0.8rem;
  cursor: pointer;
  transition: background 0.2s, border-color 0.2s, color 0.2s;
}
.unit-toggle button:last-child {
  border-radius: 0 6px 6px 0;
}
.unit-toggle button.active {
  background: rgba(0, 200, 255, 0.12);
  border-color: #00c8ff;
  color: #00c8ff;
}
.unit-toggle button:hover:not(.active) {
  border-color: #00c8ff;
  color: #00c8ff;
}

.param-note {
  font-size: 0.75rem;
  color: #2d4a6e;
  margin-top: -0.5rem;
}

/* --- 右側 --- */
.result-card {
  flex: 1;
  min-width: 0;
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  overflow: hidden;
}

.result-card .card-title {
  padding: 1rem 1.25rem 0;
}

.empty-hint {
  padding: 3rem 1.25rem;
  text-align: center;
  color: #2d4a6e;
  font-size: 0.875rem;
}

.result-summary {
  display: flex;
  gap: 1.5rem;
  padding: 0.5rem 1.25rem 0.75rem;
  font-size: 0.8rem;
  color: #4a7aad;
  border-bottom: 1px solid #111f35;
  flex-wrap: wrap;
}

.sum-val {
  color: #00c8ff;
  font-weight: 600;
  margin-left: 0.3rem;
}

.sum-val.breakeven {
  color: #f9a825;
}

.table-wrap {
  overflow-x: auto;
}

table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.84rem;
}

thead tr {
  background: #111f35;
}

th {
  padding: 0.6rem 0.9rem;
  text-align: right;
  color: #c9d6e8;
  font-size: 0.78rem;
  font-weight: 600;
  white-space: nowrap;
  border-bottom: 1px solid #1e3a5f;
}
th:first-child { text-align: right; }

td {
  padding: 0.55rem 0.9rem;
  text-align: right;
  color: #c9d6e8;
  border-bottom: 1px solid #111f35;
  font-variant-numeric: tabular-nums;
  white-space: nowrap;
}

tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255, 255, 255, 0.015); }

.row-target td {
  background: rgba(249, 168, 37, 0.08);
}
.row-target:hover td {
  background: rgba(249, 168, 37, 0.12);
}

.profit-box {
  display: inline-block;
  border: 1px solid #ef5350;
  padding: 0 4px;
  border-radius: 2px;
}
.row-target.pos .profit-box {
  border-color: #26a69a;
}

.pos { color: #26a69a; }
.neg { color: #ef5350; }

.fee-cell { color: #c9d6e8; }
.actual-fee {
  color: #2d4a6e;
  font-size: 0.75rem;
  margin-left: 2px;
}

@media (max-width: 900px) {
  .calc-layout { flex-direction: column; }
  .params-card { width: 100%; }

  /* 手機上參數卡改 2 欄 grid */
  .params-card { display: grid; grid-template-columns: 1fr 1fr; gap: 0 1.25rem; }
  .card-title { grid-column: 1 / -1; }
  .param-note { grid-column: 1 / -1; }
}

@media (max-width: 640px) {
  header { padding: 0.6rem 0.75rem; flex-wrap: wrap; gap: 0.4rem; }
  .brand-name { font-size: 0.9rem; }
  .status-dot, .status-text { display: none; }
  .header-right { width: 100%; border-top: 1px solid #111f35; padding-top: 0.45rem; gap: 0.35rem; flex-wrap: wrap; }
  .nav-link { font-size: 0.72rem; padding: 0.26rem 0.55rem; }
  .logout-btn { font-size: 0.72rem; padding: 0.26rem 0.55rem; }
  main { padding: 0.75rem; }

  /* 參數卡改單欄 */
  .params-card { grid-template-columns: 1fr; padding: 1rem; }

  /* 數字輸入框 adj-btn 縮小 */
  .adj-btn { width: 30px; }

  /* 試算結果 summary 換行 */
  .result-summary { flex-direction: column; gap: 0.4rem; }

  /* 手機隱藏次要欄：買入手續費、賣出手續費、交易稅（保留賣出價格/損益/報酬率/固投資成本） */
  th.col-buy-fee, td.col-buy-fee,
  th.col-sell-fee, td.col-sell-fee,
  th.col-tax, td.col-tax { display: none; }

  /* 括號內的實際費用在手機上不顯示 */
  .actual-fee { display: none; }

  /* 調小 table 字體和 padding */
  table { font-size: 0.78rem; }
  th, td { padding: 0.45rem 0.55rem; }
}
</style>
