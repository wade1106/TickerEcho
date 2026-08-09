<template>
  <div class="add-alert-form">
    <h2>
      <span class="h2-icon">{{ editingAlert ? '✎' : '+' }}</span>
      {{ editingAlert ? '編輯警報' : '新增警報' }}
    </h2>

    <div v-if="!editingAlert" class="search-row">
      <input v-model="searchQuery" placeholder="輸入股票代碼或中文名稱..." @input="onSearchInput" />
      <ul v-if="searchResults.length" class="dropdown">
        <li v-for="stock in searchResults" :key="stock.ticker" @click="selectStock(stock)">
          <span class="code">{{ stock.code }}</span>
          <span class="name">{{ stock.name }}</span>
        </li>
      </ul>
    </div>

    <div v-if="selected" class="form-body">
      <div class="selected-stock">
        <span class="ticker-badge">{{ selected.ticker }}</span>
        {{ selected.name }}
      </div>

      <div class="conditions-row">
        <div class="cond-block above">
          <label>▲ 高於</label>
          <input v-model.number="abovePrice" type="number" step="0.01" placeholder="目標價" />
        </div>
        <div class="cond-divider">|</div>
        <div class="cond-block equal">
          <label>≈ 等於</label>
          <input v-model.number="equalPrice" type="number" step="0.01" placeholder="目標價" />
        </div>
        <div class="cond-divider">|</div>
        <div class="cond-block below">
          <label>▼ 低於</label>
          <input v-model.number="belowPrice" type="number" step="0.01" placeholder="目標價" />
        </div>
        <div class="cond-divider">|</div>
        <div class="cond-block email-block">
          <label>通知 Email（選填）</label>
          <input v-model="userEmail" type="email" placeholder="your@email.com" />
        </div>
      </div>

      <div class="form-footer">
        <button @click="submit" :disabled="!canSubmit || submitting" class="submit-btn">
          <span v-if="submitting" class="btn-spinner"></span>
          {{ submitting ? '處理中...' : (editingAlert ? '更新' : '加入警報') }}
        </button>
        <button class="cancel-btn" @click="editingAlert ? cancelEdit() : reset()">取消</button>
        <p v-if="message" :class="['message', messageType]">{{ message }}</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import client from '@/api/client'

const props = defineProps<{ editingAlert?: any }>()
const emit = defineEmits(['added', 'cancel-edit'])

let debounceTimer: ReturnType<typeof setTimeout> | null = null

const searchQuery = ref('')
const searchResults = ref<any[]>([])
const selected = ref<any>(null)
const abovePrice = ref<number | null>(null)
const equalPrice = ref<number | null>(null)
const belowPrice = ref<number | null>(null)
const userEmail = ref('')
const message = ref('')
const messageType = ref<'success' | 'error'>('success')
const submitting = ref(false)

watch(() => props.editingAlert, (alert) => {
  if (alert) {
    selected.value = { ticker: alert.ticker, name: alert.name }
    abovePrice.value = alert.above_price ?? null
    equalPrice.value = alert.equal_price ?? null
    belowPrice.value = alert.below_price ?? null
    userEmail.value = alert.user_email ?? ''
  } else {
    reset()
  }
}, { immediate: true })

function toPrice(v: any): number | null {
  const n = Number(v)
  return v !== null && v !== '' && Number.isFinite(n) ? n : null
}

const canSubmit = computed(() => {
  const hasPrice = [abovePrice.value, equalPrice.value, belowPrice.value].some(
    v => toPrice(v) !== null
  )
  return selected.value && hasPrice
})

function onSearchInput() {
  if (debounceTimer) clearTimeout(debounceTimer)
  if (searchQuery.value.length < 2) { searchResults.value = []; return }
  debounceTimer = setTimeout(async () => {
    const res = await client.get('/stocks/search', { params: { q: searchQuery.value } })
    searchResults.value = res.data
  }, 300)
}

function selectStock(stock: any) {
  selected.value = stock
  searchQuery.value = `${stock.code} ${stock.name}`
  searchResults.value = []
}

function reset() {
  selected.value = null
  searchQuery.value = ''
  abovePrice.value = null
  equalPrice.value = null
  belowPrice.value = null
  userEmail.value = ''
}

function cancelEdit() {
  emit('cancel-edit')
}

async function submit() {
  if (!canSubmit.value || submitting.value) return
  submitting.value = true
  const start = Date.now()
  try {
    if (props.editingAlert) {
      await client.patch(`/alerts/${props.editingAlert.id}`, {
        above_price: toPrice(abovePrice.value),
        equal_price: toPrice(equalPrice.value),
        below_price: toPrice(belowPrice.value),
        user_email: userEmail.value,
      })
      messageType.value = 'success'
      message.value = '已更新'
      emit('added')
    } else {
      await client.post('/alerts', {
        ticker: selected.value.ticker,
        name: selected.value.name,
        user_email: userEmail.value,
        above_price: toPrice(abovePrice.value),
        equal_price: toPrice(equalPrice.value),
        below_price: toPrice(belowPrice.value),
      })
      messageType.value = 'success'
      message.value = `已新增 ${selected.value.name} 警報`
      reset()
      emit('added')
    }
  } catch (e: any) {
    messageType.value = 'error'
    message.value = e?.response?.data?.detail ?? '操作失敗'
  } finally {
    const elapsed = Date.now() - start
    const remaining = 500 - elapsed
    if (remaining > 0) await new Promise(r => setTimeout(r, remaining))
    submitting.value = false
  }
  setTimeout(() => (message.value = ''), 5000)
}
</script>

<style scoped>
.add-alert-form {
  padding: 1.25rem 1.5rem;
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 10px;
  margin-bottom: 1.5rem;
}

h2 {
  margin: 0 0 1rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: #4a7aad;
  letter-spacing: 1px;
  text-transform: uppercase;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.h2-icon {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 18px; height: 18px;
  background: #00c8ff;
  color: #080c14;
  border-radius: 4px;
  font-size: 0.9rem;
  font-weight: 700;
  line-height: 1;
}

.search-row { position: relative; margin-bottom: 0.75rem; }

input {
  padding: 0.55rem 0.75rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  font-size: 0.875rem;
  color: #c9d6e8;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
input:focus { border-color: #00c8ff; box-shadow: 0 0 0 2px rgba(0,200,255,0.1); }
input::placeholder { color: #2d4a6e; }
.search-row input { width: 100%; }

.dropdown {
  position: absolute;
  top: calc(100% + 4px); left: 0; right: 0;
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  list-style: none;
  margin: 0; padding: 0.25rem 0;
  z-index: 100;
  max-height: 200px;
  overflow-y: auto;
  box-shadow: 0 8px 24px rgba(0,0,0,0.5);
}
.dropdown li {
  padding: 0.5rem 0.75rem;
  cursor: pointer;
  display: flex;
  gap: 0.75rem;
  align-items: center;
  font-size: 0.875rem;
  transition: background 0.15s;
}
.dropdown li:hover { background: #111f35; }
.code { color: #00c8ff; font-weight: 600; min-width: 56px; font-size: 0.8rem; }
.name { color: #c9d6e8; }

.form-body { display: flex; flex-direction: column; gap: 0.75rem; }

.selected-stock {
  font-size: 0.9rem;
  color: #c9d6e8;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}

.ticker-badge {
  background: rgba(0,200,255,0.1);
  border: 1px solid rgba(0,200,255,0.3);
  color: #00c8ff;
  padding: 0.15rem 0.5rem;
  border-radius: 4px;
  font-size: 0.78rem;
  font-weight: 600;
  letter-spacing: 0.5px;
}

.conditions-row {
  display: flex;
  align-items: flex-end;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-radius: 8px;
  overflow: hidden;
}

.cond-block { flex: 1; padding: 0.6rem 0.75rem; display: flex; flex-direction: column; gap: 0.3rem; min-width: 0; }
.email-block { flex: 1.8; }

.cond-divider {
  color: #1e3a5f;
  font-size: 1.2rem;
  padding-bottom: 0.5rem;
  user-select: none;
  flex-shrink: 0;
  align-self: flex-end;
}

.cond-block label {
  display: block;
  font-size: 0.72rem;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}
.cond-block.above label { color: #ff6b6b; }
.cond-block.equal label { color: #fbbf24; }
.cond-block.below label { color: #4ade80; }
.email-block label { color: #4a7aad; }

.cond-block input {
  width: 100%;
  background: transparent;
  border: none;
  border-bottom: 1px solid #1e3a5f;
  border-radius: 0;
  padding: 0.25rem 0;
  font-size: 0.875rem;
  box-shadow: none !important;
}
.cond-block.above input:focus { border-bottom-color: #ff6b6b; }
.cond-block.equal input:focus { border-bottom-color: #fbbf24; }
.cond-block.below input:focus { border-bottom-color: #4ade80; }
.email-block input:focus { border-bottom-color: #00c8ff; }

.form-footer { display: flex; align-items: center; gap: 0.75rem; flex-wrap: wrap; }

.btn-spinner {
  display: inline-block;
  width: 13px; height: 13px;
  border: 2px solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  border-radius: 50%;
  animation: btn-spin 0.6s linear infinite;
  margin-right: 0.4rem;
}
@keyframes btn-spin { to { transform: rotate(360deg); } }
.submit-btn { display: inline-flex; align-items: center; }

button {
  padding: 0.55rem 1.5rem;
  background: linear-gradient(135deg, #0066cc, #0099ee);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.875rem;
  font-weight: 600;
  letter-spacing: 0.5px;
  box-shadow: 0 0 12px rgba(0,150,255,0.2);
  transition: opacity 0.2s, box-shadow 0.2s;
  white-space: nowrap;
}
button:hover { opacity: 0.9; box-shadow: 0 0 18px rgba(0,150,255,0.35); }
button:disabled { opacity: 0.4; cursor: not-allowed; }

.cancel-btn {
  background: transparent;
  border: 1px solid #1e3a5f;
  color: #4a7aad;
  box-shadow: none;
}
.cancel-btn:hover { border-color: #4a7aad; color: #c9d6e8; box-shadow: none; opacity: 1; }

.message { font-size: 0.82rem; padding: 0.4rem 0.6rem; border-radius: 4px; margin: 0; }
.message.success { color: #4ade80; background: rgba(74,222,128,0.08); border-left: 2px solid #4ade80; }
.message.error { color: #ff4d6d; background: rgba(255,77,109,0.08); border-left: 2px solid #ff4d6d; }

@media (max-width: 640px) {
  .conditions-row { flex-direction: column; }
  .cond-divider { display: none; }
  .cond-block, .email-block { flex: unset; width: 100%; }
  .form-footer { flex-direction: column; align-items: flex-start; }
  button { width: 100%; justify-content: center; }
  .cancel-btn { width: 100%; text-align: center; }
}
</style>
