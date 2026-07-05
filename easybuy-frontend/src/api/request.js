import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: 'http://localhost:9000',
  timeout: 10000
})

// --- Token 过期统一处理 ---
function handleAuthFailure(reason) {
  // 清除本地认证信息
  localStorage.removeItem('token')
  localStorage.removeItem('userInfo')
  // 仅在非登录页时跳转, 避免无限重定向
  if (router.currentRoute.value.path !== '/login') {
    ElMessage.warning(reason || '登录已过期，请重新登录')
    router.push({
      path: '/login',
      query: { redirect: router.currentRoute.value.fullPath }
    })
  }
}

// --- 请求拦截器 ---
request.interceptors.request.use(
  config => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  error => Promise.reject(error)
)

// --- 响应拦截器 ---
request.interceptors.response.use(
  response => {
    const res = response.data

    // 业务码非 200: 业务异常
    if (res && typeof res === 'object' && 'code' in res) {
      // 401: token 过期或无效 -> 跳登录
      if (res.code === 401) {
        handleAuthFailure(res.message || '登录已过期')
        return Promise.reject(new Error(res.message || 'Unauthorized'))
      }
      // 403: 无权限
      if (res.code === 403) {
        ElMessage.error(res.message || '没有权限执行该操作')
        return Promise.reject(new Error(res.message || 'Forbidden'))
      }
      // 其他业务错误
      if (res.code !== 200) {
        ElMessage.error(res.message || '请求失败')
        return Promise.reject(new Error(res.message || 'Request failed'))
      }
      return res
    }

    // 没有业务码, 直接返回原始数据
    return res
  },
  error => {
    // HTTP 层错误
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        handleAuthFailure(data?.message || '登录已过期，请重新登录')
      } else if (status === 403) {
        ElMessage.error(data?.message || '没有权限执行该操作')
      } else if (status === 404) {
        ElMessage.error(data?.message || '请求的资源不存在')
      } else if (status === 429) {
        ElMessage.warning('请求过于频繁，请稍后重试')
      } else if (status >= 500) {
        ElMessage.error(data?.message || '服务器异常，请稍后重试')
      } else {
        ElMessage.error(data?.message || error.message || '请求失败')
      }
    } else if (error.code === 'ECONNABORTED') {
      ElMessage.error('请求超时，请检查网络')
    } else {
      ElMessage.error(error.message || '网络异常')
    }
    return Promise.reject(error)
  }
)

export default request
