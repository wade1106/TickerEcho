import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('access_token'))

  function isLoggedIn() {
    return !!token.value
  }

  async function login(username: string, password: string) {
    const res = await axios.post('/api/auth/login', { username, password })
    token.value = res.data.access_token
    localStorage.setItem('access_token', token.value!)
  }

  function logout() {
    token.value = null
    localStorage.removeItem('access_token')
  }

  return { token, isLoggedIn, login, logout }
})
