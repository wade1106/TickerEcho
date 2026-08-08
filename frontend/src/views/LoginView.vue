<template>
  <div class="login-container">
    <!-- decorative candlestick chart background -->
    <svg class="chart-bg" viewBox="0 0 1600 900" preserveAspectRatio="xMidYMid slice" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">
      <!-- horizontal grid lines -->
      <g stroke="#1a2d47" stroke-width="1" opacity="0.7">
        <line x1="0" y1="180" x2="1600" y2="180"/>
        <line x1="0" y1="300" x2="1600" y2="300"/>
        <line x1="0" y1="420" x2="1600" y2="420"/>
        <line x1="0" y1="540" x2="1600" y2="540"/>
        <line x1="0" y1="660" x2="1600" y2="660"/>
      </g>
      <!-- green (bullish) candles — body: y=close, height=open-close -->
      <g fill="#3a9d6e" stroke="#3a9d6e" stroke-width="1.2" opacity="0.38">
        <line x1="20"   y1="595" x2="20"   y2="645"/><rect x="14"  y="612" width="12" height="16"/>
        <line x1="84"   y1="590" x2="84"   y2="648"/><rect x="78"  y="608" width="12" height="22"/>
        <line x1="148"  y1="580" x2="148"  y2="640"/><rect x="142" y="602" width="12" height="23"/>
        <line x1="212"  y1="570" x2="212"  y2="640"/><rect x="206" y="598" width="12" height="27"/>
        <line x1="276"  y1="562" x2="276"  y2="632"/><rect x="270" y="590" width="12" height="28"/>
        <line x1="340"  y1="545" x2="340"  y2="625"/><rect x="334" y="580" width="12" height="30"/>
        <line x1="372"  y1="548" x2="372"  y2="598"/><rect x="366" y="560" width="12" height="22"/>
        <line x1="436"  y1="528" x2="436"  y2="595"/><rect x="430" y="545" width="12" height="35"/>
        <line x1="500"  y1="510" x2="500"  y2="582"/><rect x="494" y="525" width="12" height="40"/>
        <line x1="596"  y1="478" x2="596"  y2="528"/><rect x="590" y="482" width="12" height="28"/>
        <line x1="628"  y1="462" x2="628"  y2="502"/><rect x="622" y="468" width="12" height="17"/>
        <line x1="692"  y1="445" x2="692"  y2="508"/><rect x="686" y="455" width="12" height="35"/>
        <line x1="724"  y1="430" x2="724"  y2="472"/><rect x="718" y="438" width="12" height="20"/>
        <line x1="788"  y1="415" x2="788"  y2="478"/><rect x="782" y="422" width="12" height="38"/>
        <line x1="820"  y1="398" x2="820"  y2="442"/><rect x="814" y="405" width="12" height="20"/>
        <line x1="884"  y1="382" x2="884"  y2="440"/><rect x="878" y="388" width="12" height="34"/>
        <line x1="916"  y1="365" x2="916"  y2="408"/><rect x="910" y="372" width="12" height="20"/>
        <line x1="948"  y1="352" x2="948"  y2="392"/><rect x="942" y="358" width="12" height="17"/>
        <line x1="980"  y1="342" x2="980"  y2="378"/><rect x="974" y="348" width="12" height="14"/>
        <line x1="1044" y1="335" x2="1044" y2="385"/><rect x="1038" y="342" width="12" height="28"/>
        <line x1="1172" y1="402" x2="1172" y2="448"/><rect x="1166" y="418" width="12" height="12"/>
        <line x1="1236" y1="430" x2="1236" y2="468"/><rect x="1230" y="438" width="12" height="12"/>
        <line x1="1332" y1="465" x2="1332" y2="508"/><rect x="1326" y="472" width="12" height="18"/>
        <line x1="1396" y1="468" x2="1396" y2="515"/><rect x="1390" y="478" width="12" height="20"/>
        <line x1="1460" y1="458" x2="1460" y2="510"/><rect x="1454" y="470" width="12" height="25"/>
        <line x1="1524" y1="450" x2="1524" y2="508"/><rect x="1518" y="465" width="12" height="25"/>
        <line x1="1588" y1="445" x2="1588" y2="502"/><rect x="1582" y="460" width="12" height="25"/>
      </g>
      <!-- red (bearish) candles — body: y=open, height=close-open -->
      <g fill="#c0392b" stroke="#c0392b" stroke-width="1.2" opacity="0.38">
        <line x1="52"   y1="605" x2="52"   y2="648"/><rect x="46"  y="615" width="12" height="17"/>
        <line x1="116"  y1="598" x2="116"  y2="638"/><rect x="110" y="610" width="12" height="15"/>
        <line x1="180"  y1="588" x2="180"  y2="635"/><rect x="174" y="605" width="12" height="17"/>
        <line x1="244"  y1="578" x2="244"  y2="630"/><rect x="238" y="600" width="12" height="15"/>
        <line x1="308"  y1="568" x2="308"  y2="625"/><rect x="302" y="592" width="12" height="16"/>
        <line x1="404"  y1="552" x2="404"  y2="592"/><rect x="398" y="562" width="12" height="16"/>
        <line x1="468"  y1="535" x2="468"  y2="578"/><rect x="462" y="548" width="12" height="14"/>
        <line x1="532"  y1="518" x2="532"  y2="560"/><rect x="526" y="528" width="12" height="17"/>
        <line x1="660"  y1="468" x2="660"  y2="505"/><rect x="654" y="470" width="12" height="18"/>
        <line x1="756"  y1="438" x2="756"  y2="472"/><rect x="750" y="440" width="12" height="18"/>
        <line x1="852"  y1="405" x2="852"  y2="438"/><rect x="846" y="408" width="12" height="14"/>
        <line x1="1012" y1="348" x2="1012" y2="385"/><rect x="1006" y="352" width="12" height="16"/>
        <line x1="1076" y1="328" x2="1076" y2="378"/><rect x="1070" y="345" width="12" height="15"/>
        <line x1="1108" y1="345" x2="1108" y2="412"/><rect x="1102" y="362" width="12" height="33"/>
        <line x1="1140" y1="378" x2="1140" y2="448"/><rect x="1134" y="398" width="12" height="30"/>
        <line x1="1204" y1="405" x2="1204" y2="465"/><rect x="1198" y="420" width="12" height="28"/>
        <line x1="1268" y1="432" x2="1268" y2="488"/><rect x="1262" y="440" width="12" height="28"/>
        <line x1="1300" y1="455" x2="1300" y2="505"/><rect x="1294" y="470" width="12" height="18"/>
        <line x1="1364" y1="458" x2="1364" y2="512"/><rect x="1358" y="475" width="12" height="20"/>
        <line x1="1428" y1="462" x2="1428" y2="508"/><rect x="1422" y="480" width="12" height="12"/>
        <line x1="1492" y1="455" x2="1492" y2="505"/><rect x="1486" y="472" width="12" height="16"/>
        <line x1="1556" y1="448" x2="1556" y2="498"/><rect x="1550" y="468" width="12" height="14"/>
      </g>
    </svg>
    <div class="glow-ring"></div>
    <div class="login-card">
      <div class="brand">
        <span class="brand-icon">◈</span>
        <h1>TickerEcho</h1>
        <p class="brand-sub">台股價格監控系統</p>
      </div>
      <form @submit.prevent="handleLogin">
        <div class="field">
          <label>帳號</label>
          <input
            v-model="username"
            type="text"
            autocomplete="username"
            required
          />
        </div>
        <div class="field">
          <label>密碼</label>
          <div class="password-wrap">
            <input
              v-model="password"
              :type="showPassword ? 'text' : 'password'"
              autocomplete="current-password"
              required
            />
            <button type="button" class="eye-btn" @click="showPassword = !showPassword" tabindex="-1">
              <svg v-if="!showPassword" xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/></svg>
              <svg v-else xmlns="http://www.w3.org/2000/svg" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17.94 17.94A10.07 10.07 0 0 1 12 20c-7 0-11-8-11-8a18.45 18.45 0 0 1 5.06-5.94M9.9 4.24A9.12 9.12 0 0 1 12 4c7 0 11 8 11 8a18.5 18.5 0 0 1-2.16 3.19m-6.72-1.07a3 3 0 1 1-4.24-4.24"/><line x1="1" y1="1" x2="23" y2="23"/></svg>
            </button>
          </div>
        </div>
        <p v-if="error" class="error">{{ error }}</p>
        <button type="submit" :disabled="loading">{{ loading ? '驗證中...' : '登入系統' }}</button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const username = ref('admin')
const password = ref('changeme')
const showPassword = ref(false)
const error = ref('')
const loading = ref(false)

async function handleLogin() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(username.value, password.value)
    router.push('/')
  } catch {
    error.value = '帳號或密碼錯誤'
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: radial-gradient(ellipse at 50% 40%, #071428 0%, #080c14 70%);
  position: relative;
  overflow: hidden;
}

.login-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background-image:
    linear-gradient(rgba(0, 200, 255, 0.03) 1px, transparent 1px),
    linear-gradient(90deg, rgba(0, 200, 255, 0.03) 1px, transparent 1px);
  background-size: 40px 40px;
  pointer-events: none;
}

.chart-bg {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  pointer-events: none;
  z-index: 0;
}

.glow-ring {
  position: absolute;
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(0, 180, 255, 0.06) 0%, transparent 70%);
  pointer-events: none;
  z-index: 1;
}

.login-card {
  position: relative;
  z-index: 2;
  background: #0d1829;
  border: 1px solid #1e3a5f;
  border-radius: 12px;
  padding: 2.25rem 2rem;
  width: 360px;
  box-shadow: 0 0 40px rgba(0, 150, 255, 0.08), inset 0 1px 0 rgba(255,255,255,0.04);
}

.brand {
  text-align: center;
  margin-bottom: 2rem;
}

.brand-icon {
  display: block;
  font-size: 2rem;
  color: #00c8ff;
  text-shadow: 0 0 16px rgba(0, 200, 255, 0.6);
  margin-bottom: 0.5rem;
  line-height: 1;
}

h1 {
  margin: 0 0 0.25rem;
  font-size: 1.5rem;
  font-weight: 700;
  letter-spacing: 2px;
  color: #e2eeff;
}

.brand-sub {
  margin: 0;
  font-size: 0.75rem;
  color: #4a7aad;
  letter-spacing: 1px;
}

.field {
  margin-bottom: 1.1rem;
}

label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.75rem;
  color: #4a7aad;
  letter-spacing: 0.5px;
  text-transform: uppercase;
}

input {
  width: 100%;
  padding: 0.6rem 0.75rem;
  background: #060f1e;
  border: 1px solid #1e3a5f;
  border-radius: 6px;
  font-size: 0.9rem;
  color: #c9d6e8;
  outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}

input:focus {
  border-color: #00c8ff;
  box-shadow: 0 0 0 2px rgba(0, 200, 255, 0.12);
}

.password-wrap {
  position: relative;
  display: flex;
  align-items: center;
}

.password-wrap input { padding-right: 2.5rem; }

.eye-btn {
  position: absolute;
  right: 0.6rem;
  background: none;
  border: none;
  cursor: pointer;
  color: #4a7aad;
  padding: 0;
  display: flex;
  align-items: center;
  transition: color 0.2s;
}

.eye-btn:hover { color: #00c8ff; }

.error {
  color: #ff4d6d;
  font-size: 0.82rem;
  margin: 0.35rem 0 0.6rem;
  padding: 0.4rem 0.6rem;
  background: rgba(255, 77, 109, 0.08);
  border-radius: 4px;
  border-left: 2px solid #ff4d6d;
}

button[type="submit"] {
  width: 100%;
  padding: 0.7rem;
  margin-top: 0.5rem;
  background: linear-gradient(135deg, #0066cc, #0099ee);
  color: #fff;
  border: none;
  border-radius: 6px;
  cursor: pointer;
  font-size: 0.9rem;
  font-weight: 600;
  letter-spacing: 1px;
  transition: opacity 0.2s, box-shadow 0.2s;
  box-shadow: 0 0 16px rgba(0, 150, 255, 0.25);
}

button[type="submit"]:hover {
  opacity: 0.9;
  box-shadow: 0 0 24px rgba(0, 150, 255, 0.4);
}

button[type="submit"]:disabled {
  opacity: 0.5;
  cursor: not-allowed;
}
</style>
