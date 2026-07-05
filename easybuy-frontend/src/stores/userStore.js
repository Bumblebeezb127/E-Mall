import { defineStore } from 'pinia'
import { login as loginApi, register as registerApi, getUserInfo as getUserInfoApi } from '@/api/user'

const TOKEN_KEY = 'token'
const USER_INFO_KEY = 'userInfo'

function safeParse(json, fallback) {
  try {
    return json ? JSON.parse(json) : fallback
  } catch {
    return fallback
  }
}

export const useUserStore = defineStore('user', {
  state: () => ({
    token: localStorage.getItem(TOKEN_KEY) || '',
    userInfo: safeParse(localStorage.getItem(USER_INFO_KEY), {})
  }),

  getters: {
    isLoggedIn: (state) => !!state.token,

    userId: (state) => {
      if (state.userInfo?.id) return state.userInfo.id
      return null
    },

    username: (state) => state.userInfo?.username || '',

    // 综合判断登录态: 有 token 且未过期
    isAuthValid: (state) => {
      if (!state.token) return false
      return !isTokenExpired(state.token)
    }
  },

  actions: {
    initFromStorage() {
      this.token = localStorage.getItem(TOKEN_KEY) || ''
      const storedUserInfo = localStorage.getItem(USER_INFO_KEY)
      this.userInfo = safeParse(storedUserInfo, {})
    },

    setToken(token) {
      this.token = token
      localStorage.setItem(TOKEN_KEY, token)
    },

    setUserInfo(userInfo) {
      this.userInfo = userInfo || {}
      localStorage.setItem(USER_INFO_KEY, JSON.stringify(this.userInfo))
    },

    async login(username, password) {
      try {
        const res = await loginApi({ username, password })

        if (res.data && res.data.token) {
          this.setToken(res.data.token)
          this.setUserInfo({
            id: res.data.id,
            username: res.data.username,
            role: res.data.role || 'USER',
            token: res.data.token,
            expiresIn: res.data.expiresIn
          })
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
          this.setUserInfo({ ...this.userInfo, ...res.data })
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

    // 检查 token 是否过期 (未过期返回 false, 已过期或无效返回 true)
    isTokenExpired() {
      return isTokenExpired(this.token)
    },

    parseJwtPayload(token) {
      return parseJwtPayload(token)
    }
  }
})

// --- 工具函数 ---

function parseJwtPayload(token) {
  if (!token) return null
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

function isTokenExpired(token) {
  if (!token) return true
  const payload = parseJwtPayload(token)
  if (!payload || !payload.exp) return true
  const now = Math.floor(Date.now() / 1000)
  // 提前 30 秒视为过期, 避免临界点
  return payload.exp - 30 < now
}
