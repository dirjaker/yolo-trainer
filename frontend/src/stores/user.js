import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, register as registerApi } from '../api/auth'

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')

  async function login(form) {
    const res = await loginApi(form.username, form.password)
    token.value = res.token
    username.value = form.username
    localStorage.setItem('token', res.token)
    localStorage.setItem('username', form.username)
  }

  async function register(form) {
    await registerApi(form.username, form.email, form.password)
  }

  function logout() {
    token.value = ''
    username.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
  }

  return { token, username, login, register, logout }
})
