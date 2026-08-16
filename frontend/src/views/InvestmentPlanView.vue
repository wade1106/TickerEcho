<template>
  <div class="dashboard">
    <header>
      <div class="brand">
        <span class="brand-icon">◈</span>
        <span class="brand-name">TickerEcho</span>
      </div>
      <div class="header-right">
        <span class="status-dot"></span>
        <span class="status-text">系統運行中</span>
        <router-link to="/" class="calc-link">警報首頁</router-link>
        <router-link to="/stock-search" class="calc-link">股票查詢</router-link>
        <router-link to="/calculator" class="calc-link">股市計算機</router-link>
        <button class="logout-btn" @click="logout">登出</button>
      </div>
    </header>

    <main>
      <!-- Search Panel -->
      <div class="search-panel">
        <h2><span class="h2-icon">≡</span> 搜尋條件</h2>
        <div class="search-fields">
          <div class="field-group">
            <label>日期</label>
            <div class="input-wrap">
              <input type="date" v-model="searchDate" class="field-input" @change="doSearch" />
              <button v-if="searchDate" class="clear-x" @click="clearField('date')" type="button" tabindex="-1">×</button>
            </div>
          </div>
          <div class="field-group">
            <label>股票名稱或代號</label>
            <div class="input-wrap">
              <input type="text" v-model="searchStock" class="field-input" placeholder="輸入股票代號或名稱..." @keyup.enter="doSearch" />
              <button v-if="searchStock" class="clear-x" @click="clearField('stock')" type="button" tabindex="-1">×</button>
            </div>
          </div>
          <div class="field-group">
            <label>投資人</label>
            <div class="input-wrap">
              <input type="text" v-model="searchInvestor" class="field-input" placeholder="輸入投資人名稱..." @keyup.enter="doSearch" />
              <button v-if="searchInvestor" class="clear-x" @click="clearField('investor')" type="button" tabindex="-1">×</button>
            </div>
          </div>
          <div class="field-actions">
            <button class="search-btn" @click="doSearch">搜尋</button>
          </div>
        </div>
      </div>

      <!-- Plan List -->
      <div class="plan-list">
        <div class="list-header">
          <h2><span class="h2-icon">≡</span> 投資計畫列表</h2>
          <div class="list-controls">
            <span class="count-badge">共 {{ total }} 筆</span>
            <button class="add-btn" @click="openCreate">＋ 新增計畫</button>
          </div>
        </div>

        <div v-if="loading" class="loading-row">
          <span class="spinner"></span>
          <span>載入中...</span>
        </div>

        <p v-else-if="plans.length === 0" class="empty">目前沒有投資計畫</p>

        <div v-else class="table-wrap">
          <table>
            <thead>
              <tr>
                <th class="col-no">#</th>
                <th>日期</th>
                <th>計畫名稱</th>
                <th>投資人</th>
                <th>股票標的</th>
                <th>即時股價</th>
                <th>計畫內容</th>
                <th class="col-action">操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(plan, idx) in plans" :key="plan.id">
                <td class="col-no">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
                <td class="date-cell">{{ plan.plan_date }}</td>
                <td class="name-cell">{{ plan.plan_name }}</td>
                <td class="investor-cell">{{ plan.investor }}</td>
                <td>
                  <router-link :to="`/chart/${plan.ticker}`" class="stock-link">
                    <span class="stock-name">{{ plan.stock_name || plan.ticker }}</span>
                    <span class="stock-ticker">{{ plan.ticker }}</span>
                  </router-link>
                </td>
                <td class="price-cell">
                  <template v-if="prices[plan.ticker] === undefined">
                    <span class="price-loading">取得中...</span>
                  </template>
                  <template v-else-if="prices[plan.ticker] === null">
                    <span class="price-na">—</span>
                  </template>
                  <template v-else>
                    <span v-if="prices[plan.ticker]?.price != null" class="price-val">{{ prices[plan.ticker].price.toLocaleString() }}</span>
                    <span v-if="prices[plan.ticker]?.change_percent != null" :class="['change-pct', prices[plan.ticker].change_percent >= 0 ? 'up' : 'down']">
                      {{ prices[plan.ticker].change_percent >= 0 ? '+' : '' }}{{ prices[plan.ticker].change_percent.toFixed(2) }}%
                    </span>
                    <span v-if="prices[plan.ticker]?.price == null" class="price-na">—</span>
                  </template>
                </td>
                <td class="content-cell" :title="plan.content">
                  {{ plan.content.length > 25 ? plan.content.slice(0, 25) + '…' : plan.content }}
                </td>
                <td class="action-cell">
                  <button class="view-btn" @click="viewTarget = plan">檢視</button>
                  <button class="edit-btn" @click="openEdit(plan)">編輯</button>
                  <button class="del-btn" @click="deleteTarget = plan">刪除</button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>

        <!-- Pagination - always visible -->
        <div class="pagination">
          <div class="pagination-left">
            <span class="pg-label">每頁</span>
            <select v-model="pageSize" class="pg-select" @change="onPageSizeChange">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
            <span class="pg-label">筆</span>
          </div>
          <div class="pagination-center">
            <button @click="gotoPage(currentPage - 1)" :disabled="currentPage === 1">‹</button>
            <button
              v-for="p in visiblePages"
              :key="p"
              :class="{ active: p === currentPage }"
              @click="gotoPage(p)"
            >{{ p }}</button>
            <button @click="gotoPage(currentPage + 1)" :disabled="currentPage === totalPages">›</button>
          </div>
          <div class="pagination-right">
            <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 頁</span>
          </div>
        </div>
      </div>
    </main>

    <!-- Create/Edit Modal -->
    <div v-if="showForm" class="modal-overlay" @click.self="showForm = false">
      <div class="modal form-modal">
        <h3>{{ editingPlan ? '編輯投資計畫' : '新增投資計畫' }}</h3>
        <div class="form-grid">
          <div class="form-field">
            <label>日期 <span class="required">*</span></label>
            <input type="date" v-model="form.plan_date" class="field-input form-date-input" />
          </div>
          <div class="form-field">
            <label>計畫項目名稱 <span class="required">*</span></label>
            <input type="text" v-model="form.plan_name" class="field-input" placeholder="輸入計畫名稱..." />
          </div>
          <div class="form-field">
            <label>投資人</label>
            <input type="text" v-model="form.investor" class="field-input" placeholder="輸入投資人名稱..." />
          </div>
          <div class="form-field">
            <label>股票代號</label>
            <input type="text" v-model="form.ticker" class="field-input" placeholder="例: 2330" />
          </div>
          <div class="form-field">
            <label>股票名稱</label>
            <input type="text" v-model="form.stock_name" class="field-input" placeholder="例: 台積電" />
          </div>
          <div class="form-field full-width content-field">
            <label>計畫內容 <span class="required">*</span></label>
            <textarea v-model="form.content" class="field-textarea content-textarea" placeholder="輸入投資計畫內容..." rows="10"></textarea>
          </div>
        </div>
        <p v-if="formError" class="form-error">{{ formError }}</p>
        <div class="modal-footer">
          <button class="modal-cancel" @click="showForm = false">取消</button>
          <button class="modal-confirm save-btn" @click="submitForm" :disabled="submitting">
            {{ submitting ? '儲存中...' : '儲存' }}
          </button>
        </div>
      </div>
    </div>

    <!-- View Modal -->
    <div v-if="viewTarget" class="modal-overlay" @click.self="viewTarget = null">
      <div class="modal form-modal">
        <h3>投資計畫檢視</h3>
        <div class="view-grid">
          <div class="view-row">
            <span class="view-label">日期</span>
            <span class="view-val">{{ viewTarget.plan_date }}</span>
          </div>
          <div class="view-row">
            <span class="view-label">計畫名稱</span>
            <span class="view-val">{{ viewTarget.plan_name }}</span>
          </div>
          <div class="view-row">
            <span class="view-label">投資人</span>
            <span class="view-val">{{ viewTarget.investor || '—' }}</span>
          </div>
          <div class="view-row">
            <span class="view-label">股票代號</span>
            <span class="view-val">{{ viewTarget.ticker || '—' }}</span>
          </div>
          <div class="view-row">
            <span class="view-label">股票名稱</span>
            <span class="view-val">{{ viewTarget.stock_name || '—' }}</span>
          </div>
          <div class="view-row full-row">
            <span class="view-label">計畫內容</span>
            <pre class="view-content">{{ viewTarget.content }}</pre>
          </div>
        </div>
        <div class="modal-footer">
          <button class="modal-cancel" @click="viewTarget = null">關閉</button>
        </div>
      </div>
    </div>

    <!-- Delete Confirmation Modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal">
        <h3>確認刪除</h3>
        <p>確定要刪除 <strong>{{ deleteTarget.plan_name }}</strong> 這筆投資計畫嗎？</p>
        <div class="modal-footer">
          <button class="modal-cancel" @click="deleteTarget = null">取消</button>
          <button class="modal-confirm" @click="doDelete">確認刪除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'

const router = useRouter()
const auth = useAuthStore()

const plans = ref<any[]>([])
const total = ref(0)
const loading = ref(false)
const prices = ref<Record<string, any>>({})

const currentPage = ref(1)
const pageSize = ref(10)

const searchDate = ref('')
const searchStock = ref('')
const searchInvestor = ref('')
const appliedDate = ref('')
const appliedStock = ref('')
const appliedInvestor = ref('')

const showForm = ref(false)
const editingPlan = ref<any>(null)
const submitting = ref(false)
const formError = ref('')
const form = ref({
  plan_date: '',
  plan_name: '',
  investor: '',
  ticker: '',
  stock_name: '',
  content: '',
})

const deleteTarget = ref<any>(null)
const viewTarget = ref<any>(null)

const totalPages = computed(() => Math.max(1, Math.ceil(total.value / pageSize.value)))

const visiblePages = computed(() => {
  const result: number[] = []
  const tp = totalPages.value
  const cur = currentPage.value
  let start = Math.max(1, cur - 2)
  const end = Math.min(tp, start + 4)
  if (end - start < 4) start = Math.max(1, end - 4)
  for (let i = start; i <= end; i++) result.push(i)
  return result
})

async function loadPlans() {
  loading.value = true
  const startTs = Date.now()
  try {
    const params: Record<string, any> = { page: currentPage.value, page_size: pageSize.value }
    if (appliedDate.value) params.plan_date = appliedDate.value
    if (appliedStock.value) params.stock = appliedStock.value
    if (appliedInvestor.value) params.investor = appliedInvestor.value

    const res = await client.get('/investment-plans', { params })
    plans.value = res.data.items
    total.value = res.data.total
    fetchPrices()
  } finally {
    const elapsed = Date.now() - startTs
    if (400 - elapsed > 0) await new Promise(r => setTimeout(r, 400 - elapsed))
    loading.value = false
  }
}

async function fetchPrices() {
  const tickers = [...new Set<string>(plans.value.map((p: any) => p.ticker))]
  tickers.forEach(t => {
    if (!(t in prices.value)) prices.value[t] = undefined
  })
  await Promise.allSettled(
    tickers.map(async (ticker) => {
      try {
        const res = await client.get(`/stocks/${ticker}/price`)
        prices.value = { ...prices.value, [ticker]: res.data }
      } catch {
        prices.value = { ...prices.value, [ticker]: null }
      }
    })
  )
}

function doSearch() {
  appliedDate.value = searchDate.value
  appliedStock.value = searchStock.value
  appliedInvestor.value = searchInvestor.value
  currentPage.value = 1
  loadPlans()
}

function clearField(field: 'date' | 'stock' | 'investor') {
  if (field === 'date') searchDate.value = ''
  if (field === 'stock') searchStock.value = ''
  if (field === 'investor') searchInvestor.value = ''
  doSearch()
}

function gotoPage(p: number) {
  if (p < 1 || p > totalPages.value) return
  currentPage.value = p
  loadPlans()
}

function onPageSizeChange() {
  currentPage.value = 1
  loadPlans()
}

function openCreate() {
  editingPlan.value = null
  form.value = { plan_date: '', plan_name: '', investor: '', ticker: '', stock_name: '', content: '' }
  formError.value = ''
  showForm.value = true
}

function openEdit(plan: any) {
  editingPlan.value = plan
  form.value = {
    plan_date: plan.plan_date,
    plan_name: plan.plan_name,
    investor: plan.investor,
    ticker: plan.ticker,
    stock_name: plan.stock_name,
    content: plan.content,
  }
  formError.value = ''
  showForm.value = true
}

async function submitForm() {
  if (!form.value.plan_date || !form.value.plan_name || !form.value.content) {
    formError.value = '請填寫所有必填欄位（*）'
    return
  }
  submitting.value = true
  formError.value = ''
  try {
    if (editingPlan.value) {
      await client.put(`/investment-plans/${editingPlan.value.id}`, form.value)
    } else {
      await client.post('/investment-plans', form.value)
    }
    showForm.value = false
    await loadPlans()
  } catch (e: any) {
    formError.value = e.response?.data?.detail || '操作失敗，請重試'
  } finally {
    submitting.value = false
  }
}

async function doDelete() {
  if (!deleteTarget.value) return
  await client.delete(`/investment-plans/${deleteTarget.value.id}`)
  deleteTarget.value = null
  await loadPlans()
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(loadPlans)
</script>

<style scoped>
.dashboard { min-height: 100vh; background: #080c14; }

header {
  background: #0d1829;
  border-bottom: 1px solid #1e3a5f;
  padding: 0.75rem 2rem;
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: sticky; top: 0; z-index: 10;
}

.brand { display: flex; align-items: center; gap: 0.5rem; }
.brand-icon { color: #00c8ff; font-size: 1.2rem; text-shadow: 0 0 10px rgba(0,200,255,0.6); }
.brand-name { font-size: 1rem; font-weight: 700; letter-spacing: 2px; color: #e2eeff; }
.header-right { display: flex; align-items: center; gap: 0.75rem; }

.status-dot { width: 8px; height: 8px; border-radius: 50%; background: #4ade80; box-shadow: 0 0 6px rgba(74,222,128,0.7); animation: pulse 2s infinite; }
@keyframes pulse { 0%,100% { opacity: 1; } 50% { opacity: 0.5; } }
.status-text { font-size: 0.75rem; color: #4a7aad; letter-spacing: 0.5px; }

.calc-link { background: transparent; border: 1px solid #1e3a5f; color: #4a7aad; padding: 0.35rem 0.9rem; border-radius: 4px; font-size: 0.8rem; text-decoration: none; transition: border-color 0.2s, color 0.2s; }
.calc-link:hover { border-color: #00c8ff; color: #00c8ff; }

.logout-btn { background: transparent; border: 1px solid #1e3a5f; color: #4a7aad; padding: 0.35rem 0.9rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem; transition: border-color 0.2s, color 0.2s; }
.logout-btn:hover { border-color: #00c8ff; color: #00c8ff; }

main { max-width: 1600px; margin: 0 auto; padding: 1.5rem 2rem; display: flex; flex-direction: column; gap: 1.25rem; }

/* Search Panel */
.search-panel { background: #0d1829; border: 1px solid #1e3a5f; border-radius: 10px; padding: 1.25rem 1.5rem; }
.search-panel h2 { margin: 0 0 1rem; font-size: 0.85rem; font-weight: 600; color: #4a7aad; letter-spacing: 1px; text-transform: uppercase; display: flex; align-items: center; gap: 0.5rem; }
.h2-icon { color: #00c8ff; }

.search-fields { display: flex; align-items: flex-end; gap: 1rem; flex-wrap: wrap; }
.field-group { display: flex; flex-direction: column; gap: 0.35rem; }
.field-group label { font-size: 0.75rem; color: #4a7aad; letter-spacing: 0.3px; }
/* Wrapper acts as the styled "input box"; the real input is borderless inside */
.input-wrap {
  display: inline-flex;
  align-items: center;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  transition: border-color 0.2s;
}
.input-wrap:focus-within { border-color: #00c8ff; }
.input-wrap .field-input {
  border: none;
  background: transparent;
  outline: none;
  width: 170px;
  padding: 0.45rem 0.25rem 0.45rem 0.75rem;
}

/* Standalone field-input (form modal) keeps its own border */
.field-input { padding: 0.45rem 0.75rem; background: #060f1e; border: 1px solid #1e3a5f; border-radius: 6px; font-size: 0.8rem; color: #c9d6e8; outline: none; width: 200px; transition: border-color 0.2s; box-sizing: border-box; }
.field-input::placeholder { color: #2d4a6e; }
.field-input:focus { border-color: #00c8ff; }

/* Make calendar picker icon visible on dark background */
input[type="date"]::-webkit-calendar-picker-indicator {
  cursor: pointer;
  filter: brightness(0) invert(0.6) sepia(1) hue-rotate(175deg) saturate(5) brightness(1.5);
  opacity: 0.75;
  flex-shrink: 0;
}
input[type="date"]::-webkit-calendar-picker-indicator:hover { opacity: 1; }

/* Clear button: flex sibling at right edge */
.clear-x {
  flex-shrink: 0;
  padding: 0 0.45rem;
  background: none;
  border: none;
  color: #2d4a6e;
  cursor: pointer;
  font-size: 1rem;
  line-height: 1;
  transition: color 0.15s;
  user-select: none;
}
.clear-x:hover { color: #c9d6e8; }

.field-actions { display: flex; gap: 0.5rem; padding-bottom: 1px; }
.search-btn { padding: 0.45rem 1.1rem; background: rgba(0,200,255,0.12); border: 1px solid rgba(0,200,255,0.4); color: #00c8ff; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; transition: background 0.2s; }
.search-btn:hover { background: rgba(0,200,255,0.22); }

/* Plan List */
.plan-list { background: #0d1829; border: 1px solid #1e3a5f; border-radius: 10px; padding: 1.25rem 1.5rem; }
.list-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; gap: 1rem; flex-wrap: wrap; }
h2 { margin: 0; font-size: 0.85rem; font-weight: 600; color: #4a7aad; letter-spacing: 1px; text-transform: uppercase; display: flex; align-items: center; gap: 0.5rem; }
.list-controls { display: flex; align-items: center; gap: 0.75rem; }
.count-badge { font-size: 0.75rem; color: #4a7aad; white-space: nowrap; }
.add-btn { padding: 0.4rem 1rem; background: rgba(0,200,255,0.12); border: 1px solid rgba(0,200,255,0.4); color: #00c8ff; border-radius: 6px; cursor: pointer; font-size: 0.8rem; font-weight: 600; transition: background 0.2s; }
.add-btn:hover { background: rgba(0,200,255,0.22); }

.loading-row { display: flex; align-items: center; gap: 0.75rem; padding: 2rem 0; justify-content: center; color: #4a7aad; font-size: 0.875rem; }
.spinner { display: inline-block; width: 20px; height: 20px; border: 2px solid #1e3a5f; border-top-color: #00c8ff; border-radius: 50%; animation: spin 0.65s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }
.empty { color: #2d4a6e; font-size: 0.875rem; padding: 2rem 0; text-align: center; }

.table-wrap { overflow-x: auto; }
table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #1e3a5f; color: #2d4a6e; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap; }
td { padding: 0.75rem 0.75rem; border-bottom: 1px solid #111f35; color: #c9d6e8; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.015); }

.col-no { width: 36px; color: #2d4a6e !important; font-size: 0.75rem; text-align: center; }
.col-action { text-align: center; white-space: nowrap; }
.action-cell { text-align: center; white-space: nowrap; }

.date-cell { color: #4a7aad; white-space: nowrap; font-size: 0.82rem; }
.name-cell { font-weight: 500; }
.investor-cell { color: #c9d6e8; }

.stock-link { text-decoration: none; display: flex; flex-direction: column; gap: 2px; }
.stock-name { color: #c9d6e8; font-weight: 500; }
.stock-ticker { color: #00c8ff; font-size: 0.75rem; letter-spacing: 0.5px; }

.price-cell { white-space: nowrap; }
.price-loading { color: #2d4a6e; font-size: 0.75rem; }
.price-na { color: #2d4a6e; }
.price-val { font-family: 'Courier New', monospace; font-weight: 600; color: #c9d6e8; margin-right: 0.3rem; }
.change-pct { font-size: 0.75rem; font-family: 'Courier New', monospace; font-weight: 600; }
.up { color: #ff6b6b; }
.down { color: #4ade80; }

.content-cell { color: #4a7aad; font-size: 0.82rem; max-width: 260px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; cursor: default; }

.view-btn { background: transparent; border: 1px solid rgba(74,122,173,0.4); color: #4a7aad; padding: 0.25rem 0.6rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; margin-right: 0.4rem; transition: background 0.2s, border-color 0.2s, color 0.2s; }
.view-btn:hover { background: rgba(74,122,173,0.1); border-color: #4a7aad; color: #c9d6e8; }
.edit-btn { background: transparent; border: 1px solid rgba(0,200,255,0.3); color: #00c8ff; padding: 0.25rem 0.6rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; margin-right: 0.4rem; transition: background 0.2s, border-color 0.2s; }
.edit-btn:hover { background: rgba(0,200,255,0.1); border-color: #00c8ff; }
.del-btn { background: transparent; border: 1px solid rgba(255,77,109,0.3); color: #ff4d6d; padding: 0.25rem 0.6rem; border-radius: 4px; cursor: pointer; font-size: 0.75rem; transition: background 0.2s, border-color 0.2s; }
.del-btn:hover { background: rgba(255,77,109,0.1); border-color: #ff4d6d; }

/* Pagination */
.pagination { display: flex; align-items: center; justify-content: space-between; gap: 0.75rem; margin-top: 1rem; flex-wrap: wrap; border-top: 1px solid #111f35; padding-top: 0.75rem; }
.pagination-left, .pagination-center, .pagination-right { display: flex; align-items: center; gap: 0.35rem; }
.pg-label { font-size: 0.75rem; color: #2d4a6e; white-space: nowrap; }
.pg-select { padding: 0.25rem 0.4rem; background: #060f1e; border: 1px solid #1e3a5f; border-radius: 4px; color: #4a7aad; font-size: 0.78rem; outline: none; cursor: pointer; }
.pg-select:focus { border-color: #00c8ff; }
.pg-select option { background: #0d1829; }
.pagination-center button { padding: 0.3rem 0.6rem; background: #060f1e; border: 1px solid #1e3a5f; color: #4a7aad; border-radius: 4px; cursor: pointer; font-size: 0.8rem; min-width: 30px; transition: border-color 0.2s, color 0.2s; }
.pagination-center button:hover:not(:disabled) { border-color: #00c8ff; color: #00c8ff; }
.pagination-center button.active { background: rgba(0,200,255,0.12); border-color: #00c8ff; color: #00c8ff; }
.pagination-center button:disabled { opacity: 0.3; cursor: not-allowed; }
.page-info { font-size: 0.75rem; color: #2d4a6e; white-space: nowrap; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.modal { background: #0d1829; border: 1px solid #1e3a5f; border-radius: 10px; padding: 1.75rem 2rem; width: 400px; max-width: 90vw; box-shadow: 0 0 40px rgba(0,0,0,0.6); }
.form-modal { width: 640px; max-height: 90vh; overflow-y: auto; }
.modal h3 { margin: 0 0 1.25rem; color: #e2eeff; font-size: 1rem; }
.modal p { margin: 0 0 1.5rem; color: #4a7aad; font-size: 0.875rem; line-height: 1.6; }
.modal strong { color: #00c8ff; }
.modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.25rem; }
.modal-cancel { padding: 0.5rem 1.25rem; background: transparent; border: 1px solid #1e3a5f; color: #4a7aad; border-radius: 6px; cursor: pointer; font-size: 0.875rem; transition: border-color 0.2s, color 0.2s; }
.modal-cancel:hover { border-color: #4a7aad; color: #c9d6e8; }
.modal-confirm { padding: 0.5rem 1.25rem; background: rgba(255,77,109,0.15); border: 1px solid rgba(255,77,109,0.4); color: #ff4d6d; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 600; transition: background 0.2s, border-color 0.2s; }
.modal-confirm:hover { background: rgba(255,77,109,0.25); border-color: #ff4d6d; }
.save-btn { background: rgba(0,200,255,0.12) !important; border-color: rgba(0,200,255,0.4) !important; color: #00c8ff !important; }
.save-btn:hover { background: rgba(0,200,255,0.22) !important; }
.save-btn:disabled { opacity: 0.5; cursor: not-allowed; }

/* Form Grid */
.form-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1rem; }
.form-field { display: flex; flex-direction: column; gap: 0.4rem; }
.form-field.full-width { grid-column: 1 / -1; }
.form-field label { font-size: 0.78rem; color: #4a7aad; }
.required { color: #ff4d6d; }
.field-textarea { padding: 0.5rem 0.75rem; background: #060f1e; border: 1px solid #1e3a5f; border-radius: 6px; font-size: 0.82rem; color: #c9d6e8; outline: none; resize: vertical; font-family: inherit; transition: border-color 0.2s; width: 100%; box-sizing: border-box; }
.field-textarea::placeholder { color: #2d4a6e; }
.field-textarea:focus { border-color: #00c8ff; }
.content-textarea { min-height: 220px; font-size: 0.9rem; line-height: 1.6; }
/* Form modal date input fills its grid cell */
.form-date-input { width: 100%; }
.content-field label { font-size: 0.82rem; font-weight: 600; color: #00c8ff; }
.form-error { color: #ff4d6d; font-size: 0.8rem; margin: 0.5rem 0 0; }

/* View modal */
.view-grid { display: flex; flex-direction: column; gap: 0.75rem; }
.view-row { display: flex; gap: 1rem; align-items: baseline; }
.full-row { flex-direction: column; gap: 0.4rem; }
.view-label { font-size: 0.75rem; color: #2d4a6e; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap; min-width: 72px; }
.view-val { color: #c9d6e8; font-size: 0.875rem; }
.view-content { margin: 0; color: #c9d6e8; font-size: 0.875rem; line-height: 1.7; white-space: pre-wrap; word-break: break-word; background: #060f1e; border: 1px solid #1e3a5f; border-radius: 6px; padding: 0.75rem 1rem; font-family: inherit; max-height: 360px; overflow-y: auto; }

@media (max-width: 640px) {
  header { padding: 0.6rem 1rem; flex-wrap: wrap; gap: 0.5rem; }
  .status-text { display: none; }
  .header-right { width: 100%; border-top: 1px solid #111f35; padding-top: 0.5rem; gap: 0.5rem; }
  main { padding: 0.75rem; }
  .search-fields { flex-direction: column; align-items: stretch; }
  .field-input { width: 100%; }
  .field-group { width: 100%; }
  .form-grid { grid-template-columns: 1fr; }
  .form-modal { width: 95vw; }
  table { min-width: 700px; }
}
</style>
