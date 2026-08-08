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
        <button class="logout-btn" @click="logout">登出</button>
      </div>
    </header>

    <main>
      <AddAlertForm
        :editingAlert="editingAlert"
        @added="onAlertSaved"
        @cancel-edit="editingAlert = null"
      />

      <div class="alert-list">
        <div class="list-header">
          <h2><span class="h2-icon">≡</span> 警報列表</h2>
          <div class="list-controls">
            <input v-model="searchQuery" class="search-input" placeholder="搜尋股票名稱或代碼..." />
            <span class="count-badge">{{ filteredAlerts.length }} 筆</span>
          </div>
        </div>

        <div v-if="loading" class="loading-row">
          <span class="spinner"></span>
          <span>載入中...</span>
        </div>

        <p v-else-if="filteredAlerts.length === 0" class="empty">
          {{ alerts.length === 0 ? '目前沒有警報' : '沒有符合的結果' }}
        </p>

        <table v-else>
          <thead>
            <tr>
              <th class="col-no">#</th>
              <th>股票</th>
              <th class="col-cond">▲ 高於</th>
              <th class="col-cond">≈ 等於</th>
              <th class="col-cond">▼ 低於</th>
              <th>Email</th>
              <th class="col-action">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-for="(alert, idx) in pagedAlerts" :key="alert.id" :class="{ 'row-done': !alert.is_active }">
              <td class="col-no">{{ (currentPage - 1) * pageSize + idx + 1 }}</td>
              <td>
                <router-link :to="`/chart/${alert.ticker}`">
                  <span class="stock-name">{{ alert.name }}</span>
                  <span class="stock-ticker">{{ alert.ticker }}</span>
                </router-link>
              </td>
              <td class="cond-cell">
                <span v-if="alert.above_price != null" :class="['cond-val', alert.above_triggered_at ? 'triggered' : 'above']">
                  {{ alert.above_price.toLocaleString() }}
                  <span class="cond-tag">{{ alert.above_triggered_at ? '已觸發' : '監控中' }}</span>
                </span>
                <span v-else class="cond-empty">—</span>
              </td>
              <td class="cond-cell">
                <span v-if="alert.equal_price != null" :class="['cond-val', alert.equal_triggered_at ? 'triggered' : 'equal']">
                  {{ alert.equal_price.toLocaleString() }}
                  <span class="cond-tag">{{ alert.equal_triggered_at ? '已觸發' : '監控中' }}</span>
                </span>
                <span v-else class="cond-empty">—</span>
              </td>
              <td class="cond-cell">
                <span v-if="alert.below_price != null" :class="['cond-val', alert.below_triggered_at ? 'triggered' : 'below']">
                  {{ alert.below_price.toLocaleString() }}
                  <span class="cond-tag">{{ alert.below_triggered_at ? '已觸發' : '監控中' }}</span>
                </span>
                <span v-else class="cond-empty">—</span>
              </td>
              <td class="email-cell">{{ alert.user_email || '—' }}</td>
              <td class="action-cell">
                <button class="edit-btn" @click="startEdit(alert)">編輯</button>
                <button class="del-btn" @click="deleteTarget = alert">刪除</button>
              </td>
            </tr>
          </tbody>
        </table>

        <div v-if="!loading && filteredAlerts.length > 0" class="pagination">
          <div class="pagination-left">
            <span class="pg-label">每頁</span>
            <select v-model="pageSize" class="pg-select">
              <option :value="5">5</option>
              <option :value="10">10</option>
              <option :value="20">20</option>
              <option :value="50">50</option>
            </select>
            <span class="pg-label">筆</span>
          </div>
          <div class="pagination-center">
            <button @click="currentPage--" :disabled="currentPage === 1">‹</button>
            <button v-for="p in totalPages" :key="p" :class="{ active: p === currentPage }" @click="currentPage = p">{{ p }}</button>
            <button @click="currentPage++" :disabled="currentPage === totalPages">›</button>
          </div>
          <div class="pagination-right">
            <span class="pg-label">前往</span>
            <input v-model="goToPage" class="pg-jump" type="number" min="1" :max="totalPages" placeholder="頁" @keyup.enter="jumpToPage" />
            <button class="pg-go" @click="jumpToPage">Go</button>
            <span class="page-info">第 {{ currentPage }} / {{ totalPages }} 頁</span>
          </div>
        </div>
      </div>
    </main>

    <!-- Delete confirmation modal -->
    <div v-if="deleteTarget" class="modal-overlay" @click.self="deleteTarget = null">
      <div class="modal">
        <h3>確認刪除</h3>
        <p>確定要刪除 <strong>{{ deleteTarget.name }}</strong> 這筆警報嗎？</p>
        <div class="modal-footer">
          <button class="modal-cancel" @click="deleteTarget = null">取消</button>
          <button class="modal-confirm" @click="doDelete">確認刪除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import client from '@/api/client'
import AddAlertForm from '@/components/AddAlertForm.vue'

const router = useRouter()
const auth = useAuthStore()
const alerts = ref<any[]>([])
const loading = ref(false)
const searchQuery = ref('')
const currentPage = ref(1)
const pageSize = ref(10)
const goToPage = ref('')
const editingAlert = ref<any>(null)
const deleteTarget = ref<any>(null)

const filteredAlerts = computed(() => {
  const q = searchQuery.value.trim().toLowerCase()
  if (!q) return alerts.value
  return alerts.value.filter(
    a => a.ticker.toLowerCase().includes(q) || a.name.toLowerCase().includes(q) || (a.user_email && a.user_email.toLowerCase().includes(q))
  )
})

const totalPages = computed(() => Math.max(1, Math.ceil(filteredAlerts.value.length / pageSize.value)))
const pagedAlerts = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  return filteredAlerts.value.slice(start, start + pageSize.value)
})

watch(searchQuery, () => { currentPage.value = 1 })
watch(pageSize, () => { currentPage.value = 1 })

function jumpToPage() {
  const n = parseInt(goToPage.value)
  if (n >= 1 && n <= totalPages.value) currentPage.value = n
  goToPage.value = ''
}

async function loadAlerts() {
  loading.value = true
  const start = Date.now()
  try {
    const res = await client.get('/alerts')
    alerts.value = res.data
  } finally {
    const elapsed = Date.now() - start
    if (400 - elapsed > 0) await new Promise(r => setTimeout(r, 400 - elapsed))
    loading.value = false
  }
}

function startEdit(alert: any) {
  editingAlert.value = alert
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

function onAlertSaved() {
  editingAlert.value = null
  loadAlerts()
}

async function doDelete() {
  if (!deleteTarget.value) return
  await client.delete(`/alerts/${deleteTarget.value.id}`)
  deleteTarget.value = null
  await loadAlerts()
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(loadAlerts)
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

.logout-btn { background: transparent; border: 1px solid #1e3a5f; color: #4a7aad; padding: 0.35rem 0.9rem; border-radius: 4px; cursor: pointer; font-size: 0.8rem; transition: border-color 0.2s, color 0.2s; }
.logout-btn:hover { border-color: #00c8ff; color: #00c8ff; }

main { max-width: 1600px; margin: 0 auto; padding: 1.5rem 2rem; }

.alert-list { background: #0d1829; border: 1px solid #1e3a5f; border-radius: 10px; padding: 1.25rem 1.5rem; }

.list-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 1rem; gap: 1rem; flex-wrap: wrap; }

h2 { margin: 0; font-size: 0.85rem; font-weight: 600; color: #4a7aad; letter-spacing: 1px; text-transform: uppercase; display: flex; align-items: center; gap: 0.5rem; }
.h2-icon { color: #00c8ff; font-size: 1rem; }
.list-controls { display: flex; align-items: center; gap: 0.75rem; }

.search-input { padding: 0.45rem 0.75rem; background: #060f1e; border: 1px solid #1e3a5f; border-radius: 6px; font-size: 0.8rem; color: #c9d6e8; outline: none; width: 220px; transition: border-color 0.2s; }
.search-input::placeholder { color: #2d4a6e; }
.search-input:focus { border-color: #00c8ff; }
.count-badge { font-size: 0.75rem; color: #4a7aad; white-space: nowrap; }

.loading-row { display: flex; align-items: center; gap: 0.75rem; padding: 2rem 0; justify-content: center; color: #4a7aad; font-size: 0.875rem; }
.spinner { display: inline-block; width: 20px; height: 20px; border: 2px solid #1e3a5f; border-top-color: #00c8ff; border-radius: 50%; animation: spin 0.65s linear infinite; flex-shrink: 0; }
@keyframes spin { to { transform: rotate(360deg); } }

.empty { color: #2d4a6e; font-size: 0.875rem; padding: 2rem 0; text-align: center; }

table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
th { text-align: left; padding: 0.5rem 0.75rem; border-bottom: 1px solid #1e3a5f; color: #2d4a6e; font-size: 0.75rem; font-weight: 600; letter-spacing: 0.5px; text-transform: uppercase; white-space: nowrap; }
td { padding: 0.75rem 0.75rem; border-bottom: 1px solid #111f35; color: #c9d6e8; vertical-align: middle; }
tr:last-child td { border-bottom: none; }
tr:hover td { background: rgba(255,255,255,0.015); }
tr.row-done td { opacity: 0.45; }

.col-no { width: 36px; color: #2d4a6e !important; font-size: 0.75rem; text-align: center; }
.col-cond { text-align: center; }
.col-action { text-align: center; }

a { text-decoration: none; display: flex; flex-direction: column; gap: 2px; }
.stock-name { color: #c9d6e8; font-weight: 500; }
.stock-ticker { color: #00c8ff; font-size: 0.75rem; letter-spacing: 0.5px; }

.cond-cell { text-align: center; }

.cond-val { display: inline-flex; flex-direction: column; align-items: center; gap: 2px; font-family: 'Courier New', monospace; font-weight: 600; font-size: 0.875rem; }
.cond-tag { font-size: 0.65rem; font-family: inherit; font-weight: 400; opacity: 0.8; }

.above { color: #ff6b6b; }
.equal { color: #fbbf24; }
.below { color: #4ade80; }
.triggered { color: #2d4a6e; }
.cond-empty { color: #1e3a5f; }

.email-cell { color: #4a7aad; font-size: 0.8rem; }
.action-cell { white-space: nowrap; text-align: center; }

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
.pagination-center button, .pg-go { padding: 0.3rem 0.6rem; background: #060f1e; border: 1px solid #1e3a5f; color: #4a7aad; border-radius: 4px; cursor: pointer; font-size: 0.8rem; min-width: 30px; transition: border-color 0.2s, color 0.2s; }
.pagination-center button:hover:not(:disabled), .pg-go:hover { border-color: #00c8ff; color: #00c8ff; }
.pagination-center button.active { background: rgba(0,200,255,0.12); border-color: #00c8ff; color: #00c8ff; }
.pagination-center button:disabled { opacity: 0.3; cursor: not-allowed; }
.pg-jump { width: 52px; padding: 0.28rem 0.4rem; background: #060f1e; border: 1px solid #1e3a5f; border-radius: 4px; color: #c9d6e8; font-size: 0.78rem; text-align: center; outline: none; }
.pg-jump:focus { border-color: #00c8ff; }
.pg-jump::-webkit-inner-spin-button { display: none; }
.page-info { font-size: 0.75rem; color: #2d4a6e; margin-left: 0.25rem; white-space: nowrap; }

/* Modal */
.modal-overlay { position: fixed; inset: 0; background: rgba(0,0,0,0.7); display: flex; align-items: center; justify-content: center; z-index: 1000; backdrop-filter: blur(2px); }
.modal { background: #0d1829; border: 1px solid #1e3a5f; border-radius: 10px; padding: 1.75rem 2rem; width: 400px; max-width: 90vw; box-shadow: 0 0 40px rgba(0,0,0,0.6); }
.modal h3 { margin: 0 0 0.75rem; color: #e2eeff; font-size: 1rem; }
.modal p { margin: 0 0 1.5rem; color: #4a7aad; font-size: 0.875rem; line-height: 1.6; }
.modal strong { color: #00c8ff; }
.modal-footer { display: flex; justify-content: flex-end; gap: 0.75rem; }
.modal-cancel { padding: 0.5rem 1.25rem; background: transparent; border: 1px solid #1e3a5f; color: #4a7aad; border-radius: 6px; cursor: pointer; font-size: 0.875rem; transition: border-color 0.2s, color 0.2s; }
.modal-cancel:hover { border-color: #4a7aad; color: #c9d6e8; }
.modal-confirm { padding: 0.5rem 1.25rem; background: rgba(255,77,109,0.15); border: 1px solid rgba(255,77,109,0.4); color: #ff4d6d; border-radius: 6px; cursor: pointer; font-size: 0.875rem; font-weight: 600; transition: background 0.2s, border-color 0.2s; }
.modal-confirm:hover { background: rgba(255,77,109,0.25); border-color: #ff4d6d; }
</style>
