import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/userStore'

const routes = [
  {
    path: '/',
    redirect: '/products'
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '用户登录' }
  },
  {
    path: '/register',
    name: 'Register',
    component: () => import('@/views/Register.vue'),
    meta: { requiresAuth: false, title: '用户注册' }
  },
  {
    path: '/products',
    name: 'Products',
    component: () => import('@/views/ProductList.vue'),
    meta: { requiresAuth: true, title: '商品列表' }
  },
  {
    path: '/order/create',
    name: 'OrderCreate',
    component: () => import('@/views/OrderCreate.vue'),
    meta: { requiresAuth: true, title: '创建订单' }
  },
  {
    path: '/orders',
    name: 'Orders',
    component: () => import('@/views/OrderList.vue'),
    meta: { requiresAuth: true, title: '我的订单' }
  },
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/views/NotFound.vue'),
    meta: { requiresAuth: false, title: '404 Not Found' }
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const token = userStore.token
  const requiresAuth = to.meta.requiresAuth

  // 1. 主动检查 token 是否过期 (避免带着过期 token 访问受保护页面)
  if (token && userStore.isTokenExpired()) {
    userStore.clearAuth()
    ElMessage?.warning?.('登录已过期，请重新登录')
    if (to.path !== '/login') {
      return next({ path: '/login', query: { redirect: to.fullPath } })
    }
  }

  // 2. 需要登录但没有 token (或 token 刚被清除)
  if (requiresAuth && !userStore.token) {
    return next({ path: '/login', query: { redirect: to.fullPath } })
  }

  // 3. 已登录访问 /login 或 /register
  if ((to.path === '/login' || to.path === '/register') && userStore.token) {
    return next('/products')
  }

  // 4. 设置页面标题
  if (to.meta.title) {
    document.title = `${to.meta.title} - 易购商城`
  }

  next()
})

export default router
