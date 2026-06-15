import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi, getUserInfo as getUserInfoApi } from '@/api/user'

const TOKEN_KEY = 'token'
const USER_INFO_KEY = 'userInfo'

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    userInfo: JSON.parse(localStorage.getItem(USER_INFO_KEY) || '{}')
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,

    userId: (state) => state.userInfo?.id || null,

    username: (state) => state.userInfo?.username || ''
  },

  actions: {
    initFromStorage() {
      this.token = localStorage.getItem(TOKEN_KEY) || ''
      const storedUserInfo = localStorage.getItem(USER_INFO_KEY)
      if (storedUserInfo) {
        try {
          this.userInfo = JSON.parse(storedUserInfo)
        } catch (e) {
          this.userInfo = {}
          localStorage.removeItem(USER_INFO_KEY)
        }
      }
    },

    setToken(token) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },

    setUserInfo(userInfo) {
      this.userInfo = userInfo
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(userInfo))
    },

    async login(username, password) {
      try {
        const res = await loginApi({ username, password })

        if (res.data && res.data.token) {
          this.setToken(res.data.token)
          this.setUserInfo(res.data)
        }

        return res
      } catch (error) {
        this.clearAuth()
        throw error
      }
    },

    async register(username, password) {
      try {
        const res = await registerApi({ username, password })
        return res
      } catch (error) {
        throw error
      }
    },

    async getUserInfo() {
      try {
        const res = await getUserInfoApi()
        if (res.data) {
          this.setUserInfo(res.data)
        }
        return res
      } catch (error) {
        if (error.response?.status === 401) {
          this.clearAuth()
        }
        throw error
      }
    },

    async logout() {
      this.clearAuth()
    },

    clearAuth() {
      this.token = ''
      this.userInfo = {}
      localStorage.removeItem(TOKEN_KEY)
      localStorage.removeItem(USER_INFO_KEY)
    },

    isTokenExpired() {
      if (!this.token) return true

      try {
        const payload = this.parseJwtPayload(this.token)
        if (!payload || !payload.exp) return false

        const now = Math.floor(Date.now() / 1000)
        return payload.exp < now
      } catch {
        return true
      }
    },

    parseJwtPayload(token) {
      try {
        const base64Url = token.split('.')[1]
        if (!base64Url) return null

        const base64 = base64Url.replace(/-/g, '+').replace(/_/g, '/')
        const jsonPayload = decodeURIComponent(
          atob(base64)
            .split('')
            .map((c) => '%' + ('00' + c.charCodeAt(0).toString(16)).slice(-2))
            .join('')
        )

        return JSON.parse(jsonPayload)
      } catch {
        return null
      }
    }
  }
})
